import socket
import random

def isConnected(clientSocket: socket.socket):
  if not clientSocket or clientSocket.fileno() == -1:
    print('Not Connected.')
    return False
  return True

def sendFTP(message: str, clientSocket: socket.socket):
  """
  Send an FTP message to the server, receive and print the response.

  Args:
    message (str): The FTP message to send to the server.
    clientSocket (socket.socket): The socket object representing the client connection.

  Returns:
    resp: The response received from the server.

  """
  if not isConnected(clientSocket):
    return
  
  clientSocket.sendall((message + '\r\n').encode())

  resp = clientSocket.recv(1024).decode()
  print(resp, end='')
  return resp

def initSocket(clientSocket: socket.socket = None, ip: str = None, port: str = "21"):
  """
  Initialize a socket connection to the specified IP address and port number.

  Args:
    ip (str): The IP address to connect to. If not provided, the user will be prompted to enter it.
    port (int): The port number to connect to. Default is 21.

  Returns:
    clientSocket (socket.socket): The socket object representing the client connection.

  """

  if clientSocket and clientSocket.fileno() != -1:
    print("Already connected to test.rebex.net, use disconnect first.")
    return clientSocket, ip

  if ip is None:
    user_input = input('To: ').split()

    if len(user_input) > 2 or len(user_input) == 0:
      print('Usage: open host name [port]')
      return clientSocket, ip

    ip = user_input[0]
    port = user_input[1] if len(user_input) == 2 else port

  try:
    if not port.isdigit():
      print(f'{ip}: bad port number\nUsage: open host name [port]')
      return clientSocket, ip

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((ip, int(port)))
    resp = clientSocket.recv(1024)

    if resp.decode().startswith("220"):
      print(f"Connected to {ip}")
    print(resp.decode(), end='')
    sendFTP('OPTS UTF8 ON', clientSocket)
    userHandler(clientSocket, ip)

  except socket.timeout:
    print('> ftp: connect :Connection timed out')
    return clientSocket, ip

  except Exception as e:
    print(e)
    return clientSocket, ip

  return clientSocket, ip

def userHandler(clientSocket: socket.socket, ip: str = None, user: str = None, password: str = None):
  if not isConnected(clientSocket):
    return
  
  if user is None:
    if ip:
      user = input(f'User ({ip}:(none)): ')
    else:
      user = input(f'Username ')

    if not user:
      print("Login failed.")
      return
  
  resp = sendFTP(f'USER {user}', clientSocket)

  if (resp.startswith("331")):
    if not password:
      password = input("Password: ")
    
    res = sendFTP(f'PASS {password}', clientSocket)
    if (res.startswith("230")):
      return

  print("Login failed.")

def ls(clientSocket: socket.socket):
  dataPort = random.randint(1024, 65535)

  localIP = clientSocket.getsockname()[0]

  portCommand = "PORT " + ",".join(localIP.split(".")) + "," + str(dataPort // 256) + "," + str(dataPort % 256)

  resp = sendFTP(portCommand, clientSocket)

  if resp.startswith("200"):
    dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSocket.bind((localIP, dataPort))
    dataSocket.listen(1)
    dataConn, _ = dataSocket.accept()

    resp = sendFTP('NLST', clientSocket)

    while True:
      data = dataConn.recv(1024).decode()
      if not data:
        break
      print(data, end='')

    dataConn.close()
    dataSocket.close()
    print(clientSocket.recv(1024).decode(), end='')

clientSocket = None
ip = None

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
      clientSocket, ip = initSocket(clientSocket, *args[1:])

    elif command == 'user':
      if len(args) > 1:
        userHandler(clientSocket, None, *args[1:])
      else:
        userHandler(clientSocket)
    
    elif command == 'ascii':
      sendFTP('TYPE A', clientSocket)

    elif command == 'binary':
      sendFTP('TYPE I', clientSocket)

    elif command == 'ls':
      ls(clientSocket)
    
    # ยังไม่เสร็จ

    elif command == 'cd':
      sendFTP(f'CWD {args[1]}', clientSocket)

    elif command in ["close", "disconnect"]:
      sendFTP('QUIT', clientSocket)
      clientSocket.close()
      clientSocket = None

    elif command == 'delete':
      sendFTP(f'DELE {args[1]}', clientSocket)

    elif command == 'get':
      sendFTP(f'RETR {args[1]}', clientSocket)

    elif command == 'put':
      sendFTP(f'STOR {args[1]}', clientSocket)

    elif command == 'pwd':
      sendFTP('XPWD', clientSocket)

    elif command == 'rename':
      from_name = input(f'From name: ')
      to_name = input(f'To name: ')
      sendFTP(f'RNFR {from_name}', clientSocket)
      sendFTP(f'RNTO {to_name}', clientSocket)

    else:
      print('Invalid command.')

  except Exception as e:
    print(f"Error: {e}")

