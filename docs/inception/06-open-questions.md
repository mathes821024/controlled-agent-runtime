# Open questions

| ID | Question | Blocks | Safe default |
|---|---|---|---|
| OQ-01 | Is Apache-2.0 the final public license? | First public release | Do not publish until Owner confirms |
| OQ-02 | What owner/security contact should public docs name? | Vulnerability reporting UX | Use GitHub private reporting only |
| OQ-03 | Should G1 expose a library API, CLI, or both? | G1 design | Library-first, no server |
| OQ-04 | What policy expression subset is safe and understandable? | G1 evaluator | Exact-match and numeric comparisons only |
| OQ-05 | How are policy/schema versions negotiated? | Compatibility promise | Reject unsupported versions |
| OQ-06 | What evidence retention and redaction rules apply? | Persistence | In-memory synthetic evidence only |
| OQ-07 | What is the threat model for plugins/adapters? | External adapters | No dynamic plugins |
| OQ-08 | What authenticates a human reviewer? | Human-review implementation | No approval implementation |

No open question may be resolved implicitly by code. Record the decision in an ADR
or update this register before implementation.

