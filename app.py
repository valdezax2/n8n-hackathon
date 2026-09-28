"""Fake CRM with a web UI and a JSON REST API (for n8n HTTP Request nodes).

Run:  .venv/bin/python app.py   ->  http://localhost:5050
Optional auth: set API_KEY env var, then send header `X-API-Key: <key>`.
"""
import json
import os
import random
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

import seed

DATA_FILE = Path(__file__).with_name("data.json")
API_KEY = os.environ.get("API_KEY")
lock = threading.Lock()

app = Flask(__name__)
app.json.sort_keys = False


def load():
    if not DATA_FILE.exists():
        save(seed.generate(50))
    return json.loads(DATA_FILE.read_text())


def save(data):
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


contacts = load()


def find(cid):
    c = next((c for c in contacts if c["id"] == cid), None)
    if c is None:
        abort(404, description=f"Contact {cid} not found")
    return c


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    return resp


@app.before_request
def check_key():
    if request.method == "OPTIONS":
        return "", 204
    if API_KEY and request.path.startswith("/api/") and request.path != "/api":
        if request.headers.get("X-API-Key") != API_KEY and request.args.get("api_key") != API_KEY:
            return jsonify(error="Invalid or missing API key"), 401


@app.errorhandler(404)
@app.errorhandler(400)
def err(e):
    if request.path.startswith("/api"):
        return jsonify(error=e.description), e.code
    return e


# ---------- UI ----------
@app.get("/")
def index():
    return render_template("index.html")


# ---------- API ----------
@app.get("/api")
def api_index():
    return jsonify(
        name="Fake CRM API",
        auth="X-API-Key header" if API_KEY else "none",
        endpoints={
            "GET /api/contacts": "list; query: q, status, company, role, owner, tag, email, phone, sort, order, limit, offset, include_conversations",
            "GET /api/contacts/<id>": "one contact incl. conversations",
            "POST /api/contacts": "create (JSON body); missing fields are faked",
            "PATCH /api/contacts/<id>": "update fields",
            "DELETE /api/contacts/<id>": "delete",
            "GET /api/contacts/<id>/conversations": "list conversations",
            "POST /api/contacts/<id>/conversations": "log a conversation {channel, subject, summary, sentiment, rep}",
            "GET /api/contacts/random": "one random contact",
            "GET /api/companies": "companies with contact counts",
            "GET /api/stats": "pipeline stats",
            "POST /api/generate": "regenerate data {count, seed, append}",
        },
    )


@app.get("/api/contacts")
def list_contacts():
    a = request.args
    res = contacts
    if q := a.get("q", "").lower():
        res = [c for c in res if q in f'{c["name"]} {c["email"]} {c["company"]} {c["role"]} {c["address"]["city"]}'.lower()]
    for field in ("status", "company", "role", "owner", "industry"):
        if v := a.get(field):
            res = [c for c in res if c[field].lower() == v.lower()]
    if tag := a.get("tag"):
        res = [c for c in res if tag in c["tags"]]
    if email := a.get("email"):
        res = [c for c in res if c["email"].lower() == email.lower()]
    if phone := "".join(ch for ch in a.get("phone", "") if ch.isdigit())[-10:]:
        digits = lambda s: "".join(ch for ch in s if ch.isdigit())
        res = [c for c in res if digits(c["phone"]).endswith(phone) or digits(c["mobile"]).endswith(phone)]
    sort = a.get("sort", "id")
    if res and sort in res[0]:
        res = sorted(res, key=lambda c: c[sort], reverse=a.get("order") == "desc")
    total = len(res)
    offset = int(a.get("offset", 0))
    limit = int(a.get("limit", 100))
    res = res[offset: offset + limit]
    if a.get("include_conversations", "true").lower() == "false":
        res = [{k: v for k, v in c.items() if k != "conversations"} for c in res]
    return jsonify(total=total, offset=offset, limit=limit, data=res)


