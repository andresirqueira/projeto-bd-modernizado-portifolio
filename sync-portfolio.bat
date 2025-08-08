@echo off
echo 🔄 Iniciando sincronização do portfólio...
echo.

echo [INFO] Atualizando projeto principal...
cd ..

echo [INFO] Fazendo commit das mudanças no projeto principal...
git add .
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "datestamp=%YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"
git commit -m "Atualização automática - %datestamp%"
git push origin main
echo [SUCCESS] Projeto principal atualizado!

echo.
echo [INFO] Atualizando clone do portfólio...
cd projeto-bd-modernizado-portifolio

echo [INFO] Buscando mudanças do upstream...
git fetch upstream

echo [INFO] Fazendo merge das mudanças...
git merge upstream/main

echo [INFO] Enviando para o repositório do portfólio...
git push origin main

echo [SUCCESS] Clone do portfólio atualizado!

echo.
echo [SUCCESS] ✅ Sincronização completa!
echo [INFO] O Render deve fazer deploy automático em alguns minutos.
echo.
echo [WARNING] 💡 Dica: Execute este script sempre que fizer mudanças importantes no projeto principal.
pause
