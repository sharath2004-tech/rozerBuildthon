@echo off
echo ============================================================
echo AI Revenue Recovery Dashboard - Next.js
echo ============================================================
echo.

REM Check if in recovery-agent-dashboard directory
if not exist "package.json" (
    echo ERROR: Must run from recovery-agent-dashboard directory
    echo Run: cd recovery-agent-dashboard
    pause
    exit /b 1
)

REM Check if pnpm is installed
where pnpm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo pnpm not found. Installing pnpm...
    call npm install -g pnpm
    echo.
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies with pnpm...
    call pnpm install
    echo.
)

echo Starting development server...
echo.
echo ============================================================
echo Dashboard will run on: http://localhost:3000
echo ============================================================
echo.
echo Press CTRL+C to stop
echo.

pnpm dev

pause
