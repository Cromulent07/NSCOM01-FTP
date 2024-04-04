import os
import socket
import threading

class FTPServer:
    SERVER = '127.0.0.1'
    BUFFER_SIZE = 4096
    USERS = {
        "john": "1234",
        "jane": "5678",
        "joe": "qwerty",
    }

    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.bind((self.SERVER, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.SERVER}:{self.port}")

        while True:
            conn, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            client_handler = FTPClientHandler(conn, self.SERVER)
            threading.Thread(target=client_handler.handle_client, daemon=True).start()

class FTPClientHandler:
    def __init__(self, connection, server_ip):
        self.connection = connection
        self.server_ip = server_ip
        self.is_authenticated = False
        self.user = None
        self.current_directory = os.getcwd()
        self.data_socket = None

    def send_response(self, message):
        self.connection.sendall(message.encode())

    def handle_client(self):
        self.send_response("220 Service Ready for User")
        while True:
            command = self.connection.recv(FTPServer.BUFFER_SIZE).decode().strip()
            if not command:
                continue
            print(f"Received command: {command}")
            self.process_command(command)

    def process_command(self, command):
        parts = command.split(maxsplit=1)
        cmd = parts[0].upper()
        argument = parts[1].strip('"') if len(parts) > 1 else None

        command_handlers = {
            'USER': self.handle_user,
            'PASS': self.handle_pass,
            'PWD': self.handle_pwd,
            'CWD': self.handle_cwd,
            'QUIT': self.handle_quit,
            'CDUP': self.handle_cdup,
            'MKD': self.handle_mkd,
            'RMD': self.handle_rmd,
            'PASV': self.handle_pasv,
            'LIST': self.handle_list,
            'RETR': self.handle_retr,
            'DELE': self.handle_dele,
            'STOR': self.handle_stor,
            'HELP': self.handle_help
        }

        handler = command_handlers.get(cmd)
        if handler:
            handler(argument)
        else:
            self.send_response("500 Syntax error, command unrecognized")

    def handle_user(self, username, *args):
        if username in FTPServer.USERS:
            self.user = username
            self.send_response("331 Username OK, need password")
        else:
            self.send_response("430 Invalid username or password")

    def handle_pass(self, password, *args):
        if self.user and FTPServer.USERS.get(self.user) == password:
            self.is_authenticated = True
            self.send_response("230 User logged in, proceed")
        else:
            self.send_response("530 Not logged in")

    def handle_pwd(self, *args):
        if self.is_authenticated:
            self.send_response(f"257 \"{self.current_directory}\" is the current directory")
        else:
            self.send_response("530 Not logged in")

    def handle_cwd(self, directory, *args):
        if self.is_authenticated:
            if directory:
                full_path = os.path.join(self.current_directory, directory)
                if os.path.isdir(full_path):
                    self.current_directory = full_path
                    self.send_response(f"250 Directory changed to {full_path}")
                else:
                    self.send_response(f"550 Directory not found: {directory}")
            else:
                self.send_response("501 Syntax error in parameters or arguments.")
        else:
            self.send_response("530 Not logged in")

    def handle_cdup(self, *args):
        if self.is_authenticated:
            self.current_directory = os.path.dirname(self.current_directory)
            self.send_response("200 Command okay, changed to parent directory")
        else:
            self.send_response("530 Not logged in")

    def handle_mkd(self, directory, *args):
        if self.is_authenticated:
            if directory:
                full_path = os.path.join(self.current_directory, directory)
                if not os.path.exists(full_path):
                    os.mkdir(full_path)
                    self.send_response(f"257 \"{directory}\" directory created")
                else:
                    self.send_response(f"550 Directory already exists: {directory}")
            else:
                self.send_response("501 Syntax error in parameters or arguments.")
        else:
            self.send_response("530 Not logged in")

    def handle_rmd(self, directory, *args):
        if self.is_authenticated:
            if directory:
                full_path = os.path.join(self.current_directory, directory)
                if os.path.isdir(full_path):
                    os.rmdir(full_path)
                    self.send_response(f"250 \"{directory}\" directory removed")
                else:
                    self.send_response(f"550 Directory not found: {directory}")
            else:
                self.send_response("501 Syntax error in parameters or arguments.")
        else:
            self.send_response("530 Not logged in")

    def handle_pasv(self, *args):
        if self.is_authenticated:
            if self.data_socket:
                self.data_socket.close()
            self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.data_socket.bind((self.server_ip, 0))
            self.data_socket.listen(1)
            ip, port = self.data_socket.getsockname()
            ip_formatted = ip.replace('.', ',')
            p1, p2 = divmod(port, 256)
            self.send_response(f"227 Entering Passive Mode ({ip_formatted},{p1},{p2}).")
        else:
            self.send_response("530 Not logged in")

    def handle_list(self, *args):
        if self.is_authenticated:
            file_list = os.listdir(self.current_directory)
            file_list_string = '\n'.join(file_list)
            self.send_response(f"200 Command okay.\n{file_list_string}")
        else:
            self.send_response("530 Not logged in")

    def handle_retr(self, filename, *args):
        if self.is_authenticated:
            file_path = os.path.join(self.current_directory, filename)
            if os.path.exists(file_path):
                self.send_response("150 Opening data connection")
                with open(file_path, 'rb') as file:
                    data = file.read(FTPServer.BUFFER_SIZE)
                    while data:
                        self.connection.sendall(data)
                        data = file.read(FTPServer.BUFFER_SIZE)
                self.send_response("226 Transfer complete")
            else:
                self.send_response("550 File not found")
        else:
            self.send_response("530 Not logged in")

    def handle_dele(self, filename, *args):
        if self.is_authenticated:
            file_path = os.path.join(self.current_directory, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.send_response(f"250 \"{filename}\" deleted")
            else:
                self.send_response("550 File not found")
        else:
            self.send_response("530 Not logged in")

    def handle_stor(self, filename, *args):
        if self.is_authenticated:
            file_path = os.path.join(self.current_directory, filename)
            self.send_response("150 Ok to send data")
            with open(file_path, 'wb') as file:
                data = self.connection.recv(FTPServer.BUFFER_SIZE)
                while data:
                    file.write(data)
                    data = self.connection.recv(FTPServer.BUFFER_SIZE)
            self.send_response("226 Transfer complete")
        else:
            self.send_response("530 Not logged in")

    def handle_help(self, *args):
        help_text = '''
        USER <username>: Log in as <username>
        PASS <password>: Provide <password> for authentication
        PWD: Show current directory path
        CWD <path>: Change working directory to <path>
        CDUP: Change to parent directory
        MKD <directory>: Make a new directory
        RMD <directory>: Remove a directory
        PASV: Enter passive mode
        LIST: List files in the current directory
        RETR <filename>: Retrieve a file
        DELE <filename>: Delete a file
        STOR <filename>: Store a file
        HELP: Show this help message
        QUIT: Disconnect
        '''
        self.send_response(f"214-Here are the FTP commands:\n{help_text}")

    def handle_quit(self, *args):
        self.send_response("221 Goodbye")
        self.connection.close()

def main():
    port = int(input("Enter port: "))
    server = FTPServer(port)
    server.start()

if __name__ == "__main__":
    main()
