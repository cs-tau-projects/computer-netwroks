def handle_ceasar_input(line):
    """Helper function to validate Caesar cipher input."""
    if not line or not line.strip():
        return None
    
    # Try to find the last space in the line
    try:
        last_space_index = line.rstrip().rfind(' ')
        if last_space_index == -1:  # No spaces found
            return None
        
        # Extract the sentence and the number
        sentence = line[:last_space_index]
        number_str = line[last_space_index + 1:].strip()
        
        # Check if the last part is a number
        try:
            number = int(number_str)
            return (sentence, number)
        except ValueError:
            # The last part is not a number
            return None
    except Exception:
        # Any other error, return None
        return None
