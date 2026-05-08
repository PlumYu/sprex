# Sprite Extractor / 雪碧图拆分工具

Demo
<img width="1662" height="946" alt="gptgen1" src="https://github.com/user-attachments/assets/1c09d900-4aa7-4f92-96ab-3ac715cede4a" />
<img width="2088" height="1049" alt="image" src="https://github.com/user-attachments/assets/fb0f3600-5042-4184-9c1d-d15c5b72211d" />


> 基于 OpenCV 的雪碧图（Sprite Sheet）自动拆分命令行工具，无需数据文件，自动检测并提取子图。

> A CLI-based sprite sheet auto-splitter powered by OpenCV. No data files needed — detects and extracts individual sprites automatically.

---

## Features / 功能特性

- **自动检测** — 使用 OpenCV 轮廓检测自动识别雪碧图中的子图，无需 plist/xml/json 数据文件
- **智能白色背景识别** — 通过 RGB 三通道阈值判断，精确分离白色背景与前景内容
- **命令行操作** — 纯 CLI 交互，支持批量处理，适合脚本化工作流
- **透明通道支持** — 优先使用 Alpha 通道检测，兼容无透明通道的雪碧图
- **噪点过滤** — 可配置最小面积阈值，过滤碎片噪点
- **边界填充** — 可选的裁剪边距，保留子图边缘信息
- **批量处理** — 自动处理输入目录下的所有图片，按文件名分目录输出

---

## Installation / 安装

### 使用 Conda（推荐）

```bash
conda env create -f environment.yml
conda activate sprite-extractor
```

### 使用 pip

```bash
pip install opencv-python numpy
```

---

## Usage / 使用方法

### Quick Start / 快速开始

1. 将需要拆分的雪碧图放入 `input/` 文件夹
2. 运行命令：
   ```bash
   python sprite_extractor.py
   ```
3. 在 `output/` 文件夹中查看结果

### Directory Structure / 目录结构

```
sprite-extractor/
├── input/                  # 放入雪碧图
│   ├── characters.png
│   ├── items.png
│   └── ...
├── output/                 # 拆分结果（按雪碧图名称自动分目录）
│   ├── characters/
│   │   ├── characters_0000.png
│   │   ├── characters_0001.png
│   │   └── ...
│   └── items/
│       ├── items_0000.png
│       └── ...
├── sprite_extractor.py     # 主程序
├── environment.yml         # Conda 环境配置
└── README.md
```

### Command Line Options / 命令行参数

```
python sprite_extractor.py [OPTIONS]

Options:
  -i, --input DIR      输入目录路径（默认: input）
  -o, --output DIR     输出目录路径（默认: output）
  --min-area INT       最小轮廓面积，过滤噪点（默认: 100 像素²）
  --padding INT        裁剪边距填充像素（默认: 1）
  --tolerance INT      背景色容差，值越小边缘越精确（默认: 15）
  --bg-threshold INT   白色背景阈值，RGB 三通道都高于此值视为背景（默认: 240）
  -h, --help           显示帮助信息
```

### Examples / 示例

```bash
# 使用默认 input/output 目录
python sprite_extractor.py

# 自定义输入输出目录
python sprite_extractor.py -i my_sprites -o my_output

# 过滤面积小于 500px² 的噪点
python sprite_extractor.py --min-area 500

# 每个子图多保留 5px 边距
python sprite_extractor.py --padding 5

# 更严格的白色背景检测（适用于接近白色但不是纯白的背景）
python sprite_extractor.py --bg-threshold 250

# 更宽松的白色背景检测（适用于灰白色背景）
python sprite_extractor.py --bg-threshold 220

# 组合使用
python sprite_extractor.py -i sprites -o results --min-area 200 --padding 3
```

---

## How It Works / 工作原理

1. **读取图像** — 使用 OpenCV 读取雪碧图（支持 PNG/JPG/BMP/WebP）
2. **生成遮罩** — 优先使用 Alpha 通道；无透明通道时通过 RGB 三通道阈值判断白色背景
3. **形态学处理** — 闭运算填充前景内部孔洞，开运算去除小噪点
4. **轮廓检测** — 查找外部轮廓，过滤小于阈值的噪点
5. **背景透明化** — 将白色背景像素转换为透明通道
6. **裁剪保存** — 按从上到下、从左到右的顺序裁剪并保存为 PNG 文件

### 参数调优建议

| 场景 | 建议调整 |
|------|----------|
| 子图之间有间隙但检测不到 | 降低 `--bg-threshold`（如 220） |
| 背景不是纯白而是灰白 | 降低 `--bg-threshold`（如 200） |
| 检测到太多噪点碎片 | 增大 `--min-area`（如 500） |
| 子图边缘被裁切 | 增大 `--padding`（如 3-5） |
| 子图内部有白色区域被误判为背景 | 提高 `--bg-threshold`（如 250） |

---

## Supported Formats / 支持格式

**输入格式：** PNG, JPG/JPEG, BMP, WebP

**输出格式：** PNG（带 Alpha 透明通道）

---

## Requirements / 依赖

- Python >= 3.10
- OpenCV >= 4.8.0
- NumPy >= 1.24.0

---

## Project Origin / 项目来源

本项目基于 [Akascape/Sprite-Extractor-On-The-Go](https://github.com/Akascape/Sprite-Extractor-On-The-Go) 重构，原项目为 tkinter GUI 程序，需要数据文件（plist/xml/json）配合使用。本版本将其改造为 OpenCV 自动检测的命令行工具，无需数据文件即可自动识别子图。

---

## License / 许可证

[MIT License](LICENSE)
