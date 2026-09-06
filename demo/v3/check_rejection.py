"""Record an intentional structural error; never modify the installed plugin."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bridge import execute


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--repo-root', type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.input.read_text(encoding='utf-8-sig'))
    good_html = args.assets / 'hermes.architecture.html'
    before = hashlib.sha256(good_html.read_bytes()).hexdigest()
    spec['connections'][0]['to'] = 'demo_missing_node'
    broken = args.assets / 'intentional-missing-node.architecture.json'
    with broken.open('x', encoding='utf-8') as stream:
        json.dump(spec, stream, ensure_ascii=False, indent=2)
    result = execute('validate', str(broken.resolve()), repo_root=str(args.repo_root.resolve()))
    after = hashlib.sha256(good_html.read_bytes()).hexdigest()
    if result['ok'] or before != after:
        raise SystemExit('The recording does not demonstrate the intended rejection.')
    public = {'intentional_test_input': True, 'mutation': 'connections[0].to = demo_missing_node',
              'ok': result['ok'], 'exit_code': result.get('exit_code'),
              'error': result.get('error'), 'diagnostics': result.get('diagnostics'),
              'stage': result.get('receipt', {}).get('stage'),
              'saved_good_html_unchanged': before == after,
              'scope': 'Structural rejection only; not semantic correctness or a native Hermes failure.'}
    # This error is derived from a public graph; strip host paths before recording.
    clean = json.dumps(public, ensure_ascii=False, indent=2)
    for local in (str(args.assets.resolve()), str(args.input.resolve()), str(args.repo_root.resolve())):
        clean = clean.replace(local.replace('\\', '\\\\'), '<local-path>')
    (args.assets / 'rejection.public.json').write_text(clean, encoding='utf-8')
    print(clean)
