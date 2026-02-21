@echo off
:: Autor: Ing. Walter Rodriguez - 2026-02-20
:: run.bat - Inicia la aplicacion directamente (con consola, util para debug)
:: Para iniciar SIN consola, usa doble clic en: iniciar.vbs
cd /d "%~dp0"
python main.py
pause
