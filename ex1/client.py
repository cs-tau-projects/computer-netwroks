import socket
import json
import sys
import select
from client_utils import handle_ceasar_input

DEFAULT_HOST = "127.0.0.1"  # Replace with the actual server address
DEFAULT_PORT = 1337         # Replace with the server port
BURST_SIZE = 4096
RESULT_SET = {"lcm_result", "parentheses_result", "caesar_result"}
MESSAGE_SET = {"error", "login_failure", "greeting", "continue", "login_success"}


def parse_args():
    """
    Read command-line arguments for server host and port.
    Returns a tuple (host, port).
    """
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    match len(sys.argv):
        case 1:
            pass
        case 2:
            server_host = str(sys.argv[1])
        case 3:
            server_host = str(sys.argv[1])
            try:
                server_port = int(sys.argv[2])
                assert 1 <= server_port <= 65535
            except Exception:
                print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
        case _:
            print("Invalid number of args")
            exit()

    return server_host, server_port


def handle_user_input(line, client_state):
    length = len(line)
    retry_answer = (None, -1)
    if length == 0:
        return retry_answer

    print(f"CLIENT: Processing user input: {' '.join(line)}")
    
    # Clear any previous response to prevent it from being displayed again after an error
    client_state["last_response_cleared"] = False

    if client_state["auth_state"] == 1 and length > 0:
        # Allow quitting at any time
        if line[0] == "quit":
            if length != 1:
                return retry_answer
            print("CLIENT: Quitting application")
            return (None, -2)

        # Accept explicit Password:
        if line[0] == "Password:":
            if length != 2:
                return retry_answer
            print("CLIENT: Sending password")
            result = (json.dumps({"type": "login_password", "password": line[1]}), 0)
            return result

        # Any other command (including trying another username) is not allowed now.
        print("CLIENT ERROR: Invalid actsrc/financial-transactions/utils/get-money-movements.tsion while waiting for password. Login flow reset.")
        print("CLIENT: Please start over with: User: username")
        client_state["auth_state"] = 0
        client_state["username"] = None
        return retry_answer

    match line[0]:
        case "User:":
            if length != 2:
                return retry_answer
            print(f"CLIENT: Sending username: {line[1]}")
            return (json.dumps({"type": "login_username", "username": line[1]}), 0)

        case "Password:":
            if length != 2:
                return retry_answer
            print("CLIENT: Sending password")
            result = (json.dumps({"type": "login_password", "password": line[1]}), 0)
            return result

        case "parentheses:":
            if length != 2:
                return retry_answer
            print(f"CLIENT: Sending parentheses validation request for: {line[1]}")
            return (json.dumps({"type": "parentheses", "string": line[1]}), 0)

        case "lcm:":
            if length != 3:
                return retry_answer
            print(f"CLIENT: Sending LCM request for values: {line[1]} and {line[2]}")
            return (json.dumps({"type": "lcm", "x": line[1], "y": line[2]}), 0)

        case "caesar:" | "ceasar:":  # Handle both correct spelling and common misspelling
            # Join all arguments after the command
            if len(line) < 2:  # Need at least command and some text
                return retry_answer
            # Join all arguments after the command to create a single string
            text_and_shift = " ".join(line[1:])
            ceasar_response = handle_ceasar_input(text_and_shift)
            if ceasar_response is None:
                return retry_answer
            print(f"CLIENT: Sending Caesar cipher request with shift: {ceasar_response[1]}")
            return (json.dumps({"type": "caesar", "text": ceasar_response[0], "shift": ceasar_response[1]}), 0)

        case "quit":
            if length != 1:
                return retry_answer
            print("CLIENT: Quitting application")
            return (None, -2)

        case _:
            return retry_answer


