import os
import csv
import json
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, Response

app = Flask(__name__)

# Constants & Configuration
ENROLMENT_NUMBER = "PGD202564978"
AGENTS_FILE = os.path.join(os.path.dirname(__file__), "agents.json")
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.csv")

# Initialize Data Stores
def init_data():
    if not os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Customer", "Agent", "Action", "Amount", "Decision", "Rule"])

    if not os.path.exists(AGENTS_FILE):
        seed_agents = [
            {
                "id": "AGT-101",
                "customer": "Ananya Sharma",
                "agent_name": "FashionBot-Alpha",
                "status": "ACTIVE",
                "registered_at": "2026-11-19 10:30:00",
                "revoked_at": "-"
            },
            {
                "id": "AGT-102",
                "customer": "Rohan Mehta",
                "agent_name": "StyleScout-99",
                "status": "REVOKED",
                "registered_at": "2026-11-18 14:15:00",
                "revoked_at": "2026-11-19 09:20:15"
            }
        ]
        save_agents(seed_agents)

def load_agents():
    init_data()
    try:
        with open(AGENTS_FILE, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_agents(agents):
    with open(AGENTS_FILE, mode="w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2)

def find_agent(agent_name):
    agents = load_agents()
    clean_name = (agent_name or "").strip().lower()
    for ag in agents:
        if ag["agent_name"].strip().lower() == clean_name:
            return ag
    return None

def register_agent(customer, agent_name):
    agents = load_agents()
    clean_name = (agent_name or "").strip()
    clean_cust = (customer or "").strip()
    if not clean_name or not clean_cust:
        return False, "Customer Name and Agent Name are both required."

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ag in agents:
        if ag["agent_name"].strip().lower() == clean_name.lower():
            if ag["status"] == "ACTIVE":
                return False, f"Agent '{clean_name}' is already registered and ACTIVE."
            else:
                ag["status"] = "ACTIVE"
                ag["customer"] = clean_cust
                ag["registered_at"] = now_str
                ag["revoked_at"] = "-"
                save_agents(agents)
                return True, f"Agent '{clean_name}' re-activated with status ACTIVE."

    new_id = f"AGT-{len(agents) + 101}"
    new_agent = {
        "id": new_id,
        "customer": clean_cust,
        "agent_name": clean_name,
        "status": "ACTIVE",
        "registered_at": now_str,
        "revoked_at": "-"
    }
    agents.append(new_agent)
    save_agents(agents)
    return True, f"Agent '{clean_name}' registered successfully."

def revoke_agent(agent_id):
    agents = load_agents()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ag in agents:
        if ag["id"] == agent_id or ag["agent_name"].strip().lower() == agent_id.strip().lower():
            ag["status"] = "REVOKED"
            ag["revoked_at"] = now_str
            save_agents(agents)
            return True, f"Agent '{ag['agent_name']}' status changed to REVOKED at {now_str}."
    return False, "Agent not found."

def log_audit_request(customer, agent, action, amount, decision, rule):
    init_data()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    amt_str = f"₹{amount:,.2f}" if isinstance(amount, (int, float)) else str(amount)
    with open(AUDIT_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([now_str, customer, agent, action, amt_str, decision, rule])

def read_audit_logs():
    init_data()
    logs = []
    if not os.path.exists(AUDIT_LOG_FILE):
        return logs
    with open(AUDIT_LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    return list(reversed(logs))

# Policy Evaluation Engine adhering to RULES.md
def evaluate_request(customer_name, agent_name, action, amount_raw):
    clean_cust = (customer_name or "").strip()
    clean_agent = (agent_name or "").strip()
    clean_action = (action or "").strip().lower()

    # Parse amount
    try:
        amt = float(amount_raw) if amount_raw is not None and str(amount_raw).strip() != "" else 0.0
    except (ValueError, TypeError):
        amt = 0.0

    agent_record = find_agent(clean_agent)

    # Rule 1: Revoked agents are always BLOCKED.
    if agent_record and agent_record.get("status") == "REVOKED":
        decision = "BLOCK"
        rule = "Rule 1"
        badge = "block"
        reason = f"Revoked agent '{clean_agent}' is BLOCKED. All requests from revoked agents are strictly denied."
        log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
        return {
            "decision": decision,
            "rule": rule,
            "badge": badge,
            "reason": reason,
            "customer": clean_cust,
            "agent": clean_agent,
            "action": clean_action,
            "amount": amt
        }

    # Rule 2: Unknown/unregistered agents are always BLOCKED.
    if not agent_record:
        decision = "BLOCK"
        rule = "Rule 2"
        badge = "block"
        reason = f"Agent '{clean_agent}' is unknown or not registered. Unregistered agents are always BLOCKED."
        log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
        return {
            "decision": decision,
            "rule": rule,
            "badge": badge,
            "reason": reason,
            "customer": clean_cust,
            "agent": clean_agent,
            "action": clean_action,
            "amount": amt
        }

    # At this point, the agent is Registered and ACTIVE.
    # Rule 3: Registered active agents requesting view order are ALLOWED.
    if clean_action == "view order":
        decision = "ALLOW"
        rule = "Rule 3"
        badge = "allow"
        reason = f"Active agent '{clean_agent}' requested 'view order'. Read-only order view is ALLOWED."
        log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
        return {
            "decision": decision,
            "rule": rule,
            "badge": badge,
            "reason": reason,
            "customer": clean_cust,
            "agent": clean_agent,
            "action": clean_action,
            "amount": amt
        }

    # Rule 4 & Rule 5: place order
    if clean_action == "place order":
        # Rule 4: Registered active agents requesting place order with amount <= ₹3,000 are ALLOWED.
        if amt <= 3000.0:
            decision = "ALLOW"
            rule = "Rule 4"
            badge = "allow"
            reason = f"Order amount of ₹{amt:,.2f} is ≤ ₹2,500. Approved without checkout friction for routine fashion essentials."
            log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
            return {
                "decision": decision,
                "rule": rule,
                "badge": badge,
                "reason": reason,
                "customer": clean_cust,
                "agent": clean_agent,
                "action": clean_action,
                "amount": amt
            }
        else:
            # Rule 5: Registered active agents requesting place order with amount > ₹2,500 require ASK CUSTOMER confirmation.
            decision = "ASK CUSTOMER"
            rule = "Rule 5"
            badge = "ask"
            reason = f"Order amount of ₹{amt:,.2f} exceeds ₹2,500 threshold. Customer confirmation is REQUIRED to prevent accidental expensive purchases."
            log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
            return {
                "decision": decision,
                "rule": rule,
                "badge": badge,
                "reason": reason,
                "customer": clean_cust,
                "agent": clean_agent,
                "action": clean_action,
                "amount": amt
            }

    # Rule 6: Registered active agents requesting return or refund require ASK CUSTOMER confirmation regardless of amount.
    if clean_action in ["return", "refund"]:
        decision = "ASK CUSTOMER"
        rule = "Rule 6"
        badge = "ask"
        reason = f"Action '{clean_action}' requires customer confirmation regardless of order amount to protect user accounts and prevent unauthorized reversals."
        log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
        return {
            "decision": decision,
            "rule": rule,
            "badge": badge,
            "reason": reason,
            "customer": clean_cust,
            "agent": clean_agent,
            "action": clean_action,
            "amount": amt
        }

    # Rule 7: Any other invalid action is BLOCKED.
    decision = "BLOCK"
    rule = "Rule 7"
    badge = "block"
    reason = f"Action '{clean_action}' is invalid or unauthorized under gatekeeper policies. Request is BLOCKED."
    log_audit_request(clean_cust, clean_agent, clean_action, amt, decision, rule)
    return {
        "decision": decision,
        "rule": rule,
        "badge": badge,
        "reason": reason,
        "customer": clean_cust,
        "agent": clean_agent,
        "action": clean_action,
        "amount": amt
    }

# Embedded HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Myntra Agent Gatekeeper</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --myntra-pink: #ff3f6c;
            --myntra-pink-hover: #e02f5a;
            --myntra-pink-light: #fff0f3;
            --dark-slate: #282c3f;
            --dark-slate-darker: #1a1e2d;
            --slate-muted: #535766;
            --slate-light: #686b78;
            --bg-page: #f4f5f8;
            --bg-card: #ffffff;
            --border-color: #e2e4e9;
            --border-hover: #cfd2da;
            --color-allow-bg: #ecfdf5;
            --color-allow-border: #10b981;
            --color-allow-text: #065f46;
            --color-ask-bg: #fffbeb;
            --color-ask-border: #f59e0b;
            --color-ask-text: #92400e;
            --color-block-bg: #fef2f2;
            --color-block-border: #ef4444;
            --color-block-text: #991b1b;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 12px rgba(40,44,63,0.08);
            --shadow-lg: 0 10px 25px -5px rgba(40,44,63,0.12);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-page);
            color: var(--dark-slate);
            line-height: 1.5;
            padding-bottom: 60px;
        }

        /* Top Header */
        .site-header {
            background: linear-gradient(135deg, var(--dark-slate-darker) 0%, var(--dark-slate) 100%);
            color: #ffffff;
            padding: 20px 0;
            border-bottom: 4px solid var(--myntra-pink);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo-mark {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #ff3f6c 0%, #ff527b 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 24px;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(255, 63, 108, 0.4);
            letter-spacing: -1px;
        }

        .brand-title {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-subtitle {
            font-size: 13px;
            color: #b5b7c0;
            font-weight: 500;
            margin-top: 2px;
        }

        .enrolment-badge {
            background: rgba(255, 63, 108, 0.15);
            border: 1.5px solid var(--myntra-pink);
            padding: 8px 18px;
            border-radius: 30px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            backdrop-filter: blur(8px);
            box-shadow: 0 2px 10px rgba(255, 63, 108, 0.25);
        }

        .enrolment-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: #ff85a1;
            font-weight: 700;
        }

        .enrolment-number {
            font-family: 'JetBrains Mono', monospace;
            font-size: 17px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 1px;
        }

        /* Container */
        .main-container {
            max-width: 1280px;
            margin: 30px auto;
            padding: 0 24px;
            display: flex;
            flex-direction: column;
            gap: 30px;
        }

        /* Alert notifications */
        .toast-banner {
            padding: 12px 18px;
            border-radius: var(--radius-md);
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: var(--shadow-sm);
        }

        .toast-success {
            background-color: #ecfdf5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }

        .toast-error {
            background-color: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }

        /* Grid for Sections 1 & 2 */
        .sections-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
        }

        @media (max-width: 992px) {
            .sections-grid {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .card-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border-color);
            background-color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .card-header-title {
            font-size: 17px;
            font-weight: 700;
            color: var(--dark-slate);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-header-icon {
            color: var(--myntra-pink);
            font-size: 19px;
        }

        .section-tag {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 700;
            background: var(--myntra-pink-light);
            color: var(--myntra-pink);
            padding: 4px 10px;
            border-radius: 20px;
        }

        .card-body {
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            flex: 1;
        }

        /* Form elements */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .form-label {
            font-size: 13px;
            font-weight: 600;
            color: var(--slate-muted);
            display: flex;
            justify-content: space-between;
        }

        .form-control {
            width: 100%;
            padding: 10px 14px;
            font-size: 14px;
            font-family: inherit;
            border: 1.5px solid var(--border-color);
            border-radius: var(--radius-sm);
            background: #ffffff;
            color: var(--dark-slate);
            transition: all 0.2s ease;
        }

        .form-control:focus {
            outline: none;
            border-color: var(--myntra-pink);
            box-shadow: 0 0 0 3px rgba(255, 63, 108, 0.15);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 700;
            padding: 11px 20px;
            border-radius: var(--radius-sm);
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--myntra-pink) 0%, #ff527b 100%);
            color: #ffffff;
            box-shadow: 0 4px 10px rgba(255, 63, 108, 0.25);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #e02f5a 0%, #ff3f6c 100%);
            box-shadow: 0 6px 14px rgba(255, 63, 108, 0.35);
            transform: translateY(-1px);
        }

        .btn-danger {
            background-color: #ef4444;
            color: #ffffff;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            border-radius: 4px;
        }

        .btn-danger:hover {
            background-color: #dc2626;
            transform: translateY(-1px);
        }

        .btn-disabled {
            background-color: #e2e4e9;
            color: #9496a1;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            border-radius: 4px;
            cursor: not-allowed;
            border: none;
        }

        /* Preset simulation buttons */
        .presets-container {
            background: #fafbfc;
            border: 1px dashed var(--border-color);
            border-radius: var(--radius-md);
            padding: 14px;
        }

        .presets-title {
            font-size: 12px;
            font-weight: 700;
            color: var(--slate-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .presets-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .chip-btn {
            background: #ffffff;
            border: 1px solid var(--border-color);
            padding: 5px 11px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: var(--dark-slate);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .chip-btn:hover {
            border-color: var(--myntra-pink);
            color: var(--myntra-pink);
            background: var(--myntra-pink-light);
        }

        /* Decision Box Component */
        .decision-wrapper {
            margin-top: 10px;
        }

        .decision-box {
            border-radius: var(--radius-lg);
            padding: 24px;
            box-shadow: var(--shadow-lg);
            border-width: 2.5px;
            border-style: solid;
            position: relative;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .decision-allow {
            background: linear-gradient(145deg, #ecfdf5 0%, #f0fdf4 100%);
            border-color: var(--color-allow-border);
            color: var(--color-allow-text);
        }

        .decision-ask {
            background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 100%);
            border-color: var(--color-ask-border);
            color: var(--color-ask-text);
        }

        .decision-block {
            background: linear-gradient(145deg, #fef2f2 0%, #fee2e2 100%);
            border-color: var(--color-block-border);
            color: var(--color-block-text);
        }

        .decision-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .decision-badge-large {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .decision-rule-pill {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            font-family: 'JetBrains Mono', monospace;
        }

        .decision-allow .decision-rule-pill {
            background-color: #10b981;
            color: #ffffff;
        }

        .decision-ask .decision-rule-pill {
            background-color: #f59e0b;
            color: #ffffff;
        }

        .decision-block .decision-rule-pill {
            background-color: #ef4444;
            color: #ffffff;
        }

        .decision-reason {
            font-size: 15px;
            font-weight: 600;
            line-height: 1.5;
            margin-bottom: 16px;
        }

        .decision-meta {
            background: rgba(255, 255, 255, 0.7);
            border-radius: var(--radius-sm);
            padding: 12px 16px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            font-size: 13px;
            backdrop-filter: blur(4px);
        }

        .decision-meta-item strong {
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            opacity: 0.75;
            margin-bottom: 2px;
        }

        .threshold-callout {
            margin-top: 14px;
            padding: 10px 14px;
            background: rgba(255, 255, 255, 0.85);
            border-left: 3px solid var(--myntra-pink);
            border-radius: 4px;
            font-size: 12.5px;
            color: var(--dark-slate);
            line-height: 1.4;
        }

        /* Tables */
        .table-container {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
            text-align: left;
        }

        th {
            background-color: #f8f9fa;
            color: var(--slate-muted);
            font-weight: 700;
            font-size: 11.5px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            padding: 12px 16px;
            border-bottom: 1.5px solid var(--border-color);
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            color: var(--dark-slate);
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background-color: #fafbfc;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }

        .status-active {
            background-color: #ecfdf5;
            color: #059669;
            border: 1px solid #a7f3d0;
        }

        .status-active::before {
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #10b981;
        }

        .status-revoked {
            background-color: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }

        .status-revoked::before {
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #ef4444;
        }

        .tag-decision {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 11.5px;
        }

        .tag-allow {
            background-color: #ecfdf5;
            color: #059669;
        }

        .tag-ask {
            background-color: #fffbeb;
            color: #d97706;
        }

        .tag-block {
            background-color: #fef2f2;
            color: #dc2626;
        }

        .font-mono {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12.5px;
        }

        .empty-placeholder {
            text-align: center;
            padding: 30px;
            color: var(--slate-light);
            font-size: 14px;
        }

        /* Footer policy bar */
        .policy-footer {
            margin-top: 10px;
            background: #ffffff;
            border-radius: var(--radius-md);
            padding: 16px 20px;
            border: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            color: var(--slate-muted);
        }

        .policy-footer strong {
            color: var(--dark-slate);
        }

        .policy-icon {
            font-size: 20px;
            color: var(--myntra-pink);
        }
    </style>
</head>
<body>

    <!-- Header with prominent Enrolment Number -->
    <header class="site-header">
        <div class="header-container">
            <div class="header-brand">
                <div class="brand-logo-mark">M</div>
                <div>
                    <h1 class="brand-title">Myntra Agent Gatekeeper</h1>
                    <p class="brand-subtitle">Autonomous E-Commerce Policy Engine & Governance Gate</p>
                </div>
            </div>
            <div class="enrolment-badge">
                <span class="enrolment-label">Candidate Enrolment No.</span>
                <span class="enrolment-number">{{ enrolment_number }}</span>
            </div>
        </div>
    </header>

    <main class="main-container">

        <!-- Notification message -->
        {% if toast_msg %}
        <div class="toast-banner {{ 'toast-success' if toast_type == 'success' else 'toast-error' }}">
            <span>{{ '✓' if toast_type == 'success' else '⚠' }}</span>
            <span>{{ toast_msg }}</span>
        </div>
        {% endif %}

        <!-- Two-column Section: Registry & Simulator -->
        <div class="sections-grid">

            <!-- SECTION 1: Agent Registry -->
            <div class="card">
                <div class="card-header">
                    <div class="card-header-title">
                        <span class="card-header-icon">🛡️</span>
                        <span>Agent Registry</span>
                    </div>
                    <span class="section-tag">Section 1</span>
                </div>
                <div class="card-body">
                    <!-- Registration Form -->
                    <form action="{{ url_for('register_route') }}" method="POST">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div class="form-group">
                                <label class="form-label">Customer Name</label>
                                <input type="text" name="customer" class="form-control" placeholder="e.g. Priya Patel" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Agent Name</label>
                                <input type="text" name="agent_name" class="form-control" placeholder="e.g. MyntraBot-01" required>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width: 100%;">
                            + Register AI Agent
                        </button>
                    </form>

                    <!-- Registered Agents Table -->
                    <div style="margin-top: 10px;">
                        <h4 style="font-size: 13px; font-weight: 700; color: var(--slate-muted); text-transform: uppercase; margin-bottom: 10px;">
                            Registered Agents ({{ agents|length }})
                        </h4>
                        <div class="table-container" style="max-height: 280px; overflow-y: auto;">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Agent</th>
                                        <th>Customer</th>
                                        <th>Status</th>
                                        <th>Registered At</th>
                                        <th>Revoked At</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for ag in agents %}
                                    <tr>
                                        <td style="font-weight: 700;">{{ ag.agent_name }}</td>
                                        <td>{{ ag.customer }}</td>
                                        <td>
                                            <span class="status-badge {{ 'status-active' if ag.status == 'ACTIVE' else 'status-revoked' }}">
                                                {{ ag.status }}
                                            </span>
                                        </td>
                                        <td class="font-mono" style="font-size: 11.5px; color: var(--slate-muted);">{{ ag.registered_at }}</td>
                                        <td class="font-mono" style="font-size: 11.5px; color: var(--slate-muted);">{{ ag.revoked_at }}</td>
                                        <td>
                                            {% if ag.status == 'ACTIVE' %}
                                            <form action="{{ url_for('revoke_route', agent_id=ag.id) }}" method="POST" style="display:inline;">
                                                <button type="submit" class="btn btn-danger" onclick="return confirm('Revoke {{ ag.agent_name }}?');">
                                                    Revoke Agent
                                                </button>
                                            </form>
                                            {% else %}
                                            <button class="btn btn-disabled" disabled>Revoked</button>
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr>
                                        <td colspan="6" class="empty-placeholder">No agents registered yet.</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SECTION 2: Simulate Agent Request -->
            <div class="card">
                <div class="card-header">
                    <div class="card-header-title">
                        <span class="card-header-icon">⚡</span>
                        <span>Simulate Agent Request</span>
                    </div>
                    <span class="section-tag">Section 2</span>
                </div>
                <div class="card-body">
                    <!-- Quick Test Scenarios -->
                    <div class="presets-container">
                        <div class="presets-title">⚡ Quick Preset Test Scenarios:</div>
                        <div class="presets-chips">
                            <button type="button" class="chip-btn" onclick="setPreset('Ananya Sharma', 'FashionBot-Alpha', 'place order', '1500')">
                                Rule 4: Place Order ≤ ₹3,000 (ALLOW)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Ananya Sharma', 'FashionBot-Alpha', 'place order', '3999')">
                                Rule 5: Place Order &gt; ₹3,000 (ASK)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Ananya Sharma', 'FashionBot-Alpha', 'view order', '0')">
                                Rule 3: View Order (ALLOW)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Ananya Sharma', 'FashionBot-Alpha', 'return', '1200')">
                                Rule 6: Return (ASK)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Ananya Sharma', 'FashionBot-Alpha', 'refund', '2500')">
                                Rule 6: Refund (ASK)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Rohan Mehta', 'StyleScout-99', 'place order', '1200')">
                                Rule 1: Revoked Agent (BLOCK)
                            </button>
                            <button type="button" class="chip-btn" onclick="setPreset('Guest User', 'RogueBot-X', 'place order', '800')">
                                Rule 2: Unknown Agent (BLOCK)
                            </button>
                        </div>
                    </div>

                    <!-- Simulation Form -->
                    <form action="{{ url_for('simulate_route') }}" method="POST">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div class="form-group">
                                <label class="form-label">Customer Name</label>
                                <input type="text" id="sim_customer" name="customer" class="form-control" placeholder="Customer Name" value="{{ last_customer or 'Ananya Sharma' }}" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Agent Name</label>
                                <input type="text" id="sim_agent" name="agent_name" class="form-control" placeholder="Agent Name" value="{{ last_agent or 'FashionBot-Alpha' }}" required>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                            <div class="form-group">
                                <label class="form-label">Action</label>
                                <select id="sim_action" name="action" class="form-control" required>
                                    <option value="view order" {{ 'selected' if last_action == 'view order' else '' }}>view order</option>
                                    <option value="place order" {{ 'selected' if (last_action == 'place order' or not last_action) else '' }}>place order</option>
                                    <option value="return" {{ 'selected' if last_action == 'return' else '' }}>return</option>
                                    <option value="refund" {{ 'selected' if last_action == 'refund' else '' }}>refund</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Order Amount in INR (₹)</label>
                                <input type="number" id="sim_amount" name="amount" class="form-control" placeholder="e.g. 2500" step="0.01" min="0" value="{{ last_amount if last_amount is not none else '1500' }}">
                            </div>
                        </div>

                        <button type="submit" class="btn btn-primary" style="width: 100%;">
                            Evaluate Policy Decision & Simulate
                        </button>
                    </form>

                    <!-- Decision Box Display -->
                    {% if decision_result %}
                    <div class="decision-wrapper">
                        <div class="decision-box decision-{{ decision_result.badge }}">
                            <div class="decision-top">
                                <div class="decision-badge-large">
                                    {% if decision_result.decision == 'ALLOW' %}
                                        <span>✅</span> ALLOW
                                    {% elif decision_result.decision == 'ASK CUSTOMER' %}
                                        <span>⚠️</span> ASK CUSTOMER
                                    {% else %}
                                        <span>🚫</span> BLOCK
                                    {% endif %}
                                </div>
                                <div class="decision-rule-pill">{{ decision_result.rule }}</div>
                            </div>

                            <p class="decision-reason">{{ decision_result.reason }}</p>

                            <div class="decision-meta">
                                <div class="decision-meta-item">
                                    <strong>Customer</strong>
                                    <span>{{ decision_result.customer }}</span>
                                </div>
                                <div class="decision-meta-item">
                                    <strong>Agent</strong>
                                    <span>{{ decision_result.agent }}</span>
                                </div>
                                <div class="decision-meta-item">
                                    <strong>Action</strong>
                                    <span>{{ decision_result.action }}</span>
                                </div>
                                <div class="decision-meta-item">
                                    <strong>Amount</strong>
                                    <span class="font-mono">₹{{ "%.2f"|format(decision_result.amount) }}</span>
                                </div>
                            </div>

                            <div class="threshold-callout">
                                <strong>Policy Rationale:</strong> The <strong>₹2,500</strong> threshold covers routine fashion essentials (like t-shirts or casual footwear) without checkout friction while protecting customers from expensive accidental orders.
                            </div>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

        </div>

        <!-- SECTION 3: Live Audit Log -->
        <div class="card">
            <div class="card-header">
                <div class="card-header-title">
                    <span class="card-header-icon">📋</span>
                    <span>Live Audit Log</span>
                    <span style="font-size: 13px; font-weight: 500; color: var(--slate-muted); margin-left: 8px;">
                        (Persisted to audit_log.csv &bull; {{ audit_logs|length }} total events)
                    </span>
                </div>
                <a href="{{ url_for('download_audit_route') }}" class="btn btn-primary" style="padding: 6px 14px; font-size: 12px;">
                    ⬇ Download CSV
                </a>
            </div>
            <div class="card-body" style="padding: 0;">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Customer</th>
                                <th>Agent</th>
                                <th>Action</th>
                                <th>Amount</th>
                                <th>Decision</th>
                                <th>Rule</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in audit_logs %}
                            <tr>
                                <td class="font-mono" style="font-size: 12px; color: var(--slate-muted);">{{ log.Timestamp }}</td>
                                <td style="font-weight: 600;">{{ log.Customer }}</td>
                                <td class="font-mono" style="font-weight: 600;">{{ log.Agent }}</td>
                                <td>
                                    <span style="font-size: 12px; background: #f0f1f4; padding: 2px 7px; border-radius: 4px; font-weight: 600;">
                                        {{ log.Action }}
                                    </span>
                                </td>
                                <td class="font-mono">{{ log.Amount }}</td>
                                <td>
                                    {% if log.Decision == 'ALLOW' %}
                                    <span class="tag-decision tag-allow">ALLOW</span>
                                    {% elif log.Decision == 'ASK CUSTOMER' %}
                                    <span class="tag-decision tag-ask">ASK CUSTOMER</span>
                                    {% else %}
                                    <span class="tag-decision tag-block">BLOCK</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <strong style="font-family: 'JetBrains Mono', monospace; font-size: 12px;">{{ log.Rule }}</strong>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="7" class="empty-placeholder">No requests logged yet. Simulate a request above to generate audit logs.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Footer Rationale Callout -->
        <div class="policy-footer">
            <span class="policy-icon">ℹ️</span>
            <div>
                <strong>E-Commerce Policy Threshold Note:</strong> ₹2,500 was chosen because it covers routine fashion essentials (like t-shirts or casual footwear) without checkout friction while protecting customers from expensive accidental orders.
            </div>
        </div>

    </main>

    <script>
        function setPreset(cust, agent, action, amt) {
            document.getElementById('sim_customer').value = cust;
            document.getElementById('sim_agent').value = agent;
            document.getElementById('sim_action').value = action;
            document.getElementById('sim_amount').value = amt;
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    agents = load_agents()
    audit_logs = read_audit_logs()
    toast_msg = request.args.get("toast_msg")
    toast_type = request.args.get("toast_type", "success")
    return render_template_string(
        HTML_TEMPLATE,
        enrolment_number=ENROLMENT_NUMBER,
        agents=agents,
        audit_logs=audit_logs,
        decision_result=None,
        toast_msg=toast_msg,
        toast_type=toast_type,
        last_customer="",
        last_agent="",
        last_action="",
        last_amount=""
    )

@app.route("/register", methods=["POST"])
def register_route():
    customer = request.form.get("customer")
    agent_name = request.form.get("agent_name")
    success, msg = register_agent(customer, agent_name)
    toast_type = "success" if success else "error"
    return redirect(url_for("index", toast_msg=msg, toast_type=toast_type))

@app.route("/revoke/<agent_id>", methods=["POST"])
def revoke_route(agent_id):
    success, msg = revoke_agent(agent_id)
    toast_type = "success" if success else "error"
    return redirect(url_for("index", toast_msg=msg, toast_type=toast_type))

@app.route("/simulate", methods=["POST"])
def simulate_route():
    customer = request.form.get("customer")
    agent_name = request.form.get("agent_name")
    action = request.form.get("action")
    amount = request.form.get("amount")

    decision_result = evaluate_request(customer, agent_name, action, amount)
    agents = load_agents()
    audit_logs = read_audit_logs()

    return render_template_string(
        HTML_TEMPLATE,
        enrolment_number=ENROLMENT_NUMBER,
        agents=agents,
        audit_logs=audit_logs,
        decision_result=decision_result,
        toast_msg=f"Decision executed under {decision_result['rule']}: {decision_result['decision']}",
        toast_type="success",
        last_customer=customer,
        last_agent=agent_name,
        last_action=action,
        last_amount=amount
    )

@app.route("/download-audit")
def download_audit_route():
    init_data()
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            csv_content = f.read()
    else:
        csv_content = "Timestamp,Customer,Agent,Action,Amount,Decision,Rule\n"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=audit_log.csv"}
    )

if __name__ == "__main__":
    init_data()
    print(f"Myntra Agent Gatekeeper (Enrolment Number: {ENROLMENT_NUMBER})")
    print("Starting server at http://127.0.0.1:5000 ...")
    app.run(debug=True, host="0.0.0.0", port=5000)
