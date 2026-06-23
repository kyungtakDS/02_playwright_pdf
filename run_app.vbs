Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = "C:\miniconda3\envs\flood_risk311\pythonw.exe"
script = """" & scriptDir & "\gui_app.py" & """"

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = scriptDir
shell.Run """" & pythonw & """ " & script, 0, False
