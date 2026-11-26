# Bhawanipur Digiicampus integration notes

## What the screenshots establish

The supplied portal screenshots show these UI sections:

- Home/feed, posts, classes, events and notifications.
- Student profile/e-portfolio.
- Classroom with ongoing and previous courses.
- Course Work with modules and individual sessions.
- Resources listing downloadable course material.
- Assignments with Ongoing and Closed tabs.
- Assignment detail fields: start date, due date, submission type, assignment type, grading, description, resources/attachments and prior submissions.
- Calendar with academic/institutional events and classes.

One assignment detail screenshot showed `Submission Type: Online Submissions`, `Assignment Type: Class Assignment`, `Grading: Graded Assignment`, a resource named `WCA_Assignment.docx`, a previously submitted PDF, and a description `Handwritten and Scanned`.

These are UI observations, not a verified API contract.

## Community project to review

https://github.com/Sheikh162/digii-campus-mcp

This community project documents read-style calls for profile, courses, assignment list/detail, feed, notifications, calendar and course sessions/resources. Candidate route strings from that repository must be validated against the Bhawanipur tenant before they are used. The repository's live tests against another tenant do not prove compatibility with Bhawanipur.

## Candidate paths (not enabled by default)

The connector's configuration may be set to candidate patterns such as:

- `/rest/classes/v1/classroom`
- `/rest/classes/v2/`
- `/rest/classes/{classId}/users/{ukid}/assignments`
- `/rest/assignments/v1/getStudentAssignmentDetails`
- `/rest/classes/{classId}/users/{ukid}/lessons`
- `/rest/classroomV2/class/{classId}/module`
- `/rest/classroomV2/class/{classId}/sessions/{sessionId}`
- `/rest/classes/v2/lessons`
- `/rest/institutionalCalendar/events`
- `/api/feedV3`
- `/rest/service/notifications`

Do not put these values into `.env` until the Bhawanipur route, parameters, authentication header and response shape have been verified.

## Authentication separation

- Clerk authenticates a student to Ashu.
- Digiicampus has its own college-side authentication.
- The community connector describes an `Auth-Token` header. This is not the Clerk JWT.

Do not copy browser cookies or scrape session storage. Do not bypass OTP, CAPTCHA or MFA. Prefer an official college-supported API/OAuth integration. A single `DIGII_AUTH_TOKEN` in `.env` is allowed only for a private local read-only developer test after permission is granted; it is not a production multi-student design.

The connector supports encrypted per-integration credential lookup if the approved credential flow provisions `college_integrations.encrypted_credentials`. No public endpoint accepts raw session tokens.

## Enablement checklist

1. Confirm written/official permission from Bhawanipur/Digii.
2. Verify a supported authentication flow.
3. Verify profile and class endpoints against Bhawanipur.
4. Verify assignment listing, pagination and detail endpoint against Bhawanipur.
5. Verify resource URLs and safe download method.
6. Verify feed/calendar/notifications separately.
7. Configure only verified paths in `.env`.
8. Set `DIGII_READONLY_ENABLED=true` only for the permitted read-only scope.
9. Run connection test and inspect redacted sync logs.
10. Keep write/submission operations disabled until an authorized write interface is documented and tested.

## Assignment submission

The screenshots confirm that the portal UI displays online submissions and previous uploaded PDFs. They do not establish an API endpoint or permission for an external application to upload assignments. The repository reference does not document academic assignment upload. `DigiicampusSubmissionProvider` therefore remains disabled and raises a manual-submission-required condition. Do not claim upload success without portal-side confirmation.
