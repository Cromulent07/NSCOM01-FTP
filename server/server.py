# Import os module for operating system-related functionalities
import os
# Import sys module for system-specific parameters and functions
import sys
# Import socket module for network communication
import socket
# Import threading module for concurrent execution
import threading

# Define constant SERVER_HOST for the server IP address
SERVER_HOST = '127.0.0.1'
# Define constant SERVER_PORT for the server port
SERVER_PORT = 21
# Define constant BUFFER_SIZE for the size of data buffer
BUFFER_SIZE = 4096

# Define dictionary USERS for storing user credentials
USERS = {
    "john": "1234",
    "jane": "5678",
    "joe": "qwerty",
}

# Define HELP string for providing available commands
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

# Define dictionary REPLIES for FTP server replies
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


# Function to handle client connections
def handle_client(conn):
    # Initialize authentication status, connection mode, and user information
    authenticated = False
    pasv_mode = False
    data_conn = None
    type = None
    mode = None
    structure = None
    user = None

    # Authentication loop
    while not authenticated:
        # Receive and decode command from client
        command = conn.recv(BUFFER_SIZE).decode()
        # Split command into parts
        cmd_parts = command.split()
        # Check if command is 'USER'
        if cmd_parts[0] == 'USER':
            # Check if username exists in the list of authorized users
            if cmd_parts[1] in USERS:
                user = cmd_parts[1]
                # Send authentication response to client
                response = REPLIES[331]
                conn.sendall(response.encode())
            else:
                # Send error response to client
                response = REPLIES[430]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASS' and user:
            # Check if password matches the username
            if USERS[user] == cmd_parts[1]:
                authenticated = True
                response = REPLIES[230]
                conn.sendall(response.encode())

                # Receive and decode client's transfer type, mode, and
                # structure
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

    # Main command loop
    while True:
        # Receive and decode command from client
        command = conn.recv(BUFFER_SIZE).decode()

        # If no command received, break the loop
        if not command:
            break
        cmd_parts = command.split()
        if cmd_parts[0] == 'PWD':
            # Get current working directory and send it to the client
            current_directory = os.getcwd()
            response = f"257 {current_directory}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'CWD':
            try:
                # Change directory to the specified one
                os.chdir(cmd_parts[1])
                response = f"250 Directory changed to {cmd_parts[1]}"
                conn.sendall(response.encode())
            except FileNotFoundError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'CDUP':
            # Move one directory up
            os.chdir("..")
            response = REPLIES[200]
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'MKD':
            # Create a new directory
            os.mkdir(cmd_parts[1])
            response = f"257 Directory created: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'RMD':
            # Remove specified directory
            os.rmdir(cmd_parts[1])
            response = f"250 Directory deleted: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASV':
            # Enter passive mode for data connection
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind((SERVER_HOST, 0))
            data_socket.listen(1)
            data_port = data_socket.getsockname()[1]
            ip_address = SERVER_HOST.replace('.', ',')
            response = f"227 Entering Passive Mode ({ip_address},{
                data_port // 256},{data_port % 256}).\r\n"
            conn.sendall(response.encode())
            data_conn, _ = data_socket.accept()
        elif cmd_parts[0] == 'LIST':
            # Send directory listing to the client
            dir_output = os.popen('dir').read().replace('\n', '\r\n')
            response = f"{REPLIES[200]}\r\n{dir_output}\r\n"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'RETR':
            # Retrieve a file from the server
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
            # Delete a file
            os.remove(cmd_parts[1])
            response = f"250 File deleted: {cmd_parts[1]}"
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'STOR':
            if data_conn:
                # Store a file on the server
                filename = cmd_parts[1]
                response = REPLIES[150]
                conn.sendall(response.encode())
                receive_file(data_conn, filename)
                data_conn.close()
            else:
                response = REPLIES[425]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'HELP':
            # Provide help information
            response = REPLIES[214] + HELP
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'QUIT':
            # Quit the session
            response = REPLIES[200]
            conn.sendall(response.encode())
            break
        else:
            response = REPLIES[500]
            conn.sendall(response.encode())


# Function to send a file to the client
def send_file(conn, filename):
    # Open file in binary mode and send it to the client
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            conn.sendall(data)


# Function to receive a file from the client
def receive_file(conn, filename):
    # Receive file from the client and write it to disk
    with open(filename, 'wb') as f:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)


# Main function to start the FTP server
def main():
    # Declare global variables
    global SERVER_HOST, SERVER_PORT
    # Check if server port is specified in command-line arguments
    if len(sys.argv) == 2:
        SERVER_PORT = int(sys.argv[1])

    # Create a server socket and bind it to host and port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)

    # Print server information
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    # Main server loop
    while True:
        # Accept incoming connections
        conn, addr = server_socket.accept()
        # Send initial response to client
        conn.sendall(REPLIES[220].encode())
        print(f"Connection from {addr}")
        # Spawn a new thread to handle client connection
        threading.Thread(target=handle_client, args=(conn,)).start()


# Check if the script is being run directly
if __name__ == "__main__":
    # Call the main function
    main()
