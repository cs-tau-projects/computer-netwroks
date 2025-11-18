#!/usr/bin/python3
import os
import sys
import subprocess
import time
import socket
import threading
import signal

# Test if a port is available
def is_port_available(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.bind(('localhost', port))
        sock.close()
        return True
    except:
        return False

# Find an available port for testing
def find_available_port():
    for port in range(8000, 9000):
        if is_port_available(port):
            return port
    raise Exception("Could not find an available port")

# Simple echo server for testing connections
def run_echo_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)
    
    def accept_connection():
        while True:
            try:
                client, _ = server.accept()
                client.sendall(b'{"type": "greeting", "message": "Test server"}\n')
                client.close()
            except:
                break
    
    thread = threading.Thread(target=accept_connection)
    thread.daemon = True
    thread.start()
    return server, thread

# More direct testing approach by modifying the client temporarily
def test_client_args():
    print("Testing client argument handling...")
    
    # Create a temporary test version of the client
    temp_client_path = 'test_client_args.py'
    with open('ex1_client.py', 'r') as source_file:
        client_code = source_file.read()
        
    # Modify the client code to only print the host and port and exit
    modified_client_code = client_code.replace(
        'def main():',
        '''def main():
    # TEST VERSION - Only print args and exit
    server_host, server_port = parse_args()
    print(f"TEST_OUTPUT: host={server_host}, port={server_port}")
    sys.exit(0)
    # Original code continues below
''')
    
    with open(temp_client_path, 'w') as test_file:
        test_file.write(modified_client_code)
    
    try:
        tests = [
            # Test with no args (should use localhost:1337)
            {
                'args': [],
                'expected_host': 'localhost',
                'expected_port': 1337
            },
            # Test with hostname only (should use specified host and default port 1337)
            {
                'args': ['127.0.0.1'],
                'expected_host': '127.0.0.1',
                'expected_port': 1337
            },
            # Test with hostname and port (should use both specified values)
            {
                'args': ['127.0.0.1', '8080'],
                'expected_host': '127.0.0.1',
                'expected_port': 8080
            },
            # Test with invalid port (should use default port)
            {
                'args': ['127.0.0.1', '999999'],
                'expected_host': '127.0.0.1',
                'expected_port': 1337
            }
        ]
        
        for i, test in enumerate(tests):
            print(f"\nTest {i+1}: {' '.join(['./test_client_args.py'] + test['args'])}")
            
            # Start the modified client process
            cmd = [sys.executable, temp_client_path] + test['args']
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            stdout = proc.stdout
            stderr = proc.stderr
            
            if stderr:
                print(f"Stderr: {stderr}")
            
            # Look for the special TEST_OUTPUT line
            result_line = None
            for line in stdout.splitlines():
                if "TEST_OUTPUT:" in line:
                    result_line = line
                    break
            
            if result_line:
                # Extract host and port from the output
                import re
                match = re.search(r'host=([^,]+), port=(\d+)', result_line)
                if match:
                    actual_host = match.group(1)
                    actual_port = int(match.group(2))
                    
                    if (actual_host == test['expected_host'] and 
                        actual_port == test['expected_port']):
                        print(f"✅ Success: Found expected host={actual_host}, port={actual_port}")
                    else:
                        print(f"❌ Failed: Expected host={test['expected_host']}, port={test['expected_port']}, "
                              f"but got host={actual_host}, port={actual_port}")
                else:
                    print(f"❌ Failed: Could not parse host and port from output line: {result_line}")
            else:
                print(f"❌ Failed: Could not find test output line in output")
                print(f"Full output was:\n{stdout}")
    
    finally:
        # Clean up
        try:
            os.remove(temp_client_path)
        except:
            pass

if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    test_client_args()
    print("\nTesting complete!")
