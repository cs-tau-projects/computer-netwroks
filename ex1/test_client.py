#!/usr/bin/python3
import socket
import json
import sys
import time
import threading
import argparse
import random
from concurrent.futures import ThreadPoolExecutor

# Default values
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1337
TIMEOUT = 5  # Socket timeout in seconds

class TestClient:
    def __init__(self, host, port, username, password, client_id=None):
        """Initialize a test client with server connection details and credentials."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id if client_id is not None else f"client-{random.randint(1000, 9999)}"
        self.socket = None
        self.connected = False
        self.authenticated = False
        self.recv_buffer = bytearray()
        self.verbose = False

    def log(self, message):
        """Print a log message if verbose mode is enabled."""
        if self.verbose:
            client_prefix = f"[{self.client_id}]" if self.client_id else ""
            print(f"{client_prefix} {message}")

    def connect(self):
        """Connect to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.log(f"Connected to server at {self.host}:{self.port}")
            
            # Receive welcome message
            welcome = self.receive_response()
            if not welcome or welcome.get("type") != "greeting":
                self.log(f"Error: Expected welcome message, got: {welcome}")
                return False
            return True
        except Exception as e:
            self.log(f"Connection error: {e}")
            return False

    def authenticate(self):
        """Authenticate with the server using provided credentials."""
        if not self.connected:
            self.log("Error: Not connected to server")
            return False

        try:
            # Send username
            username_message = json.dumps({"type": "login_username", "username": self.username})
            self.send_message(username_message)
            
            # Receive username acknowledgement
            username_response = self.receive_response()
            if not username_response:
                self.log("Error: No response after sending username")
                return False
            
            if username_response.get("type") == "login_failure":
                self.log(f"Authentication failed: Invalid username '{self.username}'")
                return False
            
            # Send password
            password_message = json.dumps({"type": "login_password", "password": self.password})
            self.send_message(password_message)
            
            # Receive authentication result
            auth_response = self.receive_response()
            if not auth_response:
                self.log("Error: No response after sending password")
                return False
            
            if auth_response.get("type") == "login_success":
                self.authenticated = True
                self.log(f"Successfully authenticated as {self.username}")
                return True
            else:
                self.log(f"Authentication failed: {auth_response.get('message', 'Unknown reason')}")
                return False
                
        except Exception as e:
            self.log(f"Authentication error: {e}")
            return False

    def send_message(self, message):
        """Send a message to the server."""
        if not self.connected:
            self.log("Error: Not connected to server")
            return False

        try:
            self.socket.sendall(message.encode('utf-8') + b"\n")
            self.log(f"Sent: {message}")
            return True
        except Exception as e:
            self.log(f"Send error: {e}")
            self.connected = False
            return False

    def receive_response(self):
        """Receive and parse a response from the server."""
        if not self.connected:
            self.log("Error: Not connected to server")
            return None

        try:
            while b"\n" not in self.recv_buffer:
                chunk = self.socket.recv(4096)
                if not chunk:
                    self.log("Connection closed by server")
                    self.connected = False
                    return None
                self.recv_buffer.extend(chunk)

            # Extract one complete message
            line, _, rest = self.recv_buffer.partition(b"\n")
            self.recv_buffer = rest

            try:
                response = json.loads(line.decode('utf-8'))
                self.log(f"Received: {response}")
                return response
            except json.JSONDecodeError:
                self.log(f"Error decoding response: {line}")
                return None
                
        except socket.timeout:
            self.log("Socket timeout while waiting for response")
            return None
        except Exception as e:
            self.log(f"Receive error: {e}")
            self.connected = False
            return None

    def disconnect(self):
        """Close the connection to the server."""
        if self.connected and self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.authenticated = False
        self.log("Disconnected from server")

    def test_parentheses(self, string):
        """Test the parentheses validation command."""
        if not self.authenticated:
            self.log("Error: Not authenticated")
            return False, None
            
        request = json.dumps({"type": "parentheses", "string": string})
        if not self.send_message(request):
            return False, None
            
        response = self.receive_response()
        if not response:
            return False, None
            
        if response.get("type") == "parentheses_result":
            return True, response.get("result")
        else:
            self.log(f"Unexpected response type: {response.get('type')}")
            return False, None

    def test_lcm(self, x, y):
        """Test the LCM calculation command."""
        if not self.authenticated:
            self.log("Error: Not authenticated")
            return False, None
            
        request = json.dumps({"type": "lcm", "x": x, "y": y})
        if not self.send_message(request):
            return False, None
            
        response = self.receive_response()
        if not response:
            return False, None
            
        if response.get("type") == "lcm_result":
            return True, response.get("result")
        else:
            self.log(f"Unexpected response type: {response.get('type')}")
            return False, None

    def test_caesar(self, text, shift):
        """Test the Caesar cipher command."""
        if not self.authenticated:
            self.log("Error: Not authenticated")
            return False, None
            
        request = json.dumps({"type": "caesar", "text": text, "shift": shift})
        if not self.send_message(request):
            return False, None
            
        response = self.receive_response()
        if not response:
            return False, None
            
        if response.get("type") == "caesar_result":
            return True, response.get("result")
        else:
            self.log(f"Unexpected response type: {response.get('type')}")
            return False, None

