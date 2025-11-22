#!/usr/bin/python3

# Global verbose flag
verbose = False

def print_strings(verbose_flag, *strings):
    """
    Print multiple strings based on verbose mode setting.
    
    Args:
        verbose_flag (bool): If True, prints each string on a new line.
        *strings: Variable number of string arguments to print.
    """
    if verbose_flag:
        for string in strings:
            print(string, flush=True)
