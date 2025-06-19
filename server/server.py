import threading
import sys
from socket import *
import json

# In-memory storage for users (username -> password)
active_users = {}
USER_FILE = "users.json"

def load_users():
    """
    This function loads user credentials from the USER_FILE (JSON).

    Returns: Dictionary with usernames as keys and passwords as values (username -> password)
    """
    try:
        with open(USER_FILE, 'r') as openfile:
            json_object = json.load(openfile)
            return json_object
    except FileNotFoundError:
        # If file does not exist, return empty ictionary
        return {}

def save_users(users):
    """
    This function saves users to the USER_FILE.
    It overwrites each time (it does not append)
    """
    with open(USER_FILE, "w") as outfile:
        json.dump(users, outfile)

def handle_client(client_sock, addr):
    """
    This function handles communication with a client.

    It continuously recieves messages from the client.
    It decides what to do based on the command type sent.

    login: Checks if username and password is in USER_FILE
    register: Saves login info in USER_FILE as long as it's username is not taken
    ex: Logs the user out and removes from active_users
    pm: Broadcasts a public message to all active_users
    dm: Sends a direct message to a specified recipient
    """
    global users
    print(f"Connection established with {addr}")
    try:
        while True:
            # Receive message from client
            message = client_sock.recv(1024).decode('utf-8')
            if not message:
                print(f"Client {addr} disconnected.")
                break

            # Client JSON -> variables
            request = json.loads(message)
            command = request.get("command")
            username = request.get("username")
            password = request.get("password")

            # Process login message from client
            if command == "login":
                # Valid login
                if username in users and users[username] == password:
                    active_users[username] = client_sock
                    response = {"status": "success", "active_users": list(active_users.keys())}
                    broadcast_active_users(client_sock) # Broadcast active_users to all active clients
                # Catch invalid logins and update status to the client
                elif username not in users:
                    response = {"status": "user_not_found"}
                else:
                    response = {"status": "failed"}

            # Process register message from client
            elif command == "register":
                if username in users:
                    response = {"status": "username_taken"}
                else:
                    users[username] = password  # Store user in memory
                    save_users(users)
                    response = {"status": "success"}

            # Process exit message from client
            elif command.lower() == "ex":
                # Handle the EX command (logout)
                if username in active_users:
                    del active_users[username]
                    response = {"status": "exiting"}
                    broadcast_active_users(client_sock) # Broadcast active_users to all active clients
                else:
                    response = {"status": "user_not_logged_in"}

            # Process pm message from client
            elif command.lower() == "pm":
                if username in active_users:
                    message_content = request.get("message", "")
                    broadcast_message = {
                        "type": "pm",
                        "from": username,
                        "message": message_content
                    }

                    # Send the message to all active users
                    for user, user_sock in active_users.items():
                        if user_sock != client_sock:  # Don't send back to the sender
                            try:
                                # Send to user
                                user_sock.send(json.dumps(broadcast_message).encode('utf-8'))
                            except:
                                response = {"status": "message_failed"}
                response = {"status": "message_sent"}

            # Process dm message from client
            elif command.lower() == "dm":
                if username in active_users:
                    message_content = request.get("message", "")
                    recipient_username = request.get("recipient")

                    if recipient_username in active_users:
                        if recipient_username != username:
                            recipient_sock = active_users[recipient_username]
                            if recipient_sock:
                                direct_message = {
                                    "type": "dm",
                                    "from": username,
                                    "message": message_content
                                }
                                try:
                                    # Send to specific user
                                    recipient_sock.send(json.dumps(direct_message).encode('utf-8'))
                                    response = {"status": "message_sent"}
                                except:
                                    response = {"status": "message_failed"}
                            else:
                                response = {"status": "recipient_sock_not_found"}
                        else:
                            response = {"status": "cannot_message_self"} # Prevent user sending to themselves
                    else:
                        response = {"status": "recipient_username_not_found"}
                else:
                    response = {"status": "sender_not_active"}

            # Catch invlaid command
            else:
                response = {"status": "unknown_command"}

            client_sock.send(json.dumps(response).encode('utf-8'))
    except ConnectionError:
        print(f"Connection error with {addr}.")
    finally:
        # Ensure client socket is closed upon exit
        print(f"Closing connection to {addr}")
        client_sock.close()

def broadcast_active_users(excluded_usersock=None):
    """
    This function sends the list of active users to all connected users

    Optional argument allows for a user (the sender) to be excluded
    """
    updated_users_list = {
        "type": "active_users",
        "active_users": list(active_users.keys())
    }

    for user_sock in list(active_users.values()):
        if excluded_usersock is None or user_sock != excluded_usersock:
            try:
                user_sock.send(json.dumps(updated_users_list).encode('utf-8'))
            except:
                print(f"Failed to send updated user list to a client.")

def periodic_broadcast():
    """
    This function broadcasts active users list every 30 seconds

    (It is not utilized in the final program, but it is functional)
    """
    broadcast_active_users()
    threading.Timer(30, periodic_broadcast).start()


def run_server(port_number):
    """
    Runs the server and creates threads to handle clients

    The argument specifies the port number
    """
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.bind(('', port_number))
    server_sock.listen(100)
    print(f"Server listening on port {port_number}")

    try:
        while True:
            client_sock, addr = server_sock.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_sock, addr))
            client_thread.start()
            print(f"Started thread for {addr}")
    except:
        print("\n\nShutting down server")
        server_sock.close()

if __name__ == '__main__':
    users = load_users()

    # Ensure the correct number of arguments were passed (Ex: python3 server.py 12000)
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} server_port")
        sys.exit(1)

    try:
        server_port = int(sys.argv[1])
    except ValueError:
        print("Port number must be an integer.")
        sys.exit(1)

    if not (1024 <= server_port <= 65535):
        print("Port number must be between 1024 and 65535.")
        sys.exit(1)

    """Periodic broadcast is commented out, as I opted to instead inform users when active_users changes"""
    # periodic_broadcast()

    # Run the server based on the server port
    run_server(server_port)
