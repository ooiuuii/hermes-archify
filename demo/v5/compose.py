"""Replace only V4's native scene with a real recording; never generate, record or upload."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('v4_compositor', ROOT.parent / 'v4' / 'compose.py')
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)
OUTPUT = 'hermes-archify-native-vs-plugin-v5.zh.mp4'
NATIVE = '02-native'
SCENES = ['01-hook', NATIVE, '03-problem', '04-switch', '05-question',
          '06-route', '07-source', '08-checks', '09-recap', '10-close']
NATIVE_FILES = ['native/hermes-native.architecture.html', 'native/hermes-native.png',
                'native/run.public.json', 'native/source-notes.md']


def source_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'Missing or out-of-directory input: {name}')
    return path


def evidence(path, root):
    return {'file': path.relative_to(root).as_posix(), 'sha256': v4.sha256(path),
            'bytes': path.stat().st_size}


def native_frame(font_path):
    image = v4.Image.new('RGB', (v4.W, v4.H), v4.BG)
    draw = v4.ImageDraw.Draw(image)

    def text(x, y, value, size=30, color=v4.INK, width=524):
        font = v4.ImageFont.truetype(str(font_path), size)
        for line in value.split('\n'):
            if font.getlength(line) > width:
                raise ValueError(f'Static caption exceeds its panel width: {line}')
            draw.text((x, y), line, font=font, fill=color)
            y += round(size * 1.5)

    draw.rounded_rectangle((48, 88, 644, 924), radius=16, fill='#281e1b', outline=v4.ORANGE, width=2)
    draw.rounded_rectangle((670, 80, 1880, 932), radius=12, fill='#151b23', outline=v4.ORANGE, width=2)
    text(52, 24, 'A · Hermes 原生 architecture-diagram', 36, v4.ORANGE, 1820)
    text(82, 128, '本次真实生成', 38, v4.ORANGE)
    text(82, 190, '不是官方空白模板', 32)
    text(82, 298, '直接生成 HTML / SVG', 32)
    text(82, 354, 'HTML + SVG / 普通网页阅读', 27)
    text(82, 456, '未调用 Archify', 34, v4.ORANGE)
    text(82, 558, '清晰组织模块与关系\n适合静态说明与讲解', 30)
    text(82, 747, '生成记录与源码说明随包提供\n不是质量或速度竞赛', 25, v4.MUTED)
    text(51, 1043, '完整视口 · 连续浏览器实录 · 原速播放 · A 为本次原生生成，B 沿用先前经监督的产物',
         18, v4.MUTED, 1815)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True, help='Complete V4 artifact directory, preserved unchanged.')
    parser.add_argument('--assets', type=Path, required=True, help='Separate V5 directory with native evidence and recordings/02-native.*.')
    parser.add_argument('--font', type=Path, default=Path('C:/Windows/Fonts/msyh.ttc'))
    args = parser.parse_args()
    previous, assets = args.previous.resolve(), args.assets.resolve()
    if previous == assets or previous in assets.parents or assets in previous.parents:
        raise SystemExit('V4 and V5 directories must not overlap; previous editions remain untouched.')
    if (assets / OUTPUT).exists():
        raise SystemExit('Final video already exists; use a fresh artifact directory. Never overwrite a finished edit.')
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise SystemExit(f'{tool} must already be installed; this script never installs tools.')
    if not args.font.is_file():
        raise SystemExit('Pass --font with an existing Chinese TrueType/OpenType font.')
    prior = v4.read_json(source_file(previous, 'manifest.json'))
    scenes = prior['scenes']
    if ([scene['id'] for scene in scenes] != SCENES or prior['video'] != v4.OUTPUT
            or prior['dimensions'] != [v4.W, v4.H] or prior['fps'] != v4.FPS):
        raise SystemExit('Expected the complete ten-scene 1920x1080, 30 fps V4 baseline.')
    copies, plans, elapsed = {}, [], 0.0

    def reuse(name):
        copies[name] = source_file(previous, name)
        return copies[name]

    for scene in scenes:
        scene_id, duration = scene['id'], float(scene['duration'])
        if not math.isfinite(duration) or duration <= 0 or abs(float(scene['start']) - elapsed) > 0.0001:
            raise SystemExit(f'Invalid previous scene timeline: {scene_id}')
        elapsed += duration
        original = source_file(previous, f'{scene_id}.mp4')
        info = v4.probe(original)
        v4.require_duration(info, duration, original)
        if ((info['width'], info['height']) != (v4.W, v4.H) or not info['audio']
                or abs(info['seconds'] - duration) > 1 / v4.FPS
                or v4.sha256(original) != scene['segment_sha256']):
            raise SystemExit(f'Previous scene does not match the approved V4 segment: {scene_id}')
        plans.append((scene, original))
        if scene_id != NATIVE:
            reuse(f'{scene_id}.mp4')
            for name in scene.get('frames', []):
                reuse(f'frames/{name}')
        if scene_id in ('06-route', '07-source'):
            recording = scene['recording']
            for field, checksum in [('raw_clip', 'sha256'), ('input_events', 'input_events_sha256')]:
                if v4.sha256(reuse(recording[field])) != recording[checksum]:
                    raise SystemExit(f'Previous recording evidence has changed: {scene_id} / {field}')
    native_scene = scenes[1]
    duration = float(native_scene['duration'])
    raw = source_file(assets, f'recordings/{NATIVE}.mp4')
    metadata = source_file(assets, f'recordings/{NATIVE}.json')
    raw_info = v4.probe(raw)
    v4.require_duration(raw_info, duration, raw)
    if not isinstance(v4.read_json(metadata), dict):
        raise SystemExit('Native recording metadata must be a JSON object from the actual recording.')
    native_evidence = [evidence(source_file(assets, name), assets) for name in NATIVE_FILES]
    if not isinstance(v4.read_json(assets / 'native/run.public.json'), dict):
        raise SystemExit('Native generation evidence must be a public JSON object.')
    for name in ('captions.zh.srt', 'receipt.public.json', 'hermes.architecture.html', 'captures/overview.png'):
        reuse(name)
    if v4.sha256(copies['hermes.architecture.html']) != prior['artifact_sha256']:
        raise SystemExit('Plugin HTML no longer matches the V4 evidence.')
    if (previous / 'rejection.public.json').is_file():
        reuse('rejection.public.json')
    for path in (previous / 'captures').glob('*'):
        if path.is_file():
            reuse(f'captures/{path.name}')
    copies['previous.manifest.json'] = previous / 'manifest.json'
    captions = v4.srt_to_ass_events(copies['captions.zh.srt'].read_text(encoding='utf-8-sig'))
    if len(captions) != 43 or v4.sha256(copies['captions.zh.srt']) != prior['caption_source_sha256']:
        raise SystemExit('Expected all 43 unchanged V4 subtitle cues.')
    ass = v4.load_caption_serializer()(captions)
    player_template = (ROOT / 'player.html').read_text(encoding='utf-8')
    if player_template.count('__DEMO_MANIFEST_JSON__') != 1:
        raise SystemExit('Player template must contain one inline manifest placeholder.')
    generated = [OUTPUT, 'picture.mp4', 'manifest.json', 'captions.zh.ass', 'edit.ffconcat',
                 'player.html', 'index.html', 'SHA256SUMS.txt', f'{NATIVE}.mp4', f'frames/{NATIVE}-frame.png']
    for name in generated:
        if (assets / name).exists():
            raise SystemExit(f'Refusing to overwrite a generated file: {assets / name}')
    for name, source in copies.items():
        target = assets / name
        if target.exists() and (not target.is_file() or v4.sha256(target) != v4.sha256(source)):
            raise SystemExit(f'Refusing to overwrite different reuse evidence: {name}')
    outer_image = native_frame(args.font)  # Validate font/layout before any output is written.
    # Full preflight above: no new generation, recording, speed change, crop or frozen tail.
    for name, source in copies.items():
        v4.copy_identical_or_new(source, assets / name)
    (assets / 'captions.zh.ass').write_text(ass, encoding='utf-8')
    outer = assets / 'frames' / f'{NATIVE}-frame.png'
    outer.parent.mkdir(parents=True, exist_ok=True)
    outer_image.save(outer)
    x, y, width, height = v4.fit_recording(raw_info['width'], raw_info['height'])
    graph = (f'[1:v]setpts=PTS-STARTPTS,scale={width}:{height}:flags=lanczos,setsar=1,fps={v4.FPS}[browser];'
             f'[0:v][browser]overlay={x}:{y}:shortest=1:eof_action=endall,format=yuv420p[video]')
    segment = assets / f'{NATIVE}.mp4'
    v4.run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-loop', '1', '-framerate', v4.FPS,
           '-i', outer, '-i', raw, '-i', plans[1][1], '-filter_complex_threads', '4',
           '-filter_complex', graph, '-map', '[video]', '-map', '2:a:0', '-t', f'{duration:.8f}',
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-threads', '4', '-r', v4.FPS,
           '-c:a', 'copy', '-movflags', '+faststart', segment)
    v4.require_duration(v4.probe(segment), duration, segment)
    final_scenes = []
    for scene, original in plans:
        record = {**scene, 'previous_segment_sha256': v4.sha256(original),
                  'origin': 'unchanged V4 scene MP4 including original narration, before subtitle burn'}
        if scene['id'] == NATIVE:
            record.update(title='A · Hermes 原生 architecture-diagram · 本次真实生成',
                          origin='continuous browser recording of this native generation; original V4 narration unchanged',
                          captures=[], frames=[outer.name], recording={
                              'raw_clip': raw.relative_to(assets).as_posix(), 'sha256': v4.sha256(raw),
                              'bytes': raw.stat().st_size, 'probe': raw_info,
                              'input_events': metadata.relative_to(assets).as_posix(),
                              'input_events_sha256': v4.sha256(metadata),
                              'input_method': 'real browser input events; no claim of human operation',
                              'speed': 1.0, 'no_speed_change': True, 'trim_start_seconds': 0,
                              'used_seconds': duration, 'freeze_tail': False, 'crop': None,
                              'display_rectangle': [x, y, width, height],
                              'frame_rate_policy': '30 fps output cadence; timestamps are not speed-scaled'})
        record['segment_sha256'] = v4.sha256(assets / f'{scene["id"]}.mp4')
        final_scenes.append(record)
    (assets / 'edit.ffconcat').write_text('ffconcat version 1.0\n' + ''.join(
        f"file '{scene_id}.mp4'\n" for scene_id in SCENES), encoding='utf-8')
    v4.run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-safe', '0', '-f', 'concat',
           '-i', 'edit.ffconcat', '-c', 'copy', '-threads', '4', 'picture.mp4', cwd=assets)
    v4.run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', 'picture.mp4',
           '-vf', "ass=filename='captions.zh.ass'", '-c:v', 'libx264', '-preset', 'fast',
           '-crf', '19', '-threads', '4', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
           '-movflags', '+faststart', OUTPUT, cwd=assets)
    final = assets / OUTPUT
    final_info = v4.probe(final)
    if abs(final_info['seconds'] - elapsed) > 1 / v4.FPS:
        raise SystemExit('Final duration differs from the preserved narration/subtitle timeline; inspect before handoff.')
    manifest = {**prior, 'video': OUTPUT, 'sha256': v4.sha256(final), 'seconds': final_info['seconds'],
                'scenes': final_scenes, 'final_probe': final_info,
                'previous_manifest_sha256': v4.sha256(previous / 'manifest.json'),
                'caption_source_sha256': v4.sha256(assets / 'captions.zh.srt'),
                'caption_ass_sha256': v4.sha256(assets / 'captions.zh.ass'), 'caption_count': 43,
                'recording': '02-native, 06-route and 07-source are continuous original-speed browser recordings; nine V4 scene MP4s reused unchanged',
                'native_baseline': 'This actual Hermes architecture-diagram generation, direct HTML/SVG; not an empty official template; no Archify call',
                'native_evidence': native_evidence, 'plugin_baseline': 'Previously supervised delivered artifact, not a new B model run',
                'new_model_run': True, 'new_model_run_scope': 'A only, completed before browser recording; see native/run.public.json',
                'no_speed_change': True, 'browser_recording_review': 'pending review of this newly composed video',
                'evidence_files': sorted(set(copies) | set(NATIVE_FILES) | {raw.relative_to(assets).as_posix(), metadata.relative_to(assets).as_posix()}),
                'editorial_notes': [
                    'Only 02-native was replaced; nine V4 scene MP4s, all narration and 43 subtitle cues remain unchanged.',
                    'A shows this actual native generation; B reuses the previously supervised artifact. Not a quality, speed or cost benchmark.',
                    'All three product segments are continuous real browser recordings, not live model-generation footage; no claim of human operation.',
                    'The full viewport is retained at original speed; only uniform display scaling and excess tail trimming.',
                    'Native HTML/SVG supports useful static explanation. The failure card is editorial, not a captured native failure.',
                    'The missing-node test intentionally damages a copied graph; it is not an observed native defect.',
                    'Archify supplies the interaction/checking engine; neither workflow proves runtime topology or semantic correctness.',
                    'Teknium image provenance remains unverified; this video makes no attribution or endorsement claim.',
                ]}
    (assets / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    player = player_template.replace('__DEMO_MANIFEST_JSON__', json.dumps(manifest, ensure_ascii=False).replace('<', r'\u003c'))
    for name in ('player.html', 'index.html'):
        (assets / name).write_text(player, encoding='utf-8')
    (assets / 'SHA256SUMS.txt').write_text(f'{manifest["sha256"]}  {OUTPUT}\n', encoding='utf-8')
    print(json.dumps({'video': str(final), 'player': str(assets / 'player.html'),
                      'seconds': final_info['seconds'], 'sha256': manifest['sha256'],
                      'review': 'Composition finished; watch the actual result before claiming visual approval.'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
