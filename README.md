# Fake CRM for n8n

A small Flask app that serves a fake CRM: a web UI plus a JSON REST API full of generated contacts, companies and conversation history. It's meant as a target for n8n HTTP Request nodes during the hackathon.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Open http://localhost:5050 for the UI, or http://localhost:5050/api for the endpoint list.

On first run, if `data.json` doesn't exist, 50 contacts are generated and saved there. All API writes are persisted to the same file.

## Configuration

| Env var       | Default | Purpose                                                        |
|---------------|---------|----------------------------------------------------------------|
| `PORT`        | `5050`  | Port to listen on                                              |
| `API_KEY`     | unset   | When set, `/api/*` requires `X-API-Key: <key>` (or `?api_key=`) |
| `FLASK_DEBUG` | unset   | Set to `1` to enable Flask debug mode                          |

CORS is open to all origins.

## API

| Method | Path                                  | Description |
|--------|---------------------------------------|-------------|
| GET    | `/api`                                | API info and endpoint list (never requires a key) |
| GET    | `/api/contacts`                       | List contacts (filters below) |
| GET    | `/api/contacts/<id>`                  | One contact, including conversations |
| GET    | `/api/contacts/random`                | One random contact |
| POST   | `/api/contacts`                       | Create a contact; any fields you omit are faked |
| PATCH/PUT | `/api/contacts/<id>`               | Update fields (nested objects like `address` are merged) |
| DELETE | `/api/contacts/<id>`                  | Delete a contact |
| GET    | `/api/contacts/<id>/conversations`    | List a contact's conversations |
| POST   | `/api/contacts/<id>/conversations`    | Log a conversation: `{summary, channel, subject, sentiment, rep, date, duration_min}` (`summary` required) |
| GET    | `/api/companies`                      | Companies with contact counts and pipeline value |
| GET    | `/api/stats`                          | Pipeline stats by status |
| POST   | `/api/generate`                       | Regenerate data: `{count, seed, append}` (count 1–5000) |

### Filtering `/api/contacts`

- `q`: free-text search over name, email, company, role and city
- `status`, `company`, `role`, `owner`, `industry`: exact match, case-insensitive
- `tag`, `email`: exact match
- `phone`: matches on the last 10 digits of phone or mobile
- `sort` (any field, default `id`), `order=desc`
- `limit` (default 100), `offset` (default 0)
- `include_conversations=false` to drop conversation history from the list

Responses are shaped as `{total, offset, limit, data: [...]}`.

### Examples

```bash
curl "http://localhost:5050/api/contacts?status=Customer&limit=5&include_conversations=false"

curl -X POST http://localhost:5050/api/contacts \
  -H "Content-Type: application/json" \
  -d '{"name": "Ada Lovelace", "company": "Analytical Engines Inc."}'

curl -X POST http://localhost:5050/api/contacts/1/conversations \
  -H "Content-Type: application/json" \
  -d '{"summary": "Asked for a demo next week", "channel": "Phone", "sentiment": "positive"}'
```

## Using it from n8n

In an **HTTP Request** node, set the URL to `http://localhost:5050/api/...`. If n8n runs in Docker, use `http://host.docker.internal:5050` instead. If `API_KEY` is set, add a header `X-API-Key` with the key.

## Files

- `app.py`: Flask app (UI and API)
- `seed.py`: fake data generator with no external dependencies (`python seed.py [count]`)
- `templates/`: Jinja templates for the UI
- `data.json`: generated data store, created on first run
- `requirements.txt`: Python dependencies
- `.devcontainer/`: Codespaces config that installs deps, starts the app and makes port 5050 public
