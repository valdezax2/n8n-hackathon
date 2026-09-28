"""Generate fake CRM data (no external deps). Run: python seed.py [count]"""
import json
import random
import sys
import uuid
from datetime import datetime, timedelta

FIRST = ["James", "Maria", "Wei", "Aisha", "Carlos", "Priya", "Liam", "Sofia", "Noah", "Fatima",
         "Ethan", "Yuki", "Olivia", "Mateo", "Chloe", "Omar", "Emma", "Lucas", "Ava", "Diego",
         "Hannah", "Kwame", "Isabella", "Ravi", "Grace", "Andre", "Mia", "Tomás", "Zoe", "Samuel"]
LAST = ["Smith", "Garcia", "Chen", "Khan", "Rodriguez", "Patel", "Johnson", "Rossi", "Nguyen", "Ali",
        "Brown", "Tanaka", "Williams", "Lopez", "Martin", "Hassan", "Davis", "Silva", "Taylor", "Kim",
        "Okafor", "Müller", "Hernandez", "Sharma", "Wilson", "Dubois", "Anderson", "Reyes", "Clark", "Valdez"]
COMPANY_A = ["Blue", "Summit", "Nova", "Apex", "Green", "Iron", "Bright", "Silver", "North", "Quantum",
             "Pioneer", "Cedar", "Atlas", "Vertex", "Harbor"]
COMPANY_B = ["Logistics", "Health", "Analytics", "Foods", "Energy", "Software", "Retail", "Capital",
             "Robotics", "Media", "Manufacturing", "Labs", "Solutions", "Networks", "Partners"]
SUFFIX = ["Inc.", "LLC", "Group", "Co.", "Corp."]
INDUSTRY = {"Logistics": "Transportation", "Health": "Healthcare", "Analytics": "Technology",
            "Foods": "Food & Beverage", "Energy": "Energy", "Software": "Technology", "Retail": "Retail",
            "Capital": "Finance", "Robotics": "Manufacturing", "Media": "Media", "Manufacturing": "Manufacturing",
            "Labs": "Biotech", "Solutions": "Consulting", "Networks": "Telecom", "Partners": "Consulting"}
ROLES = ["CEO", "CTO", "CFO", "VP of Sales", "VP of Engineering", "Head of Marketing", "Operations Manager",
         "Procurement Lead", "IT Director", "Product Manager", "Office Manager", "Founder", "COO",
         "Customer Success Manager", "Head of Partnerships"]
STREETS = ["Main St", "Oak Ave", "Maple Dr", "Broadway", "Pine St", "Elm St", "Cedar Ln", "Lakeview Rd",
           "Market St", "Sunset Blvd", "2nd Ave", "Park Pl", "River Rd", "Highland Ave", "Washington St"]
CITIES = [("New York", "NY", "100"), ("Miami", "FL", "331"), ("Austin", "TX", "787"), ("Chicago", "IL", "606"),
          ("Seattle", "WA", "981"), ("Denver", "CO", "802"), ("Boston", "MA", "021"), ("Atlanta", "GA", "303"),
          ("San Francisco", "CA", "941"), ("Phoenix", "AZ", "850"), ("Nashville", "TN", "372"),
          ("Portland", "OR", "972")]
STATUSES = ["Lead", "Prospect", "Qualified", "Customer", "Churned"]
SOURCES = ["Website", "Referral", "LinkedIn", "Trade Show", "Cold Call", "Webinar", "Partner"]
TAGS = ["high-value", "decision-maker", "budget-approved", "needs-demo", "renewal", "at-risk",
        "upsell", "enterprise", "smb", "technical"]
