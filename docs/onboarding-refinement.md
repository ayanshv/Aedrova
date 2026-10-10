# Onboarding refinement

Workspace setup is now a two-step flow: workspace name, then agent nickname and provider. A successful creation opens an explicit ready screen, with optional teammate invitations and a Continue button leading to a small workspace home. Workspace administration is behind Workspace settings, not the onboarding destination. Joining an invitation also lands on workspace home.

A successful RPC followed by a failed snapshot refresh is reported as saved, avoiding a misleading creation retry. Failed creation keeps the typed name and nickname. Submission is disabled while a request runs. This does not make ambiguous network timeouts idempotent: users must refresh before retrying a timed-out write.

Google sign-in uses the official Google G asset from https://developers.google.com/static/identity/images/g-logo.png, distributed with the app. Branding reference: https://developers.google.com/identity/branding-guidelines.

No new SQL migration or OAuth setting is required. The owner must sign into the rebuilt app to verify the hosted create/join flow. Automated UI tests use a fake identity service; they do not replace authenticated hosted tenant-isolation validation. Shared messaging remains milestone 4.


## October 2: setup controls overlapping the heading

Reproduced the Getting started dialog with its workspace button at the window's top edge.
The position animation sampled content before the layout had assigned its geometry.
Setup content now stays under layout control, and old step controls hide before deferred
deletion. All four steps were captured in light/dark with motion enabled; new regression
checks step forward/back navigation after animations settle. The internal Mac preview was
rebuilt and development-signed. Public signing/notarization remains gated.
