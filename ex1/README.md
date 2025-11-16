# Networking HW-1 Protocol described
## Server - Client Communication:
all the data is being transfered via JSON, Every function/data type as described:
- **Flags and Messages**
    - Login Success =   {"type": "login_success", "message": f"Hi, {username}, good to see you."}
    - Login Failure =   {"type": "login_failure", "message": "Failed to login."}
    - error message =   {"type": "error", "message": "example_error_message"}
    - continue =        {"type": "continue", "message": ""}

- **functions request**
    - User: username_of_user =      {"type": "login_username", "username": "example_username"}
    - Password: password_of_user =  {"type": "login_password", "password": "example_password"}
    - Parentheses: X =              {"type": "parentheses", "string": example_string_of_parentheses}
    - Lcm: X Y =                    {"type": "lcm", "x": example_x, "y": example_y}
    - Caesar: plaintext X =         {"type": "caesar", "text": example_string, "shift": example_shift}
    - quit =                        "quit"

- **functions response**
    - Parentheses: X =      {"type": "parentheses_result", "balanced": result}
    - Lcm: X Y =            {"type": "lcm_result", "result": result}
    - Caesar: plaintext X = {"type": "caesar_result", "result": result}

