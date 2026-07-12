@echo off
title INSTALADOR - Gerador de Legendas
echo ====================================================
echo    CONFIGURANDO O AMBIENTE (PRIMEIRA EXECUCAO)
echo ====================================================
echo.

:: Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] O Python nao foi encontrado neste computador!
    echo Por favor, instale o Python e marque a opcao Add Python to PATH.
    echo.
    pause
    exit
)

echo [1/4] Criando o Ambiente Virtual isolado (VENV)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar o ambiente virtual.
    pause
    exit
)

echo [2/4] Ativando o ambiente virtual...
call venv\Scripts\activate

echo [3/4] Atualizando o gerenciador de pacotes (pip)...
python -m pip install --upgrade pip

echo.
echo ====================================================
echo    INSTALANDO O PYTORCH COM SUPORTE A GPU (CUDA)
echo    Isso garante a velocidade maxima do Whisper.
echo ====================================================
echo.
:: Remove o torch padrao caso exista para evitar conflitos
pip uninstall torch torchvision torchaudio -y >nul 2>&1

:: Instala a versao do PyTorch homologada para CUDA (GPU NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo [4/4] Instalando demais dependencias do projeto...
pip install -r requirements.txt

echo.
echo ====================================================
echo    INSTALACAO CONCLUIDA COM SUCESSO!
echo    Agora voce pode usar o arquivo INICIAR.bat
echo ====================================================
echo.
pause