@app.get("/api/contacts/random")
def random_contact():
    return jsonify(random.choice(contacts))


@app.get("/api/contacts/<int:cid>")
def get_contact(cid):
    return jsonify(find(cid))


@app.post("/api/contacts")
def create_contact():
    body = request.get_json(silent=True) or {}
    with lock:
        new_id = max((c["id"] for c in contacts), default=0) + 1
        c = seed.fake_contact(new_id)
        for k, v in body.items():
            if k != "id" and k in c:
                c[k] = {**c[k], **v} if isinstance(c[k], dict) and isinstance(v, dict) else v
        if "name" in body and "email" not in body:
            c["first_name"], _, c["last_name"] = body["name"].partition(" ")
        contacts.append(c)
        save(contacts)
    return jsonify(c), 201


@app.route("/api/contacts/<int:cid>", methods=["PATCH", "PUT"])
def update_contact(cid):
    body = request.get_json(silent=True) or {}
    with lock:
        c = find(cid)
        for k, v in body.items():
            if k != "id" and k in c:
                c[k] = {**c[k], **v} if isinstance(c[k], dict) and isinstance(v, dict) else v
        save(contacts)
    return jsonify(c)


@app.delete("/api/contacts/<int:cid>")
def delete_contact(cid):
    with lock:
        c = find(cid)
        contacts.remove(c)
        save(contacts)
    return jsonify(deleted=cid)


@app.get("/api/contacts/<int:cid>/conversations")
def list_convos(cid):
    return jsonify(find(cid)["conversations"])


@app.post("/api/contacts/<int:cid>/conversations")
def add_convo(cid):
    body = request.get_json(silent=True) or {}
    if not body.get("summary"):
        abort(400, description="'summary' is required")
    with lock:
        c = find(cid)
        convo = {
            "id": str(uuid.uuid4())[:8],
            "date": body.get("date") or datetime.now().isoformat(timespec="minutes"),
            "channel": body.get("channel", "Email"),
            "subject": body.get("subject", "Follow-up"),
            "summary": body["summary"],
            "sentiment": body.get("sentiment", "neutral"),
            "rep": body.get("rep", c["owner"]),
            "duration_min": body.get("duration_min", 0),
        }
        c["conversations"].insert(0, convo)
        c["conversations"].sort(key=lambda x: x["date"], reverse=True)
        c["last_contacted"] = c["conversations"][0]["date"]
        save(contacts)
    return jsonify(convo), 201


@app.get("/api/companies")
def companies():
    out = {}
    for c in contacts:
        co = out.setdefault(c["company"], {"company": c["company"], "industry": c["industry"],
                                            "website": c["website"], "contacts": 0, "pipeline_value": 0})
        co["contacts"] += 1
        co["pipeline_value"] += c["deal_value"]
    return jsonify(sorted(out.values(), key=lambda x: -x["pipeline_value"]))


@app.get("/api/stats")
def stats():
    by_status = {}
    for c in contacts:
        s = by_status.setdefault(c["status"], {"count": 0, "value": 0})
        s["count"] += 1
        s["value"] += c["deal_value"]
    return jsonify(
        contacts=len(contacts),
        conversations=sum(len(c["conversations"]) for c in contacts),
        pipeline_value=sum(c["deal_value"] for c in contacts),
        by_status=by_status,
    )


@app.post("/api/generate")
def regenerate():
    global contacts
    body = request.get_json(silent=True) or {}
    count = max(1, min(int(body.get("count", 50)), 5000))
    with lock:
        new = seed.generate(count, body.get("seed", random.randint(0, 10**6)))
        if body.get("append"):
            start = max((c["id"] for c in contacts), default=0)
            for i, c in enumerate(new, 1):
                c["id"] = start + i
            contacts.extend(new)
        else:
            contacts = new
        save(contacts)
    return jsonify(total=len(contacts))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=os.environ.get("FLASK_DEBUG") == "1")
