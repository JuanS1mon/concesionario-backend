@echo off
echo Inicializando repositorio Git para el backend...

REM Verificar si git está instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git no está instalado. Por favor instala Git primero.
    pause
    exit /b 1
)

REM Inicializar repositorio
git init

REM Agregar archivos
git add .

REM Crear commit inicial
git commit -m "Initial commit: FastAPI backend for car dealership"

echo.
echo Repositorio backend inicializado correctamente.
echo.
echo Próximos pasos:
echo 1. Crear repositorio en GitHub llamado 'concesionario-backend'
echo 2. Ejecutar: git remote add origin https://github.com/TU_USUARIO/concesionario-backend.git
echo 3. Ejecutar: git push -u origin main
echo.
pause