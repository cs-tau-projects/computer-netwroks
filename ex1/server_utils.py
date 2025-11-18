import math, sys, json, os

DEFAULT_PORT = 1337


def load_users(path):
    """
    Load users from a tab-delimited text file (username<TAB>password).
    Ignores blank lines.
    Returns a dict of {username: password}.
    """
    users = {}
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            username, password = parts
            users[username.strip()] = password.strip()
    return users


def balanced_parentheses(s):
    """
    Check if a parentheses string is balanced.
    Returns True for balanced, False for unbalanced, and None for invalid input.
    """
    if any(ch not in ("(", ")") for ch in s):
        return None
    count = 0
    for ch in s:
        if ch == "(":
            count += 1
        elif ch == ")":
            count -= 1
            if count < 0:
                return False
    return count == 0


def lcm(x, y):
    """
    Compute least common multiple for two signed ints.
    """
    if x == 0 or y == 0:
        return 0
    return abs(x * y) // math.gcd(x, y)


def caesar(text, shift):
    """
    Caesar cipher. Only lowercase/uppercase letters and spaces are allowed.
    Output is always lowercase. Handles both positive and negative shifts.
    If invalid chars found, return None.
    """
    result = []
    # Handle negative shifts by converting to equivalent positive shift
    shift = shift % 26
    
    for ch in text:
        if ch == " ":
            result.append(" ")
        elif ch.isalpha():
            c = ch.lower()
            k = (ord(c) - ord('a') + shift) % 26
            result.append(chr(ord('a') + k))
        else:
            return None
    return "".join(result)


def parse_args():
    """
    Read command-line arguments for port number.
    Returns the port number or None if invalid.
    """

    if not (2 <= len(sys.argv) <= 3):
        print(f"Usage: {os.path.basename(sys.argv[0])} users_file [port]")
        sys.exit(1)
    users_file = sys.argv[1]
    if not os.path.isfile(users_file):
        print(f"Users file not found: {users_file}")
        sys.exit(1)
    port = DEFAULT_PORT
    if len(sys.argv) == 3:
        try:
            p = int(sys.argv[2]); assert 1 <= p <= 65535
            port = p
        except Exception:
            print(f"Invalid port number. Using default port {DEFAULT_PORT}.")
    return users_file, port
        

# Handler function for server.py


def handle_lcm(data):
    try:
        x = int(data.get("x"))
        y = int(data.get("y"))
    except (TypeError, ValueError):
        return json.dumps({"type": "error", "message": "Invalid parameters for LCM."})
    result = lcm(x, y)
    return json.dumps({"type": "lcm_result", "result": result})


def handle_parentheses(data):
    s = data.get("string")
    if not isinstance(s, str):
        return json.dumps({"type": "error", "message": "Invalid parameters for parentheses check."})
    result = balanced_parentheses(s)
    if result is None:
        return json.dumps({"type": "error", "message": "String contains invalid characters."})
    return json.dumps({"type": "parentheses_result", "result": result})


def handle_caesar(data):
    text = data.get("text")
    try:
        shift = int(data.get("shift"))
    except (TypeError, ValueError):
        return json.dumps({"type": "error", "message": "Invalid parameters for LCM."})
    if not isinstance(text, str) or not isinstance(shift, int):
        return json.dumps({"type": "error", "message": "Invalid parameters for Caesar cipher."})
    result = caesar(text, shift)
    if result is None:
        return json.dumps({"type": "error", "message": "error: invalid input"})
    return json.dumps({"type": "caesar_result", "result": result})
