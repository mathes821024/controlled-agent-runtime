# Product Contract — controlled-agent-runtime

**Status:** Draft — awaiting Owner + ChatGPT Product Gate Review  
**Project:** controlled-agent-runtime  
**Repo root:** `/Users/xyl/Documents/workAI/controlled-agent-runtime`  
**Baseline HEAD:** `329d926` on `main`  
**Author:** Product Manager  
**Evidence date:** 2026-09-24  

本文件是 Product Contract 草案。它不宣布 Product Gate PASS，不冻结范围，也不授权实现。

阅读时区分四层证据：

| 标记 | 含义 |
|------|------|
| **HEAD** | 已提交在 `329d926` |
| **Worktree draft** | 本轮开始前就存在的未提交修改。Product Manager 只阅读，不拥有、不批准 |
| **Checked now** | 本轮对当前工作区运行了静态校验和单元测试。通过只说明契约文件自洽 |
| **Not a runtime** | Demo Seed 里的 `executed` 是对未来运行时的期望，不是本仓库已经执行过动作 |

本轮静态结果（工作区，不是 HEAD）：`scripts/validate_repository.py` 返回 OK；`tests/` 中 8 个测试通过。这是 **static** 证据。

---

## 1. Product Definition

Controlled Agent Runtime 是一个证据优先、由策略驱动的控制面。它要解决的问题是：AI 可以提出动作意图，但不能因此成为身份、业务事实、批准、幂等或副作用的权威。

产品把一次受控动作分成五段：

```text
Proposal   模型或界面提出意图和非权威字段
Authority  可信上下文、权威 Tool、人工审核建立事实
Policy     确定性规则给出 deny / needs_input / needs_review / allow_execution
Execution  只有守卫都通过后，白名单 Adapter 才可以做有界动作
Evidence   有顺序、已脱敏的审计轨迹说明发生了什么
```

当前仓库处于 **Gate 0 / Inception**。它交付的是可评审的契约、策略样例、合成 Demo Seed 和工程治理。它不包含可投产的动作运行时，也不授权真实执行。

领域上它保持中立。退款只是第一个合成样例，用来检验“提案不得冒充权威”这件事，不是产品本身变成支付产品。

仓库声明的提取来源是私有项目 `payment-controlled-agent` 的只读抽象。公开仓库重写了中立契约和合成数据，不继承该来源的私有适配器、载荷、凭证或内部 API。

## 2. Problem & Value

### 问题

AI 辅助流程很容易把三件事混成一件：听懂人话、认定业务事实、产生副作用。一句看起来合理的模型输出，会被当成已核实事实或执行决定。

### 为什么存在

需要一个小的、可复用的参考控制面，把权威、策略、人工审核、幂等和证据分开，并且让后来的工程师不靠私有来源也能评审这些边界。

### 价值

- 提案和权威事实不能互相覆盖。
- 策略是版本化数据，人可以审，未来运行时必须确定性求值。
- 不确定、缺失或依赖不可用时失败关闭，而不是放行。
- 人工审核是绑定到案件、行为人和时间的决定，不是一句话或一个关联 token。
- 代码检查、本地夹具、外部集成和生产观察是不同强度的证据，不能升级表述。

### 它不是什么

按 `docs/inception/02-scope-and-non-goals.md`：

- 不是生产运行时、API 服务器、SDK 产品、数据库或用户界面
- 不是真实支付、邮件、文档、消息、身份或模型接入
- 不是通用策略语言或通用工作流引擎
- 不是合规认证、安全审计结论或生产适用性声明
- 不是私有来源项目的迁移或内部 API 兼容层

## 3. Users / Actors

名字以仓库原文为准。

### 现在就存在的人

| Actor | 仓库依据 | 产品职责 |
|-------|----------|----------|
| **Owner** | `GOVERNANCE.md` | 项目范围上的最终 Admission、Decision、Execution Gate。合并代码不等于可以连接生产、导入私有数据、部署或执行真实动作 |
| **Maintainer** | `GOVERNANCE.md` | 在已准入的 Gate 内评审仓库变更和发布 |
| **Contributor** | `GOVERNANCE.md` | 带证据提出变更，遵守边界 |
| **Application engineer** | Charter | 把 AI 辅助加到动作流程里的人；Gate 0 的成功是他能读懂契约 |
| **Security / risk reviewer** | Charter | 定义不可绕过的控制 |
| **Domain owner** | Charter | 批准策略和执行边界。与仓库 Owner 不是自动同一个人 |
| **Auditor / operator** | Charter | 需要可追踪的结果。当前只能审计文档和静态契约，没有运行中的操作台 |

