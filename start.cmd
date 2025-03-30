@echo off
chcp 65001 >nul 2>&1  :: Устанавливаем кодировку UTF-8 для консоли

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не найден. Убедитесь, что Python установлен и добавлен в PATH.
    pause
    exit /b
)

:: Создание виртуального окружения, если оно не существует
if not exist venv (
    echo Создаётся виртуальное окружение...
    python -m venv venv
)

:: Активация виртуального окружения
call venv\Scripts\activate

:: Установка зависимостей
echo Устанавливаются зависимости...
python.exe -m pip install --upgrade pip >nul
pip install -r requirements.txt

:: Запуск программы
echo Запуск программы...
python autologin.py

:: Завершение
echo Программа завершила работу.
pause