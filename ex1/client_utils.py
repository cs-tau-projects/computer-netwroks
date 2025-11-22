#!/usr/bin/python3

import sys, json
import general_utils
from general_utils import print_strings

# Now using the verbose flag from general_utils

DEFAULT_HOST = "localhost"  # Default hostname as required
DEFAULT_PORT = 1337         # Default port
BURST_SIZE = 4096
RESULT_SET = {"lcm_result", "parentheses_result", "caesar_result"}
MESSAGE_SET = {"error", "login_failure", "greeting", "continue", "login_success"}


def parse_args():
    """
    Read command-line arguments for server host, port, and verbose option.
    Returns a tuple (host, port).
    Sets the global verbose flag if --verbose is present.
    """
    
    # Create a copy of args to process
    args = sys.argv[1:]
    
    # Check for --verbose flag anywhere in the arguments
    if "--verbose" in args:
        general_utils.verbose = True
        args.remove("--verbose")
        print("Client verbose mode enabled")  # Direct print to verify flag is processed
    
    # Now process remaining args for host and port
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    
    if len(args) == 0:
        print_strings(general_utils.verbose, f"CLIENT: No host specified. Using default host {DEFAULT_HOST}")
    elif len(args) == 1:
        # Check if the argument might be a port (numeric)
        try:
            maybe_port = int(args[0])
            if 1 <= maybe_port <= 65535:
                # This is likely a port number, which is not allowed without hostname
                print(f"Error: Cannot provide port without hostname")
                print(f"Usage: {sys.argv[0]} [hostname [port]] [--verbose]")
                print(f"Note: You cannot provide port without hostname")
                exit()
        except ValueError:
            # Not a number, so assume it's a hostname
            pass
            
        server_host = str(args[0])
        print_strings(general_utils.verbose, f"CLIENT: No port specified. Using default port {DEFAULT_PORT}")
    elif len(args) == 2:
        server_host = str(args[0])
        try:
            server_port = int(args[1])
            if not (1 <= server_port <= 65535):
                print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
                print_strings(general_utils.verbose, f"CLIENT: Invalid port number. Using default port {DEFAULT_PORT}")
                server_port = DEFAULT_PORT
        except Exception:
            print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
            print_strings(general_utils.verbose, f"CLIENT: Invalid port number. Using default port {DEFAULT_PORT}")
            server_port = DEFAULT_PORT
    else:
        print(f"Usage: {sys.argv[0]} [hostname [port]] [--verbose]")
        print(f"Note: You cannot provide port without hostname")
        exit()

    return server_host, server_port


def handle_user_input(line, client_state):
    length = len(line)
    retry_answer = (None, -1)
    if length == 0:
        return retry_answer

    print_strings(general_utils.verbose, f"CLIENT: Processing user input: {' '.join(line)}")
    
    # Clear any previous response to prevent it from being displayed again after an error
    client_state["last_response_cleared"] = False

    if client_state["auth_state"] == 1 and length > 0:
        # Allow quitting at any time
        if line[0] == "quit":
            if length != 1:
                return retry_answer
            print_strings(general_utils.verbose, "CLIENT: Quitting application")
            return (None, -2)

        # Accept explicit Password:
        if line[0] == "Password:":
            if length != 2:
                return retry_answer
            print_strings(general_utils.verbose, "CLIENT: Sending password")
            result = (json.dumps({"type": "login_password", "password": line[1]}), 0)
            return result

        # Any other command (including trying another username) is not allowed now.
        print_strings(general_utils.verbose, "CLIENT ERROR: Invalid format. Please use 'Password: yourpassword'")
        return (None, -2)

    if line[0] == "User:":
        if length != 2:
            return retry_answer
        print_strings(general_utils.verbose, f"CLIENT: Sending username: {line[1]}")
        return (json.dumps({"type": "login_username", "username": line[1]}), 0)

    elif line[0] == "Password:":
        if length != 2:
            return retry_answer
        print_strings(general_utils.verbose, "CLIENT: Sending password")
        result = (json.dumps({"type": "login_password", "password": line[1]}), 0)
        return result

    elif line[0] == "parentheses:":
        if length != 2:
            return retry_answer
        print_strings(general_utils.verbose, f"CLIENT: Sending parentheses validation request for: {line[1]}")
        return (json.dumps({"type": "parentheses", "string": line[1]}), 0)

    elif line[0] == "lcm:":
        if length != 3:
            return retry_answer
        print_strings(general_utils.verbose, f"CLIENT: Sending LCM request for values: {line[1]} and {line[2]}")
        return (json.dumps({"type": "lcm", "x": line[1], "y": line[2]}), 0)

    elif line[0] == "caesar:" or line[0] == "ceasar:":  # Handle both correct spelling and common misspelling
        # Join all arguments after the command
        if len(line) < 2:  # Need at least command and some text
            return retry_answer
        # Join all arguments after the command to create a single string
        text_and_shift = " ".join(line[1:])
        ceasar_response = handle_ceasar_input(text_and_shift)
        if ceasar_response is None:
            return retry_answer
        print_strings(general_utils.verbose, f"CLIENT: Sending Caesar cipher request with shift: {ceasar_response[1]}")
        return (json.dumps({"type": "caesar", "text": ceasar_response[0], "shift": ceasar_response[1]}), 0)

    elif line[0] == "quit":
        if length != 1:
            return retry_answer
        print_strings(general_utils.verbose, "CLIENT: Quitting application")
        return (None, -2)

    else:
        return retry_answer


