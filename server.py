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
    "joe": "qwerty"
}

REPLIES = {
    110: '110 Restart marker reply.',
    120: '120 Service ready in nnn minutes.',
    125: '125 Data connection already open; transfer starting.',
    150: '150 File status okay; about to open data connection.',
    200: '200 Command okay.',
    202: '202 Command not implemented, superfluous at this site.',
    211: '211 System status, or system help reply.',
    212: '212 Directory status.',
    213: '213 File status.',
    214: '214 Help message.',
    215: '215 NAME system type.',
    220: '220 Service ready for new user.',
    221: '221 Service closing control connection.',
    225: '225 Data connection open; no transfer in progress.',
    226: '226 Closing data connection.',
    227: '227 Entering Passive Mode (h1,h2,h3,h4,p1,p2).',
    230: '230 User logged in, proceed.',
    250: '250 Requested file action okay, completed.',
    257: '257 "PATHNAME" created.',
    331: '331 User name okay, need password.',
    332: '332 Need account for login.',
    350: '350 Requested file action pending further information.',
    401: '401 Unauthorized, you are not logged in.',
    421: '421 Service not available, closing control connection.',
    425: '425 Can\'t open data connection.',
    426: '426 Connection closed; transfer aborted.',
    430: 'Invalid username or password.',
    450: '450 Requested file action not taken.',
    451: '451 Requested action aborted: local error in processing.',
    452: '452 Requested action not taken.',
    500: '500 Syntax error, command unrecognized.',
    501: '501 Syntax error in parameters or arguments.',
    502: '502 Command not implemented.',
    503: '503 Bad sequence of commands.',
    504: '504 Command not implemented for that parameter.',
    530: '530 Not logged in.',
    532: '532 Need account for storing files.',
    550: '550 Requested action not taken.',
    551: '551 Requested action aborted: page type unknown.',
    552: '552 Requested file action aborted.',
    553: '553 Requested action not taken.',
}

def handle_client(conn):
    is_authorized = False
    data_conn = None
    user = ''

    # Authentication
    while not is_authorized:
        command = conn.recv(BUFFER_SIZE).decode()

        cmd_parts = command.split()
        if cmd_parts[0] == 'USER': # Implement USER command
            if cmd_parts[1] in USERS:
                user = cmd_parts[1]
                response = REPLIES[331]
            else:
                response = REPLIES[430]
        elif cmd_parts[0] == 'PASS' and user: # Implement PASS command
            if USERS[user]==cmd_parts[1]:
                is_authorized = True
                response = REPLIES[230]
            else:
                response = REPLIES[530]
        elif cmd_parts[0] == 'QUIT': # Implement QUIT command
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
        if cmd_parts[0] == 'PWD': # Implement PWD command
            current_directory = os.getcwd()
            response = f"257 {current_directory}"
        elif cmd_parts[0] == 'CWD': # Implement CWD command
            try:
                os.chdir(cmd_parts[1])
                response = f"250 Directory changed to {cmd_parts[1]}"
            except FileNotFoundError:
                response = REPLIES[550]
        elif cmd_parts[0] == 'CDUP': # Implement CDUP command
            os.chdir("..")
            response = REPLIES[200]
        elif cmd_parts[0] == 'MKD': # Implement MKD command
            os.mkdir(cmd_parts[1])
            response = f"257 Directory created: {cmd_parts[1]}"
        elif cmd_parts[0] == 'RMD': # Implement RMD command
            os.rmdir(cmd_parts[1])
            response = f"250 Directory deleted: {cmd_parts[1]}"
        elif cmd_parts[0] == 'PASV': # Create a new data socket
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind((SERVER_HOST, 0))  # Bind to any available port
            data_socket.listen(1)
            data_port = data_socket.getsockname()[1]  # Get the port number
            ip_address = SERVER_HOST.replace('.', ',')  # Convert IP address format
            response = f"227 Entering Passive Mode ({ip_address},{data_port // 256},{data_port % 256}).\r\n"
            conn.sendall(response.encode())
            # Accept the client connection on the data socket
            data_conn, _ = data_socket.accept()
        elif cmd_parts[0] == 'LIST': # Send directory listing over the data connection
            if data_conn:
                file_list = '\n'.join(os.listdir('.'))
                data_conn.sendall(file_list.encode())
                data_conn.close()  # Close the data connection
                response = REPLIES[226]
            else:
                response = REPLIES[425]
        elif cmd_parts[0] == 'RETR': # Implement RETR command
            filename = cmd_parts[1]
            if os.path.exists(filename):
                if data_conn:
                    response = REPLIES[150]
                    data_conn.sendall(response.encode())
                    send_file(data_conn, filename)
                    response = REPLIES[226]
                else:
                    response = REPLIES[425]
            else:
                response = REPLIES[550]
        elif cmd_parts[0] == 'DELE': # Implement DELE command
            os.remove(cmd_parts[1])
            response = f"250 File deleted: {cmd_parts[1]}"
        elif cmd_parts[0] == 'STOR': # Implement STOR command
            if data_conn:
                filename = cmd_parts[1]
                response = REPLIES[150]
                data_conn.sendall(response.encode())
                receive_file(data_conn, filename)
                response = REPLIES[226]
            else:
                response = REPLIES[425]
        elif cmd_parts[0] == 'HELP': # Implement HELP command
            response = REPLIES[214]
        elif cmd_parts[0] == 'TYPE': # Implement TYPE command
            response = REPLIES[200]
        elif cmd_parts[0] == 'MODE': # Implement MODE command
            response = REPLIES[200]
        elif cmd_parts[0] == 'STRU': # Implement STRU command
            response = REPLIES[200]
        elif cmd_parts[0] == 'QUIT': # Implement QUIT command
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
    global SERVER_HOST, SERVER_PORT  # Declare global variables
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
