# GitHub Upload Instructions Script
# This script guides you through uploading your project to GitHub

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "GITHUB UPLOAD INSTRUCTIONS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host

# Step 1: Check Git installation
Write-Host "[STEP 1: CHECKING GIT INSTALLATION]" -ForegroundColor Yellow
$gitPath = $null
$commonGitPaths = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Git\bin\git.exe"
)

foreach ($path in $commonGitPaths) {
    if (Test-Path $path) {
        $gitPath = $path
        Write-Host "✓ Git found at: $gitPath" -ForegroundColor Green
        break
    }
}

if (-not $gitPath) {
    Write-Host "✗ Git not found! Please install Git first." -ForegroundColor Red
    Write-Host "Git download URL: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "Press Enter after installation, or Ctrl+C to exit"
    
    # Recheck Git
    foreach ($path in $commonGitPaths) {
        if (Test-Path $path) {
            $gitPath = $path
            Write-Host "✓ Git found at: $gitPath" -ForegroundColor Green
            break
        }
    }
    
    if (-not $gitPath) {
        Write-Host "✗ Still cannot find Git, cannot continue." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Show Git version
Write-Host "Git version:"
& $gitPath --version
Write-Host

# Step 2: Set GitHub information
Write-Host "[STEP 2: SETTING GITHUB INFORMATION]" -ForegroundColor Yellow
Write-Host "Enter your GitHub username (not email):"
$username = Read-Host

if (-not $username) {
    Write-Host "✗ GitHub username cannot be empty!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Enter repository name (default: video_keev):"
$repoName = Read-Host
if (-not $repoName) {
    $repoName = "video_keev"
}

# Step 3: Initialize Git repository if needed
Write-Host "[STEP 3: GIT REPOSITORY INITIALIZATION]" -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "Initializing new Git repository..."
    & $gitPath init
    
    # Create .gitignore file
    if (-not (Test-Path ".gitignore")) {
        Write-Host "Creating .gitignore file..."
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
        Write-Host "✓ .gitignore file created" -ForegroundColor Green
    }
    
    # Add all files
    Write-Host "Adding all files to Git..."
    & $gitPath add .
    
    # Commit files
    Write-Host "Creating initial commit..."
    & $gitPath commit -m "Initial commit"
} else {
    Write-Host "✓ Git repository already exists" -ForegroundColor Green
    Write-Host "Repository status:"
    & $gitPath status --short
    
    # Check for uncommitted changes
    $statusOutput = & $gitPath status --porcelain
    if ($statusOutput) {
        Write-Host "Uncommitted changes detected. Commit now? (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        if ($response -eq "Y" -or $response -eq "y") {
            & $gitPath add .
            Write-Host "Enter commit message:"
            $commitMsg = Read-Host
            if (-not $commitMsg) {
                $commitMsg = "Update files"
            }
            & $gitPath commit -m $commitMsg
        }
    }
}
Write-Host

# Step 4: Create GitHub repository (manual instructions)
Write-Host "[STEP 4: CREATE GITHUB REPOSITORY]" -ForegroundColor Yellow
Write-Host "Please create repository manually on GitHub:"
Write-Host "1. Go to https://github.com/new" -ForegroundColor Cyan
Write-Host "2. Repository name: $repoName" -ForegroundColor Cyan
Write-Host "3. Keep it empty (do not add README, .gitignore, or license)" -ForegroundColor Cyan
Write-Host "4. Click 'Create repository' button" -ForegroundColor Cyan
Write-Host
Write-Host "Press Enter after creating repository..."
Read-Host

# Step 5: Set up remote repository
Write-Host "[STEP 5: SET UP REMOTE REPOSITORY]" -ForegroundColor Yellow
$remoteUrl = "https://github.com/$username/$repoName.git"
Write-Host "Setting remote URL: $remoteUrl"

# Remove existing origin if any
& $gitPath remote remove origin 2>$null

# Add new origin
& $gitPath remote add origin $remoteUrl

# Set main branch
& $gitPath branch -M main

# Show remote config
Write-Host "Remote configuration:"
& $gitPath remote -v
Write-Host

# Step 6: Create Personal Access Token (manual instructions)
Write-Host "[STEP 6: CREATE PERSONAL ACCESS TOKEN (PAT)]" -ForegroundColor Yellow
Write-Host "IMPORTANT: Create GitHub Personal Access Token for authentication:"
Write-Host "1. Go to https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "2. Set token name (e.g., 'local-dev-token')" -ForegroundColor Cyan
Write-Host "3. Set expiration date" -ForegroundColor Cyan
Write-Host "4. Check 'repo' permission for full repository access" -ForegroundColor Cyan
Write-Host "5. Scroll down and click 'Generate token'" -ForegroundColor Cyan
Write-Host "6. Copy and save the token - you can't see it again!" -ForegroundColor Cyan
Write-Host
Write-Host "Press Enter after creating and copying the token..."
Read-Host

# Step 7: Push code
Write-Host "[STEP 7: PUSH CODE TO GITHUB]" -ForegroundColor Yellow
Write-Host "When prompted for credentials:"
Write-Host "- Username: $username" -ForegroundColor Cyan
Write-Host "- Password: Use your Personal Access Token, NOT GitHub password" -ForegroundColor Cyan
Write-Host
Write-Host "Press Enter to start pushing..."
Read-Host

# Execute push
Write-Host "Pushing code to GitHub..."
& $gitPath push -u origin main

# Check result
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 SUCCESS! Code pushed to GitHub!" -ForegroundColor Green
    Write-Host "Repository URL: $remoteUrl" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Visit the repository URL to view your code"
    Write-Host "2. Use 'git push' to push future changes"
    Write-Host "3. Securely store your Personal Access Token"
} else {
    Write-Host ""
    Write-Host "❌ FAILED to push! Check these:" -ForegroundColor Red
    Write-Host "1. GitHub username: $username"
    Write-Host "2. Repository name: $repoName"
    Write-Host "3. Repository exists on GitHub"
    Write-Host "4. Personal Access Token has 'repo' permission"
    Write-Host "5. Network connection"
}

Write-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PROCESS COMPLETED" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"