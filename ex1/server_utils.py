#!/usr/bin/python3

import math, sys, json, os
import general_utils
from general_utils import print_strings

DEFAULT_PORT = 1337
# Using verbose flag from general_utils


def handle_message(message, client, users):
    print_strings(general_utils.verbose, "SERVER: Received message from client")
    try:
        data = json.loads(message.decode('utf-8'))
        print_strings(general_utils.verbose, f"SERVER: Message type: {data.get('type', 'unknown')}")
        
    except json.JSONDecodeError:
        print_strings(general_utils.verbose, "SERVER: ERROR - Invalid JSON format received")
        return json.dumps({"type": "error", "message": "Invalid JSON format."})
    #Deal with authentication
    cmd_type = data.get("type")
    fail = json.dumps({"type": "login_failure", "message": "Failed to login."})
    print_strings(general_utils.verbose, f"SERVER: Client authentication state: {client['authenticated']}")
    if client["authenticated"] == 0:
        if cmd_type != "login_username":
            print_strings(general_utils.verbose, "SERVER: Client sent invalid command before authentication.")
            # Signal to disconnect client for unauthorized command
            return "DISCONNECT"
        username = data.get("username")
        if username not in users:
            print_strings(general_utils.verbose, f"SERVER: Authentication failed - Username '{username}' not found")
            return fail
        client["username"] = username
        client["authenticated"] = 1
        return json.dumps({"type": "continue", "message": ""})
    elif client["authenticated"] == 1:
        if cmd_type != "login_password":
            print_strings(general_utils.verbose, "SERVER: Client sent non-password message when password was expected.")
            # Signal to disconnect client for unauthorized command
            return "DISCONNECT"
        password = data.get("password")
        username = client["username"] 
        # Check if the username exists in the users dictionary
        if username not in users:
            print_strings(general_utils.verbose, f"SERVER: Authentication failed - Username '{username}' not found")
            return fail
        if(users[username] != password):
            print_strings(general_utils.verbose, f"SERVER: Authentication failed - Invalid password for user '{username}'")
            return fail
        client["authenticated"] = 2
        print_strings(general_utils.verbose, f"SERVER: User '{username}' successfully authenticated")
        return json.dumps({"type": "login_success", "message": f"Hi {username}, good to see you."})
    elif client["authenticated"] == 2:
        print_strings(general_utils.verbose, "Client is authenticated.")
        pass
    
    # Authenticated user commands
    if cmd_type == "lcm":
        print_strings(general_utils.verbose, f"SERVER: Processing LCM command with values {data.get('x')} and {data.get('y')}")
        return handle_lcm(data)
    elif cmd_type == "parentheses":
        print_strings(general_utils.verbose, f"SERVER: Processing parentheses validation for string: {data.get('string')}")
        return handle_parentheses(data)
    elif cmd_type == "caesar":
        print_strings(general_utils.verbose, f"SERVER: Processing Caesar cipher with shift {data.get('shift')}")
        return handle_caesar(data)
    else:
        print_strings(general_utils.verbose, f"SERVER: ERROR - Unknown command type: {cmd_type}")
        # Clear any previous response data to prevent showing it again
        return json.dumps({"type": "error", "message": "Unknown command or incorrect format. Please check and try again."})

def delete_client(client_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers):
    print_strings(general_utils.verbose, f"SERVER: Closing connection with client {clients.get(client_socket, {}).get('username', 'unknown')}")
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    clients.pop(client_socket, None)
    client_send_buffers.pop(client_socket, None)
    clients_recv_buffers.pop(client_socket, None)
    try:
        client_socket.close()
    except OSError:
        pass

def load_users(path):
    """
    Load users from a tab-delimited text file (username<TAB>password).
    Ignores blank lines.
    Returns a dict of {username: password}.
    """
    users = {}
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            username, password = parts
            users[username.strip()] = password.strip()
    return users


def balanced_parentheses(s):
    """
    Check if a parentheses string is balanced.
    Returns True for balanced, False for unbalanced, and None for invalid input.
    """
    if any(ch not in ("(", ")") for ch in s):
        return None
    count = 0
    for ch in s:
        if ch == "(":
            count += 1
        elif ch == ")":
            count -= 1
            if count < 0:
                return False
    return count == 0


def lcm(x, y):
    """
    Compute least common multiple for two signed ints.
    """
    if x == 0 or y == 0:
        return 0
    return abs(x * y) // math.gcd(x, y)


def caesar(text, shift):
    """
    Caesar cipher. Only lowercase/uppercase letters and spaces are allowed.
    Output is always lowercase. Handles both positive and negative shifts.
    If invalid chars found, return None.
    """
    result = []
    # Handle negative shifts by converting to equivalent positive shift
    shift = shift % 26
    
    for ch in text:
        if ch == " ":
            result.append(" ")
        elif ch.isalpha():
            c = ch.lower()
            k = (ord(c) - ord('a') + shift) % 26
            result.append(chr(ord('a') + k))
        else:
            return None
    return "".join(result)


def parse_args():
    """
    Read command-line arguments for port number and verbose option.
    Returns a tuple (users_file, port).
    Sets the global verbose flag if --verbose is present.
    """
    # Create a copy of args to process
    args = sys.argv[1:]
    
    # Check for --verbose flag anywhere in the arguments
    if "--verbose" in args:
        general_utils.verbose = True
        args.remove("--verbose")
        print("Verbose mode enabled")  # Direct print to verify flag is processed
    
    # Now check remaining args
    if not (1 <= len(args) <= 2):
        print(f"Usage: {os.path.basename(sys.argv[0])} users_file [port] [--verbose]")
        sys.exit(1)
        
    users_file = args[0]
    if not os.path.isfile(users_file):
        # Try relative path from the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, users_file)
        if os.path.isfile(full_path):
            users_file = full_path
        else:
            print(f"Users file not found: {users_file}")
            sys.exit(1)
        
    port = DEFAULT_PORT
    if len(args) == 2:
        try:
            p = int(args[1])
            if 1 <= p <= 65535:
                port = p
            else:
                print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
        except Exception:
            print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
            
    return users_file, port
        

# Handler function for server.py


def handle_lcm(data):
    try:
        x = int(data.get("x"))
        y = int(data.get("y"))
    except (TypeError, ValueError):
        return json.dumps({"type": "error", "message": "Invalid parameters for LCM."})
    result = lcm(x, y)
    return json.dumps({"type": "lcm_result", "result": result})


def handle_parentheses(data):
    s = data.get("string")
    if not isinstance(s, str):
        return json.dumps({"type": "error", "message": "Invalid parameters for parentheses check."})
    result = balanced_parentheses(s)
    if result is None:
        return json.dumps({"type": "error", "message": "String contains invalid characters."})
    return json.dumps({"type": "parentheses_result", "result": result})


def handle_caesar(data):
    text = data.get("text")
    try:
        shift = int(data.get("shift"))
    except (TypeError, ValueError):
        return json.dumps({"type": "error", "message": "Invalid parameters for Caesar cipher."})
    if not isinstance(text, str) or not isinstance(shift, int):
        return json.dumps({"type": "error", "message": "Invalid parameters for Caesar cipher."})
    result = caesar(text, shift)
    if result is None:
        return json.dumps({"type": "error", "message": "error: invalid input"})
    return json.dumps({"type": "caesar_result", "result": result})
