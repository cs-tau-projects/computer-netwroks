import socket
import json
import sys
import select

DEFAULT_HOST = "127.0.0.1"  # Replace with the actual server address
DEFAULT_PORT = 1337         # Replace with the server port
BURST_SIZE = 4096





def parse_args():
    """
    Read command-line arguments for port number.
    Returns the port number or None if invalid.
    """
    server_host = DEFAULT_HOST
    server_port = DEFAULT_PORT
    match len(sys.argv):#Might need to fix case that port given without host
        case 1:
            pass
        case 2:
            try:
                server_host = str(sys.argv[1])
            except Exception:
                print(f"Invalid port number. Using default host {DEFAULT_HOST}.")
        case 3:
            try:
                server_host = str(sys.argv[1])
            except Exception:
                print(f"Invalid host. Using default host {DEFAULT_HOST}.")

            try:
                server_port = int(sys.argv[2])
                assert 1 <= server_port <= 65535
            except Exception:
                print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
        case _:
            print("invalid number of args")
            exit()

    return server_host, server_port



def handle_user_input(line):
    length = len(line)
    retry_answer = (None, -1)
    if(length == 0):
        return retry_answer
    match line[0]:
        case "User:":
            if(length != 2):
                return retry_answer
            return (json.dumps({"type": "login_username", "username": line[1]}), 0)
        case "Password:":
            if(length != 2):
                return retry_answer
            return (json.dumps({"type": "login_password", "password": line[1]}), 0)
        case "parentheses":
            if(length != 2):
                return retry_answer
            return (json.dumps({"type": "parentheses", "string": line[1]}), 0)
        case "lcm:":
            if(length != 3):
                return retry_answer
            return (json.dumps({"type": "lcm", "x": line[1], "y": line[2]}), 0)
        case "caesar:":
            if(length != 3):
                return retry_answer
            return (json.dumps({"type": "caesar", "text": line[1], "shift": line[2]}), 0)
        case "quit":
            if(length != 1):
                return retry_answer
            return (None, -2)
        case _:
            return retry_answer


def handle_server_input(line):
    try:
        data = json.loads(line.decode('utf-8'))
    except json.JSONDecodeError:
        data = json.dumps({"type": "error", "message": "error converting message to Json"})
    
    cmd_type = data.get("type")
    match cmd_type:
        case "lcm_result":
            print(data.get("result"))
        case "parentheses_result":
            print(data.get("balanced"))
        case "caesar_result":
            print(data.get("result"))
        case "login_success":
            print(data.get("message"))
        case "continue":
            pass
        case "error":
            print(f"Error: {data.get("message")}")
        case "login_failure":
            print(data.get("message"))
        case _:
            print("Error: Unknown response")

    return handle_user_input(input())
    

def delete_client(client_socket):
    try:
        client_socket.close()
    except OSError:
        #ignore errors when closing socket
        pass
    exit()





def main():

    server_host, server_port = parse_args()
    send_buf = bytearray()
    recv_buf = bytearray()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_host, server_port))
    except OSError as e:
        print(f"Could not connect to server at {server_host}:{server_port}: {e}")
        sys.exit(1)
    

    while(True):
        
        readable, writable, _ = select.select([client_socket], [client_socket], [client_socket])

        if(client_socket in readable):

            message = client_socket.recv(BURST_SIZE)
            if not message:
                delete_client(client_socket)
            
            recv_buf.extend(message)
            if b"\n" in recv_buf:
                # Handle case where message is too long (e.g. we passed some size - throw error?)
                line, _, rest = recv_buf.partition(b"\n")
                recv_buf = rest
                valid = 0
                while not valid:#repeat until valid input given
                    response, val = handle_server_input(line)
                    match val:
                        case 0:
                            send_buf.extend(response.encode('utf-8') + b"\n")
                            valid = 1
                        case -1:
                            print("invalid user input, try again")
                        case -2:
                            delete_client(client_socket)

            

            
        if(client_socket in writable and len(send_buf) > 0):
            try:
                sent = client_socket.send(send_buf)
                send_buf = send_buf[sent:]
            except BrokenPipeError:
                delete_client(client_socket)



if __name__ == "__main__":
    main()
