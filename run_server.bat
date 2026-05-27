@echo off
echo =======================================================
echo     MENJALANKAN SERVER BACKEND CHATBOT (OPTIMAL)
echo =======================================================
echo.
echo Memastikan dependensi telah terinstal...
pip install -r requirements.txt > nul 2>&1
echo Dependensi siap.
echo.
echo Memulai server FastAPI...
echo.
python -m app.main --server
pause