### 契约里的运行时角色（尚未实现）

| Actor | 权威 |
|-------|------|
| Model / UI | 只能提出 Proposal |
| Trusted context | 主体、租户、应用、环境。不来自模型 |
| Authoritative Tool | 资源事实。退款样例里是交易查询 |
| Policy engine | 策略版本和决定 |
| Human reviewer | 批准或拒绝。认证方式仍是开放问题 |
| Adapter | 归一化后的执行结果。Gate 0 禁止真实 Adapter |

## 4. Core User Journeys

从业务任务出发。当前没有产品界面，所以下面没有页面流程。

### 4.1 工程师评审公开契约

**今天就能做。** 阅读 Inception、Policy、Seed 和 ADR，不打开私有来源，回答：什么是权威、什么时候禁止执行、未来运行时必须留下什么证据。

Gate 0 的成功标准就是这件事。总览里的退出勾选仍是空的，所以这条旅程还没有被 Owner 接受。

### 4.2 风险评审者检查“模型不能决定什么”

**今天是文档和策略样例，不是运行中的拦截器。** 样例把主体、租户、资源引用、批准身份、幂等键、执行令牌和 Adapter 结果列为模型不可填写的字段。工作区草案进一步把原始金额、退款金额和 `respCode` 也列为不可来自模型。

### 4.3 领域负责人看一条退款提案该停在哪里

这是样例业务，不是已上线流程。规则意图在 HEAD 里已经有草稿：

- 意图不是 `refund` → `deny`
- 必填提案字段缺失 → `needs_input`
- 提案金额与权威原始金额不一致 → `deny`（仅全额退款）
- 金额高于样例阈值 → `needs_review`
- 前面都通过 → `allow_execution`，意思是可以进入执行守卫，不是已经执行

工作区草案用 seed-02、seed-03 把“高于阈值”和“金额不一致”写成未来符合性期望，并规定这两条都不得调用 Adapter。仓库里没有求值器去跑这些规则。

### 4.4 未来运行时才存在的执行旅程

契约要求的顺序是：提案进入 → 校验 → 绑定可信上下文 → 装载权威事实 → 策略决定 → 需要时绑定人工决定 → 执行前重校验 → 占用幂等 → 才允许白名单 Adapter → 归一化结果和证据。

失败的门不再发出后续执行事件。真实 Adapter 在 Gate 0 关闭。这条旅程是 **Contracted**，不是 **Implemented**。

### 4.5 审计者判断一句话能证明什么

证据分 `static`、`local_runtime`、`integration`、`production`。本仓库今天只有 static。通过本地校验不能写成集成通过或生产可用。

## 5. Current Product State

### Implemented

- 一个无第三方依赖的仓库契约检查器：`src/controlled_agent_runtime/validation.py`，命令为 `python3 scripts/validate_repository.py`，包入口为 `controlled-agent-validate`。
- HEAD 上的检查器核对：默认拒绝、合成数据、一组受保护字段、执行前重校验、幂等、真实 Adapter 关闭，以及 seed-01 的形状。
- 工作区里的检查器还核对金额契约、条件语言未冻结、退款业务码、R-04，以及 seed-01/02/03。这是未提交代码，不是 `329d926` 的行为。
- 工程骨架：许可证文件、安全政策、贡献说明、治理、CI、Issue / PR 模板。本轮没有改 CI，也没有把它当成产品功能。

没有提案求值器，没有审核服务，没有 Adapter 调用，没有数据库，没有用户界面。

### Contracted / documented

**HEAD 已有：**