CHANNELS = ["Phone", "Email", "Meeting", "Video Call", "Chat"]
SENTIMENT = ["positive", "neutral", "negative"]
TOPICS = [
    ("Intro call", "Discussed current workflow and pain points around {pain}. Interested in a follow-up demo."),
    ("Product demo", "Walked through the dashboard and reporting features. Asked about {pain} integration."),
    ("Pricing discussion", "Reviewed pricing tiers. Concerned about cost for {n} seats; requested a discount."),
    ("Contract negotiation", "Legal is reviewing the MSA. Pushback on the payment terms (net-60 requested)."),
    ("Support issue", "Reported a problem with {pain}. Escalated to support, ticket #{ticket}."),
    ("Quarterly check-in", "Usage is up {pct}% this quarter. Team is happy, exploring more seats."),
    ("Renewal", "Renewal due in {days} days. Wants to lock in current pricing for 2 years."),
    ("Follow-up", "Sent case study and ROI calculator. Waiting on feedback from their {dept} team."),
    ("Complaint", "Unhappy with response times on {pain}. Promised a call with the account manager."),
    ("Upsell", "Pitched the premium tier with advanced {pain} features. Will discuss internally."),
]
PAINS = ["data syncing", "invoicing", "onboarding", "reporting", "API access", "SSO", "inventory tracking",
         "customer support", "lead routing", "analytics"]
DEPTS = ["finance", "IT", "legal", "operations", "executive"]
REPS = ["Alex Rivera", "Jordan Lee", "Sam Patel", "Taylor Brooks"]


def fake_phone():
    return f"+1 ({random.randint(201, 989)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"


def fake_conversation(created):
    title, tmpl = random.choice(TOPICS)
    span_days = max((datetime.now() - created).days - 1, 1)
    day = created.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=random.randint(1, span_days))
    date = day + timedelta(hours=random.randint(8, 17), minutes=random.choice([0, 15, 30, 45]))
    return {
        "id": str(uuid.uuid4())[:8],
        "date": date.isoformat(timespec="minutes"),
        "channel": random.choice(CHANNELS),
        "subject": title,
        "summary": tmpl.format(pain=random.choice(PAINS), n=random.randint(5, 250), ticket=random.randint(1000, 9999),
                               pct=random.randint(5, 60), days=random.randint(10, 90), dept=random.choice(DEPTS)),
        "sentiment": random.choice(SENTIMENT),
        "rep": random.choice(REPS),
        "duration_min": random.randint(5, 60),
    }


def fake_contact(i):
    first, last = random.choice(FIRST), random.choice(LAST)
    a, b = random.choice(COMPANY_A), random.choice(COMPANY_B)
    company = f"{a} {b} {random.choice(SUFFIX)}"
    domain = f"{a}{b}".lower() + ".com"
    city, state, zip3 = random.choice(CITIES)
    created = datetime.now() - timedelta(days=random.randint(60, 900))
    convos = sorted((fake_conversation(created) for _ in range(random.randint(1, 8))), key=lambda c: c["date"], reverse=True)
    return {
        "id": i,
        "name": f"{first} {last}",
        "first_name": first,
        "last_name": last,
        "email": f"{first.lower()}.{last.lower()}@{domain}".replace("ü", "u").replace("á", "a"),
        "phone": fake_phone(),
        "mobile": fake_phone(),
        "role": random.choice(ROLES),
        "company": company,
        "industry": INDUSTRY[b],
        "company_size": random.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"]),
        "website": f"https://www.{domain}",
        "address": {
            "street": f"{random.randint(10, 9999)} {random.choice(STREETS)}",
            "city": city,
            "state": state,
            "zip": f"{zip3}{random.randint(10, 99)}",
            "country": "USA",
        },
        "status": random.choice(STATUSES),
        "lead_source": random.choice(SOURCES),
        "deal_value": random.choice([0, 0] + [random.randint(2, 250) * 1000 for _ in range(5)]),
        "owner": random.choice(REPS),
        "tags": random.sample(TAGS, random.randint(0, 3)),
        "linkedin": f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100, 999)}",
        "created_at": created.isoformat(timespec="seconds"),
        "last_contacted": convos[0]["date"],
        "notes": "",
        "conversations": convos,
    }


def generate(count=50, seed=42):
    random.seed(seed)
    return [fake_contact(i) for i in range(1, count + 1)]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    with open("data.json", "w") as f:
        json.dump(generate(n), f, indent=2, ensure_ascii=False)
    print(f"Wrote {n} contacts to data.json")
