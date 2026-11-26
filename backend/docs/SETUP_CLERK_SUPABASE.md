# Clerk + Supabase setup

1. Keep Clerk Google OAuth configured in the existing Next.js frontend.
2. In Clerk, use the current Connect with Supabase feature to make Clerk session tokens compatible with Supabase.
3. Add Clerk in Supabase Dashboard → Authentication → Third-Party Auth.
4. Ensure the Clerk session JWT includes the `role` claim with value `authenticated`.
5. Set the Clerk instance domain in local Supabase config when using Supabase CLI locally.
6. Use the Clerk session JWT for user-scoped API requests. FastAPI verifies it through `clerk-backend-api`; PostgREST receives it as `Authorization: Bearer <clerk-jwt>` alongside the Supabase publishable `apikey`.
7. User-scoped Storage requests use the same Clerk JWT so Storage RLS is checked.
8. Use the Supabase secret key only from the server/worker for admin operations. Current `sb_secret_...` keys are opaque API keys; send them in `apikey`, not as a JWT Bearer token.

Do not create Supabase Auth accounts. The Supabase auth service is used to validate third-party Clerk JWT claims, not to present a second login flow.
