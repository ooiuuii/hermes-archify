请真实使用 Hermes 自带的 architecture-diagram 技能生成一张 Hermes 架构图。
先通过 skill_view 完整阅读 architecture-diagram 的 SKILL.md 和 templates/template.html，
然后读取本机 Hermes 源码，按照技能的原生 HTML + inline SVG 工作流创作，不调用 Archify。

问题：一次请求如何从 Hermes CLI 进入 Agent/模型循环，再被分派到工具？
范围包括 CLI、Agent 运行时、模型循环、模型调用、工具选择/注册/分派、文件/Skill/终端工具、
插件管理器，以及 hermes-archify 作为插件接入工具注册表。保持约 8–12 个主要组件。
画的是高层源码解释，不是运行时追踪，不需要画完整仓库所有子系统。

只读源码：<HERMES_SOURCE>
监督者已核对该工作树干净，Git revision 为 126ff7071b6b755055879648f4e859b3187d0fac。
可从 cli.py、run_agent.py、agent/、tools/registry.py、tools/、hermes_cli/plugins.py
和 toolsets.py 中有针对性地查找。独立插件源码可只读 <PLUGIN_ROOT> 下的
__init__.py、plugin.yaml、bridge.py、README.md，按实际找到的文件为准。
不要读取已有图、之前的运行产物或 Archify 生成的 JSON/HTML，不要复制之前的图来改格式。

请生成真实可读、布局清楚的结果，不要为了比较故意省略技能已有的能力或制造错误。
遵守原技能的单文件 HTML、内联 SVG/CSS、无 JavaScript 要求；可以按你的判断组织
标题、图、摘要卡和必要的源码依据。不确定的关系应标注，不要凭空添加依赖。
正常完成一轮生成与自己的源码/文件复查即可，不要为了“完美”反复扩大范围。

只可写入当前工作目录：
- hermes-native.architecture.html：技能生成的真实成品，不是官方空白模板。
- source-notes.md：实际读到的文件/行号、范围和未核实部分，说明这是源码解释。

源码、技能原件、插件和所有日常配置是只读；不要读秘密、环境或认证；不要安装东西、
发布、联网找图、发消息、调用其他代理。浏览器由监督者随后检查；你没有检查时不要
声称浏览器验收通过。最后用中文报告两个文件的路径和你实际做过的检查。
