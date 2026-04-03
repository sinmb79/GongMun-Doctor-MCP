# Why This Exists

Meta description: Local-first MCP server for secure Korean official-document correction without sending files to cloud APIs.

Labels: mcp, local-first, security, hwpx, korean-documents, claude, codex

Government and enterprise teams do not struggle because they lack AI. They struggle because every useful automation asks them to trade away control. GongMun Doctor MCP exists to keep the useful part of AI, natural language workflow, while keeping the risky part, document movement and cloud dependence, on a short leash.

This repository turns GongMun Doctor into a local MCP server so a client like Claude can say "correct this document" and use your machine's document pipeline instead of uploading sensitive files somewhere else.

## ⚡ What You Get In 30 Seconds

- You keep the original rule-based correction engine.
- You gain a local MCP server that Claude or any stdio MCP client can call.
- You can correct one document, inspect rules, fetch reports, preview text, and batch a folder.
- You do not need cloud API keys for the default workflow.

## 🔒 Security First

This project is opinionated on purpose.

- Local filesystem paths only. URLs are rejected.
- Default tools make no network calls.
- Cloud LLM analysis is not part of the default MCP surface.
- Markdown reports are written only when you ask for them.
- HWP/HWPX handling stays on the machine that already has access to the files.

That is the whole point. Convenience without careless leakage is still possible.

## 🧰 Tools

These MCP tools are exposed today:

- `correct_document(file_path, dry_run=False, report=False)`
- `correct_documents_in_folder(folder_path, dry_run=False, report=False, recursive=False)`
- `list_rules(layer=None)`
- `get_correction_report(file_path)`
- `preview_text_corrections(text, layers=None)`
- `list_document_templates(category=None)`
- `match_document_templates(query)`
- `get_template_variables(template_id)`
- `render_document_template(template_id, values)`

## 🚀 Quick Start

If you already have a Python environment for local tools, install the package in editable mode and add the MCP dependency.

```bash
python -m pip install "mcp[cli]>=1.0,<2"
python -m pip install -e . --no-deps
```

Then start the server over stdio:

```bash
python -m gongmun_doctor.mcp.server
```

If you want to inspect the tool surface before wiring it into a client, run the MCP Inspector:

```bash
npx -y @modelcontextprotocol/inspector python -m gongmun_doctor.mcp.server
```

## 🖥️ Claude Desktop Example

If you use Claude Desktop, the shape is simple: point Claude at a local stdio server. An example config is included at [examples/claude_desktop_config.json](examples/claude_desktop_config.json).

Use the Python interpreter that can import this package. On a locked-down machine, that detail matters more than the JSON.

## ✅ What Works Today

### Single document correction

Ask the client to call `correct_document` with a local `.hwpx` path. Use `dry_run=true` if you want a safe preview first.

### Batch correction

Ask the client to call `correct_documents_in_folder` and point it at a folder. This is the bridge from one-off fixes to real operational use.

### Report retrieval

If a report was written, `get_correction_report` reads the sidecar Markdown file back into the chat so review can happen in context.

## 🛠️ Development Notes

- The MCP layer is a wrapper around the existing GongMun Doctor core, not a rewrite.
- `engine.py` was lightly decoupled so text-only MCP features do not hard-fail when HWPX runtime pieces are absent.
- Python 3.14 may fail to build `python-hwpx` dependencies because of `lxml`. Python 3.12 or 3.13 is the safer baseline for full document handling.

See [docs/mcp-preparation.md](docs/mcp-preparation.md) for the migration notes and security posture behind these decisions.

## 🧭 Roadmap

- Harden folder batching with richer filtering and summary reporting.
- Add client-specific setup docs once the target client mix is fixed.
- Split high-side local tools from any future remote or cloud-assisted tools.
- Treat HWP COM automation as a separate permission boundary, not a casual helper.

## 🌱 Philosophy

The best AI tooling for sensitive work is not the one that feels magical first. It is the one that still deserves your trust after the magic wears off.
