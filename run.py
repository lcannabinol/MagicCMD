#!/usr/bin/env python3
import subprocess
subprocess.run('chcp 65001', shell=True)

import os
import sys
import re
import filecmp
import requests
import json
import webbrowser
import shutil
import subprocess as sp
import time
import platform
from agent_api import ask_permission

# App paths
APP_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(APP_DIR, 'magickcfg.json')
KEY_FILE = os.path.join(APP_DIR, 'groq_key.txt')
AGENTS_DIR = os.path.join(APP_DIR, 'agents')
LOG_FILE = os.path.join(APP_DIR, 'magick_setup.log')
os.makedirs(AGENTS_DIR, exist_ok=True)

# Default cloud models
DEFAULT_MODELS = [
    'llama-3.3-70b-versatile',
    'llama-3.3-13b',
    'mistral-7b',
    'falcon-7b',
    'gpt-4o-mini'
]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DOCS = "https://www.groq.com"

# Localization strings
LOCALES = {
    'en': {
        'welcome': 'MagickCMD - AI to Windows desktop assistant',
        'version': 'Version 2.0 (Cloud agent + local options)',
        'prompt_input': "Enter a question or command (type 'exit' to quit):",
        'you': 'You',
        'assistant': 'Assistant',
        'getting_response': 'Getting response from cloud model...',
        'program_finished': 'Program finished.',
        'program_interrupted': 'Program interrupted by user.',
        'error': 'Error:',
        'no_api_key': 'GROQ API key not found.',
        'no_api_key_instructions': 'Get an API key from: ',
        'paste_key_prompt': 'Paste your GROQ API key now (or leave empty to return):',
        'api_choice_prompt': 'Choose: [E]nter key  [C]onfigure local agents  [S]imulate  [X]Exit',
        'simulated_prefix': 'Simulated response: ',
        'yes': 'yes', 'no': 'no', 'yes_all_short': 'a',
        'permission_prompt': 'Permission required - proceed?',
        'invalid_choice': 'Invalid choice, please type y/n/a (a = yes to all).',
        'choose_language': 'Choose language: 1) Russian (RU)  2) English (EN)',
        'lang_prompt': 'Enter 1 or 2 [2]: ',
        'agent_menu_heading': 'Local agent / offline model options',
        'agent_menu_prompt': 'Select agent 1-5, 0-back, x-cancel:',
        'agent_submenu_prompt': "Options: [O]pen docs  [I]nstall steps  [A]uto-install  0-back  x-exit",
        'open_browser': 'Opening browser to docs...',
        'back': 'Back',
        'cancelled': 'Cancelled.',
        'settings_hint': "Type '/s' to open settings or '/reset' to reset settings",
        'opened': 'Opened:',
        'cannot_open': 'Cannot open:',
        'checking_software': 'Checking required software (git, python, pip)...',
        'software_ok': 'Required software present.',
        'software_missing': 'Missing software: ',
        'checking_gpu': 'Checking GPU / CUDA availability...',
        'gpu_none': 'No NVIDIA GPU detected or CUDA not available.',
        'gpu_info': 'GPU detected: '
    },
    'ru': {
        'welcome': 'MagickCMD - помощник для взаимодействия ИИ с рабочим столом Windows',
        'version': 'Версия 2.0 (Cloud agent + локальные опции)',
        'prompt_input': "Введите вопрос или команду (введите 'exit' для выхода):",
        'you': 'Вы',
        'assistant': 'Ассистент',
        'getting_response': 'Получаю ответ от облачной модели...',
        'program_finished': 'Программа завершена.',
        'program_interrupted': 'Программа прервана пользователем.',
        'error': 'Ошибка:',
        'no_api_key': 'Переменная окружения GROQ_API_KEY не найдена.',
        'no_api_key_instructions': 'Как получить ключ: ',
        'paste_key_prompt': 'Вставьте ваш GROQ API ключ сейчас (или оставьте пустым чтобы вернуться):',
        'api_choice_prompt': 'Выберите: [E] Ввести ключ  [C] Настроить локальные агенты  [S] Симулировать  [X] Выход',
        'simulated_prefix': 'Симулированный ответ: ',
        'yes': 'да', 'no': 'нет', 'yes_all_short': 'a',
        'permission_prompt': 'Требуется разрешение - продолжить?',
        'invalid_choice': 'Неверный ввод, введите y/n/a (a = все разрешения).',
        'choose_language': 'Выберите язык: 1) Русский (RU)  2) English (EN)',
        'lang_prompt': 'Введите 1 или 2 [1]: ',
        'agent_menu_heading': 'Варианты локального агента / оффлайн модели',
        'agent_menu_prompt': 'Выберите агент 1-5, 0-back, x-cancel:',
        'agent_submenu_prompt': "Действия: [O] Открыть документацию  [I] Команды установки  [A] Автоустановка  0-back  x-exit",
        'open_browser': 'Открываю браузер с документацией...',
        'back': 'Назад',
        'cancelled': 'Отменено.',
        'settings_hint': "Введите '/s' чтобы открыть настройки или '/reset' чтобы сбросить настройки",
        'opened': 'Открыто:',
        'cannot_open': 'Не удалось открыть:',
        'reset_done': 'Настройки сброшены. Переходим к повторному выбору языка.',
        'reset_prompt': 'Сбросить настройки и язык? (y/N): ',
        'checking_software': 'Проверка необходимого ПО (git, python, pip)...',
        'software_ok': 'Необходимое ПО присутствует.',
        'software_missing': 'Отсутствует ПО: ',
        'checking_gpu': 'Проверка наличия GPU / CUDA...',
        'gpu_none': 'NVIDIA GPU не обнаружен или CUDA недоступна.',
        'gpu_info': 'Обнаружен GPU: '
    }
}

