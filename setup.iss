; Script generated for Inno Setup - Cashflow Dashboard Installer
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Cashflow Dashboard"
#define MyAppVersion "2.0"
#define MyAppPublisher "sonics007"
#define MyAppURL "https://github.com/sonics007/cashflow_flexibee"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{C1F48C8B-9E3A-4F8C-8A9E-1B2C3D4E5F6G}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={src}
UsePreviousAppDir=no
CreateAppDir=no
OutputBaseFilename=CashflowSetup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "slovak"; MessagesFile: "compiler:Languages\Slovak.isl"

[Files]
; Pribalíme naše inštalačné skripty
Source: "install-windows.bat"; DestDir: "{tmp}"; Flags: ignoreversion
Source: "install-windows.ps1"; DestDir: "{tmp}"; Flags: ignoreversion

[Run]
; Spustíme inštalačný BAT súbor z dočasného adresára
Filename: "{tmp}\install-windows.bat"; Description: "Inštalovať Cashflow Dashboard"; Flags: waituntilterminated runascurrentuser

[Messages]
SetupWindowTitle=Inštalácia Cashflow Dashboard
WelcomeLabel2=Tento sprievodca nainštaluje Cashflow Dashboard na váš počítač.%n%nInštalátor automaticky:%n - Stiahne a nainštaluje Python%n - Stiahne najnovšiu verziu aplikácie%n - Nastaví Windows službu
