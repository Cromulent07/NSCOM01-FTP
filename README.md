# NSCOM01-FTP

## TODO
- [x] USER – username
- [x] PASS – password
- [x] PWD – print working directory
- [x] CWD – change working directory
- [x] CDUP – change the client’s current working directory to the immediate parent directory of the current working directory
- [x] MKD – make directory
- [x] RMD – remove directory
- [ ] PASV - client initiates a command channel (control connection) to the server. However, instead of sending the PORT command, it sends the PASV command, which requests a server port to connect to for data transmission. When the FTP server replies, it indicates what data port number it has opened for the ensuing data transfer.
- [ ] LIST – print current list of files
- [ ] RETR – retrieve/get file(s)
- [ ] DELE – delete files
- [ ] STOR – upload data at the server site
- [ ] HELP – returns available commands for the client
- [ ] TYPE – transfer mode (ASCII/Binary)
- [ ] MODE – sets the transfer mode (Stream, Block, or Compressed)
- [ ] STRU – set file transfer structure
- [x] QUIT – close socket