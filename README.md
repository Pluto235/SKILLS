# SKILLS — Codex App 配置仓库

这是 Pluto235 的 Codex App 配置快照，用于在不同机器之间恢复个人 skills、安全设置和用户选择的插件。

仓库以当前 Codex App 为唯一目标，不再维护 Claude Code 配置或 Claude 插件兼容层。

## 保存的内容

| 路径 | 作用 |
|---|---|
| `codex/skills/` | `~/.agents/skills` 的规范化快照 |
| `codex/config.template.toml` | 脱敏后的可移植 Codex 设置 |
| `codex/manifest.json` | skill 清单、已启用插件、可移植 Git marketplace 和需要恢复的用户插件 |
| `codex/install.sh` | 在新机器恢复配置 |
| `codex/sync.sh` | 从当前机器刷新安全快照 |
| `sync-all.sh` | 同步、密钥扫描并显示差异 |
| `install-all.sh` | 一键恢复入口 |

## 新机器恢复

```bash
git clone git@github.com:Pluto235/SKILLS.git ~/Documents/SKILLS
bash ~/Documents/SKILLS/install-all.sh --dry-run
bash ~/Documents/SKILLS/install-all.sh
```

恢复完成后重启 Codex。需要 OAuth 的插件（例如 GitHub）仍需使用目标账号完成授权；认证信息不会进入 Git 仓库。
恢复脚本只依赖 `python3` 和 `codex`，适用于没有预装 `jq` 的 Linux SSH 主机。

## 从当前机器同步

```bash
cd ~/Documents/SKILLS
git pull --rebase --autostash
bash sync-all.sh
git diff --stat
git diff
git add -A
git commit -m "sync Codex App config from $(hostname) on $(date -u +%Y-%m-%d)"
git push
```

## 设计原则

- 用户 skill 统一保存在 `~/.agents/skills`，避免与旧 `~/.codex/skills` 产生同名冲突。
- 系统自带 skill、运行时、插件缓存和应用内部文件不复制。
- OpenAI bundled/primary-runtime/default 插件由 Codex 自己恢复。
- `manifest.json` 只把用户主动安装、可跨机器恢复的远程插件列入 `plugins.restore`。
- 自定义 marketplace 仅保存可移植的 Git URL，不保存本地 marketplace 路径或任何认证信息；恢复时先添加 marketplace，再安装插件。
- 本机路径、项目 trust、历史记录和认证凭据不会同步。

## 绝不入库

- `~/.codex/auth.json`
- API key、OAuth token、GitHub PAT
- sessions、archived sessions、history、cache、telemetry、shell snapshots
- Codex App 内置 runtime 和 marketplace 缓存
- 项目级 trust/history 状态

即使仓库保持私有，也按“可能公开”标准处理敏感信息。
