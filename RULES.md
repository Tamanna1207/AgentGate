# Myntra Agent Gatekeeper
**Enrolment Number:** PGD202564978

## AI Agent Policy & Action Rules

This policy governs AI agent operations covering the following actions: **view order**, **place order**, **return**, and **refund**.

- **Rule 1:** Revoked agents are always BLOCKED.
- **Rule 2:** Unknown/unregistered agents are always BLOCKED.
- **Rule 3:** Registered active agents requesting view order are ALLOWED.
- **Rule 4:** Registered active agents requesting place order with amount less than or equal to ₹2,500 are ALLOWED.
- **Rule 5:** Registered active agents requesting place order with amount greater than ₹2,500 require ASK CUSTOMER confirmation.
- **Rule 6:** Registered active agents requesting return or refund require ASK CUSTOMER confirmation regardless of amount.
- **Rule 7:** Any other invalid action is BLOCKED.

---

**Threshold Justification:** The ₹2,500 threshold was chosen because it covers routine fashion essentials (like t-shirts or casual footwear) without checkout friction while protecting customers from expensive accidental orders.
