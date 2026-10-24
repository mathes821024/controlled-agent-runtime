# Security Policy

## Supported versions

The project is pre-alpha and has no supported production release. Security fixes
target the default branch until a version policy is published.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities, leaked credentials, private data,
or exploit details. Use GitHub's private vulnerability reporting after the public
repository enables it. Until then, contact the repository owner privately through
an agreed channel.

Include the affected contract or component, impact, reproduction using synthetic
data, and a suggested containment step. Do not test against systems or data you do
not own or have explicit authorization to use.

## Explicit non-claims

Gate 0 artifacts are design contracts. The Gate 1 reference runtime and Human
Acceptance UI are synthetic local evidence. They have not been
production-hardened, externally audited, or approved for real actions.

## Local / VPS demo

`make demo` has **no authentication**. It binds `127.0.0.1` by default and
refuses a public bind unless `--allow-public-bind` is passed. Do not publish
port 8000 on a public NIC, do not run it as root, and do not store host
passwords in this repository. See
[`docs/ops/2gb-vps-quickstart.md`](docs/ops/2gb-vps-quickstart.md).

