import os
import json
import argparse
import zipfile


path = 'data.json'
data = {}

# --------------------------------------------------generate data.json------------------------------------------------------------
def check_download(language, repo):
    path = f'data/download_repo/{language}/{repo.replace('/', ':')}.zip'
    if os.path.exists(path):
        return 1
    return 0

def show_infomation():
    all_num = 0
    for key in data:
        num = data[key]['download_length']
        print(key, num)
        all_num = all_num + num
    print(f"总共有项目{all_num}个")

def collect_and_process_files():
    folder_path = 'data/tasks'
    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        # print(f"root {root}")
        if root.endswith('tasks'):
            continue
        key = root.split('/')[-1]
        data[key] = {'length':0, 'repos':[], 'nums':[], 'download':[], 'download_length':0}
        for file_name in files:
            file_path = os.path.join(root, file_name)
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            # 如果文件大小为0，删除文件
            if file_size == 0:
                print(f"Deleting empty file: {file_path}")
                os.remove(file_path)
                continue
            # 如果文件以 .all 结尾，不记录信息
            if file_name.endswith('.all'):
                continue
            # 文件以.json结尾，记录信息
            lines = open(file_path, 'r', encoding='utf-8').readlines()
            task_length = len(lines)
            repo_name = file_name.split('-task-instances')[0].replace(':', '/')
            data[key]['length'] = data[key]['length'] + 1
            data[key]['repos'].append(repo_name)
            data[key]['nums'].append(task_length)
            d = check_download(key, repo_name)
            data[key]['download'].append(d)
            if d==1:
                data[key]['download_length'] = data[key]['download_length'] + 1
    show_infomation()
    with open(path, 'w') as file:
        json.dump(data, file)
    return

#-------------------------------------------------read data-----------------------------------------------------------

def check_language(language):
    languages = ['c', 'c_sharp', 'cpp', 'go', 'java', 'javascript', 'php', 'python', 'rust', 'ruby']
    if language in languages:
        return True
    print("错误语言类型")
    return False

def get_repos(language, split='all'):
    test_data = {
        'python':['janbjorge/pgqueuer','laike9m/Python-Type-Challenges','hynek/stamina','Bunsly/JobSpy'],
        'ruby':['joeldrapper/quickdraw','Shopify/autotuner','skryukov/skooma'],
        'c':['nushell/tree-sitter-nu','wmww/gtk4-layer-shell','ivoanjo/gvl-tracing'],
        'javascript':['RoleModel/turbo-confirm','mcollina/borp','sindresorhus/make-asynchronous'],
        'c_sharp':['amantinband/error-or'],
        'go':['wind-c/comqtt','destel/rill','failsafe-go/failsafe-go'],
        'cpp':['foxglove/ros-foxglove-bridge','lico-n/ZygiskFrida'],
        'rust':['tokio-rs/turmoil','automerge/autosurgeon','guywaldman/magic-cli','rust-cross/cargo-zigbuild'],
        'java':['projectdiscovery/nuclei-burp-plugin','Bindambc/whatsapp-business-java-api','microsoft/semantic-kernel-java'],
    }
    train_data = {
        'ruby':['jhawthorn/vernier','gbaptista/ollama-ai','oven-sh/homebrew-bun','alexandreruban/action-markdown','hopsoft/universalid','excid3/revise_auth','trilogy-libraries/activerecord-trilogy-adapter'],
        'c_sharp':['Sergio0694/PolySharp'],
        'c':['jszczerbinsky/lwp','microsoft/xdp-for-windows'],
        'python':['microsoft/picologging','noamgat/lm-format-enforcer','Textualize/trogon','pydantic/pydantic-settings','datadreamer-dev/DataDreamer','farizrahman4u/loopgpt','python-humanize/humanize','tetra-framework/tetra','getludic/ludic'],
        'java':['zema1/suo5','abhi9720/BankingPortal-API','woowacourse-teams/2023-hang-log','Futsch1/medTimer','woowacourse-teams/2022-dallog','maplibre/maplibre-react-native','valentinajemuovic/banking-kata-java','3arthqu4ke/headlessmc','marcushellberg/java-ai-playground','ollama4j/ollama4j'],
        'cpp':['kibae/onnxruntime-server','sudara/melatonin_blur'],
        'javascript':['sindresorhus/nano-spawn','LavaMoat/snow','11ty/webc','sindresorhus/super-regex'],
        'go':['Wsine/feishu2md','sozercan/kubectl-ai','charmbracelet/log'],
        'rust':['resyncgg/dacquiri','sophiajt/june','woodruffw/zizmor','hydro-project/rust-sitter','tokio-rs/toasty','vincent-herlemont/native_db','lunatic-solutions/submillisecond','lnx-search/datacake','SoftbearStudios/bitcode','zurawiki/gptcommit','matiaskorhonen/paper-age'],
    }
    if split == 'test':
        return test_data[language]
    if split == 'train':
        return train_data[language]

    if not os.path.exists(path):
        collect_and_process_files()
    tem_data = json.load(open(path, 'r'))
    languages = ['c', 'c_sharp', 'cpp', 'go', 'java', 'javascript', 'php', 'python', 'rust', 'ruby']
    if language == 'all':
        download_data = {}
        for i in languages:
            repos = []
            for j in range(len(tem_data[i]['download'])):
                if j==1:
                    repos.append(tem_data[i]['repos'][j])
            download_data[i] = repos
        return download_data
    if not check_language(language):
        return None
    repos = []
    for j in range(len(tem_data[language]['download'])):
        if tem_data[language]['download'][j] == 1:
            repos.append(tem_data[language]['repos'][j])
    return repos

def get_task_path(language, repo):
    if not check_language:
        return ""
    return f'data/tasks/{language}/{repo.replace('/', ':')}-task-instances.jsonl'

def get_download_path(language, repo):
    if not check_language:
        return ""
    return f'data/download_repo/{language}/{repo.replace('/', ':')}.zip'

def read_zip(language:str, repo:str, file_path:str):
    zip_path = get_download_path(language, repo)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        final_path = ''
        # 读取特定文件的内容
        for file_name in file_list:
            if file_name.endswith(file_path):
                final_path = file_name
                break
        if final_path == '':
            return False, ''
        with zip_ref.open(final_path) as file:
            content = file.read().decode('utf-8')  # 假设文件内容为 UTF-8 编码
            return True, content

def read_repo_lines(language:str, repo:str):
    total_lines = 0
    zip_path = get_download_path(language, repo)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        # 读取特定文件的内容
        for file_name in file_list:
            suffix = file_name.split('.')[-1]
            suffixs = ['py', 'c', 'cs', 'cpp', 'java', 'js', 'go', 'rb', 'rs', 'p']
            if suffix not in suffixs:
                continue
            with zip_ref.open(file_name) as file:
                content = file.read().decode('utf-8')  # 假设文件内容为 UTF-8 编码
                total_lines = total_lines + len(content)
    return total_lines


def read_task(language:str, repo:str):
    task_path = get_task_path(language, repo)
    lines = open(task_path, 'r', encoding='utf-8').readlines()
    return lines


#-------------------------------------------------------main-----------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', '-g', default=False, type=bool, help='生成data.json')
    # parser.add_argument('--read', '-r', default=False, type=bool, help='读取data.json')
    args = parser.parse_args()

    if args.generate:
        # 调用函数
        collect_and_process_files()
