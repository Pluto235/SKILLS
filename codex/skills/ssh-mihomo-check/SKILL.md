---
name: ssh-mihomo-check
description: Inspect and repair remote mihomo proxy paths over SSH. Use when Codex needs to log into a server such as ETO or PDC via an existing SSH alias or a non-interactive host target, read the remote mihomo config and controller state, diagnose whether the current proxy path is unhealthy, switch the active business proxy group to a stable node when needed, and report the final proxy status plus any node change that was made.
---

# SSH Mihomo Check

Use this skill for remote proxy health checks on Linux servers that already support non-interactive SSH access.

Run the bundled script instead of reconstructing ad hoc SSH, API, and probe commands. The script handles SSH login, remote mihomo discovery, controller authentication via the remote `config.yaml`, health checks, node selection, optional switching, and structured reporting.

## Workflow

1. Accept a target as either an SSH alias from `~/.ssh/config` or a direct non-interactive `host` / `user@host`.
2. Run the bundled script:

```bash
python3 /Users/luoji/.codex/skills/ssh-mihomo-check/scripts/check_mihomo_proxy.py TARGET
```

3. Default behavior:
   - Prefer the business selector group `稳联云`
   - Read controller auth from the remote `config.yaml` when `secret:` exists
   - Treat current proxy as unhealthy when node delay tests fail, time out, or proxy egress probes fail
   - Prefer `自动选择.now`, then `故障转移.now`, then the lowest-delay healthy candidate from the business group
4. Return a concise summary with diagnostics:
   - target and resolved SSH info
   - whether `mihomo` is running
   - controller and proxy listener availability
   - active group, current node, and whether a switch happened
   - final proxy health and key probe results

## Operating Rules

- Assume the server already allows non-interactive SSH. Do not prompt for passwords.
- Use `ssh -o BatchMode=yes -o RemoteCommand=none` semantics to avoid collisions with local SSH `RemoteCommand` settings.
- Do not expose or echo the remote controller `secret` in the final answer.
- Prefer the bundled script's default test URLs and switching policy unless the user explicitly asks for a different probe URL or target group.
- When verifying without changing state, pass `--no-switch`.

## Commands

Normal repair run:

```bash
python3 /Users/luoji/.codex/skills/ssh-mihomo-check/scripts/check_mihomo_proxy.py ETO
```

Inspection only:

```bash
python3 /Users/luoji/.codex/skills/ssh-mihomo-check/scripts/check_mihomo_proxy.py PDC --no-switch
```

Structured output:

```bash
python3 /Users/luoji/.codex/skills/ssh-mihomo-check/scripts/check_mihomo_proxy.py ETO --json
```

Custom group or probe:

```bash
python3 /Users/luoji/.codex/skills/ssh-mihomo-check/scripts/check_mihomo_proxy.py user@example-host --group MySelector --probe-url https://example.com/generate_204
```

## Resource

`scripts/check_mihomo_proxy.py` is the source of truth for probing, candidate selection, switching, and final reporting.
