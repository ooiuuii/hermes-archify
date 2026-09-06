"""Replace two V3 scenes with uninterrupted browser recordings; never record or upload."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = 'hermes-archify-continuous-demo-v4.zh.mp4'
W, H, FPS = 1920, 1080, 30
REPLACEMENTS = {'06-route', '07-source'}
VIDEO_BOUNDS = (678, 88, 1872, 924)
BG, INK, MUTED = '#0b1118', '#f6f2e9', '#abb6c3'
ORANGE, GREEN = '#ffac80', '#91edc4'


def run(*args, cwd=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def probe(path):
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,duration,pix_fmt,sample_rate,channels',
        '-of', 'json', str(path),
    ], capture_output=True, text=True, encoding='utf-8', check=True)
    data = json.loads(result.stdout)
    video = next((item for item in data['streams'] if item['codec_type'] == 'video'), None)
    if not video:
        raise ValueError(f'No video stream: {path}')
    duration = float(video.get('duration', data['format'].get('duration', 0)))
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f'Invalid video duration: {path}')
    return {'width': video['width'], 'height': video['height'], 'seconds': duration,
            'frame_rate': video['avg_frame_rate'], 'video_codec': video['codec_name'],
            'pixel_format': video.get('pix_fmt'),
            'audio': [item for item in data['streams'] if item['codec_type'] == 'audio']}


def require_duration(info, seconds, path):
    # Only tolerate ffprobe's six-decimal serialization, never a missing frame.
    if info['seconds'] + 0.000001 < seconds:
        raise ValueError(f'Clip too short: {path} is {info["seconds"]:.6f}s; '
                         f'need {seconds:.6f}s. Record longer; no frozen-tail padding is allowed.')


def fit_recording(width, height):
    left, top, right, bottom = VIDEO_BOUNDS
    scale = min((right - left) / width, (bottom - top) / height)
    fitted_w = max(2, int(width * scale) // 2 * 2)
    fitted_h = max(2, int(height * scale) // 2 * 2)
    return (left + (right - left - fitted_w) // 2,
            top + (bottom - top - fitted_h) // 2, fitted_w, fitted_h)


def srt_to_ass_events(source):
    """Keep SRT text verbatim; convert only timestamp precision and line separators."""
    def timestamp(value):
        match = re.fullmatch(r'(\d+):([0-5]\d):([0-5]\d),(\d{3})', value)
        if not match:
            raise ValueError(f'Invalid SRT timestamp: {value}')
        hour, minute, second, millis = map(int, match.groups())
        centis = round((((hour * 60 + minute) * 60 + second) * 1000 + millis) / 10)
        seconds, fraction = divmod(centis, 100)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f'{hours}:{minutes:02d}:{seconds:02d}.{fraction:02d}'

    events = []
    normalized = source.replace('\r\n', '\n').strip('\n')
    for block in normalized.split('\n\n'):
        lines = block.split('\n')
        if len(lines) < 3 or not lines[0].isdigit():
            raise ValueError('Malformed SRT cue; refusing to rewrite its text.')
        timing = lines[1].split(' --> ')
        if len(timing) != 2:
            raise ValueError(f'Malformed SRT timing: {lines[1]}')
        events.append((timestamp(timing[0]), timestamp(timing[1]), '\n'.join(lines[2:])))
    if not events:
        raise ValueError('No captions found in the previous SRT.')
    return events


def load_caption_serializer():
    spec = importlib.util.spec_from_file_location('v2_caption_builder', ROOT.parent / 'v2' / 'build_video.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.serialize_ass_captions


def copy_identical_or_new(source, destination):
    if destination.exists():
        if not destination.is_file() or sha256(source) != sha256(destination):
            raise ValueError(f'Refusing to overwrite a different file: {destination}')
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def frame(scene_id, font_path):
    image = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=30, color=INK, width=548, gap=1.4):
        font = ImageFont.truetype(str(font_path), size)
        rows, line = [], ''
        for char in value:
            if char == '\n' or font.getlength(line + char) > width:
                rows.append(line)
                line = '' if char == '\n' else char
            else:
                line += char
        if line:
            rows.append(line)
        for row in rows:
            draw.text((x, y), row, font=font, fill=color)
            y += round(size * gap)
        return y

    draw.rounded_rectangle((48, 88, 644, 924), radius=16, fill='#281e1b', outline=ORANGE, width=2)
    draw.rounded_rectangle((670, 80, 1880, 932), radius=12, fill='#10201e', outline=GREEN, width=2)
    text(52, 27, 'A  原生默认技能 · 静态读图', 29, ORANGE)
    text(678, 27, 'B  插件 · 真实网页连续录屏', 30, GREEN, 1180)
    text(82, 124, '同一个阅读问题', 25, MUTED)
    text(82, 175, 'CLI 怎样到达工具？', 38, INK)
    if scene_id == '06-route':
        text(82, 292, 'A  自己沿线读', 36, ORANGE)
        text(85, 359, '找到入口\n辨认分支\n沿着箭头找到终点', 30, INK, gap=1.65)
        text(82, 580, 'B  选择起点与终点', 34, GREEN)
        text(85, 648, '图中路径单独高亮\n6 个节点 / 5 次跳转', 30, INK, gap=1.65)
    else:
        text(82, 292, 'A  另外定位代码', 36, ORANGE)
        text(85, 359, '默认模板没有来源面板\n自行查找版本、文件、行号', 29, INK, gap=1.65)
        text(82, 557, 'B  从节点查看依据', 34, GREEN)
        text(85, 628, '查找 tool_registry\n查看固定版本的源码引用', 29, INK, gap=1.65)
    text(85, 791, '路径不是运行时追踪。\n引用不是语义认证。', 26, MUTED, gap=1.55)
    text(51, 1043, '连续浏览器实录 · 真实输入事件驱动鼠标高亮 · 非现场模型生成 · 交互与校验来自 Archify',
         18, MUTED, 1815)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--font', type=Path, help='Chinese font for the static A/B frame (default: Windows Microsoft YaHei).')
    args = parser.parse_args()
    previous, assets = args.previous.resolve(), args.assets.resolve()
    if previous == assets:
        raise SystemExit('V4 must use a different artifact directory; V3 remains untouched.')
    final = assets / OUTPUT
    if final.exists():
        raise SystemExit('Final video already exists. Use a fresh artifact directory; it will not be overwritten.')
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise SystemExit(f'{tool} must already be installed; this script never installs tools.')
    font_path = args.font or Path('C:/Windows/Fonts/msyh.ttc')
    if not font_path.is_file():
        raise SystemExit('Pass --font with an existing Chinese TrueType/OpenType font.')
    prior = read_json(previous / 'manifest.json')
    scenes = prior['scenes']
    ids = [scene['id'] for scene in scenes]
    if len(ids) != 10 or len(set(ids)) != 10 or not REPLACEMENTS.issubset(ids):
        raise SystemExit('Expected the ten V3 scenes, including 06-route and 07-source.')
    if prior['dimensions'] != [W, H] or prior['fps'] != FPS:
        raise SystemExit('V3 must be 1920x1080 at 30 fps to reuse its eight scene clips unchanged.')
    if any(not re.fullmatch(r'\d{2}-[a-z]+', scene_id) for scene_id in ids):
        raise SystemExit('Unexpected scene filename.')
    plans = []
    for scene in scenes:
        scene_id, duration = scene['id'], float(scene['duration'])
        original = previous / f'{scene_id}.mp4'
        original_info = probe(original)
        require_duration(original_info, duration, original)
        if (original_info['width'], original_info['height']) != (W, H) or not original_info['audio']:
            raise SystemExit(f'Expected full-size V3 scene with its original narration: {original}')
        plan = {'scene': scene, 'original': original, 'original_sha256': sha256(original)}
        if scene_id in REPLACEMENTS:
            raw = assets / 'recordings' / f'{scene_id}.mp4'
            metadata = raw.with_suffix('.json')
            info = probe(raw)
            require_duration(info, duration, raw)
            if not isinstance(read_json(metadata), (dict, list)):
                raise SystemExit(f'Recording input-event metadata must be JSON: {metadata}')
            plan.update(raw=raw, info=info, metadata=metadata,
                        raw_sha256=sha256(raw), metadata_sha256=sha256(metadata))
        plans.append(plan)
    required = ['captions.zh.srt', 'receipt.public.json', 'hermes.architecture.html',
                'native-template.html', 'captures/overview.png']
    for name in required:
        if not (previous / name).is_file():
            raise SystemExit(f'Missing previous evidence: {name}')
    if sha256(previous / 'hermes.architecture.html') != prior['artifact_sha256']:
        raise SystemExit('Previous HTML no longer matches the previous manifest.')
    serializer = load_caption_serializer()
    ass = serializer(srt_to_ass_events((previous / 'captions.zh.srt').read_text(encoding='utf-8-sig')))
    player_template = (ROOT / 'player.html').read_text(encoding='utf-8')
    if '__DEMO_MANIFEST_JSON__' not in player_template:
        raise SystemExit('Player template is missing its inline manifest placeholder.')
    # No writes happen before both complete recordings and all reuse inputs pass preflight.
    generated = [OUTPUT, 'picture.mp4', 'manifest.json', 'captions.zh.ass', 'edit.ffconcat',
                 'player.html', 'index.html', 'SHA256SUMS.txt']
    generated += [f'{scene_id}.mp4' for scene_id in REPLACEMENTS]
    generated += [f'frames/{scene_id}-frame.png' for scene_id in REPLACEMENTS]
    for name in generated:
        if (assets / name).exists():
            raise SystemExit(f'Refusing to replace an existing generated file: {assets / name}')
    assets.mkdir(parents=True, exist_ok=True)
    (assets / 'frames').mkdir(exist_ok=True)
    references = required + [name for name in ('rejection.public.json',)
                             if (previous / name).is_file()]
    for name in references:
        copy_identical_or_new(previous / name, assets / name)
    for source in (previous / 'captures').glob('*'):
        if source.is_file():
            copy_identical_or_new(source, assets / 'captures' / source.name)
    copy_identical_or_new(previous / 'manifest.json', assets / 'previous.manifest.json')
    (assets / 'captions.zh.ass').write_text(ass, encoding='utf-8')
    final_scenes = []
    for plan in plans:
        scene, original = plan['scene'], plan['original']
        scene_id, duration = scene['id'], float(scene['duration'])
        segment = assets / f'{scene_id}.mp4'
        record = {**scene, 'previous_segment_sha256': plan['original_sha256']}
        if scene_id not in REPLACEMENTS:
            copy_identical_or_new(original, segment)
            record['origin'] = 'unchanged V3 scene MP4, including original narration, before subtitle burn'
            for filename in scene.get('frames', []):
                copy_identical_or_new(previous / 'frames' / filename, assets / 'frames' / filename)
        else:
            x, y, width, height = fit_recording(plan['info']['width'], plan['info']['height'])
            outer = assets / 'frames' / f'{scene_id}-frame.png'
            frame(scene_id, font_path).save(outer)
            filtergraph = (f'[1:v]setpts=PTS-STARTPTS,scale={width}:{height}:flags=lanczos,setsar=1,fps={FPS}[browser];'
                           f'[0:v][browser]overlay={x}:{y}:shortest=1:eof_action=endall,format=yuv420p[video]')
            run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-loop', '1', '-framerate', FPS,
                '-i', outer, '-i', plan['raw'], '-i', original, '-filter_complex_threads', '4',
                '-filter_complex', filtergraph, '-map', '[video]', '-map', '2:a:0',
                '-t', f'{duration:.8f}', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
                '-threads', '4', '-r', FPS, '-c:a', 'copy', '-movflags', '+faststart', segment)
            info = probe(segment)
            require_duration(info, duration, segment)
            record.update(origin='continuous real browser recording, with unchanged original V3 narration',
                          captures=[], frames=[outer.name], recording={
                              'raw_clip': plan['raw'].relative_to(assets).as_posix(),
                              'sha256': plan['raw_sha256'], 'bytes': plan['raw'].stat().st_size,
                              'probe': plan['info'], 'input_events': plan['metadata'].relative_to(assets).as_posix(),
                              'input_events_sha256': plan['metadata_sha256'],
                              'input_method': 'real browser input events; event-driven mouse highlight; not claimed human-operated',
                              'speed': 1.0, 'no_speed_change': True, 'trim_start_seconds': 0,
                              'used_seconds': duration, 'freeze_tail': False, 'crop': None,
                              'display_rectangle': [x, y, width, height],
                              'frame_rate_policy': '30 fps output cadence; timestamps are not speed-scaled',
                          })
        record['segment_sha256'] = sha256(segment)
        final_scenes.append(record)
    listing = 'ffconcat version 1.0\n' + ''.join(f"file '{scene_id}.mp4'\n" for scene_id in ids)
    (assets / 'edit.ffconcat').write_text(listing, encoding='utf-8')
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-safe', '0', '-f', 'concat',
        '-i', 'edit.ffconcat', '-c', 'copy', '-threads', '4', 'picture.mp4', cwd=assets)
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', 'picture.mp4',
        '-vf', "ass=filename='captions.zh.ass'", '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '19', '-threads', '4', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
        '-movflags', '+faststart', OUTPUT, cwd=assets)
    final_info = probe(final)
    total = sum(float(scene['duration']) for scene in scenes)
    if abs(final_info['seconds'] - total) > 1 / FPS:
        raise SystemExit('Final duration differs from the preserved subtitle/narration timeline; inspect before handoff.')
    manifest = {**prior, 'video': OUTPUT, 'sha256': sha256(final), 'seconds': final_info['seconds'],
                'scenes': final_scenes, 'final_probe': final_info,
                'previous_manifest_sha256': sha256(previous / 'manifest.json'),
                'caption_source_sha256': sha256(previous / 'captions.zh.srt'),
                'caption_ass_sha256': sha256(assets / 'captions.zh.ass'),
                'caption_serialization': 'v2.serialize_ass_captions; ten ASS event fields including Effect; SRT text unchanged',
                'recording': '06-route and 07-source: continuous real browser recordings at original speed; eight other scenes reused unchanged from V3',
                'new_model_run': False, 'no_speed_change': True,
                'browser_recording_review': 'pending review of this newly composed video',
                'evidence_files': references + ['previous.manifest.json'],
                'editorial_notes': prior.get('editorial_notes', []) + [
                    'Two browser recordings use real input-event-driven cursor highlights; no claim of human operation.',
                    'Entire recorded viewport is preserved; only uniform display scaling and excess tail trimming.',
                    'Existing HTML and checks remain the original evidence, not a fresh model run or semantic certificate.',
                ]}
    (assets / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    player = player_template.replace('__DEMO_MANIFEST_JSON__', json.dumps(manifest, ensure_ascii=False).replace('<', r'\u003c'))
    for name in ('player.html', 'index.html'):
        (assets / name).write_text(player, encoding='utf-8')
    (assets / 'SHA256SUMS.txt').write_text(f'{manifest["sha256"]}  {OUTPUT}\n', encoding='utf-8')
    print(json.dumps({'video': str(final), 'player': str(assets / 'player.html'),
                      'seconds': final_info['seconds'], 'sha256': manifest['sha256'],
                      'review': 'Composition finished; watch the actual result before claiming visual approval.'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
