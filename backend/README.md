# Ashu Backend

Python/FastAPI backend for the existing Ashu Next.js application. It uses Clerk as the single identity provider and Supabase for Postgres, private Storage, Realtime, and PGMQ queues.

> **Important integration status:** This is a runnable backend foundation with real API/service implementations and database migrations. Bhawanipur Digiicampus is deliberately **read-only and disabled by default** until its API routes, authentication method, and permission are verified against the actual tenant. Automatic assignment upload is represented by a disabled provider; it is not claimed to work yet.

## 1. What is included

- Clerk session-token verification for FastAPI (no second login flow).
- Supabase REST client that forwards the Clerk JWT for user-scoped RLS requests.
- Supabase migrations for profiles, courses, classroom modules, sessions, assignments, questions, events, materials, embeddings, documents, approvals, submissions, notifications, feed, calendar and sync logs.
- RLS policies using the Clerk JWT `sub` claim.
- Private Storage buckets and signed download URLs.
- Course/assignment normalizers and a configurable, read-only Digiicampus adapter.
- Idempotent assignment fingerprint/diff logic.
- Assignment list filters and dashboard aggregations.
- Gemini primary AI service and optional Groq text generation.
- PDF/DOCX extraction and generation.
- Study-material chunking and pgvector retrieval.
- Telegram Bot API and WhatsApp Business Platform clients.
- Student document approval tied to the exact document checksum.
- Handwritten/scanned assignment detection and scanned-PDF upload endpoint.
- PGMQ worker with retry visibility and a failure table.
- API tests for core normalization and processing utilities.

## 2. Requirements

- Python 3.11 or later (3.12 recommended).
- A Supabase project with Data API enabled, Clerk configured as a third-party auth provider, and PGMQ enabled.
- A Clerk application already integrated into the existing Next.js frontend with Google OAuth.
- Optional Gemini, Telegram and WhatsApp credentials.

## 3. Install (Windows PowerShell)

From this `backend` folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` with your own credentials. Never commit it.

On macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
```

## 4. Configure Clerk + Supabase

