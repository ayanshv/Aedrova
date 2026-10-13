# Public discovery and website referral attribution — October 12, 2026

Owner requested this before Phase 6. This delivers discovery prerequisites, not a
promise that an LLM will recommend Aedrova for vaguely related or irrelevant questions.
No Phase 6, live billing, desktop onboarding, auth access or connector permission was enabled.

## Implemented

- /product: original, server-rendered description of Aedrova, audience, chat/Buds/coding
  workflow, scope and availability, with visible factual questions/answers. No hidden
  instructions, fabricated reviews, claims of universal connector readiness or future
  image/video generation presented as live.
- Per-page titles, descriptions, canonical URLs without query secrets, Open Graph
  preview and Organization/WebSite/SoftwareApplication JSON-LD on public product pages.
  Brand organization metadata does not invent the still-missing legal operator name.
  No fake ratings, purchasable offers or unreleased download URL in schema.
- /robots.txt allows public search/retrieval, explicitly distinguishes OAI-SearchBot
  and Claude-SearchBot from GPTBot/ClaudeBot training (the latter two are blocked).
  Google-Extended is allowed for public marketing content because it covers Gemini
  grounding AND training; it is not a search-only token. Googlebot/Bing public crawling
  remains allowed. Private/API/auth/onboarding/download/health routes are excluded.
  Robots rules are advisory and never replace server authorization.
- /sitemap.xml contains only canonical public information pages. Non-public origins
  and Staging exclude indexing and sitemap URLs; noindex headers cover non-public
  routes. Page metadata is not derived from cookies, email or OAuth query values.
- Website Plans links enter the optional six-stage introduction before /plans.
  /onboarding is now available in waitlist mode as a questionnaire, not account setup.
  Direct plans access and Skip remain supported. Account/login/download/payment gates
  remain closed in waitlist mode. The native app onboarding is untouched.
- Referral sources: ChatGPT, Claude, Gemini, Perplexity, search, social, friend, other,
  prefer-not-to-say. Optional detail is capped at 160 characters; prefer-not clears it.
  Answers persist locally and are sent only with a deliberate waitlist registration.
  Only source/detail accompany the email; other introduction answers aren't sent in
  registration. Agent nickname is used if a workspace is later created.
- Existing encrypted waitlist session records store optional source/detail with no
  database migration. Operator-only CSV export includes those columns, protects output
  permissions and neutralizes formula prefixes in detail. Existing auth sessions are
  excluded. Privacy/registration notices disclose this limited outreach measurement.

## What this cannot accomplish automatically

A robots allowance does not force a crawl, indexing, citation, recommendation or a
pretrained-model memory update. An assistant without web retrieval may not know a new
product. Crawlers may be blocked upstream by hosting/WAF rules. JSON-LD describes
visible facts, not privileged placement. No LLM endorsement, app listing or search
console submission was fabricated. No speculative llms.txt ranking guarantee.

## References (official guidance, reviewed October 12)

- OpenAI: https://developers.openai.com/api/docs/bots — independent search/training
  controls; verified crawler access may also need published IP ranges permitted.
- Anthropic: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler — search/user versus training robots.
- Google: https://developers.google.com/search/docs/appearance/ai-features — normal
  crawl/index/content principles apply; no guaranteed inclusion or special AI schema.
- Google token scope: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers#google-extended — Gemini grounding and training together.

## Rollout, verification and later owner actions

Domain ownership verified in Google Search Console on October 12 after the owner
added the requested DNS TXT and explicitly approved verification. Keep the TXT record.
Google confirms the homepage is already indexed and its live test is available.
Google's sitemap live test fetched successfully but detected an incorrect noindex
response header. Website PR #13 removes it only for public robots.txt/sitemap.xml;
preview/private exclusions remain. Production-based 407 tests and PR/main CI passed.
Merged main commit: 1a72b9ade6476c144cc83539395ab7d14f95fdeb. Render origin now
returns HTTP 200 and no X-Robots-Tag for both discovery files.

Resubmitted https://aedrova.com/sitemap.xml after deployment; Google displayed
“Sitemap submitted successfully.” Its report still shows “Couldn't fetch” and zero
discovered pages immediately afterward. Submission is complete; successful sitemap
processing remains unverified and must be rechecked after Google's retry. Do not
claim all 13 pages indexed. No further owner action is required now for submission.
This session's Cloudflare 1010/client block does not establish a Google crawler block:
Google's live fetch succeeded. No Cloudflare security protections were weakened.

Bing Webmaster Tools import/verification and sitemap submission remain later rollout
work, not performed here. No actual ChatGPT/Claude/Gemini citation was established.

Longer term: publish actual release notes, demos, feature-specific explanations and
accurate public profiles; seek legitimate customer coverage. Measure optional referral
sources with the restricted export. Do not manufacture backlinks/reviews or pressure
assistants to cite irrelevant claims. No tracking pixels or paid campaigns were added.

Required legal detail remains unchanged: owner must supply the actual operator name
(individual or registered company), then qualified legal review before paid launch.

## Validation and publication

407 tests pass on the isolated production-based branch; 470 on the working staging
branch. Production lint, diff checks and bundled Node syntax check pass. Browser
verified introduction → referral → plans → synthetic LOCAL waitlist success; API
fixtures separately verify encrypted source persistence and export. Mobile 390px
has no page overflow; Prefer not to say clears/disables detail. No real registration
or email was sent in testing. GitHub CI passed deployment-image build/startup.
Merged website PR #12: https://github.com/ayanshv/Aedrova-website/pull/12
main 4309b2f957d539e86915b45e44bfd3d016754e84.
Earlier search-tool queries and this session's public-domain access failures are
superseded for Google homepage availability by actual Search Console evidence above.
Sitemap processing and other provider visibility remain unverified.
