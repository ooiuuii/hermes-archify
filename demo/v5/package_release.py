"""Prepare an explicit public V5 asset bundle; no network, inference or publishing."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
import zipfile

HERE = Path(__file__).resolve().parent
VIDEO = 'hermes-archify-native-vs-plugin-v5.zh.mp4'
FILES = [VIDEO, 'captions.zh.srt', 'captions.zh.ass', 'hermes.architecture.html',
         'receipt.public.json', 'rejection.public.json', 'captures/overview.png',
         'native/hermes-native.architecture.html', 'native/hermes-native.png',
         'native/run.public.json', 'native/native-proof.public.json',
         'native/source-notes.md', 'previous.manifest.json', 'QUALITY-CHECK.md',
         'PR-SOURCE-NOTES.md'] + [f'recordings/{scene}.{ext}'
             for scene in ('02-native', '06-route', '07-source') for ext in ('mp4', 'json')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def normalize(text, roots):
    # Exact task-owned locations only. Generic project references in approved
    # HTML/PNG/video stay untouched; source paths are not architectural claims.
    for index, root in enumerate(sorted(roots, key=len, reverse=True), start=1):
        root = root.replace('\\', '/')
        replacement = f'<SOURCE_ROOT_{index}>'
        text = text.replace(root, replacement).replace(root.replace('/', '\\'), replacement)
    return text


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src', 'poster') and value:
                part = urlsplit(value)
                if not part.scheme and not part.netloc and part.path:
                    self.links.append(unquote(part.path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--live-work', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--redact-root', action='append', default=[],
                        help='Task-owned absolute source root to normalize in public text; repeat as needed.')
    args = parser.parse_args()
    source, live, output = (p.resolve() for p in (args.assets, args.live_work, args.destination))
    if output.exists() or any(output == p or output in p.parents or p in output.parents for p in (source, live)):
        raise SystemExit('Choose a fresh directory separate from the preserved source artifacts.')
    for name in FILES + ['manifest.json']:
        if not (source / name).is_file():
            raise SystemExit(f'Missing required source: {name}')
    for name in ('hermes.architecture.json', 'source-evidence.md'):
        if not (live / name).is_file():
            raise SystemExit(f'Missing recorded model/evidence: {name}')
    original = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if sha(source / VIDEO) != original['sha256']:
        raise SystemExit('Approved video no longer matches its manifest.')
    if sha(source / 'hermes.architecture.html') != original['artifact_sha256']:
        raise SystemExit('Plugin HTML no longer matches its receipt.')
    output.mkdir(parents=True)
    bundle = output / 'bundle'
    for name in FILES:
        target = bundle / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    shutil.copyfile(live / 'hermes.architecture.json', bundle / 'hermes.architecture.json')
    (bundle / 'plugin-source-notes.md').write_text(
        normalize((live / 'source-evidence.md').read_text(encoding='utf-8'), args.redact_root), encoding='utf-8')
    notes = bundle / 'native/source-notes.md'
    notes.write_text(normalize(notes.read_text(encoding='utf-8'), args.redact_root), encoding='utf-8')
    proof_path = bundle / 'native/native-proof.public.json'
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    for item in proof['recorded_write_paths']:
        for key in tuple(item):
            item[key] = str(item[key]).replace('\\', '/').rsplit('/', 1)[-1]
    proof['publication_note'] = 'Write paths are basenames; the original private run record is retained locally.'
    dump(proof_path, proof)
    manifest = {**original, 'publication': {
        'version': '0.1.1', 'original_manifest_sha256': sha(source / 'manifest.json'),
        'notes': 'Source-note paths and proof write paths normalized; video and both HTML/PNG outputs are unchanged.',
        'excluded': ['private logs', 'profiles', 'databases', 'raw JPEG frames', 'failed takes', 'intermediate edits'],
        'model': 'hermes.architecture.json', 'source_notes': 'plugin-source-notes.md',
        'review': 'QUALITY-CHECK.md',
    }}
    for entry in manifest['native_evidence']:
        entry['original_sha256'] = entry['sha256']
        entry['sha256'] = sha(bundle / entry['file'])
        entry['bytes'] = (bundle / entry['file']).stat().st_size
    # The generation receipt's original artifact hashes are historical evidence,
    # not hashes of redacted copies. Keep them and add a clearly separate mapping.
    run_path = bundle / 'native/run.public.json'
    run = json.loads(run_path.read_text(encoding='utf-8'))
    run['publication'] = {'original_receipt_sha256': sha(source / 'native/run.public.json'),
                          'published_source_notes_sha256': sha(notes),
                          'artifact_hashes_above': 'original generation bytes before source-note path normalization'}
    dump(run_path, run)
    for entry in manifest['native_evidence']:
        entry['sha256'] = sha(bundle / entry['file'])
        entry['bytes'] = (bundle / entry['file']).stat().st_size
    manifest['publication']['files'] = sorted(
        {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
        | {'manifest.json', 'index.html', 'player.html', 'PUBLICATION.md', 'SHA256SUMS.txt'})
    dump(bundle / 'manifest.json', manifest)
    player = (HERE / 'player.html').read_text(encoding='utf-8')
    player = player.replace('本地演示', '公开演示包')
    player = player.replace('旧版产物保持不变，不代表新产品版本发布。', '旧版产物保持不变；本包随插件 v0.1.1 发布。')
    player = player.replace('<a href="previous.manifest.json">',
        '<a href="QUALITY-CHECK.md">成片检查</a> · <a href="PR-SOURCE-NOTES.md">PR 图片来源核查</a> · <a href="previous.manifest.json">')
    player = player.replace('公开生成记录</a>', '公开生成记录</a> · <a href="native/native-proof.public.json">技能调用证明</a>')
    player = player.replace('<li><a href="hermes.architecture.html">交互图</a>',
        '<li><a href="hermes.architecture.json">可编辑 JSON</a> · <a href="plugin-source-notes.md">源码说明</a> · <a href="hermes.architecture.html">交互图</a>')
    player = player.replace('__DEMO_MANIFEST_JSON__', json.dumps(manifest, ensure_ascii=False).replace('<', r'\u003c'))
    for name in ('index.html', 'player.html'):
        (bundle / name).write_text(player, encoding='utf-8')
    (bundle / 'PUBLICATION.md').write_text(
        '# Public V5 package\n\nExtract this ZIP and open index.html. No live Hermes instance is required.\n\n'
        'Video, HTML and PNG bytes are the approved recorded outputs. Text source notes and proof paths are normalized. '
        'Generation-receipt hashes refer to the original generation; manifest native_evidence hashes refer to the published copies. '
        'SHA256SUMS.txt covers every packaged file other than itself.\n\n'
        'Production manifests retain hashes of intermediate scenes and screenshots as historical evidence; those build files and raw JPEG frames '
        'are deliberately not included. The public file inventory is in manifest.publication.files. '
        'Generic project paths visible in original media are retained; no private profiles, credentials, logs or transcripts are included.\n', encoding='utf-8')
    # Scan only the explicitly assembled public set. Fail closed, printing names
    # rather than matched content; no private directory traversal or secret reads.
    forbidden = re.compile(r'(?:[A-Z]:[/\\]Users[/\\]|/Users/|/home/|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{24,})', re.I)
    for path in bundle.rglob('*'):
        if path.suffix in ('.json', '.html', '.md', '.srt', '.ass') and forbidden.search(path.read_text(encoding='utf-8')):
            raise SystemExit(f'Public evidence requires manual redaction: {path.relative_to(bundle)}')
    links = LocalLinks()
    links.feed(player)
    for href in links.links:
        path = (bundle / href).resolve()
        if not path.is_relative_to(bundle) or (href != 'SHA256SUMS.txt' and not path.is_file()):
            raise SystemExit(f'Broken or out-of-bundle player link: {href}')
    sums = ''.join(f'{sha(p)}  {p.relative_to(bundle).as_posix()}\n' for p in sorted(bundle.rglob('*')) if p.is_file())
    (bundle / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
    archive = output / 'hermes-archify-demo-v5.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(bundle).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise SystemExit('ZIP CRC validation failed.')
    print(json.dumps({'bundle': str(bundle), 'archive': str(archive), 'sha256': sha(archive),
                      'bytes': archive.stat().st_size, 'video_unchanged': sha(bundle / VIDEO) == original['sha256'],
                      'player_links_checked': len(links.links)}, indent=2))


if __name__ == '__main__':
    main()
