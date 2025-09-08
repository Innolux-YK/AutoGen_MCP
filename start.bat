@echo off
chcp 65001 >nul 2>&1
cls
echo ====================================
echo       RAG System Startup Script
echo ====================================
echo.

:menu
echo Please select an operation:
echo 1. Install packages
echo 2. Document processing and indexing
echo 3. Start QA system
echo 4. Exit
echo.
set /p "choice=Please enter option (1-4): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto process
if "%choice%"=="3" goto run_qa
if "%choice%"=="4" goto exit

echo Invalid option, please try again!
echo.
pause
goto menu

:install
cls
echo.
echo Installing packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Package installation failed! Please check your network connection and Python environment.
    echo.
    pause
) else (
    echo.
    echo Package installation completed!
    echo.
    pause
)
goto menu

:process
cls
echo ====================================
echo         Document Processing Options
echo ====================================
echo Please select processing mode:
echo 1. Incremental processing ^(keep existing data, process new documents only^)
echo 2. Full reprocessing ^(clear all data and start fresh^)
echo 3. Return to main menu
echo.
set /p "process_choice=Please enter option (1-3): "

if "%process_choice%"=="1" goto incremental_process
if "%process_choice%"=="2" goto full_reprocess
if "%process_choice%"=="3" goto menu

echo Invalid option, please try again!
echo.
pause
goto process

:incremental_process
cls
echo.
echo Running incremental document processing...
echo This will preserve existing vector database and images, process new documents only
echo This may take a few minutes, please be patient...
echo.
echo Detailed process information will be shown below:
echo ====================================
call python document_processor.py --incremental
set "process_result=%errorlevel%"
echo ====================================
echo.
if "%process_result%"=="0" (
    echo [COMPLETED] Incremental processing finished!
) else (
    echo [ERROR] Document processing failed! Please check if there are document files in Dataset directory.
)
echo.
pause
goto menu

:full_reprocess
cls
echo ====================================
echo         Full Reprocessing Warning
echo ====================================
echo This operation will:
echo * Delete vector_db folder ^(all vector data^)
echo * Delete images folder ^(all extracted images^)
echo * Reprocess all documents and generate new vector database
echo.
echo This operation cannot be undone! Please confirm to continue.
echo.
set /p "confirm=Are you sure you want to fully reprocess? (y/n): "

if /i "%confirm%"=="y" goto do_full_reprocess
if /i "%confirm%"=="yes" goto do_full_reprocess
echo.
echo Operation cancelled.
echo.
pause
goto process

:do_full_reprocess
cls
echo.
echo Cleaning old data...

if exist "vector_db" (
    echo Deleting vector database...
    rmdir /s /q "vector_db" 2>nul
    echo - vector_db folder deleted
)

if exist "images" (
    echo Deleting image data...
    rmdir /s /q "images" 2>nul
    echo - images folder deleted
)

echo.
echo Data cleanup completed! Starting full reprocessing...
echo This may take a long time, please be patient...
echo.
echo Detailed process information will be shown below:
echo ====================================
call python document_processor.py --force-retrain
set "process_result=%errorlevel%"
echo ====================================
echo.
if "%process_result%"=="0" (
    echo [COMPLETED] Full reprocessing finished!
) else (
    echo [ERROR] Full reprocessing failed! Please check if there are document files in Dataset directory.
)
echo.
pause
goto menu

:run_qa
cls
echo.
echo Starting RAG Question-Answer System ..
echo.
python start_chat_app.py
goto menu

:exit
cls
echo.
echo Thank you for using!
echo.
pause
exit
