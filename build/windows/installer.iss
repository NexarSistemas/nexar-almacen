[Setup]
AppName=NexarStock
AppVersion=1.0
DefaultDirName={pf}\NexarStock
OutputDir=Output
OutputBaseFilename=NexarStockInstaller

[Files]
Source: "dist\app.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\NexarStock"; Filename: "{app}\app.exe"