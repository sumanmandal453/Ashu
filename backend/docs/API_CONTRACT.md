# Ashu API Contract (v1)

Base path: `/api/v1`. All routes except `/webhooks/clerk` require `Authorization: Bearer <Clerk session JWT>`.

Success response:

```json
{"success": true, "data": {}, "message": "OK"}
```

Paginated response:

```json
{"success": true, "data": [], "pagination": {"page": 1, "page_size": 20, "total": 0, "total_pages": 0}}
```

## Identity and profile

| Method | Path | Purpose |
|---|---|---|
| GET | `/users/me` | Verify current Clerk identity |
| GET | `/users/profile` | Current profile |
| PATCH | `/users/profile` | Update editable profile fields |

## Dashboard

| Method | Path | Purpose |
|---|---|---|
| GET | `/dashboard/summary` | Assignment status counters |
| GET | `/dashboard/upcoming-deadlines` | Next deadlines |
| GET | `/dashboard/recent-activity` | Assignment events |
| GET | `/dashboard/completed-per-week` | Verified submission records (raw records in this first version) |
| GET | `/dashboard/assignments-by-subject` | Subject distribution |

## Courses and subjects

| Method | Path | Purpose |
|---|---|---|
| GET | `/subjects` | Student subjects |
| GET | `/courses` | Student courses |
| GET | `/courses/{course_id}` | Course detail |
| GET | `/courses/{course_id}/modules` | Course modules |
| GET | `/courses/{course_id}/sessions` | Course sessions |
| GET | `/courses/{course_id}/resources` | Course resources and signed local URLs |

## Assignments

| Method | Path | Purpose |
|---|---|---|
| GET | `/assignments` | Filter/search/sort/paginate assignments |
| POST | `/assignments` | Create a manually entered assignment |
| GET | `/assignments/{id}` | Assignment details |
| PATCH | `/assignments/{id}` | Edit permitted student workflow fields |
| GET | `/assignments/{id}/summary` | Latest AI summary |
| GET | `/assignments/{id}/attachments` | Attachments |
| POST | `/assignments/{id}/process` | Queue summary processing |

Query parameters for list: `status`, `subject_id`, `search`, `sort_by`, `sort_order`, `page`, `page_size`. Allowed student workflow statuses are `new`, `pending`, `in_progress`, `ai_generated`, and `awaiting_approval`. `submitted` is determined by portal verification, not an editable status.

## AI

| Method | Path | Purpose |
|---|---|---|
| POST | `/ai/generate-summary` | Summarize a stored assignment |
| POST | `/ai/generate-answer` | Generate a question answer draft (optionally RAG-grounded) |
| POST | `/ai/improve-answer` | Improve provided answer text |
| POST | `/ai/check-completeness` | Return structured coverage review |

## Study materials

| Method | Path | Purpose |
|---|---|---|
| POST | `/materials/upload` | Upload PDF/DOCX/PPTX/TXT/image allowed by validator |
| GET | `/materials` | List materials |
| GET | `/materials/{id}` | Material and short-lived signed URL |
| POST | `/materials/{id}/process` | Queue extraction/chunking/embedding |
| DELETE | `/materials/{id}` | Delete material record |

## Documents and submissions

| Method | Path | Purpose |
|---|---|---|
| POST | `/documents/generate` | Generate PDF or DOCX for stored assignment answers |
| POST | `/documents/{id}/upload-handwritten-scan` | Upload final scanned PDF if assignment requires handwriting |
| GET | `/documents` | List generated documents |
| GET | `/documents/{id}` | Document metadata and signed URL |
| GET | `/documents/{id}/download` | Returns document metadata and signed URL |
| DELETE | `/documents/{id}` | Delete document metadata |
| GET | `/submissions` | Submission workflow records |
| GET | `/submissions/history` | Submission history |
| POST | `/submissions/{id}/approve` | Approve exact document checksum |
| POST | `/submissions/{id}/attempt` | Attempts configured provider; currently returns manual fallback |
| GET | `/submissions/{id}/status` | Submission status |

## Digiicampus integration

| Method | Path | Purpose |
|---|---|---|
| POST | `/integrations/digii/connect` | Create student integration record |
| POST | `/integrations/digii/test` | Test configured, authorized read-only connection |
| POST | `/integrations/digii/sync` | Enqueue a read-only sync job |
| GET | `/integrations/digii/status` | Integration status |
| GET | `/integrations/digii/courses` | Saved course records |
| GET | `/integrations/digii/feed` | Saved feed posts |
| GET | `/integrations/digii/notifications` | Saved portal notifications |
| DELETE | `/integrations/digii/disconnect` | Disconnect and clear encrypted token field |

The adapter is disabled until its Bhawanipur path/credential configuration is independently verified.

## Notifications and integrations

| Method | Path | Purpose |
|---|---|---|
| GET | `/notifications` | In-app notifications |
| PATCH | `/notifications/{id}/read` | Mark one read |
| PATCH | `/notifications/read-all` | Mark all read |
| GET | `/notifications/preferences` | Preferences |
| PATCH | `/notifications/preferences` | Update preferences |
| POST | `/integrations/telegram/connect` | Save Telegram chat ID |
| POST | `/integrations/telegram/test` | Send test message |
| POST | `/integrations/whatsapp/connect` | Save WhatsApp recipient/consent record |
| POST | `/integrations/whatsapp/test?template_name=...` | Send approved template test |

## Calendar and analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/calendar/events?start=&end=` | Calendar events by range |
| GET | `/calendar/upcoming` | Upcoming events |
| GET | `/calendar/monthly?month=YYYY-MM` | Month events |
| GET | `/calendar/deadlines` | Assignment deadlines |
| GET | `/analytics/overview` | Aggregate assignments |
| GET | `/analytics/weekly-completion` | Submission records |
| GET | `/analytics/subject-distribution` | Subject distribution |
| GET | `/analytics/submission-performance` | Attempt summary |

## Settings

| Method | Path | Purpose |
|---|---|---|
| GET | `/settings` | Profile and notification preferences |
| PATCH | `/settings/profile` | Update profile |
| PATCH | `/settings/preferences` | Notification preferences |
| PATCH | `/settings/ai-preferences` | AI defaults |
| PATCH | `/settings/reminders` | Reminder defaults |

## Webhook and health

- `POST /api/v1/webhooks/clerk`: Clerk/Svix signature-verified user lifecycle webhook.
- `GET /health/live`: liveness.
- `GET /health/ready`: reports missing core configuration.