- Charter、范围、信任边界、Gate 与证据模型、运行时概念契约
- ADR-0001（提案与权威分离）和 ADR-0002（默认失败关闭），状态均为 Accepted for Gate 0
- Policy 草稿 `demo.refund.full.v1` / `1.0.0`，`default_effect = deny`
- 受保护字段：`principal_id`、`tenant_id`、`resource_ref`、`authorized_by`、`approval_status`、`idempotency_key`、`execution_token`、`adapter_result`
- 提案允许字段：`intent`、`original_order_id`、`requested_amount_minor`、`merchant_email`
- Demo Seed `seed-01`。期望结果写成 `executed`，原因码 `mock_business_success`。没有 `expectation_kind`
- 开放问题 OQ-01 到 OQ-08
- Gate 0 退出标准全部未勾选

**只存在于未提交工作区：**

- Policy 版本变为 `1.0.1`，增加 CNY 整数分、`1 yuan = 100` 分、`10000` 分 = 100 元、禁止浮点
- `amount_minor > 10000` 必须 `needs_review`；`<= 10000` 只表示有资格进入后续守卫
- 提案金额只用于一致性比较。权威金额来自交易查询，不来自模型
- 受保护字段增加 `original_amount_minor`、`refund_amount_minor`、`respCode`
- 提案字段改为 `intent`、`appid`、`term_id`、`original_order_no`、`original_transaction_date`，外加可选的 `requested_amount_minor` 和 `merchant_email`
- 条件语言状态 `NOT_FROZEN`。`when` 仍是示意，不是已选定的表达式语言
- 业务码：`00` → `REFUND_SUCCEEDED`，`12` → `ALREADY_REFUNDED`，其他 → `REFUND_FAILED`。`ALREADY_REFUNDED` 如何变成最终运行时结果仍开放
- `refund_order_no` 的演示拼接是 `original_order_no + appid`，状态为 `OPEN_QUESTION`
- seed-01 改为 `future_conformance_expectation`；新增 seed-02（高于阈值，`needs_review`，不执行）和 seed-03（金额不一致，`denied`，不执行）
- 开放问题增加 OQ-09、OQ-10、OQ-11

这些工作区内容是候选契约，不是 Owner 已接受的决定。

### Tested

工作区上的 8 个单元测试和仓库校验在本轮通过。它们锁定的是 JSON 和文档不变量，包括工作区里的金额、人工审核阈值、三枚 Seed 和“真实 Adapter 不得出现”。

它们没有：

- 执行策略求值
- 调用退款 Adapter
- 证明 seed-01 的 `executed` 已经发生
- 覆盖 HEAD `1.0.0` 单独仍能通过现在这套更严的测试

### Planned

`docs/inception/02-scope-and-non-goals.md` 把后续 Gate 标成需要单独批准：

| Gate | 候选结果 |
|------|----------|
| G1 | 内存中的参考求值器和轨迹引擎 |
| G2 | 持久化与并发控制 |
| G3 | 人工审核参考流程 |
| G4 | 外部 Adapter 接口 |
| G5 | 部署形态 |

OQ-03 的安全默认是 G1 先做库、不做服务器。这仍是默认，不是决定。

### Missing

- 运行时求值器
- 人工审核的认证与实现（OQ-08）
- 任何产品 UI
- 持久化、幂等存储、真实 Adapter
- 已冻结的策略条件语言
- 已接受的 Gate 0 退出记录

## 6. Core Business Rules

只写产品约束。退款规则是样例，用来说明控制面，不把本产品定义成退款系统。

### 控制面（HEAD 与工作区一致）

1. 模型输出是 Proposal。它不能写入可信上下文、权威事实、批准、幂等身份或 Adapter 结果。
2. 策略默认 `deny`。没有显式规则和测试，不得加宽松回退。
3. 同一组归一化输入，策略结果必须确定。
4. 执行前必须重校验，并先占用幂等。批准过期或状态变化则不执行。
5. 人工授权在需要时才出现；一个能定位案件的 token 不是批准。
6. Adapter 只接收执行所需的最少字段，不接收模型对话原文。
7. 传输成功、协议成功不等于业务成功。
8. 执行证据不能出现在授权和守卫证据之前。
9. 真实 Adapter 在 Gate 0 关闭。样例只允许合成夹具和 mock。
10. 示例邮箱使用 `.invalid`。仓库不放真实凭证、端点、客户或支付数据。
11. 开放问题不能靠写代码偷偷关掉。要记 ADR 或先改开放问题登记。

