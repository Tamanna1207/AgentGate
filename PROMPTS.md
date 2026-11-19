# Myntra Agent Gatekeeper — AI Prompts & Verification Log

**Candidate Enrolment Number:** PGD202564978  
**Project:** Myntra Agent Gatekeeper (Autonomous E-Commerce AI Agent Governance Engine)

---

## 1. AI Prompts Given to Coding Agent

This section documents the primary prompts provided to the AI coding agent to construct the policy framework and implement the full-stack Flask web application.

### Prompt 1: Policy Rules Generation (`RULES.md`)

> **Prompt:**  
> "Create a file named RULES.md in this folder for an e-commerce AI policy system called Myntra Agent Gatekeeper (Enrolment Number: PGD202564978. Write 7 clear rules covering these actions: view order, place order, return, and refund. Include:  
> - **Rule 1:** Revoked agents are always BLOCKED.  
> - **Rule 2:** Unknown/unregistered agents are always BLOCKED.  
> - **Rule 3:** Registered active agents requesting view order are ALLOWED.  
> - **Rule 4:** Registered active agents requesting place order with amount less than or equal to ₹2,500 are ALLOWED.  
> - **Rule 5:** Registered active agents requesting place order with amount greater than ₹2,500 require ASK CUSTOMER confirmation.  
> - **Rule 6:** Registered active agents requesting return or refund require ASK CUSTOMER confirmation regardless of amount.  
> - **Rule 7:** Any other invalid action is BLOCKED.  
> Add one line at the bottom explaining why ₹2,500 was chosen: it covers routine fashion essentials (like t-shirts or casual footwear) without checkout friction while protecting customers from expensive accidental orders."

---

### Prompt 2: Flask Web Application & Governance Engine (`app.py` & `requirements.txt`)

> **Prompt:**  
> "Build a clean, modern Python web app using Flask in a file called app.py (with an embedded HTML interface styled with Myntra's pink and dark slate colors) called 'Myntra Agent Gatekeeper'.  
> Requirements:  
> 1. Show my Enrolment Number 'PGD202564978' prominently in the header.  
> 2. Section 1 - Agent Registry: A form to register an AI agent (Customer Name, Agent Name) which saves it with status ACTIVE and registration timestamp. Show a table of registered agents with a red 'Revoke Agent' button next to each active agent. Clicking Revoke changes status to REVOKED and saves the exact Revocation Date & Time.  
> 3. Section 2 - Simulate Agent Request: A form with Customer Name, Agent Name, Action dropdown (view order, place order, return, refund), and Order Amount in INR (₹).  
> 4. Implement the exact 7 rules from RULES.md.  
> 5. When submitted, show a large colored decision box (Green for ALLOW, Yellow/Orange for ASK CUSTOMER, Red for BLOCK) displaying the exact Rule Number and clear reason.  
> 6. Save every single request to audit_log.csv (columns: Timestamp, Customer, Agent, Action, Amount, Decision, Rule) and display the live Audit Log table at the bottom of the page. Include requirements.txt with flask."

---

## 2. Manual Verification & Edits Made by Me

Following code generation, I conducted a manual code review, applied custom policy adjustments, and verified runtime behavior directly on the live server:

### A. Threshold Adjustment from ₹2,500 to ₹3,000
- **Python Backend (`app.py`):** I reviewed the evaluation logic in `evaluate_request()` and updated the auto-approval upper limit for Rule 4 from `amt <= 2500.0` to `amt <= 3000.0`. Orders up to ₹3,000 are now auto-approved, while orders strictly exceeding ₹3,000 trigger Rule 5 (`ASK CUSTOMER`).
- **HTML/UI Presentation (`app.py`):** I updated the preset button labels in the interface to reflect the new threshold:
  - Updated label to: `Rule 4: Place Order ≤ ₹3,000 (ALLOW)`
  - Updated label to: `Rule 5: Place Order > ₹3,000 (ASK)`
- **Targeted Scope / Presets Preserved:** I ensured that the `refund` test preset amount (`₹2,500`) was left completely intact (`setPreset('Ananya Sharma', 'FashionBot-Alpha', 'refund', '2500')`), confirming that refund/return requests remain strictly governed by Rule 6 regardless of the transaction figure.

### B. Agent Lifecycle & Revocation Verification (`ShopAssistAI`)
To thoroughly validate the agent state machine, registry persistence, and security enforcement:

1. **Registration:** Registered a new agent named `ShopAssistAI` for customer `Aarav`. The system saved it as `ACTIVE` with registration timestamp `2026-11-19 18:52:48` in `agents.json`.
2. **Active State Verification:**
   - Simulated `view order` $\rightarrow$ Evaluated as **ALLOW** under **Rule 3**.
   - Simulated `place order` of ₹1,200 ($\le$ ₹3,000) $\rightarrow$ Evaluated as **ALLOW** under **Rule 4**.
   - Simulated `place order` of ₹4,500 ($>$ ₹3,000) $\rightarrow$ Evaluated as **ASK CUSTOMER** under **Rule 5**.
   - Simulated `refund` of ₹999 $\rightarrow$ Evaluated as **ASK CUSTOMER** under **Rule 6**.
3. **Revocation Execution:** Clicked the red **Revoke Agent** button for `ShopAssistAI`. The system transitioned its status to `REVOKED` and permanently recorded the exact revocation timestamp (`2026-11-19 18:56:32`).
4. **Immediate Rule 1 Enforcement:** Dispatched a subsequent `view order` request for `ShopAssistAI`. The gatekeeper immediately blocked the call under **Rule 1** (`BLOCK`), displaying the large red decision box and logging the event to `audit_log.csv` (`2026-11-19 18:57:00,Aarav,ShopAssistAI,view order,₹0.00,BLOCK,Rule 1`).
