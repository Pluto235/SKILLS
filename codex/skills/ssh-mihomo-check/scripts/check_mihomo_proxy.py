#!/usr/bin/env python3
"""Inspect a remote mihomo instance over SSH and switch to a healthy node if needed."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import textwrap
from typing import Any


GROUP_TYPES = {"Selector", "URLTest", "Fallback"}
NON_NODE_TYPES = GROUP_TYPES | {"Direct", "Reject", "RejectDrop", "Pass", "Compatible"}
DEFAULT_GROUP = "稳联云"
DEFAULT_PRIMARY_PROBE = "https://www.google.com/generate_204"
DEFAULT_FALLBACK_PROBE = "https://www.gstatic.com/generate_204"


REMOTE_SCRIPT = textwrap.dedent(
    r"""
    import argparse
    import getpass
    import json
    import os
    import shlex
    import subprocess
    import sys
    import time
    import urllib.error
    import urllib.parse
    import urllib.request
    from pathlib import Path

    GROUP_TYPES = {"Selector", "URLTest", "Fallback"}
    NON_NODE_TYPES = GROUP_TYPES | {"Direct", "Reject", "RejectDrop", "Pass", "Compatible"}


    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--group", required=True)
        parser.add_argument("--probe-url", required=True)
        parser.add_argument("--fallback-probe-url", required=True)
        parser.add_argument("--delay-timeout-ms", type=int, required=True)
        parser.add_argument("--request-timeout", type=int, required=True)
        parser.add_argument("--no-switch", action="store_true")
        return parser.parse_args()


    def read_process_table():
        proc = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]


    def find_mihomo_process():
        for line in read_process_table():
            if "mihomo" not in line:
                continue
            pid_text, _, args = line.strip().partition(" ")
            try:
                pid = int(pid_text)
            except ValueError:
                continue
            tokens = shlex.split(args)
            config_dir = None
            for index, token in enumerate(tokens):
                if token == "-d" and index + 1 < len(tokens):
                    config_dir = tokens[index + 1]
                    break
            return {
                "pid": pid,
                "command": args,
                "config_dir": config_dir,
            }
        return None


    def parse_scalar_config(config_text):
        values = {}
        for raw_line in config_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if key in {
                "external-controller",
                "secret",
                "mixed-port",
                "port",
                "socks-port",
                "mode",
                "bind-address",
            }:
                values[key] = value.strip().strip("'\"")
        return values


    def api_client(controller, secret):
        headers = {}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"

        def request(method, path, payload=None):
            url = f"http://{controller}{path}"
            data = None
            if payload is not None:
                data = json.dumps(payload).encode()
                headers_local = dict(headers)
                headers_local["Content-Type"] = "application/json"
            else:
                headers_local = headers
            req = urllib.request.Request(url, data=data, method=method, headers=headers_local)
            with urllib.request.urlopen(req, timeout=10) as response:
                raw = response.read()
                if not raw:
                    return {}
                return json.loads(raw.decode())

        return request


    def proxy_probe(port, urls, timeout_seconds):
        diagnostics = []
        proxy_url = f"http://127.0.0.1:{port}"
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        )
        opener.addheaders = [("User-Agent", "ssh-mihomo-check/1.0")]

        for url in urls:
            started = time.perf_counter()
            try:
                request = urllib.request.Request(url, method="GET")
                with opener.open(request, timeout=timeout_seconds) as response:
                    elapsed = round(time.perf_counter() - started, 3)
                    code = getattr(response, "status", response.getcode())
                    ok = 200 <= code < 400
                    diagnostics.append(
                        {
                            "url": url,
                            "ok": ok,
                            "code": code,
                            "elapsed_seconds": elapsed,
                        }
                    )
                    if ok:
                        return diagnostics[-1], diagnostics
            except Exception as exc:
                elapsed = round(time.perf_counter() - started, 3)
                diagnostics.append(
                    {
                        "url": url,
                        "ok": False,
                        "error": str(exc),
                        "elapsed_seconds": elapsed,
                    }
                )
        return None, diagnostics


    def node_delay(api_request, node_name, urls, timeout_ms):
        attempts = []
        quoted_name = urllib.parse.quote(node_name, safe="")
        for url in urls:
            quoted_url = urllib.parse.quote(url, safe="")
            path = f"/proxies/{quoted_name}/delay?timeout={timeout_ms}&url={quoted_url}"
            try:
                data = api_request("GET", path)
                delay = data.get("delay")
                if isinstance(delay, int):
                    attempt = {"ok": True, "url": url, "delay_ms": delay}
                    attempts.append(attempt)
                    return attempt, attempts
                attempts.append({"ok": False, "url": url, "error": f"unexpected payload: {data}"})
            except Exception as exc:
                attempts.append({"ok": False, "url": url, "error": str(exc)})
        return None, attempts


    def choose_target_group(proxies, desired_group):
        if desired_group in proxies and proxies[desired_group].get("type") == "Selector":
            return desired_group

        selectors = [
            name
            for name, meta in proxies.items()
            if meta.get("type") == "Selector"
        ]
        for name in selectors:
            if name != "GLOBAL":
                return name
        if "GLOBAL" in selectors:
            return "GLOBAL"
        if desired_group in proxies:
            return desired_group
        for name in ("自动选择", "故障转移"):
            if name in proxies:
                return name
        for name, meta in proxies.items():
            if meta.get("type") in GROUP_TYPES:
                return name
        return None


    def is_real_node(proxies, name):
        meta = proxies.get(name)
        if not meta:
            return False
        return meta.get("type") not in NON_NODE_TYPES


    def candidate_nodes(proxies, group_name):
        group_meta = proxies.get(group_name) or {}
        names = []
        for name in group_meta.get("all") or []:
            if is_real_node(proxies, name):
                names.append(name)
        return names


    def switch_group(api_request, group_name, node_name):
        quoted_group = urllib.parse.quote(group_name, safe="")
        api_request("PUT", f"/proxies/{quoted_group}", {"name": node_name})


    def main():
        args = parse_args()
        result = {
            "target_user": getpass.getuser(),
            "server_hostname": subprocess.run(
                ["hostname"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
            "requested_group": args.group,
        }

        process = find_mihomo_process()
        result["mihomo"] = {
            "running": bool(process),
            "pid": process.get("pid") if process else None,
            "command": process.get("command") if process else None,
        }
        if not process:
            result["status"] = "error"
            result["error"] = "mihomo process not found"
            print(json.dumps(result, ensure_ascii=False))
            return

        config_dir = process.get("config_dir") or str(Path.home() / ".config" / "mihomo")
        config_path = Path(config_dir) / "config.yaml"
        result["mihomo"]["config_path"] = str(config_path)
        if not config_path.exists():
            result["status"] = "error"
            result["error"] = f"config not found: {config_path}"
            print(json.dumps(result, ensure_ascii=False))
            return

        config_text = config_path.read_text(encoding="utf-8")
        config = parse_scalar_config(config_text)
        controller = config.get("external-controller", "127.0.0.1:9090")
        secret = config.get("secret")
        mixed_port = int(config.get("mixed-port") or config.get("port") or 7890)
        http_port = int(config.get("port") or mixed_port)
        socks_port = int(config.get("socks-port") or 7892)

        result["controller"] = {
            "address": controller,
            "auth_required": bool(secret),
        }
        result["ports"] = {
            "mixed": mixed_port,
            "http": http_port,
            "socks": socks_port,
        }

        api_request = api_client(controller, secret)
        try:
            version = api_request("GET", "/version")
            proxies_payload = api_request("GET", "/proxies")
        except Exception as exc:
            result["status"] = "error"
            result["error"] = f"controller query failed: {exc}"
            print(json.dumps(result, ensure_ascii=False))
            return

        proxies = proxies_payload.get("proxies") or {}
        result["controller"]["version"] = version.get("version")

        target_group = choose_target_group(proxies, args.group)
        if not target_group:
            result["status"] = "error"
            result["error"] = "no usable proxy group found"
            print(json.dumps(result, ensure_ascii=False))
            return

        group_meta = proxies.get(target_group) or {}
        auto_group = proxies.get("自动选择") or {}
        fallback_group = proxies.get("故障转移") or {}
        current_node = group_meta.get("now")

        result["group"] = {
            "name": target_group,
            "type": group_meta.get("type"),
            "current_node": current_node,
            "auto_group_node": auto_group.get("now"),
            "fallback_group_node": fallback_group.get("now"),
            "candidate_count": len(candidate_nodes(proxies, target_group)),
        }

        probe_urls = [args.probe_url]
        if args.fallback_probe_url and args.fallback_probe_url != args.probe_url:
            probe_urls.append(args.fallback_probe_url)

        current_delay, current_delay_attempts = (None, [])
        if current_node and is_real_node(proxies, current_node):
            current_delay, current_delay_attempts = node_delay(
                api_request, current_node, probe_urls, args.delay_timeout_ms
            )

        proxy_probe_result, proxy_probe_attempts = proxy_probe(
            mixed_port, probe_urls, args.request_timeout
        )
        healthy = bool(current_delay and proxy_probe_result)

        result["checks"] = {
            "current_node_delay": current_delay,
            "current_node_delay_attempts": current_delay_attempts,
            "proxy_probe": proxy_probe_result,
            "proxy_probe_attempts": proxy_probe_attempts,
            "healthy": healthy,
        }

        preferred_candidates = []
        for preferred in (auto_group.get("now"), fallback_group.get("now")):
            if preferred and preferred not in preferred_candidates and is_real_node(proxies, preferred):
                preferred_candidates.append(preferred)

        tested_candidates = []
        recommendation = None

        def test_candidate(name):
            success, attempts = node_delay(api_request, name, probe_urls, args.delay_timeout_ms)
            record = {
                "name": name,
                "ok": bool(success),
                "delay": success.get("delay_ms") if success else None,
                "attempts": attempts,
            }
            tested_candidates.append(record)
            return record

        if not healthy:
            for name in preferred_candidates:
                record = test_candidate(name)
                if record["ok"]:
                    recommendation = record
                    break

            if recommendation is None:
                ranked = []
                for name in candidate_nodes(proxies, target_group):
                    if name == current_node:
                        continue
                    record = test_candidate(name)
                    if record["ok"]:
                        ranked.append(record)
                if ranked:
                    ranked.sort(key=lambda item: (item["delay"], item["name"]))
                    recommendation = ranked[0]

        action = "none"
        switched_to = None
        final_probe_result = proxy_probe_result
        final_probe_attempts = proxy_probe_attempts

        if recommendation and recommendation["name"] != current_node:
            action = "recommend" if args.no_switch else "switch"
            if not args.no_switch and group_meta.get("type") == "Selector":
                try:
                    switch_group(api_request, target_group, recommendation["name"])
                    switched_to = recommendation["name"]
                    final_probe_result, final_probe_attempts = proxy_probe(
                        mixed_port, probe_urls, args.request_timeout
                    )
                except Exception as exc:
                    result["switch_error"] = str(exc)

        result["recommendation"] = recommendation
        result["tested_candidates"] = tested_candidates
        result["action"] = action
        result["switched_to"] = switched_to
        result["final_proxy_probe"] = final_probe_result
        result["final_proxy_probe_attempts"] = final_probe_attempts
        result["status"] = "ok"
        print(json.dumps(result, ensure_ascii=False))


    if __name__ == "__main__":
        main()
    """
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a remote mihomo proxy path over SSH and switch to a stable node if needed.",
    )
    parser.add_argument("target", help="SSH alias, host, or user@host")
    parser.add_argument("--group", default=DEFAULT_GROUP, help=f"Preferred business selector group (default: {DEFAULT_GROUP})")
    parser.add_argument("--probe-url", default=DEFAULT_PRIMARY_PROBE, help="Primary probe URL for delay and proxy tests")
    parser.add_argument(
        "--fallback-probe-url",
        default=DEFAULT_FALLBACK_PROBE,
        help="Fallback probe URL if the primary probe fails",
    )
    parser.add_argument("--delay-timeout-ms", type=int, default=5000, help="Delay test timeout in milliseconds")
    parser.add_argument("--request-timeout", type=int, default=15, help="Proxy request timeout in seconds")
    parser.add_argument("--connect-timeout", type=int, default=10, help="SSH connect timeout in seconds")
    parser.add_argument("--no-switch", action="store_true", help="Inspect and recommend only; do not change the remote node")
    parser.add_argument("--json", action="store_true", help="Print raw JSON result")
    return parser.parse_args()


def run_command(command: list[str], stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )


def ssh_base(target: str, connect_timeout: int) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        "-o",
        "RemoteCommand=none",
        target,
    ]


def remote_python(target: str, connect_timeout: int, args: list[str]) -> dict[str, Any]:
    remote_cmd = "python3 - " + " ".join(shlex.quote(arg) for arg in args)
    command = ssh_base(target, connect_timeout) + [remote_cmd]
    result = run_command(command, stdin_text=REMOTE_SCRIPT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "remote python execution failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid remote JSON: {exc}: {result.stdout}") from exc


def ssh_resolve(target: str, connect_timeout: int) -> dict[str, str]:
    command = [
        "ssh",
        "-G",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        target,
    ]
    result = run_command(command)
    if result.returncode != 0:
        return {"target": target}
    resolved: dict[str, str] = {"target": target}
    for raw_line in result.stdout.splitlines():
        if not raw_line.strip():
            continue
        key, _, value = raw_line.partition(" ")
        if key in {"host", "hostname", "user", "port", "identityfile"} and value:
            resolved[key] = value.strip()
    return resolved


def format_attempts(attempts: list[dict[str, Any]]) -> str:
    fragments = []
    for item in attempts:
        url = item.get("url", "?")
        if item.get("ok"):
            delay = item.get("delay_ms")
            code = item.get("code")
            elapsed = item.get("elapsed_seconds")
            if delay is not None:
                fragments.append(f"{url} delay={delay}ms")
            elif code is not None:
                fragments.append(f"{url} code={code} t={elapsed}s")
            else:
                fragments.append(f"{url} ok")
        else:
            error = item.get("error", "failed")
            fragments.append(f"{url} error={error}")
    return "; ".join(fragments) if fragments else "n/a"


def print_summary(data: dict[str, Any], resolved: dict[str, str]) -> None:
    if data.get("status") != "ok":
        print(f"Target: {resolved.get('target')}")
        print(f"Error: {data.get('error', 'unknown error')}")
        return

    group = data.get("group", {})
    checks = data.get("checks", {})
    recommendation = data.get("recommendation")
    final_probe = data.get("final_proxy_probe")
    action = data.get("action")
    switched_to = data.get("switched_to")

    resolved_bits = [resolved.get("target")]
    if resolved.get("user") and resolved.get("hostname"):
        resolved_bits.append(f"{resolved['user']}@{resolved['hostname']}")
    elif resolved.get("hostname"):
        resolved_bits.append(resolved["hostname"])

    print(f"Target: {' -> '.join(bit for bit in resolved_bits if bit)}")
    print(
        "Mihomo: "
        f"{'running' if data.get('mihomo', {}).get('running') else 'not running'}"
        f" pid={data.get('mihomo', {}).get('pid') or 'n/a'}"
    )
    print(
        "Controller: "
        f"{data.get('controller', {}).get('address')} "
        f"(auth_required={data.get('controller', {}).get('auth_required')}, "
        f"version={data.get('controller', {}).get('version', 'n/a')})"
    )
    print(
        "Group: "
        f"{group.get('name')} current={group.get('current_node') or 'n/a'} "
        f"auto={group.get('auto_group_node') or 'n/a'} "
        f"fallback={group.get('fallback_group_node') or 'n/a'}"
    )
    print(f"Health: {'healthy' if checks.get('healthy') else 'unhealthy'}")
    print("Current node delay checks: " + format_attempts(checks.get("current_node_delay_attempts") or []))
    print("Proxy probe checks: " + format_attempts(checks.get("proxy_probe_attempts") or []))

    if action == "switch":
        print(f"Action: switched {group.get('name')} to {switched_to}")
    elif action == "recommend":
        print(f"Action: recommend switch to {recommendation.get('name') if recommendation else 'n/a'}")
    else:
        print("Action: no switch")

    if recommendation:
        print(
            "Recommendation diagnostics: "
            f"{recommendation.get('name')} "
            f"delay={recommendation.get('delay') if recommendation.get('delay') is not None else 'n/a'}ms"
        )
    else:
        print("Recommendation diagnostics: no healthy replacement found")

    if final_probe:
        print("Final proxy probe: " + format_attempts([final_probe]))
    elif data.get("final_proxy_probe_attempts"):
        print("Final proxy probe: " + format_attempts(data["final_proxy_probe_attempts"]))
    else:
        print("Final proxy probe: n/a")

    if data.get("switch_error"):
        print(f"Switch error: {data['switch_error']}")


def main() -> int:
    args = parse_args()
    resolved = ssh_resolve(args.target, args.connect_timeout)

    remote_args = [
        "--group",
        args.group,
        "--probe-url",
        args.probe_url,
        "--fallback-probe-url",
        args.fallback_probe_url,
        "--delay-timeout-ms",
        str(args.delay_timeout_ms),
        "--request-timeout",
        str(args.request_timeout),
    ]
    if args.no_switch:
        remote_args.append("--no-switch")

    try:
        data = remote_python(args.target, args.connect_timeout, remote_args)
    except Exception as exc:
        print(f"Target: {args.target}")
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        json.dump({"resolved_ssh": resolved, "result": data}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print_summary(data, resolved)

    return 0 if data.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
