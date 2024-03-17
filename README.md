
<div style="text-align: justify">

# File Transfer Protocol (FTP)

## Background
The goal of this project is to deepen your understanding on network application protocols through network socket programming. At this point, you have implemented simple client-server (text and file exchange) program in CSNETWK and TFTP client program in MP#1.

In this project, you will develop FTP client and FTP server network application. Developed in 1971, the File Transfer Protocol (FTP) is one of the oldest protocols still in common use today. FTP’s development predates TCP/IP, yet the protocol still works fairly well on the modern internet.

FTP is a client-server oriented protocol for uploading, downloading, and managing files. The FTP server’s job is to listen for incoming connections from clients and then respond to their requests. These requests include all common file and directory operations, such as listing the files in a directory, making and deleting directories, uploading files from the client machine to the server, and downloading files from the server to the client machines. FTP clients connect to FTP servers and issue commands to tell the server what to do.

## Instructions
Double-click on "run.bat" to execute the batch file. This will start both the server and the client simultaneously.

Or if you prefer to run it manually, you need to open two command prompts in the project's directory and run the following commands.
The following commands will run the server and the client on port 21.

### Server
```cmd
python server\server.py 21
```

### Client
```cmd
python client\client.py 21
```

## Requirements
- Implement an FTP Server program that listens and provides service to FTP clients.
- Implement an FTP Client Program that sends a request to FTP Server application.
- COMMAND is typically a three or four letter command, in all caps, that tells the FTP server to perform some action. Depending on what command is sent, additional parameters may also be required. Note that parameters should not be surrounded by < and > symbols; we use those to denote things in messages that are optional. All FTP requests end with \r\n.
  - https://en.wikipedia.org/wiki/List_of_FTP_server_return_codesLinks to an external site.
- Run only on command line with the following request messages:
  - **USER** – username
  - **PASS** – password
  - **PWD** – print working directory
  - **CWD** – change working directory
  - **CDUP** – change the client’s current working directory to the immediate parent directory of the current working directory
  - **MKD** – make directory
  - **RMD** – remove directory
  - **PASV** - client initiates a command channel (control connection) to the server. However, instead of sending the PORT command, it sends the PASV command, which requests a server port to connect to for data transmission. When the FTP server replies, it indicates what data port number it has opened for the ensuing data transfer.
  - **LIST** – print current list of files
  - **RETR** – retrieve/get file(s)
  - **DELE** – delete files
  - **STOR** – upload data at the server site
  - **HELP** – returns available commands for the client
  - **TYPE** – transfer mode (ASCII/Binary)
  - **MODE** – sets the transfer mode (Stream, Block, or Compressed)
  - **STRU** – set file transfer structure
  - **QUIT** – close socket
- You may use higher port numbers for control and data connections to avoid conflict with your operating system.

## Implementation
- **Server and client programs are running on a single machine only.**
- **Server side**
  - Create an array or database of user + password information.
    - Use the following default accounts
      - USER: john PASS: 1234
      - USER: jane PASS: 5678
      - USER: joe PASS: qwerty
    - Define the file location path (user-input or hard-coded).
    - Run the server on the defined port number x.
    - Server listens to incoming client requests on port number x.
    - Sends appropriate response code to client once its successfully connected.
    - Send a banner message to client once connected. (e.g. Welcome to NSCOM01 FTP server).
- **Client side**
  - Connect to the server using USER, PASS.
  - Set the following before proceeding to upload and download files. You may not print this via CLI and run in the background.
    - TYPE I\r\n - Set the connection to 8-bit binary data mode (as opposed to 7-bit ASCII or 36-bit EBCDIC).
    - MODE S\r\n - Set the connection to stream mode
    - STRU F\r\n - Set the connection to file-oriented mode
  - User can perform the commands above.
</div>