def test_send_unknown_command_before_auth(host, port, verbose=False):
    """Test sending unknown command before authentication."""
    print("\n=== Testing disconnection on unknown command before authentication ===")
    
    client = TestClient(host, port, "dummy", "dummy")
    client.verbose = verbose
    
    # Connect to server
    if not client.connect():
        print("✗ Connection test failed")
        return False
    print("✓ Connection test passed")
    
    # Send an unknown command instead of authentication
    unknown_command = json.dumps({"type": "parentheses", "string": "()"})
    if not client.send_message(unknown_command):
        print("✗ Failed to send message")
        client.disconnect()
        return False
    
    # Try to receive a response, but we expect the server to close the connection
    response = client.receive_response()
    
    # The connection should be closed
    if client.connected:
        print("✗ Test failed: Server did not disconnect client after unknown command before authentication")
        client.disconnect()
        return False
    else:
        print("✓ Test passed: Server correctly disconnected client after unknown command before authentication")
        return True

def test_send_unknown_command_after_username(host, port, username, verbose=False):
    """Test sending unknown command after username but before password."""
    print("\n=== Testing disconnection on unknown command after username ===")
    
    client = TestClient(host, port, username, "dummy")
    client.verbose = verbose
    
    # Connect to server
    if not client.connect():
        print("✗ Connection test failed")
        return False
    print("✓ Connection test passed")
    
    # Send username
    username_message = json.dumps({"type": "login_username", "username": username})
    if not client.send_message(username_message):
        print("✗ Failed to send username")
        client.disconnect()
        return False
    
    # Receive response to username
    response = client.receive_response()
    if not response or response.get("type") != "continue":
        print("✗ Username not accepted")
        client.disconnect()
        return False
    
    # Send an unknown command instead of password
    unknown_command = json.dumps({"type": "lcm", "x": "5", "y": "10"})
    if not client.send_message(unknown_command):
        print("✗ Failed to send message")
        client.disconnect()
        return False
    
    # Try to receive a response, but we expect the server to close the connection
    response = client.receive_response()
    
    # The connection should be closed
    if client.connected:
        print("✗ Test failed: Server did not disconnect client after unknown command after username")
        client.disconnect()
        return False
    else:
        print("✓ Test passed: Server correctly disconnected client after unknown command after username")
        return True

def test_invalid_auth(host, port, verbose=False):
    """Test authentication with invalid credentials."""
    print("\n=== Testing authentication with invalid credentials ===")
    
    tests = [
        # Test with invalid username
        ("NonexistentUser", "anypassword", "Invalid username test"),
        # Test with valid username but wrong password
        ("Alice", "wrongpassword", "Wrong password test")
    ]
    
    all_passed = True
    for username, password, test_name in tests:
        client = TestClient(host, port, username, password)
        client.verbose = verbose
        
        # Connect to server
        if not client.connect():
            print(f"✗ {test_name}: Connection failed")
            all_passed = False
            continue
        
        # Try to authenticate
        if client.authenticate():
            print(f"✗ {test_name}: Authentication succeeded when it should have failed")
            all_passed = False
        else:
            print(f"✓ {test_name}: Authentication correctly failed")
        
        client.disconnect()
    
    return all_passed

