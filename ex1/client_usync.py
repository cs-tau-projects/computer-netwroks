import socket
import json
import sys
import select

DEFAULT_HOST = "127.0.0.1"  # Replace with the actual server address
DEFAULT_PORT = 1337         # Replace with the server port
BUFFER_SIZE = 4096
MESSAGE_MAX_SIZE = 4096
BURST_SIZE = 4096
LINUX = 1






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
                server_host = int(sys.argv[1])
            except Exception:
                print(f"Invalid port number. Using default host {DEFAULT_HOST}.")
        case 3:
            try:
                server_host = str(sys.argv[1])
            except Exception:
                print(f"Invalid port number. Using default host {DEFAULT_HOST}.")

            try:
                server_port = int(sys.argv[2])
                assert 1 <= server_port <= 65535
            except Exception:
                print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
        case _:
            print("invalid number of args")
            exit()

    return server_host, server_port



def handle_user_input(line):#decide what error code to set
    if(len(line == 0)):
        return None
    match line[0]:
        case "User:":
            if(len(line != 2)):
                return -1
            return json.dumps({"type": "login_username", "username": line[1]})
            pass
        case "Password:":
            
            pass
        case "parentheses":
            pass
        case "lcm:":
            pass
        case "caesar:":
            pass
        case "quit":
            pass


def handle_server_input(line):
    pass

def delete_client(client_socket):
    pass





def send_message(sock, message):
    """Send a JSON message to the server."""
    sock.sendall((json.dumps(message) + "\n").encode('utf-8'))

def receive_message(sock):
    """Receive a JSON message from the server."""
    data = b""
    while b"\n" not in data:
        data += sock.recv(BUFFER_SIZE)
    return json.loads(data.decode('utf-8').strip())

def authenticate(sock, username, password):
    """Perform the authentication process."""
    login_request = {
        "type": "login",
        "username": username,
        "password": password
    }
    send_message(sock, login_request)
    response = receive_message(sock)
    print(f"Server Response: {response}")
    return response.get("type") == "login_success"



def main():

    server_host, server_port = parse_args()
    send_buf = bytearray()
    recv_buf = bytearray()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    
    while(True):
        
        readable, writeable, exceptional = select.select([client_socket], [client_socket], [client_socket])
        line = []
        #remove before submission!!!!!!!!!!!!!!!!! keep only linux case!!!
        if(LINUX):
            readable, _, _ = select.select([sys.stdin], [], [])
            if(sys.stdin in readable):
                line = sys.stdin.readline().strip().split()
        else:
            import msvcrt
            if(msvcrt.kbhit()):
                line = input().strip().split()

        send_data = handle_user_input(line)
        if send_data is not None:
            send_buf.extend(send_data.encode('utf-8') + b"\n")



        if(client_socket in readable):

            message = client_socket.recv(BURST_SIZE)
            if not message:
                # print(f"Closed connection from {clients[notified_socket]['address']}.")
                delete_client(client_socket)
                continue
            
            recv_buf.extend(message)
            if b"\n" not in recv_buf:
                # Hanlde case where message is too long (e.g. we passed some size - throw error?)
                continue
            


            while b"\n" in recv_buf:
                line, _, rest = recv_buf.partition(b"\n")
                recv_buf = rest
                response = handle_server_input(line)
                if response is not None:
                    send_buf.extend(response.encode('utf-8') + b"\n")

            
        if(client_socket in writeable and len(send_buf) > 0):
            # Potentialy add try except here
            sent = client_socket.send(send_buf)
            send_buf = send_buf[sent:]

        if(client_socket in exceptional):
            #deal with problem. clos
            pass



if __name__ == "__main__":
    main()
