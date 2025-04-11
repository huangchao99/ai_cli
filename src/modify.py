# -*- coding: utf-8 -*-

"""
Implementation of the modify mode for the AI CLI tool.
"""

import os
import sys
import tempfile
import subprocess
from typing import List, Tuple, Optional

from .api import DeepSeekClient
from .utils import colorize, write_file_content


def parse_diff(diff_text: str) -> List[Tuple[int, str, str]]:
    """
    Parse a unified diff format into a list of chunks.
    
    Args:
        diff_text: The diff text in unified format
        
    Returns:
        List of tuples (line_num, original, modified) where line_num is the starting line
    """
    # Find diff chunks if they exist
    chunks = []
    current_chunk = None
    line_num = None
    
    # Handle potential code blocks in the response
    if "```diff" in diff_text:
        # Extract the content between diff code blocks
        start = diff_text.find("```diff")
        end = diff_text.find("```", start + 7)
        if end > start:
            diff_text = diff_text[start + 7:end].strip()
    elif "```" in diff_text:
        # Extract the content between generic code blocks
        start = diff_text.find("```")
        end = diff_text.find("```", start + 3)
        if end > start:
            diff_text = diff_text[start + 3:end].strip()
    
    # Clean up the diff text by removing any explanatory text or unnecessary content
    lines = diff_text.splitlines()
    
    # Extract only the diff-related lines
    in_diff_section = False
    diff_lines = []
    
    # Consider lines with diff markers as potential diff content
    for i, line in enumerate(lines):
        line = line.rstrip()
        # Check for diff header markers
        if line.startswith("--- ") or line.startswith("+++ "):
            in_diff_section = True
            diff_lines.append(line)
        # Check for diff hunk markers
        elif line.startswith("@@") and "@@" in line[2:]:
            in_diff_section = True
            diff_lines.append(line)
            
            # Extract line number
            try:
                # Parse the line number from the @@ -X,Y +X,Y @@ format
                hunk_info = line.split("@@")[1].strip()
                original_range = hunk_info.split(" ")[0]
                line_num = int(original_range.split(",")[0][1:])  # Remove the '-' prefix
            except (IndexError, ValueError):
                line_num = 1
        # Handle diff content lines
        elif in_diff_section or line.startswith("+") or line.startswith("-") or line.startswith(" "):
            diff_lines.append(line)
    
    # If no diff section markers found but there are +/- lines, include all lines as a basic diff
    if not in_diff_section and any(line.startswith("+") or line.startswith("-") for line in lines):
        diff_lines = lines
        line_num = 1  # Default starting line
    
    # If we have anything in diff_lines, assume it could be a diff
    if diff_lines:
        # Process the cleaned diff lines
        original_chunk = []
        modified_chunk = []
        
        # Process by chunks separated by hunk headers
        current_line_num = 1
        
        for line in diff_lines:
            # Skip empty lines in the diff
            if not line.strip():
                continue
                
            # Process hunk headers
            if line.startswith("@@"):
                if current_chunk is not None and (original_chunk or modified_chunk):
                    chunks.append((current_chunk, "\n".join(original_chunk), "\n".join(modified_chunk)))
                    original_chunk = []
                    modified_chunk = []
                
                # Extract line number
                try:
                    hunk_info = line.split("@@")[1].strip()
                    original_range = hunk_info.split(" ")[0]
                    current_line_num = int(original_range.split(",")[0][1:])  # Remove the '-' prefix
                except (IndexError, ValueError):
                    current_line_num = 1
                    
                current_chunk = current_line_num
            # Skip file headers
            elif line.startswith("---") or line.startswith("+++"):
                continue
            # Process removed lines
            elif line.startswith("-"):
                original_chunk.append(line[1:])
            # Process added lines
            elif line.startswith("+"):
                modified_chunk.append(line[1:])
            # Process context lines (unchanged)
            else:
                # Remove the space prefix if it exists
                content_line = line[1:] if line.startswith(" ") else line
                original_chunk.append(content_line)
                modified_chunk.append(content_line)
        
        # Add the last chunk if there's anything left
        if current_chunk is not None and (original_chunk or modified_chunk):
            chunks.append((current_line_num, "\n".join(original_chunk), "\n".join(modified_chunk)))
    
    # If no chunks were identified and the text isn't empty, try to use the whole content as a single change
    if not chunks and diff_text.strip():
        # Use the whole diff_text as a suggested replacement
        chunks = [(1, diff_text, diff_text)]
    
    return chunks


def display_diff(file_path: str, chunks: List[Tuple[int, str, str]]) -> None:
    """
    Display diff chunks in a user-friendly format.
    
    Args:
        file_path: Path to the file being modified
        chunks: List of diff chunks as returned by parse_diff
    """
    print()
    print(colorize(f"--- {file_path} (原始版本)", "red"))
    print(colorize(f"+++ {file_path} (AI建议)", "green"))
    
    for i, (line_num, original, modified) in enumerate(chunks):
        print(colorize(f"@@ -{line_num},{len(original.splitlines()) if original else 0} "
              f"+{line_num},{len(modified.splitlines()) if modified else 0} @@", "cyan"))
        
        # Display the original content with '-' prefix
        if original:
            for line in original.splitlines():
                print(colorize(f"-{line}", "red"))
        
        # Display the modified content with '+' prefix
        if modified:
            for line in modified.splitlines():
                print(colorize(f"+{line}", "green"))
        
        print()


