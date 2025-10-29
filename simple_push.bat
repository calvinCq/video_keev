@echo off
cls

:: 简化的GitHub推送脚本
echo ==============================================
echo            SIMPLE GITHUB PUSH
echo ==============================================
echo.

:: 设置GitHub信息
set GITHUB_USERNAME=calvinCq
set REPO_NAME=video_keev
set REMOTE_URL=https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

echo 使用配置:
echo - GitHub用户名: %GITHUB_USERNAME%
echo - 仓库名称: %REPO_NAME%
echo - 仓库URL: %REMOTE_URL%
echo.

:: 检查Git是否可用
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Git! 请先安装Git。
    echo Git下载地址: https://git-scm.com/download/win
    pause
    exit /b 1
)

:: 检查Git版本
echo Git版本:
git --version
echo.

:: 检查是否有.git目录
if not exist .git (
    echo 初始化Git仓库...
    git init
    
    :: 创建.gitignore文件（如果不存在）
    if not exist .gitignore (
        echo 创建.gitignore文件...
        (echo # OS generated files
         echo .DS_Store
         echo .DS_Store?
         echo ._*
         echo .Spotlight-V100
         echo .Trashes
         echo ehthumbs.db
         echo Thumbs.db
         echo.
         echo # Python
         echo __pycache__/
         echo *.py[cod]
         echo *$py.class
         echo *.so
         echo .Python
         echo.
         echo # Virtual Environment
         echo venv/
         echo env/
         echo ENV/
         echo.
         echo # IDE
         echo .vscode/
         echo .idea/
         echo *.swp
         echo *.swo
         echo.
         echo # Environment variables
         echo .env
         echo .env.local
         echo .env.development.local
         echo .env.test.local
         echo .env.production.local
         echo.
         echo # Logs
         echo *.log
         echo logs/
         echo.
         echo # Outputs
         echo outputs/
         echo temp/
         echo.
         echo # Test reports
         echo test_report.txt
         echo test_run.log) > .gitignore
    )
    
    echo 添加文件到Git...
    git add .
    
    echo 提交文件...
    git commit -m "Initial commit"
)

:: 设置远程仓库
echo 设置远程仓库...
git remote remove origin 2>nul
git remote add origin %REMOTE_URL%
git branch -M main

echo 远程仓库配置:
git remote -v
echo.

:: 重要提示
echo ==============================================
echo 重要提示:
echo 当Git提示输入凭据时:
echo - 用户名: %GITHUB_USERNAME%
echo - 密码: 请输入您的Personal Access Token (不是GitHub密码)
echo ==============================================
echo.
echo 注意: 如果您没有Personal Access Token，请先在GitHub上创建一个
echo 访问 https://github.com/settings/tokens/new 并勾选'repo'权限
echo.

:: 等待用户确认
echo 准备推送代码到GitHub...
echo 按任意键继续，或按Ctrl+C取消...
pause >nul

:: 执行推送
echo 正在推送代码...
git push -u origin main

:: 检查结果
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==============================================
    echo 成功! 代码已推送到GitHub。
    echo 仓库地址: %REMOTE_URL%
    echo ==============================================
) else (
    echo.
    echo ==============================================
    echo 推送失败! 请检查以下几点:
    echo 1. 确保仓库 '%REPO_NAME%' 已在GitHub上创建
    echo 2. 确保Personal Access Token正确且有'repo'权限
    echo 3. 检查网络连接
    echo ==============================================
)

echo.
echo 按任意键退出...
pause