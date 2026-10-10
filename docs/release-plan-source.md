# Owner-supplied release phase proposal

Reference for planning only; execution requires the phase approval gates.

Establish the release baseline
Start here
Includes: Your items 12, 15, and the preparation for item 14.
- Inventory the existing application, backend, database, connectors, AI providers, website, and payment integration.
- Record what's working, partially working, missing, or broken. Don't assume a feature works because its button appears.
- Remove Pulse and all related UI references, routes, and unused code where safe.
- Establish development, staging, and production configurations so testing cannot accidentally affect live customers.
- Secure the GitHub repository, check environment variables and secrets, and set up automated tests for future changes.
Completion gate: A documented list of what's ready, what needs work, and what's allowed into the first public release.



02

Complete the connector and AI-provider systems
Includes: Your items 1, 5, 10, and 11.
Create a connector audit covering every integration planned for launch, including GitHub, Supabase, Figma, Notion, Stripe, Linear, PostHog, and the relevant marketing and research tools.
For each connector, test connection, permissions, data retrieval, supported actions, expired credentials, token refresh, rate limits, error handling, disconnection, and reconnection. Only expose actions the integration actually implements.
Separately verify:
- OpenAI: credentials, model access, request handling, usage accounting, and failure behavior.
- Anthropic: secure key storage, provider integration, usage accounting, timeouts, and error handling.
- Stripe Bud connector: distinguish users connecting their own Stripe account from using Stripe to collect Aedrova subscriptions. Start with read-only access where practical and require explicit authorization before consequential financial actions.
Use least-privilege permissions. Where a provider requires OAuth verification, confirm that approval is complete before relying on those scopes in production. Google's guidance calls for the narrowest necessary scope and verification of applicable sensitive or restricted scopes. 

Google for Developers
+1



Completion gate: Every connector advertised at launch passes the same repeatable test matrix. Anything not ready is disabled or clearly identified as unavailable.



03

Finish messaging, meetings, and file context
Includes: Your items 2, 3, and 4.
Meeting transcription: Decide how meetings are captured, how participants are notified and consent is obtained, where transcripts are stored, and which agents can use them. Test transcription accuracy, speaker attribution where supported, long meetings, interruptions, and deletion.
Voice-to-text: Provide an obvious record button, microphone permission handling, a recording indicator, editable transcript preview, and a clear send action. Users must be able to cancel without sending.
File uploads: Establish explicit size, type, count, and total-storage limits. Validate files on the server, not just in the UI. Test malformed documents, oversized files, parsing failures, and malicious instructions embedded in documents.
Shared context: Make it clear which room, files, meetings, and connected sources an agent can use. Don't automatically make all workspace content available to every Bud without a defined permission and relevance model.
Completion gate: Each feature has documented limits, an understandable permission flow, reliable failure handling, and tests for data isolation.



04

Simplify the complete user experience
Includes: Your items 6, 8, and 13.
Redesign and refine the chatspace's interactions before updating the marketing site.
The @ menu should have clear, separate sections for Aedrova, other agents, and Buds. Show each one's purpose and, where useful, connection status. Search, keyboard navigation, and selection should feel natural.
Audit every screen individually. Each screen should have one obvious primary action, useful context, and secondary options that appear only when needed.
Check the whole journey: sign-up, workspace creation, invitations, chat, agent selection, connector setup, approvals, generated results, errors, settings, billing, and account deletion.
Every view needs sensible loading, empty, success, and failure states. Remove redundant controls, inconsistent styling, placeholder content, confusing terminology, and dead ends.
Completion gate: A new user can understand what to do next without needing a tutorial or asking your team for help.



05

Finalize legal, privacy, and business readiness
Includes: Your item 7, plus additional legal and operational work.
First document the actual data flow: what you collect, what gets sent to OpenAI or Anthropic, which connectors can read or modify data, what gets logged, and how long information is retained.
Prepare and have the appropriate professional review:
- Privacy Policy and Terms of Service.
- Acceptable Use Policy and rules for user-generated content.
- Subscription, renewal, cancellation, refund, and billing disclosures.
- AI-provider and third-party data disclosures.
- Cookie and analytics notices where applicable.
- A data-deletion and retention procedure, and a subprocessor list. Add appropriate business data-processing terms if selling to teams that need them.
Also confirm business ownership, founder agreements, intellectual property assignment, required registrations, bookkeeping, taxes, and who is authorized to sign contracts and maintain payment-provider accounts.
Completion gate: Your published documents accurately describe the real product, and your business and payment arrangements are ready for commercial use.
Policies alone do not eliminate legal risk. Applicable requirements depend on your business, users, and data practices, so have a qualified lawyer review the final arrangements.



06

Finish billing and the website purchase journey
Includes: Your items 16 and 17.3–17.5, plus the remaining billing work.
Establish the final plans, prices, limits, and entitlements before connecting the entire purchase flow.
Test the full lifecycle: initial checkout, successful and failed payments, renewals, cancellations, refunds, plan changes, duplicate webhook delivery, delayed events, and access after subscription changes. Stripe documents subscription webhooks for these lifecycle events, including successful payments and payment failures. 

Stripe Documentation



Enforce paid access on the backend, not by simply hiding buttons on the website.
Then replace the waitlist-only experience with the actual onboarding and purchase journey:
1. The visitor understands the product and its value.
2. They create an account and configure their workspace.
3. They see clear plan and billing terms.
4. They complete checkout.
5. Their account receives the correct entitlements.
6. They access the proper desktop download and installation instructions.
The onboarding, pricing, checkout, and account screens should feel like the same product. Clearly explain what users pay, when they renew, how they cancel, and what happens after cancellation.
Completion gate: A real test customer can purchase, access the right features, manage their subscription, and recover from common billing problems without manual database changes.



07

Perform the full security and reliability audit
Release blocker
Includes: The main work in your item 14.
This phase should cover:
Security: Supabase Row Level Security (RLS), workspace membership checks, server-side authorization, session expiry, connector-token protection, secret leakage, unsafe file processing, prompt injection, and unauthorized agent actions.
Rate limiting: Enforce server-side limits by user and workspace, with suitable IP-level protection and provider-specific controls. Bound request frequency, concurrent tasks, model tokens, file uploads, transcription use, tool calls, retries, and total AI spending. Apply plan entitlements to these limits and test that they cannot be bypassed through direct API requests.
Reliability: Simulate unavailable AI providers, expired OAuth tokens, network interruptions, database errors, stalled jobs, and webhook failures. Verify retries, timeouts, idempotency, and clear recovery messages.
Operations: Set up production error monitoring, spending alerts, usage dashboards, backups, and a tested restore procedure. Check dependency vulnerabilities and remove debug endpoints, test accounts, leftover bypasses, and development-only configuration.
Completion gate: All critical user journeys pass; no unresolved critical or high-severity security issues remain; workspace isolation has been verified; spending limits work; and the team knows how to respond to an incident. Use the OWASP API Security Top 10 as a baseline for the API review.