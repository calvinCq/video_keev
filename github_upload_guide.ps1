# GitHub项目上传指导脚本
# 这个脚本将帮助您将当前项目上传到GitHub

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "GitHub 项目上传指导" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host

# 步骤1: 验证Git安装
Write-Host "【步骤1: 检查Git安装】" -ForegroundColor Yellow
$gitPath = $null
$commonGitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Git\bin\git.exe"
)

foreach ($path in $commonGitPaths) {
    if (Test-Path $path) {
        $gitPath = $path
        Write-Host "✓ Git已安装，路径: $gitPath" -ForegroundColor Green
        break
    }
}

if (-not $gitPath) {
    Write-Host "✗ 未找到Git! 请先安装Git." -ForegroundColor Red
    Write-Host "Git下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "安装完成后按Enter继续，或按Ctrl+C退出"
    # 重新检查Git
    foreach ($path in $commonGitPaths) {
        if (Test-Path $path) {
            $gitPath = $path
            Write-Host "✓ Git已安装，路径: $gitPath" -ForegroundColor Green
            break
        }
    }
    if (-not $gitPath) {
        Write-Host "✗ 仍然未找到Git，无法继续." -ForegroundColor Red
        Read-Host "按Enter退出"
        exit 1
    }
}

# 显示Git版本
Write-Host "Git版本:"
& $gitPath --version
Write-Host

# 步骤2: 设置GitHub信息
Write-Host "【步骤2: 设置GitHub信息】" -ForegroundColor Yellow
Write-Host "请输入您的GitHub用户名(非邮箱):"
$username = Read-Host

if (-not $username) {
    Write-Host "✗ GitHub用户名不能为空!" -ForegroundColor Red
    Read-Host "按Enter退出"
    exit 1
}

Write-Host "请输入您要创建/使用的仓库名称(默认为video_keev):"
$repoName = Read-Host
if (-not $repoName) {
    $repoName = "video_keev"
}

# 步骤3: 检查并初始化Git仓库
Write-Host "【步骤3: Git仓库初始化】" -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "创建新的Git仓库..."
    & $gitPath init
    
    # 创建.gitignore文件
    if (-not (Test-Path ".gitignore")) {
        Write-Host "创建.gitignore文件..."
        $gitignoreContent = @"
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
*.log
logs/

# Outputs
outputs/
temp/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Test reports
test_report.txt
test_run.log
"@
        $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding utf8
        Write-Host "✓ .gitignore文件已创建" -ForegroundColor Green
    }
    
    # 添加所有文件
    Write-Host "添加所有文件到Git..."
    & $gitPath add .
    
    # 提交文件
    Write-Host "创建初始提交..."
    & $gitPath commit -m "Initial commit"
} else {
    Write-Host "✓ Git仓库已存在" -ForegroundColor Green
    Write-Host "检查仓库状态:"
    & $gitPath status --short
    
    # 如果有未提交的更改，提示用户
    $statusOutput = & $gitPath status --porcelain
    if ($statusOutput) {
        Write-Host "发现未提交的更改，是否提交? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq "Y" -or $response -eq "y") {
            & $gitPath add .
            Write-Host "请输入提交信息:"
            $commitMsg = Read-Host
            if (-not $commitMsg) {
                $commitMsg = "Update files"
            }
            & $gitPath commit -m $commitMsg
        }
    }
}
Write-Host

# 步骤4: 创建GitHub仓库(提供手动指导)
Write-Host "【步骤4: 创建GitHub仓库】" -ForegroundColor Yellow
Write-Host "请在GitHub网站上手动创建仓库:"
Write-Host "1. 访问 https://github.com/new" -ForegroundColor Cyan
Write-Host "2. 仓库名称: $repoName" -ForegroundColor Cyan
Write-Host "3. 保持仓库为空(不勾选README, .gitignore或license)" -ForegroundColor Cyan
Write-Host "4. 点击'Create repository'按钮" -ForegroundColor Cyan
Write-Host
Write-Host "仓库创建完成后按Enter继续..."
Read-Host

# 步骤5: 设置远程仓库
Write-Host "【步骤5: 设置远程仓库】" -ForegroundColor Yellow
$remoteUrl = "https://github.com/$username/$repoName.git"
Write-Host "设置远程仓库URL: $remoteUrl"

# 移除现有的origin(如果有)
& $gitPath remote remove origin 2>$null

# 添加新的origin
& $gitPath remote add origin $remoteUrl

# 设置主分支为main
& $gitPath branch -M main

# 显示远程配置
Write-Host "远程仓库配置:"
& $gitPath remote -v
Write-Host

# 步骤6: 创建Personal Access Token(提供手动指导)
Write-Host "【步骤6: 创建Personal Access Token (PAT)】" -ForegroundColor Yellow
Write-Host "重要: 现在需要创建GitHub Personal Access Token用于身份验证:"
Write-Host "1. 访问 https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "2. 设置Token名称(如'local-dev-token')" -ForegroundColor Cyan
Write-Host "3. 设置过期时间(建议选择适当的时间)" -ForegroundColor Cyan
Write-Host "4. 勾选'repo'权限(完整仓库访问权限)" -ForegroundColor Cyan
Write-Host "5. 滚动到底部，点击'Generate token'" -ForegroundColor Cyan
Write-Host "6. 复制生成的token并保存，关闭页面后将无法再次看到!" -ForegroundColor Cyan
Write-Host
Write-Host "Token创建并复制后按Enter继续..."
Read-Host

# 步骤7: 推送代码
Write-Host "【步骤7: 推送代码到GitHub】" -ForegroundColor Yellow
Write-Host "现在将使用您的GitHub凭据推送代码"
Write-Host "当Git提示输入凭据时:"
Write-Host "- 用户名: $username" -ForegroundColor Cyan
Write-Host "- 密码: 使用刚才创建的Personal Access Token，而不是GitHub密码" -ForegroundColor Cyan
Write-Host
Write-Host "按Enter开始推送..."
Read-Host

# 执行推送
Write-Host "正在推送代码到GitHub..."
& $gitPath push -u origin main

# 检查结果
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 成功! 代码已成功推送到GitHub!" -ForegroundColor Green
    Write-Host "仓库URL: $remoteUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "后续操作提示:"
    Write-Host "1. 可以在浏览器中访问仓库URL查看您的代码"
    Write-Host "2. 定期使用 'git push' 推送新的更改"
    Write-Host "3. 记得安全保存您的Personal Access Token"
} else {
    Write-Host ""
    Write-Host "❌ 推送失败! 请检查以下几点:" -ForegroundColor Red
    Write-Host "1. GitHub用户名是否正确: $username"
    Write-Host "2. 仓库名是否正确: $repoName"
    Write-Host "3. 仓库是否已在GitHub上创建"
    Write-Host "4. Personal Access Token是否包含'repo'权限"
    Write-Host "5. 网络连接是否正常"
    Write-Host ""
    Write-Host "错误解决建议:"
    Write-Host "- 重新检查并创建正确的Personal Access Token"
    Write-Host "- 确认仓库在GitHub上存在且名称正确"
    Write-Host "- 确保您有仓库的访问权限"
}

Write-Host
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "操作完成" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Read-Host "按Enter退出"