# Globals
yes_to_all = False
lang = 'en'
config = {}


def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
    print(msg)


def t(key):
    return LOCALES.get(lang, LOCALES['en']).get(key, key)


def load_config():
    global config
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}
    else:
        config = {}
    # Ensure keys
    config.setdefault('api_key', os.getenv('GROQ_API_KEY', '').strip())
    config.setdefault('models', DEFAULT_MODELS.copy())
    config.setdefault('current_model_index', 0)


def save_config():
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error saving config: {e}")


def persist_key_to_file(key):
    try:
        with open(KEY_FILE, 'w', encoding='utf-8') as f:
            f.write(key)
        log('API key written to ' + KEY_FILE)
    except Exception as e:
        log(f"Error writing key file: {e}")


def set_api_key(key, persist_env=True):
    config['api_key'] = key
    persist_key_to_file(key)
    save_config()
    os.environ['GROQ_API_KEY'] = key
    if persist_env:
        try:
            sp.run('setx GROQ_API_KEY "{}"'.format(key), shell=True, check=False)
            log('API key persisted in user environment via setx')
        except Exception as e:
            log('Failed to persist API key: ' + str(e))


def test_api_call(model=None, timeout=10):
    key = config.get('api_key', '').strip()
    if not key:
        return False, 'No API key'
    if model is None:
        models = config.get('models', DEFAULT_MODELS)
        idx = config.get('current_model_index', 0)
        model = models[idx] if idx < len(models) else models[0]
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    data = {'model': model, 'messages': [{'role': 'user', 'content': 'Say "ok"'}], 'max_tokens': 5}
    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=timeout)
        r.raise_for_status()
        return True, 'OK'
    except requests.exceptions.HTTPError as he:
        status = None
        try:
            status = he.response.status_code
        except Exception:
            pass
        if status == 404:
            return False, 'Model not found (404)'
        return False, str(he)
    except Exception as e:
        return False, str(e)


def check_software():
    log(t('checking_software'))
    missing = []
    for exe in ('git', 'python', 'pip'):
        if shutil.which(exe) is None:
            missing.append(exe)
    if missing:
        log(t('software_missing') + ', '.join(missing))
        return False, missing
    log(t('software_ok'))
    return True, []


