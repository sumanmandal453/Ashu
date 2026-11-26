-- Run this only after enabling pg_cron and applying the initial migration.
-- It enqueues one global dispatch tick; the Python worker finds connected integrations.
select cron.schedule(
  'ashu-assignment-sync-dispatch',
  '*/15 * * * *',
  $$select pgmq.send('scheduled-dispatch', '{"task_type":"dispatch.sync"}'::jsonb);$$
);

-- To remove later:
-- select cron.unschedule('ashu-assignment-sync-dispatch');
