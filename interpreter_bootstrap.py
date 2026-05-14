import sys
import os
import ctypes

# Elevate to admin if not already (will prompt UAC)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

if os.name == 'nt' and not is_admin():
    # Relaunch the script with admin privileges
    python_exe = sys.executable
    script = os.path.abspath(__file__)
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    lpParameters = f'"{script}" {params}'.strip()
    try:
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', python_exe, lpParameters, None, 1)
        sys.exit(0)
    except Exception as e:
        print('Elevation failed or cancelled:', e)
        # proceed without elevation

# If elevated, log admin acquisition
if os.name == 'nt' and is_admin():
    try:
        import getpass
        user = getpass.getuser()
        log_line = f"Administrator privileges acquired. User: {user}"
        # append to magick_setup.log
        try:
            with open(os.path.join(os.path.dirname(__file__), 'magick_setup.log'), 'a', encoding='utf-8') as lf:
                lf.write(log_line + '\n')
        except Exception:
            pass
        print(log_line)
    except Exception:
        pass

# ensure UTF-8 code page
import subprocess
subprocess.run('chcp 65001', shell=True)

import json
import requests

# load key from config
try:
    cfg_path = os.path.join(os.path.dirname(__file__), 'magickcfg.json')
    cfg = json.load(open(cfg_path, 'r', encoding='utf-8'))
    API_KEY = cfg.get('api_key', '')
except Exception:
    API_KEY = os.getenv('GROQ_API_KEY', '')

if not API_KEY:
    raise SystemExit('No API key available')


def ask_fallback(question):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": question}],
        "max_tokens": 1000
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# integrate with interpreter if available
try:
    from interpreter import interpreter
    import agent_api

    # expose agent API to interpreter for controlled command execution
    interpreter.agent = agent_api
    interpreter.agent_api = agent_api
    interpreter.exec_cmd = agent_api.run_cmd
    interpreter.exec_ps = agent_api.run_powershell

    interpreter.llm.model = 'groq/llama-3.1-8b-instant'
    interpreter.llm.api_key = API_KEY
    interpreter.llm.max_tokens = 500
    interpreter.llm.context_window = 3000

    # Strong system message enforcing direct Windows action workflow
    interpreter.system_message = """
Ты ассистент для автоматизации исключительно Windows.
Используй только представленные функции: agent.run_cmd(command) или agent.run_powershell(ps_cmd).
Не используй Linux или macOS команды, не описывай шаги словами.
Если нужно открыть автозапуск, запусти explorer "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup" или equivalent PowerShell command.
Выполняй команду сразу и возвращай результат выполнения.
Если не знаешь, попробуй ask_fallback('вопрос') и используй ответ как инструкцию.
Всегда логируй действия и результаты в magick_setup.log.
"""

    # Ensure Open-Interpreter skills directory exists and register an 'agent' skill that proxies to agent_api
    try:
        skills = interpreter.computer.skills
        os.makedirs(skills.path, exist_ok=True)
        skill_file = os.path.join(skills.path, 'agent.py')
        skill_code = (
            "import sys, os\n"
            "proj_path = r\"D:\\\\mAgIcmd\"\n"
            "if proj_path not in sys.path:\n"
            "    sys.path.insert(0, proj_path)\n"
            "try:\n"
            "    from agent_api import run_cmd\n"
            "except Exception as e:\n"
            "    def agent_run(command):\n"
            "        return {'returncode':1,'stdout':'','stderr':f'Failed to import agent_api.run_cmd: {e}'}\n"
            "else:\n"
            "    def agent_run(command):\n"
            "        return run_cmd(command)\n"
        )
        # write or overwrite the skill file
        try:
            with open(skill_file, 'w', encoding='utf-8') as sf:
                sf.write(skill_code)
        except Exception:
            pass
        # import skills so interpreter can call agent_run() as a skill
        try:
            interpreter.computer.skills.import_skills()
        except Exception:
            pass
    except Exception:
        pass

    # Start interactive interpreter chat loop (with detailed error logging)
    try:
        interpreter.chat()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # write full traceback to log
        try:
            with open(os.path.join(os.path.dirname(__file__), 'magick_setup.log'), 'a', encoding='utf-8') as lf:
                lf.write('\n' + tb + '\n')
        except Exception:
            pass
        print('Interpreter integration failed. Full traceback written to magick_setup.log')
        print(str(e))
        # if known issue detected, give a concise hint and exit gracefully
        if 'tool_use_failed' in tb:
            print('Detected tool_use_failed in interpreter traceback. Likely a tools execution error inside interpreter.')
            print('Action: ensure tools return stable dicts and not string status codes. Agent API returns dicts {returncode, stdout, stderr}.')
            print('Interpreter will exit to avoid crash. Check magick_setup.log for details.')
            sys.exit(1)
        # otherwise exit with error
        sys.exit(1)
except Exception as e:
    print('Interpreter integration failed:', e)