def check_cuda_and_vram():
    log(t('checking_gpu'))
    # Attempt to detect NVIDIA GPUs via nvidia-smi
    nvidia = shutil.which('nvidia-smi')
    if nvidia:
        try:
            out = sp.check_output(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], encoding='utf-8')
            # parse output lines
            gpus = [line.strip() for line in out.strip().splitlines() if line.strip()]
            info = []
            for g in gpus:
                parts = [p.strip() for p in g.split(',')]
                if len(parts) >= 2:
                    name = parts[0]
                    mem = parts[1]
                    info.append((name, mem))
            if not info:
                log(t('gpu_none'))
                return None
            # Log first GPU info
            gpu_desc = f"{info[0][0]} ({info[0][1]} MiB)"
            log(t('gpu_info') + gpu_desc)
            return info
        except Exception as e:
            log('nvidia-smi failed: ' + str(e))
            return None
    else:
        # Try CUDA Python probe if available
        try:
            import torch
            if torch.cuda.is_available():
                count = torch.cuda.device_count()
                info = []
                for i in range(count):
                    name = torch.cuda.get_device_name(i)
                    mem = int(torch.cuda.get_device_properties(i).total_memory / (1024*1024))
                    info.append((name, str(mem)))
                gpu_desc = f"{info[0][0]} ({info[0][1]} MiB)"
                log(t('gpu_info') + gpu_desc)
                return info
        except Exception:
            pass
        log(t('gpu_none'))
        return None


def clone_repo(url, dest):
    if os.path.exists(dest):
        log('Repo already exists: ' + dest)
        return True
    try:
        sp.run(['git', 'clone', url, dest], check=True)
        log('Cloned ' + url)
        return True
    except Exception as e:
        log('git clone failed: ' + str(e))
        return False


def pip_install_requirements(folder):
    req = os.path.join(folder, 'requirements.txt')
    if not os.path.exists(req):
        log('No requirements.txt found in ' + folder)
        return False
    try:
        sp.run([sys.executable, '-m', 'pip', 'install', '-r', req], check=True)
        log('Installed requirements for ' + folder)
        return True
    except Exception as e:
        log('pip install failed: ' + str(e))
        return False


def normalize_path(path):
    if not path:
        return None
    path = path.strip().strip('"').strip("'")
    path = os.path.expandvars(path)
    return os.path.abspath(path)


def find_path_by_name(name, start_dirs=None, max_depth=4):
    name = name.strip().lower()
    if not start_dirs:
        start_dirs = [os.path.expandvars(r'%USERPROFILE%')]
    for base in start_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            depth = root[len(base):].count(os.sep)
            if depth > max_depth:
                continue
            for entry in dirs + files:
                if name in entry.lower():
                    return os.path.join(root, entry)
    return None


def compare_paths(path1, path2):
    p1 = normalize_path(path1)
    p2 = normalize_path(path2)
    if not p1 or not p2:
        return False, 'Invalid path(s)'
    if not os.path.exists(p1) or not os.path.exists(p2):
        return False, f'Path missing: {p1 if not os.path.exists(p1) else p2}'
    if os.path.isdir(p1) or os.path.isdir(p2):
        same = os.path.abspath(p1) == os.path.abspath(p2)
        return True, f'Directory compare result: {same}'
    same = filecmp.cmp(p1, p2, shallow=False)
    return True, f'Files identical: {same}'


def execute_windows_path(path):
    try:
        if os.path.exists(path):
            os.startfile(path)
            message = f"{t('opened')} {path}"
            log(message)
            return True, message
        else:
            message = f"{t('cannot_open')} {path}"
            log(message)
            return False, message
    except Exception as e:
        message = f"{t('cannot_open')} {path}: {e}"
        log(message)
        return False, message


