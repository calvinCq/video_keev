@echo off
cls

:: GitHub上传命令指导文件
echo ===================================================================
echo                      GITHUB 上传命令指导
echo ===================================================================
echo.
echo 此文件包含将当前项目上传到GitHub所需的所有命令和步骤。
echo 请按照以下步骤手动执行命令。
echo.
echo ===================================================================
echo.

:: 步骤1: 检查Git是否安装
echo 【步骤1: 检查Git安装】
echo 请运行以下命令检查Git是否安装:
echo git --version
echo.

:: 步骤2: 创建GitHub仓库
echo 【步骤2: 创建GitHub仓库】
echo 1. 打开浏览器，访问 https://github.com/new
echo 2. 输入仓库名称: video_keev
echo 3. 不要勾选任何初始化选项(README, .gitignore, license)
echo 4. 点击 "Create repository"
echo 5. 复制创建后的仓库URL
echo.

:: 步骤3: 创建Personal Access Token
echo 【步骤3: 创建访问令牌】
echo 1. 访问 https://github.com/settings/tokens/new
echo 2. 设置token名称，如 "local-dev-token"
echo 3. 勾选 "repo" 权限
echo 4. 点击 "Generate token"
echo 5. 复制并保存生成的token
echo.

:: 步骤4: 初始化Git仓库(如果尚未初始化)
echo 【步骤4: 初始化Git仓库】
echo 请复制并运行以下命令:
echo @echo off
echo git init
echo git config --global user.name "YOUR_GITHUB_USERNAME"
echo git config --global user.email "YOUR_EMAIL@example.com"
echo.

:: 步骤5: 创建.gitignore文件
echo 【步骤5: 创建.gitignore文件】
echo @echo off
echo echo # OS generated files^>^>.gitignore
echo echo .DS_Store^>^>^>.gitignore
echo echo .DS_Store?^>^>^>.gitignore
echo echo ._^*>>.gitignore
echo echo .Spotlight-V100^>^>^>.gitignore
echo echo .Trashes^>^>^>.gitignore
echo echo ehthumbs.db^>^>^>.gitignore
echo echo Thumbs.db^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Python^>^>^>.gitignore
echo echo __pycache__/^>^>^>.gitignore
echo echo *.py[cod]^>^>^>.gitignore
echo echo *$py.class^>^>^>.gitignore
echo echo *.so^>^>^>.gitignore
echo echo .Python^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Virtual Environment^>^>^>.gitignore
echo echo venv/^>^>^>.gitignore
echo echo env/^>^>^>.gitignore
echo echo ENV/^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # IDE^>^>^>.gitignore
echo echo .vscode/^>^>^>.gitignore
echo echo .idea/^>^>^>.gitignore
echo echo *.swp^>^>^>.gitignore
echo echo *.swo^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Environment variables^>^>^>.gitignore
echo echo .env^>^>^>.gitignore
echo echo .env.local^>^>^>.gitignore
echo echo .env.development.local^>^>^>.gitignore
echo echo .env.test.local^>^>^>.gitignore
echo echo .env.production.local^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Logs^>^>^>.gitignore
echo echo *.log^>^>^>.gitignore
echo echo logs/^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Outputs^>^>^>.gitignore
echo echo outputs/^>^>^>.gitignore
echo echo temp/^>^>^>.gitignore
echo echo.^>^>^>.gitignore
echo echo # Test reports^>^>^>.gitignore
echo echo test_report.txt^>^>^>.gitignore
echo echo test_run.log^>^>^>.gitignore
echo.

:: 步骤6: 提交文件
echo 【步骤6: 提交文件】
echo @echo off
echo git add .
echo git commit -m "Initial commit"
echo.

:: 步骤7: 添加远程仓库
echo 【步骤7: 添加远程仓库】
echo 请将YOUR_GITHUB_USERNAME替换为您的GitHub用户名，然后运行:
echo @echo off
echo git remote add origin https://github.com/YOUR_GITHUB_USERNAME/video_keev.git
echo git branch -M main
echo.

:: 步骤8: 推送到GitHub
echo 【步骤8: 推送到GitHub】
echo @echo off
echo echo 请在提示输入凭据时:
echo echo - 用户名: 输入您的GitHub用户名
echo echo - 密码: 输入您的Personal Access Token
echo git push -u origin main
echo.

:: 常见问题解决
echo ===================================================================
echo                      常见问题解决
echo ===================================================================
echo 1. 如果推送失败，错误为 "remote: Repository not found"
echo    解决方法: 确保GitHub用户名正确，且仓库已创建
echo.
echo 2. 如果推送失败，错误为 "remote: Permission to ... denied"
echo    解决方法: 确保您的Personal Access Token有正确的权限
echo.
echo 3. 如果本地已存在git仓库，可以跳过初始化步骤
echo.
echo 4. 后续推送新更改时，只需要运行:
echo    git add .
echo    git commit -m "描述您的更改"
echo    git push
echo.
echo ===================================================================
echo.
echo 请按任意键退出...
pause