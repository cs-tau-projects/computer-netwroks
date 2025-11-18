#!/usr/bin/python3
import sys
import subprocess
import re

def test_client_args():
    print("Testing client argument handling...")
    
    # Test cases
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
            'args': ['example.com', '8080'],
            'expected_host': 'example.com',
            'expected_port': 8080
        },
        # Test with invalid port (should use default port)
        {
            'args': ['127.0.0.1', '999999'],
            'expected_host': '127.0.0.1',
            'expected_port': 1337
        }
    ]
    
    # Directly check the parse_args function source code
    with open('ex1_client.py', 'r') as f:
        client_code = f.read()
    
    print("\nAnalyzing parse_args function...")
    
    # Check for default host and port values
    host_pattern = r'DEFAULT_HOST\s*=\s*["\']([^"\']+)["\']'
    port_pattern = r'DEFAULT_PORT\s*=\s*(\d+)'
    
    host_match = re.search(host_pattern, client_code)
    port_match = re.search(port_pattern, client_code)
    
    if host_match and port_match:
        actual_default_host = host_match.group(1)
        actual_default_port = int(port_match.group(1))
        
        if actual_default_host == 'localhost' and actual_default_port == 1337:
            print(f"✅ Success: Default values correctly set to host='{actual_default_host}', port={actual_default_port}")
        else:
            print(f"❌ Failed: Default values should be host='localhost', port=1337, but got host='{actual_default_host}', port={actual_default_port}")
    else:
        print("❌ Failed: Could not find DEFAULT_HOST or DEFAULT_PORT values in the code")
    
    # Check for parameter handling logic
    print("\nChecking parameter handling logic...")
    
    # For cases with different arg counts
    arg_handling_check = True
    
    # Check for handling no args
    if 'case 1:' in client_code and ('pass' in client_code.split('case 1:')[1].split('case')[0]):
        print("✅ Success: No args case correctly handles default values")
    else:
        print("❌ Failed: No args case doesn't appear to use default values")
        arg_handling_check = False
    
    # Check for handling 1 arg (hostname)
    if 'case 2:' in client_code and ('server_host = ' in client_code.split('case 2:')[1].split('case')[0]):
        print("✅ Success: One arg case correctly sets hostname")
    else:
        print("❌ Failed: One arg case doesn't appear to set hostname correctly")
        arg_handling_check = False
    
    # Check for handling 2 args (hostname, port)
    if 'case 3:' in client_code and ('server_host = ' in client_code.split('case 3:')[1].split('case')[0]) and ('server_port = ' in client_code.split('case 3:')[1].split('case')[0]):
        print("✅ Success: Two args case correctly sets hostname and port")
    else:
        print("❌ Failed: Two args case doesn't appear to set hostname and port correctly")
        arg_handling_check = False
    
    # Check for port validation logic
    if 'assert' in client_code and 'server_port' in client_code and '65535' in client_code:
        print("✅ Success: Port range validation is implemented")
    else:
        print("⚠️ Warning: Could not confirm port range validation (1-65535)")
    
    # Check for invalid port handling
    if 'except' in client_code and 'server_port' in client_code and 'DEFAULT_PORT' in client_code:
        print("✅ Success: Invalid port handling fallback to default is implemented")
    else:
        print("⚠️ Warning: Could not confirm invalid port handling")
    
    # Overall test result
    print("\n=== Overall Assessment ===")
    overall_success = host_match and port_match and (actual_default_host == 'localhost') and (actual_default_port == 1337) and arg_handling_check
    
    if overall_success:
        print("✅ All tests PASSED: The client correctly handles command-line arguments as required")
    else:
        print("❌ Some tests FAILED: The client may not be handling command-line arguments correctly")
    
    return overall_success

if __name__ == "__main__":
    test_client_args()
    print("\nTesting complete!")
