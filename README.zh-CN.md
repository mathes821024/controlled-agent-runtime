# Controlled Agent Runtime（受控智能体运行时）

这是一个面向高风险 AI 动作的、证据优先且由策略驱动的控制面项目。

> **当前状态：Gate 0 / Inception。** 当前仓库只冻结契约、Policy、合成 Demo
> Seed 和工程治理，不包含可用于生产的动作运行时，也不授权任何真实执行。

核心分工：模型负责理解意图和提出候选字段；可信上下文、权威 Tool 和人工审核负责建立事实；确定性 Policy 负责决策；只有通过重校验、授权与幂等保护后，白名单 Adapter 才可能执行动作；全链路生成脱敏、可排序的审计证据。

从这里开始：

- [Gate 0 / Inception 总览](docs/inception/00-overview.md)
- [Policy 说明](policy/README.md)
- [Demo Seed 说明](demo-seeds/README.md)（`future_conformance_expectation`：描述未来 Runtime 应满足的期望，不是本仓库已执行证据）
- [工程治理](docs/governance/engineering-governance.md)
- [公开发布检查表](docs/governance/public-release-checklist.md)

本地验证（Python 3.11+，不访问网络）：

```bash
python3 scripts/validate_repository.py
python3 -m unittest discover -s tests -v
```
