#!/usr/bin/python3

import socket
import sys
import select
import general_utils
from general_utils import print_strings
from client_utils import parse_args, delete_client, handle_server_input, BURST_SIZE

def main():
    print_strings(general_utils.verbose, 
        "=" * 60,
        "CLIENT: Starting authentication client",
        "CLIENT GUIDE: To log in, use format: User: username",
        "CLIENT GUIDE: After username is accepted, you can simply type your password",
        "=" * 60
    )

    server_host, server_port = parse_args()
    print_strings(general_utils.verbose, f"CLIENT: Connecting to server at {server_host}:{server_port}")
    send_buf = bytearray()
    recv_buf = bytearray()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(3)  # Set a 3-second timeout for connection

    client_state = {
        "auth_state": 0,  # 0: not authenticated, 1: sent username, 2: authenticated
        "username": None
    }

    try:
        client_socket.connect((server_host, server_port))
        print_strings(general_utils.verbose, "CLIENT: Successfully connected to server")
    except (OSError, socket.timeout) as e:
        print(f"CONNECTION ERROR: Could not connect to {server_host}:{server_port} - {e}")
        print_strings(general_utils.verbose, f"CLIENT: Connection failed - {e}")
        sys.exit(1)

    while True:
        readable, writable, _ = select.select([client_socket], [client_socket], [client_socket])

        if client_socket in readable:
            message = client_socket.recv(BURST_SIZE)
            if not message:
                print_strings(general_utils.verbose, "CLIENT: Server closed connection")
                delete_client(client_socket)

            print_strings(general_utils.verbose, f"CLIENT: Received {len(message)} bytes from server")
            recv_buf.extend(message)
            if b"\n" in recv_buf:
                line, _, rest = recv_buf.partition(b"\n")
                recv_buf = bytearray(rest)
                print_strings(general_utils.verbose, "CLIENT: Processing complete message from server")
                valid = 0
                while not valid:
                    response, val = handle_server_input(line, client_state)
                    if val == 0:
                        send_buf.extend(response.encode('utf-8') + b"\n")
                        valid = 1
                    elif val == -1:
                        print_strings(general_utils.verbose, "Invalid user input, try again")
                        # Mark that we should skip displaying the previous response
                        client_state["last_response_cleared"] = True
                    elif val == -2:
                        delete_client(client_socket)

        if client_socket in writable and len(send_buf) > 0:
            try:
                sent = client_socket.send(send_buf)
                send_buf = send_buf[sent:]
                print_strings(general_utils.verbose, f"CLIENT: Sent {sent} bytes to server")
            except BrokenPipeError:
                delete_client(client_socket)


if __name__ == "__main__":
    main()