def handle_server_input(line, client_state):
    # Check if we should skip displaying a response after an invalid input
    if client_state.get("last_response_cleared", False):
        client_state["last_response_cleared"] = False
        return handle_user_input(input().strip().split(), client_state)
        
    print_strings(general_utils.verbose, "CLIENT: Received response from server")
    try:
        data = json.loads(line.decode('utf-8'))
        print_strings(general_utils.verbose, f"CLIENT: Response type: {data.get('type', 'unknown')}")
    except json.JSONDecodeError:
        print_strings(general_utils.verbose, "CLIENT: ERROR - Could not parse server response as JSON")
        data = {"type": "error", "message": "error converting message to Json"}

    cmd_type = data.get("type")
    # Handle error responses explicitly to prevent showing previous responses
    if cmd_type == "error":
        print("\n" + data.get("message"))
        print_strings(general_utils.verbose, "\nCLIENT: Command failed. Please try again.")
        if client_state["auth_state"] == 2:
            print_strings(general_utils.verbose, 
                "CLIENT: You can use the following commands:",
                "  lcm: x y - Calculate least common multiple",
                "  parentheses: string - Check if parentheses are balanced",
                "  caesar: text shift - Apply Caesar cipher",
                "  quit - Exit the client"
            )
    elif cmd_type in RESULT_SET:
        if cmd_type == "lcm_result":
            print("the lcm is: ", data.get("result"), sep='')
        elif cmd_type == "parentheses_result":
            tmp_res = data.get("result")
            answer = "yes" if tmp_res else "no"
            print("the parentheses are balanced: ", answer, sep='')
        elif cmd_type == "caesar_result":
            print("the ciphertext is: ", data.get("result"), sep='')
    elif cmd_type in MESSAGE_SET:
        print("\n" + data.get("message"))
        if cmd_type == "continue":
            client_state["auth_state"] = 1
            client_state["username"] = "username_sent"
            print_strings(general_utils.verbose, 
                "\n" + "=" * 60,
                "CLIENT: USERNAME ACCEPTED. NOW ENTER YOUR PASSWORD.",
                "CLIENT: Please use the format 'Password: yourpassword'",
                "=" * 60 + "\n",
                "CLIENT: *** IMPORTANT: Only password in the correct format is accepted now. ***"
            )

        elif cmd_type == "login_success":
            client_state["auth_state"] = 2
            print_strings(general_utils.verbose, 
                "CLIENT: Successfully logged in!",
                "CLIENT: You can now use the following commands:",
                "  lcm: x y - Calculate least common multiple",
                "  parentheses: string - Check if parentheses are balanced",
                "  caesar: text shift - Apply Caesar cipher",
                "  quit - Exit the client"
            )

    else:
        print("Error: Unknown response")

    return handle_user_input(input().strip().split(), client_state)


def delete_client(client_socket):
    print_strings(general_utils.verbose, "CLIENT: Closing connection and exiting")
    try:
        client_socket.close()
    except OSError:
        print("CLIENT: Error closing socket (ignored)")
    exit()


def handle_ceasar_input(line):
    """Helper function to validate Caesar cipher input."""
    if not line or not line.strip():
        return None
    
    # Try to find the last space in the line
    try:
        last_space_index = line.rstrip().rfind(' ')
        if last_space_index == -1:  # No spaces found
            return None
        
        # Extract the sentence and the number
        sentence = line[:last_space_index]
        number_str = line[last_space_index + 1:].strip()
        
        # Check if the last part is a number
        try:
            number = int(number_str)
            return (sentence, number)
        except ValueError:
            # The last part is not a number
            return None
    except Exception:
        # Any other error, return None
        return None
