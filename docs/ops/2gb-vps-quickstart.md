# 2GB VPS quickstart — HITL demo (no LLM)

一页纸。在约 2GB RAM 的 CPU VPS 上跑合成退款 / 支付管控 HITL 演示。不下载模型。

One page. Run the synthetic refund / payment-control HITL demo on a tiny CPU VPS. No model download.

This is **local / demo evidence**, not a Gate 5 deployment profile and not production authorization. The later Human Acceptance host recorded in [`docs/governance/ai-workstation.md`](../governance/ai-workstation.md) is a name only: this repo stores no password, key, or assumed login for it.

## What you get

- Deterministic `ReferenceRuntime` (Gate 1 Slice 1)
- Human Acceptance UI on FastAPI (Gate 1 Slice 2)
- Four canned scenarios: safe auto, human review, amount mismatch, authority attack
- Typical footprint: **~50 MB RSS** idle on Python 3.12, **~60 MB** `.venv` disk.
  Budget **80–150 MB RAM** and **< 300 MB disk** with OS slack.

## What you do not get

- No large language model, no weight download, no Ollama
- No real payment / refund adapter
- No authentication, database, or TLS in the Python process
- No permission to execute real-world side effects

`CAR_PROPOSAL_HOOK` defaults to `off`. Setting it to `local_model` **fail-closes** and does not pull weights. A 2GB box cannot host a useful general LLM.

## 0. Memory budget

| Item | Keep? | Notes |
|---|---|---|
| Ubuntu + sshd | yes | leave ~500 MB for the OS |
| Python 3.11+ venv + FastAPI | yes | the demo |
| systemd unit | optional | preferred over Docker on 2GB |
| Docker Engine | optional | extra ~200–400 MB; skip if tight |
| nginx / Caddy | optional | only if you terminate TLS on the box |
| Ollama / llama.cpp / CUDA | **no** | will OOM or fill the disk |

Do not `ollama pull` anything on this host.

## 1. Install (Ubuntu 22.04 / 24.04)

SSH in with **your** credential (key preferred). This repo does not assume a root password. If you landed as root, create an unprivileged user before running the demo.

```bash
# Python must be 3.11+. Ubuntu 24.04 is fine as python3.
# Ubuntu 22.04: apt-get install -y python3.11 python3.11-venv && update-alternatives or call python3.11
apt-get update
apt-get install -y git make python3 python3-venv python3-pip
# If `python3 -m venv` fails with ensurepip, install the matching package:
# Ubuntu 24.04 → python3.12-venv ; Ubuntu 22.04 → python3.11 python3.11-venv
python3 --version

id car-demo >/dev/null 2>&1 || useradd --system --create-home --home-dir /opt/controlled-agent-runtime --shell /bin/bash car-demo
mkdir -p /opt/controlled-agent-runtime
chown car-demo:car-demo /opt/controlled-agent-runtime

sudo -u car-demo git clone https://github.com/mathes821024/controlled-agent-runtime.git /opt/controlled-agent-runtime
cd /opt/controlled-agent-runtime
sudo -u car-demo make demo-install
sudo -u car-demo make check
sudo -u car-demo make test
```

If the clone already exists, `git pull` as `car-demo` and rerun `make demo-install`.

Copy [`.env.example`](../../.env.example) to `.env` only if you need overrides. Never commit `.env`.

## 2. Run (loopback)

```bash
sudo -u car-demo make demo
# or:
sudo -u car-demo /opt/controlled-agent-runtime/.venv/bin/python -m controlled_agent_runtime.demo
```

Listens on `http://127.0.0.1:8000`. Binding `0.0.0.0` is refused unless you pass `--allow-public-bind`. The demo has **no login**.

Foreground check:

```bash
curl -sS http://127.0.0.1:8000/api/health
# {"status":"ok","mode":"synthetic_only","real_adapters":"disabled","proposal_hook":"off","llm":"disabled"}
```

Then `POST /api/demo/run` with `{"scenario":"safe_auto"}` or open the UI through a tunnel.

The same loopback origin also serves optional Ingress: `POST /api/agent/propose`.
See [agent-graph-quickstart.md](agent-graph-quickstart.md).

## 3. Expose the UI safely

**Preferred: SSH tunnel** from the operator laptop. Leave security-group / firewall at SSH only (port 22). Do not open 8000 to `0.0.0.0/0`.

```bash
ssh -N -L 8000:127.0.0.1:8000 USER@VPS_HOST
```

Open `http://127.0.0.1:8000` on the laptop. Replace `USER@VPS_HOST` with the account you actually use. Do not paste passwords into this repository.

**If you need a browser on the public internet:** keep uvicorn on loopback and put TLS + **basic auth** on Caddy or nginx on 443. Example: [`deploy/demo/Caddyfile.example`](../../deploy/demo/Caddyfile.example). Generate the password hash on the host (`caddy hash-password`); store it in a local env file that is not in git.

**Do not** run a naked `python -m ... --host 0.0.0.0` as root on a public NIC. That publishes an unauthenticated control-plane UI.

Alibaba Cloud security group: allow 22 (and 80/443 only if you added a proxy). Do not allow 8000.

If nginx already strips `/hitl/` to the uvicorn root (same location as the UI),
the **public** Ingress URL is `http://HOST/hitl/api/agent/propose`. Keep
uvicorn on `127.0.0.1:8000`. **Do not open port 8000.** From the box, curl
`http://127.0.0.1:8000/api/agent/propose`. Details:
[agent-graph-quickstart.md](agent-graph-quickstart.md).

## 4. Optional systemd

```bash
cp deploy/demo/controlled-agent-demo.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now controlled-agent-demo
systemctl status controlled-agent-demo --no-pager
```

Edit `WorkingDirectory` / `ExecStart` if the checkout is not `/opt/controlled-agent-runtime`. The unit binds `127.0.0.1:8000`, caps memory at 256 MB, and runs as `car-demo`.

## 5. Optional Docker Compose

Skip this on a 2GB box if Docker is not already installed. Compose publishes **host loopback only**.

```bash
cd /opt/controlled-agent-runtime
docker compose -f deploy/demo/docker-compose.yml up --build -d
```

Do not change the port mapping to `0.0.0.0:8000:8000`.

## Security caveats

- Synthetic data only. Real adapters stay disabled.
- No secrets belong in this repo, in the systemd unit, or in compose files.
- `/api/docs` is unauthenticated. Keep it off the public NIC.
- Fonts in the UI may load from a CDN; the **runtime path is offline**. System fonts are the fallback.
- Merge approval and this guide do **not** authorize production data, real refunds, or a public launch.

## Residual

HITL approval identity (OQ-08), policy DSL (OQ-09), and a real local-model hook remain open. The stub at `POST /api/demo/propose` exists so a later gate can attach a small on-box model without changing the default canned-seed demo.
