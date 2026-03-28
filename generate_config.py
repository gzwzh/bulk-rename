config_content = """[Application]
name=批量重命名
version=1.0.0
entry_point=launcher:main
icon=inco.ico
console=false

[Python]
version=3.11.0

[Include]
files=dist/批量重命名.exe
    inco.ico
    launcher.py > pkgs

[Build]
nsi_template=installer.nsi
"""
with open('installer.cfg', 'w', encoding='mbcs') as f:
    f.write(config_content)
