# Phase 4 — UX simplification and polish

Owner approved October 12, 2026. Phase 3 acceptance stays open; this approval does
not certify connectors, voice quality, meeting hosting, or isolation.

## Implemented

- Typed @ completion now has separate Agents, Buds, People and Notify channel
  sections. Search includes display names and usernames. Up/Down selects a real
  participant, skipping section labels; Tab/Return inserts without sending;
  Escape dismisses. Configured Bud appearance/color is shown beside its role.
  Paused legacy agent records are excluded. The named main build agent remains
  the production Agents entry; no fictional agents or new backend routes were added.
- The toolbar mention menu uses the same catalog and section hierarchy. Existing
  person, Bud and agent routing tokens remain unchanged. Username-only matches
  retain the existing @username syntax and user ID.
- The picker is a child of the existing main window, anchored above the composer.
  It creates no native window, does not activate another Space, and does not resize
  the conversation feed. Hiding the composer or losing editor focus dismisses it.
  Rows scroll within a bounded height; long labels elide and have tooltips.
- Bud connector setup no longer forces a 960px minimum/1100px resize. It works
  within the 600px Bud setup minimum. Cards adapt to one, two or three columns;
  permissions, consent, saving and real connection requirements remain intact.
- Settings keeps Workspace settings, Log out and Done in a fixed footer, outside
  the scrolling content. Done is the primary action. Existing immediate preference
  saving and explicit profile-name saving remain unchanged.

## Screen review

This is source/automated-layout review, not a claim of live customer acceptance.

| Journey | Review and retained interaction | Evidence |
| --- | --- | --- |
| Google account/workspace/invitations | Guided account pages, deliberate dashboard entry, role-aware controls and server errors | account/connected regressions |
| Required profile and Bud setup | Back/Continue, optional details, seven Bud stages, finish-later remains incomplete | profile/Bud/onboarding suites |
| Chat and threads | Named @ search, deliberate send, keyboard selection, grouped feed, reactions, attachments and voice controls | mention/chat/visual/media suites |
| Connector setup | Role gallery, responsive cards, provider availability, explicit resource/consent and fallback disclosure | Bud/connector suites |
| Agent work/results and approvals | Existing in-chat progress, final result replacement and explicit apply/publish controls | build/execution/review suites |
| Preferences and team billing | Scrollable sections with persistent exit actions; existing workspace billing permissions retained | settings/visual/billing suites |
| Meetings and review | Existing audio/video separation, consent, transcript review/Confirm and roster layout | meeting suites; hosted gate remains open |
| Loading/error/empty/disabled states | Existing skeleton/recovery patterns retained; unavailable connectors stay disabled with explanation | connected/account/Bud regressions |
| Keyboard/theme/compact layout | No-focus mention list, Tab/Return/Escape, neutral dark palette and scroll/overflow checks | visual/onboarding/design-system suites |

Rendered native Qt fixture screenshots were inspected in light and dark at
1100×760, plus Settings at 560×540. Evidence is local/ignored under
`work/phase-4-ui/`; these are test fixtures, not screenshots for marketing.
A compact 900×650 chat regression verifies the picker stays above the composer
and the composer does not overlap the footer. Existing onboarding layout coverage
continues to exercise light/dark and compact/full desktop widths.

Validation: 782 native tests passed (`QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`),
including account/chat/AI/connector/billing/access-control regressions. Ruff and
`git diff --check` passed. The existing audioop deprecation warning is unrelated to
this UX change; this is not a Windows/clean-machine or hosted acceptance result.

## Acceptance and owner actions

No SQL, provider key, consent or purchase is required for these UI changes.
The existing staging application still has an unsaved Bud draft open and was not
restarted or discarded. To validate the updated native build: finish/save that
configuration, or deliberately choose Finish later, then close Aedrova Staging
and tell the assistant it is ready to reopen. Do not reconfigure accounts or keys.
A fresh-user live walkthrough remains required before closing the Phase 4 gate:
account → profile → required connected Bud → controls tour → @Bud → result,
including Finish later/resume and compact-window keyboard use. The preceding
Phase 3 two-account login/isolation, sound/playback and hosting gates remain open.
Public checkout/downloads stay disabled. Phase 5 requires separate owner approval.
