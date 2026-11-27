-- Ashu initial schema. Apply with `supabase db push` after configuring Clerk third-party auth.
create extension if not exists vector with schema extensions;
create extension if not exists pgmq;

create table if not exists public.profiles (
  clerk_user_id text primary key,
  full_name text,
  email text,
  college_name text default 'Bhawanipur Global Campus',
  department text,
  course_name text,
  semester text,
  roll_number text,
  timezone text not null default 'Asia/Kolkata',
  onboarding_completed boolean not null default false,
  account_status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.college_integrations (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  provider text not null,
  tenant_name text,
  base_url text not null,
  external_student_id text,
  connection_status text not null default 'not_connected',
  permission_status text not null default 'not_verified',
  last_synced_at timestamptz,
  next_sync_at timestamptz,
  sync_interval_minutes integer not null default 15 check (sync_interval_minutes between 5 and 1440),
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, provider)
);

-- Private storage for integration credentials.
-- Only the backend service_role can access this table.
create table if not exists public.college_integration_secrets (
  integration_id uuid primary key
    references public.college_integrations(id) on delete cascade,
  encrypted_credentials text not null,
  credential_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.college_integration_secrets enable row level security;

revoke all privileges on table public.college_integration_secrets
  from PUBLIC, anon, authenticated;

grant all privileges on table public.college_integration_secrets
  to service_role;

create table if not exists public.subjects (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  subject_name text not null,
  subject_code text,
  faculty_name text,
  subject_type text,
  semester text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.courses (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete set null,
  external_course_id text,
  external_class_id text,
  subject_id uuid references public.subjects(id) on delete set null,
  course_name text not null,
  course_code text,
  faculty_name text,
  course_type text,
  course_status text,
  raw_source jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, integration_id, external_class_id)
);

create table if not exists public.course_modules (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  course_id uuid not null references public.courses(id) on delete cascade,
  external_module_id text,
  module_name text not null,
  module_order integer,
  created_at timestamptz not null default now()
);

create table if not exists public.course_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  course_id uuid not null references public.courses(id) on delete cascade,
  module_id uuid references public.course_modules(id) on delete set null,
  external_session_id text,
  session_title text not null,
  session_description text,
  session_date date,
  start_time time,
  end_time time,
  session_status text,
  faculty_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.resources (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  course_id uuid references public.courses(id) on delete cascade,
  session_id uuid references public.course_sessions(id) on delete set null,
  external_resource_id text,
  resource_name text not null,
  external_resource_url text,
  storage_path text,
  file_type text,
  file_size bigint,
  processing_status text not null default 'not_started',
  created_at timestamptz not null default now()
);

create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete set null,
  course_id uuid references public.courses(id) on delete set null,
  subject_id uuid references public.subjects(id) on delete set null,
  subject_name text,
  external_assignment_id text,
  external_class_id text,
  title text not null,
  description text,
  instructions text,
  start_at timestamptz,
  deadline timestamptz,
  submission_type text,
  assignment_type text,
  grading_type text,
  total_marks numeric(10,2),
  portal_status text,
  workflow_status text not null default 'new',
  portal_is_submitted boolean not null default false,
  priority text not null default 'medium' check (priority in ('low','medium','high')),
  source_platform text not null default 'digiicampus',
  source_url text,
  content_hash text,
  detected_at timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, integration_id, external_class_id, external_assignment_id)
);

create table if not exists public.assignment_attachments (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  external_resource_id text,
  original_file_name text not null,
  external_file_url text,
  storage_path text,
  file_type text,
  file_size bigint,
  content_hash text,
  extraction_status text not null default 'pending',
  created_at timestamptz not null default now()
);

create table if not exists public.assignment_questions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  question_number integer,
  question_text text not null,
  maximum_marks numeric(10,2),
  question_type text,
  source_reference jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.assignment_events (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid references public.assignments(id) on delete cascade,
  event_type text not null,
  old_value jsonb,
  new_value jsonb,
  event_timestamp timestamptz not null default now(),
  processing_status text not null default 'pending'
);

create table if not exists public.assignment_summaries (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  short_summary text,
  detailed_summary text,
  objective text,
  question_count integer,
  important_instructions jsonb not null default '[]'::jsonb,
  document_requirements jsonb not null default '[]'::jsonb,
  uncertainties jsonb not null default '[]'::jsonb,
  ai_provider text,
  model_name text,
  generated_at timestamptz not null default now()
);

