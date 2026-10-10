# How Aedrova updates

A DMG is a frozen disk image containing one built version of Aedrova. Editing Python
source or pushing GitHub commits does not change a DMG that has already been downloaded,
nor does it update installed apps automatically.

For every shipped desktop release:
1. Test the changes and increase `project.version` in the desktop `pyproject.toml`
   (for example, 0.1.0 → 0.1.1). The installed-version check now reads bundled package
   metadata, and packaging uses the same version in the macOS Info.plist.
2. Build the app with `scripts/package_desktop.py`; sign with Developer ID for public use.
3. Run `scripts/build_dmg.py --notary-profile aedrova-notary`. It notarizes/staples/verifies
   the app and DMG and produces a new checksum/release manifest. Internal `--preview`
   images are explicitly not public releases.
4. Upload the new DMG and adjacent manifest into a NEW versioned directory on the
   release server. Update `AEDROVA_DOWNLOAD_PATH` and `AEDROVA_DOWNLOAD_SHA256`, verify
   the staging release and restart/roll the backend so its verified configuration points
   to that version. Do not overwrite a DMG in place while it is being downloaded.
5. The website download link serves that verified version. Existing clients use
   Help → Check for updates to compare their bundled version with `/api/release`.
   If newer and compatible, they can open the download page.
6. The user downloads the new DMG, quits Aedrova, drags the replacement into Applications
   and reopens. Their account data in Supabase, user preferences and original project
   files live outside the app bundle. Retain the previous app until the new one works.

The current updater is explicit/manual. There is no silent self-update, background
installation, delta patching or automatic GitHub-to-DMG publishing. Automatic installation
would be a separate approved feature with signed update metadata, rollback and release
acceptance. Backend-only changes can be deployed independently when backwards compatible;
database changes should support both old and new desktop versions during rollout.

Public downloads remain gated by the outstanding Developer ID, notarization, HTTPS
hosting and fresh-Mac acceptance described in milestone-11-release.md. A locally rebuilt
preview DMG does not open the public website download automatically.
