[Setup]
AppName=JARVIS Personal Desktop AI Assistant
AppVersion=1.0.0
AppPublisher=JARVIS AI Project
DefaultDirName={autopf}\JARVIS
DefaultGroupName=JARVIS
OutputBaseFilename=JARVIS-Setup-v1.0.0
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\JARVIS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\JARVIS"; Filename: "{app}\JARVIS.exe"
Name: "{autodesktop}\JARVIS"; Filename: "{app}\JARVIS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\JARVIS.exe"; Description: "{cm:LaunchProgram,JARVIS}"; Flags: nowait postinstall skipifsilent
