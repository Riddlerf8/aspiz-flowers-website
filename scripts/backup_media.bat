@echo off
REM ============================================================
REM  cicek-deposu media backup script (product/category photos)
REM ============================================================
REM  mysqldump only backs up the DATABASE — product photos live on
REM  disk in media/, not in MySQL, so they need their own backup.
REM  This mirrors media/ to BACKUP_DIR using robocopy (built into
REM  Windows, incremental — only copies new/changed files after the
REM  first run, so it's fast to run daily).
REM
REM  Schedule this the same way as backup_db.bat in Task Scheduler,
REM  right after the DB backup job.
REM ============================================================

REM --- Settings: edit these for your machine -------------------
set SOURCE_DIR=C:\path\to\p-up\media
set BACKUP_DIR=C:\backups\cicek-deposu\media
REM --------------------------------------------------------------

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo [%date% %time%] Mirroring %SOURCE_DIR% to %BACKUP_DIR% ...

REM /MIR mirrors the source exactly (including deletions), /R:3 retries
REM a locked file 3 times, /W:5 waits 5 seconds between retries, /NFL
REM and /NDL keep the log output short.
robocopy "%SOURCE_DIR%" "%BACKUP_DIR%" /MIR /R:3 /W:5 /NFL /NDL

REM robocopy's exit codes 0-7 all mean success (different combinations
REM of "files copied" / "no changes"); 8+ means a real error.
if %ERRORLEVEL% GEQ 8 (
    echo [%date% %time%] ERROR: robocopy failed with exit code %ERRORLEVEL%.
    exit /b 1
)

echo [%date% %time%] Done.
