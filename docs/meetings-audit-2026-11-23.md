# Meetings audit, November 23, 2026

## Which path matters

Aedrova does not host the meeting. People stay in Zoom, Google Meet or Teams. The product path is:

1. **Detect** (Mac): the native helper sees which app is using the microphone and the capsule
   asks "Take meeting notes?". Detection never records.
2. **Capture** after explicit consent: microphone and computer audio, transcribed on this Mac with
   a pinned Whisper model. No audio leaves the machine.
3. **Review and Confirm**: the person edits notes and transcript, then Confirm uploads one text
   file, `meeting-notes.txt`, to the channel through the verified attachment pipeline.
4. **Context**: the agent reads that attachment with the channel's other evidence and says it is
   "Reading reviewed meeting notes". No server meeting setting is involved.

Hosted calls (LiveKit) are optional and separate. They need the meeting service, so packaged beta
builds now hide them unless built with `AEDROVA_HOSTED_CALLS_ENABLED=true`.

## Checked

- Detection, capture, review, share and agent retrieval each have tests, and they pass.
- The speech model, on-device runtime and capture helper are bundled by `scripts/package_desktop.py`.
- A 20-second physical capture passed on November 6 (both sources transcribed, then discarded).
- The suggestion capsule is an always-on-top tool window, so it shows while Zoom is in front.

## Changed in source

1. **Hosted calls survive brief network trouble.** A single missed check-in used to end a live
   call; it now takes three in a row, and refused access still ends the call immediately.
2. **Hosted calls survive long sessions.** The account token is refreshed before it expires.
3. **Hosted entries are hidden in packaged builds** unless switched on, so testers do not meet a
   "meeting service is not configured" error. Source runs are unchanged.

## Context after Confirm

Confirm shares `meeting-notes.txt` as a channel file. The agent and channel Buds read it through
the same retrieval, and it is now always included: for every channel being read, the three newest
`meeting-notes.txt` shares are brought in by file name. Before this, a note was found only when the
question's words matched the message "Shared a file: meeting-notes.txt" or it was among the
latest messages, so asking from another channel or after many newer messages could miss it.
Private Bud conversations still read workspace context only when "workspace context" is ticked.

## Limits testers should know

- **Mac only.** Windows and Linux have no capture or detection.
- **macOS 14.2 or newer** is needed to see which app uses the microphone.
- **Recognized:** Zoom, Teams, Webex, and browsers using the microphone (Google Meet in a
  browser). FaceTime, Slack huddles and Discord are not recognized; manual Start always works.
- **A muted call may not be detected**, because detection looks for microphone input.
- **Browser tab titles** are not readable without Screen Recording permission, so Meet is found
  by microphone use, not by its page title.
- **First use downloads a 148 MB speech model** (pinned and checksum-verified).
- **Speakers are not named.** The transcript labels "Microphone" and "Computer audio" only.
- **Draft notes are extracted lines, not an AI summary.**

## Still to prove before calling this launch-ready

- A real external call: headphones, mute, a long call, stopping cleanly.
- Confirm on a real channel, then an agent answer that cites the notes, from a second account.
- A second account that is not in the channel cannot read the notes.
- The signed helper in the notarized app: microphone and system-audio prompts on a clean Mac.
