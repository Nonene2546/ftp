import unittest
from unittest.mock import patch, MagicMock
import unittest
import subprocess
import multiprocessing
import re

def run_command(input_side_effects, result_queue):
  try:
    process = subprocess.Popen(["python", "myftp/myftp.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outputs, _ = process.communicate((''.join([x.decode() for x in input_side_effects]).encode()), timeout=2)
    results = []

    for output in outputs.split(b'\n'):
      result = output.decode().strip()
      if result != '':
        results.append(result)

    result_queue.put(results)
  except subprocess.TimeoutExpired as e:
    result_queue.put(e)

@patch('subprocess.Popen')
def mock_process(input_side_effects, expected_outputs, mock_popen):
  mock_process = MagicMock()
  mock_process.communicate.side_effect = expected_outputs
  mock_popen.return_value = mock_process

  result_queue = multiprocessing.Queue()
  process = multiprocessing.Process(target=run_command, args=(input_side_effects, result_queue))
  process.start()
  
  process.join(timeout=5)

  result = result_queue.get()

  return process, result

class TestCLIApp(unittest.TestCase):
  def validate(self, process, expected_outputs, result):
    if process.is_alive():
      process.terminate()
      process.join()
      self.fail("Command timed out")
    
    if isinstance(result, subprocess.TimeoutExpired):
      self.fail("Command timed out")
    else:
      # self.assertTrue(False, f"expected: {expected_outputs}\nresult: {result}")
      if len(expected_outputs) != len(result):
        self.assertTrue(False, f"Length of output doesn't match with expected length. expected: {len(expected_outputs)} result: {len(result)}\nexpected: {expected_outputs}\nresult: {result}")
      for expected_output, output in zip(expected_outputs, result):
        self.assertTrue(re.search(output, expected_output) or output == expected_output, f"answer doesn't match\nexpected: {expected_output}\nresult  : {output}")
      # self.assertTrue(False, f"\nexpected: {expected_outputs}\nresult: {result}")
  
  def execute(self, input_side_effects, expected_outputs):
    process, result = mock_process(input_side_effects, expected_outputs)
    self.validate(process, expected_outputs, result)

  def test_invalid_then_quit(self):
    input_side_effects = [b"a\n", b"quit\n"]
    expected_outputs = ["ftp> Invalid command.", "ftp>"]
    
    self.execute(input_side_effects, expected_outputs)

  def test_open_nologin_quit(self):
    input_side_effects = [b"open test.rebex.net\n", b"\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to test.rebex.net.", "220 Rebex FTP Server ready.", "200 Enabled UTF-8 encoding.", "User (test.rebex.net:(none)): 501 User name not specified.", "Login failed.", "ftp> 221 Closing session."]
    
    self.execute(input_side_effects, expected_outputs)
  
  def test_open_nologin_quit_2(self):
    input_side_effects = [b"open 194.108.117.16\n", b"\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 194.108.117.16.", "220 Rebex FTP Server ready.", "200 Enabled UTF-8 encoding.", "User (194.108.117.16:(none)): 501 User name not specified.", "Login failed.", "ftp> 221 Closing session."]

    self.execute(input_side_effects, expected_outputs)
  
  def test_open_nologin_quit_3(self):
    input_side_effects = [b"open 127.0.0.1\n", b"\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 501 Missing required argument", "Login failed.", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)
  
  def test_quit(self):
    input_side_effects = [b"quit\n"]
    expected_outputs = ["ftp>"]

    self.execute(input_side_effects, expected_outputs)

  def test_open_login_quit(self):
    input_side_effects = [b"open 127.0.0.1\n", b"alice\n", b"password\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 331 Please, specify the password.", "Password: 230 Login successful.", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)

  def test_open_nologin_login_quit(self):
    input_side_effects = [b"open 127.0.0.1\n", b"\n", b"user alice password\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 501 Missing required argument", "Login failed.", "ftp> 331 Please, specify the password.", "230 Login successful.", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)

  def test_open_nologin_login_quit_2(self):
    input_side_effects = [b"open 127.0.0.1\n", b"\n", b"user\n", b"alice\n", b"password\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 501 Missing required argument", "Login failed.", "ftp> Username 331 Please, specify the password.", "Password: 230 Login successful.", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)
  
  def test_open_login_ascii_quit(self):
    input_side_effects = [b"open 127.0.0.1\n", b"alice\n", b"password\n", b"ascii\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 331 Please, specify the password.", "Password: 230 Login successful.", "ftp> 200 Type set to A", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)

  def test_open_login_binary_quit(self):
    input_side_effects = [b"open 127.0.0.1\n", b"alice\n", b"password\n", b"binary\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 331 Please, specify the password.", "Password: 230 Login successful.", "ftp> 200 Type set to I", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)

  def test_open_login_pwd_quit(self):
    input_side_effects = [b"open 127.0.0.1\n", b"alice\n", b"password\n", b"pwd\n", b"quit\n"]
    expected_outputs = ["ftp> Connected to 127.0.0.1.", "220-FileZilla Server 1.8.1", "220 Please visit https://filezilla-project.org/", "202 UTF8 mode is always enabled. No need to send this command", "User (127.0.0.1:(none)): 331 Please, specify the password.", "Password: 230 Login successful.", "ftp> 257 \"/\" is current directory.", "ftp> 221 Goodbye."]

    self.execute(input_side_effects, expected_outputs)

if __name__ == "__main__":
  suite = unittest.TestLoader().loadTestsFromTestCase(TestCLIApp)
  result = unittest.TextTestRunner(verbosity=2).run(suite)
  
  if not result.wasSuccessful():
    print("\nFailed tests:")
    for failed_test, error in result.failures:
      print('----------', failed_test, '----------')
      print('\n'.join(error.split('\n')[-4:]))
