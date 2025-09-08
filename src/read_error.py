import os
import re
import json
import argparse
from read_repo_data import read_zip
from util import apply_diff
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
error_types = [
    'misuse_equal_sign1',
    'misuse_equal_sign2',
    'open_bracket1',
    'open_bracket2',
    'open_bracket3',
    'no_colon',
    'no_comma',
    'no_semicolon',
    'wrong_return',
    'invalid_annotation_symbols',
    'wrong_import_name',
    'wrong_class_call',
    'wrong_func_call',
    'binary_div_0',
    'binary_opposite',
    'binary_less',
    'if_opposite',
    'if_const',
    'wrong_index',
]

# 统计每个项目每个文件中各类错误的数量
def statistics_error():
    root = 'data/error'
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    with pd.ExcelWriter('data/error_nums.xlsx') as writer:
        for language in languages:
            path = f'{root}/{language}.json'
            data = json.load(open(path, 'r'))
            language_data = []
            for repo_info in data:
                for key in repo_info:
                    if key == 'repo':
                        repo_name = repo_info['repo']
                        continue
                    task_id = key
                    problem_statement = repo_info[task_id]['problem_statement']
                    test_patch = repo_info[task_id]['test_patch']
                    modified_files = repo_info[task_id]['modified_files']
                    repo_diffs = repo_info[task_id]['error_diffs']
                    for file_path in repo_diffs:
                        file_info = [repo_name, task_id, file_path]
                        file_diffs = repo_diffs[file_path]
                        file_diffs_num = {}
                        for file_diff in file_diffs:
                            file_diffs_num[file_diff['error_type']]=len(file_diff['diffs'])
                        for error_type in error_types:
                            file_info.append(file_diffs_num[error_type])
                        language_data.append(file_info)
            df = pd.DataFrame(language_data, columns=['name','task id','file']+error_types)
            # df.to_excel(f'data/error_nums/{language}.xlsx', sheet_name='Sheet1', index=False)
            df.to_excel(writer, sheet_name=language, index=False)

# 统计并筛选每个项目中每个文件的大小、行数
def statistics_file():
    root = 'data/error'
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    with pd.ExcelWriter('data/file_size.xlsx') as writer:
        for language in languages:
            path = f'{root}/{language}.json'
            data = json.load(open(path, 'r'))
            language_data = []
            for repo_info in data:
                for key in repo_info:
                    if key == 'repo':
                        repo_name = repo_info['repo']
                        continue
                    task_id = key
                    problem_statement = repo_info[task_id]['problem_statement']
                    test_patch = repo_info[task_id]['test_patch']
                    modified_files = repo_info[task_id]['modified_files']
                    repo_diffs = repo_info[task_id]['error_diffs']
                    for file_path in repo_diffs:
                        # 分析文件的大小和行数
                        state, code = read_zip(language, repo_name, file_path)
                        if not state:
                            continue
                        lines = code.count('\n')+1
                        file_info = [repo_name, task_id, file_path, lines]  # file基本信息
                        language_data.append(file_info)
            df = pd.DataFrame(language_data, columns=['name','task id','file', 'lines'])
            # df = df[df['lines'] <= 1000]
            df = df[df['lines'] >= 50]
            df_unique = df.drop_duplicates(subset=['file', 'name'])
            # df.to_excel(f'data/error_nums/{language}.xlsx', sheet_name='Sheet1', index=False)
            df_unique.to_excel(writer, sheet_name=language, index=False)

