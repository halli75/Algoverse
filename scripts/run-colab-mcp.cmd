@echo off
set FASTMCP_SHOW_CLI_BANNER=false
set FASTMCP_SHOW_SERVER_BANNER=false
set PYTHONWARNINGS=ignore
"C:\Users\arnav\.local\bin\uvx.exe" git+https://github.com/googlecolab/colab-mcp %*