def test_send_invalid_command_format(host, port, username, password, verbose=False):
    """Test sending commands with invalid format."""
    print("\n=== Testing commands with invalid format ===")
    
    client = TestClient(host, port, username, password)
    client.verbose = verbose
    
    # Connect and authenticate
    if not client.connect() or not client.authenticate():
        print("✗ Connection or authentication failed")
        client.disconnect()
        return False
    
    tests = [
        # Missing parameter
        (json.dumps({"type": "lcm", "x": "5"}), "Missing parameter test"),
        # Invalid JSON format (sent as string without proper escaping)
        ("{type: lcm, x: 5, y: 10}", "Invalid JSON test"),
        # Unknown command type
        (json.dumps({"type": "unknown_command", "param": "value"}), "Unknown command type test")
    ]
    
    all_passed = True
    for command, test_name in tests:
        # Send command with invalid format
        if not client.send_message(command):
            print(f"✗ {test_name}: Failed to send message")
            all_passed = False
            continue
        
        # Receive response
        response = client.receive_response()
        
        # Check that server responded with an error and didn't crash
        if not response or not client.connected:
            print(f"✗ {test_name}: Server disconnected or no response")
            all_passed = False
        elif response.get("type") != "error":
            print(f"✗ {test_name}: Expected error response, got {response}")
            all_passed = False
        else:
            print(f"✓ {test_name}: Server correctly returned error response")
    
    client.disconnect()
    return all_passed

