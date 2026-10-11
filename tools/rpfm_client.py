"""Minimal raw-HTTP RPFM MCP client. The registered tools did not load this session.

RPFM's MCP sessions time out, and a dead one answers HTTP 404 on every call. The
session is re-established transparently: a 404 means re-initialize, re-bind the
schema, re-open whatever packs were open, then retry the call once. Pack state is
per-session, so it MUST be rebuilt inside the new one - a fresh session with no packs
answers "Pack not found" rather than reconnecting to the old one.
"""
import json
import re
import urllib.error
import urllib.request

URL = "http://127.0.0.1:45127/mcp"
_sid = [None]
_n = [100]
_reopen = []          # pack paths to reopen after a session is replaced


def _post(body, sid):
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if sid:
        headers["Mcp-Session-Id"] = sid
    return urllib.request.urlopen(
        urllib.request.Request(URL, data=body, headers=headers), timeout=900)


def _parse(raw, tool):
    lines = [l for l in raw.splitlines() if re.match(r"^data:\s*\{", l)]
    if not lines:
        raise RuntimeError("no data line: " + raw[:400])
    o = json.loads(lines[-1].split("data:", 1)[1].strip())
    if "error" in o:
        raise RuntimeError("RPC error on %s: %s" % (tool, json.dumps(o["error"])[:400]))
    txt = "\n".join(x.get("text", "") for x in o["result"]["content"]
                    if x.get("type") == "text")
    try:
        return json.loads(txt)
    except ValueError:
        return txt


def _raw(tool, args):
    _n[0] += 1
    body = json.dumps({"jsonrpc": "2.0", "id": _n[0], "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode("utf-8")
    return _parse(_post(body, _sid[0]).read().decode("utf-8", "replace"), tool)


def _new_session():
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "cc-raw", "version": "1"}}})
    r = _post(body.encode("utf-8"), None)
    sid = r.headers.get("mcp-session-id")
    r.read()
    assert sid, "no mcp-session-id returned"
    _sid[0] = sid
    _raw("set_game_selected", {"game_name": "warhammer_3",
                               "rebuild_dependencies": False})
    for p in list(_reopen):
        _raw("open_packfiles", {"paths": [p]})
    return sid


def call(tool, args, quiet=False):
    if _sid[0] is None:
        _new_session()
    try:
        p = _raw(tool, args)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        _new_session()
        p = _raw(tool, args)
    if isinstance(p, dict) and "Error" in p:
        raise RuntimeError("%s failed: %s" % (tool, p["Error"]))
    if tool == "open_packfiles":
        for path in args.get("paths", []):
            if path not in _reopen:
                _reopen.append(path)
    if not quiet:
        print("  %-32s ok" % tool)
    return p


def open_pack(path):
    """Open a pack and remember it, so a session timeout does not lose it."""
    r = call("open_packfiles", {"paths": [path]}, quiet=True)
    if path not in _reopen:
        _reopen.append(path)
    return r
