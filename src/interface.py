import json
import subprocess
import argparse
import ollama
from util import apply_diff
import logging
import requests
import time
import os
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11435/v1/',

    # required but ignored
    api_key='ollama',
)

# python src/interface.py -i data/re-test/c.json -o data/re-test/out-c.json

def get_prompt(data):
    if isinstance(data['diff'], list):
        error_code = data['code']
        for diff in data['diff']:
            error_code = apply_diff(error_code, diff) 
    else:
        error_code = apply_diff(data['code'], data['diff'])
    error_description = data['error_description']
    test_patch = data['test_patch']
    problem_statement = data['problem_statement']
    prompt4 = f"""
Oberve the following code and errors:
<code>
{error_code}
</code>

<error type>
Type 1 : Using = instead of  == in comparisons.
Type 2 : Using == instead of = in assignments.
Type 3 : Missing closing parenthesis in code.
Type 4 : Missing closing bracket in lists.
Type 5 : Missing closing brace in dictionaries or blocks.
Type 6 : Missing colon : at the end of a statement.
Type 7 : Missing comma , between elements.
Type 8 : Missing semicolon ; at the end of a line.
Type 9 : Using invalid symbols or no symbols in type annotations.
Type 10 : Incorrect return statement.
Type 11 : Incorrect module/class/function name in import.
Type 12 : Incorrect class name when calling a class.
Type 13 : Incorrect function name when calling a function.
Type 14 : Incorrect or missing function parameters.
Type 15 : Division by zero in binary operations.
Type 16 : Using wrong binary operator.
Type 17 : Missing operand in binary operation.
Type 18 : Using opposite condition in if statement.
Type 19 : Using constant value in if condition.
Type 20 : Two separate bugs in the same code segment.
Type 21 : Three separate bugs in the same code segment.
Type 22 : Four separate bugs in the same code segment.
</error type>

You need to write the following content:
1. Is there an error or errors in the code ?
2. If there is an error or errors, write the index of the error type.
3. If there is an error or errors, write which line the error or errors are.
4. If there is an error or errors, write the right code of the error line.

If there is an error or errors in the code, your output should follow the format, and multiple <fix> lines are allowed.:
<error>yes</error>
<type>index of error type</type>
<line>Line number or numbers of the error code, split with ','</line>
<fix><line>a line number</line><code>the correct code for this line</code></fix>

If there is no error in the code, Your output should follow the format:
<error>no</error>

Notice that do not write anything else.
"""
    return prompt4



def run(model, input_file, output_file):
    retries=3
    # 读取测试文件
    with open(input_file, 'r') as file:
        test_data = json.load(file)
    responses = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            responses=json.load(file)
        print(len(responses), '-------------------------------------')
        print(len(test_data), '-------------------------------------')
    if len(responses) == len(test_data):
        print(f'{model}   {input_file} is already down.')
        return 
    for data in test_data[len(responses):]:
        attempt = 0
        try:
            # response = ollama.chat(
            #     model = model,
            #     messages = [{'role': 'user', 'content': get_prompt(data)}],
            #     options={"num_ctx": 16384},   # 限制生成的最大长度
            # )
            # content = json.loads(response.model_dump_json())['message']['content']
            content = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": get_prompt(data)},
                        ],
                    }
                ],
                timeout=15,  # Add timeout here
            )
            content = content.choices[0].message.content
            # print(content)

            responses.append(content)
            if len(responses) % 100 ==0:
                with open(output_file, 'w') as file:
                    json.dump(responses, file)
            continue
        except requests.exceptions.Timeout as e:
            attempt += 1  # Increment the attempt counter
            logging.error(f"Attempt {attempt} timed out: {e}")  # Log the timeout error message
            if attempt >= retries:  # If the max retries have been reached
                logging.error(f"Max retries reached. Skipping.")  # Log that we are skipping this task
                # return None  # Return None if max retries are reached
            time.sleep(5)  # Wait for 5 seconds before retrying the request
        except requests.exceptions.RequestException as e:
            attempt += 1  # Increment the attempt counter
            logging.error(f"Attempt {attempt} failed: {e}")  # Log the error message
            if attempt >= retries:  # If the max retries have been reached
                logging.error(f"Max retries reached. Skipping.")  # Log that we are skipping this task
                # return None  # Return None if max retries are reached
            time.sleep(5)  # Wait for 5 seconds before retrying the request
        except Exception as e:
            # Catch any other exception
            attempt += 1
            logging.error(f"Error occurred: {e}")
            # If the error is related to sensitive content (based on error message)
            if attempt >= retries:
                logging.error(f"Unexpected error: {e}. Skipping.")
                # return None  # Return None for other unexpected errors
            time.sleep(5)  # Wait before retrying
        responses.append("")
    # 写入输出文件
    with open(output_file, 'w') as file:
        json.dump(responses, file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', '-m', type=str, help='输入模型', default='qwen2.5-coder:latest')
    parser.add_argument('--input', '-i', type=str, help='输入文件名')
    parser.add_argument('--output', '-o', type=str, help='输出文件名')
    args = parser.parse_args()
    # Remove existing StreamHandler(s)
    for handler in logging.getLogger().handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            logging.getLogger().removeHandler(handler)
        
    # 设置日志
    language = args.input.split('/')[-1].split('.')[0]
    logging.basicConfig(filename=f'data/log-{language}.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    # Add StreamHandler to also print to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    print(args.model)
    print(args.input, args.output)
    run(args.model, args.input, args.output)
    


