import math
import sys



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
    Output is always lowercase. If invalid chars found, return None.
    """
    result = []
    for ch in text:
        if ch == " ":
            result.append(" ")
        elif ch.isalpha():
            c = ch.lower()
            k = (ord(c) - 97 + shift) % 26
            result.append(chr(97 + k))
        else:
            return None
    return "".join(result)


def is_valid_port(port):
    """
    Check if a port number is valid (1-65535).
    """
    return isinstance(port, int) and 1 <= port <= 65535


def read_args():
    """
    Read command-line arguments for port number.
    Returns the port number or None if invalid.
    """

    DEFAULT_PORT = 1337

    match len(sys.argv):
        case 1:
            return DEFAULT_PORT
        case 2:
            port = int(sys.argv[1])
            if is_valid_port(port):
                return port
            else:
                return None
        case _:
            return None
        
    return "".join(result)
