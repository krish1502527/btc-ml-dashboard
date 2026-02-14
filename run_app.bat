@echo off
echo ============================================
echo   BTC Prediction App Launcher
echo ============================================

REM --- Activate conda ---
call "C:\anaconda3\condabin\conda.bat" activate btc_ml

REM --- Go to project folder ---
cd /d "C:\Users\krish\OneDrive\Desktop\BITCOIN FINAL FOLDER FOR PREDICTION!"

REM --- Run Flask app ---
python app.py

echo.
echo ============================================
echo App stopped. Press any key to exit...
pause