def run_single_client_test(host, port, username, password, verbose=False):
    """Run tests using a single client."""
    print("\n=== Running single client tests ===")
    
    client = TestClient(host, port, username, password)
    client.verbose = verbose
    
    # Connect to server
    if not client.connect():
        print("✗ Connection test failed")
        return False
    print("✓ Connection test passed")
    
    # Authenticate
    if not client.authenticate():
        print("✗ Authentication test failed")
        client.disconnect()
        return False
    print("✓ Authentication test passed")
    
    # Test parentheses validation
    test_cases = [
        ("()", True),
        ("(())", True),
        ("(()())", True),
        ("(()", False),
        ("())", False),
        ("(()))", False),
        ("((()))()(())", True)
    ]
    
    all_passed = True
    for string, expected in test_cases:
        success, result = client.test_parentheses(string)
        if not success or result != expected:
            print(f"✗ Parentheses test failed for '{string}': expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"✓ Parentheses test passed for '{string}'")
    
    # Test LCM calculation
    test_cases = [
        ("6", "8", 24),
        ("15", "25", 75),
        ("6", "21", 42),
        ("17", "19", 323),
        ("0", "5", 0),
        ("12", "18", 36)
    ]
    
    for x, y, expected in test_cases:
        success, result = client.test_lcm(x, y)
        if not success or result != expected:
            print(f"✗ LCM test failed for {x},{y}: expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"✓ LCM test passed for {x},{y}")
    
    # Test Caesar cipher
    test_cases = [
        ("hello", 2, "jgnnq"),
        ("abcxyz", 3, "defabc"),
        ("Caesar Cipher", 7, "jhlzhy jpwoly"),  # Expecting lowercase conversion
        ("abcdefghijklmnopqrstuvwxyz", 13, "nopqrstuvwxyzabcdefghijklm")
    ]
    
    for text, shift, expected in test_cases:
        success, result = client.test_caesar(text, shift)
        if expected is None:  # Expecting an error
            if success:
                print(f"✗ Caesar test failed for '{text}',{shift}: expected error, got {result}")
                all_passed = False
            else:
                print(f"✓ Caesar test correctly failed for '{text}',{shift}")
        elif not success or result != expected:
            print(f"✗ Caesar test failed for '{text}',{shift}: expected '{expected}', got '{result}'")
            all_passed = False
        else:
            print(f"✓ Caesar test passed for '{text}',{shift}")
    
    client.disconnect()
    
    if all_passed:
        print("\n✓ All single client tests passed")
    else:
        print("\n✗ Some tests failed")
    
    return all_passed

def stress_test_worker(args, client_id):
    """Worker function for stress testing."""
    host, port, username, password, iterations, delay, verbose = args
    
    client = TestClient(host, port, username, password, client_id)
    client.verbose = verbose
    
    success_count = 0
    failure_count = 0
    
    try:
        # Connect and authenticate
        if client.connect() and client.authenticate():
            for i in range(iterations):
                # Choose a random test to perform
                test_type = random.choice(['parentheses', 'lcm', 'caesar'])
                
                if test_type == 'parentheses':
                    # Generate a random parentheses string
                    length = random.randint(2, 20)
                    chars = ["(", ")"]
                    string = ''.join(random.choice(chars) for _ in range(length))
                    success, _ = client.test_parentheses(string)
                    
                elif test_type == 'lcm':
                    # Generate random numbers for LCM
                    x = str(random.randint(1, 100))
                    y = str(random.randint(1, 100))
                    success, _ = client.test_lcm(x, y)
                    
                else:  # caesar
                    # Generate a random text for Caesar cipher
                    length = random.randint(5, 20)
                    chars = [chr(ord('a') + i) for i in range(26)]
                    text = ''.join(random.choice(chars) for _ in range(length))
                    shift = random.randint(1, 25)
                    success, _ = client.test_caesar(text, shift)
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    
                # Small delay between requests to prevent overwhelming server
                time.sleep(delay)
        else:
            print(f"Client {client_id} failed to connect or authenticate")
            failure_count += 1
            
    except Exception as e:
        print(f"Client {client_id} error: {e}")
        failure_count += 1
    finally:
        client.disconnect()
        
    return client_id, success_count, failure_count

def run_stress_test(host, port, username, password, num_clients=5, iterations=20, delay=0.1, verbose=False):
    """Run a stress test with multiple clients connecting simultaneously."""
    print(f"\n=== Running stress test with {num_clients} clients, {iterations} iterations each ===")
    
    args = (host, port, username, password, iterations, delay, verbose)
    futures = []
    
    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        for i in range(num_clients):
            client_id = f"stress-{i+1}"
            futures.append(executor.submit(stress_test_worker, args, client_id))
    
    total_success = 0
    total_failure = 0
    
    for future in futures:
        client_id, success_count, failure_count = future.result()
        print(f"Client {client_id}: {success_count} successful, {failure_count} failed operations")
        total_success += success_count
        total_failure += failure_count
    
    print(f"\nStress test completed: {total_success} successful, {total_failure} failed operations")
    success_rate = (total_success / (total_success + total_failure)) * 100 if total_success + total_failure > 0 else 0
    print(f"Success rate: {success_rate:.2f}%")
    
    return total_failure == 0

def run_sad_path_tests(host, port, username, password, verbose=False):
    """Run sad path tests to verify server handles error cases correctly."""
    print("\n=== Running sad path tests ===")
    
    # Test sending unknown command before authentication
    unknown_cmd_before_auth = test_send_unknown_command_before_auth(host, port, verbose)
    
    # Test sending unknown command after username but before password
    unknown_cmd_after_username = test_send_unknown_command_after_username(host, port, username, verbose)
    
    # Test authentication with invalid credentials
    invalid_auth = test_invalid_auth(host, port, verbose)
    
    # Test sending commands with invalid format
    invalid_cmd_format = test_send_invalid_command_format(host, port, username, password, verbose)
    
    all_passed = all([unknown_cmd_before_auth, unknown_cmd_after_username, invalid_auth, invalid_cmd_format])
    
    if all_passed:
        print("\n✓ All sad path tests passed")
    else:
        print("\n✗ Some sad path tests failed")
    
    return all_passed

def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description='Test script for client-server program')
    parser.add_argument('--host', default=DEFAULT_HOST, help=f'Server hostname (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Server port (default: {DEFAULT_PORT})')
    parser.add_argument('--username', default='Alice', help='Username for authentication')
    parser.add_argument('--password', default='BetT3RpAas', help='Password for authentication')
    parser.add_argument('--clients', type=int, default=5, help='Number of clients for stress testing')
    parser.add_argument('--iterations', type=int, default=20, help='Number of operations per client in stress test')
    parser.add_argument('--stress-only', action='store_true', help='Run only the stress test')
    parser.add_argument('--single-only', action='store_true', help='Run only the single client test')
    parser.add_argument('--sad-only', action='store_true', help='Run only the sad path tests')
    parser.add_argument('--skip-sad', action='store_true', help='Skip the sad path tests')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    results = []
    
    # Run single client test (happy path)
    if not args.stress_only and not args.sad_only:
        single_client_success = run_single_client_test(
            args.host, args.port, args.username, args.password, args.verbose
        )
        results.append(("Single client test", single_client_success))
    
    # Run sad path tests
    if not args.stress_only and not args.single_only and not args.skip_sad:
        sad_path_success = run_sad_path_tests(
            args.host, args.port, args.username, args.password, args.verbose
        )
        results.append(("Sad path tests", sad_path_success))
    
    # Run stress test
    if not args.single_only and not args.sad_only:
        stress_test_success = run_stress_test(
            args.host, args.port, args.username, args.password, 
            args.clients, args.iterations, verbose=args.verbose
        )
        results.append(("Stress test", stress_test_success))
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")
        all_passed = all_passed and success
    
    # Return exit code based on test results
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
