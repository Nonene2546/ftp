import socket
import random
import os
import time

class FTPStatsCalculator:
  def __init__(self):
    pass

  def start_timer(self):
    self.start_time = time.time()

  def end_timer(self):
    self.end_time = time.time()

  def print_stats(self, number_of_bytes):
    transfer_time = self.end_time - self.start_time
    transfer_speed = number_of_bytes / (transfer_time + 1e-10) / 1000
    print(f'ftp: {number_of_bytes} bytes sent in {transfer_time:.2f}Seconds {transfer_speed:.2f}Kbytes/sec.')

class FTPClient:
  def __init__(self):
    self.client_socket = None
    self.ip = None
    self.stats_calculator = FTPStatsCalculator()

  def sending_port_command(self):
    data_port = random.randint(1024, 65535)
    local_ip = self.client_socket.getsockname()[0]
    port_command = "PORT " + ",".join(local_ip.split(".")) + "," + str(data_port // 256) + "," + str(
      data_port % 256)

    resp = self.send_ftp(port_command)
    return resp, local_ip, data_port

  def init_data_socket(self, local_ip, data_port):
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.settimeout(10)
    data_socket.bind((local_ip, data_port))
    data_socket.listen(1)
    return data_socket

  def is_connected(self):
    if not self.client_socket or self.client_socket.fileno() == -1:
      return False
    return True

  def disconnect(self):
    resp = self.send_ftp('QUIT')
    if resp is None:
      return
    self.client_socket.close()
    self.client_socket = None

  def send_ftp(self, message):
    if not self.is_connected():
      print('Not connected.')
      return None

    self.client_socket.sendall((message + '\r\n').encode())
    resp = self.client_socket.recv(1024).decode()
    print(resp, end='')

    if resp.startswith("550 Closing"):
      print('Connection closed by remote host.')
      self.client_socket.close()
      self.client_socket = None

    return resp

  def init_socket(self, ip=None, port="21"):
    if self.client_socket and self.client_socket.fileno() != -1:
      print(f"Already connected to {self.ip}, use disconnect first.")
      return

    if ip is None:
      user_input = input('To: ').split()

      if len(user_input) > 2 or len(user_input) == 0:
        print('Usage: open host name [port]')
        return

      ip = user_input[0]
      port = user_input[1] if len(user_input) == 2 else port

    try:
      if not port.isdigit():
        print(f'{ip}: bad port number\nUsage: open host name [port]')
        return
      
      self.ip = ip

      self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.client_socket.connect((ip, int(port)))
      resp = self.client_socket.recv(1024)

      if resp.decode().startswith("220"):
        print(f"Connected to {ip}.")
      print(resp.decode(), end='')
      self.send_ftp('OPTS UTF8 ON')
      self.user_handler(ip)

    except socket.timeout:
      print('> ftp: connect :Connection timed out')
      return

    except Exception as e:
      print(e)
      return

  def user_handler(self, ip=None, user=None, password=None):
    if not self.is_connected():
      return

    if user is None:
      if ip:
        user = input(f'User ({ip}:(none)): ')
      else:
        user = input(f'Username ')

      if not user:
        self.send_ftp('User ')
        print("Login failed.")
        return

    resp = self.send_ftp(f'USER {user}')

    if resp.startswith("331"):
      if not password:
        password = input("Password: ")

      res = self.send_ftp(f'PASS {password}')
      if res.startswith("230"):
        return

    print("Login failed.")

  def get(self, remote_file: str = None, local_file: str = None):
    if remote_file is None:
      remote_file = input(f'Remote file ')
      local_file = input(f'Local file ')
    elif local_file is None:
      local_file = remote_file

    resp, local_ip, data_port = self.sending_port_command()

    if resp.startswith("200"):
      try:
        data_socket = self.init_data_socket()

        resp = self.send_ftp(f'RETR {remote_file}')
        if resp.startswith('5'):
          return
        
        write_to = os.path.join(os.getcwd(), local_file)
        can_write = 1
        try:
          with open(write_to, 'w') as file:
            file.write('')
        except:
          can_write = 0
          print('> R:No such process')
        
        if resp.startswith('1') and can_write:
          data_conn, _ = data_socket.accept()
          bytes_recv = 0
          self.stats_calculator.start_timer()

          while True:
            data = data_conn.recv(1024)
            if not data:
              break
            
            with open(write_to, 'ab') as file:
              file.write(data)

            bytes_recv += len(data)

          self.stats_calculator.end_timer()
          data_conn.close()

        data_socket.close()
        print(self.client_socket.recv(1024).decode(), end='')
        self.stats_calculator.print_stats(bytes_recv)

      except socket.timeout:
        print('> ftp: connect :Connection timed out')

  def ls(self, remote_file: str = None, local_file: str = None):
    resp, local_ip, data_port = self.sending_port_command()

    if resp.startswith("200"):
      try:
        data_socket = self.init_data_socket(local_ip, data_port)

        resp = self.send_ftp(f'NLST {remote_file}' if remote_file is not None else 'NLST')

        if resp.startswith('5'):
          data_socket.close()
          return

        if resp.startswith('1'):
          if local_file is not None:
            write_to = os.path.join(os.getcwd(), local_file)
            try:
              with open(write_to, 'w'):
                pass
            except IOError:
              data_socket.close()
              raise Exception(f"Error opening local file {local_file}.\n> {local_file[0]}:No Such file or directory")
          
          data_conn, _ = data_socket.accept()
          bytes_recv = 0
          self.stats_calculator.start_timer()

          while True:
            data = data_conn.recv(1024)
            if not data:
              break

            if local_file is None:
              print(data.decode(), end='')
            else:
              with open(write_to, 'ab') as file:
                file.write(data)

            bytes_recv += len(data)
          
          self.stats_calculator.end_timer()
          data_conn.close()

        data_socket.close()
        print(self.client_socket.recv(1024).decode(), end='')

        self.stats_calculator.print_stats(bytes_recv)

      except socket.timeout:
        print('> ftp: connect :Connection timed out')
      except Exception as e:
        print(e)

  def cd(self, dir: str = None):
    if dir is None:
      dir = input(f'Remote directory ')
    self.send_ftp(f'CWD {dir}')

  def delete(self, dir: str = None):
    if dir == None:
      dir = input(f'Remote file ')
    self.send_ftp(f'DELE {dir}')

  def rename(self, from_name: str = None, to_name: str = None):
    if from_name is None:
      from_name = input(f'From name: ')
    if to_name is None:
      to_name = input(f'To name: ')

    resp = self.send_ftp(f'RNFR {from_name}')
    if resp.startswith('5'):
      return
    self.send_ftp(f'RNTO {to_name}')

  def put(self, local_file: str = None, remote_file: str = None):
    if local_file is None:
      local_file = input(f'Local file ')
      remote_file = input(f'Remote file ')
    elif remote_file is None:
      remote_file = local_file

    resp, local_ip, data_port = self.sending_port_command()

    if resp.startswith("200"):
      try:
        data_socket = self.init_data_socket()

        resp = self.send_ftp(f'STOR {remote_file}')
        if resp.startswith('5'):
          return
          
        local_file = os.path.join(os.getcwd(), local_file)
        
        if resp.startswith('1'):
          data_conn, _ = data_socket.accept()
          self.stats_calculator.start_timer()

          with open(local_file, 'rb') as file:
            bytes_sent = data_conn.sendfile(file)

          self.stats_calculator.end_timer()
          data_conn.close()
        data_socket.close()
        print(self.client_socket.recv(1024).decode(), end='')
        self.stats_calculator.print_stats(bytes_sent)

      except socket.timeout:
        print('> ftp: connect :Connection timed out')

