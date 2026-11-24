@echo off
pushd "%~dp0"
py -3 -X utf8 -m src %*
set "result=%errorlevel%"
popd
exit /b %result%
