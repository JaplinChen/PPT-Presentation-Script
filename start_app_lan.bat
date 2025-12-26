@echo off
chcp 65001 > nul
echo ===========================================
echo   PPT 演講文稿生成器 - 啟動腳本
echo   正在啟動區域網路分享模式...
echo ===========================================

echo.
echo [1/2] 啟動後端伺服器 (Backend)...
echo 正在監聽: 0.0.0.0:8080
start "PPT_Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"

echo.
echo [2/2] 啟動前端伺服器 (Frontend)...
echo 正在監聽: 0.0.0.0:5173
cd frontend
start "PPT_Frontend" cmd /k "npm run dev"

echo.
echo ===========================================
echo   ✅ 伺服器已啟動！
echo.
echo   請確保兩個新的黑色視窗都保持開啟。
echo.
echo   👉 本機使用: http://localhost:5173
echo   👉 分享網址: http://192.168.90.186:5173
echo ===========================================
pause
