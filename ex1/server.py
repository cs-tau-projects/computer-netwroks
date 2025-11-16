import socket, select, json
from utils import load_users, parse_args, handle_lcm, handle_parentheses, handle_caesar

DEFAULT_PORT = 1337
MESSAGE_MAX_SIZE = 4096

def handle_message(client_socket, message, client, users):
    try:
        data = json.loads(message.decode('utf-8'))
    except json.JSONDecodeError:
        return json.dumps({"type": "error", "message": "Invalid JSON format."})
    #Deal with authentication
    t = data.get("type")
    if not client["authenticated"]:
        fail = json.dumps({"type": "login_failure", "message": "Failed to login."})
        if(not client["waiting_password"]):
            if t != "login_username":
                return fail
            username = data.get("username")
            if username not in users:
                return fail
            client["username"] = username
            client["waiting_password"] = True
            return None
        else:
            if t != "login_password":
                return fail
            password = data.get("password")
            if(users[username] != password):
                return fail
            client["authenticated"] = True
            client["waiting_password"] = False
            return json.dumps({"type": "login_success", "message": f"Hi, {username}, good to see you."})
        
    
    # Authenticated user commands
    cmd_type = t
    match cmd_type:
        case "lcm":
            return handle_lcm(data, client_socket)
        case "parentheses":
            return handle_parentheses(data, client_socket)
        case "caesar":
            return handle_caesar(data, client_socket)
        case _:
            return json.dumps({"type": "error", "message": "Unknown command."})

def delete_client(client_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers):
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
        print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
        port = DEFAULT_PORT
        
    users = load_users(users_file) # Dict of {username: password}

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)
    server_socket.bind(("", port))
    server_socket.listen(5)
    print(f"Server listening on port {port}...")

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
                clients[client_socket] = {"authenticated": False, "waiting_password" : False,  "username": None}
                client_send_buffers[client_socket] = bytearray()
                clients_recv_buffers[client_socket] = bytearray()
                greeting = json.dumps({"type": "greeting", "message": "Welcome! Please log in."}) + "\n"
                client_send_buffers[client_socket].extend(greeting.encode("utf-8"))
                # print(f"Accepted new connection from {client_socket.getpeername()}.")
            else:
                message = notified_socket.recv(MESSAGE_MAX_SIZE)
                if not message:
                    # print(f"Closed connection from {clients[notified_socket]['address']}.")
                    delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)
                    if(notified_socket in writeable):
                        writeable.remove()
                    continue

                buf = clients_recv_buffers[notified_socket]
                buf.extend(message)
                if b"\n" not in clients_recv_buffers[notified_socket]:
                    # Hanlde case where message is too long (e.g. we passed some size - throw error?)
                    continue

                # In handle message, clear buffer until newline
                while b"\n" in buf:
                    line, _, rest = buf.partition(b"\n")
                    clients_recv_buffers[notified_socket] = rest
                    response = handle_message(notified_socket, line, clients[notified_socket], users)
                    if response is not None:
                        client_send_buffers[notified_socket].extend(response.encode('utf-8') + b"\n")

        for notified_socket in writeable:
            if notified_socket in clients and len(client_send_buffers[notified_socket]) > 0:
                # Potentialy add try except here
                sent = notified_socket.send(client_send_buffers[notified_socket])
                client_send_buffers[notified_socket] = client_send_buffers[notified_socket][sent:]
        
        for notified_socket in exceptional:
            delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)


if __name__ == "__main__":
    main()