def apply_changes(file_path: str, content: str, chunks: List[Tuple[int, str, str]], 
                 selected_chunks: List[int] = None) -> str:
    """
    Apply selected diff chunks to the file content.
    
    Args:
        file_path: Path to the file being modified
        content: Original file content
        chunks: List of diff chunks as returned by parse_diff
        selected_chunks: List of chunk indices to apply (default: all)
        
    Returns:
        Modified content with changes applied
    """
    if not chunks:
        return content
        
    if selected_chunks is None:
        selected_chunks = list(range(len(chunks)))
        
    # Convert content to lines for easier manipulation
    lines = content.splitlines()
    
    # Apply changes in reverse order to avoid line number shifts
    for chunk_idx in sorted(selected_chunks, reverse=True):
        if chunk_idx >= len(chunks):
            continue
            
        line_num, original, modified = chunks[chunk_idx]
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        # Adjust line_num to be 0-based
        line_idx = line_num - 1
        
        # Remove original lines and insert modified lines
        del lines[line_idx:line_idx + len(original_lines)]
        lines[line_idx:line_idx] = modified_lines
    
    # Preserve the file's line ending behavior
    if content and content.endswith("\n"):
        return "\n".join(lines) + "\n"
    else:
        return "\n".join(lines)


def edit_chunk(chunk_content: str) -> str:
    """
    Open an editor for the user to edit a diff chunk.
    
    Args:
        chunk_content: Content of the chunk to edit
        
    Returns:
        Edited chunk content
    """
    editor = os.environ.get("EDITOR", "vim")
    
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as temp:
        temp_path = temp.name
        temp.write(chunk_content)
    
    try:
        subprocess.run([editor, temp_path], check=True)
        with open(temp_path, "r") as f:
            edited_content = f.read()
        return edited_content
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def process_modify_request(client: DeepSeekClient, file_path: str, content: str, 
                          prompt: str, input_text: Optional[str] = None) -> int:
    """
    Process a modification request.
    
    Args:
        client: DeepSeekClient instance
        file_path: Path to the file to modify
        content: Content of the file
        prompt: Modification prompt
        input_text: Optional additional context
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Generate a diff from the model
        diff_text = client.generate_diff(content, prompt, input_text)
        
        # Parse the diff
        chunks = parse_diff(diff_text)
        
        if not chunks:
            print("No changes were suggested by the model.")
            return 0
        
        # Display the diff
        display_diff(file_path, chunks)
        
        # Interactive mode to handle changes
        if sys.stdout.isatty():
            while True:
                print(colorize("\n交互选项:", "cyan"))
                print("[1] 接受修改   [2] 拒绝   [3] 编辑   [4] 拆分应用")
                choice = input(colorize("[?] 请选择操作 (默认1): ", "yellow") or "1")
                
                if choice == "1":
                    # Apply all changes
                    modified_content = apply_changes(file_path, content, chunks)
                    write_file_content(file_path, modified_content)
                    print(f"\n修改已应用到 {file_path}")
                    break
                elif choice == "2":
                    # Reject changes
                    print("\n修改已拒绝")
                    return 0
                elif choice == "3":
                    # Edit the changes
                    new_chunks = []
                    for i, (line_num, original, modified) in enumerate(chunks):
                        print(f"\n编辑第 {i+1} 个修改块:")
                        edited_modified = edit_chunk(modified)
                        new_chunks.append((line_num, original, edited_modified))
                    
                    chunks = new_chunks
                    display_diff(file_path, chunks)
                    
                    apply_choice = input(colorize("\n应用这些编辑后的修改? [Y/n]: ", "yellow") or "y").lower()
                    if apply_choice != "n":
                        modified_content = apply_changes(file_path, content, chunks)
                        write_file_content(file_path, modified_content)
                        print(f"\n编辑后的修改已应用到 {file_path}")
                    break
                elif choice == "4":
                    # Split and apply specific changes
                    selected_chunks = []
                    for i, (line_num, original, modified) in enumerate(chunks):
                        print(f"\n区块 {i+1}:")
                        print(colorize(f"--- 原始", "red"))
                        for line in original.splitlines():
                            print(colorize(f"- {line}", "red"))
                        print(colorize(f"+++ 修改", "green"))
                        for line in modified.splitlines():
                            print(colorize(f"+ {line}", "green"))
                            
                        apply_choice = input(colorize(f"应用此区块? [Y/n]: ", "yellow") or "y").lower()
                        if apply_choice != "n":
                            selected_chunks.append(i)
                    
                    if selected_chunks:
                        modified_content = apply_changes(file_path, content, chunks, selected_chunks)
                        write_file_content(file_path, modified_content)
                        print(f"\n已选择的修改已应用到 {file_path}")
                    else:
                        print("\n没有应用任何修改")
                    break
                else:
                    print("\n无效选择，请重试")
        else:
            # Non-interactive mode - just show the diff
            return 0
            
        return 0
    except Exception as e:
        print(f"Error during modification: {e}", file=sys.stderr)
        return 1
