import argparse
import json
import re
from unidiff import PatchSet
import pandas as pd
# 定义正则表达式
error_pattern = r"<error>(.*?)</error>"
line_pattern = r"<line>([\d,]+)</line>"  # 匹配数字和逗号的组合
fix_pattern = r"<fix><line>(\d+)</line><code>(.*?)</code></fix>"

import Levenshtein

def string_similarity(str1, str2):
    distance = Levenshtein.distance(str1, str2)
    similarity = 1 - (distance / max(len(str1), len(str2)))
    return similarity

def right_error_line(patch_str, lines):
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
        # file_changes = []
        for hunk in patched_file:
            hunk_info = {
                "start": hunk.target_start,
                "end": hunk.target_length + hunk.target_start
            }
            line_ranges.append(hunk_info)
    one_right_line = []
    for line_range in line_ranges:
        new_right_line = 0
        for line in lines:
            line = int(line)
            if line <= line_range['end'] and line >= line_range['start']:
                new_right_line = 1
                continue
        one_right_line.append(new_right_line)
    if 0 in one_right_line:
        all_right_line = 0
    else :
        all_right_line = 1
    one_right_line = 1 if 1 in one_right_line else 0
    return one_right_line, all_right_line


def is_error_line(patch_str, line):
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
        # file_changes = []
        for hunk in patched_file:
            hunk_info = {
                "start": hunk.target_start,
                "end": hunk.target_length + hunk.target_start
            }
            # file_changes.append(hunk_info)
            line_ranges.append(hunk_info)
    one_right_line = []

    for line_range in line_ranges:
        line = int(line)
        if line <= line_range['end'] and line >= line_range['start']:
            return 1
    return 0


def eval(test_file, res_file):
    test = json.load(open(test_file, 'r'))
    res = json.load(open(res_file, 'r'))
    eval_ans = []

    if len(test) != len(res):
        print("error: length is not equal")
    else:
        print("right: length is equal")
    for i in range(len(test)):
        test_item = test[i]
        eval_item = {'error_type': test_item['error_type'], 'language': test_item['language']}
        text = res[i]
        # 使用re.search()方法匹配错误信息和第一个行号
        error_match = re.search(error_pattern, text)
        line_match = re.search(line_pattern, text)

        if error_match:
            error_content = error_match.group(1)
            if error_content == 'yes':
                eval_item['has_error'] = 1
            else:
                eval_item['has_error'] = 0
                continue
            if line_match:
                # 获取匹配到的错误信息和第一个行号
                
                lines = line_match.group(1).split(',')  # 将行号字符串分割成列表
                one_right_line, all_right_line = right_error_line(test_item['diff'], lines)
                eval_item['one_right_line'] = one_right_line
                eval_item['all_right_line'] = all_right_line
                # 使用re.findall()方法匹配所有<fix>部分
                fix_matches = re.findall(fix_pattern, text)
                eval_item['em'] = []
                eval_item['es'] = []
                for (line, code) in fix_matches:
                    line = int(line)
                    right_line = is_error_line(test_item['diff'], line)
                    if right_line:
                        right_codes = test_item['code'].splitlines(keepends=True)
                        if line > len(right_codes):
                            em = -1
                            es = -1
                        else:
                            right_code = right_codes[line-1]
                            repair_code = code
                            em = 1 if right_code == repair_code else 0
                            es = string_similarity(right_code, repair_code)
                    else:
                        em = -1
                        es = -1
                    eval_item['em'].append(em)
                    eval_item['es'].append(es)
            else:
                eval_item['one_right_line'] = -1
                eval_item['all_right_line'] = -1
        else:
            eval_item['has_error'] = -1
        # print(eval_item)
        eval_ans.append(eval_item)
    return eval_ans



# "has_error": 1,
#             "one_right_line": 0,
#             "all_right_line": 0,
#             "em": [
#                 -1,
#                 -1,
#                 -1
#             ],
#             "es": [
#                 -1,
#                 -1,
#                 -1
#             ]

