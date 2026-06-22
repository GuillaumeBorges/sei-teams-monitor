#define AppName "SEI Monitor CGTEC"
#define AppVersion "1.0"
#define AppPublisher "CGTEC — Ministerio da Justica e Seguranca Publica"
#define AppExeName "SEI-Monitor-Setup.exe"
#define InstallDir "{localappdata}\SEI-Monitor"

[Setup]
AppId={{F4A2B3C1-8E7D-4F9A-B2C3-D4E5F6A7B8C9}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={#InstallDir}
DisableDirPage=yes
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=SEI-Monitor-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\scripts\run_windows.bat
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Scripts principais
Source: "..\sei_monitor.py";          DestDir: "{app}"; Flags: ignoreversion
Source: "..\teams_notifier.py";       DestDir: "{app}"; Flags: ignoreversion
Source: "..\db.py";                   DestDir: "{app}"; Flags: ignoreversion
Source: "..\setup_login.py";          DestDir: "{app}"; Flags: ignoreversion
Source: "..\setup_wizard.py";         DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt";        DestDir: "{app}"; Flags: ignoreversion
Source: "..\config.yaml";             DestDir: "{app}"; Flags: ignoreversion
Source: "..\GUIA_INSTALACAO_WINDOWS.md"; DestDir: "{app}"; Flags: ignoreversion

; Scripts de execucao e agendamento
Source: "..\scripts\run_windows.bat";           DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "..\scripts\install_task_windows.ps1";  DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "..\scripts\instalar_windows.bat";      DestDir: "{app}\scripts"; Flags: ignoreversion

; Script de pos-instalacao
Source: "pos_instalacao.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Fazer Login no SEI (renovar sessao)"; Filename: "{app}\setup_login.py"; IconFilename: "{sys}\shell32.dll"; IconIndex: 13
Name: "{group}\Desinstalar {#AppName}";              Filename: "{uninstallexe}"

[Run]
Filename: "{app}\pos_instalacao.bat"; \
    Description: "Finalizar instalacao (instalar dependencias e fazer login no SEI)"; \
    Flags: postinstall shellexec runasoriginaluser; \
    WorkingDir: "{app}"

[UninstallRun]
Filename: "powershell.exe"; \
    Parameters: "-ExecutionPolicy Bypass -Command ""Unregister-ScheduledTask -TaskName 'SEI Monitor - Aviso Teams' -Confirm:$false -ErrorAction SilentlyContinue"""; \
    Flags: runhidden

[Code]
function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Result := Exec('py', '-3 --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  Response: Integer;
begin
  Result := True;
  if not IsPythonInstalled() then begin
    Response := MsgBox(
      'Python nao foi encontrado no seu computador.' + #13#10 + #13#10 +
      'Clique em SIM para abrir o site de download do Python.' + #13#10 +
      'Marque "Add Python to PATH" durante a instalacao.' + #13#10 + #13#10 +
      'Depois de instalar o Python, execute este instalador novamente.',
      mbConfirmation, MB_YESNO);
    if Response = IDYES then
      ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ResultCode);
    Result := False;
  end;
end;
