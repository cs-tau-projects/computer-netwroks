#!/usr/bin/python3

import socket, select, json
import general_utils
from server_utils import load_users, parse_args, delete_client, handle_message
from general_utils import print_strings

DEFAULT_PORT = 1337
MESSAGE_MAX_SIZE = 4096

def main():
    users_file, port = parse_args()
    
    users = load_users(users_file) # Dict of {username: password}
    print_strings(general_utils.verbose, 
        f"SERVER: Loaded {len(users)} users from file: {users_file}",
        f"SERVER: Listening on port {port}..."
    )

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)
    server_socket.bind(("", port))
    server_socket.listen(5)

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
                print_strings(general_utils.verbose, f"SERVER: New connection accepted from {client_address}")
            else:
                message = notified_socket.recv(MESSAGE_MAX_SIZE)
                if not message:
                    print_strings(general_utils.verbose, f"SERVER: Client disconnected: {clients[notified_socket].get('address', 'unknown')}")
                    delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)
                    if(notified_socket in writeable):
                        writeable.remove(notified_socket)
                    continue

                buf = clients_recv_buffers[notified_socket]
                buf.extend(message)
                if b"\n" not in clients_recv_buffers[notified_socket]:
                    # Handle case where message is too long (e.g. we passed some size - throw error?)
                    continue

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
                    print_strings(general_utils.verbose, f"SERVER: Processed message from {user_id}")
                    
                    # Check if client should be disconnected for unauthorized command
                    if response == "DISCONNECT":
                        print_strings(general_utils.verbose, f"SERVER: Disconnecting client {user_id} for unauthorized command attempt before authentication")
                        delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)
                        break
                    elif response is not None:
                        # Clear previous data from buffer before adding new response
                        # This prevents old responses from being shown after errors
                        client_send_buffers[notified_socket] = bytearray()
                        client_send_buffers[notified_socket].extend(response.encode("utf-8") + b"\n")


        for notified_socket in writeable:
            if notified_socket in clients and len(client_send_buffers[notified_socket]) > 0:
                try:
                    sent = notified_socket.send(client_send_buffers[notified_socket])
                    client_send_buffers[notified_socket] = client_send_buffers[notified_socket][sent:]
                    user_id = clients[notified_socket].get('username') or notified_socket.getpeername()
                    print_strings(general_utils.verbose, f"SERVER: Sent {sent} bytes to {user_id}")
                except Exception as e:
                    print_strings(general_utils.verbose, f"SERVER: Error sending data to client: {e}")
                    delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)
        
        for notified_socket in exceptional:
            print_strings(general_utils.verbose, f"SERVER: Socket exception for client: {clients[notified_socket].get('address', 'unknown')}")
            delete_client(notified_socket, sockets_list, clients, client_send_buffers, clients_recv_buffers)


if __name__ == "__main__":
    main()
