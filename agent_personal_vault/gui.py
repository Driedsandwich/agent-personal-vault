"""Small local browser GUI."""

from __future__ import annotations

import argparse
import html
import json
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .schemas import DERIVED_FIELDS
from .vault import check_summary, derived_fields, get_schema, load_store, normalize_value, store_path, write_store


def schema_payload(schema_name: str) -> dict:
    return {
        key: {
            "label": spec.label,
            "group": spec.group,
            "optional": spec.optional,
            "hint": spec.hint,
            "example": spec.example,
            "input_type": spec.input_type,
            "options": list(spec.options),
        }
        for key, spec in get_schema(schema_name).items()
    }


def page_html(token: str, schema_name: str) -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Personal Vault</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif; background: #f6f7f9; color: #17202a; }}
    .app {{ display: grid; grid-template-columns: 240px minmax(420px, 1fr) 320px; min-height: 100vh; }}
    aside {{ background: #101828; color: #eef2f6; padding: 20px; }}
    main {{ padding: 22px; }}
    .panel {{ background: #fff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    .nav button {{ display: block; width: 100%; margin: 0 0 8px; text-align: left; }}
    button, input, textarea, select {{ font: inherit; }}
    button {{ min-height: 34px; border: 1px solid #c4cad6; border-radius: 7px; background: #fff; padding: 0 10px; cursor: pointer; }}
    button.primary {{ background: #2764d8; border-color: #2764d8; color: #fff; }}
    input, textarea, select {{ width: 100%; border: 1px solid #c4cad6; border-radius: 7px; padding: 8px; }}
    textarea {{ min-height: 80px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .field.full {{ grid-column: 1 / -1; }}
    label {{ display: flex; justify-content: space-between; gap: 8px; font-weight: 600; margin-bottom: 5px; }}
    .hint, .example, .key {{ color: #667085; font-size: 12px; }}
    .bar {{ height: 8px; background: #e5e7eb; border-radius: 99px; overflow: hidden; }}
    .bar > span {{ display: block; height: 100%; background: #13795b; }}
    .danger {{ color: #b42318; }}
    .muted {{ color: #667085; }}
    @media (max-width: 900px) {{ .app {{ display: block; }} aside {{ position: static; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<div class="app">
  <aside>
    <h1>Agent Personal Vault</h1>
    <p class="muted">AIエージェントが必要時だけ参照するローカル個人情報vault。</p>
    <div class="nav" id="nav"></div>
  </aside>
  <main>
    <div class="panel">
      <button class="primary" id="save">保存</button>
      <button id="reload">再読込</button>
      <button id="mask">マスク切替</button>
      <span id="state">保存済み</span>
      <p class="danger">外部送信はしません。応募、登録、メール送信、アップロードは別途人間確認してください。</p>
    </div>
    <form id="form"></form>
  </main>
  <aside>
    <section class="panel">
      <h2>状態</h2>
      <div id="count">0/0</div>
      <div class="bar"><span id="progress" style="width:0%"></span></div>
      <h3>不足項目</h3>
      <ul id="missing"></ul>
    </section>
    <section class="panel">
      <h2>派生項目</h2>
      <div id="derived"></div>
    </section>
  </aside>
</div>
<script>
const TOKEN = "{html.escape(token, quote=True)}";
const SCHEMA_NAME = "{html.escape(schema_name, quote=True)}";
const schema = {json.dumps(schema_payload(schema_name), ensure_ascii=False)};
const derivedSchema = {json.dumps(DERIVED_FIELDS, ensure_ascii=False)};
const form = document.getElementById("form");
let fields = {{}};
let masked = false;
let dirty = false;
let timer = null;

function esc(value) {{ return String(value).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;"); }}
function api(path, options={{}}) {{
  const sep = path.includes("?") ? "&" : "?";
  return fetch(path + sep + "token=" + encodeURIComponent(TOKEN), options).then(async r => {{
    const data = await r.json().catch(() => ({{}}));
    if (!r.ok) throw new Error(data.error || "request failed");
    return data;
  }});
}}
function groups() {{ return [...new Set(Object.values(schema).map(x => x.group))]; }}
function value(key) {{ return String(fields[key] || ""); }}
function maskValue(v) {{ if (!v) return ""; return v.length <= 4 ? "•".repeat(v.length) : v.slice(0,2) + "••••" + v.slice(-2); }}
function derived() {{
  return {{
    FULL_NAME: [value("FAMILY_NAME").trim(), value("GIVEN_NAME").trim()].filter(Boolean).join("　"),
    FULL_NAME_KANA: [value("FAMILY_NAME_KANA").trim(), value("GIVEN_NAME_KANA").trim()].filter(Boolean).join("　"),
    NAME_SEPARATOR: "全角スペース",
  }};
}}
function setState(text) {{ document.getElementById("state").textContent = text; }}
function collect() {{
  if (masked) return fields;
  const next = {{...fields}};
  for (const key of Object.keys(schema)) {{
    const node = form.querySelector(`[data-key="${{key}}"]`);
    if (node) next[key] = node.value;
  }}
  return next;
}}
function renderControl(key) {{
  const info = schema[key];
  const raw = value(key);
  const shown = masked ? maskValue(raw) : raw;
  if (info.options && info.options.length) {{
    return `<select data-key="${{key}}" ${{masked ? "disabled" : ""}}>` + info.options.map(o => `<option value="${{esc(o)}}" ${{o === raw ? "selected" : ""}}>${{esc(o || "選択してください")}}</option>`).join("") + `</select>`;
  }}
  if (key === "ADDRESS" || key === "QUALIFICATIONS" || key === "NOTES") return `<textarea data-key="${{key}}" ${{masked ? "readonly" : ""}}>${{esc(shown)}}</textarea>`;
  return `<input type="${{esc(info.input_type || "text")}}" data-key="${{key}}" value="${{esc(shown)}}" ${{masked ? "readonly" : ""}}>`;
}}
function render() {{
  document.getElementById("nav").innerHTML = groups().map(g => `<button onclick="document.getElementById('${{esc(g)}}').scrollIntoView()">${{esc(g)}}</button>`).join("");
  form.innerHTML = groups().map(group => {{
    const keys = Object.keys(schema).filter(k => schema[k].group === group);
    return `<section class="panel" id="${{esc(group)}}"><h2>${{esc(group)}}</h2><div class="grid">` + keys.map(key => {{
      const info = schema[key];
      return `<div class="field ${{["ADDRESS","QUALIFICATIONS","NOTES"].includes(key) ? "full" : ""}}"><label>${{esc(info.label)}}<span class="key">${{esc(key)}}</span></label>${{renderControl(key)}}<div class="hint">${{esc(info.hint || "")}}</div><div class="example">例: ${{esc(info.example || "")}}</div></div>`;
    }}).join("") + `</div></section>`;
  }}).join("");
  updateSide();
}}
function updateSide() {{
  const required = Object.keys(schema).filter(k => !schema[k].optional);
  const missing = required.filter(k => !value(k).trim());
  const filled = required.length - missing.length;
  document.getElementById("count").textContent = `${{filled}}/${{required.length}}`;
  document.getElementById("progress").style.width = `${{Math.round((filled / required.length) * 100)}}%`;
  document.getElementById("missing").innerHTML = missing.length ? missing.map(k => `<li>${{esc(schema[k].label)}} <span class="key">${{esc(k)}}</span></li>`).join("") : "<li>不足項目なし</li>";
  const d = derived();
  document.getElementById("derived").innerHTML = Object.keys(derivedSchema).map(k => `<div>${{esc(derivedSchema[k])}}: <strong>${{esc(d[k] || "未生成")}}</strong></div>`).join("");
}}
function scheduleSave() {{ clearTimeout(timer); timer = setTimeout(() => save(false), 900); }}
async function load() {{ const data = await api("/api/profile"); fields = data.fields || {{}}; render(); dirty=false; setState("保存済み"); }}
async function save(show=true) {{
  clearTimeout(timer);
  fields = collect();
  setState("保存中");
  await api("/api/profile", {{method:"POST", headers:{{"Content-Type":"application/json"}}, body:JSON.stringify({{fields}})}});
  dirty=false; setState(show ? "保存しました" : "保存済み");
  await load();
}}
document.getElementById("save").addEventListener("click", e => {{ e.preventDefault(); save(true).catch(err => setState(err.message)); }});
document.getElementById("reload").addEventListener("click", e => {{ e.preventDefault(); load().catch(err => setState(err.message)); }});
document.getElementById("mask").addEventListener("click", e => {{ e.preventDefault(); fields=collect(); masked=!masked; render(); }});
form.addEventListener("input", () => {{ fields=collect(); dirty=true; setState("未保存"); updateSide(); scheduleSave(); }});
window.addEventListener("beforeunload", e => {{ if (dirty) {{ e.preventDefault(); e.returnValue=""; }} }});
load().catch(err => setState(err.message));
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentPersonalVault/0.1"

    def token_ok(self) -> bool:
        query = parse_qs(urlparse(self.path).query)
        return query.get("token", [""])[0] == self.server.gui_token

    def send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            if not self.token_ok():
                self.send_response(HTTPStatus.FORBIDDEN)
                self.end_headers()
                return
            body = page_html(self.server.gui_token, self.server.schema_name).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/api/profile":
            if not self.token_ok():
                self.send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                return
            store = load_store(create=True, path=self.server.store_path, schema_name=self.server.schema_name)
            self.send_json(HTTPStatus.OK, {"fields": store.get("fields", {}), "summary": check_summary(store, self.server.store_path)})
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/profile":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self.token_ok():
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        incoming = payload.get("fields", {})
        if not isinstance(incoming, dict):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "fields must be an object"})
            return
        store = load_store(create=True, path=self.server.store_path, schema_name=self.server.schema_name)
        schema = get_schema(store["schema"])
        for key in schema:
            store["fields"][key] = normalize_value(key, str(incoming.get(key, "")))
        write_store(store, self.server.store_path)
        self.send_json(HTTPStatus.OK, {"ok": True, "summary": check_summary(store, self.server.store_path)})


def run_server(port: int, open_browser: bool, path: Path, schema_name: str) -> None:
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.gui_token = token  # type: ignore[attr-defined]
    server.store_path = path  # type: ignore[attr-defined]
    server.schema_name = schema_name  # type: ignore[attr-defined]
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/?token={token}"
    load_store(create=True, path=path, schema_name=schema_name)
    print("Agent Personal Vault GUI")
    print(f"url: {url}")
    print("bind: 127.0.0.1")
    print(f"store: {path}")
    print("stop: Ctrl-C")
    if open_browser:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Agent Personal Vault GUI.")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--store", help="Override vault path.")
    parser.add_argument("--schema", default="job_hunting_profile")
    args = parser.parse_args()
    run_server(args.port, args.open, Path(args.store).expanduser() if args.store else store_path(), args.schema)


if __name__ == "__main__":
    main()
