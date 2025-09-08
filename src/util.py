import tree_sitter_python as tspython
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_c_sharp as tscsharp
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_ruby as tsruby
import tree_sitter_rust as tsrust
import tree_sitter_bash as tsbash
import tree_sitter_php as tsphp
import tree_sitter_html as tshtml
import tree_sitter_css as tscss
import tree_sitter_kotlin as tskotlin
from tree_sitter import Language, Parser, Node
import argparse
import json
from unidiff import PatchSet
from difflib import unified_diff
import os
import zipfile
import random
import string
lang2tslang = {
        'python': tspython,
        'c': tsc,
        'cpp': tscpp,
        'c_sharp': tscsharp,
        'java': tsjava,
        'go': tsgo,
        'javascript': tsjs,
        'ruby': tsruby,
        'rust': tsrust,
        'bash': tsbash,
        'php': tsphp,
        'html': tshtml,
        'css': tscss,
        'kotlin': tskotlin
    }
lang2suffix = {
    'python': 'py',
    'c': 'c', 
    'c_sharp': 'cs',
    'cpp': 'cpp', 
    'java':'java', 
    'javascript':'js',
    'go': 'go',
    'ruby': 'rb',
    'rust': 'rs',
    'php': 'p',
}
def get_language(lang:str):
    return Language(lang2tslang[lang].language())

def get_root(lang:str, code:str):
    LANGUAGE = get_language(lang)
    parser = Parser(LANGUAGE)
    tree = parser.parse(code.encode('utf-8'))
    root = tree.root_node
    return tree, root

def get_query(lang:str, query_text:str, root:Node):
    LANGUAGE = get_language(lang)
    query = LANGUAGE.query(query_text)
    data = query.captures(root)
    captures = [{key: value for key, value in zip(data.keys(), values)} for values in zip(*data.values())]
    return captures


def get_diff(ori_code, fix_code, path):
# 生成 diff 格式
    diff = unified_diff(
        ori_code.splitlines(keepends=True),  # 保留换行符
        fix_code.splitlines(keepends=True),
        fromfile=path,
        tofile=path
    )

    # 将 diff 保存为字符串
    diff_text = ''.join(diff)
    return diff_text

# 如果需要用 diff 修改 code1 得到 code2，可以使用以下代码
'''
def apply_diff(base, diff_text):
    """
    使用 diff 修改 base 字符串
    """
    patch = PatchSet(diff_text.splitlines(keepends=True))
    result_lines = base.splitlines(keepends=True)
    for hunk in patch[0]:  # 假设只有一个文件
        start_index = hunk.source_start - 1  # 转换为 Python 索引
        for i, line in enumerate(hunk):
            if line.is_added:
                result_lines.insert(start_index + i, line.value)
            elif line.is_removed:
                del result_lines[start_index + i]
    return ''.join(result_lines)
'''

def apply_diff(base, diff_text):
    """
    使用 diff 修改 base 字符串，保留缩进和顺序。
    """
    base_lines = base.splitlines(keepends=True)  # 保留换行符
    diff_lines = diff_text.splitlines(keepends=True)

    # 解析 diff
    result = []
    base_index = 0
    # print(diff_text)
    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++"):
            continue  # 忽略文件头
        elif line.startswith("@@"):
            # 解析块头信息
            parts = line.split()
            base_start = int(parts[1].split(",")[0].replace("-", "")) - 1
            while base_index < base_start:
                result.append(base_lines[base_index])
                base_index += 1
        elif line.startswith("-"):
            base_index += 1  # 跳过删除的行
        elif line.startswith("+"):
            result.append(line[1:])  # 添加新增行（去掉 "+" 标记）
        else:
            result.append(base_lines[base_index])  # 保留原始行
            base_index += 1
        # print(result)
        # input()

    # 添加剩余的行
    result.extend(base_lines[base_index:])

    return ''.join(result)


from unidiff import PatchSet

def extract_line_ranges_safe(patch_str):
    """
    从 PatchSet 类型字符串中提取修改的行数范围，捕获异常以便调试。
    """
    try:
        patch_set = PatchSet(patch_str)
    except UnidiffParseError as e:
        print(f"UnidiffParseError: {e}")
        return []

    line_ranges = []
    for patched_file in patch_set:
        file_changes = {"file_path": patched_file.path, "hunks": []}
        for hunk in patched_file:
            hunk_info = {
                "start": hunk.target_start,
                "length": hunk.target_length
            }
            file_changes["hunks"].append(hunk_info)
        line_ranges.append(file_changes)
    return line_ranges


# 定义生成随机字符串的函数
def generate_random_string(length):
    # 生成由小写字母、大写字母、数字组成的随机字符串
    characters = string.ascii_letters + string.digits  # 包含大小写字母和数字
    return ''.join(random.choice(characters) for _ in range(length))

def print_tree(node, indent=0):
    """递归打印语法树"""
    print("  " * indent + f"{node.type} [{node.start_point}-{node.end_point}]")
    for child in node.children:
        print_tree(child, indent + 1)

