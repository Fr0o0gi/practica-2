@echo off
pushd "%~dp0"
python -X utf8 -m src %*
set "result=%errorlevel%"
popd
exit /b %result%
