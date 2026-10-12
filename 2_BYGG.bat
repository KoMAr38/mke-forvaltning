@echo off
cd /d "%~dp0"
echo === 1/4 dbt seed ===
call dbt seed --profiles-dir .
if errorlevel 1 (echo FEIL i dbt seed & pause & exit /b 1)
echo.
echo === 2/4 dbt run ===
call dbt run --profiles-dir .
if errorlevel 1 (echo FEIL i dbt run & pause & exit /b 1)
echo.
echo === 3/4 dbt test  (forventet: PASS=30 WARN=0 ERROR=0) ===
call dbt test --profiles-dir .
echo.
echo === 4/4 Eksport til data\mart ===
python src\eksport.py
if errorlevel 1 (echo FEIL i eksport & pause & exit /b 1)
echo.
echo Ferdig. Aapne powerbi\MKE_Eiendomsforvaltning.pbip og trykk Refresh.
pause
