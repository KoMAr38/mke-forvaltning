@echo off
cd /d "%~dp0"
echo Lager modellen (TMDL), bakgrunnsbildene og rapporten (PBIR) paa nytt fra src\powerbi.
echo Endringer du har lagret i Power BI Desktop blir overskrevet. Lukk Desktop foerst.
pause
python src\powerbi\lag_modell.py
if errorlevel 1 (echo FEIL i lag_modell & pause & exit /b 1)
python src\powerbi\lag_bilder.py 30
if errorlevel 1 (echo FEIL i lag_bilder & pause & exit /b 1)
python src\powerbi\lag_rapport.py 30
if errorlevel 1 (echo FEIL i lag_rapport & pause & exit /b 1)
echo.
echo Ferdig.
pause