# 根据statistics_file生成的文件行数统计绘制分布图
def generate_file_line_distribute():
    root = 'data/error'
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    for language in languages:
        reader = pd.read_excel('data/file_size.xlsx', sheet_name=language)
        lines = reader['lines']
        lines.plot(kind='density')  # 使用 DataFrame 的 plot 方法
        # plt.title('Density Plot of lines')
        # plt.xlabel('lines')
        # plt.savefig(f'img/density_plot_of_lines_{language}.png')  # 指定保存的文件名和路径
        # plt.close()

        # sns.violinplot(x='lines', data=reader)
        # plt.title('Violin Plot of column_name')
        # plt.savefig(f'img/vio/density_plot_of_lines_{language}.png')  # 指定保存的文件名和路径
        # plt.close()

        reader['lines'].hist(bins=30)  # bins 参数控制直方图中条形的数量
        plt.title('Distribution of lines')
        plt.xlabel('lines')
        plt.ylabel('Frequency')
        plt.savefig(f'img/hist/density_plot_of_lines_{language}.png') 
        plt.close()

# 根据statistics_file筛选的文件统计符合要求的文件及对应的错误数量
def generate_file_filter_errors():
    root = 'data/error'
    repo_filter_info = []
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    with pd.ExcelWriter('data/file_error.xlsx') as writer:
        for language in languages:
            file_reader = pd.read_excel('data/file_size.xlsx', sheet_name=language)
            error_reader = pd.read_excel('data/error_nums.xlsx', sheet_name=language)
            result = pd.merge(file_reader, error_reader, on=['name', 'task id', 'file'], how='inner')
            result.to_excel(writer, sheet_name=language, index=False)                    

# 根据statistics_file筛选的文件统计符合要求的项目及对应的错误数量
def generate_repo_filter_errors():
    root = 'data/error'
    repo_filter_info = []
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    with pd.ExcelWriter('data/50-1000/repo_error_all.xlsx') as writer:
        for language in languages:
            file_reader = pd.read_excel('data/50-1000/file_size.xlsx', sheet_name=language)
            error_reader = pd.read_excel('data/error_nums.xlsx', sheet_name=language)
            result = pd.merge(file_reader, error_reader, on=['name', 'task id', 'file'], how='inner')    
            result = result.drop('task id', axis=1)  
            result = result.drop('file', axis=1)  
           
            result = result.groupby('name').sum()
            result.reset_index(inplace=True)
            name = result['name']
            lines = result['lines']
            result = result.drop('name', axis=1)
            result = result.drop('lines', axis=1) 
            all = result.sum(axis=1)
            df = pd.DataFrame()
            df['name']=name 
            df['lines']=lines 
            df['all']=all
            df.to_excel(writer, sheet_name=language, index=False)   

# 根据statistics_file筛选的文件统计language-error
def generate_language_error():
    root = 'data/error'
    repo_filter_info = []
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    # 初始化空的DataFrame用于存储最终结果
    df_final = pd.DataFrame()
    for language in languages:
        try:
            # 尝试读取文件大小和错误数的Excel文件
            file_reader = pd.read_excel('data/50-1000/file_size.xlsx', sheet_name=language)
            error_reader = pd.read_excel('data/error_nums.xlsx', sheet_name=language)
            # 合并两个DataFrame
            result = pd.merge(file_reader, error_reader, on=['name', 'task id', 'file'], how='inner')
            # 删除不需要的列
            result = result.drop(['task id', 'file', 'name', 'lines'], axis=1, errors='ignore')  # 使用errors='ignore'避免因列不存在而出错
            # 只对数值列求和
            result = result.select_dtypes(include=[np.number]).sum()
            result['all'] = result.sum()
            result['language'] = language
            # 将结果添加到最终的DataFrame
            df_final = pd.concat([df_final, result.to_frame().T], ignore_index=True)
        except Exception as e:
            print(f"Error processing {language}: {e}")
    # 保存最终的DataFrame到Excel文件
    with pd.ExcelWriter('data/50-1000/language-error.xlsx') as writer:
        df_final.to_excel(writer, index=False)

def extract_line_numbers(diff_str):
    # 用正则表达式匹配 diff 中的 @@ 行
    match = re.search(r'@@ -\d+,\d+ \+(\d+),(\d+) @@', diff_str)
    if match:
        new_start = int(match.group(1))  # 新版本起始行号
        new_length = int(match.group(2))  # 新版本变更长度
        new_end = new_start + new_length - 1  # 新版本结束行号
        
        return new_start, new_end
    else:
        return None, None

