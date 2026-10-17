# Native Aedrova app icon

`Aedrova.icon` is the macOS Icon Composer source. It preserves the existing
Aedrova artwork as a foreground layer and uses a quiet light base, charcoal dark
base and system-controlled mono material for Clear and Tinted. Tint hue/strength,
Always/Auto and the chosen appearance belong to macOS, not Aedrova's chat theme.
No generated replacement logo or additional in-app setting is needed.

The foreground canvas is framed from the original transparent artwork using the
same visible bounds/780px placement as `scripts/prepare_brand_icon.py`. The original
logo remains untouched. Native masks and lighting are applied by Apple's renderer.

`scripts/macos_icon.py` invokes Xcode's `actool`, installs `Assets.car` and the
compatible `Aedrova.icns` into `Contents/Resources`, and returns the compiler's
`CFBundleIconName`/`CFBundleIconFile` metadata. Both `package_desktop.py` and
`staging_macos.py` do this **before signing**. Compiler failure fails the build;
do not silently omit adaptive icons. Xcode 26+ with the macOS SDK is required.
Unbundled source and Windows retain the existing static icon. Bundled macOS code
does not set a Qt runtime icon when the native catalog is installed, which would
otherwise replace the system rendition.

Validation: compile the catalog, inspect its generated Info.plist, and use the
Icon Composer `ictool --export-image` command for Default, Dark, ClearLight,
ClearDark, TintedLight and TintedDark. Inspect at small sizes as well as 512px.
Then restart a newly built app and test each icon style in macOS Appearance.
Finder/Dock may cache the icon of an already-running/installed older bundle;
updating source alone does not update an existing distributed installation.

Official reference: [Creating your app icon using Icon Composer](https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer).
