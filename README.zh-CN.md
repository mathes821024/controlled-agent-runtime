# Controlled Agent Runtime（受控智能体运行时）

这是一个面向高风险 AI 动作的、证据优先且由策略驱动的控制面项目。第一个具体痛点是**退款 / 支付管控**：模型可以起草退款提案，但不能成为身份、金额、批准或适配器成功的权威。

> **当前状态：** Gate 0 契约已在 `main`；Gate 1 Slice 1 内存参考运行时与 Slice 2 人工验收 UI 也已在 `main`。这是合成、本地证据，**不是**可投产的动作运行时，也不授权真实执行。

从这里开始：

- [2GB VPS 一页纸](docs/ops/2gb-vps-quickstart.md)（默认不下载模型）
- [Gate 0 / Inception 总览](docs/inception/00-overview.md)
- [Policy 说明](policy/README.md)
- [Demo Seed 说明](demo-seeds/README.md)
- [工程治理](docs/governance/engineering-governance.md)

本地 / 小 VPS（Python 3.11+，默认不访问网络、不拉模型）：

```bash
make check
make test
make demo
# 浏览器打开 http://127.0.0.1:8000
```

默认只监听回环。VPS 上请用 SSH 隧道或本机反向代理，不要把 8000 裸开到公网，也不要在 2GB 机器上安装大模型。
