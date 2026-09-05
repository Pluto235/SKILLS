---
name: preview
description: "Use this skill when the user asks for a read-only task preview before implementation, especially in a new thread or unfamiliar project. It helps inspect the project enough to restate the real problem, list clear requirements, identify ambiguities and likely misunderstandings, and propose an execution plan without modifying code or files."
---

# Preview

## Purpose

Use this skill to do a read-only understanding pass before implementation. The goal is to prevent premature edits by making the task, project context, risks, and plan explicit.

## Hard Boundary

Do not modify files, create files, delete files, install packages, run formatters, make commits, push branches, or start implementation.

Allowed actions are read-only inspection and non-mutating commands, such as `pwd`, `ls`, `find`, `rg`, `sed`, `cat`, `git status`, `git log`, `git show`, and test discovery commands that do not execute the test suite unless the user explicitly asks.

If a command might write files, start services, mutate caches, or change dependencies, do not run it during preview.

## Workflow

1. Restate the real problem the user wants solved.
2. Identify explicit requirements from the user request.
3. Identify implicit requirements and project constraints discovered from local context.
4. Identify ambiguities, missing details, and assumptions.
5. Identify where direct implementation is most likely to misunderstand the user.
6. Inspect only enough project context to make the plan credible.
7. Give a concrete execution plan.
8. Stop before edits and ask for confirmation when implementation is not already explicitly authorized.

## Project Inspection

Prefer focused inspection over broad reading:
- Read repository guidance first when present: `AGENTS.md`, `CLAUDE.md`, `README.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, or equivalent.
- Use `rg --files` and targeted `rg` searches to map relevant files.
- Mention which files or signals informed the plan.
- Do not over-index on stale docs when code contradicts them; call out that tension.

## Output Format

Use concise sections:

**Problem Understanding**

State what the user is really trying to accomplish.

**Clear Requirements**

List what is explicit and actionable.

**Ambiguities**

List unclear points, missing inputs, or choices that could affect implementation.

**Likely Misunderstandings**

Name the most likely wrong interpretation if implementation starts immediately.

**Project Context Observed**

List the key files, commands, or repo signals inspected.

**Execution Plan**

Give ordered implementation steps. Keep it specific enough that the next turn can execute it.

**Confirmation Needed**

Say whether implementation can proceed directly or which decisions need user confirmation.