create table if not exists public.generated_answers (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid references public.assignments(id) on delete cascade,
  question_id uuid references public.assignment_questions(id) on delete set null,
  question_text text,
  answer_text text not null,
  ai_provider text,
  model_name text,
  source_references jsonb not null default '[]'::jsonb,
  generation_status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.study_materials (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  subject_id uuid references public.subjects(id) on delete set null,
  file_name text not null,
  storage_path text not null,
  file_type text,
  file_size bigint,
  content_hash text,
  processing_status text not null default 'queued',
  uploaded_at timestamptz not null default now()
);

create table if not exists public.material_chunks (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  material_id uuid not null references public.study_materials(id) on delete cascade,
  chunk_text text not null,
  embedding extensions.vector(768),
  page_number integer,
  chunk_index integer not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(material_id, chunk_index)
);

create table if not exists public.generated_documents (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  file_name text not null,
  file_format text not null check (file_format in ('pdf','docx')),
  storage_path text not null,
  version_number integer not null default 1,
  checksum text not null,
  approval_status text not null default 'awaiting_review',
  requires_handwritten_submission boolean not null default false,
  generated_at timestamptz not null default now(),
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  unique(assignment_id, version_number)
);

create table if not exists public.approval_records (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  document_id uuid not null references public.generated_documents(id) on delete cascade,
  document_checksum text not null,
  approval_status text not null,
  approved_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.submission_attempts (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid not null references public.assignments(id) on delete cascade,
  document_id uuid not null references public.generated_documents(id) on delete cascade,
  approval_record_id uuid references public.approval_records(id) on delete set null,
  approval_status text not null default 'awaiting_approval',
  submission_method text,
  submission_status text not null default 'not_started',
  attempted_at timestamptz,
  verified_at timestamptz,
  portal_reference text,
  evidence_metadata jsonb,
  failure_reason text,
  created_at timestamptz not null default now()
);

create table if not exists public.feed_posts (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete cascade,
  external_post_id text,
  author text,
  post_text text,
  post_type text,
  posted_at timestamptz,
  detected_at timestamptz not null default now(),
  source_url text
);

create table if not exists public.portal_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete cascade,
  external_notification_id text,
  title text not null,
  body text,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.calendar_events (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete cascade,
  external_event_id text,
  course_id uuid references public.courses(id) on delete set null,
  event_title text not null,
  event_type text,
  start_at timestamptz,
  end_at timestamptz,
  venue text,
  faculty_name text,
  source text,
  created_at timestamptz not null default now()
);

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  assignment_id uuid references public.assignments(id) on delete cascade,
  notification_type text not null,
  title text not null,
  message text not null,
  channel text not null default 'in_app',
  delivery_status text not null default 'pending',
  sent_at timestamptz,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.notification_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id text not null unique references public.profiles(clerk_user_id) on delete cascade,
  telegram_enabled boolean not null default false,
  whatsapp_enabled boolean not null default false,
  new_assignment_alert boolean not null default true,
  deadline_reminder boolean not null default true,
  answer_ready boolean not null default true,
  document_ready boolean not null default true,
  approval_required boolean not null default true,
  submission_confirmation boolean not null default true,
  quiet_hours_start time,
  quiet_hours_end time,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.notification_channels (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  channel text not null check (channel in ('telegram','whatsapp')),
  recipient text not null,
  status text not null default 'pending_verification',
  consent_at timestamptz,
  created_at timestamptz not null default now(),
  unique(user_id, channel, recipient)
);

create table if not exists public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id text not null unique references public.profiles(clerk_user_id) on delete cascade,
  default_language text not null default 'English',
  default_answer_length text not null default 'medium',
  default_answer_style text not null default 'exam_oriented',
  default_ai_provider text not null default 'gemini',
  reminder_offsets jsonb not null default '["7_days","3_days","1_day","6_hours","1_hour"]'::jsonb,
  timezone text not null default 'Asia/Kolkata',
  quiet_hours_start time,
  quiet_hours_end time,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.sync_logs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  integration_id uuid references public.college_integrations(id) on delete set null,
  sync_type text not null,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  sync_status text not null default 'running',
  courses_found integer not null default 0,
  assignments_found integer not null default 0,
  assignments_created integer not null default 0,
  assignments_updated integer not null default 0,
  resources_found integer not null default 0,
  error_message text
);

create table if not exists public.worker_failures (
  id uuid primary key default gen_random_uuid(),
  queue_name text not null,
  message_id bigint not null,
  user_id text,
  payload jsonb not null default '{}'::jsonb,
  attempts integer not null,
  error_message text,
  created_at timestamptz not null default now()
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.profiles(clerk_user_id) on delete cascade,
  action text not null,
  entity_type text,
  entity_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

ALTER TABLE public.worker_failures ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.worker_failures FROM anon, authenticated;
GRANT ALL ON public.worker_failures TO service_role;

-- One reminder per assignment, user and offset. The worker also checks before insert.
create unique index if not exists notifications_deadline_reminder_unique
  on public.notifications(user_id, assignment_id, notification_type)
  where assignment_id is not null and notification_type like 'deadline_reminder_%';

create index if not exists assignments_user_deadline_idx on public.assignments(user_id, deadline);
create index if not exists assignments_user_status_idx on public.assignments(user_id, workflow_status);
create index if not exists assignment_events_user_time_idx on public.assignment_events(user_id, event_timestamp desc);
create index if not exists notifications_user_time_idx on public.notifications(user_id, created_at desc);
create index if not exists calendar_events_user_start_idx on public.calendar_events(user_id, start_at);
create unique index if not exists feed_posts_external_unique on public.feed_posts(user_id, integration_id, external_post_id) where external_post_id is not null;
create unique index if not exists calendar_events_external_unique on public.calendar_events(user_id, integration_id, external_event_id) where external_event_id is not null;
create unique index if not exists portal_notifications_external_unique on public.portal_notifications(user_id, integration_id, external_notification_id) where external_notification_id is not null;
create index if not exists material_chunks_embedding_idx on public.material_chunks using hnsw (embedding extensions.vector_cosine_ops);

-- RLS: authenticated Clerk JWTs must contain role=authenticated, and sub must be Clerk user ID.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'college_integrations','subjects','courses','course_modules','course_sessions','resources',
    'assignments','assignment_attachments','assignment_questions','assignment_events',
    'assignment_summaries','generated_answers','study_materials','material_chunks',
    'generated_documents','approval_records','submission_attempts','feed_posts','calendar_events',
    'notifications','portal_notifications','notification_preferences','notification_channels','user_preferences','sync_logs','audit_logs'
  ] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY %I ON public.%I FOR ALL TO authenticated USING (user_id = (SELECT auth.jwt()->>''sub'')) WITH CHECK (user_id = (SELECT auth.jwt()->>''sub''))', t || '_owner_policy', t);
  END LOOP;
END $$;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY profiles_owner_policy ON public.profiles FOR ALL TO authenticated
USING (clerk_user_id = (SELECT auth.jwt()->>'sub'))
WITH CHECK (clerk_user_id = (SELECT auth.jwt()->>'sub'));

-- Private storage buckets.
insert into storage.buckets (id, name, public) values
  ('assignment-files','assignment-files',false),
  ('study-materials','study-materials',false),
  ('generated-documents','generated-documents',false)
on conflict (id) do nothing;

CREATE POLICY "students manage own Ashu files" ON storage.objects
FOR ALL TO authenticated
USING (
  bucket_id in ('assignment-files','study-materials','generated-documents')
  AND split_part(name, '/', 1) = (SELECT auth.jwt()->>'sub')
)
WITH CHECK (
  bucket_id in ('assignment-files','study-materials','generated-documents')
  AND split_part(name, '/', 1) = (SELECT auth.jwt()->>'sub')
);

-- Vector search: invoker privileges and an explicit identity match prevent cross-user retrieval.
CREATE OR REPLACE FUNCTION public.match_material_chunks(
  query_embedding extensions.vector(768),
  match_count integer DEFAULT 5,
  filter_user_id text DEFAULT NULL
)
RETURNS TABLE (id uuid, material_id uuid, chunk_text text, page_number integer, similarity double precision)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public, extensions
AS $$
  SELECT mc.id, mc.material_id, mc.chunk_text, mc.page_number,
         1 - (mc.embedding <=> query_embedding) AS similarity
  FROM public.material_chunks mc
  WHERE mc.user_id = (SELECT auth.jwt()->>'sub')
    AND mc.user_id = filter_user_id
  ORDER BY mc.embedding <=> query_embedding
  LIMIT LEAST(GREATEST(match_count, 1), 20);
$$;
GRANT EXECUTE ON FUNCTION public.match_material_chunks(extensions.vector, integer, text) TO authenticated;

-- Queue functions are exposed only to the server-side service role. Never grant to anon/authenticated.
DO $$
BEGIN
  PERFORM pgmq.create('scheduled-dispatch');
EXCEPTION WHEN others THEN
  NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('course-sync');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('assignment-sync');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('assignment-processing');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('ai-generation');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('document-generation');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('notification-delivery');
EXCEPTION WHEN others THEN NULL;
END $$;
DO $$
BEGIN
  PERFORM pgmq.create('deadline-reminders');
EXCEPTION WHEN others THEN NULL;
END $$;

CREATE OR REPLACE FUNCTION public.ashu_enqueue_job(queue_name text, job jsonb)
RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pgmq, public, pg_temp
AS $$
DECLARE msg_id bigint;
BEGIN
  IF queue_name NOT IN ('scheduled-dispatch','course-sync','assignment-sync','assignment-processing','ai-generation','document-generation','notification-delivery','deadline-reminders') THEN
    RAISE EXCEPTION 'Invalid Ashu queue';
  END IF;
  msg_id := pgmq.send(queue_name, job);
  RETURN msg_id;
END;
$$;
REVOKE ALL ON FUNCTION public.ashu_enqueue_job(text, jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ashu_enqueue_job(text, jsonb) TO service_role;

CREATE OR REPLACE FUNCTION public.ashu_upsert_profile(profile jsonb)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp
AS $$
BEGIN
  INSERT INTO public.profiles (clerk_user_id, full_name, email)
  VALUES (profile->>'clerk_user_id', profile->>'full_name', profile->>'email')
  ON CONFLICT (clerk_user_id) DO UPDATE SET
    full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
    email = COALESCE(EXCLUDED.email, profiles.email),
    updated_at = now();
END;
$$;
REVOKE ALL ON FUNCTION public.ashu_upsert_profile(jsonb) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ashu_upsert_profile(jsonb) TO service_role;
