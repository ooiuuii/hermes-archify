"""Extract only scoped native-run provenance and basic artifact checks, not reasoning."""
import argparse
import collections
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sqlite3


class Artifact(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = collections.Counter()
        self.script_urls = []
        self.event_attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        for key, value in attrs:
            if key.lower().startswith('on'):
                self.event_attributes.append(key)
            if tag == 'script' and key == 'src':
                self.script_urls.append(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.run_root.resolve()
    report = json.loads((root / 'run.public.json').read_text(encoding='utf-8'))
    db = sqlite3.connect('file:' + (root / 'hermes-home/state.db').as_posix() + '?mode=ro', uri=True)
    counts = dict(db.execute('SELECT tool_name,COUNT(*) FROM messages WHERE role=? GROUP BY tool_name', ('tool',)))
    skills, writes = [], []
    for (raw,) in db.execute('SELECT tool_calls FROM messages WHERE role=? AND tool_calls IS NOT NULL', ('assistant',)):
        for call in json.loads(raw):
            function = call.get('function', {})
            name = function.get('name')
            arguments = function.get('arguments', {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if name == 'skill_view':
                skills.append({key: arguments.get(key) for key in ('name', 'file_path')})
            elif name == 'write_file':
                writes.append({key: arguments.get(key) for key in ('path', 'file_path') if key in arguments})
    html_path = root / 'work/hermes-native.architecture.html'
    html = html_path.read_text(encoding='utf-8-sig')
    parsed = Artifact()
    parsed.feed(html)
    used_native = any(item['name'] == 'architecture-diagram' for item in skills)
    template_read = any(item['name'] == 'architecture-diagram' and item.get('file_path') == 'templates/template.html' for item in skills)
    passed = (report['exit_code'] == 0 and used_native and template_read and parsed.tags['svg'] > 0
              and parsed.tags['script'] == 0 and not parsed.event_attributes
              and not counts.get('archify_diagram') and bool(counts.get('write_file')))
    output = {'ok': passed, 'native_skill_loaded': used_native, 'native_template_loaded': template_read,
              'recorded_skill_calls': skills, 'recorded_write_paths': writes, 'tool_result_counts': counts,
              'html_sha256': hashlib.sha256(html_path.read_bytes()).hexdigest(),
              'html_bytes': html_path.stat().st_size,
              'svg_elements': parsed.tags['svg'], 'javascript_elements': parsed.tags['script'],
              'event_handler_attributes': parsed.event_attributes,
              'archify_tool_invocations': counts.get('archify_diagram', 0),
              'interpretation': 'Real native-skill output; checks are basic file/provenance checks, not semantic certification.',
              'browser_check': 'separate observer report required'}
    (root / 'native-proof.public.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
