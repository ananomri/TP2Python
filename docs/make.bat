@ECHO OFF
REM Utilisation :  make html   (résultat : _build\html\index.html)
if "%SPHINXBUILD%" == "" set SPHINXBUILD=sphinx-build
if "%1" == "" goto help
if "%1" == "clean" ( rmdir /s /q _build & goto end )
%SPHINXBUILD% -b %1 . _build\%1
goto end
:help
echo Utilisation : make html
:end
