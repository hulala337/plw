#define MyAppName "鹈鹕工作台"
#ifndef MyAppVersion
#define MyAppVersion "3.6.0"
#endif
#define MyAppPublisher "TF7Z-XY"
#define MyAppExeName "PelicanWorkbench.exe"
[Setup]
AppId={{B6D1C8B4-0C1C-4A43-A3AD-5F5CB35D7B21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PelicanWorkbench
DefaultGroupName={#MyAppName}
OutputDir=..\release
OutputBaseFilename=PelicanWorkbench_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
[Files]
Source: "..\dist\PelicanWorkbench.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："
Name: "startup"; Description: "登录 Windows 后自动启动到系统托盘"; GroupDescription: "启动："
[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PelicanWorkbench"; ValueData: """{app}\{#MyAppExeName}"" --tray"; Tasks: startup
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动鹈鹕工作台"; Flags: nowait postinstall skipifsilent
