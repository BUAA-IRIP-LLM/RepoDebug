import re
import random
from util import *
from query import *
import numpy as np
import tokenize
from io import BytesIO
from tree_sitter import Node
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import jaccard_score

MAX_NUM = 5


def jaccard_similarity(word1, word2):
    # 使用 CountVectorizer 对字符串进行字符级别向量化
    vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 1), binary=True)
    X = vectorizer.fit_transform([word1, word2]).toarray()
    
    # 计算 Jaccard 相似度
    similarity = jaccard_score(X[0], X[1], average='macro')  # 改为 'macro' 或 'micro'
    return similarity


class CodeTransformate:
    def __init__(self, language, repo, task_id, task, file, code, root, line_ranges):
        self.language = language
        self.repo = repo
        self.task_id = task_id
        self.task = task
        self.test_patch = task['test_patch']
        self.problem_statement = task['problem_statement']
        self.created_at = task['created_at']
        self.code = code
        self.root = root 
        self.file_path = file
        self.line_ranges = line_ranges
        self.identifiers = self.get_identifiers()
        self.classes = self.get_classes()
        self.funcs = self.get_funcs()
        self.diffs = []

    def get_funcs(self):
        query_text = query_func_def[self.language]
        captures = get_query(self.language, query_text, self.root)
        funcs = []
        for capture in captures:
            func = self.node2string(capture['name'])
            funcs.append(func)
        return funcs

    def get_classes(self):
        query_text = query_class_def[self.language]
        captures = get_query(self.language, query_text, self.root)
        classes = []
        for capture in captures:
            class_name = self.node2string(capture['name'])
            classes.append(class_name)
        return classes

    def get_identifiers(self):
        query_text = """(identifier)@identifier"""
        captures = get_query(self.language, query_text, self.root)
        identifiers = []
        for capture in captures:
            identifier = capture['identifier']
            identifiers.append(self.code[identifier.start_byte: identifier.end_byte])
        return list(set(identifiers))

    def get_closest_identifier(self, target_identifier):
        max_cosine_sim = -1
        if isinstance(target_identifier, str):
            target_identifier_str = target_identifier
        elif isinstance(target_identifier, Node):
            target_identifier_str = self.code[target_identifier.start_byte: target_identifier.end_byte]
        else:
            target_identifier_str = ''
        closest_identifier = ''
        for identifier in self.identifiers:
            if identifier == target_identifier_str:
                continue
            cosine_sim = jaccard_similarity(identifier, target_identifier_str)
            if cosine_sim > max_cosine_sim:
                max_cosine_sim = cosine_sim
                closest_identifier = identifier
        return closest_identifier

    def check_line_ranges(self, node):
        for line_range in self.line_ranges:
            if node.start_byte > line_range['start']+ line_range['length'] or node.end_byte > line_range['start']:
                return True
        return False


    def del_node(self, node):
        del_code = self.code[:node.start_byte] + self.code[node.end_byte:]
        if self.code == del_code:
            return False, ""
        return True, del_code

    def rep_node(self, node, new_code):
        rep_code = self.code[:node.start_byte] + new_code + self.code[node.end_byte:]
        if self.code == rep_code:
            return False, ""
        return True, rep_code

    def node2string(self, node):
        return self.code[node.start_byte: node.end_byte]

    def add_diffs(self, error_type, diffs, error_description=None):
        for diff in diffs:
            if error_description == None:
                self.diffs.append({'error_type': error_type, 'diff': diff, 'error_description': error2desc[error_type]})
            else:
                self.diffs.append({'error_type': error_type, 'diff': diff, 'error_description': error_description})
        return 

    def load_data(self):
        datas = []
        for diff in self.diffs:
            data = {
                'language': self.language,
                'repo': self.repo,
                'task_id': self.task_id,
                'file': self.file_path,
                'lines': len(self.code.split('\n')),
                'created_at': self.created_at,
                'problem_statement': self.problem_statement,
                'test_patch': self.test_patch,
                'code': self.code,
            }
            data |= diff
            datas.append(data)
        return datas


    def multi_errors(self, num):
        single_diffs = []
        for diff in self.diffs:
            if diff['error_type'] not in ['multi_errors2', 'multi_errors3', 'multi_errors4']:
                single_diffs.append(diff)
        diffs_num = 5*num if len(single_diffs) > 5*num else int(len(single_diffs) / 5) * 5
        old_diffs = random.choices(single_diffs, k=diffs_num)
        diffs = []
        for i in range(int(diffs_num / 5)):
            new_diff = []
            new_desc = []
            for j in range(num):
                new_diff.append(old_diffs[i*num+j]['diff'])
                if old_diffs[i*num+j]['error_description'] not in new_desc:
                    new_desc.append(old_diffs[i*num+j]['error_description'])
            diffs.append({'error_type': f'multi_errors{num}', 'diff': new_diff, 'error_description': new_desc})
        self.diffs = self.diffs + diffs
        return 

    def get_diffs(self):
        for key in error2func:
            diffs = error2func[key](self)
            self.add_diffs(key, diffs)
        self.multi_errors(2)
        self.multi_errors(3)
        self.multi_errors(4)
        return self.load_data()

