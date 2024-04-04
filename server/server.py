# Import os module for operating system-related functionalities
import os
# Import shutil module for recursive deletion of a directory
import shutil
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
    150: '150 File status okay; about to open data connection.\r\n',
    200: '200 Command okay.\r\n',
    214: '214 Help message.\r\n',
    230: '230 User logged in, proceed.\r\n',
    331: '331 User name okay, need password.\r\n',
    401: '401 Unauthorized, you are not logged in.\r\n',
    430: '430 Invalid username or password.\r\n',
    500: '500 Syntax error, command unrecognized.\r\n',
    503: '503 Use PASV command to establish a data connection\r\n',
    530: '530 Not logged in.\r\n',
    550: '550 Requested action not taken.\r\n',
}


# Function to handle client connections
def handle_client(conn):
    # Initialize authentication status, connection mode, and user information
    authenticated = False
    data_conn = None
    user = None

    # Authentication loop
    while not authenticated:
        # Receive and decode command from client
        command = conn.recv(BUFFER_SIZE).decode()
        # Split command into parts
        cmd_parts = command.split()
        # Check if command is 'USER'
        if cmd_parts[0] == 'USER':
            try:
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
            except IndexError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASS' and user:
            try:
                # Check if password matches the username
                if USERS[user] == cmd_parts[1]:
                    authenticated = True
                    response = REPLIES[230]
                    conn.sendall(response.encode())

                    # Receive and decode client's transfer type, mode, and
                    # structure
                    conn.recv(BUFFER_SIZE).decode().split()[1]
                    conn.sendall(REPLIES[200].encode())
                    conn.recv(BUFFER_SIZE).decode().split()[1]
                    conn.sendall(REPLIES[200].encode())
                    conn.recv(BUFFER_SIZE).decode().split()[1]
                    conn.sendall(REPLIES[200].encode())
                else:
                    response = REPLIES[530]
            except IndexError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'QUIT':
            response = REPLIES[200]
            conn.sendall(response.encode())
            break
        else:
            response = REPLIES[401]
            conn.sendall(response.encode())
    print(f'User {user} is connected!')

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
            except (FileNotFoundError, IndexError):
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'CDUP':
            # Move one directory up
            os.chdir("..")
            response = REPLIES[200]
            conn.sendall(response.encode())
        elif cmd_parts[0] == 'MKD':
            try:
                # Create a new directory
                os.mkdir(cmd_parts[1])
                response = f"257 Directory created: {cmd_parts[1]}"
                conn.sendall(response.encode())
            except IndexError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'RMD':
            try:
                # Remove specified directory
                shutil.rmtree(cmd_parts[1])
                response = f"250 Directory deleted: {cmd_parts[1]}"
                conn.sendall(response.encode())
            except IndexError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'DELE':
            try:
                # Delete a file
                os.remove(cmd_parts[1])
                response = f"250 File deleted: {cmd_parts[1]}"
                conn.sendall(response.encode())
            except IndexError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'PASV':
            try:
                # Enter passive mode for data connection
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.bind((SERVER_HOST, 0))
                data_socket.listen(1)
                data_port = data_socket.getsockname()[1]
                ip_address = SERVER_HOST.replace('.', ',')
                response = f"227 Entering Passive Mode ({ip_address},{ data_port // 256},{data_port % 256}).\r\n"
                conn.sendall(response.encode())
                data_conn, _ = data_socket.accept()
            except ConnectionAbortedError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'LIST':
            try:
                if data_conn:
                    # Send directory listing to the client
                    response = REPLIES[150]
                    conn.sendall(response.encode())
                    send_list(data_conn)
                    # Close data connection and set it to None
                    data_conn.close()
                    data_conn = None
                else:
                    # Send response to open a data connection first
                    response = REPLIES[503]
                    conn.sendall(response.encode())
            except OSError:
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'RETR':
            # Check if the command is 'RETR' (retrieve)
            try:
                # Retrieve a file from the server
                filename = cmd_parts[1]
                if os.path.exists(filename):
                    if data_conn:
                        # Data connection established, send file
                        response = REPLIES[150]
                        conn.sendall(response.encode())
                        send_file(data_conn, filename)
                        # Close data connection and set it to None
                        data_conn.close()
                        data_conn = None
                    else:
                        # Data connection not established
                        response = REPLIES[503]
                        conn.sendall(response.encode())
                else:
                    # File not found
                    response = REPLIES[550]
                    conn.sendall(response.encode())
            except (IndexError, OSError):
                # Missing filename argument
                response = REPLIES[550]
                conn.sendall(response.encode())
        elif cmd_parts[0] == 'STOR':
            # Check if the command is 'STOR' (store)
            try:
                if data_conn:
                    # Store a file on the server
                    filename = cmd_parts[1]
                    response = REPLIES[150]
                    conn.sendall(response.encode())
                    receive_file(data_conn, filename)
                    # Close data connection and set it to None
                    data_conn.close()
                    data_conn = None
                else:
                    # Data connection not established
                    response = REPLIES[503]
                    conn.sendall(response.encode())
            except (IndexError, OSError):
                # Missing filename argument
                response = REPLIES[550]
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
            # Invalid command
            response = REPLIES[500]
            conn.sendall(response.encode())

        print(f"{user}: {' '.join(cmd_parts)}")


# Function to send a file to the client
def send_file(conn, filename):
    # Open file in binary mode and send it to the client
    with open(filename, 'rb') as f:
        # Read data from the file and send it to the client
        while True:
            # Read a chunk of data from the file
            data = f.read(BUFFER_SIZE)
            # If no data read, exit loop
            if not data:
                break
            # Send the data chunk to the client
            conn.sendall(data)


# Function to receive a file from the client
def receive_file(conn, filename):
    # Open the file in binary write mode
    with open(filename, 'wb') as f:
        # Loop until there's no more data to receive
        while True:
            # Receive data from the client
            data = conn.recv(BUFFER_SIZE)
            # If no data received, exit loop
            if not data:
                break
            # Write received data to the file
            f.write(data)


def send_list(data_conn):
    # Send directory listing to the client
    dir_output = os.popen('dir').read().replace('\n', '\r\n')
    data_conn.sendall(dir_output.encode())


# Main function to start the FTP server
def main():
    # Declare global variables
    global SERVER_HOST, SERVER_PORT
    # Check if server port is specified in command-line arguments
    if len(sys.argv) == 2:
        SERVER_PORT = int(sys.argv[1])
    else:
        # Print usage message if the port number is not provided
        print("Usage: server.py <port>")
        return

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
        conn.sendall(f"220 Welcome to NSCOM01 FTP server!\r\n".encode())
        print(f"Connection from {addr}")
        # Spawn a new thread to handle client connection
        threading.Thread(target=handle_client, args=(conn,)).start()


# Check if the script is being run directly
if __name__ == "__main__":
    # Call the main function
    main()