### 退款样例（规则意图在 HEAD；单位和字段集在工作区被收紧，尚未提交）

12. 只做全额退款。提案金额不等于权威原始金额时，结果是 `deny` / `full_refund_only`。
13. 高于样例阈值时，结果是 `needs_review` / `demo_amount_threshold`，并且不得调用 Adapter。
14. `allow_execution` 只表示有资格进入守卫。

工作区草案额外写明，Product Manager 不把它们当成已批准：

15. 货币是 CNY，金额只用整数分。`10000` 分等于 100 元，不是 10000 元。
16. 恰好 `10000` 分仍可能进入后续守卫；大于 `10000` 分必须人工审核。
17. `respCode = 12` 表示已经退过，不是一次新的退款成功。它的最终运行时结果还没定。

## 7. Decision & Execution Boundaries

仓库能够支持的结论只有这些。

### AI 可以决定什么

模型或界面可以提出意图和普通栏位，例如样例里的退款意图、订单定位字段和可选的申请金额。申请金额只用来和权威金额对照。

### AI 不能决定什么

不能决定主体、租户、应用、权威交易事实、策略版本、策略结果、批准人和批准状态、幂等键、执行令牌、Adapter 结果、最终结果。提示词不能放宽能力或改策略。

工作区草案还禁止模型提供原始金额、退款金额和 `respCode`。HEAD 的受保护字段名单里还没有这三项。

### 什么时候必须人介入

- 策略结果为 `needs_review` 时。退款样例里，这是金额高于演示阈值。
- 项目层：章程、范围、权威矩阵、策略语义、受保护字段、默认失败行为、新 Adapter、持久化、认证或人工审核机制，都要 Owner / ADR，不能由实现自行吸收。
- 连接生产、导入私有数据、部署、执行真实动作，各自需要明确的 Owner Gate。

`needs_input` 是补齐提案字段，不是人工批准。

### 谁拥有最终执行权

- 项目是否允许进入下一 Gate：Owner。
- 一次副作用是否可以发生：未来运行时，在策略允许、需要时的人工决定、重校验和幂等都完成后。今天没有这个运行时。
- 人工审核者如何被认证：未知。OQ-08 的安全默认是不实现批准。
- Maintainer 合并拉取请求：不是执行权，也不是部署权。

## 8. MVP Scope

这里的 MVP 是 Gate 0，不是一个可退款的产品。

### In Scope

- 领域中立的词汇和信任模型
- Policy 与 Demo Seed 的 JSON Schema
- 至少一个合成退款 Seed，用来表达受控动作和证据顺序
- 必须出现的审计事件顺序，以及禁止出现的执行事件
- Issue、ADR、PR、安全和公开发布的治理
- 无依赖的静态校验

工作区正在把范围里的“一个 Seed”扩成三条符合性向量，并把金额单位写死。这是否仍属于 Gate 0，要由 Owner 决定，不能由本草案宣布。

## 9. Out of Scope

### 明确不做

- 生产运行时、API 服务器、数据库、用户界面
- 真实支付或其他外部系统
- 密钥、端点、客户数据和运行手册
- 通用策略语言、通用工作流引擎、动态插件
- 合规或生产安全认证
- 把私有来源项目搬进本仓库

### Deferred

- G1 到 G5，见第 5 节
- 人工审核实现
- 真实 Adapter
- 证据留存的持久化策略（OQ-06 的默认是只在内存中放合成证据）
- `ALREADY_REFUNDED` 的最终结果映射
- 演示用退款单号的防碰撞方案

## 10. Acceptance Criteria

下列条目用来评审**这份草案是否把产品说清**。全部满足也不等于 Gate 0 退出，更不等于可以写运行时。

1. 读者能说出产品是控制面，退款只是合成样例。
2. 读者能指出模型可以填什么、不能填什么。
3. 读者能区分 `deny`、`needs_input`、`needs_review`、`allow_execution`，并且知道最后一个还不是执行。
4. 读者能看出 seed 里的 `executed` 是未来期望。本仓库没有执行退款。
5. 读者能看出 HEAD `1.0.0` 和工作区 `1.0.1` 草案不是同一份已接受契约。
6. 读者能说出人工审核何时出现，以及今天没有审核实现。
7. 读者不会从“测试通过”推出“可以上线或可以动真实资金”。