def misuse_equal_sign1(codeTf):
    diffs = []
    query_text = """("==")@equal"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        equal_node = capture['equal']
        state, error_code = codeTf.rep_node(equal_node, '=')
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs 

def misuse_equal_sign2(codeTf):
    diffs = []
    query_text = """("=")@equal"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        equal_node = capture['equal']
        state, error_code = codeTf.rep_node(equal_node, '==')
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs 

def open_bracket1(codeTf):
    diffs = []
    query_text = """(")")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def open_bracket2(codeTf):
    diffs = []
    query_text = """("]")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def open_bracket3(codeTf):
    diffs = []
    query_text = """("}")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def no_colon(codeTf):
    diffs = []
    query_text = """(":")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def no_comma(codeTf):
    diffs = []
    query_text = """(",")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def no_semicolon(codeTf):
    diffs = []
    query_text = """(";")@node"""
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        state, error_code = codeTf.del_node(node)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def ref_process(codeTf, ref_node, split1, split2):
    refs = codeTf.node2string(ref_node)

    if codeTf.language in ['c', 'cpp', 'go']:
        start = refs[0]
        end = refs[-1]
        refs = codeTf.node2string(ref_node)[1:-1]
        if split1 in refs:
            path = refs.split(split1)[:-1]
            name = refs.split(split1)[-1]
            if split2 in name: # c cpp
                name = name.split(split2)[-2]
                new_code = codeTf.get_closest_identifier(name)
                new_code = split1.join(path)+split1+new_code+split2+refs.split(split1)[-1].split(split2)[-1]
            else: # go
                new_code = codeTf.get_closest_identifier(name)
                new_code = split1.join(path)+split1+new_code
        else:
            if split2 in refs: # c  cpp
                name = refs.split(split2)[-2]
                new_code = codeTf.get_closest_identifier(name)
                new_code = new_code+split2+refs.split(split2)[-1]
            else: # go
                name = refs
                new_code = codeTf.get_closest_identifier(name)

        new_code = start + new_code + end
        return codeTf.rep_node(ref_node, new_code)

    if split1 in refs:
        ref_list = refs.split(split1)
        random_ref = ref_list[-1]
        ref_list.remove(random_ref)
        if split2 in random_ref:
            path = split2.join(random_ref.split(split2)[:-1])
            name = random_ref.split(split2)[-1]
            new_code = codeTf.get_closest_identifier(name)
            new_code = path+split2+new_code
        else:
            name = random_ref
            new_code = codeTf.get_closest_identifier(name)
        new_code = split1.join(ref_list)+split1+new_code
        return codeTf.rep_node(ref_node, new_code)
    else:
        if split2 in refs:
            path = split2.join(refs.split(split2)[:-1])
            name = refs.split(split2)[-1]
            new_code = codeTf.get_closest_identifier(name)
            new_code = path+split2+new_code
        else:
            name = refs
            new_code = codeTf.get_closest_identifier(name)
        return codeTf.rep_node(ref_node, new_code)

def wrong_import_name(codeTf):
    diffs = []
    query = query_import[codeTf.language]
    if codeTf.language in ['c_sharp', 'java', 'javascript']:
        query_text = query
        captures = get_query(codeTf.language, query_text, codeTf.root)
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
        for capture in captures:
            full_node = capture['full']
            if 'ref' not in capture:
                continue
            ref_node = capture['ref']
            state, error_code = ref_process(codeTf, ref_node, ',', '.')
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    elif codeTf.language in ['go']:
        query_text = query
        captures = get_query(codeTf.language, query_text, codeTf.root)
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
        for capture in captures:
            full_node = capture['full']
            if 'ref' not in capture:
                continue
            ref_node = capture['ref']
            state, error_code = ref_process(codeTf, ref_node, '/', '.')
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    elif codeTf.language in ['ruby']:
        query_text = query
        captures = get_query(codeTf.language, query_text, codeTf.root)
        new_captures = []
        for capture in captures:
            require = codeTf.node2string(capture['require'])
            full = codeTf.node2string(capture['full'])
            if require != 'require' or 'require' not in full:
                continue
            if capture['ref'].start_byte > capture['full'].end_byte or capture['ref'].end_byte < capture['full'].start_byte:
                continue
            new_captures.append(capture)
        captures = new_captures
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
        for capture in captures:
            require = codeTf.node2string(capture['require'])
            full_node = capture['full']
            if 'ref' not in capture:
                continue
            ref_node = capture['ref']
            state, error_code = ref_process(codeTf, ref_node, '/', '.')
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    elif codeTf.language in ['php', 'python', 'rust']:
        for key in query:
            query_text = query[key]
            captures = get_query(codeTf.language, query_text, codeTf.root)
            captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
            for capture in captures:
                if 'ref' not in capture:
                    continue
                ref_node = capture['ref']
                full_node = capture['full']
                state, error_code = ref_process(codeTf, ref_node, ',', '.')
                if not state:
                    continue
                diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    elif codeTf.language in ['c', 'cpp']:
        for key in query:
            query_text = query[key]
            captures = get_query(codeTf.language, query_text, codeTf.root)
            captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
            for capture in captures:
                if 'ref' not in capture:
                    continue
                ref_node = capture['ref']
                full_node = capture['full']
                state, error_code = ref_process(codeTf, ref_node, '/', '.')
                if not state:
                    continue
                diff = get_diff(codeTf.code, error_code, codeTf.file_path)
                # print(diff)
                diffs.append(diff)
    
    return diffs

def wrong_class_call(codeTf):
    diffs = []
    query_text = query_class_call[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        class_node = capture['class']
        if not codeTf.check_line_ranges(class_node):
            captures.remove(capture)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        class_node = capture['class']
        class_name = codeTf.node2string(class_node)
        if len(codeTf.classes) > 0:
            max_sim = -1
            new_code = ''
            for class_item in codeTf.classes:
                sim = jaccard_similarity(class_item, class_name)
                if sim == 1:
                    continue
                if sim > max_sim:
                    max_sim = sim
                    new_code = class_item
        else:
            new_code = codeTf.get_closest_identifier(class_name)
        state, error_code = codeTf.rep_node(class_node, new_code)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def wrong_func_call(codeTf):
    diffs = []
    query_text = query_func_call[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        func_node = capture['func']
        if not codeTf.check_line_ranges(func_node):
            captures.remove(capture)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        func_node = capture['func']
        func_name = codeTf.node2string(func_node)
        if len(codeTf.funcs) > 0:
            max_sim = -1
            new_code = ''
            for func_item in codeTf.funcs:
                sim = jaccard_similarity(func_item, func_name)
                if sim == 1:
                    continue
                if sim > max_sim:
                    max_sim = sim
                    new_code = func_item
        else:
            new_code = codeTf.get_closest_identifier(func_name)
        state, error_code = codeTf.rep_node(func_node, new_code)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

def binary_div_0(codeTf):
    diffs = []
    if codeTf.language in ['python', 'rust', 'go', 'javascript', 'ruby']:
        query_text = query_binary_expression[codeTf.language]
        captures = get_query(codeTf.language, query_text, codeTf.root)
        new_captures = []
        for capture in captures:
            binary_node = capture['binary']
            if not codeTf.check_line_ranges(binary_node):
                continue
            expression = codeTf.node2string(binary_node)
            # # print(expression)
            if not ('+' in expression or '-' in expression or '*' in expression or '/' in expression):
                # # print('not in')
                continue
            new_captures.append(capture)
        captures = new_captures
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures

        for capture in captures:
            binary_node = capture['binary']
            expression = codeTf.node2string(binary_node)
            expression = f'({expression})/0'
            state, error_code = codeTf.rep_node(binary_node, expression)
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    return diffs

def binary_opposite(codeTf):
    diffs = []
    if codeTf.language in ['python', 'rust', 'go', 'javascript', 'ruby']:
        query_text = query_binary_expression[codeTf.language]
        captures = get_query(codeTf.language, query_text, codeTf.root)
        new_captures = []
        for capture in captures:
            binary_node = capture['binary']
            if not codeTf.check_line_ranges(binary_node):
                continue
            expression = codeTf.node2string(binary_node)
            # # print(expression)
            if not ('+' in expression or '-' in expression or '*' in expression or '/' in expression):
                # # print('not in')
                continue
            new_captures.append(capture)
        captures = new_captures
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures

        for capture in captures:
            binary_node = capture['binary']
            expression = codeTf.node2string(binary_node)
            # print(expression)
            if '+' in expression:
                expression = expression.replace('+', '-')
            elif '-' in expression:
                expression = expression.replace('-', '+ ')
            elif '*' in expression:
                expression = expression.replace('*', '/ ')
            elif '/' in expression:
                expression = expression.replace('/', '*')
            # error_code = codeTf.code[:left_node.end_byte] + op + codeTf.code[right_node.start_byte:]
            state, error_code = codeTf.rep_node(binary_node, expression)
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    else:
        # c ++ -- += -= *= /=
        query_texts = ['("++")@op', '("--")@op', '("+=")@op', '("-=")@op', '("*=")@op', '("/=")@op']
        new_captures = []
        for query_text in query_texts:
            captures = get_query(codeTf.language, query_text, codeTf.root)
            for capture in captures:
                op_node = capture['op']
                if not codeTf.check_line_ranges(op_node):
                    continue
                new_captures.append(capture)

        captures = new_captures
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
        for capture in captures:
            op_node = capture['op']
            op = codeTf.node2string(op_node)
            if op == '++':
                new_op = '--'
            elif op == '--':
                new_op = '++'
            elif op == '+=':
                new_op = '-='
            elif op == '-=':
                new_op = '+='
            elif op == '*=':
                new_op = '/='
            elif op == '/=':
                new_op = '*='
            state, error_code = codeTf.rep_node(op_node, new_op)
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    return diffs

def binary_less(codeTf):
    diffs = []
    if codeTf.language in ['python', 'rust', 'go', 'javascript', 'ruby']:
        query_text = query_binary_expression[codeTf.language]
        captures = get_query(codeTf.language, query_text, codeTf.root)
        new_captures = []
        for capture in captures:
            binary_node = capture['binary']
            if not codeTf.check_line_ranges(binary_node):
                continue
            expression = codeTf.node2string(binary_node)
            # # print(expression)
            if not ('+' in expression or '-' in expression or '*' in expression or '/' in expression):
                # # print('not in')
                continue
            new_captures.append(capture)
        captures = new_captures
        captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures

        for capture in captures:
            binary_node = capture['binary']
            expression = codeTf.node2string(binary_node)
            # print(expression)
            if '+' in expression:
                expression = random.choice(expression.split('+'))
            elif '-' in expression:
                expression = random.choice(expression.split('-'))
            elif '*' in expression:
                expression = random.choice(expression.split('*'))
            elif '/' in expression:
                expression = random.choice(expression.split('/'))
            # error_code = codeTf.code[:left_node.end_byte] + op + codeTf.code[right_node.start_byte:]
            state, error_code = codeTf.rep_node(binary_node, expression)
            if not state:
                continue
            diff = get_diff(codeTf.code, error_code, codeTf.file_path)
            # print(diff)
            diffs.append(diff)
    return diffs

def if_opposite(codeTf):
    diffs = []
    query_text = query_if_condition[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        if 'condition' not in captures:
            captures.remove(capture)
            continue
        condition_node = capture['condition']
        condition = codeTf.node2string(condition_node)
        if not codeTf.check_line_ranges(condition_node):
            captures.remove(capture)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        # print(capture)
        if 'condition' not in capture:
            captures.remove(capture)
            continue
        condition_node = capture['condition']
        condition = codeTf.node2string(condition_node)
        new_condition = condition
        if '>=' in new_condition:
            new_condition = new_condition.replace('>=', '<=')
        elif '>' in new_condition:
            new_condition = new_condition.replace(' >', ' <')
        elif '<=' in new_condition:
            new_condition = new_condition.replace('<=', '>=')
        elif '<' in new_condition:
            new_condition = new_condition.replace(' <', ' >')
        
        if '===' in new_condition:
            new_condition = new_condition.replace('===', '!==')
        elif '!==' in new_condition:
            new_condition = new_condition.replace('!==', '===')
        elif '==' in new_condition:
            new_condition = new_condition.replace('==', '!=')
        elif '!=' in new_condition:
            new_condition = new_condition.replace('!=', '==')

        if '||' in new_condition:
            new_condition = new_condition.replace('||', '&&')
        elif '&&' in new_condition:
            new_condition = new_condition.replace('&&', '||')
        if new_condition == condition:
            continue

        state, error_code = codeTf.rep_node(condition_node, new_condition)
        if not state:
            continue
        diff = get_diff(codeTf.code, error_code, codeTf.file_path)
        # print(diff)
        # input()
        diffs.append(diff)
    return diffs

def if_const(codeTf):
    diffs = []
    query_text = query_if_condition[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        if 'condition' not in captures:
            captures.remove(capture)
            continue
        condition_node = capture['condition']
        condition = codeTf.node2string(condition_node)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        if 'condition' not in capture:
            # print('condition not in capture')
            captures.remove(capture)
            continue
        condition_node = capture['condition']
        condition = codeTf.node2string(condition_node)
        if not codeTf.check_line_ranges(condition_node):
            # print('not check_line_ranges')
            continue
        random_number = random.random()
        if random_number < 0.5:
            new_condition = '1'
        else:
            new_condition = '0'
        state, error_code = codeTf.rep_node(condition_node, new_condition)
        if not state:
            continue
        diff=get_diff(codeTf.code, error_code, codeTf.file_path)
        diffs.append(diff)
    return diffs

def wrong_params(codeTf):
    diffs = []
    query_text = query_parameters[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        if not 'paras' in capture:
            captures.remove(capture)
            continue
        paras_node = capture['paras']
        if not codeTf.check_line_ranges(paras_node):
            captures.remove(capture)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        if not 'paras' in capture:
            continue
        paras_node = capture['paras']
        query_identifier = "(identifier)@identifier"
        identifiers_captures = get_query(codeTf.language, query_identifier, paras_node)
        if len(identifiers_captures) > 0:
            random_identifier_capture = random.choice(identifiers_captures)
            identifier_node = random_identifier_capture['identifier']
            new_code = codeTf.get_closest_identifier(identifier_node)
            state, error_code = codeTf.rep_node(identifier_node, new_code)
            if not state:
                continue
            diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
        else:
            query_string_text = query_string[codeTf.language]
            string_captures = get_query(codeTf.language, query_string_text, paras_node)
            if len(string_captures) > 0:
                random_string_capture = random.choice(string_captures)
                string_node = random_string_capture['node']
                length = string_node.end_byte - string_node.start_byte -2
                characters = string.ascii_letters + string.digits  # 包含大小写字母和数字
                new_code = "\"" + ''.join(random.choices(characters, k=length)) + "\""
                state, error_code = codeTf.rep_node(string_node, new_code)
                if not state:
                    continue
                diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
            else:
                paras = codeTf.node2string(paras_node)
                new_code = re.sub(r'\d', str(random.randint(0, 9)) , paras, count=1)
                state, error_code = codeTf.rep_node(paras_node, new_code)
                if not state:
                    continue
                diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs 

def wrong_return(codeTf):
    diffs = []
    query_text = query_return[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    for capture in captures:
        value = capture['value']
        return_node = capture['return']
        if not codeTf.check_line_ranges(return_node):
            captures.remove(capture)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        value = capture['value']
        return_node = capture['return']
        nodes = get_query(codeTf.language, "(identifier)@identifier", value)
        identifiers = [node['identifier'] for node in nodes]
        if len(identifiers) > 0:
            for identifier in identifiers:
                identifier_str = codeTf.code[identifier.start_byte: identifier.end_byte]
                if identifier_str == 'self':
                    identifiers.remove(identifier)
            if len(identifiers) > 0:
                random_identifier = random.choice(identifiers)
                new_code = codeTf.get_closest_identifier(random_identifier)
                state, error_code = codeTf.rep_node(random_identifier, new_code)
                if not state:
                    continue
                diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))

    return diffs

def invalid_annotation_symbols(codeTf):
    diffs = []
    query_text = query_comment[codeTf.language]
    captures = get_query(codeTf.language, query_text, codeTf.root)
    captures = random.sample(captures, MAX_NUM) if len(captures) > 5 else captures
    for capture in captures:
        node = capture['node']
        comment = codeTf.code[node.start_byte: node.end_byte]
        new_code = comment
        if comment[:2] == '//' or comment[:2] == '/*':
            new_code = new_code[2:].replace('/', '')
        if comment[-2:] == '*/':
            new_code = new_code[:-2]
        if comment[0] == '#':
            new_code = new_code.replace('#', '')
        if new_code == '':
            continue
        state, error_code = codeTf.rep_node(node, new_code)
        if not state:
            continue
        diffs.append(get_diff(codeTf.code, error_code, codeTf.file_path))
    return diffs

error2func = {
    'misuse_equal_sign1': misuse_equal_sign1,
    'misuse_equal_sign2': misuse_equal_sign2,
    'open_bracket1': open_bracket1,
    'open_bracket2': open_bracket2,
    'open_bracket3': open_bracket3,
    'no_colon': no_colon,
    'no_comma': no_comma,
    'no_semicolon': no_semicolon,

    'wrong_return': wrong_return,
    'invalid_annotation_symbols': invalid_annotation_symbols,
    'wrong_import_name': wrong_import_name,
    'wrong_class_call': wrong_class_call,
    'wrong_func_call': wrong_func_call,

    'binary_div_0':binary_div_0,
    'binary_opposite': binary_opposite,
    'binary_less': binary_less,
    'if_opposite': if_opposite,
    'if_const': if_const,

    'wrong_params': wrong_params,
}

error2desc = {
    'misuse_equal_sign1':'Detects incorrect use of a single equal sign for comparison instead of double equal signs.',
    'misuse_equal_sign2':'Identifies cases where double equal signs are mistakenly used for assignment.',
    'open_bracket1':'Verifies that all opening brackets have corresponding closing brackets.',
    'open_bracket2':'Verifies that all opening brackets have corresponding closing brackets.',
    'open_bracket3':'Verifies that all opening brackets have corresponding closing brackets.',
    'no_colon':'Finds instances where colons are missing in statements.',
    'no_comma':'Detects missing commas in lists, function arguments, and other comma-separated contexts.',
    'no_semicolon':'Identifies missing semicolons at the end of statements in languages that require them.',
    'wrong_return':'Checks for incorrect return statements, such as returning the wrong type or value.',
    'invalid_annotation_symbols':'Detects invalid or misused annotation symbols in code comments or type hints.',
    'wrong_import_name':'Identifies incorrect module or function names in import statements.',
    'wrong_class_call':'Verifies that class instances are created with the correct constructor and arguments.',
    'wrong_func_call':'Checks for incorrect function calls, including wrong arguments or missing parameters.',
    'binary_div_0':'Detects division by zero in binary operations, which can cause runtime errors.',
    'binary_opposite':'Identifies incorrect use of binary opposite operators, like using `+` instead of `-`.',
    'binary_less':'Checks for incorrect use of binary less-than operators, ensuring logical correctness.',
    'if_opposite':'Detects logical errors in `if` conditions, such as using `==` instead of `!=`.',
    'if_const':'Identifies `if` statements with constant conditions, which are always true or false.', 
    'wrong_params':'Checks for incorrect function parameters, including wrong types or missing arguments.',
}