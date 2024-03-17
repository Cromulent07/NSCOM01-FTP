import os
import sys
import socket
import threading

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 21
BUFFER_SIZE = 4096

USERS = {
    "john": "1234",
    "jane": "5678",
    "joe": "qwerty",
    "q": "q"
}

HELP = '''
USER - username
PASS - password
PWD  - print working directory
CWD  - change working directory
CDUP - change the client's current working directory to the immediate parent
       directory of the current working directory
MKD  - make directory
RMD  - remove directory
PASV - client initiates a command channel (control connection) to the server.
LIST - print current list of files
RETR - retrieve/get file(s)
DELE - delete files
STOR - upload data at the server site
HELP - returns available commands for the client
TYPE - transfer mode (ASCII/Binary)
MODE - sets the transfer mode (Stream, Block, or Compressed)
STRU - set file transfer structure
QUIT - close socket\r\n'''

REPLIES = {
    110: '110 Restart marker reply.\r\n',
    120: '120 Service ready in nnn minutes.\r\n',
    125: '125 Data connection already open; transfer starting.\r\n',
    150: '150 File status okay; about to open data connection.\r\n',
    200: '200 Command okay.\r\n',
    202: '202 Command not implemented, superfluous at this site.\r\n',
    211: '211 System status, or system help reply.\r\n',
    212: '212 Directory status.\r\n',
    213: '213 File status.\r\n',
    214: '214 Help message.\r\n',
    215: '215 NAME system type.\r\n',
    220: '220 Service ready for new user.\r\n',
    221: '221 Service closing control connection.\r\n',
    225: '225 Data connection open; no transfer in progress.\r\n',
    226: '226 Closing data connection.\r\n',
    227: '227 Entering Passive Mode (h1,h2,h3,h4,p1,p2).\r\n',
    230: '230 User logged in, proceed.\r\n',
    250: '250 Requested file action okay, completed.\r\n',
    257: '257 "PATHNAME" created.\r\n',
    331: '331 User name okay, need password.\r\n',
    332: '332 Need account for login.\r\n',
    350: '350 Requested file action pending further information.\r\n',
    401: '401 Unauthorized, you are not logged in.\r\n',
    421: '421 Service not available, closing control connection.\r\n',
    425: '425 Can\'t open data connection.\r\n',
    426: '426 Connection closed; transfer aborted.\r\n',
    430: 'Invalid username or password.\r\n',
    450: '450 Requested file action not taken.\r\n',
    451: '451 Requested action aborted: local error in processing.\r\n',
    452: '452 Requested action not taken.\r\n',
    500: '500 Syntax error, command unrecognized.\r\n',
    501: '501 Syntax error in parameters or arguments.\r\n',
    502: '502 Command not implemented.\r\n',
    503: '503 Bad sequence of commands.\r\n',
    504: '504 Command not implemented for that parameter.\r\n',
    530: '530 Not logged in.\r\n',
    532: '532 Need account for storing files.\r\n',
    550: '550 Requested action not taken.\r\n',
    551: '551 Requested action aborted: page type unknown.\r\n',
    552: '552 Requested file action aborted.\r\n',
    553: '553 Requested action not taken.\r\n',
}


def handle_client(conn):
    authenticated = False
    pasv_mode = False
    data_conn = None
    type = None
    mode = None
    structure = None
    user = None

    while not authenticated:
        command = conn.recv(BUFFER_SIZE).decode()
        cmd_parts = command.split()
        if cmd_parts[0] == 'USER':
            if cmd_parts[1] in USERS:
                user = cmd_parts[1]
                response = REPLIES[331]
                conn.sendall(response.encode())
            else:
                response = REPLIES[430]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASS' and user:
            if USERS[user] == cmd_parts[1]:
                authenticated = True
                response = REPLIES[230]
                conn.sendall(response.encode())

                type = conn.recv(BUFFER_SIZE).decode().split()[1]
                conn.sendall(REPLIES[200].encode())
                mode = conn.recv(BUFFER_SIZE).decode().split()[1]
                conn.sendall(REPLIES[200].encode())
                structure = conn.recv(BUFFER_SIZE).decode().split()[1]
                conn.sendall(REPLIES[200].encode())
            else:
                response = REPLIES[530]
        elif cmd_parts[0] == 'QUIT':
            response = REPLIES[200]
            conn.sendall(response.encode())
            break
        else:
            response = REPLIES[401]
            conn.sendall(response.encode())

    while True:
        command = conn.recv(BUFFER_SIZE).decode()

        if not command:
            break
        cmd_parts = command.split()
        if cmd_parts[0] == 'PWD':
            current_directory = os.getcwd()
            response = f"257 {current_directory}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'CWD':
            try:
                os.chdir(cmd_parts[1])
                response = f"250 Directory changed to {cmd_parts[1]}"
                conn.sendall(response.encode())
            except FileNotFoundError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'CDUP':
            os.chdir("..")
            response = REPLIES[200]
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'MKD':
            os.mkdir(cmd_parts[1])
            response = f"257 Directory created: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'RMD':
            os.rmdir(cmd_parts[1])
            response = f"250 Directory deleted: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASV':
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind((SERVER_HOST, 0))
            data_socket.listen(1)
            data_port = data_socket.getsockname()[1]
            ip_address = SERVER_HOST.replace(
                '.', ',')
            response = f"227 Entering Passive Mode ({ip_address},{
                data_port // 256},{data_port % 256}).\r\n"
            conn.sendall(response.encode())
            data_conn, _ = data_socket.accept()
        elif cmd_parts[0] == 'LIST':
            dir_output = os.popen('dir').read().replace(
                '\n', '\r\n')
            response = f"{REPLIES[200]}\r\n{dir_output}\r\n"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'RETR':
            filename = cmd_parts[1]
            if os.path.exists(filename):
                if data_conn:
                    response = REPLIES[150]
                    conn.sendall(response.encode())
                    send_file(data_conn, filename)
                    data_conn.close()
                else:
                    response = REPLIES[425]
                    conn.sendall(response.encode())
            else:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'DELE':
            os.remove(cmd_parts[1])
            response = f"250 File deleted: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'STOR':
            if data_conn:
                filename = cmd_parts[1]
                response = REPLIES[150]
                conn.sendall(response.encode())
                receive_file(data_conn, filename)
                data_conn.close()
            else:
                response = REPLIES[425]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'HELP':
            response = REPLIES[214] + HELP
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'QUIT':
            response = REPLIES[200]
            conn.sendall(response.encode())
            break
        else:
            response = REPLIES[500]
            conn.sendall(response.encode())


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


def main():
    global SERVER_HOST, SERVER_PORT
    if len(sys.argv) == 2:
        SERVER_PORT = int(sys.argv[1])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)

    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        conn, addr = server_socket.accept()
        conn.sendall(REPLIES[220].encode())
        print(f"Connection from {addr}")
        threading.Thread(target=handle_client, args=(conn,)).start()


if __name__ == "__main__":
    main()
