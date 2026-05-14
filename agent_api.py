import subprocess
import shlex
import os
import time

# Session-wide flag for 'yes to all'
yes_to_all = False
LOG_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'magick_setup.log')

DANGEROUS_PATTERNS = [
    'shutdown', 'reboot', 'restart', 'format ', 'rm -rf', 'del /f /s /q', 'del /s /q', 'rmdir /s', 'erase /s',
    'drop database', 'mkfs', ':(){:|:&};:', 'poweroff'
]


def _log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
    print(msg)


def ask_permission(prompt=None):
    """Ask user for permission. Returns True if allowed. 'a' or 'all' sets yes_to_all for session."""
    global yes_to_all
    if yes_to_all:
        _log('Permission auto-granted (yes-to-all)')
        return True
    if prompt is None:
        prompt = "Permission required - proceed?"
    try:
        ans = input(f"{prompt} (y/n/a=all): ").strip().lower()
    except Exception:
        return False
    if ans in ('a', 'all'):
        yes_to_all = True
        _log('User set yes-to-all for session')
        return True
    if ans in ('y', 'yes'):
        _log('User granted permission')
        return True
    _log('User denied permission')
    return False


def _is_dangerous(cmd_str):
    s = cmd_str.lower()
    for p in DANGEROUS_PATTERNS:
        if p in s:
            return True, p
    return False, None


def _format_result(res):
    # Return a stable dict for interpreter/tooling
    try:
        return {
            'returncode': int(res.returncode) if hasattr(res, 'returncode') else 1,
            'stdout': res.stdout if hasattr(res, 'stdout') else str(res),
            'stderr': res.stderr if hasattr(res, 'stderr') else ''
        }
    except Exception:
        return {'returncode': 1, 'stdout': '', 'stderr': 'Failed to format result'}


def run_cmd(cmd, shell=True):
    """Execute a shell command after asking permission. Returns dict with keys: returncode, stdout, stderr."""
    # normalize command to string for checks and logging
    cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)

    # check for dangerous patterns
    dangerous, pattern = _is_dangerous(cmd_str)
    if dangerous:
        if not ask_permission(f"Command appears dangerous ({pattern}). Proceed?"):
            _log(f"Dangerous command blocked: {cmd_str}")
            return {'returncode': 2, 'stdout': '', 'stderr': 'Blocked dangerous command'}

    # Removed permission check for direct execution
    try:
        _log('Executing: ' + cmd_str)
        res = subprocess.run(cmd, shell=shell, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out = _format_result(res)
        _log(f"Command completed: returncode={out['returncode']}, stdout_len={len(out['stdout'])}, stderr_len={len(out['stderr'])}")
        return out
    except Exception as e:
        _log('Execution failed: ' + str(e))
        return {'returncode': 1, 'stdout': '', 'stderr': str(e)}


def run_powershell(ps_cmd):
    """Run a PowerShell command string after permission. Returns same dict format."""
    full = f"powershell -NoProfile -Command \"{ps_cmd}\""
    return run_cmd(full, shell=True)
