@echo off
:: Configura o terminal para aceitar caracteres especiais em português (UTF-8)
chcp 65001 >nul
cls

echo ===================================================
echo   🎾 ANALISADOR BIOMECÂNICO - TÊNIS E VÔLEI 🏐
echo ===================================================
echo.

:: 1. Tenta encontrar se o Python ou o Launcher do Python está disponível no sistema
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto PYTHON_ENCONTRADO
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto PYTHON_ENCONTRADO
)

:: Se chegou aqui, nenhum comando de Python foi reconhecido
echo [ERRO CRÍTICO] O Python não foi encontrado ou não está no PATH do Windows!
echo.
echo COMO RESOLVER:
echo 1. Reinstale o Python que está no seu pendrive.
echo 2. IMPORTANTE: Na primeira tela de instalação, marque obrigatoriamente
echo    a caixinha "Add Python to.exe to PATH" (Adicionar Python ao PATH).
echo.
pause
exit /b

:PYTHON_ENCONTRADO
echo [OK] Python detectado com sucesso usando o comando: %PY_CMD%
echo.

:: 2. Verifica se o arquivo requirements.txt existe
if not exist "requirements.txt" (
    echo [ERRO] O arquivo "requirements.txt" não foi encontrado nesta pasta!
    echo.
    pause
    exit /b
)

:: 3. Instala as dependências de forma automática
echo [1/2] Verificando e instalando dependências (Streamlit, Plotly, MediaPipe)...
echo (Isso pode levar alguns segundos na primeira execução com internet)
echo.
%PY_CMD% -m pip install --upgrade pip >nul 2>&1
%PY_CMD% -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] Houve um problema na instalação automática.
    echo Verifique sua conexão com a internet para baixar os pacotes na primeira vez.
    echo.
    pause
)

echo.
echo ===================================================
echo [2/2] Iniciando o Servidor Local do Analisador...
echo ===================================================
echo O aplicativo abrirá automaticamente no seu navegador.
echo Para fechar o sistema, basta fechar esta janela preta.
echo.

:: 4. Executa o Streamlit usando o comando de Python correto detectado
%PY_CMD% -m streamlit run app.py

pause