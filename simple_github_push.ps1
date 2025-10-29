Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "GitHub Push Script (Simple Version)" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTE: GitHub requires Personal Access Token (PAT) for authentication." -ForegroundColor Yellow
Write-Host "1. Make sure you have created an 'video_keev' repository on GitHub" -ForegroundColor Yellow
Write-Host "2. Ensure you have a PAT with 'repo' permission" -ForegroundColor Yellow
Write-Host ""

# Prompt for GitHub username
$githubUsername = Read-Host -Prompt "Enter your GitHub username"
$githubRepo = "https://github.com/$githubUsername/video_keev.git"

Write-Host ""
Write-Host "Setting up remote repository: $githubRepo" -ForegroundColor Green

# Remove old remote if exists
try {
    git remote remove origin
} catch {
    # Ignore if origin doesn't exist
}

# Add new remote
git remote add origin $githubRepo

# Rename branch to main
git branch -M main

Write-Host ""
Write-Host "Preparing to push code..." -ForegroundColor Green
Write-Host "When prompted, use your PAT as password!" -ForegroundColor Yellow

# Execute push
$result = git push -u origin main 2>&1

# Check result
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "Success! Code pushed to GitHub." -ForegroundColor Green
    Write-Host "Access at: https://github.com/$githubUsername/video_keev" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Red
    Write-Host "Push failed. Error: $result" -ForegroundColor Red
    Write-Host "Check repository exists and PAT is correct." -ForegroundColor Red
    Write-Host "===========================================" -ForegroundColor Red
}

Read-Host -Prompt "Press Enter to exit"