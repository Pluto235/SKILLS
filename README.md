# 天文课题组 Codex Skills 工具包

这个仓库整理了一组适合课题组共享的 Codex skills，用于天文文献检索、PDF 转 LLM 可读 Markdown、静态报告生成、HTML 批注、组会网页 PPT、项目日志和研究计划讨论。

仓库只包含可分享的 skills 和说明文档，不包含个人 API token、Codex 会话记录、插件缓存、模型配置、SSH 配置或本机路径历史。

## 从 GitHub 安装

推荐让每个人克隆这个发布分支，而不是克隆仓库默认分支：

```bash
git clone --branch publish/lab-codex-skills-cn --single-branch \
  git@github.com:Pluto235/SKILLS.git \
  ~/Documents/astro-codex-skills

cd ~/Documents/astro-codex-skills
bash install.sh
```

如果没有配置 GitHub SSH key，可以用 HTTPS：

```bash
git clone --branch publish/lab-codex-skills-cn --single-branch \
  https://github.com/Pluto235/SKILLS.git \
  ~/Documents/astro-codex-skills

cd ~/Documents/astro-codex-skills
bash install.sh
```

也可以直接把下面这段话发给 Codex：

```text
请克隆 https://github.com/Pluto235/SKILLS.git 的 publish/lab-codex-skills-cn 分支到 ~/Documents/astro-codex-skills，先运行 bash install.sh --dry-run 给我看会安装哪些 skills；如果没问题，再运行 bash install.sh 安装到 ~/.codex/skills，并提醒我重启 Codex。
```

日常安装建议直接拉取这个分支；需要固定版本时，可以使用仓库 tag，例如 `v2026.06.11`。

## 本地安装

克隆仓库后，在仓库根目录运行：

```bash
bash install.sh
```

默认安装 `skills/` 下的核心 skills 到：

```text
~/.codex/skills/
```

安装可选包：

```bash
bash install.sh --with-pua
bash install.sh --all
```

安装后重启 Codex，让新 skills 被加载。

## 核心 Skills

| Skill | 用途 | 典型场景 |
| --- | --- | --- |
| `nasa-ads-literature` | NASA ADS / arXiv 天文文献检索 | 查 ADS、查 arXiv、导出 BibTeX、下载开放 PDF |
| `mineru-pdf-to-md` | 用 MinerU 把 PDF 转为 LLM 可读 Markdown | 论文总结、翻译、精读、从 PDF 抽取正文/图片/表格 |
| `local-html-annotations` | 给本地 HTML 报告添加离线批注功能 | 批阅报告、选中文本加评论、导出/导入批注 JSON |
| `notion-html-report` | 把 Markdown / 研究记录渲染成 Notion 风格静态 HTML | 科研复现报告、pipeline 报告、实验总结 |
| `guizang-ppt-skill` | 生成横向翻页网页 PPT | 组会、开题、分享、发布会风格演示 |
| `devlog` | 维护项目 `devlog.md` 修改日志 | 记录代码改动、实验进展、项目历史 |
| `grill-me` | 对研究计划或设计进行连续追问 | 开题前、proposal 前、方案不清楚时做压力测试 |

## 可选 Skills

### `optional/pua-debugging`

这是一组强语气的调试/防摆烂提示词 skills，包括 `pua`、`pua-en`、`pua-ja` 和若干 alias。它们用于 agent 卡住、反复失败、过早放弃时，强制 agent 做更彻底的排查。

这组包语气刻意激烈，不建议作为课题组默认安装。适合个人选择性安装。

安装：

```bash
bash install.sh --with-pua
```

## 推荐插件

这些 Codex 插件不是本仓库内容，不要把 `~/.codex/plugins/cache` 提交到 GitHub。它们是可选增强项，是否可用取决于个人 Codex 环境。

