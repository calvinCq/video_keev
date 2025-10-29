# GitHub上传指南

## 准备工作

1. 确保您已安装Git: [下载Git](https://git-scm.com/download/win)
2. 确保您有GitHub账号
3. 在GitHub上创建名为 `video_keev` 的仓库
4. 生成Personal Access Token (PAT):
   - 访问 https://github.com/settings/tokens/new
   - 设置名称（例如：`video_keev_upload`）
   - 勾选 `repo` 权限
   - 点击 "Generate token"
   - 复制生成的token并保存（只会显示一次）

## 一键上传方法

我已经为您准备了两个简化的上传脚本：

### 方法1：使用批处理脚本

1. 双击运行 `simple_push.bat`
2. 按照提示操作
3. 当提示输入凭据时：
   - 用户名：`calvinCq`
   - 密码：输入您的Personal Access Token（不是GitHub密码）

### 方法2：使用PowerShell脚本

1. 右键点击 `simple_push.ps1` 并选择 "使用PowerShell运行"
2. 按照提示操作
3. 当提示输入凭据时：
   - 用户名：`calvinCq`
   - 密码：输入您的Personal Access Token（不是GitHub密码）

## 手动执行步骤（如果脚本失败）

打开命令提示符或PowerShell，依次执行以下命令：

```bash
# 1. 初始化Git仓库
git init

# 2. 创建.gitignore文件（可选）
echo "# OS files\n.DS_Store\nehthumbs.db\nThumbs.db\n\n# Python\n__pycache__/\n*.py[cod]\n\n# Virtual Environment\nvenv/\nenv/\n\n# IDE\n.vscode/\n.idea/\n\n# Environment variables\n.env" > .gitignore

# 3. 添加所有文件
git add .

# 4. 提交文件
git commit -m "Initial commit"

# 5. 重命名主分支为main
git branch -M main

# 6. 添加远程仓库
git remote add origin https://github.com/calvinCq/video_keev.git

# 7. 推送代码
git push -u origin main
```

## 常见问题排查

- **推送失败，显示权限被拒绝**：请检查您的Personal Access Token是否正确且包含`repo`权限
- **仓库不存在错误**：请确保您已在GitHub上创建了名为`video_keev`的仓库
- **Git未找到错误**：请安装Git并确保它已添加到系统路径中
- **凭据缓存问题**：可以尝试以下命令清除Git凭据缓存：
  ```bash
  git credential reject
  protocol=https
  host=github.com
  <按Enter键>
  ```

## 联系方式

如有任何问题，请参考GitHub官方文档或联系技术支持。