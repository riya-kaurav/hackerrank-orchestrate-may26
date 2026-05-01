# code/main.py

import csv
import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TICKETS_PATH = os.path.join(BASE_DIR, "support_tickets", "support_tickets.csv")

# ── Step 1: Read and print every ticket ────────────────────────────────
def load_tickets(path):
    tickets = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickets.append(row)
    return tickets

# ── Step 2: Classify tickets ───────────────────────────────────────────

def classify_request_type(issue_text):
    text = issue_text.lower()

    # Invalid = asking for something clearly outside support scope
    invalid_keywords = ["increase my score", "tell the company", "ban the seller", 
                        "move me to the next round", "review my answers"]
    for kw in invalid_keywords:
        if kw in text:
            return "invalid"

    # Bug = something broken / stopped working
    bug_keywords = ["stopped", "not working", "broke", "error", "crash", "failed", "interruped"]
    for kw in bug_keywords:
        if kw in text:
            return "bug"

    # Feature request = asking for new capability
    feature_keywords = ["add", "would be great", "suggest", "feature", "allow", "support for"]
    for kw in feature_keywords:
        if kw in text:
            return "feature_request"

    # Default: general product issue
    return "product_issue"


def classify_product_area(issue_text, company):
    text = issue_text.lower()
    company = company.lower()

    if company == "claude":
        if any(kw in text for kw in ["workspace", "seat", "admin", "access", "team"]):
            return "Team & Access Management"
        if any(kw in text for kw in ["billing", "payment", "charge", "refund", "subscription"]):
            return "Billing"
        return "General Support"

    if company == "hackerrank":
        if any(kw in text for kw in ["test", "score", "graded", "assessment", "answers"]):
            return "Assessments & Scoring"
        if any(kw in text for kw in ["interview", "mock", "session"]):
            return "Interviews"
        if any(kw in text for kw in ["payment", "refund", "order", "billing"]):
            return "Billing"
        return "General Support"

    if company == "visa":
        if any(kw in text for kw in ["refund", "merchant", "wrong product", "dispute", "chargeback"]):
            return "Dispute & Chargeback"
        if any(kw in text for kw in ["fraud", "unauthorized", "stolen", "blocked"]):
            return "Fraud & Security"
        if any(kw in text for kw in ["payment", "transaction", "charge"]):
            return "Payments"
        return "General Support"

    return "General Support"


# ── Step 3: Decide status ──────────────────────────────────────────────

ESCALATE_KEYWORDS = [
    "fraud", "unauthorized", "stolen", "dispute", "chargeback",
    "restore my access", "lost access", "account locked", "ban",
    "override", "tell the company", "increase my score",
    "move me to the next round", "refund", "order id"
]

def decide_status(issue_text, request_type):
    text = issue_text.lower()

    # Always escalate invalid requests
    if request_type == "invalid":
        return "escalated"

    # Escalate if sensitive keywords found
    for kw in ESCALATE_KEYWORDS:
        if kw in text:
            return "escalated"

    return "replied"

# ── Step 4: Load support docs from data/ ──────────────────────────────

DATA_DIR = os.path.join(BASE_DIR, "data")

def load_docs(data_dir):
    docs = []
    for root, dirs, files in os.walk(data_dir):  # ← os.walk recurses automatically
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Figure out which company from the path
                rel_path = os.path.relpath(filepath, data_dir)
                company  = rel_path.split(os.sep)[0]  # first folder = company name

                docs.append({
                    "company":  company,
                    "filename": filename,
                    "content":  content
                })
            except Exception as e:
                print(f"  [WARN] Could not read {filepath}: {e}")
    return docs

# ── Step 5: Generate response and justification ────────────────────────

def generate_response(status, request_type, product_area, company, issue, context):
    company = company if (company and str(company).strip() not in ("None", "")) else "Support"
    
    # ── Escalated tickets ──────────────────────────────────────────────
    if status == "escalated":
        if request_type == "invalid":
            return (
                f"Thank you for reaching out. Unfortunately, this request falls outside "
                f"what {company} support is able to action. We are unable to override "
                f"third-party decisions, intervene with external merchants, or modify "
                f"platform outcomes on your behalf. Please review our support policies "
                f"for further guidance.",
                "Request classified as invalid — asks for actions outside support scope "
                f"(e.g. overriding recruiter decisions, banning merchants, restoring "
                f"unauthorised access). Escalated per policy."
            )
        else:
            return (
                f"Thank you for contacting {company} support. Your case has been escalated "
                f"to our specialist team who will review it shortly. Please do not share "
                f"sensitive account details over this channel. A support agent will follow "
                f"up with you directly.",
                f"Issue involves a sensitive area ({product_area}) such as billing, fraud, "
                f"account access, or identity. Escalated to human agent for secure handling."
            )

    # ── Replied tickets — use context from docs ────────────────────────
    if context:
        # Pull first 300 chars of doc as grounded snippet
        lines = [l for l in context.splitlines() if not l.startswith("---") and not l.startswith("title:")]
        snippet = " ".join(lines)[:300].strip()
        return (
            f"Thank you for reaching out to {company} support regarding {product_area}. "
            f"Based on our documentation: {snippet}... "
            f"If this does not resolve your issue, please provide more details and we "
            f"will assist you further.",
            f"Issue matched to {product_area} documentation. Response grounded in local "
            f"support corpus. No sensitive data detected — safe to reply directly."
        )
    else:
        return (
            f"Thank you for contacting our support team. We received your message about "
            f"{product_area}. Could you please provide more details about the issue so "
            f"we can assist you better?",
            "No matching documentation found for this ticket. Requested clarification "
            "from user rather than guessing."
        )

# ── Step 6: Write output.csv ───────────────────────────────────────────

OUTPUT_PATH = os.path.join(BASE_DIR, "support_tickets", "output.csv")

def save_output(results, path):
    fieldnames = ["status", "product_area", "response", "justification", "request_type"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n Saved {len(results)} rows to {path}")

def find_relevant_doc(query, company, docs):
    """
    Returns the content of the best matching doc for this company.
    Simple scoring: count how many query words appear in the doc.
    """
    query_words = set(query.lower().split())
    company_lower = company.lower()

    best_doc   = None
    best_score = 0

    for doc in docs:
        if doc["company"].lower() != company_lower:
            continue                        # only search same company's docs

        doc_text = doc["content"].lower()
        score = sum(1 for word in query_words if word in doc_text)

        if score > best_score:
            best_score = score
            best_doc   = doc

    if best_doc:
        return best_doc["content"][:1500]   # return first 1500 chars as context
    return None


def main():
    tickets = load_tickets(TICKETS_PATH)
    docs    = load_docs(DATA_DIR) 
    print(f"Loaded {len(tickets)} tickets, {len(docs)} support docs\n")
    print("=" * 60)

    results = []

    for i, ticket in enumerate(tickets, start=1):
        issue   = ticket["Issue"]
        subject = ticket["Subject"]
        company = ticket["Company"]

        request_type = classify_request_type(issue)
        product_area = classify_product_area(issue, company)
        status       = decide_status(issue, request_type) 
        context      = find_relevant_doc(issue, company, docs)
        response, justification = generate_response(   # ← add this
            status, request_type, product_area, company, issue, context
        )

        
        print(f"Ticket #{i} | {company} | {status} | {request_type}")
        print(f"  {response[:100]}...")
        print("-" * 60)

        results.append({                # ← collect each row
            "status":        status,
            "product_area":  product_area,
            "response":      response,
            "justification": justification,
            "request_type":  request_type,
        })

    save_output(results, OUTPUT_PATH)     

if __name__ == "__main__":
    main()