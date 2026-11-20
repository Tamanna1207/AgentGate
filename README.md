# Myntra Agent Gatekeeper

**Enrolment Number:** PGD202564978  
**Project:** Autonomous E-Commerce AI Agent Governance Prototype

---

## Overview

**Myntra Agent Gatekeeper** is a Flask-based security and policy prototype that governs AI agents operating on behalf of e-commerce customers. It enforces strict real-time access controls across four primary operations: **view order**, **place order**, **return**, and **refund**.

Key capabilities include:
- **Agent Registry:** Register customer AI agents (`ACTIVE`), view timestamps, and revoke agents with recorded revocation dates and times.
- **Request Simulator:** Test requests against gatekeeper policies, showing an instant colored decision box (**ALLOW** in green, **ASK CUSTOMER** in yellow/orange, **BLOCK** in red) along with the exact rule number and rationale.
- **Live Audit Log:** Persists every single transaction to `audit_log.csv` and displays a real-time table in the web interface.

---

## 7 Policy Rules Summary

- **Rule 1:** Revoked agents are always **BLOCKED**.
- **Rule 2:** Unknown/unregistered agents are always **BLOCKED**.
- **Rule 3:** Registered active agents requesting `view order` are **ALLOWED**.
- **Rule 4:** Registered active agents requesting `place order` $\le$ threshold (₹2,500 / ₹3,000) are **ALLOWED**.
- **Rule 5:** Registered active agents requesting `place order` $>$ threshold require **ASK CUSTOMER** confirmation.
- **Rule 6:** Registered active agents requesting `return` or `refund` require **ASK CUSTOMER** confirmation regardless of amount.
- **Rule 7:** Any other invalid action is **BLOCKED**.

---

## Step-by-Step Instructions

### Step 1: Install Flask
```bash
pip install flask
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open in Web Browser
Navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

Submitted by: Tamanna Gandhi (PGD202564978) - 20 Nov 2026
