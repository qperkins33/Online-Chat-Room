import threading
import sys
from socket import *
import json

# Global variable to track the user's login status
loggedIn = False

def printMessage(*args, newline=False):
    """
    This function formats all incoming messages.

    This function expects two or more arguments. The last argument is the message.
    All preceding arguemts will be info about the message, so they will print
    surrounded by brackets.

    Optional newline argument is used as a flag for if there should be a newline
    before the message. This is used for formatting in certain cases.

    Example output:
    [ACTIVE USERS]: ['user2', 'user1']
    [INFO]: Client connection closed.
    [PM] [SENT BY: user1]: Hello
    """

    # if newLine, print the extra newLine
    if newline:
        print()
    # if no arguments are provided
    if len(args) <= 0:
        print("[INFO]: Empty message.")
        return
    # if one argument is provided
    elif len(args) == 1:
        print(f"{args[0]}")
        return
    # if two or more arguments are provided
    else:
        # The last argument is the message
        message = args[-1]

        # All preceding arguments are bracket texts
        brackets = args[:-1]

        # Create the string with info args surrounded by brackets
        brack_text = " ".join(f"[{br}]" for br in brackets)
        print(f"{brack_text}: {message}")

def login(sock):
    """
    This function handles the login process for the client.

    The user is prompted for their login information. If the userame does not
    exist in the JSON file, the user is offerred the option to register a new user.

    Returns: valid username
    """
    global loggedIn
    while True:
        # Prompt the user for their username, while ensuring the input is not null and cleaning the input
        username = input("Enter username: ")
        username = username.strip()

        while not username:
            username = input("Enter valid username: ")
            username = username.strip()

        password = input("Enter password: ")
        password = password.strip()

        while not password:
            password = input("Enter valid password: ")
            password = password.strip()

        login_data = {
            "command": "login",
            "username": username,
            "password": password
        }

        try:
            # Send the login data to the server as a JSON-encoded message
            sock.send(json.dumps(login_data).encode('utf-8'))

            # Wait for the server's response (1024 bytes)
            response = sock.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            # Process the response_data based on the status
            if response_data["status"] == "success":
                printMessage("INFO", "Login successful!")
                printMessage("ACTIVE USERS", response_data.get("active_users", [])) # if success, dispaly active users
                loggedIn = True
                return username  # Login successful, return the username to indicate success

            elif response_data["status"] == "user_not_found":
                printMessage("INFO", "Username does not exist.") # Notify user that their username does not exist
                choice = input("Would you like to register? (yes/no): ").strip().lower()

                if choice == "yes":
                    # Call the registration function if the user chooses to register
                    return register_user(sock, username)
                else:
                    printMessage("INFO", "Returning to login page.")
            else:
                # If a failure occurred, inform the user and repeat the login process
                printMessage("INFO", "Login failed. Try again.")

        except ConnectionError:
            printMessage("INFO", "Connection error. Unable to communicate with the server.")
            return None  # Exit login attempt if connection is lost

def register_user(sock, username):
    """
    This function handles the registration process for the client.

    This function passes a username and prompts the client to enter
    a password for the username.

    Returns: Valid username
    """
    while True:
        # Prompt the user to enter a password
        password = input(f"Enter password for new user [{username}]: ")
        password = password.strip()

        while not password:
            password = input(f"Enter valid password for new user [{username}]: ")
            password = password.strip()

        register_data = {
            "command": "register",
            "username": username,
            "password": password
        }

        try:
            # Send the registration data to the server as a JSON-encoded message
            sock.send(json.dumps(register_data).encode('utf-8'))

            # Wait for the server's response
            response = sock.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            # Process the response_data based on the status
            if response_data["status"] == "success":
                printMessage("INFO", "Registration successful. You can now log in.") # If successful, return to the login page
                return login(sock)

            elif response_data["status"] == "username_taken":
                printMessage("INFO", "Username already exists. Choose a different username.") # If username is taken, return to the login page and enter new username
                return login(sock)

            else:
                printMessage("INFO", "Registration failed. Try again.") # If an error occurs try again

        except ConnectionError:
            printMessage("INFO", "Connection error. Unable to communicate with the server.")
            return False  # Exit registration attempt if connection is lost