def plan_windows_command(user_input):
    text = user_input.lower()
    # Переменные среды - все варианты фраз
    if any(p in text for p in ('переменные среды', 'переменных среды', 'переменных системы',
                                'переменные системы', 'environment variables', 'env variables')):
        return {'action': 'run_exe', 'cmd': 'rundll32 sysdm.cpl,EditEnvironmentVariables', 'description': 'Open Environment Variables'}
    if 'настройки системы' in text or 'system settings' in text or 'параметры системы' in text:
        return {'action': 'run_exe', 'cmd': 'ms-settings:', 'description': 'Open Windows Settings'}
    if 'свойства системы' in text or 'system properties' in text:
        return {'action': 'run_exe', 'cmd': 'systempropertiesadvanced', 'description': 'Open System Properties'}
    if 'панель управления' in text or 'control panel' in text:
        return {'action': 'run_exe', 'cmd': 'control', 'description': 'Open Control Panel'}
    if 'диспетчер задач' in text or 'task manager' in text:
        return {'action': 'run_exe', 'cmd': 'taskmgr', 'description': 'Open Task Manager'}
    if 'редактор реестра' in text or 'registry editor' in text or 'regedit' in text:
        return {'action': 'run_exe', 'cmd': 'regedit', 'description': 'Open Registry Editor'}
    if 'создать папку' in text or 'create folder' in text or 'создать каталог' in text:
        m = re.search(r'create folder\s+(.+)|создать папку\s+(.+)|создать каталог\s+(.+)', text)
        path = normalize_path(m.group(1) or m.group(2) or m.group(3)) if m else None
        return {'action': 'create_folder', 'path': path}
    if 'создать файл' in text or 'create file' in text:
        m = re.search(r'create file\s+(.+)|создать файл\s+(.+)', text)
        path = normalize_path(m.group(1) or m.group(2)) if m else None
        return {'action': 'create_file', 'path': path}
    if 'сравнить' in text or 'compare' in text:
        parts = re.split(r'\s+и\s+|\s+and\s+', text)
        if len(parts) >= 2:
            return {'action': 'compare', 'path1': normalize_path(parts[-2]), 'path2': normalize_path(parts[-1])}
    if 'найти' in text or 'find' in text:
        m = re.search(r'find\s+(.+)|найти\s+(.+)', text)
        if m:
            name = m.group(1) or m.group(2)
            return {'action': 'find', 'target': name.strip()}
    if 'автозапуск' in text or 'startup' in text:
        return {'action': 'open', 'path': os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup')}
    if 'документ' in text or 'documents' in text:
        return {'action': 'open', 'path': os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'Documents')}
    if 'загруз' in text or 'downloads' in text:
        return {'action': 'open', 'path': os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'Downloads')}
    if 'проводник' in text or 'explorer' in text or 'file explorer' in text or 'файловый проводник' in text:
        return {'action': 'open', 'path': os.path.expandvars(r'%USERPROFILE%')}
    if 'удалить' in text or 'delete' in text:
        m = re.search(r'delete\s+(.+)|удалить\s+(.+)', text)
        path = normalize_path(m.group(1) or m.group(2)) if m else None
        return {'action': 'delete', 'path': path}
    return None


def simulate_windows_plan(plan):
    if not plan:
        return False, 'No valid Windows plan detected.'
    action = plan.get('action')
    if action == 'run_exe':
        cmd = plan.get('cmd', '')
        desc = plan.get('description', cmd)
        return True, f'Will execute: {desc} ({cmd})'
    if action == 'open':
        path = plan.get('path')
        if not path:
            return False, 'Target path missing.'
        if not os.path.exists(path):
            return False, f'Path does not exist: {path}'
        return True, f'Will open {path}'
    if action == 'create_folder':
        path = plan.get('path')
        if not path:
            return False, 'Folder path missing.'
        return True, f'Will create folder {path}'
    if action == 'create_file':
        path = plan.get('path')
        if not path:
            return False, 'File path missing.'
        return True, f'Will create file {path}'
    if action == 'compare':
        p1 = plan.get('path1')
        p2 = plan.get('path2')
        if not p1 or not p2:
            return False, 'Compare paths missing.'
        if not os.path.exists(p1) or not os.path.exists(p2):
            return False, 'One or both compare paths missing.'
        return True, f'Will compare {p1} and {p2}'
    if action == 'find':
        target = plan.get('target')
        if not target:
            return False, 'Find target missing.'
        return True, f'Will search for {target}'
    if action == 'delete':
        path = plan.get('path')
        if not path:
            return False, 'Delete target missing.'
        if not os.path.exists(path):
            return False, f'Path not found: {path}'
        return True, f'Will delete {path}'
    return False, 'Unknown plan action.'


