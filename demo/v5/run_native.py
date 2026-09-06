"""One real native-skill Hermes run in a fresh profile; never expose credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--hermes-source', type=Path, required=True)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    root = args.run_root.resolve()
    source = args.hermes_source.resolve(strict=True)
    skill = source / 'skills/creative/architecture-diagram'
    python = source / 'venv/Scripts/python.exe'
    query = (HERE / 'native-task.md').read_text(encoding='utf-8').replace(
        '<HERMES_SOURCE>', source.as_posix()).replace('<PLUGIN_ROOT>', HERE.parents[1].as_posix())
    sys.path.insert(0, str(source))
    if args.child:
        payload = json.loads(sys.stdin.readline())
        from cli import main as hermes_main
        hermes_main(query=query,
                    model=payload['model'], provider=payload['provider'],
                    api_key=payload['api_key'], base_url=payload['base_url'],
                    toolsets='file,skills', max_turns=35, quiet=False)
        return
    if root.exists():
        raise SystemExit('Run directory already exists; preserve it and select a fresh directory.')
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain']).strip():
        raise SystemExit('Hermes source changed; review it before reusing this comparison prompt.')
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD']).decode().strip()
    if revision != '126ff7071b6b755055879648f4e859b3187d0fac':
        raise SystemExit('Hermes revision differs from the comparison prompt.')
    profile, work = root / 'hermes-home', root / 'work'
    allowed = ('PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT',
               'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY')
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.update(HERMES_HOME=str(profile), USERPROFILE=str(root / 'os-user'),
               APPDATA=str(root / 'os-user/AppData/Roaming'),
               LOCALAPPDATA=str(root / 'os-user/AppData/Local'),
               PYTHONPATH=str(source), PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               HERMES_SESSION_SOURCE='tool', TEMP=str(root / 'temp'), TMP=str(root / 'temp'))
    for folder in (profile, work, root / 'temp', Path(env['APPDATA']), Path(env['LOCALAPPDATA'])):
        folder.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill, profile / 'skills/architecture-diagram')
    (profile / 'config.yaml').write_text(
        'terminal:\n  backend: local\n  cwd: .\n  home_mode: profile\n'
        'memory:\n  memory_enabled: false\n  user_profile_enabled: false\n', encoding='utf-8')
    # Normal existing login helper. Credentials pass through an anonymous stdin
    # pipe, not command arguments, environment variables, run metadata or files.
    from hermes_cli.auth import resolve_codex_runtime_credentials
    credentials = resolve_codex_runtime_credentials(refresh_if_expiring=False)
    payload = {'model': 'gpt-5.6-sol', 'provider': 'openai-codex',
               **{key: credentials[key] for key in ('api_key', 'base_url')}}
    if payload['base_url'].rstrip('/') != 'https://chatgpt.com/backend-api/codex':
        raise SystemExit('Unexpected inference endpoint; no credentials were sent.')
    started = time.time()
    with (root / 'run.private.log').open('wb') as log:
        proc = subprocess.Popen([str(python), '-u', str(Path(__file__).resolve()),
                                 '--child', '--run-root', str(root),
                                 '--hermes-source', str(source)], cwd=work, env=env,
                                stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
        proc.stdin.write((json.dumps(payload) + '\n').encode('utf-8'))
        proc.stdin.close()
        payload.clear()
        credentials.clear()
        print(json.dumps({'pid': proc.pid, 'run_root': str(root), 'source_revision': revision}), flush=True)
        proc.wait()
    result = {'exit_code': proc.returncode, 'elapsed_seconds': round(time.time()-started, 2),
              'source_revision': revision, 'model': 'gpt-5.6-sol', 'provider': 'openai-codex',
              'toolsets': ['file', 'skills'], 'plugins_installed': False,
              'skill_sha256': digest(skill / 'SKILL.md'),
              'template_sha256': digest(skill / 'templates/template.html'),
              'prompt_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest(),
              'prompt_template_sha256': digest(HERE / 'native-task.md'),
              'artifacts': {path.name: {'bytes': path.stat().st_size, 'sha256': digest(path)}
                            for path in work.iterdir() if path.is_file()},
              'browser_check': 'not_run_at_generation_time'}
    (root / 'run.public.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    raise SystemExit(proc.returncode)


if __name__ == '__main__':
    main()
