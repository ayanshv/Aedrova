# Hosted configuration check — September 27, 2026

The owner reports applying the SQL migrations, configuring Google OAuth, allowing the loopback redirect, and disabling public Realtime access.

The desktop source and packaged app now use the supplied public Supabase configuration for cpelagtufyocepnqcqqd. Only a publishable key is embedded. Packaging uses environment configuration when explicitly supplied, otherwise the application public configuration.

Live checks: Auth settings returned HTTP 200 with Google enabled. Anonymous reads of workspaces, workspace_members, channels, workspace_invitations, and workspace_agent_preferences all returned HTTP 401 / PostgreSQL 42501 permission denied. These checks do not establish authenticated tenant isolation or successful Google login.

Email authentication is still enabled according to hosted Auth settings. Owner action: disable Email in Supabase Authentication → Sign In / Providers → Email for Google-only access.

Validation: 96 Python tests passed; Ruff and whitespace checks passed; configured Mac package built, codesign verification passed, baseline release secret scan passed, and packaged account-screen smoke launch passed. The smoke report is a UI check, not an authenticated connection test.

Next required owner action: use Continue with Google in the newly opened app, complete consent, then create a workspace and choose an agent nickname. Report success or the exact error. A second Google test account is needed for hosted invitation and cross-workspace isolation checks. Milestone 3 remains open pending authenticated live verification; milestone 4 has not started.