def execute_windows_plan(plan):
    action = plan.get('action')
    if action == 'run_exe':
        from agent_api import run_cmd
        cmd = plan.get('cmd', '')
        desc = plan.get('description', cmd)
        log(f'Запускаю: {desc}')
        result = run_cmd(cmd)
        if result['returncode'] == 0:
            return True, f'Выполнено: {desc}'
        else:
            # Для GUI-утилит returncode != 0 норма, главное - нет stderr
            if not result['stderr']:
                return True, f'Выполнено: {desc}'
            return False, f'Ошибка: {result["stderr"]}'
    if action == 'open':
        return execute_windows_path(plan.get('path'))
    if action == 'create_folder':
        path = plan.get('path')
        os.makedirs(path, exist_ok=True)
        return True, f"{t('opened')} {path}"
    if action == 'create_file':
        path = plan.get('path')
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        open(path, 'a', encoding='utf-8').close()
        return True, f"{t('opened')} {path}"
    if action == 'compare':
        ok, msg = compare_paths(plan.get('path1'), plan.get('path2'))
        return ok, msg
    if action == 'find':
        found = find_path_by_name(plan.get('target'))
        if found:
            return execute_windows_path(found)
        return False, f"Not found: {plan.get('target')}"
    if action == 'delete':
        path = plan.get('path')
        if ask_permission(t('permission_prompt')):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True, f'Deleted {path}'
            except Exception as e:
                return False, str(e)
        return False, 'Permission denied.'
    return False, 'Unknown plan action.'


def attempt_auto_install(agent_id):
    ok, missing = check_software()
    if not ok:
        log('Auto-install aborted. Missing: ' + ','.join(missing))
        return False
    if agent_id == 2:
        dest = os.path.join(AGENTS_DIR, 'llama.cpp')
        url = 'https://github.com/ggerganov/llama.cpp.git'
        log('Cloning llama.cpp to ' + dest)
        if not clone_repo(url, dest):
            return False
        log('Auto-install notes: llama.cpp may require building in WSL on Windows. Open docs.')
        webbrowser.open('https://github.com/ggerganov/llama.cpp')
        return True
    if agent_id == 3:
        dest = os.path.join(AGENTS_DIR, 'text-generation-webui')
        url = 'https://github.com/oobabooga/text-generation-webui.git'
        log('Cloning text-generation-webui to ' + dest)
        if not clone_repo(url, dest):
            return False
        log('Installing Python requirements (may take a while).')
        if not pip_install_requirements(dest):
            log('Requirements install failed; open docs.')
            webbrowser.open('https://github.com/oobabooga/text-generation-webui')
            return False
        log('Web UI cloned and requirements installed. Opening docs for model download.')
        webbrowser.open('https://github.com/oobabooga/text-generation-webui')
        return True
    webbrowser.open('https://huggingface.co')
    return True


def choose_language(interactive_default=None):
    global lang
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ('ru', 'en'):
            lang = arg
            config['language'] = lang
            save_config()
            return
    if config.get('language', '').lower() in ('ru', 'en'):
        lang = config['language'].lower()
        return
    try:
        print(LOCALES.get(lang, LOCALES['en'])['choose_language'])
        choice = input(LOCALES.get(lang, LOCALES['en'])['lang_prompt']).strip()
    except Exception:
        choice = ''
    if choice == '' and interactive_default:
        lang = interactive_default
    elif choice == '1':
        lang = 'ru'
    else:
        lang = 'en'
    config['language'] = lang
    save_config()


def show_agent_options():
    print('\n' + t('agent_menu_heading') + '\n')
    options = [
        (1, 'Cloud API agent (minimal) - tiny local footprint, use cloud models.'),
        (2, 'llama.cpp / ggml (7B quantized) - CPU friendly; Windows 7+.'),
        (3, 'GPU small (Mistral-7B / Falcon-7B) - needs CUDA; faster.'),
        (4, 'Medium (~13B) - requires ~8GB VRAM; high-quality Russian support.'),
        (5, 'Large (70B+) - requires modern GPU (24GB+); maximum quality.')
    ]
    for n, d in options:
        print(f"{n}. {d}")
    print("\n0. " + t('back') + "    x. " + t('cancelled'))
    return options


