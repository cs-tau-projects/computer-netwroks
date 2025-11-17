import socket, select, json
from utils import load_users, parse_args, handle_lcm, handle_parentheses, handle_caesar

DEFAULT_PORT = 1337
MESSAGE_MAX_SIZE = 4096

def handle_message(message, client, users):
    print("SERVER: Received message from client")
    try:
        data = json.loads(message.decode('utf-8'))
        print(f"SERVER: Message type: {data.get('type', 'unknown')}")
        
    except json.JSONDecodeError:
        print("SERVER: ERROR - Invalid JSON format received")
        return json.dumps({"type": "error", "message": "Invalid JSON format."})
    #Deal with authentication
    cmd_type = data.get("type")
    fail = json.dumps({"type": "login_failure", "message": "Failed to login."})
    print(f"SERVER: Client authentication state: {client['authenticated']}")
    match client["authenticated"]:
        case 0:
            if cmd_type != "login_username":
                print("SERVER: Client sent invalid command before authentication.")
                return fail
            username = data.get("username")
            if username not in users:
                print(f"SERVER: Authentication failed - Username '{username}' not found")
                return fail
            client["username"] = username
            client["authenticated"] = 1
            return json.dumps({"type": "continue", "message": ""})
        case 1:
            if cmd_type != "login_password":
                print("SERVER: Client sent invalid command before authentication.")
                return fail
            password = data.get("password")
            username = client["username"]  # Get username from client object instead of using local variable
            if(users[username] != password):
                print(f"SERVER: Authentication failed - Invalid password for user '{username}'")
                return fail
            client["authenticated"] = 2
            print(f"SERVER: User '{username}' successfully authenticated")
            return json.dumps({"type": "login_success", "message": f"Hi, {username}, good to see you."})
        case 2:
            print("Client is authenticated.")
            pass
    
    # Authenticated user commands
    match cmd_type:
        case "lcm":
            print(f"SERVER: Processing LCM command with values {data.get('x')} and {data.get('y')}")
            return handle_lcm(data)
        case "parentheses":
            print(f"SERVER: Processing parentheses validation for string: {data.get('string')}")
            return handle_parentheses(data)
        case "caesar":
            print(f"SERVER: Processing Caesar cipher with shift {data.get('shift')}")
            return handle_caesar(data)
        case _:
            print(f"SERVER: ERROR - Unknown command type: {cmd_type}")
            return json.dumps({"type": "error", "message": "Unknown command."})

def delete_client(client_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers):
    print(f"SERVER: Closing connection with client {clients.get(client_socket, {}).get('username', 'unknown')}")
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    clients.pop(client_socket, None)
    client_send_buffers.pop(client_socket, None)
    clients_recv_buffers.pop(client_socket, None)
    try:
        client_socket.close()
    except OSError:
        pass

def main():
    users_file, port = parse_args()
    if (port is None):
        print(f"SERVER: Invalid port number. Using default port {DEFAULT_PORT}.")
        port = DEFAULT_PORT
        
    users = load_users(users_file) # Dict of {username: password}
    print(f"SERVER: Loaded {len(users)} users from file: {users_file}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)
    server_socket.bind(("", port))
    server_socket.listen(5)
    print(f"SERVER: Listening on port {port}...")

    sockets_list = [server_socket]
    clients = {}
    client_send_buffers = {}
    clients_recv_buffers = {}

    while True:
        # Writable sockets are those with data to send
        writable_set = [s for s in sockets_list if client_send_buffers.get(s) and len(client_send_buffers[s]) > 0]
        readable, writeable, exceptional = select.select(sockets_list, writable_set, sockets_list)

        for notified_socket in readable:
            if notified_socket == server_socket:
                client_socket, _ = server_socket.accept()
                client_socket.setblocking(False)
                sockets_list.append(client_socket)
                clients[client_socket] = {"authenticated": 0,  "username": None}# 0 for no_auth, 1 for only_username, 2 for fully_auth
                client_send_buffers[client_socket] = bytearray()
                clients_recv_buffers[client_socket] = bytearray()
                greeting = json.dumps({"type": "greeting", "message": "Welcome! Please log in."}) + "\n"
                client_send_buffers[client_socket].extend(greeting.encode("utf-8"))
                client_address = client_socket.getpeername()
                clients[client_socket]["address"] = client_address
                print(f"SERVER: New connection accepted from {client_address}")
            else:
                message = notified_socket.recv(MESSAGE_MAX_SIZE)
                if not message:
                    print(f"SERVER: Client disconnected: {clients[notified_socket].get('address', 'unknown')}")
                    delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)
                    if(notified_socket in writeable):
                        writeable.remove()
                    continue

                buf = clients_recv_buffers[notified_socket]
                buf.extend(message)
                if b"\n" not in clients_recv_buffers[notified_socket]:
                    # Hanlde case where message is too long (e.g. we passed some size - throw error?)
                    continue

                buf = clients_recv_buffers[notified_socket]
                buf.extend(message)

                # Process as many complete newline-terminated messages as we have.
                while True:
                    nl_index = buf.find(b"\n")
                    if nl_index == -1:
                        break  # no full message yet; wait for more data

                    # Extract one full message (without the trailing newline)
                    line = bytes(buf[:nl_index])
                    # Remove the processed message (+ the newline) from the buffer
                    del buf[:nl_index + 1]

                    if not line:
                        continue  # skip empty lines or keepalives

                    # Process the message
                    response = handle_message(line, clients[notified_socket], users)
                    user_id = clients[notified_socket].get('username') or notified_socket.getpeername()
                    print(f"SERVER: Processed message from {user_id}")
                    if response is not None:
                        client_send_buffers[notified_socket].extend(response.encode("utf-8") + b"\n")


        for notified_socket in writeable:
            if notified_socket in clients and len(client_send_buffers[notified_socket]) > 0:
                # Potentialy add try except here
                sent = notified_socket.send(client_send_buffers[notified_socket])
                client_send_buffers[notified_socket] = client_send_buffers[notified_socket][sent:]
                user_id = clients[notified_socket].get('username') or notified_socket.getpeername()
                print(f"SERVER: Sent {sent} bytes to {user_id}")
        
        for notified_socket in exceptional:
            print(f"SERVER: Socket exception for client: {clients[notified_socket].get('address', 'unknown')}")
            delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)


if __name__ == "__main__":
    main()
