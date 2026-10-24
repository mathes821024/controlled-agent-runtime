# Demo host packaging (not Gate 5)

Optional files for the **synthetic Human Acceptance demo** on a small CPU VPS.

This directory is not a production deployment profile. It does not authorize
any host (including the later acceptance IP recorded in
[`docs/governance/ai-workstation.md`](../../docs/governance/ai-workstation.md)).
It stores no credentials, passwords, or private keys.

| File | Role |
|---|---|
| `controlled-agent-demo.service` | systemd unit: bind `127.0.0.1:8000` as a non-root user |
| `docker-compose.yml` + `Dockerfile` | optional container; host publish is loopback-only |
| `Caddyfile.example` | optional TLS reverse proxy in front of loopback |

Start from the one-pager: [`docs/ops/2gb-vps-quickstart.md`](../../docs/ops/2gb-vps-quickstart.md).

Do not run the demo as root. Do not publish port 8000 on a public NIC. The
process has no authentication.