def agent_submenu(selection):
    print('\n' + t('agent_submenu_prompt'))
    choice = input('> ').strip().lower()
    if choice == 'o':
        log(t('open_browser'))
        if selection == 2:
            webbrowser.open('https://github.com/ggerganov/llama.cpp')
        elif selection == 3:
            webbrowser.open('https://github.com/oobabooga/text-generation-webui')
        else:
            webbrowser.open('https://huggingface.co')
        return
    if choice == 'i':
        print('\n')
        if selection == 1:
            print('Cloud API agent (minimal) - set GROQ_API_KEY and choose cloud model.')
            print('To persist key: PowerShell: setx GROQ_API_KEY "<your_key>"')
        elif selection == 2:
            print('llama.cpp (ggml) 7B - Windows steps:')
            print('  1) Clone repo (will be attempted if you choose Auto-install)')
            print('  2) Build using make (WSL recommended)')
            print('  3) Download a quantized model from Hugging Face and place it in models\\')
        elif selection == 3:
            print('text-generation-webui:')
            print('  1) Clone repo (auto-install will attempt this)')
            print('  2) pip install -r requirements.txt')
            print('  3) Download model files to models/ and launch webui')
        elif selection == 4:
            print('Medium models: use bitsandbytes + transformers; check docs for offload options.')
        elif selection == 5:
            print('Large models: multi-GPU or hosted runtimes recommended.')
        print('\nNote: respect model licenses and download from official sources.')
        return
    if choice == 'a':
        consent = True
        if not yes_to_all:
            consent = ask_permission('Auto-install will modify files and install packages. Proceed?')
        if consent:
            ok = attempt_auto_install(selection)
            if ok:
                log('Auto-install completed (or started).')
            else:
                log('Auto-install failed or aborted; see messages above.')
        return
    if choice == '0':
        return 'back'
    if choice == 'x':
        return 'exit'
    log(t('invalid_choice'))
    return


def configure_agents():
    while True:
        show_agent_options()
        sel = input('\n' + t('agent_menu_prompt') + ' ').strip().lower()
        if sel == '0':
            return 'back'
        if sel == 'x':
            return 'exit'
        if sel in ['1','2','3','4','5']:
            res = agent_submenu(int(sel))
            if res == 'back':
                continue
            if res == 'exit':
                return 'exit'
            input('\nPress Enter to return to agent menu...')
            continue
        log(t('invalid_choice'))


def prompt_for_api_key_and_config():
    load_config()
    if config.get('api_key'):
        os.environ['GROQ_API_KEY'] = config.get('api_key')
        log('Using saved API key from config')
        return True
    log('\n' + t('no_api_key'))
    log(t('no_api_key_instructions') + GROQ_DOCS)
    while True:
        log('\n' + t('api_choice_prompt'))
        choice = input('> ').strip().lower()
        if choice in ['e', 'enter', '']:
            key = input('\n' + t('paste_key_prompt') + '\n> ').strip()
            if key:
                set_api_key(key, persist_env=True)
                persist_key_to_file(key)
                log('\nAPI key saved and persisted.')
                ok, msg = test_api_call()
                if ok:
                    log('Cloud agent OK with model: ' + config.get('models', [])[config.get('current_model_index',0)])
                else:
                    log('Test API call failed: ' + msg)
                return True
            else:
                continue
        elif choice in ['c']:
            res = configure_agents()
            if res == 'exit':
                log(t('cancelled'))
                return False
            continue
        elif choice in ['s']:
            log('\nContinuing with simulated responses.')
            return False
        elif choice in ['x']:
            log('\n' + t('cancelled'))
            sys.exit(0)
        else:
            log(t('invalid_choice'))


def print_models():
    models = config.get('models', DEFAULT_MODELS)
    cur = config.get('current_model_index', 0)
    for i, m in enumerate(models):
        marker = ' *' if i == cur else '  '
        print(f"{i+1}.{marker} {m}")


