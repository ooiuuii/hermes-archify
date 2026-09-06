"""Compose an honest narrated walkthrough from real browser captures (no upload)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 30
BG, PANEL, INK, MUTED = '#0c141c', '#172530', '#f3f1e8', '#adbac6'
MINT, CORAL, LINE = '#b5e3cd', '#ffa18e', '#334550'
EXPECTED_HTML = '83c0782061b045c7c0d3b470a6b9e9aed753e9c8dbb53a0f920295e232c02f18'


def run(*args: str):
    subprocess.run(list(args), check=True)


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialize_ass_captions(events):
    """Serialize ASS-timestamped captions; Text is the final, comma-safe field."""
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Microsoft YaHei,31,&H00E8F1F3,&H000000FF,&H001C140C,&H001C140C,0,0,0,0,100,100,0,0,1,0,0,2,78,78,83,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    dialogue = []
    for start, end, content in events:
        ass_text = content.replace('\n', r'\N')
        dialogue.append(f'Dialogue: 0,{start},{end},Default,,0,0,0,,{ass_text}')
    return header + '\n'.join(dialogue) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--storyboard', type=Path, default=ROOT / 'storyboard.json')
    args = parser.parse_args()
    assets = args.assets.resolve()
    story = json.loads(args.storyboard.read_text(encoding='utf-8'))
    output_name = story.get('output_name', 'hermes-archify-workflow-v2.zh.mp4')
    if Path(output_name).name != output_name or not output_name.endswith('.mp4'):
        raise SystemExit('output_name must be an MP4 basename.')
    final = assets / output_name
    if final.exists():
        raise SystemExit('Final video already exists; use a fresh output directory.')
    frames = assets / 'frames'
    frames.mkdir(exist_ok=True)
    receipt = json.loads(args.receipt.read_text(encoding='utf-8-sig'))
    record = receipt.get('receipt', receipt)
    digest = checksum(assets / 'hermes.architecture.html')
    if digest != EXPECTED_HTML or record['artifact']['sha256'] != digest:
        raise SystemExit('Recorded HTML does not match the verified demonstration artifact.')
    validation, evidence = record['validation'], record['evidence']
    if not (record['ok'] and validation['checksPassed'] == validation['checkCount'] == 9
            and validation['errors'] == validation['warnings'] == 0
            and evidence['references'] == 34):
        raise SystemExit('The receipt no longer supports this edit; revise the storyboard.')
    public = {'artifact_sha256': digest, 'validation': validation,
              'evidence': evidence, 'generation_browser_check': receipt.get('browser_check'),
              'boundary': 'Authored model, not runtime topology proof. Saved execution, not a new run.'}
    (assets / 'receipt.public.json').write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding='utf-8')
    fonts = {}
    contrast = None
    if story.get('layout') == 'contrast':
        module_spec = importlib.util.spec_from_file_location('contrast_layout', ROOT.parent / 'v3' / 'layout.py')
        contrast = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(contrast)

    def font(size):
        if size not in fonts:
            fonts[size] = ImageFont.truetype(str(args.font), size)
        return fonts[size]

    def wrap(text, size, width):
        lines, current = [], ''
        for char in text:
            if char == '\n' or font(size).getlength(current + char) > width:
                lines.append(current)
                current = '' if char == '\n' else char
            else:
                current += char
        if current:
            lines.append(current)
        return lines

    def text(d, pos, value, size=30, color=INK, width=None, leading=1.45):
        x, y = pos
        lines = wrap(value, size, width) if width else value.split('\n')
        for line in lines:
            d.text((x, y), line, font=font(size), fill=color)
            y += round(size * leading)
        return y

    def box(d, bounds, fill=PANEL, outline=LINE):
        d.rounded_rectangle(bounds, radius=22, fill=fill, outline=outline, width=2)

    def capture(im, name, bounds, crop=None):
        source = Image.open(assets / 'captures' / name).convert('RGB')
        if crop:
            source = source.crop(crop)
        x, y, right, bottom = bounds
        fitted = ImageOps.contain(source, (right - x, bottom - y), Image.Resampling.LANCZOS)
        im.paste(fitted, (x + (right - x - fitted.width) // 2, y + (bottom - y - fitted.height) // 2))

    def screen(im, name):
        source = Image.open(assets / 'captures' / name)
        # Crop only recorded pixels, retaining the selected graph / panel region.
        crop = (26, 80, source.width - 26, min(source.height, 910)) if source.height > 950 else None
        capture(im, name, (78, 229, 1222, 881), crop)

    def bullets(d, rows, x=1300, y=260, width=530):
        for number, title, explanation in rows:
            text(d, (x, y), number, 22, CORAL)
            y = text(d, (x, y + 40), title, 35, INK, width)
            y = text(d, (x, y + 10), explanation, 25, MUTED, width) + 35

    def base(scene, index):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 8), fill=MINT)
        text(d, (64, 35), 'HERMES  ×  ARCHIFY', 25, MINT)
        text(d, (1390, 38), 'WORKFLOW DEMO  /  V2', 21, MUTED)
        text(d, (64, 92), scene['title'], 46)
        text(d, (66, 157), scene['subtitle'], 24, MUTED)
        d.line((64, 930, 1856, 930), fill=LINE, width=2)
        text(d, (64, 1045), '独立社区扩展 · Archify 提供渲染与交互 · 本地合成语音', 19, MUTED)
        text(d, (1670, 1045), f'{index + 1:02d} / 10', 19, MINT)
        return im

    def compose(scene, index, step):
        if contrast is not None:
            return contrast.render(scene, index, step, assets=assets, font_path=args.font,
                                   receipt=record, scene_count=len(story['scenes']))
        im = base(scene, index)
        d = ImageDraw.Draw(im)
        kind = scene['kind']
        if kind == 'intro':
            text(d, (80, 285), '让架构图\n成为一份\n可以核查的解释。', 70, INK, 1030, 1.35)
            text(d, (84, 658), '具体问题  /  交互阅读  /  源码依据', 31, MINT)
            text(d, (84, 750), '不是“不再画错”。\n是让你更方便发现哪里可能画错。', 29, MUTED)
            box(d, (1190, 255, 1834, 850))
            bullets(d, [('01', '明确问题', '不要让一张图承担整个仓库。'),
                        ('02', '沿图探索', '章节、节点、路径与源码引用。'),
                        ('03', '检查后交付', '把机器检查与人的判断分开。')], 1240, 282, 545)
        elif kind == 'native':
            box(d, (64, 212, 1240, 898))
            screen(im, 'native-template.png')
            bullets(d, [('已有', 'HTML + SVG', '原生已能生成网页架构图。'),
                        ('轻量', '直接按模板编写', '不依赖额外渲染引擎；有设计规范。'),
                        ('边界', '模板要求无 JavaScript', '未内建本演示中的节点与路径交互。')])
        elif kind == 'question':
            box(d, (70, 235, 780, 796))
            text(d, (110, 276), '范围过宽', 27, CORAL)
            text(d, (110, 355), '“画出整个\nHermes 仓库。”', 49, INK, 610)
            text(d, (110, 590), '组件越堆越多，\n不一定解释清楚任何问题。', 30, MUTED)
            box(d, (830, 235, 1850, 796), outline=MINT)
            text(d, (875, 276), '一个具体问题', 27, MINT)
            text(d, (875, 346), '“一次请求如何从 CLI\n进入模型循环，\n再分派到工具？”', 45, INK, 900, 1.35)
            text(d, (875, 581), '8–12 个主要节点 · 关系依据源码\n不确定的标注 · 不扩展无关模块', 30, MINT, 890)
            text(d, (75, 835), '方法参考：Better Stack · 2026-09-04  |  这种问法同样改善原生出图。', 25, MUTED)
        elif kind == 'pipeline':
            columns = [('01  HERMES', '读源码\n编写 JSON', '作者负责组件、关系、依据和布局选择。'),
                       ('02  ARCHIFY', '校验\n诊断与修正', '插件调用固定版本引擎；修正由作者完成。'),
                       ('03  DELIVERY', '交互 HTML\n+ JSON + 回执', '生成后检查页面与关键箭头，再交付。')]
            for col, (eyebrow, heading, body) in enumerate(columns):
                x = 70 + col * 607
                box(d, (x, 265, x + 568, 757))
                text(d, (x + 34, 304), eyebrow, 26, MINT)
                text(d, (x + 34, 378), heading, 49)
                text(d, (x + 34, 585), body, 28, MUTED, 495)
            text(d, (82, 817), '我们的插件是调用桥梁，不是另一个自动理解仓库的模型。', 32, CORAL)
        elif kind == 'viewer':
            box(d, (64, 212, 1240, 898))
            name = scene['captures'][step]
            screen(im, name)
            if scene['id'] == '05-chapter':
                bullets(d, [('01', '先看主线', 'CLI → Agent → 模型循环'),
                            ('02', '再看工具接入', '工具分派、注册表与插件'),
                            ('说明', '真实产物，分步剪辑', '已生成并经额外核查修正；非现场模型运行。')])
            elif scene['id'] == '06-route':
                text(d, (1300, 242), f'{step + 1:02d} / 03  路径操作', 25, CORAL)
                rows = ['点击“路径”', '选择 Hermes CLI', '选择 hermes-archify']
                for j, row in enumerate(rows):
                    text(d, (1300, 305 + j * 64), row, 30, MINT if j == step else MUTED)
                text(d, (1300, 552), '6 个节点 / 5 次跳转', 36, MINT)
                text(d, (1300, 625), '结果来自图中的有向关系。\n不是实际调用日志，\n也不是运行时性能追踪。', 29, INK, 510)
            else:
                text(d, (1300, 245), '定位 → 聚焦 → 看依据', 29, MINT)
                if step == 2:
                    capture(im, name, (1290, 320, 1846, 703), (52, 259, 325, 420))
                    text(d, (1300, 739), '源码面板局部放大 · 原始截图', 21, MUTED)
                else:
                    bullets(d, [('01', '查找 tool_registry', '从一张图中快速定位关心的组件。'),
                                ('02', '打开源码引用', '版本、文件和行号可追溯。')], y=336)
                text(d, (1300, 813), '引用可定位 ≠ 解释一定正确', 27, CORAL)
            text(d, (88, 898), f'真实浏览器画面 · 局部取景 · 步骤 {step + 1}/3', 18, MUTED)
        elif kind == 'checks':
            box(d, (70, 242, 908, 840), outline=MINT)
            text(d, (110, 280), 'SAVED DELIVERY RECEIPT', 25, MINT)
            text(d, (110, 350), '9 / 9', 105, INK)
            text(d, (490, 407), '检查通过', 35, MINT)
            text(d, (115, 512), '0 错误 / 0 警告\n34 处源码引用可定位', 32, MUTED)
            text(d, (115, 665), 'HTML SHA-256', 23, MINT)
            text(d, (115, 710), digest[:32] + '\n' + digest[32:], 24, INK)
            text(d, (990, 296), '它没有证明：', 43, CORAL)
            bullets(d, [('01', '每条箭头都真实', '模型仍可能误解源码。'),
                        ('02', '页面视觉已通过检查', '浏览器检查与生成回执分开记录。'),
                        ('03', '图回答了你的问题', '需要人工回到问题本身核查。')], x=990, y=381, width=800)
        elif kind == 'choice':
            for x, label, title, detail, note, accent in [
                (70, '轻量说明', '原生 architecture-diagram', '静态 HTML + SVG\n遵循设计模板\n无需额外渲染引擎', '已有能力，不需要贬低。', CORAL),
                (980, '交互检查', 'Hermes × Archify', '章节、节点与路径探索\n固定版本源码引用\n结构化诊断与交付回执', '增加能力，也增加引擎安装步骤。', MINT)]:
                box(d, (x, 253, x + 866, 820), outline=accent)
                text(d, (x + 40, 295), label, 25, accent)
                text(d, (x + 40, 366), title, 35)
                text(d, (x + 40, 468), detail, 35, INK, 780, 1.7)
                text(d, (x + 40, 742), note, 26, MUTED)
        elif kind == 'outro':
            text(d, (84, 280), '明确问题 → 生成 → 检查 → 交付', 55, MINT)
            text(d, (84, 405), '更方便核查。\n不是保证永远画对。', 77, INK, 1700, 1.4)
            text(d, (89, 697), scene['url'], 39, MINT)
            text(d, (89, 785), '社区项目 · 非 Nous Research / Archify 官方产品\n本片演示已验证的本机候选版本；安装与发布状态以仓库为准。', 26, MUTED)
        return im

    segments, caption_entries, proof, total = [], [], [], 0.0
    for index, scene in enumerate(story['scenes']):
        audio = assets / 'audio' / (scene['id'] + '.wav')
        with wave.open(str(audio)) as wav:
            speech = wav.getnframes() / wav.getframerate()
        duration = math.ceil(max(scene['minimum_seconds'], speech + 1.2) * FPS) / FPS
        clips = len(scene.get('captures', [])) if scene['kind'] == 'viewer' else 1
        framefiles = []
        for step in range(clips):
            frame = frames / f'{scene["id"]}-{step:02d}.png'
            compose(scene, index, step).save(frame)
            framefiles.append(frame)
        # Captions are phrase-level reading cues, proportionally timed to measured speech.
        phrases = re.findall(r'[^。！？]+[。！？]?', scene['narration'])
        weights = [max(1, sum(0.5 if ord(c) < 128 else 1 for c in phrase)) for phrase in phrases]
        elapsed = 0.45
        for phrase, weight in zip(phrases, weights):
            end = elapsed + speech * weight / sum(weights)
            caption_entries.append((total + elapsed, total + end, phrase))
            elapsed = end
        concat = assets / (scene['id'] + '.ffconcat')
        # Keep the completed interaction on screen longer than its selection steps.
        fractions = [0.20, 0.24, 0.56] if clips == 3 else [1.0]
        listing = ['ffconcat version 1.0']
        for frame, fraction in zip(framefiles, fractions):
            relative = frame.relative_to(assets).as_posix()
            listing.extend([f"file '{relative}'", f'duration {duration * fraction:.8f}'])
        listing.append(f"file '{framefiles[-1].relative_to(assets).as_posix()}'")
        concat.write_text('\n'.join(listing) + '\n', encoding='utf-8')
        segment = assets / (scene['id'] + '.mp4')
        run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-safe', '0', '-f', 'concat',
            '-i', str(concat), '-i', str(audio), '-vf', f'fps={FPS}',
            '-af', 'adelay=450:all=1,apad', '-t', f'{duration:.8f}',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-pix_fmt', 'yuv420p',
            '-threads', '4', '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '1', str(segment))
        proof.append({'id': scene['id'], 'start': round(total, 4), 'duration': duration,
                      'title': scene['title'], 'lane': scene.get('lane'),
                      'speech_duration': speech, 'captures': scene.get('captures', []),
                      'frames': [x.name for x in framefiles]})
        total += duration
        segments.append(segment)
        print(f'{scene["id"]}: {duration:.2f}s ({speech:.2f}s narration)', flush=True)

    def stamp(seconds, ass=False):
        units = 100 if ass else 1000
        value = round(seconds * units)
        second, sub = divmod(value, units)
        minute, second = divmod(second, 60)
        hour, minute = divmod(minute, 60)
        return (f'{hour}:{minute:02d}:{second:02d}.{sub:02d}' if ass
                else f'{hour:02d}:{minute:02d}:{second:02d},{sub:03d}')

    srt, ass_events = [], []
    for number, (start, end, phrase) in enumerate(caption_entries, 1):
        lines = wrap(phrase, 31, 1760)
        if len(lines) > 2:
            raise SystemExit(f'Caption too tall: {phrase}')
        content = '\n'.join(lines)
        srt.append(f'{number}\n{stamp(start)} --> {stamp(end)}\n{content}\n')
        ass_events.append((stamp(start, True), stamp(end, True), content))
    (assets / 'captions.zh.srt').write_text('\n'.join(srt), encoding='utf-8')
    (assets / 'captions.zh.ass').write_text(serialize_ass_captions(ass_events), encoding='utf-8')
    edit_list = assets / 'edit.ffconcat'
    edit_list.write_text('ffconcat version 1.0\n' + ''.join(f"file '{p.name}'\n" for p in segments), encoding='utf-8')
    picture = assets / 'picture.mp4'
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-safe', '0', '-f', 'concat',
        '-i', str(edit_list), '-c', 'copy', str(picture))
    # Run inside assets so libass gets a simple relative filename on Windows.
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', 'picture.mp4',
                    '-vf', "ass=filename='captions.zh.ass'", '-c:v', 'libx264', '-preset', 'fast',
                    '-crf', '19', '-threads', '4', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                    '-movflags', '+faststart', final.name], cwd=assets, check=True)
    capture_hashes = {p.name: checksum(p) for p in sorted((assets / 'captures').glob('*.png'))}
    report = {'video': final.name, 'sha256': checksum(final), 'seconds': total,
              'dimensions': [W, H], 'fps': FPS, 'scenes': proof, 'capture_sha256': capture_hashes,
              'artifact_sha256': digest, 'narration': 'Local Windows System.Speech; synthetic voice',
              'caption_timing': 'Phrase reading cues proportional to measured narration; not word alignment',
              'recording': 'Real browser states, step-edited with still holds; no new model session',
              'native_baseline': 'Official bundled template preview, not same-prompt A/B experiment',
              'editorial_notes': story.get('editorial_notes', [])}
    (assets / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    contact = Image.new('RGB', (960, 5 * 285), BG)
    for index, item in enumerate(proof):
        frame = Image.open(frames / item['frames'][-1])
        contact.paste(frame.resize((480, 270)), ((index % 2) * 480, (index // 2) * 285))
    contact.save(assets / 'contact-sheet.jpg', quality=90)
    (assets / 'SHA256SUMS.txt').write_text(f'{checksum(final)}  {final.name}\n', encoding='utf-8')
    print(json.dumps({'video': str(final), 'seconds': total, 'sha256': checksum(final)}, indent=2))


if __name__ == '__main__':
    main()
