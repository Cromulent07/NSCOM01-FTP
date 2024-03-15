import sys
import socket as s

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 21
BUFFER_SIZE = 4096

def main():
    global SERVER_HOST, SERVER_PORT, USER, PASSWD # Declare global variables
    if len(sys.argv) == 4:
        SERVER_PORT = int(sys.argv[1])
        USER = sys.argv[2]
        PASSWD = sys.argv[3]
    elif len(sys.argv) == 2:
        SERVER_HOST = '127.0.0.1'
        SERVER_PORT = int(sys.argv[1])
    else:
        print("Usage: client.py <port> <user> <pass>")
        return

    client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(client_socket.recv(BUFFER_SIZE).decode())

    data_socket = None

    while True:
        command = input("Enter command: ")
        client_socket.sendall(command.encode())

        if command.startswith('PASV'):
            response = client_socket.recv(BUFFER_SIZE).decode()
            print("Server response:", response)
            if response.startswith('230'):
                client_socket.sendall("TYPE I\r\n".encode())
                client_socket.sendall("MODE S\r\n".encode())
                client_socket.sendall("STRU F\r\n".encode())
            data_port = parse_pasv_response(response)
            data_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
            data_socket.connect((SERVER_HOST, data_port))

        elif data_socket:
            response = client_socket.recv(BUFFER_SIZE).decode()
            print("Server response:", response)
            if response.startswith('150'):
                if command.startswith('LIST'):
                    receive_list(data_socket)
                elif command.startswith('RETR') or command.startswith('STOR'):
                    filename = command.split()[1]
                    if command.startswith('RETR'):
                        receive_file(data_socket, filename)
                    elif command.startswith('STOR'):
                        send_file(data_socket, filename)
                data_socket.close()
                data_socket = None

        else:
            response = client_socket.recv(BUFFER_SIZE).decode()
            print("Server response:", response)

        if command == 'QUIT':
            break

    client_socket.close()

def parse_pasv_response(response):
    parts = response.split('(')[1].split(')')[0].split(',')
    ip_address = '.'.join(parts[:4])
    port = (int(parts[4]) * 256) + int(parts[5])
    return port

def send_file(conn, filename):
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            conn.sendall(data)

def receive_file(conn, filename):
    with open(filename, 'wb') as f:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)

def receive_list(conn):
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        print(data.decode(), end='')

if __name__ == "__main__":
    main()
