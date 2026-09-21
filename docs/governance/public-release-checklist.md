# Public release checklist

## Content and provenance

- [ ] No secrets, private endpoints, customer data, personal data, or raw private payloads.
- [ ] Repository-wide secret scan completed with an approved tool.
- [ ] Extraction Source was not modified and copied content has valid provenance.
- [ ] All demo identities are synthetic; example email uses `.invalid`.
- [ ] README capability claims match current implementation and evidence.

## Legal and community

- [ ] Owner confirms repository name, description, visibility, and Apache-2.0 license.
- [ ] Copyright/NOTICE text is accepted.
- [ ] Security contact or GitHub private vulnerability reporting is enabled.
- [ ] Code of Conduct, CONTRIBUTING, SECURITY, and GOVERNANCE are reviewed.

## Engineering

- [ ] `make check` and `make test` pass on the exact publish candidate.
- [ ] Git status and staged diff contain only intended public files.
- [ ] Default branch protection and required CI are configured.
- [ ] Secret scanning, Dependabot alerts, and private vulnerability reporting are enabled.
- [ ] No release, package publish, deployment, or external adapter is implied.

## First repository creation

Create an empty **public** GitHub repository without auto-generating README,
license, or `.gitignore`; this local skeleton already provides them. Do not push
until the final public-content review and explicit push authorization.

