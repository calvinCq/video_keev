# 视频复刻工具 (Video Keev)

基于云端ComfyUI服务的视频复刻工具，用于将普通视频转换为高质量的复刻版本。

## 功能特性

- 通过云端ComfyUI服务执行视频复刻处理
- 支持自定义工作流配置和处理参数
- 完整的视频处理流程：帧提取、预处理、云端处理、结果合成
- 命令行界面，易于集成和使用
- 支持多种处理质量级别和帧率设置

## 系统要求

- Python 3.8+
- 依赖包：requests, opencv-python, pyyaml, python-dotenv

## 安装步骤

1. 克隆项目代码

```bash
git clone [repository-url] cd video_keev
```

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 配置环境变量

复制`.env.example`文件为`.env`，并填写相应的配置信息：

```bash
cp .env.example .env
# 编辑.env文件，设置API密钥和端点
```

## 环境变量配置

在`.env`文件中配置以下环境变量：

- `COMFYUI_API_ENDPOINT`：ComfyUI服务端点URL
- `COMFYUI_API_KEY`：ComfyUI服务访问密钥
- `COMFYUI_TIMEOUT`：请求超时时间（秒）
- `COMFYUI_RETRY_COUNT`：请求失败重试次数
- `COMFYUI_RETRY_DELAY`：重试间隔（秒）

## 使用方法

### 1. 测试连接

在使用前，建议先测试与ComfyUI服务的连接：

```bash
python -m src.main test-connection
```

### 2. 列出可用工作流

查看系统中可用的工作流：

```bash
python -m src.main list-workflows
```

### 3. 执行视频复刻

基本用法：

```bash
python -m src.main replicate --input input_video.mp4
```

指定输出路径：

```bash
python -m src.main replicate --input input_video.mp4 --output output_video.mp4
```

使用特定工作流：

```bash
python -m src.main replicate --input input_video.mp4 --workflow realistic_video_replication
```

使用配置文件：

```bash
python -m src.main replicate --input input_video.mp4 --workflow configs/example_workflow.json
```

自定义参数：

```bash
python -m src.main replicate --input input_video.mp4 --frame-rate 15 --quality-level high --max-frames 100
```

## 工作流配置

工作流配置文件使用JSON格式，示例配置（`configs/example_workflow.json`）：

```json
{
  "workflow_id": "realistic_video_replication",
  "frame_rate": 15,
  "max_frames": 100,
  "quality_level": "high",
  "preprocess": {
    "resize": {
      "width": 720,
      "height": 480,
      "preserve_aspect_ratio": true
    },
    "normalize": true,
    "denoise": false,
    "enhance_contrast": true
  },
  "custom_params": {
    "model_id": "realistic_video_v1",
    "style": "natural",
    "motion_blur": 0.2,
    "color_correction": true,
    "sharpness": 1.2,
    "detail_preservation": "high"
  },
  "poll_interval": 5
}
```

## 目录结构

```
video_keev/
├── src/                      # 源代码目录
│   ├── __init__.py          # 包初始化
│   ├── main.py              # 主程序入口
│   ├── config/              # 配置管理
│   ├── workflow/            # 工作流管理
│   ├── api/                 # API客户端
│   ├── video/               # 视频处理
│   └── utils/               # 工具函数
├── configs/                  # 配置文件目录
├── outputs/                  # 输出目录（自动创建）
├── requirements.txt         # 依赖列表
├── .env.example             # 环境变量示例
└── README.md                # 项目文档
```

## 注意事项

1. 确保已正确配置ComfyUI服务的API密钥和端点
2. 处理大视频文件可能需要较长时间，请耐心等待
3. 处理过程会产生临时文件，存储在临时目录中
4. 建议先使用较短的视频片段进行测试

## 常见问题

### 连接失败
- 检查网络连接
- 验证API端点URL是否正确
- 确认API密钥有效

### 处理超时
- 对于长视频，考虑增加`COMFYUI_TIMEOUT`设置
- 可以降低帧率或减少最大处理帧数

### 输出质量不佳
- 尝试使用高质量级别
- 调整工作流配置中的自定义参数
- 确保输入视频质量足够好

## 许可证

[MIT License](LICENSE)