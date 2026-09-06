"""High-contrast A/B editorial layout; screenshots remain real recorded pixels."""
from functools import lru_cache
import json

from PIL import Image, ImageDraw, ImageFont, ImageOps

BG, INK, MUTED = '#0b1118', '#f6f2e9', '#abb6c3'
A, B = '#ffac80', '#91edc4'
AP, BP, LINE = '#281e1b', '#112b27', '#34414e'


@lru_cache(maxsize=24)
def get_font(path, size):
    return ImageFont.truetype(path, size)


def render(scene, index, step, *, assets, font_path, receipt, scene_count):
    im = Image.new('RGB', (1920, 1080), BG)
    d = ImageDraw.Draw(im)

    def text(x, y, value, size=32, color=INK, width=1770, leading=1.4):
        font = get_font(str(font_path), size)
        lines, line = [], ''
        for c in value:
            if c == '\n' or font.getlength(line + c) > width:
                lines.append(line)
                line = '' if c == '\n' else c
            else:
                line += c
        if line:
            lines.append(line)
        for line in lines:
            d.text((x, y), line, font=font, fill=color)
            y += round(size * leading)
        return y

    def box(bounds, color=LINE, fill='#15202a', radius=18):
        d.rounded_rectangle(bounds, radius=radius, fill=fill, outline=color, width=2)

    def shot(name, bounds, crop=None):
        source = Image.open(assets / 'captures' / name).convert('RGB')
        if crop:
            source = source.crop(crop)
        x, y, right, bottom = bounds
        fitted = ImageOps.contain(source, (right-x, bottom-y), Image.Resampling.LANCZOS)
        im.paste(fitted, (x+(right-x-fitted.width)//2, y+(bottom-y-fitted.height)//2))

    def rail(x, labels, color, y=300, width=770):
        for n, (title, body) in enumerate(labels, 1):
            text(x, y, f'{n:02d}', 23, color)
            y = text(x+65, y-3, title, 34, INK, width-65)
            y = text(x+65, y+10, body, 25, MUTED, width-65) + 38

    lane = scene['lane']
    text(64, 20, 'HERMES ARCHITECTURE  /  A vs B', 23, MUTED)
    text(1520, 20, '对照演示 · V3', 23, MUTED)
    for key, x, label, color, fill in [
        ('a', 64, 'A  原生：直接写 HTML / SVG', A, AP),
        ('b', 981, 'B  插件：JSON → 校验 → 交互 HTML', B, BP)]:
        active = lane in (key, 'both')
        box((x, 67, x+875, 153), color if active else LINE, fill if active else '#111923')
        text(x+23, 87, label, 31, color if active else MUTED, 830)
    text(66, 178, scene['title'], 44)
    d.line((64, 930, 1856, 930), fill=LINE, width=2)
    text(64, 1042, '独立社区插件 · 交互与校验来自 Archify · 中文合成解说', 19, MUTED)
    text(1620, 1042, f'{index+1:02d} / {scene_count:02d}', 19, MUTED)
    kind = scene['kind']

    if kind == 'contrast-hook':
        box((64, 270, 1035, 850), A, AP)
        text(100, 300, '“帮我画整个仓库。”', 42, A)
        # Deliberately editorial, generic module labels; never presented as Hermes output.
        positions = [(170+(n%4)*216, 443+(n//4)*117) for n in range(12)]
        for i, j in [(0,7),(0,5),(1,8),(2,9),(3,4),(3,10),(4,11),(5,6),(6,9),(7,8),(1,10),(2,11)]:
            d.line((positions[i][0],positions[i][1],positions[j][0],positions[j][1]), fill='#8c6455', width=3)
        for n,(x,y) in enumerate(positions):
            box((x-61,y-24,x+61,y+24), '#a77761', '#3a2922', 9)
            text(x-37,y-16,f'模块 {n+1}',20,A,100)
        text(100, 787, '失败模式示意 · 不是一次真实 Hermes 输出', 24, MUTED)
        text(1110, 317, '看着专业。', 55, INK)
        text(1110, 420, '但请求怎么走？\n这些框有依据吗？', 47, INK, 710, 1.55)
        text(1110, 650, '回答不了问题，\n再漂亮也是“垃圾图”。', 46, A, 710)
        text(70, 882, '批评的是无用的结果，不是说原生方案必然失败。', 24, MUTED)
    elif kind == 'native-flow':
        for x, heading, detail in [(70,'需求','你描述系统或问题'),(682,'Hermes 直接写页面','HTML + inline SVG'),(1294,'打开成品','你自己阅读和核查')]:
            box((x, 278, x+550, 493), A, AP)
            text(x+30, 310, heading, 40, A, 490)
            text(x+30, 402, detail, 28, INK, 490)
        for x in (627, 1239):
            text(x, 350, '→', 42, A)
        shot('native-template.png', (82, 535, 940, 870))
        text(1030, 546, '到这里，原生出图完成。', 43, A, 790)
        text(1030, 642, '有视觉规范，也能生成网页。\n但没有内建本片中的路径控制、\n来源面板和独立校验回执。', 31, INK, 790, 1.65)
        text(90, 882, '左下为原生官方模板预览 · 不是同题生成实验', 22, MUTED)
    elif kind == 'problem':
        cards = [('01','范围失焦','“画整个仓库”','模块全塞进来，\n问题反而看不清。'),
                 ('02','读图费劲','眼睛追线，脑内记分支','起点在哪？终点在哪？\n你自己沿线找答案。'),
                 ('03','检查没落实','有模板规范，不等于执行了检查','模型理解、内容与页面混在一起。\n页面存在，不等于判断已核实。')]
        for col,(n,title,sub,detail) in enumerate(cards):
            x=70+col*604
            box((x,283,x+565,824),A,AP)
            text(x+32,320,n,27,A)
            text(x+32,391,title,49,INK)
            text(x+32,500,sub,28,A,496)
            text(x+32,619,detail,28,MUTED,496,1.65)
        text(75,874,'HTML / SVG 不是问题。把“生成了”当作“解释清楚了”，才是问题。',30,A)
    elif kind == 'switch':
        text(100,280,'Hermes 没有换。出图流程换了。',57,B)
        rows=[('01','Hermes','先写结构化 JSON'),('02','Archify','校验，返回诊断'),('03','Hermes','按诊断修正 JSON'),('04','Archify','交付 HTML + 回执')]
        for n,(number,title,body) in enumerate(rows):
            x=70+n*453
            box((x,415,x+416,751),B,BP)
            text(x+28,447,number,24,B)
            text(x+28,507,title,42,INK)
            text(x+28,622,body,29,B,362)
        text(95,809,'B 多了可执行检查，也多了现成的图关系交互。',36,B)
        text(98,875,'插件负责连接；不是另一个自动理解仓库的模型。',25,MUTED)
    elif kind == 'question':
        box((73,280,1847,505),LINE)
        text(111,309,'“一次请求怎样从 CLI 进入模型循环，再到工具？”',43,INK,1680)
        text(115,407,'最多 12 个主要节点 · 关系依据源码 · 不扩展无关模块',31,B)
        box((73,549,928,832),A,AP)
        box((975,549,1847,832),B,BP)
        text(116,588,'A  得到静态成品',43,A)
        text(116,680,'你手动沿线读、翻代码核查。',31,INK,760)
        text(1017,588,'B  得到可交互的成品',43,B)
        text(1017,680,'选路径、查节点、看来源与回执。',31,INK,760)
        text(77,875,'好问题两边都需要。这里比较工作流和能力，不是同题生成质量跑分。',25,MUTED)
    elif kind == 'viewer':
        box((65,267,708,899),A,AP)
        box((740,267,1854,899),B,BP)
        is_route=scene['id']=='06-route'
        text(103,304,'A  原生默认流程',31,A)
        text(773,279,'B  真实产物操作',27,B)
        name=scene['captures'][step]
        if is_route:
            rail(98,[('自己找到起点','从整张图中定位入口。'),('一条条沿线读','自己区分分支和方向。'),('再找到终点','把沿途节点记在脑中。')],A,386,550)
            source=Image.open(assets/'captures'/name)
            crop=(26,157,source.width-26,855) if source.height>1000 else None
            shot(name,(762,329,1833,838),crop)
            text(782,852,['步骤 1：进入路径模式','步骤 2：选择 Hermes CLI','步骤 3：6 节点 / 5 跳，路径单独高亮'][step],25,B)
        else:
            rail(98,[('先看框和说明','默认模板没有右侧这样的来源面板。'),('另外找代码','自行定位文件、版本和行号。'),('再回来核对','判断图中解释是否有依据。')],A,377,550)
            if step==2:
                shot(name,(762,331,1178,840),(26,155,1107,865))
                shot(name,(1210,365,1825,757),(52,259,325,420))
                text(1215,790,'实际来源面板 · 局部放大',22,MUTED,600)
            else:
                shot(name,(763,331,1830,840))
            text(781,852,['步骤 1：查找节点','步骤 2：搜索 tool_registry','步骤 3：固定版本 + 文件 + 行号'][step],25,B)
        text(78,907,'A 为流程说明；B 为真实浏览器画面分步剪辑。路径不是运行时追踪，引用不是语义认证。',18,MUTED)
    elif kind == 'rejection':
        proof=json.loads((assets/'rejection.public.json').read_text(encoding='utf-8'))
        if proof['ok'] is not False or proof['exit_code']!=1 or 'demo_missing_node' not in proof['error']:
            raise ValueError('Missing real structural rejection proof.')
        box((68,272,710,855),A,AP)
        text(105,309,'A  直接生成页面',36,A)
        text(108,405,'模板会约定：\n间距、图例、颜色……',34,INK,546,1.65)
        text(108,585,'但默认技能没有\n独立的结构校验器\n和诊断回执。',33,MUTED,546,1.65)
        box((745,272,1850,855),B,BP)
        text(786,310,'B  故意破坏一条连线，再运行真实校验',31,B,1020)
        box((786,388,1810,531),A,'#18222b')
        text(810,413,'"from": "cli"\n"to": "demo_missing_node"',30,INK,960)
        text(789,566,'校验拒绝 · exit code 1',38,A)
        text(792,634,'Connection "run_conversation" references\nunknown target "demo_missing_node".',29,INK,970)
        text(790,757,f'正常交付另有回执：{receipt["validation"]["checksPassed"]}/9 通过 · 34 处源码引用',29,B,1010)
        text(74,878,'有意损坏副本的结构测试；不是原生真实故障，也不证明架构语义正确。',24,MUTED)
    elif kind == 'recap':
        for x,color,fill,title,rows in [
            (70,A,AP,'A  模型直接出页面',[('输入','需求 → Hermes'),('生成','直接写 HTML / SVG'),('阅读','你沿线读，另外核查')]),
            (980,B,BP,'B  结构化检查后交付',[('输入','需求 → Hermes 写 JSON'),('生成','Archify 校验 → Hermes 修正 → 引擎交付'),('阅读','选路径、看来源、查诊断')])]:
            box((x,277,x+863,856),color,fill)
            text(x+35,318,title,42,color)
            rail(x+34,rows,color,415,790)
        text(80,880,'同样可以是 HTML。差别在中间检查步骤，以及交付后你能怎么读它。',29,INK)
    elif kind == 'close':
        text(85,302,'不是让模型“突然更懂架构”。',58,INK)
        text(85,418,'是让你更容易检查它。',74,B)
        text(91,575,'静态说明：A 仍然够用。\n交互讲解、路径探索、源码核查：B 增加了现成工具。',35,INK,1730,1.7)
        text(92,750,'github.com/ooiuuii/hermes-archify',37,B)
        text(94,827,'两种方案都可能理解错代码。校验不能替代关键关系审查。',29,A)
        text(95,883,'社区项目，非官方产品 · 演示为已验证本机候选版本 · 安装与发布状态以仓库为准',21,MUTED)
    return im
