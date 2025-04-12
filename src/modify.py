# -*- coding: utf-8 -*-

"""
Implementation of the modify mode for the AI CLI tool.
"""

import os
import sys
import tempfile
import subprocess
import difflib
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
    
    # 处理可能的AI响应格式，例如"--- file (原始版本)"和"+++ file (AI建议)"格式
    if "原始版本" in diff_text and "AI建议" in diff_text:
        lines = diff_text.splitlines()
        original_section = []
        modified_section = []
        in_original = False
        in_modified = False
        
        for line in lines:
            if "原始版本" in line:
                in_original = True
                in_modified = False
                continue
            elif "AI建议" in line:
                in_original = False
                in_modified = True
                continue
            
            if in_original:
                if line.startswith('-'):
                    original_section.append(line[1:] if len(line) > 1 else "")
                elif line.startswith('@') or not line.strip():
                    continue
                else:
                    original_section.append(line)
            elif in_modified:
                if line.startswith('+'):
                    modified_section.append(line[1:] if len(line) > 1 else "")
                elif line.startswith('@') or not line.strip():
                    continue
                else:
                    modified_section.append(line)
        
        # 如果有提取出内容，则构建一个块
        if original_section or modified_section:
            # 比较原始和修改内容的每一行，识别相同的部分
            original_text = "\n".join(original_section)
            modified_text = "\n".join(modified_section)
            chunks.append((1, original_text, modified_text))
            return chunks
    
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
            
        # Handle diff content lines
        elif in_diff_section or line.startswith("+") or line.startswith("-") or line.startswith(" "):
            diff_lines.append(line)
    
    # If no diff section markers found but there are +/- lines, include all lines as a basic diff
    if not in_diff_section and any(line.startswith("+") or line.startswith("-") for line in lines):
        diff_lines = lines
    
    # If we have anything in diff_lines, assume it could be a diff
    if diff_lines:
        # Process the cleaned diff lines
        original_chunk = []
        modified_chunk = []
        line_num = 1  # 默认行号
        
        # 处理文件头部分
        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            
            # 跳过空行
            if not line.strip():
                i += 1
                continue
                
            # 处理hunk头部
            if line.startswith("@@"):
                try:
                    # 解析@@ -X,Y +X,Y @@格式中的行号
                    hunk_info = line.split("@@")[1].strip()
                    original_range = hunk_info.split(" ")[0]
                    line_num = int(original_range.split(",")[0][1:])  # 去掉'-'前缀
                except (IndexError, ValueError):
                    pass
                i += 1
            # 跳过文件头部
            elif line.startswith("---") or line.startswith("+++"):
                i += 1
            # 处理内容行
            else:
                break
        
        # 处理diff内容
        while i < len(diff_lines):
            line = diff_lines[i]
            
            # 跳过空行
            if not line.strip():
                i += 1
                continue
                
            # 新的hunk头部表示新的区块
            if line.startswith("@@"):
                if original_chunk or modified_chunk:
                    chunks.append((line_num, "\n".join(original_chunk), "\n".join(modified_chunk)))
                    original_chunk = []
                    modified_chunk = []
                
                try:
                    # 解析行号
                    hunk_info = line.split("@@")[1].strip()
                    original_range = hunk_info.split(" ")[0]
                    line_num = int(original_range.split(",")[0][1:])  # 去掉'-'前缀
                except (IndexError, ValueError):
                    pass
                i += 1
            # 处理移除的行
            elif line.startswith("-"):
                original_chunk.append(line[1:])
                i += 1
            # 处理添加的行
            elif line.startswith("+"):
                modified_chunk.append(line[1:])
                i += 1
            # 处理上下文行（未更改）
            else:
                # 如果有空格前缀则去掉
                content_line = line[1:] if line.startswith(" ") else line
                original_chunk.append(content_line)
                modified_chunk.append(content_line)
                i += 1
        
        # 添加最后一个区块
        if original_chunk or modified_chunk:
            chunks.append((line_num, "\n".join(original_chunk), "\n".join(modified_chunk)))
    
    # 如果没有识别到区块且文本不为空，尝试将整个内容作为单个更改
    if not chunks and diff_text.strip():
        # 使用整个diff_text作为建议的替换内容
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
        # 将原始内容和修改内容分割成行
        original_lines = original.splitlines() if original else []
        modified_lines = modified.splitlines() if modified else []
        
        # 如果是空diff（没有任何变化），跳过
        if not original_lines and not modified_lines:
            continue
            
        # 显示区块信息
        print(colorize(f"@@ -{line_num},{len(original_lines)} +{line_num},{len(modified_lines)} @@", "cyan"))
        
        # 分析原始行和修改行的相似性
        if len(original_lines) == len(modified_lines):
            # 检查哪些行是相同的
            same_lines = []
            diff_lines_orig = []
            diff_lines_mod = []
            
            for j, (orig, mod) in enumerate(zip(original_lines, modified_lines)):
                if orig == mod:
                    same_lines.append((j, orig))
                else:
                    diff_lines_orig.append((j, orig))
                    diff_lines_mod.append((j, mod))
            
            # 如果有完全相同的行，将它们组合在一起显示
            if same_lines and (diff_lines_orig or diff_lines_mod):
                current_section = "same"
                last_j = -1
                
                # 对行进行排序，并按相同/不同分组显示
                all_lines = [(j, "same", line) for j, line in same_lines] + \
                           [(j, "orig", line) for j, line in diff_lines_orig] + \
                           [(j, "mod", line) for j, line in diff_lines_mod]
                all_lines.sort(key=lambda x: x[0])
                
                for j, line_type, line in all_lines:
                    # 跳过已处理的修改行
                    if line_type == "mod" and any(x[0] == j for x in diff_lines_orig):
                        continue
                        
                    # 分组显示相同的行
                    if line_type != current_section:
                        if line_type == "same":
                            print(colorize("  (以下为无变化的代码)", "cyan"))
                        elif current_section == "same":
                            print(colorize("  (以下为有变化的代码)", "cyan"))
                        current_section = line_type
                    
                    # 显示行内容
                    if line_type == "same":
                        print(colorize(f"  {line}", "white"))
                    elif line_type == "orig":
                        print(colorize(f"-{line}", "red"))
                        # 如果有对应的修改行，紧接着显示
                        mod_lines = [l for idx, l in diff_lines_mod if idx == j]
                        if mod_lines:
                            print(colorize(f"+{mod_lines[0]}", "green"))
                    
                    last_j = j
            # 如果所有行都相同
            elif len(same_lines) == len(original_lines):
                print(colorize("  (代码无变化)", "cyan"))
                for _, line in same_lines:
                    print(colorize(f"  {line}", "white"))
            # 如果所有行都不同
            else:
                for line in original_lines:
                    print(colorize(f"-{line}", "red"))
                for line in modified_lines:
                    print(colorize(f"+{line}", "green"))
        else:
            # 行数不同，显示完整的差异
            for line in original_lines:
                print(colorize(f"-{line}", "red"))
            for line in modified_lines:
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
    except subprocess.SubprocessError as e:
        print(f"编辑器错误: {e}")
        return chunk_content
    except Exception as e:
        print(f"编辑过程中发生错误: {e}")
        return chunk_content
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def process_modify_request(client: DeepSeekClient, file_path: str, content: str, 
                          prompt: str, input_text: Optional[str] = None) -> int:
    """
    处理修改请求。
    
    Args:
        client: DeepSeekClient实例
        file_path: 要修改的文件路径
        content: 文件内容
        prompt: 修改提示
        input_text: 可选的附加上下文
        
    Returns:
        退出代码（0表示成功，非零表示失败）
    """
    try:
        # 让AI生成修改后的完整文件内容，而不是差异
        modified_text = client.generate_modified_text(content, prompt, input_text)
        
        if not modified_text or not modified_text.strip():
            print("AI未返回任何修改建议，退出修改模式。")
            return 0
            
        # 使用Python标准库difflib计算差异
        original_lines = content.splitlines()
        modified_lines = modified_text.splitlines()
        
        # 使用difflib生成统一差异格式
        diff = list(difflib.unified_diff(
            original_lines, 
            modified_lines,
            fromfile=f"{file_path} (原始版本)",
            tofile=f"{file_path} (AI建议)",
            lineterm=''
        ))
        
        # 如果没有差异，通知用户并退出
        if len(diff) <= 2:  # 只有文件头信息，没有实际差异
            print("AI未对文件内容做出任何修改。")
            return 0
            
        # 显示差异
        for line in diff:
            if line.startswith('---'):
                print(colorize(line, "red"))
            elif line.startswith('+++'):
                print(colorize(line, "green"))
            elif line.startswith('-'):
                print(colorize(line, "red"))
            elif line.startswith('+'):
                print(colorize(line, "green"))
            elif line.startswith('@@'):
                print(colorize(line, "cyan"))
            else:
                print(line)
        
        # 交互模式处理修改
        if sys.stdout.isatty():
            while True:
                try:
                    print(colorize("\n交互选项:", "cyan"))
                    print("[1] 接受修改   [2] 拒绝   [3] 编辑   [4] 查看完整修改后内容")
                    choice = input(colorize("[?] 请选择操作 (默认1): ", "yellow") or "1")
                    
                    if choice == "1":
                        # 应用修改
                        write_file_content(file_path, modified_text)
                        print(f"\n修改已应用到 {file_path}")
                        break
                    elif choice == "2":
                        # 拒绝修改
                        print("\n修改已拒绝")
                        return 0
                    elif choice == "3":
                        # 编辑修改
                        edited_text = edit_content(modified_text)
                        if edited_text != modified_text:
                            # 如果编辑后的内容与AI生成的不同，重新计算差异
                            new_diff = list(difflib.unified_diff(
                                original_lines, 
                                edited_text.splitlines(),
                                fromfile=f"{file_path} (原始版本)",
                                tofile=f"{file_path} (编辑后版本)",
                                lineterm=''
                            ))
                            
                            print("\n编辑后的差异:")
                            for line in new_diff:
                                if line.startswith('---'):
                                    print(colorize(line, "red"))
                                elif line.startswith('+++'):
                                    print(colorize(line, "green"))
                                elif line.startswith('-'):
                                    print(colorize(line, "red"))
                                elif line.startswith('+'):
                                    print(colorize(line, "green"))
                                elif line.startswith('@@'):
                                    print(colorize(line, "cyan"))
                                else:
                                    print(line)
                        
                        apply_choice = input(colorize("\n应用这些编辑后的修改? [Y/n]: ", "yellow") or "y").lower()
                        if apply_choice != "n":
                            write_file_content(file_path, edited_text)
                            print(f"\n编辑后的修改已应用到 {file_path}")
                        break
                    elif choice == "4":
                        # 显示完整的修改后内容
                        print(colorize("\n修改后的完整内容:", "cyan"))
                        for i, line in enumerate(modified_lines, 1):
                            print(f"{i:4d} | {line}")
                        continue
                    else:
                        print("\n无效选择，请重试")
                except EOFError:
                    print("\n检测到EOF错误，交互被中断")
                    return 1
                except KeyboardInterrupt:
                    print("\n操作被用户取消")
                    return 130
        else:
            # 非交互模式 - 只显示差异
            return 0
            
        return 0
    except Exception as e:
        print(f"修改过程中出错: {e}", file=sys.stderr)
        return 1


def edit_content(content: str) -> str:
    """
    打开编辑器让用户编辑内容。
    
    Args:
        content: 要编辑的内容
        
    Returns:
        编辑后的内容
    """
    editor = os.environ.get("EDITOR", "vim")
    
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as temp:
        temp_path = temp.name
        temp.write(content)
    
    try:
        subprocess.run([editor, temp_path], check=True)
        with open(temp_path, "r") as f:
            edited_content = f.read()
        return edited_content
    except subprocess.SubprocessError as e:
        print(f"编辑器错误: {e}")
        return content
    except Exception as e:
        print(f"编辑过程中发生错误: {e}")
        return content
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
