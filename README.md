# 天文课题组 Codex Skills 工具包

这个仓库整理了一组适合课题组共享的 Codex skills，用于天文文献检索、静态报告生成、HTML 批注、组会网页 PPT、项目日志和研究计划讨论。

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

本仓库不需要 GitHub Release。使用时直接拉取这个分支即可。

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
bash install.sh --with-extra
bash install.sh --all
```

安装后重启 Codex，让新 skills 被加载。

## 核心 Skills

| Skill | 用途 | 典型场景 |
| --- | --- | --- |
| `nasa-ads-literature` | NASA ADS / arXiv 天文文献检索 | 查 ADS、查 arXiv、导出 BibTeX、下载开放 PDF |
| `local-html-annotations` | 给本地 HTML 报告添加离线批注功能 | 批阅报告、选中文本加评论、导出/导入批注 JSON |
| `notion-html-report` | 把 Markdown / 研究记录渲染成 Notion 风格静态 HTML | 科研复现报告、pipeline 报告、实验总结 |
| `guizang-ppt-skill` | 生成横向翻页网页 PPT | 组会、开题、分享、发布会风格演示 |
| `devlog` | 维护项目 `devlog.md` 修改日志 | 记录代码改动、实验进展、项目历史 |
| `grill-me` | 对研究计划或设计进行连续追问 | 开题前、proposal 前、方案不清楚时做压力测试 |

## 可选 Skills

### `optional/extra-skills/md2wechat`

用于 Markdown 到微信公众号 HTML 的转换。适合课题组有科普、公号发布或中文长文排版需求时安装。

安装：

```bash
bash install.sh --with-extra
```

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
| ECC | 文献综述、网页检索、工程质量 | 提供 `exa-search`、`deep-research`、`literature-review`、`pubmed-database` 等研究/工程 skills |
| Presentations | 正式 slides / PPTX | 生成和检查演示文稿 |
| Documents | 文稿、DOCX、报告 | 处理文档类材料 |
| Spreadsheets | 文献矩阵、观测记录、表格分析 | 处理表格和 xlsx |

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
├── optional/
│   ├── extra-skills/         # 可选发布/写作类 skills
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
- 个人服务器配置、项目路径、自动化运行记录

本仓库适合公开给课题组使用，但仍建议按“可能公开泄露”的标准处理。

## 许可证

仓库中的不同 skill 可能来自不同来源。`guizang-ppt-skill` 保留其原始 LICENSE 和 README。其他由本仓库整理的本地 skills 见各自目录说明；如需正式公开发布，请在发布前再做一次逐项 license 审查。
