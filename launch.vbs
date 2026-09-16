Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
exe = root & "\dist\CyrenePet\CyrenePet.exe"
If fso.FileExists(exe) Then
    shell.Run Chr(34) & exe & Chr(34), 0, False
Else
    MsgBox "Please run build.ps1 first.", 48, "Cyrene Pet"
End If
