# 视频复刻替换功能使用指南

本文档详细介绍视频复刻工具的替换功能，包括人物替换、背景替换和商品替换的配置和使用方法。

## 功能概述

视频复刻工具现在支持三种类型的替换功能：

- **人物替换**：替换视频中的人物，可选择性保留原有人物的姿势
- **背景替换**：替换视频的背景，同时保留前景主体
- **商品替换**：识别并替换视频中的商品对象

## 安装要求

确保已安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

替换功能需要额外的依赖库：

```bash
pip install opencv-python numpy pillow
```

## 配置方法

### 1. 通过配置文件配置

在工作流配置文件（如`configs/example_workflow.json`）中添加`replacement`部分：

```json
{
  "replacement": {
    "enabled": true,
    "person": {
      "enabled": true,
      "prompt": "描述目标人物的提示词",
      "reference_image": "人物参考图像路径",
      "preserve_pose": true,
      "confidence_threshold": 0.7
    },
    "background": {
      "enabled": true,
      "prompt": "描述目标背景的提示词",
      "reference_image": "背景参考图像路径",
      "preserve_foreground": true,
      "confidence_threshold": 0.6
    },
    "product": {
      "enabled": true,
      "prompt": "描述目标商品的提示词",
      "reference_image": "商品参考图像路径",
      "confidence_threshold": 0.7
    },
    "preserve_lighting": true
  }
}
```

### 2. 通过命令行参数配置

使用命令行参数可以覆盖配置文件中的设置：

```bash
python -m src.main --video_path input.mp4 \
    --enable_replacement \
    --person_replacement \
    --person_prompt "一个穿着红色衣服的年轻女性" \
    --preserve_pose \
    --background_replacement \
    --background_prompt "现代办公室环境" \
    --product_replacement \
    --product_prompt "智能手机" \
    --preserve_lighting
```

## 命令行参数说明

### 替换功能基础参数

- `--enable_replacement`：启用替换功能
- `--preserve_lighting`：保留原视频的光照效果

### 人物替换参数

- `--person_replacement`：启用人物替换
- `--person_prompt`：人物替换的文本描述
- `--person_image`：人物参考图像路径
- `--preserve_pose`：保留原有人物的姿势

### 背景替换参数

- `--background_replacement`：启用背景替换
- `--background_prompt`：背景替换的文本描述
- `--background_image`：背景参考图像路径
- `--preserve_foreground`：保留前景主体

### 商品替换参数

- `--product_replacement`：启用商品替换
- `--product_prompt`：商品替换的文本描述
- `--product_image`：商品参考图像路径

## 使用示例

### 1. 仅替换背景

```bash
python -m src.main --video_path input.mp4 \
    --background_replacement \
    --background_prompt "美丽的海滩日落" \
    --preserve_foreground \
    --output_name beach_video
```

### 2. 替换人物

```bash
python -m src.main --video_path input.mp4 \
    --person_replacement \
    --person_image reference_person.jpg \
    --preserve_pose \
    --preview_mode
```

### 3. 同时替换人物和背景

```bash
python -m src.main --video_path input.mp4 \
    --person_replacement \
    --person_prompt "穿着西装的商务人士" \
    --preserve_pose \
    --background_replacement \
    --background_image new_office.jpg \
    --preserve_lighting
```

### 4. 替换商品

```bash
python -m src.main --video_path product_video.mp4 \
    --product_replacement \
    --product_prompt "新款笔记本电脑" \
    --product_image new_laptop.jpg \
    --fps 30
```

## 注意事项

1. **图像质量**：使用高质量的参考图像可以获得更好的替换效果
2. **计算资源**：替换功能会增加计算负担，可能需要更长的处理时间
3. **预览模式**：在全量处理前，建议使用`--preview_mode`参数进行预览
4. **替换效果**：复杂场景可能需要调整`confidence_threshold`参数以获得最佳效果
5. **保留细节**：启用`preserve_pose`、`preserve_foreground`和`preserve_lighting`可以使替换结果更加自然

## 高级配置

### 置信度阈值调整

不同类型的替换可以调整不同的置信度阈值：

- **人物替换**：默认为0.7，提高可以减少误识别
- **背景替换**：默认为0.6，可以根据背景复杂度调整
- **商品替换**：默认为0.7，对于小型商品可以适当降低

### 性能优化

对于大型视频，可以调整以下参数提高性能：

1. **降低分辨率**：使用`--resolution`参数设置较低的分辨率
2. **减少帧率**：使用`--fps`参数降低输出帧率
3. **分批次处理**：将长视频分割成多个短片段分别处理

## 故障排除

### 替换效果不佳

- 检查参考图像是否清晰且与目标场景匹配
- 调整描述提示词，使其更加具体
- 尝试不同的置信度阈值

### 处理速度慢

- 启用`--preview_mode`进行快速预览
- 降低处理分辨率
- 关闭不必要的替换功能

### 识别不准确

- 确保视频画面清晰，光线充足
- 调整置信度阈值
- 提供更具体的描述提示词

## 最佳实践

1. **先小后大**：先用少量帧预览效果
2. **细节调整**：根据预览结果调整参数
3. **分步替换**：复杂场景可以分步进行不同类型的替换
4. **保留原始**：处理前备份原始视频
5. **组合使用**：结合不同的保留选项获得最佳效果

---

如有其他问题或需要进一步的帮助，请参考项目文档或联系技术支持。