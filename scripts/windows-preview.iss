[Setup]
AppId=Aedrova.Desktop.Preview
AppName=Aedrova Preview
AppVersion={#AppVersion}
AppPublisher=Aedrova
DefaultDirName={localappdata}\Programs\Aedrova Preview
DefaultGroupName=Aedrova Preview
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\windows-preview
OutputBaseFilename=Aedrova-Windows-Preview
SetupIconFile=..\src\aedrova\desktop\assets\aedrova.ico

[Files]
Source: "..\dist\windows-preview\Aedrova\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Aedrova Preview"; Filename: "{app}\Aedrova.exe"