1. In Clerk, keep Google OAuth as the existing sign-in method. You do not need another login flow.
2. Configure Clerk's current **Connect with Supabase** integration and add Clerk under Supabase **Authentication → Third-Party Auth**.
3. Ensure the Clerk session JWT includes `role: authenticated` (use Clerk's supported Supabase connection setup; do not use the deprecated JWT-template approach).
4. In `.env`, set `CLERK_SECRET_KEY`, `CLERK_JWT_KEY`, and `CLERK_AUTHORIZED_PARTIES=http://localhost:3000`.
5. Set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `SUPABASE_SECRET_KEY`.
6. The API uses the Clerk JWT as `Authorization: Bearer ...` and the Supabase publishable key as `apikey`. The admin/worker client sends only the Supabase secret key in `apikey` and is never exposed to user requests.

Current official guides:

- Clerk Python backend verification: https://clerk.com/articles/how-to-add-authentication-to-a-python-backend
- Clerk + Supabase third-party authentication: https://supabase.com/docs/guides/auth/third-party/clerk
- Supabase API keys: https://supabase.com/docs/guides/getting-started/api-keys

## 5. Apply Supabase migrations

Install and log in to the Supabase CLI, then from the project root containing `supabase/`:

```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase db push
```

Alternatively, run `supabase/migrations/202611240001_initial_ashu.sql` in the Supabase SQL Editor. Review the migration before applying it to an existing database.

The migration creates the `vector` and `pgmq` extensions, user-owned tables, RLS policies, private buckets, a vector-search RPC, and a server-only queue enqueue RPC. If PGMQ is not enabled in your project, enable it in Supabase Integrations → Queues and re-run the relevant queue setup section.

For local Supabase, update `supabase/config.toml` with your actual Clerk instance domain.

## 6. Configure the Next.js frontend to call FastAPI

Set the backend base URL in your frontend environment, for example:

```env
NEXT_PUBLIC_ASHU_API_URL=http://localhost:8000/api/v1
```

When calling FastAPI, retrieve the current Clerk session token and send it on each request:

```ts
const token = await getToken();
const response = await fetch(`${process.env.NEXT_PUBLIC_ASHU_API_URL}/users/me`, {
  headers: { Authorization: `Bearer ${token}` },
});
```

Do not send the Clerk secret key or Supabase secret key to the browser.

## 7. Start the API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health/live
- Readiness: http://127.0.0.1:8000/health/ready
- OpenAPI docs (non-production only): http://127.0.0.1:8000/docs

`/health/ready` reports missing core configuration. Protected API endpoints require an actual Clerk session JWT.

## 8. Start the background worker

Set `SUPABASE_DATABASE_URL` to your Supabase Postgres connection string (use the pooler/direct connection settings shown by your Supabase project and require SSL).

In another terminal:

```bash
python scripts/run_worker.py
```

The worker consumes PGMQ messages. It is independent of the browser and API server.

To schedule periodic synchronization, enable `pg_cron` and run `supabase/cron_setup.sql` after applying the migration. The cron job enqueues a dispatch tick; the worker then creates per-integration sync jobs.

## 9. Digiicampus: do not enable until verified

The code uses a configurable adapter in `app/integrations/digiicampus/`. All endpoint path settings are blank and `DIGII_READONLY_ENABLED=false` by default. This is intentional.

Before enabling it:

1. Obtain written/official permission or an official supported student integration method from Bhawanipur/Digii.
2. Confirm the Bhawanipur tenant's endpoint paths, query parameters, response schema, pagination, and rate limits. The community Digii Campus MCP repository is a technical reference only; endpoint validation on another tenant is not proof for Bhawanipur.
3. Confirm the portal supports the documented `Auth-Token` mechanism for your tenant. Do not scrape browser cookies or harvest credentials.
4. Configure the verified endpoint paths and an authorized read-only credential server-side.
5. Keep `DIGII_READONLY_ENABLED=true` only after a successful read-only test.

The `.env.example` variable `DIGII_AUTH_TOKEN` is a **single-developer local test option only**. Do not use one shared token for a multi-student production service. Production should use a college-approved per-user OAuth/token exchange, encrypted per-user credentials, or another documented integration.

The adapter includes placeholder support for courses, assignments, details, modules, sessions, resources, feed, calendar and portal notifications. Missing paths raise a clear unavailable error. The code does not claim these operations have passed a live Bhawanipur test.

See `docs/DIGIICAMPUS_INTEGRATION.md`.

## 10. AI, documents and RAG

Set `GEMINI_API_KEY` to enable summaries, answer drafts, and embeddings. Default model is configured in `.env` as `GEMINI_MODEL`. The embedding implementation uses `gemini-embedding-001` at 768 dimensions, matching the migration's `vector(768)` column.

For optional text generation through Groq, set `GROQ_API_KEY` and `AI_PROVIDER=groq`. Structured JSON summary generation currently requires Gemini; keep `AI_PROVIDER=gemini` for summaries and RAG unless you extend the Groq structured-output adapter.

Document endpoints create PDF/DOCX documents in private Storage. If portal instructions contain `handwritten`, `hand written`, `hand-written`, `scanned copy`, or `write by hand`, the generated file is explicitly flagged as a printable draft. Upload the final scanned handwritten PDF through:

`POST /api/v1/documents/{document_id}/upload-handwritten-scan`

## 11. Telegram and WhatsApp

Telegram:

1. Create a bot through BotFather.
2. Set `TELEGRAM_BOT_TOKEN`.
3. In Ashu, save the user's chat ID using `POST /api/v1/integrations/telegram/connect`.
4. The student must start the bot before it can message them.
5. Test using `POST /api/v1/integrations/telegram/test`.

WhatsApp:

1. Configure the official WhatsApp Business Platform / Cloud API.
2. Set access token, phone-number ID and API version.
3. Save the recipient after consent.
4. Use an approved message template via `POST /api/v1/integrations/whatsapp/test?template_name=...`.

See official docs: https://core.telegram.org/bots/api and https://developers.facebook.com/documentation/business-messaging/whatsapp/overview/.

## 12. Automatic submission status

The `DigiicampusSubmissionProvider` deliberately raises `IntegrationUnavailable`. The public community connector documents read operations and does not demonstrate Bhawanipur academic assignment upload. The screenshots show that the portal has online submissions and past uploaded PDFs, but do not establish a programmable upload API.

The backend supports approval records, document checksums, submission tracking and a manual-submission fallback. Do not enable automatic upload until the institution provides/approves a mechanism and a controlled test verifies the exact assignment, uploaded file, and portal confirmation.

## 13. Useful endpoints

- `GET /api/v1/users/me`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/assignments`
- `POST /api/v1/integrations/digii/connect`
- `POST /api/v1/integrations/digii/test`
- `POST /api/v1/integrations/digii/sync`
- `POST /api/v1/ai/generate-summary`
- `POST /api/v1/ai/generate-answer`
- `POST /api/v1/materials/upload`
- `POST /api/v1/documents/generate`
- `GET /api/v1/notifications`
- `GET /api/v1/calendar/events`

Full endpoint details are in `docs/API_CONTRACT.md`.

## 14. Tests and lint

```bash
pytest -q
ruff check .
python -m compileall app scripts
```

Tests cover pure logic and normalization. Live Clerk, Supabase, Gemini, Telegram and Digiicampus integration tests require your own credentials and must be run in a controlled environment.

## 15. Known implementation boundaries

- No credentials were supplied with this project build; configure your own `.env`.
- No verified Bhawanipur API contract was supplied; the Digiicampus adapter is disabled by default.
- No assignment-upload API or institution approval was supplied; automatic upload is disabled.
- Queue scheduling requires PGMQ/pg_cron enabled in your Supabase project.
- For production multi-user Digiicampus integration, add an official per-user authorization flow. Do not deploy with one shared developer token.
- For production, add a distributed rate limiter/API gateway, monitoring/alerting, secret manager, backup plan and operational review.

