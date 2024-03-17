import sys
import time
import socket as s

BUFFER_SIZE = 4096
SERVER_HOST = '127.0.0.1'


def main():
    global SERVER_PORT
    if len(sys.argv) == 2:
        SERVER_PORT = int(sys.argv[1])
    else:
        print("Usage: client.py <port>")
        return

    client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(client_socket.recv(BUFFER_SIZE).decode())

    data_socket = None

    while True:
        command = input("Enter command: ") + "\r\n"
        client_socket.sendall(command.encode())
        response = client_socket.recv(BUFFER_SIZE).decode()

        if response.startswith('230'):
            print("Server response:", response)
            set_connection_modes(client_socket)

        elif command.startswith('PASV'):
            print("Server response:", response)
            data_port = parse_pasv_response(response)
            data_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
            data_socket.connect((SERVER_HOST, data_port))

        elif data_socket:
            print("Server response:", response)
            if response.startswith('150'):
                handle_data_transfer(client_socket, data_socket, command)
                data_socket.close()
                data_socket = None

        else:
            print("Server response:", response)

        if command.strip() == 'QUIT':
            break

    client_socket.close()


def set_connection_modes(client_socket):
    modes = ["TYPE I", "MODE S", "STRU F"]
    for mode in modes:
        client_socket.sendall((mode + "\r\n").encode())
        time.sleep(0.1)
        client_socket.recv(BUFFER_SIZE).decode()


def parse_pasv_response(response):
    parts = response.split('(')[1].split(')')[0].split(',')
    ip_address = '.'.join(parts[:4])
    port = (int(parts[4]) * 256) + int(parts[5])
    return port


def handle_data_transfer(client_socket, data_socket, command):
    if command.startswith('LIST'):
        receive_list(data_socket)
    elif command.startswith('RETR'):
        filename = command.split()[1]
        receive_file(data_socket, filename)
    elif command.startswith('STOR'):
        filename = command.split()[1]
        send_file(data_socket, filename)


def send_file(conn, filename):
    with open(filename, 'rb') as f:
        print(1)
        while True:
            data = f.read(BUFFER_SIZE)
            print(2)
            if not data:
                break
            conn.sendall(data)
            print(3)


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
