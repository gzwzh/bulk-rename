import os

dist_dir = r"C:\Users\admin\Desktop\总任务\任务二-鲲穹AI文件批量重命名\bulk_rename_tool\dist"
# 使用英文文件名避免 IExpress 处理中文路径/文件名的潜在 bug
target_name = os.path.join(dist_dir, "setup_v1.0.0.exe")

sed_content = f"""[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=Install Batch Rename Tool?
DisplayLicense=
FinishMessage=Install Complete!
TargetName="{target_name}"
FriendlyName=Batch Rename Installer
AppLaunched=cmd /c install.bat
PostInstallCmd=<None>
[SourceFiles]
SourceFiles0={dist_dir}\\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
%FILE3%=
"""

# Add files
sed_content = sed_content.replace("%FILE0%=", "批量重命名.exe=")
sed_content = sed_content.replace("%FILE1%=", "updater.exe=")
sed_content = sed_content.replace("%FILE2%=", "install.bat=")
sed_content = sed_content.replace("%FILE3%=", "批量重命名工具.png=")

# 使用 ANSI 编码写入，因为 IExpress 是老旧程序
with open(os.path.join(dist_dir, "setup.sed"), "w", encoding="mbcs") as f:
    f.write(sed_content)

print(f"SED file created with TargetName: {target_name}")
