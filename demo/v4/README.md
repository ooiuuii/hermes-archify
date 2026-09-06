# V4：两段连续浏览器操作

V4 只替换 V3 的 `06-route` 和 `07-source`：使用真实浏览器连续录制，配用原旁白，保持原速和原场景时长。其余八个无字幕场景 MP4 复用 V3，再统一烧录修正后的 ASS 字幕。旧版产物不改写。

这不是新的模型生成会话，也不宣称由人手动操作。鼠标指示和点击高亮由实际输入事件驱动。原生素材仍是官方模板预览，不是同题 A/B 生成实验。

## 连续采集

`record-live.mjs` 只能在已获授权的浏览器会话中调用，传入现有 tab 和该 tab 的 CDP capability；它不另起浏览器，也不绕过浏览器工具。`cursor-overlay.js` 是临时的录屏辅助层，显示真实 pointermove / pointerdown 事件。录完刷新页面移除，不写入交互 HTML 文件。

录制输出逐帧 JPEG、浏览器时间戳、真实输入事件和 `frames.ffconcat`。使用实际帧间时间编码，未变化的页面保留浏览器最后一帧至下一次画面更新；不是从几张关键截图伪造操作。正式录制前应通过当前 DOM 核对每个控件，不能照搬旧坐标。Archify 有带相同标签的隐藏测量控件，定位器只接受完全可见的元素。

编码例子（`<take>` 替换为正式录制目录，输出路径不得已有文件）：

```powershell
ffmpeg -hide_banner -loglevel error -n -safe 0 -f concat -i '<take>/frames.ffconcat' -vf 'fps=30,pad=ceil(iw/2)*2:ceil(ih/2)*2' -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -threads 2 -an -movflags +faststart 'recordings/06-route.mp4'
```

将同一次录制的 `capture.json` 复制为输出 MP4 的同名 JSON。不要把试录或超时中断的采集当作成片证据。两段正式实录分别覆盖路径选择/路径旅程和节点搜索/来源查看；不打开外部网站，不触发新的模型会话。

## 合成

在仓库根目录运行；需要 Python、构建脚本所需的 Pillow、可执行的 `ffmpeg` / `ffprobe`，以及可用于中文字幕的字体。FFmpeg 需要支持 ASS 字幕滤镜。

```powershell
python demo/v4/compose.py --previous E:/hermes-archify/artifacts/demo-v3 --assets E:/hermes-archify/artifacts/demo-v4
```

可选 `--font <CJK-font-path>` 指定字体文件。合成不会重新录制浏览器，也不会调用模型。

运行前准备：

- `--previous` 指向完整 V3 产物目录：原 `manifest.json`、带原旁白的无字幕场景 MP4、字幕、已验证图、模板、回执、`frames/` 和 `captures/`。替换段直接复用原场景 MP4 的音轨，不重新合成语音。
- `--assets` 是独立的 V4 目录，已有 `recordings/06-route.mp4`、`recordings/06-route.json`、`recordings/07-source.mp4`、`recordings/07-source.json`；不得与 V3 目录重合。
- 原始录制至少覆盖原场景全长：路径约 **22.1333 秒**，来源约 **19.3667 秒**。以 V3 manifest 的完整精度时长及 `ffprobe` 实测为准，不按显示值向下取整。录制视口为 1146 × 856，实际编码尺寸以 `ffprobe` 为准。
- 录制过短时拒绝合成，不定格尾帧凑时长、不改变速度。最终场景时长保留 V3 manifest 的值；原片多余部分可裁去。
- 目标最终视频已存在时拒绝覆盖；改用新的 V4 产物目录。不要删除或覆盖旧版来绕过检查。

## 查看与核查

完成后直接打开产物目录中的 `player.html`（`index.html` 是同内容别名）。清单数据由合成脚本嵌入页面，因此本地文件模式也能显示章节；按钮只跳转，不自动开始播放。播放器不使用远程库，也兼容已有的 `demo/v2/serve_preview.py` 本地预览工具。

主要产物：

- `hermes-archify-continuous-demo-v4.zh.mp4`：带中文烧录字幕的成片。
- `player.html` / `index.html`、`manifest.json`、`captions.zh.srt`、`captions.zh.ass`：播放器、制作记录及字幕。
- `recordings/06-route.*`、`recordings/07-source.*`：原始连续录制及其记录。
- `hermes.architecture.html`、`native-template.html`、`receipt.public.json`、`captures/`：随包参考；若 V3 有 `rejection.public.json`，也复制保留。

交付前检查完整解码、声音、字幕前缀、两段连续动作和章节跳转；对照 manifest 检查时长及哈希。两个新场景不能用旧静帧检查结果代替验收。

## 证据边界

图中路径不等于运行时调用追踪；校验和引用范围检查不保证架构语义真实。交互阅读器与校验来自 Archify，独立插件负责连接 Hermes。缺失节点案例是有意损坏副本后的结构检查，不是原生生成故障。

其余八段保留 V3 的说明画面与真实静帧素材，旁白仍为本地合成语音。原生与插件的对照只说明所展示工作流及阅读能力，不宣称质量、速度或成本胜出。不修改产品或生产设置，不自动上传，也不代表新版本发布。参考 HTML 自身可能加载外部字体；不能将本地播放器描述为所有参考页面都绝不联网。
