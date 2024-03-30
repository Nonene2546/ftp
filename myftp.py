import socket
import random
import os

class FTPClient:
  def __init__(self):
    self.client_socket = None

  def is_connected(self):
    if not self.client_socket or self.client_socket.fileno() == -1:
      print('Not Connected.')
      return False
    return True

  def disconnect(self):
    self.send_ftp('QUIT')
    self.client_socket.close()
    self.client_socket = None

  def send_ftp(self, message):
    if not self.is_connected():
      print('Not connected.')
      return

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
      print("Already connected to test.rebex.net, use disconnect first.")
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

      self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.client_socket.connect((ip, int(port)))
      resp = self.client_socket.recv(1024)

      if resp.decode().startswith("220"):
        print(f"Connected to {ip}")
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

  def get(self, dir: str = None, local_dir: str = None):
    if dir is None:
      dir = input(f'Remote file ')
      local_dir = input(f'Local file ')
    elif local_dir is None:
      local_dir = dir

    data_port = random.randint(1024, 65535)
    local_ip = self.client_socket.getsockname()[0]
    port_command = "PORT " + ",".join(local_ip.split(".")) + "," + str(data_port // 256) + "," + str(
      data_port % 256)

    resp = self.send_ftp(port_command)

    if resp.startswith("200"):
      data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      data_socket.bind((local_ip, data_port))
      data_socket.listen(1)
      data_conn, _ = data_socket.accept()

      resp = self.send_ftp(f'RETR {dir}')

      if resp.startswith('550'):
        return

      local_path = os.path.join(os.getcwd(), local_dir)
      while True:
        data = data_conn.recv(1024)
        if not data:
          break

        with open(local_path, 'wb') as file:
          file.write(data)

      data_conn.close()
      data_socket.close()
      print(self.client_socket.recv(1024).decode(), end='')

  def ls(self, dir: str = None, local_dir: str = None):
    data_port = random.randint(1024, 65535)
    local_ip = self.client_socket.getsockname()[0]
    port_command = "PORT " + ",".join(local_ip.split(".")) + "," + str(data_port // 256) + "," + str(
      data_port % 256)

    resp = self.send_ftp(port_command)

    if resp.startswith("200"):
      try:
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.settimeout(10)
        data_socket.bind((local_ip, data_port))
        data_socket.listen(1)
        data_conn, _ = data_socket.accept()

        resp = self.send_ftp(f'NLST {dir}' if dir is not None else 'NLST')

        if local_dir is not None:
          local_path = os.path.join(os.getcwd(), local_dir)

        while True:
          data = data_conn.recv(1024)
          if not data:
            break
          if local_dir is None:
            print(data.decode(), end='')
          else:
            with open(local_path, 'wb') as file:
              file.write(data)

        data_conn.close()
        data_socket.close()
        print(self.client_socket.recv(1024).decode(), end='')
      except socket.timeout:
        print('> ftp: connect :Connection timed out')

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

    resp = ftp_client.send_ftp(f'RNFR {from_name}')
    if resp.startswith('550'):
      return
    ftp_client.send_ftp(f'RNTO {to_name}')


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

    # เชื่อม local ไม่ได้
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

    # เชื่อม local ไม่ได้
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

    # ยังไม่เสร็จ
    elif command == 'put':
      ftp_client.send_ftp(f'STOR {args[1]}')

    else:
      print('Invalid command.')

  except Exception as e:
    print(f"Error: {e}")
