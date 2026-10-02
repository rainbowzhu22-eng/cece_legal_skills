on run
    set scriptsPath to "__SCRIPTS_PATH__"
    set pythonPath to scriptsPath & ".venv/bin/python"
    set launcherPath to scriptsPath & "launcher/start.py"
    try
        do shell script (quoted form of pythonPath) & " " & (quoted form of launcherPath)
    on error errorMessage
        display alert "合同脱敏启动失败" message errorMessage as critical
    end try
end run
