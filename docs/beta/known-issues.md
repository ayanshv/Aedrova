# Aedrova beta: known issues and limits

## Platform
- Mac only, macOS 14 or newer, Apple silicon. No Windows or Linux build yet.
- Updates are manual: download the new build from the site and replace the app.

## Sign-in and access
- Only invited emails can use the beta. Apple "Hide My Email" addresses cannot be matched.
- Non-Google addresses sign in with email and password.
- The beta service may take up to a minute to wake after a quiet period.

## Meetings
- Detection works for Zoom, Teams, Webex and browsers using the microphone (Google Meet).
  FaceTime, Slack huddles and Discord are not detected. You can always start notes by hand.
- A muted call may not be detected.
- Speakers are not named. The transcript labels only "Microphone" and "Computer audio".
- The first use downloads a 148 MB speech model.
- Hosted audio and video calls are not part of this beta.

## Agent and builds
- Builds work in a safe copy. Apply the result with **Review changes**.
- A build can take several minutes, and a plan that cannot cite sources is asked once to try again.
- Very long answers are shortened in the chat. Use **Save as PDF** or **Save as Markdown**.

## Buds and connectors
- Connectors read, never write: GitHub, Notion, Figma and Supabase are the supported set.
- Notion: one shared page, its nested blocks and the first five sub-pages. Databases, images and
  files are not read.
- Figma: page and frame names only. Supabase: project health only.
- Other connectors (Instagram, Stripe, Vercel) are not certified for the beta.

## Slack import
- Imports from a Slack export file. Large exports can take a while, and an interrupted import resumes.

## AI allowance
- Each workspace has a weekly and a five-hour allowance. When one is used up, chat still works and
  AI resumes as usage ages out. The meter in the sidebar shows what is left.

## Privacy
- Text you share with the agent is sent to our AI provider. Audio never leaves your Mac.
- This is a beta: data can be lost.
