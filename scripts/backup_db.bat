@echo off
REM ============================================================
REM  cicek-deposu database backup script (Windows / mysqldump)
REM ============================================================
REM  What this does:
REM    1. Dumps the MySQL database to a timestamped .sql file
REM    2. Compresses it with 7-Zip if available, otherwise keeps
REM       the plain .sql file
REM    3. Deletes backups older than RETENTION_DAYS so the backup
REM       folder doesn't grow forever
REM
REM  One-time setup:
REM    1. Put this file somewhere permanent, e.g. C:\backups\backup_db.bat
REM    2. Edit the settings block below (DB name/user/password, paths)
REM    3. Test it by double-clicking it once and checking BACKUP_DIR
REM    4. Schedule it with Windows Task Scheduler:
REM       - Open "Task Scheduler" -> "Create Basic Task"
REM       - Trigger: Daily, pick a low-traffic time (e.g. 03:00)
REM       - Action: "Start a program" -> point to this .bat file
REM       - Under the task's Settings tab, enable "Run whether user
REM         is logged on or not" so it still runs if nobody's logged in
REM
REM  IMPORTANT: this backs up the DATABASE only. The media/ folder
REM  (product photos) is not in MySQL and needs to be backed up
REM  separately (see backup_media.bat) — copy it to the same external
REM  drive / cloud storage as the .sql dumps.
REM ============================================================

setlocal enabledelayedexpansion

REM --- Settings: edit these for your machine -------------------
set DB_NAME=shop_db
set DB_USER=root
set DB_PASSWORD=CHANGE_ME
set DB_HOST=127.0.0.1
set DB_PORT=3306

REM Where mysqldump.exe lives — adjust to your MySQL install path.
set MYSQLDUMP_PATH="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"

REM Where backups get written. Ideally NOT on the same physical disk
REM as the live server (an external drive, NAS, or synced cloud folder
REM like OneDrive/Google Drive is much safer than "next to the app").
set BACKUP_DIR=C:\backups\cicek-deposu

REM How many days of backups to keep before old ones get deleted.
set RETENTION_DAYS=14
REM --------------------------------------------------------------

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Build a sortable timestamp (YYYY-MM-DD_HHMMSS) that doesn't depend
REM on the machine's regional date format.
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%%datetime:~10,2%%datetime:~12,2%

set DUMP_FILE=%BACKUP_DIR%\%DB_NAME%_%TIMESTAMP%.sql

echo [%date% %time%] Starting backup of %DB_NAME% ...

%MYSQLDUMP_PATH% --host=%DB_HOST% --port=%DB_PORT% --user=%DB_USER% --password=%DB_PASSWORD% ^
    --single-transaction --routines --triggers --default-character-set=utf8mb4 ^
    %DB_NAME% > "%DUMP_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ERROR: mysqldump failed with exit code %ERRORLEVEL%.
    exit /b 1
)

echo [%date% %time%] Backup written to %DUMP_FILE%

REM Compress with 7-Zip if installed (much smaller for daily storage),
REM otherwise leave the plain .sql file as-is.
where 7z >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    7z a -tzip "%DUMP_FILE%.zip" "%DUMP_FILE%" >nul
    if !ERRORLEVEL! EQU 0 (
        del "%DUMP_FILE%"
        echo [%date% %time%] Compressed to %DUMP_FILE%.zip
    )
)

REM Delete backups older than RETENTION_DAYS.
forfiles /p "%BACKUP_DIR%" /m "%DB_NAME%_*.*" /d -%RETENTION_DAYS% /c "cmd /c del @path" 2>nul

echo [%date% %time%] Done.
endlocal
