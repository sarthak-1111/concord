# Concord web UI

Extends CrystaLenz's run-streaming console into a sample workbench: sample picker, cross-check panel (C1–C7),
per-technique fit plots and parameters, virtual XAFS band, critic log, report export.

```bash
make api   # API on http://127.0.0.1:8000 (from the repository root)
make ui    # this app on http://127.0.0.1:3000 (installs node_modules on first run)
```

Open `http://127.0.0.1:3000/console#s0031` to go straight to a sample. The API URLs can be changed with
`NEXT_PUBLIC_API_HTTP` (default `http://localhost:8000`) and `NEXT_PUBLIC_API_WS` (default `ws://localhost:8000`).