| 插件 | 推荐用途 | 说明 |
| --- | --- | --- |
| Browser | HTML 报告、批注 UI、网页 PPT | 打开本地 HTML、点击测试、截图验证 |
| ECC | 文献综述、网页检索、工程质量 | 提供 200+ 个研究、工程、前端、测试、安全、自动化 skills 和 MCP 工具配置 |
| Presentations | 正式 slides / PPTX | 生成和检查演示文稿 |
| Documents | 文稿、DOCX、报告 | 处理文档类材料 |
| Spreadsheets | 文献矩阵、观测记录、表格分析 | 处理表格和 xlsx |

### ECC

ECC 是一个大型 Codex / Claude Code skill bundle 和插件包，官方仓库是：

- GitHub: <https://github.com/affaan-m/ECC>
- Website: <https://ecc.tools>

它不属于本仓库内容，本仓库也不会提交 ECC 插件缓存。建议把 ECC 当作“可选增强层”：本仓库提供课题组常用的、稳定的本地 skills；ECC 提供更广的通用工作流、MCP 工具和工程能力。

ECC 插件一般包括：

- **Research / literature**：`deep-research`、`literature-review`、`research-ops`、`scholar-evaluation`、`gget`、`pubmed-database`
- **Web / retrieval**：`exa-search`、`documentation-lookup`、`search-first`、`iterative-retrieval`
- **Frontend / design**：`frontend-design-direction`、`make-interfaces-feel-better`、`frontend-patterns`、`frontend-a11y`、`design-system`
- **Engineering workflow**：`tdd-workflow`、`verification-loop`、`codebase-onboarding`、`git-workflow`、`github-ops`
- **Security / quality**：`security-review`、`security-scan`、`safety-guard`、`production-audit`
- **Architecture / planning**：`architecture-decision-records`、`api-design`、`backend-patterns`、`agentic-engineering`
- **Language / framework patterns**：Python、FastAPI、Django、React/Next/Vite、Go、Rust、Java、Spring Boot、Laravel、Flutter、Kotlin、Swift 等

ECC 还会随插件提供一组 MCP server 配置，常见包括：

| MCP server | 用途 |
| --- | --- |
| `exa` | 语义网页搜索和内容抓取 |
| `context7` | 查询最新库文档和代码示例 |
| `github` | GitHub 仓库、issue、PR、文件操作 |
| `playwright` | 浏览器自动化、网页截图和 E2E 验证 |
| `memory` | 跨会话记忆 |
| `sequential-thinking` | 分步推理辅助 |

Codex 插件安装方式会随 Codex 插件系统变化。ECC 当前文档给出的 repo marketplace 安装方式是：

```bash
codex plugin marketplace add affaan-m/ECC
```

也可以使用本地 checkout：

```bash
git clone https://github.com/affaan-m/ECC.git ~/Documents/ECC
codex plugin marketplace add ~/Documents/ECC
```

安装或更新后重启 Codex，再在 Codex 插件目录里启用 `ecc`。如果 Codex 的插件系统版本不同，以 ECC 仓库 README 和 `.codex-plugin/README.md` 为准。

适合课题组的调用例子：

```text
用 deep-research 和 literature-review 帮我围绕 blazar QPO 做一轮文献调研，列出证据链和争议点。
```

```text
用 exa-search 查最近一年的 Fermi-LAT blazar QPO 相关网页和论文线索，并给出来源链接。
```

```text
用 frontend-design-direction 和 make-interfaces-feel-better 把这个科研报告 HTML 打磨成更适合组会展示的界面。
```

```text
用 tdd-workflow 和 verification-loop 修改这个 Python 分析脚本，先补测试，再实现功能并验证结果。
```

### Superpowers

Superpowers 不是本仓库打包的 skill，而是推荐单独安装的 Codex skill bundle。它提供头脑风暴、写计划、执行计划、系统调试、TDD、代码 review、开发分支收尾等工作流。

安装方式：

```bash
git clone https://github.com/smallocean43658/codex-superpowers.git ~/.codex/superpowers
mkdir -p ~/.agents/skills
ln -s ~/.codex/superpowers/skills ~/.agents/skills/superpowers
```

