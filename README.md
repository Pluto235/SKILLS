# SKILLS — 我的 Claude Code 配置同步仓库

私人仓库。同步 [Claude Code](https://claude.com/claude-code) 的个人 skills、插件清单、settings 偏好，在新机器上一键还原。

## 内容

| 路径 | 作用 |
|---|---|
| `install.sh` | 把仓库内容铺到 `~/.claude/`（幂等，可重复跑） |
| `sync.sh` | 反向：把当前机器的 `~/.claude/` 状态写回仓库 |
| `manifest.json` | marketplace + 启用插件清单 |
| `settings.template.json` | 要 merge 进 `~/.claude/settings.json` 的键（`$HOME` 占位会在 install 时被替换） |
| `statusline-command.sh` | 自定义状态栏脚本 |
| `skills/` | 个人 skill 目录 |

## 在新机器上还原（**给 Claude 的指令**）

> 告诉新机器上的 Claude Code 一句话即可：
>
> ```
> 把 git@github.com:Pluto235/SKILLS.git 克隆到 ~/.claude/SKILLS 并执行里面的 install.sh 还原我的 Claude 配置
> ```

Claude 会执行：

```bash
git clone git@github.com:Pluto235/SKILLS.git ~/.claude/SKILLS
bash ~/.claude/SKILLS/install.sh
```

依赖：`git`、`jq`（macOS: `brew install jq`；Debian/Ubuntu: `sudo apt install jq`）。

装完 **重启 Claude Code**，让插件被加载。

如果某个插件没出现，进 Claude 后跑一次 `/plugin install <name>@claude-plugins-official` 作为兜底。

## 把本机改动 push 回仓库

在 Claude 里说一句：

> sync my Claude config

Claude 会调用本仓库附带的 `sync-claude-config` skill，跑 `sync.sh`、展示 diff、再由你确认提交。

手动跑：

```bash
bash ~/.claude/SKILLS/sync.sh
cd ~/.claude/SKILLS && git add -A && git commit -m "sync from $(hostname)" && git push
```

## 注意

- `sync.sh` 会用本机的 skills 目录**覆盖**仓库的 skills 目录（删除仓库里、本机已删的 skill）。如果你想保留一个 skill 只在某台机器上，别把它放进 `~/.claude/skills/`。
- `install.sh` 的 settings merge 是 `existing * template`，模板键覆盖现有值；本机独有键不受影响。
- 仓库**只**管 skills + 插件清单 + statusline + 上述 settings 键。不要把 `~/.claude/{sessions,history.jsonl,.credentials.json,projects,cache}` 等同步进来。