def random_error():
    root = 'data/error'
    repo_filter_info = []
    for r,d,f in os.walk(root):
        languages = [file.split('.')[0] for file in f]
    language_table = []
    for language in languages:
        file_reader = pd.read_excel('data/50-1000/file_error.xlsx', sheet_name=language)
        row = file_reader.sample(n=1)
        name=str(row['name'].to_list()[0])
        task_id=str(row['task id'].to_list()[0])
        file=str(row['file'].to_list()[0])

        path = f'{root}/{language}.json'
        data = json.load(open(path, 'r'))
        for repo_info in data:
            if repo_info['repo'] != name:
                continue
            language_example={'language':language}
            repo_diffs = repo_info[task_id]['error_diffs']
            for file_path in repo_diffs:
                if file_path!=file:
                    continue
                file_diffs = repo_diffs[file_path]
                file_diffs_num = {}
                for file_diff in file_diffs:
                    if len(file_diff['diffs']) == 0:
                        continue
                    language_example[file_diff['error_type']] = random.choice(file_diff['diffs']) 
            # print(language_example)
            language_table.append(language_example)
    language_df = pd.DataFrame(language_table)
    language_df.to_excel('data/50-1000/language_examples.xlsx', index=False)
                


"""
parser = argparse.ArgumentParser()
parser.add_argument('--language', '-l', type=str)
args = parser.parse_args()
path = f'data/error/{args.language}.json'

data = json.load(open(path, 'r'))
with open(f'data/error_log/{args.language}.txt', 'w') as f:
    for repo_info in data:
        for key in repo_info:
            if key == 'repo':
                repo_name = repo_info['repo']
                continue
            task_id = key
            problem_statement = repo_info[task_id]['problem_statement']
            test_patch = repo_info[task_id]['test_patch']
            modified_files = repo_info[task_id]['modified_files']
            error_diffs = repo_info[task_id]['error_diffs']
            for file_path in error_diffs:
                for error in error_diffs[file_path]:
                    # if error['error_type'] != 'invalid_annotation_symbols':
                    #     continue
                    print(repo_name, end=',', file=f)
                    print(task_id, end=',', file=f)
                    print(file_path, end=',', file=f)
                    print(error['error_type'], end=',', file=f)
                    print(error['nums'], end='\n', file=f)
                    # for item in error['diffs']:
                    #     state, code = read_zip(args.language, repo_name, file_path)
                    #     if not state:
                    #         continue
                    #     error_code = apply_diff(code, item)
                    #     start, end = extract_line_numbers(item)
                    #     lines = code.splitlines()
                    #     # 提取第 i 行到第 j 行（注意：Python 索引从 0 开始）
                    #     # 所以从第 i 行到第 j 行是 lines[i-1:j]
                    #     selected_lines = lines[start-1:end]  # 索引范围 [i-1, j)
                    #     print(error['error_type'])
                    #     for i in selected_lines:
                    #         print(i)
                    #     print('------------'*0)
                    #     lines = error_code.splitlines()
                    #     # 提取第 i 行到第 j 行（注意：Python 索引从 0 开始）
                    #     # 所以从第 i 行到第 j 行是 lines[i-1:j]
                    #     selected_lines = lines[start-1:end]  # 索引范围 [i-1, j)
                    #     for i in selected_lines:
                    #         print(i)
                    #     input()
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', '-t', type=str)
    args = parser.parse_args()
    if args.type == 'file':
        statistics_file()
    elif args.type == 'error':
        statistics_error()
    elif args.type == 'gfld':
        generate_file_line_distribute()
    elif args.type == 'grfe':
        generate_repo_filter_errors()
    elif args.type == 'gffe':
        generate_file_filter_errors()
    elif args.type == 'gle':
        generate_language_error()
    elif args.type == 're':
        random_error()