安装后重启 Codex。常用 skills：

| Skill | 用途 |
| --- | --- |
| `superpowers:brainstorming` | 需求和方案头脑风暴 |
| `superpowers:writing-plans` | 把复杂任务写成可执行计划 |
| `superpowers:executing-plans` | 按计划逐步执行 |
| `superpowers:systematic-debugging` | 系统化排查 bug |
| `superpowers:test-driven-development` | TDD 工作流 |
| `superpowers:verification-before-completion` | 完成前验证 |

### 前端与视觉设计

如果课题组经常做网页报告、演示页面、可交互图表或小工具，推荐启用 ECC 插件里的前端设计相关 skills。它们不是本仓库内容，但能明显提升 `notion-html-report`、`local-html-annotations`、`guizang-ppt-skill` 和自定义网页工具的质量。

常用设计相关 skills：

| Skill | 用途 |
| --- | --- |
| `frontend-design-direction` | 为网站、dashboard、工具页面确定产品化设计方向 |
| `make-interfaces-feel-better` | 打磨间距、字体、边框、阴影、交互状态等细节 |
| `frontend-patterns` | React / Next.js 组件、状态、性能和 UI 工程模式 |
| `frontend-a11y` | 表单、键盘导航、ARIA、屏幕阅读器等可访问性 |
| `design-system` | 生成或审计颜色、字体、间距、圆角、组件规范 |
| `frontend-slides` | 制作前端驱动的网页 slides |
| `motion-ui` / `motion-patterns` | 页面和组件动效 |

可以这样让 Codex 使用：

```text
用 frontend-design-direction 和 make-interfaces-feel-better 帮我把这个 HTML 报告界面打磨得更像科研工具，而不是普通模板。
```

```text
用 frontend-a11y 检查这个批注 UI 的键盘操作和表单标签。
```

## NASA ADS 配置

`nasa-ads-literature` 查询 ADS 时需要每个人使用自己的 ADS API token。不要共享 token，不要把 token 提交到 GitHub。

推荐配置方式：

```bash
mkdir -p ~/.ads
chmod 700 ~/.ads
printf '%s\n' '你的_ADS_API_TOKEN' > ~/.ads/dev_key
chmod 600 ~/.ads/dev_key
```

也可以用环境变量：

```bash
export ADS_DEV_KEY="你的_ADS_API_TOKEN"
```

arXiv 查询不需要 API key。

## MinerU 配置

`mineru-pdf-to-md` 需要每个人本机先能运行 `mineru` 命令。本仓库只分发 Codex skill，不分发 MinerU、模型权重或模型缓存。

推荐用独立 Python 环境安装 MinerU：

```bash
python3 -m venv ~/.venvs/mineru
~/.venvs/mineru/bin/python -m pip install -U pip uv
~/.venvs/mineru/bin/uv pip install -U "mineru[all]"
```

如果在国内网络环境下安装较慢，可以自行配置 PyPI 镜像。安装后创建命令入口：

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/mineru <<'EOF'
#!/usr/bin/env bash
export MINERU_MODEL_SOURCE="${MINERU_MODEL_SOURCE:-modelscope}"
exec "$HOME/.venvs/mineru/bin/mineru" "$@"
EOF
chmod +x ~/.local/bin/mineru

cat > ~/.local/bin/mineru-models-download <<'EOF'
#!/usr/bin/env bash
export MINERU_MODEL_SOURCE="${MINERU_MODEL_SOURCE:-modelscope}"
exec "$HOME/.venvs/mineru/bin/mineru-models-download" "$@"
EOF
chmod +x ~/.local/bin/mineru-models-download
```

确认 `~/.local/bin` 在 `PATH` 里，然后下载 pipeline 模型：

```bash
mineru-models-download -s modelscope -m pipeline
```

如果系统没有 `mineru-models-download` 入口，可以直接运行：

```bash
MINERU_MODEL_SOURCE=modelscope ~/.venvs/mineru/bin/mineru-models-download -s modelscope -m pipeline
```

验证：

```bash
mineru -v
```

## 使用示例

### 查 ADS 文献

```bash
python3 ~/.codex/skills/nasa-ads-literature/scripts/ads_search.py \
  --query 'author:"Gaia Collaboration" year:2024' \
  --rows 10