def receive_messages(sock):
    """
    This function continuously listens for messages from the server.

    The client decides what to do based on the data type that is classifed
    when sent by the server.
    """
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message: # catch empty message
                break

            data = json.loads(message)

            message_type = data.get("type")
            # Check the message type and print
            if message_type in ("pm", "dm"):
                printMessage(message_type.upper(), f"SENT BY: {data['from']}", data['message'])
            elif message_type == "active_users":
                printMessage("ACTIVE USERS", data['active_users'])
            # For other types, print the status message from the server
            else:
                printMessage("SERVER", data['status'])

        except (ConnectionError, OSError) as e:
            if not loggedIn:
                break
            printMessage("INFO", f"Connection error: {e}")
            break

def send_messages(sock, username):
    """
    This function continuously listens for the user to input message types.

    After enterring a message type, the user is prompted to send the corresponding
    message to the server.
    """
    global loggedIn

    # Message type instructions
    instructions = (
        "\nPM: Public message to all clients.\n"
        "DM: Direct message to a specific client.\n"
        "EX: Exit the chat.\n"
    )

    # Print the instructions with the preceding newLine
    printMessage("INFO", instructions, newline=True)

    while loggedIn:
        message = input()
        message = message.strip()

        if message.lower() == 'ex': # Client typed "ex" to exit
            printMessage("INFO", "Exiting...")
            loggedIn = False
            ex_data = {
                "command": "ex",
                "username": username
            }
            try:
                # Send the shutdown command (ex) to the server
                sock.send(json.dumps(ex_data).encode('utf-8'))
                # Ensure the socket is closed in both directions
                sock.shutdown(SHUT_RDWR)
            except Exception as e:
                printMessage("INFO", f"Error exiting and closing socket: {e}")
            finally:
                # Ensure the socket is closed
                sock.close()
            break

        # Client typed "pm" to send a public message
        elif message.lower() == 'pm':
            # Prompt user for message to send
            pm_message = input("Enter message to broadcast: ")

            while not pm_message:
                pm_message = input("Enter valid message to broadcast: ")

            pm_data = {
                "command": "pm",
                "username": username,
                "message": pm_message
            }
            try:
                # Send the public message to the server
                sock.send(json.dumps(pm_data).encode('utf-8'))
            except Exception as e:
                printMessage("INFO", f"Error sending broadcast_data: {e}")

        elif message.lower() == 'dm': # Client typed "dm" to send a direct message
            # Prompt user for who to send message to
            dm_recipient = input("Enter recipient username: ")
            dm_recipient = dm_recipient.strip()

            # If invalid empty username, ask user again
            while not dm_recipient:
                dm_recipient = input("Enter valid recipient username: ")
                dm_recipient = dm_recipient.strip()

            # Prompt user for message to send
            dm_message = input("Enter message to broadcast: ")
            while not dm_message:
                dm_message = input("Enter valid message to broadcast: ")

            dm_data = {"command": "dm", "username": username, "recipient": dm_recipient, "message": dm_message}
            try:
                # Send the public message to the server
                sock.send(json.dumps(dm_data).encode('utf-8'))
            except Exception as e:
                printMessage("INFO", f"Error sending broadcast_data: {e}")

        else:
            # If invalid command, reprint the instructions and don't send anything to the server
            printMessage("INFO", "[INVALID COMMAND] [ENTER VALID COMMAND]")
            printMessage("INFO", instructions)

def run_client(server_name, server_port):
    """
    Main function to run the client.

    This function connects to server and handles calling all other functions.
    First, this function has the client login, then it creates seperate threads
    for receiving and sending. Finally, it waits for both threads to complete
    before closing the client connection.
    """

    # Create TCP socket and connect to the server based on the fucntion arguments
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((server_name, server_port))
    printMessage("INFO", "Connected to Chat Room")

    # Call the login function to assign username (registration function is called within the login function)
    username = login(client_sock)
    if not username:
        printMessage("INFO", "Login failed. Exiting.")
        client_sock.close()
        return

    # Create two threads: one for receiving messages, one for sending them
    receive_thread = threading.Thread(target=receive_messages, args=(client_sock,))
    send_thread = threading.Thread(target=send_messages, args=(client_sock, username))

    # Start both threads
    receive_thread.start()
    send_thread.start()

    # Wait for both threads to finish
    receive_thread.join()
    send_thread.join()

    printMessage("INFO", "Client connection closed.")

if __name__ == '__main__':
    # Ensure the correct number of arguments were passed (Ex: python3 client.py localhost 12000)
    if len(sys.argv) != 3:
        print(f'Usage: python3 {sys.argv[0]} server_name server_port')
        sys.exit(1)

    # Retrieve the server name and port from command-line arguments
    server_name = sys.argv[1]
    server_port = int(sys.argv[2])

    # Run the chat client
    run_client(server_name, server_port)
