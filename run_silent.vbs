Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory

' Jalankan run_app.bat secara tersembunyi (0 = hide console window)
WshShell.Run "cmd /c """ & strPath & "\run_app.bat""", 0, False
