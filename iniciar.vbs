' Autor: Ing. Walter Rodriguez - 2026-02-20
' Lanzador invisible para Avatar IA
' Abre la aplicacion Python sin ninguna ventana de consola (WindowStyle = 0)
Dim oShell, sDir
Set oShell = CreateObject("WScript.Shell")
sDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
oShell.Run "python """ & sDir & "\main.py""", 0, False
Set oShell = Nothing