```

导出 BibTeX：

```bash
python3 ~/.codex/skills/nasa-ads-literature/scripts/ads_search.py \
  --query 'cataclysmic variables year:2023' \
  --rows 5 \
  --format bibtex
```

### 查 arXiv

```bash
python3 ~/.codex/skills/nasa-ads-literature/scripts/arxiv_search.py \
  --query 'cat:astro-ph.GA AND all:"Gaia DR3"' \
  --rows 10
```

下载开放 arXiv PDF：

```bash
python3 ~/.codex/skills/nasa-ads-literature/scripts/fetch_open_pdf.py \
  --arxiv 2606.11165v1 \
  --output-dir ./papers
```

### 把 PDF 转成 LLM 可读 Markdown

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py \
  /absolute/path/to/paper.pdf
```

指定输出目录：

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py \
  /absolute/path/to/paper.pdf \
  --output-dir ./mineru-output
```

快速正文版，跳过公式和表格解析：

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py \
  /absolute/path/to/paper.pdf \
  --fast
```

扫描版或图片型 PDF：

```bash
python3 ~/.codex/skills/mineru-pdf-to-md/scripts/pdf_to_md.py \
  /absolute/path/to/scanned.pdf \
  --method ocr
```

输出通常包括：

```text
mineru-md/<pdf名>/txt/<pdf名>.md
mineru-md/<pdf名>/txt/images/
mineru-md/<pdf名>/txt/<pdf名>_content_list.json
mineru-md/<pdf名>/txt/<pdf名>_middle.json
```

### 给 HTML 报告加批注

```bash
python3 ~/.codex/skills/local-html-annotations/scripts/inject_local_annotations.py \
  /absolute/path/to/report.html
```

打开 HTML 后，点击右下角 `批注` 按钮，选中文本即可添加评论。批注默认保存在浏览器 `localStorage`，可以导出 JSON 备份。

### 给 Codex 的自然语言指令

```text
用 NASA ADS 查 2024 年 Gaia Collaboration 的论文，列出标题、bibcode、引用数并导出 BibTeX。
```

```text
把这个 Markdown 渲染成 Notion 风格 HTML，然后给 HTML 注入本地批注功能。
```

```text
用 grill-me 追问我的开题方案，直到研究问题、数据、方法和风险都说清楚。
```

## 目录结构

```text
.
├── skills/                  # 默认安装的核心 skills
│   ├── mineru-pdf-to-md/
│   ├── nasa-ads-literature/
│   └── ...
├── optional/
│   └── pua-debugging/        # 可选强语气调试包
├── install.sh
├── README.md
└── .gitignore
```

## 安全边界

不要提交以下内容：

- ADS API token、OpenAI token、GitHub token、SSH key
- `~/.ads/dev_key`
- `~/.codex/auth.json`
- Codex sessions、history、archived sessions
- `~/.codex/plugins/cache`
- MinerU 模型缓存，例如 `~/.cache/modelscope`、`~/.cache/huggingface`
- PDF 论文全文、转换后的 Markdown、抽取图片，除非确认版权和分享范围允许
- 个人服务器配置、项目路径、自动化运行记录

本仓库适合公开给课题组使用，但仍建议按“可能公开泄露”的标准处理。

## 许可证

仓库中的不同 skill 可能来自不同来源。`guizang-ppt-skill` 保留其原始 LICENSE 和 README。其他由本仓库整理的本地 skills 见各自目录说明；如需正式公开发布，请在发布前再做一次逐项 license 审查。