def main():
  ftp_client = FTPClient()

  while True:
    try:
      line = input(f'ftp> ')

      if not line:
        continue

      args = line.split()

      if len(args) == 0:
        print('Invalid command.')
        continue

      command = args[0]

      if command in ["bye", "quit"]:
        if ftp_client.is_connected():
          ftp_client.send_ftp('QUIT')
        break

      elif command == 'open':
        ftp_client.init_socket(*args[1:])

      elif command == 'user':
        if len(args) > 1:
          ftp_client.user_handler(None, *args[1:])
        else:
          ftp_client.user_handler()

      elif command == 'ascii':
        ftp_client.send_ftp('TYPE A')

      elif command == 'binary':
        ftp_client.send_ftp('TYPE I')

      elif command == 'ls':
        if len(args) > 1:
          ftp_client.ls(*args[1:])
        else:
          ftp_client.ls()

      elif command in ['disconnect', 'close']:
        ftp_client.disconnect()

      elif command == 'cd':
        ftp_client.cd(args[1] if len(args) > 1 else None)

      elif command == 'delete':
        ftp_client.delete(f'DELE {args[1] if len(args) > 1 else None}')

      elif command == 'get':
        if len(args) > 1:
          ftp_client.get(*args[1:])
        else:
          ftp_client.get()

      elif command == 'pwd':
        ftp_client.send_ftp('XPWD')

      elif command == 'rename':
        if len(args) > 1:
          ftp_client.rename(*args[1:])
        else:
          ftp_client.rename()

      elif command == 'put':
        if len(args) > 1:
          ftp_client.put(*args[1:])
        else:
          ftp_client.put()

      else:
        print('Invalid command.')

    except Exception as e:
      print(f"Error: {e}")

if __name__ == "__main__":
  main()
