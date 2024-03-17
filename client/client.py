# Import sys module for system-specific parameters and functions
import sys
# Import time module for time-related functions
import time
# Import socket module and alias it as s for network communication
import socket as s

# Define constant BUFFER_SIZE for the size of data buffer
BUFFER_SIZE = 4096
# Define constant SERVER_HOST for the server IP address
SERVER_HOST = '127.0.0.1'


# Define the main function to control the FTP client logic
def main():
    # Define global variable SERVER_PORT
    global SERVER_PORT
    # Check if the user has provided the port number as a command-line argument
    if len(sys.argv) == 2:
        # Get the port number from the command-line argument
        SERVER_PORT = int(sys.argv[1])
    else:
        # Print usage message if the port number is not provided
        print("Usage: client.py <port>")
        return

    # Create a TCP socket for the client
    client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
    # Connect the client socket to the server host and port
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    # Receive initial response from server and decode it
    print(client_socket.recv(BUFFER_SIZE).decode())

    # Initialize data socket
    data_socket = None

    try:
        # Main loop to interact with the server
        while True:
            # Prompt user to enter command
            command = input("Enter command: ") + "\r\n"
            # Send command to server
            client_socket.sendall(command.encode())
            # Receive response from server and decode it
            response = client_socket.recv(BUFFER_SIZE).decode()

            # Handle different types of server responses
            if response.startswith('230'):
                # Print server response
                print("Server response:", response)
                # Set FTP connection modes
                set_connection_modes(client_socket)

            elif command.startswith('PASV'):
                # Print server response
                print("Server response:", response)
                # Parse PASV response and extract data port
                data_port = parse_pasv_response(response)
                # Create data socket and connect to server host and data port
                data_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
                data_socket.connect((SERVER_HOST, data_port))

            elif data_socket:
                # Print server response
                print("Server response:", response)
                if response.startswith('150'):
                    # Handle data transfer based on the command
                    handle_data_transfer(data_socket, command)
                    # Close data socket after data transfer
                    data_socket.close()
                    # # Reset data socket to None
                    # data_socket = None
                else:
                    data_socket.close()

            else:
                # Print server response
                print("Server response:", response)

            # Check if the user wants to quit
            if command.strip() == 'QUIT':
                break
        client_socket.close()
    except (ConnectionResetError, OSError):
        # Close client socket
        client_socket.close()


# Function to set FTP connection modes
def set_connection_modes(client_socket):
    # Define FTP connection modes
    modes = ["TYPE I", "MODE S", "STRU F"]
    # Send each mode to server
    for mode in modes:
        client_socket.sendall((mode + "\r\n").encode())
        # Sleep for a short duration to avoid flooding the server
        time.sleep(0.1)
        # Receive response from server and decode it
        client_socket.recv(BUFFER_SIZE).decode()


# Function to parse PASV response and extract data port
def parse_pasv_response(response):
    # Split PASV response and extract parts
    parts = response.split('(')[1].split(')')[0].split(',')
    # Calculate data port
    port = (int(parts[4]) * 256) + int(parts[5])
    return port


# Function to handle data transfer based on the command
def handle_data_transfer(data_socket, command):
    if command.startswith('LIST'):
        # Receive directory listing from server
        receive_list(data_socket)
    elif command.startswith('RETR'):
        # Extract filename from command
        filename = command.split()[1]
        # Receive file from server
        receive_file(data_socket, filename)
    elif command.startswith('STOR'):
        # Extract filename from command
        filename = command.split()[1]
        # Send file to server
        send_file(data_socket, filename)


# Function to send a file to the server
def send_file(conn, filename):
    # Open file in binary mode for reading
    with open(filename, 'rb') as f:
        while True:
            # Read data from file
            data = f.read(BUFFER_SIZE)
            # Check if end of file is reached
            if not data:
                break
            # Send data to server
            conn.sendall(data)


# Function to receive a file from the server
def receive_file(conn, filename):
    # Open file in binary mode for writing
    with open(filename, 'wb') as f:
        while True:
            # Receive data from server
            data = conn.recv(BUFFER_SIZE)
            # Check if end of file is reached
            if not data:
                break
            # Write data to file
            f.write(data)


# Function to receive directory listing from the server
def receive_list(conn):
    while True:
        # Receive data from server
        data = conn.recv(BUFFER_SIZE)
        # Check if end of data is reached
        if not data:
            break
        # Decode and print received data
        print(data.decode(), end='')


# Check if the script is being run directly
if __name__ == "__main__":
    # Call the main function
    main()
