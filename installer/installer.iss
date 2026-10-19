; Inno Setup 6 Script for PRUBETH
; Codename: PRUBETH
; Official Website: https://www.bsvr.work/

#define MyAppName "PRUBETH"
#define MyAppVersion "1.91.0"
#define MyAppPublisher "BSVR Technologies"
#define MyAppURL "https://www.bsvr.work/"
#define MyAppExeName "PRUBETH.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{9F3B2E4A-8C1D-4E5F-B7A2-123456789ABC}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=PRUBETH-v1.91.0-Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.91.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductVersion=1.91.0.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\PrubethIDE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\..\dist\PrubethIDE'))
Source: "..\assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\logo.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\default_settings.json"; DestDir: "{userappdata}\PRUBETH\User"; DestName: "settings.json"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "..\assets\chatLanguageModels.json"; DestDir: "{userappdata}\PRUBETH\User"; DestName: "chatLanguageModels.json"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "..\vscode\extensions\prubeth-ai\*"; DestDir: "{app}\resources\app\extensions\prubeth-ai"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\..\vscode\extensions\prubeth-ai'))

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Visit Website (bsvr.work)"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Register website and project links in Windows Add/Remove Programs
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#MyAppURL}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "HelpLink"; ValueData: "https://www.bsvr.work/#projects"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"; Flags: uninsdeletekey

[Code]
function DirExists(Dir: String): Boolean;
begin
  Result := DirExists(Dir);
end;
