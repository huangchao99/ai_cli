# -*- coding: utf-8 -*-

"""
Utility functions for the AI CLI tool.
"""

import sys
import logging
import os
from typing import Optional


def setup_logger(debug: bool = False) -> logging.Logger:
    """
    Set up and configure the logger.
    
    Args:
        debug: Whether to enable debug logging
        
    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if debug else logging.INFO
    
    logger = logging.getLogger("ai-cli")
    logger.setLevel(log_level)
    
    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


def stream_to_stdout(text: str):
    """
    Stream text to stdout with proper handling of encoding and flush.
    
    Args:
        text: The text to stream
    """
    try:
        # Write without newline and flush immediately
        sys.stdout.write(text)
        sys.stdout.flush()
    except (UnicodeEncodeError, IOError) as e:
        # Fall back to safe encoding if there's an issue
        print(f"\nWarning: Encoding error ({e}). Trying safe encoding.", file=sys.stderr)
        try:
            sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except (IOError, AttributeError) as e:
            print(f"\nError writing to stdout: {e}", file=sys.stderr)


def read_from_stdin() -> str:
    """
    Read and return all content from stdin.
    
    Returns:
        Content from stdin as a string
    """
    try:
        # Read everything from stdin
        content = sys.stdin.read()
        return content
    except UnicodeDecodeError:
        # Try binary mode if text mode fails
        sys.stdin.close()
        sys.stdin = open(0, 'rb')  # reopen stdin in binary mode
        return sys.stdin.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Error reading from stdin: {e}", file=sys.stderr)
        return ""


def read_file_content(file_path: str) -> str:
    """
    Read and return the content of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Content of the file as a string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with binary mode and different encoding
        with open(file_path, "rb") as f:
            content = f.read()
            
        # Try common encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
                
        # Fall back to replacing invalid characters
        return content.decode("utf-8", errors="replace")


def write_file_content(file_path: str, content: str) -> None:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Raises:
        IOError: If there's an error writing to the file
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def colorize(text: str, color: str) -> str:
    """
    Add ANSI color codes to text for terminal output.
    
    Args:
        text: Text to colorize
        color: Color name ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan')
        
    Returns:
        Colorized text for terminal display
    """
    colors = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'reset': '\033[0m',
    }
    
    # Only apply colors if output is a terminal
    if sys.stdout.isatty():
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    return text
