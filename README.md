# SKILLS — Claude Code + Codex 配置同步仓库

私人配置仓库。用于同步 Claude Code 与 Codex 的个人 skills、插件清单和安全偏好模板。目标是在新机器上把这个仓库交给对应 agent 后，一键还原常用工作环境。

## 目录

| 路径 | 作用 |
|---|---|
| `install-all.sh` | 同时安装 Claude Code 与 Codex 的托管配置 |
| `sync-all.sh` | 从当前机器安全采集 Claude Code + Codex 配置并展示 diff |
| `install.sh` | 兼容旧入口，转发到 `install-all.sh` |
| `claude/` | Claude Code 专属 skills、插件 manifest、settings 模板、安装/同步脚本 |
| `codex/` | Codex 专属 skills、`.agents/skills`、Codex 配置模板、安装/同步脚本 |
| `shared/skills/` | 可复制到 Codex 的通用 skills |
| `scripts/` | 安全模板生成与 Codex TOML 合并辅助脚本 |

## 新机器一键还原

给 Claude Code 或 Codex 的指令：

```text
把 git@github.com:Pluto235/SKILLS.git 克隆到 ~/Documents/SKILLS，然后执行 bash ~/Documents/SKILLS/install-all.sh 还原我的 Claude Code 和 Codex 配置。
```

手动执行：

```bash
git clone git@github.com:Pluto235/SKILLS.git ~/Documents/SKILLS
bash ~/Documents/SKILLS/install-all.sh
```

先看将会改什么：

```bash
bash ~/Documents/SKILLS/install-all.sh --dry-run
```

安装后重启 Claude Code 和 Codex，让新 skills/plugins 被加载。

## 同步当前机器到仓库

```bash
cd ~/Documents/SKILLS
git pull --rebase --autostash
bash sync-all.sh
git diff --stat
git diff
git add -A
git commit -m "sync agent config from $(hostname) on $(date -u +%Y-%m-%d)"
git push
```

`sync-all.sh` 会刷新：

- Claude Code skills、marketplaces、enabled plugins、脱敏 settings 模板。
- Codex user skills、`~/.agents/skills`、安全 Codex config 模板。
- 明显 secret 模式检查；发现疑似 token 会失败退出。

## 边界

Claude-only：

- `claude/manifest.json`
- `claude/settings.template.json`
- `claude/statusline-command.sh`
- Claude marketplace/plugin 安装逻辑

Codex-only：

- `codex/skills/`
- `codex/agents-skills/`
- `codex/pua-skills/`
- `codex/config.template.toml`

Shared：

- `shared/skills/devlog`
- `shared/skills/grill-me`
- `shared/skills/guizang-ppt-skill`

## 绝不入库

- `~/.claude/settings.json` 里的 `env`
- `ANTHROPIC_AUTH_TOKEN`
- `GITHUB_PERSONAL_ACCESS_TOKEN`
- `~/.codex/auth.json`
- `~/.codex/models_cache.json`
- sessions、archived sessions、history、cache、telemetry、shell snapshots
- 项目级 trust/history/cache 状态

仓库即使保持私有，也按“可能泄露”标准处理密钥。
