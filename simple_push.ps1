<#
.SYNOPSIS
    简化的GitHub仓库上传脚本
.DESCRIPTION
    帮助用户将当前文件夹上传到GitHub，自动检测环境并提供详细指导
#>

# 清除屏幕并显示标题
Clear-Host
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "             SIMPLE GITHUB PUSH" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host

# 设置GitHub信息
$GitHubUsername = "calvinCq"
$RepoName = "video_keev"
$RemoteUrl = "https://github.com/$GitHubUsername/$RepoName.git"

# 显示配置信息
Write-Host "使用配置:" -ForegroundColor Green
Write-Host "- GitHub用户名: $GitHubUsername" -ForegroundColor Green
Write-Host "- 仓库名称: $RepoName" -ForegroundColor Green
Write-Host "- 仓库URL: $RemoteUrl" -ForegroundColor Green
Write-Host

# 检查Git是否可用
try {
    $GitPath = Get-Command git -ErrorAction Stop | Select-Object -ExpandProperty Source
    Write-Host "Git已找到: $GitPath" -ForegroundColor Green
    
    # 检查Git版本
    $GitVersion = git --version
    Write-Host "Git版本: $GitVersion" -ForegroundColor Green
    Write-Host
} catch {
    Write-Host "错误: 未找到Git!" -ForegroundColor Red
    Write-Host "请先安装Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host -NoNewline "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# 检查是否有.git目录
if (-not (Test-Path ".git")) {
    Write-Host "初始化Git仓库..." -ForegroundColor Yellow
    git init
    
    # 创建.gitignore文件（如果不存在）
    if (-not (Test-Path ".gitignore")) {
        Write-Host "创建.gitignore文件..." -ForegroundColor Yellow
        $gitignoreContent = @'
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

# Test reports
test_report.txt
test_run.log
'@
        $gitignoreContent | Out-File -FilePath ".gitignore" -Encoding utf8
        Write-Host ".gitignore文件已创建" -ForegroundColor Green
    }
    
    Write-Host "添加文件到Git..." -ForegroundColor Yellow
    git add .
    
    Write-Host "提交文件..." -ForegroundColor Yellow
    git commit -m "Initial commit"
    Write-Host
}

# 设置远程仓库
Write-Host "设置远程仓库..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin $RemoteUrl
git branch -M main

# 显示远程仓库配置
Write-Host "远程仓库配置:" -ForegroundColor Green
git remote -v
Write-Host

# 重要提示
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host "              重要提示:"
Write-Host "当Git提示输入凭据时:" -ForegroundColor Magenta
Write-Host "- 用户名: $GitHubUsername" -ForegroundColor Magenta
Write-Host "- 密码: 请输入您的Personal Access Token (不是GitHub密码)" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host
Write-Host "如何创建Personal Access Token:" -ForegroundColor Yellow
Write-Host "1. 访问 https://github.com/settings/tokens/new" -ForegroundColor Yellow
Write-Host "2. 设置一个名称（例如：'video_keev_upload'）" -ForegroundColor Yellow
Write-Host "3. 勾选'repo'权限" -ForegroundColor Yellow
Write-Host "4. 滚动到底部并点击'Generate token'" -ForegroundColor Yellow
Write-Host "5. 复制生成的token并安全保存（只会显示一次）" -ForegroundColor Yellow
Write-Host

# 等待用户确认
Write-Host "准备推送代码到GitHub..." -ForegroundColor Cyan
Write-Host -NoNewline "按任意键继续，或按Ctrl+C取消..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
Write-Host "`n"

# 执行推送
Write-Host "正在推送代码..." -ForegroundColor Yellow
try {
    $pushResult = git push -u origin main 2>&1
    $success = $LASTEXITCODE -eq 0
    
    if ($success) {
        Write-Host "`n===============================================" -ForegroundColor Green
        Write-Host "             成功! 代码已推送到GitHub。" -ForegroundColor Green
        Write-Host "         仓库地址: $RemoteUrl" -ForegroundColor Green
        Write-Host "===============================================" -ForegroundColor Green
    } else {
        Write-Host "`n===============================================" -ForegroundColor Red
        Write-Host "              推送失败!" -ForegroundColor Red
        Write-Host "错误信息: $pushResult" -ForegroundColor Red
        Write-Host "请检查以下几点:" -ForegroundColor Yellow
        Write-Host "1. 确保仓库 '$RepoName' 已在GitHub上创建" -ForegroundColor Yellow
        Write-Host "2. 确保Personal Access Token正确且有'repo'权限" -ForegroundColor Yellow
        Write-Host "3. 检查网络连接" -ForegroundColor Yellow
        Write-Host "4. 确保GitHub用户名 '$GitHubUsername' 正确" -ForegroundColor Yellow
        Write-Host "===============================================" -ForegroundColor Red
    }
} catch {
    Write-Host "`n===============================================" -ForegroundColor Red
    Write-Host "             推送过程中发生错误:" -ForegroundColor Red
    Write-Host "$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "===============================================" -ForegroundColor Red
}

Write-Host "`n按任意键退出..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')