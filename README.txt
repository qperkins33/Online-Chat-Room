Student Name: Quin Perkins
Metropolitan Student ID 16423236
Student Class: ICS 460-02 Networks and Security
Assignment Name: Online Chat Room

Objective:
- The client will support two main functionalities: public messaging and direct messaging.
- The server should handle multiple simultaneous client connections.
- You will need to manage communication between the client and the server using appropriate message formats and multithreading techniques.
- The program will utilize Python 3 and TCP

Operations:
- PM (Public Message): The client sends a PM operation to broadcast a message to all active clients.
- DM (Direct Message): The client sends a DM operation to message a specific client.
- EX (Exit): The client sends an EX operation to close the connection (server updates its list of active clients and closes the connection).


Running the Application:

Dependencies: Installing Dependencies is not needed. 
Imports utilized are:
import threading
import sys
from socket import *
import json

Running the Server:
1. Open a terminal.
2. Navigate to the directory containing server.py
3. Run the server by executing: "python3 server.py 12000" in your terminal (or use alternative port number).

Running the Client:
1. Open a separate terminal.
2. Navigate to the directory containing client.py
3. Run the client by executing: "python3 client.py localhost 12000" in a separate terminal window (use the same port number chosen for the server).
4. Repeat steps 1-3 to create multiple clients.

Instructions for Testing the Chat Room Client:
1. Login/Registration: The client will prompt for a username and password. If the username does not exist, you’ll have an option to register. (Otherwise, use already existing login info: [user, pass])
2. Multiple Clients: Open multiple terminal windows and run client in each. Use unique usernames and test pm and dm.
3a. Sending Messages: Enter pm/dm and press return. You will then be prompted for your next input.
3b. Example for dm inputs: (dm [press enter] -> recipient_username [press enter] -> message [press enter])
3c. Example for pm inputs: (pm [press enter] -> message [press enter])
4. Enter ex to exit the chat.

Instructions for closing the server:
1. After all users have exited, in server's terminal, execute ^C to shut it down.
