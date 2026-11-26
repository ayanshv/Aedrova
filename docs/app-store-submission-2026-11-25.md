# iPhone App Store submission pack (November 25, 2026)

Drafts for the owner to check and paste into App Store Connect. Nothing here has been uploaded.
Do not put real reviewer passwords or tester emails in this file or anywhere in the repository.

## 1. Decide first: how App Review signs in

The production beta list is on, and the app only offers Google and Apple sign-in. Apple's
reviewers cannot use a Sign in with Apple login (it hides their email behind a relay address
that can never be on the list) and will not have an account of ours.

| Option | What it takes | Trade-off |
|---|---|---|
| A. A dedicated Google test account on the beta list | Create a Google account you own, with no 2-step prompt, add it to the list, put its email and password in the review notes | Quick. The password sits in App Store Connect, so use a throwaway account and change it after review |
| B. A reviewer demo sign-in inside the app | Code change and its own review of what it exposes | Cleanest for Apple, most work |
| C. Stay on TestFlight, submit when the beta gate opens | Nothing | Apple may also ask why an app only invited people can use is public |

Recommendation: C for now, then A at the moment the beta opens.

## 2. What the owner must do (nothing here can be done for you)

Required before the first upload:
1. Pick an option in section 1.
2. In App Store Connect, open the app record for `com.aedrova.desktop` and check the name,
   primary language and category (section 3).
3. Choose the real version and build numbers (section 7), then archive a Release build with a
   distribution profile and upload it.
4. Take the screenshots (section 6) and paste in the text from sections 3 to 5.
5. Answer App Privacy (section 4), the age rating questionnaire and export compliance
   (already declared in the app: standard HTTPS only).
6. Add the review notes (section 5), with the test account if you chose option A.

Later or optional: a custom auth address (`auth.aedrova.com`), a phased release, and an app
preview video.

Blocks submission: items 1 to 6. Does not block TestFlight.

## 3. Listing text (drafts)

- **Name:** Aedrova
- **Subtitle (30 characters):** Your team, plus Agents
- **Category:** Productivity (secondary: Business)
- **Support URL:** https://aedrova.com/support
- **Privacy policy URL:** https://aedrova.com/privacy
- **Terms of use URL:** https://aedrova.com/terms
- **Copyright:** 2026 [legal name of the company, owner to fill in]

**Promotional text (170 characters):**
Catch up on your team's channels and messages from your iPhone, and get alerts that name the person and place without showing the message.

**Description:**

Aedrova brings your team's workspace to your iPhone. Read channels and direct messages, reply in threads, search everything in one place and get alerts for mentions and replies.

What you can do
- Follow channels and direct messages, with a quiet "New messages" line that shows where you left off.
- Search across your workspace to find decisions and open questions.
- See activity that mentions you or replies to you.
- Choose a light, dark or system look, a message size and chat bubbles that suit you.
- Report a message or block a teammate at any time.

Private by design
- Notifications name the person and the place, never the message itself.
- You can hide the workspace in the app switcher, and manage blocked teammates under Account and privacy.
- You can request deletion of your account from inside the app.

Aedrova works with the workspace your team already uses on Mac and Windows. Sign in with Google or Apple. Aedrova is in a private beta, so your email must be on the list.

**Keywords (100 characters, comma separated):**
team chat,workspace,channels,messages,agents,collaboration,threads,search,notes,projects

**What's new (first version):** First release of Aedrova for iPhone.

## 4. App Privacy answers

These must match `App/PrivacyInfo.xcprivacy` in the iPhone app. The manifest declares eight
data types, all linked to the person, none used for tracking, all for app functionality.

| Data type in App Store Connect | Collected | Linked to identity | Used for tracking | Purpose |
|---|---|---|---|---|
| Name | Yes | Yes | No | App functionality |
| Email address | Yes | Yes | No | App functionality |
| User ID | Yes | Yes | No | App functionality |
| Emails or text messages | Yes | Yes | No | App functionality |
| Photos or videos | Yes | Yes | No | App functionality |
| Other user content | Yes | Yes | No | App functionality |
| Customer support | Yes | Yes | No | App functionality |
| Product interaction | Yes | Yes | No | App functionality |

Also answer: no data is used to track people, and no third-party advertising is used.

Check before submitting: the push device token is stored against the person's account. Apple
treats it as a device identifier in some readings. If counsel or App Store Connect's help text
says it should be declared, add "Device ID" with the same linked, not-for-tracking, app
functionality answers and add it to the manifest. Also confirm whether any message text is
sent to an AI provider from the iPhone app (the follow-up screen asks for consent first), and
that the privacy policy says so.

## 5. Review notes (template)

Paste into "Notes" in App Store Connect. Replace the bracketed parts. Never commit the real
password.

> Aedrova is a team workspace app. It is in a private beta, so only emails on an invited list
> can sign in. A test account is provided below and is on the list.
>
> Sign in with Google using: [test account email] / [password]. Please choose "Continue with
> Google". (Sign in with Apple is also offered, but accounts that hide their email cannot be
> on the invited list, so please use the Google test account.)
>
> What to try:
> 1. Open the "[workspace name]" workspace, then a channel, and read the messages.
> 2. Long-press a message from another person to report it or block them. Blocked people are
>    listed under You > Account and privacy > Blocked teammates.
> 3. Search for a word on the Search tab.
> 4. Account deletion: You > Account and privacy > Delete account.
> 5. Notifications: Settings > Notifications > Turn on push notifications.
>
> User-generated content: people can report messages and block teammates. Reports go to the
> support team, who act on them. Our acceptable use policy (https://aedrova.com/acceptable-use)
> and terms prohibit objectionable content.
> The app does not use App Tracking Transparency and does not track people.

## 6. Screenshots

Apple's required sizes change, so check App Store Connect for the exact list. At least one set
of the largest iPhone size is needed (6.9 inch). The simulator in this project is an iPhone 17
Pro (6.3 inch), so use an iPhone 17 Pro Max simulator for 6.9 inch captures.

Suggested set (five to eight, light mode first):
1. Workspaces list with the large "Continue" card.
2. Channels list with the floating tab bar.
3. A chat with bubbles and the "New messages" line.
4. Search with results.
5. You tab and Settings.
6. A notification alert (name and place only).

Use the populated demo workspace so no real customer data appears.

## 7. Before archiving

- The repository currently says version 1.0, build 1 (`Config/App.xcconfig`), while TestFlight
  shows 11.25.2. Set `MARKETING_VERSION` to the number for the store release and raise
  `CURRENT_PROJECT_VERSION` with every upload. Decide a scheme before the first App Store
  version, because an App Store version number cannot go back.
- `aps-environment` is `development` in `Config/Aedrova.entitlements`. A distribution profile
  signs the build with the production value. After the first TestFlight build from that
  profile, confirm an alert arrives.
- TestFlight currently has 11.25.2. Nothing since then (theme fix, one-time notification ask,
  allowlist screens, unread line, chat alignment) is in a build yet.

## 8. Already in place

Sign in with Apple beside Google, in-app account deletion, report and block, a privacy
manifest, an AI consent step before follow-ups, push through Apple, export compliance
declared, and an iPhone-only build for iOS 17 and later.

## 9. Still unverified

Live Google and Apple sign-in on a real iPhone as a new person, two-way sync with the Mac,
a mention, a direct message and a reply each reaching the phone, and the "Not on the list yet"
screen with a real unlisted account.
