# Client-Server Testing Suite

This repository contains a comprehensive testing suite for the client-server application. The testing suite includes both functional testing and stress testing capabilities.

## Test Script Overview

The `test_client.py` script provides two main testing capabilities:

1. **Single Client Functional Testing**: Verifies that all required functionality works correctly
2. **Multi-Client Stress Testing**: Tests server performance and stability when multiple clients connect simultaneously

## Requirements Tested

The test script verifies all the requirements specified in the exercise:

- Server connection and client authentication
- Parentheses validation function
- LCM (Least Common Multiple) calculation
- Caesar cipher encryption
- Multiple concurrent client support

## How to Run the Tests

### Prerequisites

- Python 3.x
- The server must be running before executing tests

### Starting the Server

First, start the server:

```bash
python3 server.py users_file.txt [port]
```

### Running the Test Script

Run the test script:

```bash
python3 test_client.py [options]
```

### Command Line Arguments

The test script accepts the following command-line arguments:

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | Server hostname | 127.0.0.1 |
| `--port` | Server port | 1337 |
| `--username` | Username for authentication | Alice |
| `--password` | Password for authentication | BetT3RpAas |
| `--clients` | Number of clients for stress testing | 5 |
| `--iterations` | Number of operations per client in stress test | 20 |
| `--stress-only` | Run only the stress test | False |
| `--single-only` | Run only the single client test | False |
| `--verbose` | Enable verbose output | False |

### Examples

Run all tests with default settings:

```bash
python3 test_client.py
```

Run only the stress test with 10 clients, each performing 50 operations:

```bash
python3 test_client.py --stress-only --clients 10 --iterations 50
```

Run only the single client test with detailed output:

```bash
python3 test_client.py --single-only --verbose
```

## Test Script Details

### Single Client Test

The single client test performs the following verifications:

1. Connects to the server
2. Authenticates with provided credentials
3. Tests the parentheses validation functionality with various test cases
4. Tests the LCM calculation with multiple number pairs
5. Tests the Caesar cipher with different texts and shift values
6. Tests error handling for invalid inputs

### Stress Test

The stress test:

1. Creates multiple client connections simultaneously (default: 5)
2. Each client authenticates and performs multiple operations (default: 20)
3. Operations are randomly selected between parentheses validation, LCM calculation, and Caesar cipher
4. Reports success/failure statistics for each client and overall
5. Tests server stability under concurrent load

## Test Output

The test script provides detailed output about:

- Connection and authentication status
- Test case results (pass/fail)
- For stress testing: per-client and overall success rates
- Summary of all test results

A non-zero exit code is returned if any test fails, making the script suitable for automated testing environments.
