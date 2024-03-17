set port=21

start cmd /k "title Server && cd server && server.py %port%" && start cmd /k "title Client && cd client && client.py %port%"