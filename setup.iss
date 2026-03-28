; Inno Setup 脚本
; 批量重命名 安装程序

[Setup]
AppName=批量重命名
AppVersion=1.0.0
AppPublisher=鲲穹AI
AppPublisherURL=https://www.example.com
AppSupportURL=https://www.example.com
AppUpdatesURL=https://www.example.com
DefaultDirName={autopf}\批量重命名
DefaultGroupName=批量重命名
AllowNoIcons=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=批量重命名_安装程序
SetupIconFile=批量重命名工具.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
; 支持静默安装
; SilentInstall=yes removed as it is not a valid directive
; 静默安装时不显示进度窗口
ShowTasksTreeLines=no

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "desktopicon\silent"; Description: "静默安装时创建桌面图标"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\批量重命名.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "批量重命名工具.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "鲲穹01.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\批量重命名"; Filename: "{app}\批量重命名.exe"; IconFilename: "{app}\批量重命名工具.ico"
Name: "{group}\{cm:UninstallProgram,批量重命名}"; Filename: "{uninstallexe}"
; 普通安装时的桌面图标
Name: "{autodesktop}\批量重命名"; Filename: "{app}\批量重命名.exe"; IconFilename: "{app}\批量重命名工具.ico"; Tasks: desktopicon
; 静默安装时自动创建桌面图标
Name: "{autodesktop}\批量重命名"; Filename: "{app}\批量重命名.exe"; IconFilename: "{app}\批量重命名工具.ico"; Check: WizardSilent

[Run]
Filename: "{app}\批量重命名.exe"; Description: "{cm:LaunchProgram,批量重命名}"; Flags: nowait postinstall skipifsilent

[Code]
// 检查是否为静默安装
function WizardSilent: Boolean;
begin
  Result := WizardSilent();
end;

// 静默安装时的初始化函数
function InitializeSetup(): Boolean;
begin
  Result := True;
  // 如果是静默安装，自动选择创建桌面图标
  if WizardSilent then
  begin
    // 静默安装时的默认设置
    Log('静默安装模式：将自动创建桌面快捷方式');
  end;
end;
