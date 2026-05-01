# HackerRank Orchestrate — Support Triage Agent

A terminal-based AI agent that automatically triages support tickets
for HackerRank, Claude, and Visa using only the local support corpus.

## How it works

1. Reads tickets from `support_tickets/support_tickets.csv`
2. Classifies each ticket (`request_type`, `product_area`)
3. Decides whether to `reply` or `escalate`
4. Finds relevant answer from local `data/` docs (no internet used)
5. Writes results to `support_tickets/output.csv`

## Setup

Python 3.7+ required. No external dependencies — uses only standard library.

```bash
# Clone the repo
git clone git@github.com:<your-username>/hackerrank-orchestrate-may26.git
cd hackerrank-orchestrate-may26
```

## Run

```bash
python code/main.py
```

Output will be saved to `support_tickets/output.csv`.

## Output columns

| Column | Values |
|---|---|
| `status` | `replied`, `escalated` |
| `product_area` | support domain (e.g. Billing, Fraud & Security) |
| `response` | user-facing answer grounded in local corpus |
| `justification` | why this routing decision was made |
| `request_type` | `product_issue`, `feature_request`, `bug`, `invalid` |

## Escalation rules

Tickets are escalated when they involve:
- Billing, refunds, or order IDs
- Fraud, identity theft, or unauthorized access
- Account access or workspace recovery
- Requests outside support scope (invalid)