def handle_server_input(line, client_state):
    # Check if we should skip displaying a response after an invalid input
    if client_state.get("last_response_cleared", False):
        client_state["last_response_cleared"] = False
        return handle_user_input(input().strip().split(), client_state)
        
    print("CLIENT: Received response from server")
    try:
        data = json.loads(line.decode('utf-8'))
        print(f"CLIENT: Response type: {data.get('type', 'unknown')}")
    except json.JSONDecodeError:
        print("CLIENT: ERROR - Could not parse server response as JSON")
        data = {"type": "error", "message": "error converting message to Json"}

    cmd_type = data.get("type")
    # Handle error responses explicitly to prevent showing previous responses
    if cmd_type == "error":
        print("\n" + data.get("message"))
        print("\nCLIENT: Command failed. Please try again.")
        if client_state["auth_state"] == 2:
            print("CLIENT: You can use the following commands:")
            print("  lcm: x y - Calculate least common multiple")
            print("  parentheses: string - Check if parentheses are balanced")
            print("  caesar: text shift - Apply Caesar cipher")
            print("  quit - Exit the client")
    elif cmd_type in RESULT_SET:
        match cmd_type:
            case "lcm_result":
                print("the lcm is: ", data.get("result"), sep='')
            case "parentheses_result":
                tmp_res = data.get("result")
                answer = "yes" if tmp_res else "no"
                print("the parentheses are balanced: ", answer, sep='')
            case "caesar_result":
                print("the ciphertext is: ", data.get("result"), sep='')
    elif cmd_type in MESSAGE_SET:
        print("\n" + data.get("message"))
        if cmd_type == "continue":
            client_state["auth_state"] = 1
            client_state["username"] = "username_sent"
            print("\n" + "=" * 60)
            print("CLIENT: USERNAME ACCEPTED. NOW ENTER YOUR PASSWORD.")
            print("CLIENT: Just type your password directly - no need for 'Password:' prefix")
            print("=" * 60 + "\n")
            print("CLIENT: *** IMPORTANT: Only password is accepted now. Any other input will reset login. ***")

        elif cmd_type == "login_success":
            client_state["auth_state"] = 2
            print("CLIENT: Successfully logged in!")
            print("CLIENT: You can now use the following commands:")
            print("  lcm: x y - Calculate least common multiple")
            print("  parentheses: string - Check if parentheses are balanced")
            print("  caesar: text shift - Apply Caesar cipher")
            print("  quit - Exit the client")

        elif cmd_type == "login_failure":
            client_state["auth_state"] = 0
            client_state["username"] = None
            print("CLIENT: Authentication failed. Please start over with: User: username")

    else:
        print("Error: Unknown response")

    return handle_user_input(input().strip().split(), client_state)


def delete_client(client_socket):
    print("CLIENT: Closing connection and exiting")
    try:
        client_socket.close()
    except OSError:
        print("CLIENT: Error closing socket (ignored)")
    exit()


def main():
    print("=" * 60)
    print("CLIENT: Starting authentication client")
    print("CLIENT GUIDE: To log in, use format: User: username")
    print("CLIENT GUIDE: After username is accepted, you can simply type your password")
    print("=" * 60)

    server_host, server_port = parse_args()
    print(f"CLIENT: Connecting to server at {server_host}:{server_port}")
    send_buf = bytearray()
    recv_buf = bytearray()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_state = {
        "auth_state": 0,  # 0: not authenticated, 1: sent username, 2: authenticated
        "username": None
    }

    try:
        client_socket.connect((server_host, server_port))
        print("CLIENT: Successfully connected to server")
    except OSError as e:
        print(f"CLIENT: Connection failed - {e}")
        sys.exit(1)

    while True:
        readable, writable, _ = select.select([client_socket], [client_socket], [client_socket])

        if client_socket in readable:
            message = client_socket.recv(BURST_SIZE)
            if not message:
                print("CLIENT: Server closed connection")
                delete_client(client_socket)

            print(f"CLIENT: Received {len(message)} bytes from server")
            recv_buf.extend(message)
            if b"\n" in recv_buf:
                line, _, rest = recv_buf.partition(b"\n")
                recv_buf = bytearray(rest)
                print("CLIENT: Processing complete message from server")
                valid = 0
                while not valid:
                    response, val = handle_server_input(line, client_state)
                    match val:
                        case 0:
                            send_buf.extend(response.encode('utf-8') + b"\n")
                            valid = 1
                        case -1:
                            print("Invalid user input, try again")
                            # Mark that we should skip displaying the previous response
                            client_state["last_response_cleared"] = True
                        case -2:
                            delete_client(client_socket)

        if client_socket in writable and len(send_buf) > 0:
            try:
                sent = client_socket.send(send_buf)
                send_buf = send_buf[sent:]
                print(f"CLIENT: Sent {sent} bytes to server")
            except BrokenPipeError:
                delete_client(client_socket)


if __name__ == "__main__":
    main()
