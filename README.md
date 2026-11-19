# Myntra Agent Gatekeeper

**Candidate Enrolment Number:** PGD202564978  
**System:** Autonomous E-Commerce AI Agent Governance Engine

---

## Overview

**Myntra Agent Gatekeeper** is an autonomous policy verification and control gateway designed for e-commerce AI agents. Built with Flask and styled in Myntra's signature pink (`#ff3f6c`) and dark slate (`#282c3f`), it enforces strict governance rules covering order placement, read access, returns, and refunds.

---

## Governance Rules Enforced (RULES.md)

| Rule # | Action / Condition | Evaluation Result | Policy Rationale |
| :--- | :--- | :--- | :--- |
| **Rule 1** | Any Revoked Agent | **BLOCK** (Red) | Revoked agents are permanently barred from performing any actions. |
| **Rule 2** | Unknown / Unregistered Agent | **BLOCK** (Red) | Unregistered or unrecognized agents are blocked by default. |
| **Rule 3** | Registered Active Agent + `view order` | **ALLOW** (Green) | Read-only order queries have no financial risk and are permitted. |
| **Rule 4** | Registered Active Agent + `place order` &le; &inr;2,500 | **ALLOW** (Green) | Routine fashion essentials (t-shirts, casual footwear) auto-approved without checkout friction. |
| **Rule 5** | Registered Active Agent + `place order` &gt; &inr;2,500 | **ASK CUSTOMER** (Yellow/Orange) | High-value orders require explicit customer confirmation to prevent accidental purchases. |
| **Rule 6** | Registered Active Agent + `return` or `refund` | **ASK CUSTOMER** (Yellow/Orange) | Reversals and returns mandate explicit customer consent regardless of transaction amount. |
| **Rule 7** | Any Invalid / Unknown Action | **BLOCK** (Red) | Any action outside permitted policy specifications is blocked. |

> **Threshold Rationale (&inr;2,500):** Chosen because it covers routine fashion essentials (like t-shirts or casual footwear) without checkout friction while protecting customers from expensive accidental orders.

---

## Features

1. **Prominent Header:** Highlights Enrolment Number `PGD202564978` in a glowing badge alongside Myntra branding.
2. **Section 1 - Agent Registry:**
   - Register an AI Agent with Customer Name and Agent Name.
   - Automatically assigns `ACTIVE` status and exact registration timestamp.
   - Interactive table with a red **Revoke Agent** button next to each active agent.
   - Revocation updates status to `REVOKED` and records the exact revocation timestamp.
3. **Section 2 - Simulate Agent Request:**
   - Form for Customer Name, Agent Name, Action dropdown (`view order`, `place order`, `return`, `refund`), and Order Amount in &inr;.
   - One-click **Quick Preset Scenario** chips to immediately test Rules 1 through 7.
   - **Large Colored Decision Box:**
     - **ALLOW** (Green gradient)
     - **ASK CUSTOMER** (Amber/Yellow gradient)
     - **BLOCK** (Red gradient)
     - Displays exact Rule Number and clear reason.
4. **Live Audit Log (`audit_log.csv`):**
   - Automatically logs all simulated requests (`Timestamp`, `Customer`, `Agent`, `Action`, `Amount`, `Decision`, `Rule`).
   - Displays a live table on the web interface with newest events first.
   - Includes a one-click CSV download button.

---

## Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Open in Browser
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.