def settings_menu():
    while True:
        print('\nSettings:')
        print('1) Choose current cloud model')
        print('2) Add model to fallback list')
        print('3) Remove model')
        print('4) Test current model/key')
        print('5) Show API key and config file')
        print('6) Check required software')
        print('7) Check GPU / VRAM')
        print('8) Show running processes')
        print('9) Reset settings and reconfigure language')
        print('0) Back')
        print('x) Exit')
        choice = input('> ').strip().lower()
        if choice == '1':
            print('\nAvailable models:')
            print_models()
            sel = input('Select model number: ').strip()
            try:
                idx = int(sel)-1
                models = config.get('models', [])
                if 0 <= idx < len(models):
                    prev_idx = config.get('current_model_index', 0)
                    config['current_model_index'] = idx
                    save_config()
                    # Test the selected model
                    ok, msg = test_api_call(models[idx])
                    if ok:
                        log('Current model set to ' + models[idx])
                    else:
                        log('Test failed for selected model: ' + msg)
                        # ask user whether to keep or revert
                        ans = input('Keep this model despite failure? (y/N): ').strip().lower()
                        if ans in ['y','yes']:
                            log('Keeping model despite test failure.')
                        else:
                            config['current_model_index'] = prev_idx
                            save_config()
                            log('Reverted to previous model: ' + models[prev_idx])
                else:
                    log('Invalid selection')
            except Exception:
                log('Invalid input')
        elif choice == '2':
            newm = input('Enter model name to add: ').strip()
            if newm:
                # Validate model immediately
                ok, msg = test_api_call(newm)
                if ok:
                    config.setdefault('models',[]).append(newm)
                    save_config()
                    log('Model added: ' + newm)
                else:
                    log('Model not added, test failed: ' + msg)
                    print('Model validation failed:', msg)
        elif choice == '3':
            print_models()
            sel = input('Enter number to remove: ').strip()
            try:
                idx = int(sel)-1
                if 0 <= idx < len(config.get('models',[])):
                    removed = config['models'].pop(idx)
                    save_config()
                    log('Removed ' + removed)
                else:
                    log('Invalid')
            except Exception:
                log('Invalid')
        elif choice == '4':
            ok, msg = test_api_call()
            if ok:
                log('Test OK')
            else:
                log('Test failed: ' + msg)
        elif choice == '5':
            log('\nConfig path: ' + CONFIG_PATH)
            log('Key file: ' + KEY_FILE)
            k = config.get('api_key') or '(none)'
            log('API key (session): ' + (k[:6] + '...' if k and len(k)>6 else k))
        elif choice == '6':
            check_software()
        elif choice == '7':
            check_cuda_and_vram()
        elif choice == '8':
            # show running processes (Windows only)
            try:
                out = sp.check_output(['tasklist'], encoding='utf-8', errors='ignore')
                print('\n'.join(out.splitlines()[:20]))
            except Exception as e:
                log('Could not list processes: ' + str(e))
        elif choice == '9':
            reset_settings()
        elif choice in ['0','back']:
            return
        elif choice == 'x':
            sys.exit(0)
        else:
            log('Invalid choice')


def reset_settings():
    global config, lang
    try:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
    except Exception:
        pass
    try:
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
    except Exception:
        pass
    config = {
        'api_key': '',
        'models': DEFAULT_MODELS.copy(),
        'current_model_index': 0,
    }
    lang = 'en'
    save_config()
    print('\n' + t('reset_done'))
    choose_language(interactive_default='en')


def ask_groq(question, model=None, max_tokens=1000, system_prompt=None):
    key = config.get('api_key', '').strip()
    if not key:
        return LOCALES.get(lang, LOCALES['en'])['simulated_prefix'] + question
    if model is None:
        models = config.get('models', DEFAULT_MODELS)
        cur = config.get('current_model_index', 0)
        model = models[cur] if cur < len(models) else models[0]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    data = {"model": model, "messages": messages, "max_tokens": max_tokens}
    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        body = r.json()
        if 'choices' in body and isinstance(body['choices'], list):
            return body['choices'][0].get('message', {}).get('content', str(body))
        return json.dumps(body)
    except Exception as e:
        last_err = str(e)
        models = config.get('models', DEFAULT_MODELS)
        cur = config.get('current_model_index', 0)
        unavailable = []
        for i, m in enumerate(models):
            if i == cur:
                continue
            try:
                data['model'] = m
                r = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
                r.raise_for_status()
                b = r.json()
                if 'choices' in b and isinstance(b['choices'], list):
                    config['current_model_index'] = i
                    save_config()
                    return b['choices'][0].get('message', {}).get('content', str(b))
            except requests.exceptions.HTTPError as he:
                try:
                    status = he.response.status_code
                except Exception:
                    status = None
                if status == 404:
                    # mark model as unavailable and remove from list
                    unavailable.append((i, m))
                    last_err = f'Model {m} not found (404)'
                    continue
                last_err = str(he)
            except Exception as e2:
                last_err = str(e2)
        # remove unavailable models from config to avoid repeated 404s
        if unavailable:
            names = [m for (_, m) in unavailable]
            config['models'] = [m for m in config.get('models', []) if m not in names]
            save_config()
            log('Removed unavailable models: ' + ','.join(names))
        return f"{LOCALES.get(lang, LOCALES['en'])['error']} {last_err}"