## 11. Product Gaps

1. **同一仓库里有两份退款契约。** HEAD 使用 `original_order_id` 和 8 个受保护字段；工作区改了提案字段、金额单位、业务码和三条 Seed。后续角色如果各读一份，会做出不同产品。
2. **`10000` 的单位在 HEAD 里没有货币对象。** 字段名叫 minor，但提交版本没有写明 `10000` 是 100 元还是别的数。工作区草案补上了，尚未接受。
3. **seed-01 在 HEAD 里写成 `executed`。** 没有 `future_conformance_expectation` 时，容易被当成已经跑通过。
4. **策略 `when` 不是可执行语言。** 工作区明确 `NOT_FROZEN`。HEAD 的 OQ-04 只把“精确匹配和数值比较”当作安全默认。
5. **人工审核是产品规则，但没有审核者。** 不能在 G1 里用模型文本代替。
6. **没有当前用户界面。** 缺的是契约是否被接受，不是缺页面。

## 12. Risks

- 把工作区未提交草案写成已经冻结的业务规则。
- 把 `10000` 理解成 10000 元，从而把人工审核阈值放大一百倍。
- 把 `allow_execution` 或 seed 的 `executed` 当成执行授权。
- 在字段名还分叉时开始写 G1，使求值器绑定错误的提案契约。
- 为了“完整产品”添加界面、服务器、真实退款连接或通用编排。
- 用本轮静态测试代替 Gate 0 退出勾选。那些勾选仍然是空的。
- 把私有来源的阈值或接口写回公开契约，当成生产事实。

## 13. Assumptions

- 本轮读到的未提交文件是 Owner 既有工作，代表进行中的契约修订，不代表已接受。
- 产品身份是控制面。退款规则只服务这一个演示域。
- `pyproject.toml` 写了 Apache-2.0，但 OQ-01 仍要求公开发布前由 Owner 确认。
- 仓库中不存在产品 UI。`src/` 只有包初始化和契约检查器。
- G1 及以后都还没有单独的实现简报。

## 14. Open Questions

以登记为准，本草案不关闭任何一条。

**HEAD 已登记：**

- OQ-01 公开许可证是否最终为 Apache-2.0
- OQ-02 公开安全联系人
- OQ-03 G1 是库、CLI，还是两者
- OQ-04 安全且可读的策略表达式子集
- OQ-05 策略 / schema 版本如何协商
- OQ-06 证据保留和脱敏
- OQ-07 插件 / Adapter 威胁模型
- OQ-08 人工审核者如何认证

**只出现在工作区，尚未进入 HEAD：**

- OQ-09 哪一种确定性条件语言被批准。在此之前不选 CEL、JSONLogic、Rego 或嵌入表达式
- OQ-10 演示退款单号如何避免拼接碰撞
- OQ-11 `ALREADY_REFUNDED` 如何映射为最终运行时结果

## 15. Owner Decisions Needed

1. Gate 0 退出项是否接受：章程、范围、权威矩阵、默认拒绝、seed-01，以及哪些开放问题继续延期。本地校验不能代替这些勾选。
2. 工作区里的契约修订是否作为候选替换 HEAD `1.0.0`：CNY 分、`10000` 分 = 100 元、扩展受保护字段、新的提案字段、`respCode` 映射、seed-02 和 seed-03。不接受之前，两份契约并存。
3. 在第 2 条决定前，后续 UX 或架构角色应以哪一份字段和金额语义为准。Product Manager 的建议是：先评审工作区草案，因为它明确挡住了“测试通过 = 已经退款”和“10000 的单位不清楚”；这只是建议。
4. 人工审核在 G1 之前是否继续保持“不实现”。OQ-08 的现默认是不实现。
5. G1 的产品表面是否维持“库优先、无服务器、无界面”。OQ-03 仍开放。

---

*Draft only. Not a Gate 0 exit. Not implementation authorization.*