def read_file(save_file):
    datas = json.load(open(save_file, 'r'))
    result = {}
    NUM_TABLE = {}
    ERROES_TABLE = {}
    ONE_LINE_TABLE = {}
    ALL_LINE_TABLE = {}
    EM_TABLE = {}
    ES_TABLE = {}
    WRONG_GEN_TABLE = {}
    for data in datas:
        language = data['language']
        error_type = data['error_type']
        if language not in result:
            result[language] = {}
            NUM_TABLE[language] = {}
            ERROES_TABLE[language] = {}
            ONE_LINE_TABLE[language] = {}
            ALL_LINE_TABLE[language] = {}
            EM_TABLE[language] = {}
            ES_TABLE[language] = {}
            WRONG_GEN_TABLE[language] = {}

        if error_type not in result[language]:
            result[language][error_type] = {'num':0, 'errors':0, 'one_line':0, 'all_line':0, 'em':0, 'es':0, 'wrong_gen':0}
            NUM_TABLE[language][error_type] = 0
            ERROES_TABLE[language][error_type] = 0
            ONE_LINE_TABLE[language][error_type] = 0
            ALL_LINE_TABLE[language][error_type] = 0
            EM_TABLE[language][error_type] = 0
            ES_TABLE[language][error_type] = 0
            WRONG_GEN_TABLE[language][error_type] = 0

        result[language][error_type]['num'] += 1
        NUM_TABLE[language][error_type] +=1
        if data['has_error'] == -1:
            result[language][error_type]['wrong_gen'] += 1
            WRONG_GEN_TABLE[language][error_type] += 1
            continue
        elif data['has_error'] == 0:
            continue
        result[language][error_type]['errors'] += 1
        ERROES_TABLE[language][error_type] += 1
        if data['one_right_line'] != 1:
            continue
        result[language][error_type]['one_line'] += 1
        ONE_LINE_TABLE[language][error_type] += 1
        if data['all_right_line'] == 1:
            result[language][error_type]['all_line'] += 1
            ALL_LINE_TABLE[language][error_type] += 1
        
        if 1 in data['em']:
            result[language][error_type]['em'] += 1
            EM_TABLE[language][error_type] += 1
        for es in data['es']:
            result[language][error_type]['es'] += es
            ES_TABLE[language][error_type] += 1

    TABLES = [ERROES_TABLE, ONE_LINE_TABLE, ALL_LINE_TABLE, EM_TABLE, ES_TABLE, WRONG_GEN_TABLE]
    for table in TABLES:
        for i in table:
            for j in table[i]:
                table[i][j] = table[i][j] / NUM_TABLE[i][j]

    print(result)
    # 将二层字典转换为DataFrame
    df = pd.DataFrame(result)

    # 导出为CSV文件
    path = save_file.split('.')[0]
    df.to_csv(f'{path}.csv', index=True)

    TABLES = [NUM_TABLE, ERROES_TABLE, ONE_LINE_TABLE, ALL_LINE_TABLE, EM_TABLE, ES_TABLE, WRONG_GEN_TABLE]
    names = ['NUM_TABLE', 'ERROES_TABLE', 'ONE_LINE_TABLE', 'ALL_LINE_TABLE', 'EM_TABLE', 'ES_TABLE', 'WRONG_GEN_TABLE']
    path = save_file.split('.')[0]+'.xlsx'
    with pd.ExcelWriter(path) as writer:
        for i in range(len(TABLES)):
            table = TABLES[i]
            name = names[i]
            df = pd.DataFrame(table)
            df.to_excel(writer, sheet_name=name, index=False)  
            # df.to_csv(f'{path}.csv', index=True)

def read_file_language(save_file):
    datas = json.load(open(save_file, 'r'))
    result = {}
    NUM_TABLE = {}
    ERROES_TABLE = {}
    ONE_LINE_TABLE = {}
    ALL_LINE_TABLE = {}
    EM_TABLE = {}
    ES_TABLE = {}
    WRONG_GEN_TABLE = {}
    for data in datas:
        language = data['language']
        if language not in result:
            NUM_TABLE[language] = 0
            ERROES_TABLE[language] = 0
            ONE_LINE_TABLE[language] = 0
            ALL_LINE_TABLE[language] = 0
            EM_TABLE[language] = 0
            ES_TABLE[language] = 0
            WRONG_GEN_TABLE[language] = 0
        NUM_TABLE[language] += 1
        if data['has_error'] == -1:
            # result[language][error_type]['wrong_gen'] += 1
            WRONG_GEN_TABLE[language] += 1
            continue
        elif data['has_error'] == 0:
            continue
        # result[language][error_type]['errors'] += 1
        ERROES_TABLE[language] += 1
        if data['one_right_line'] != 1:
            continue
        # result[language][error_type]['one_line'] += 1
        ONE_LINE_TABLE[language] += 1
        if data['all_right_line'] == 1:
            # result[language][error_type]['all_line'] += 1
            ALL_LINE_TABLE[language] += 1
        
        if 1 in data['em']:
            # result[language][error_type]['em'] += 1
            EM_TABLE[language] += 1
        for es in data['es']:
            # result[language][error_type]['es'] += es
            ES_TABLE[language] += 1

    TABLES = [ERROES_TABLE, ONE_LINE_TABLE, ALL_LINE_TABLE, EM_TABLE, ES_TABLE, WRONG_GEN_TABLE]
    for table in TABLES:
        for i in table:
            table[i] = table[i] / NUM_TABLE[i]
    TABLES = [NUM_TABLE, ERROES_TABLE, ONE_LINE_TABLE, ALL_LINE_TABLE, EM_TABLE, ES_TABLE, WRONG_GEN_TABLE]
    names = ['NUM_TABLE', 'ERROES_TABLE', 'ONE_LINE_TABLE', 'ALL_LINE_TABLE', 'EM_TABLE', 'ES_TABLE', 'WRONG_GEN_TABLE']
    path = save_file.split('.')[0]+f'-language.xlsx'
    with pd.ExcelWriter(path) as writer:
        for i in range(len(TABLES)):
            table = TABLES[i]
            name = names[i]
            df = pd.DataFrame(table)
            df.to_excel(writer, sheet_name=name, index=False)  


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', type=str)
    args = parser.parse_args()
    languages = ['c', 'cpp', 'c_sharp', 'java', 'javascript', 'python', 'go', 'ruby', 'rust']
    eval_ans = []
    save_file = f'data/re-test/{args.model}-out-eval.json'
    # for language in languages:
    #     test_file = f'data/re-test/{language}.json'
    #     res_file = f'data/re-test/{args.model}-out-{language}.json'
    #     ans = eval(test_file, res_file)
    #     eval_ans.extend(ans)
    # with open(save_file, 'w') as f:
    #     json.dump(eval_ans, f)
    # read_file(save_file)
    read_file_language(save_file)