def main():
    load_config()
    choose_language(interactive_default='en')
    # Step 1: check software
    check_software()
    # Step 1.5: GPU check
    check_cuda_and_vram()
    # Step 2: ensure API key
    prompt_for_api_key_and_config()
    # Step 3: greeting
    log('\n' + LOCALES.get(lang, LOCALES['en'])['welcome'])
    log(' ' + LOCALES.get(lang, LOCALES['en'])['version'])
    log('='*40)
    log(LOCALES.get(lang, LOCALES['en'])['prompt_input'] + '  ' + LOCALES.get(lang, LOCALES['en'])['settings_hint'])

    SYSTEM_PROMPT = (
        "Ты - агент управления Windows 10 компьютером через командную строку.\n"
        "ВАЖНО: Когда пользователь просит что-то СДЕЛАТЬ - выполняй это командой, не объясняй.\n"
        "Для выполнения команды используй тег: <CMD>команда</CMD>\n"
        "Ты работаешь ТОЛЬКО на Windows 10. Никогда не упоминай macOS и Linux.\n"
        "Примеры:\n"
        "  Пользователь: открой настройки переменных системы\n"
        "  Ты: Открываю. <CMD>rundll32 sysdm.cpl,EditEnvironmentVariables</CMD>\n"
        "  Пользователь: покажи переменную PATH\n"
        "  Ты: <CMD>echo %PATH%</CMD>\n"
        "  Пользователь: список процессов\n"
        "  Ты: <CMD>tasklist</CMD>\n"
        "Если нужна информация, а не действие - отвечай текстом. "
        "Отвечай на том же языке, на котором спрашивают."
    )

    def _execute_cmd_tags(response_text):
        """Найти и выполнить все <CMD>...</CMD> теги из ответа LLM."""
        from agent_api import run_cmd
        pattern = r'<CMD>(.*?)</CMD>'
        commands = re.findall(pattern, response_text, re.IGNORECASE | re.DOTALL)
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            log(f'[Выполняю]: {cmd}')
            result = run_cmd(cmd)
            if result['stdout']:
                log(result['stdout'])
            if result['stderr']:
                log('[stderr]: ' + result['stderr'])
        clean = re.sub(pattern, '', response_text, flags=re.IGNORECASE).strip()
        return clean

    while True:
        try:
            user_input = input(f"{LOCALES.get(lang, LOCALES['en'])['you']}: ").strip()
            if user_input.lower() in ['exit', 'quit', 'выход']:
                log('\n' + LOCALES.get(lang, LOCALES['en'])['program_finished'])
                break
            if not user_input:
                continue
            if user_input.strip().lower() in ['/s', '/settings']:
                settings_menu()
                continue
            if user_input.strip().lower() in ['/reset', '/reset settings', 'reset settings']:
                reset_settings()
                continue
            plan = plan_windows_command(user_input)
            if plan is not None:
                ok, message = simulate_windows_plan(plan)
                log('Plan: ' + message)
                if ok:
                    ok, result = execute_windows_plan(plan)
                    log(result)
                else:
                    log('Plan failed. Execution skipped.')
                continue
            log('\n' + LOCALES.get(lang, LOCALES['en'])['getting_response'])
            response = ask_groq(user_input, system_prompt=SYSTEM_PROMPT)
            clean_response = _execute_cmd_tags(response)
            if clean_response:
                log(f"{LOCALES.get(lang, LOCALES['en'])['assistant']}: {clean_response}")
            log('--- ' + LOCALES.get(lang, LOCALES['en'])['settings_hint'] + ' ---')
        except KeyboardInterrupt:
            log('\n\n' + LOCALES.get(lang, LOCALES['en'])['program_interrupted'])
            break
        except Exception as e:
            log(f"{LOCALES.get(lang, LOCALES['en'])['error']} {str(e)}")

if __name__ == '__main__':
    main()