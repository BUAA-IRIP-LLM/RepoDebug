from tree_sitter import Language, Parser
import argparse
import json
from unidiff import PatchSet
import os
import zipfile
from util import extract_line_ranges_safe, lang2suffix, get_language, get_query
from test_code import get_test_code
from transformations import CodeTransformate
from read_repo_data import get_repos, read_task, read_zip, check_language

def check_file(language:str, file_path:str):
    if not file_path.endswith(lang2suffix[language]):
        return False
    if file_path.endswith('__init__.py'):
        return False
    return True
    
def repo_process(language, repo):
    tasks = read_task(language, repo)
    repo_diffs = []
    print(f'开始处理项目： {repo}')
    errored_files = []
    for task_id in range(len(tasks)):
        print(f"开始处理任务实例：{task_id}")
        # 一个任务实例
        task = json.loads(tasks[task_id]) 
        # repo = task['repo']
        # pull_number = task['pull_number']
        # instance_id = task['instance_id']
        # issue_numbers = task['issue_numbers']
        # base_commit = task['base_commit']
        # patch = task['patch']
        # test_patch = task['test_patch']
        # problem_statement = task['problem_statement']
        # hints_text = task['hints_text']
        # created_at = task['created_at']
        # repo_diffs[task_id] = {
        #     'problem_statement': problem_statement,
        #     'test_patch': test_patch,
        #     'modified_files': [hunk.path for hunk in PatchSet(test_patch)],
        #     'error_diffs': {}
        # }
        for patch_ranges in extract_line_ranges_safe(task['patch']):

            # 任务实例下的一个文件
            file_path = patch_ranges['file_path']
            if file_path in errored_files:
                continue
            errored_files.append(file_path)
            # 
            line_ranges = patch_ranges['hunks']
            if not check_file(language, file_path):
                continue
            state, code = read_zip(language, repo, file_path)
            if not state:
                continue
            print(f"开始处理文件：{file_path}")
            LANGUAGE = get_language(language)
            parser = Parser(LANGUAGE)
            tree = parser.parse(code.encode('utf-8'))
            root = tree.root_node
            query = '(ERROR)@error'
            captures = get_query(language, query, root)
            
            if len(captures) > 0:
                continue
            # java 韩文导致字符提取错误
            if file_path == 'backend/src/main/java/hanglog/trip/dto/request/ItemRequest.java':
                continue
            if file_path == 'backend/src/main/java/hanglog/trip/dto/request/ItemUpdateRequest.java':
                continue
            codeTf = CodeTransformate(language, repo, task_id, task, file_path, code, root, line_ranges)
            repo_diffs.extend(codeTf.get_diffs())
            # repo_diffs[task_id]['error_diffs'][file_path] = get_diffs(codeTf)
            # break # TODO  1个文件
        # break # TODO 1个任务实例
    return repo_diffs

def main(language: str, save_dir:str, split:str):
    if not check_language(language):
        return 
    repos = get_repos(language, split=split)

    language_diffs = []
    for repo in repos:
        repo_diffs = repo_process(language, repo)
        language_diffs.extend(repo_diffs)
        # break #  TODO 1个repo
    save_path = f'data/{save_dir}/{language}.json'
    if not os.path.exists(f'data/{save_dir}'):
        os.makedirs(f'data/{save_dir}')
    with open(save_path, 'w') as save_file:
        json.dump(language_diffs, save_file)
    print(repos)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument('--repo', '-r', type=str, help='zip文件路径', default='')
    parser.add_argument('--language', '-l', type=str, help='language', default='python')
    parser.add_argument('--save_dir', '-s', type=str, help='save_dir', default='error')
    parser.add_argument('--split', '-sp', type=str, help='split', default='train')
    args = parser.parse_args()
    main(**vars(args))