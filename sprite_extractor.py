"""
雪碧图自动拆分工具 / Sprite Sheet Auto Splitter

自动检测纯白色背景雪碧图中的子图，拆分为单独的透明背景 PNG 文件。
"""

import os
import sys
import argparse
import glob
from pathlib import Path

import cv2
import numpy as np


def _build_mask(image: np.ndarray, bg_threshold: int = 240) -> np.ndarray:
    """生成前景遮罩，用于轮廓检测定位子图位置。

    Args:
        image: 输入图像 (BGR/BGRA)
        bg_threshold: 背景色阈值，RGB 三通道都高于此值视为白色背景

    Returns:
        二值遮罩 (0=背景, 255=前景)
    """
    if image.shape[2] == 4:
        # 有 alpha 通道时，用 alpha 判断
        alpha = image[:, :, 3]
        _, mask = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)
    else:
        # 检测白色背景：RGB 三通道都 >= bg_threshold 的像素视为背景
        bgr = image[:, :, :3]
        is_white = np.all(bgr >= bg_threshold, axis=2)
        mask = np.where(is_white, 0, 255).astype(np.uint8)

    # 形态学操作：闭运算填充前景内部小孔洞
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    # 开运算去除小噪点
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return mask


def detect_sprites(
    image: np.ndarray,
    min_area: int = 100,
    padding: int = 1,
    bg_threshold: int = 240,
) -> list[tuple[int, int, int, int]]:
    """自动检测雪碧图中的子图位置（轮廓检测模式）。

    Args:
        image: 输入图像 (BGRA/BGR)
        min_area: 最小轮廓面积，过滤噪点
        padding: 裁剪区域的边距填充（像素）
        bg_threshold: 背景色阈值

    Returns:
        裁剪区域列表 [(x, y, w, h), ...]
    """
    h_img, w_img = image.shape[:2]
    mask = _build_mask(image, bg_threshold=bg_threshold)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(w_img, x + w + padding)
        y2 = min(h_img, y + h + padding)
        regions.append((x1, y1, x2 - x1, y2 - y1))

    regions.sort(key=lambda r: (r[1] // 20, r[0]))
    return regions


def extract_sprites(
    input_path: str,
    output_dir: str,
    min_area: int = 100,
    padding: int = 1,
    tolerance: int = 30,
    bg_threshold: int = 240,
    name_prefix: str = "",
) -> int:
    """从雪碧图中拆分并保存子图。

    Args:
        input_path: 雪碧图文件路径
        output_dir: 输出目录
        min_area: 最小轮廓面积（像素²），过滤噪点
        padding: 裁剪边距填充（像素）
        tolerance: 白色容差
        bg_threshold: 背景色阈值，RGB 都高于此值视为白色背景
        name_prefix: 输出文件名前缀

    Returns:
        拆分出的子图数量
    """
    image = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"  [错误] 无法读取图像: {input_path}")
        return 0

    # 使用轮廓检测自动识别子图
    regions = detect_sprites(image, min_area=min_area, padding=padding, bg_threshold=bg_threshold)
    print(f"  检测到 {len(regions)} 个子图")

    if not regions:
        print(f"  [警告] 未检测到子图: {input_path}")
        return 0

    # 转换为 BGRA
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    os.makedirs(output_dir, exist_ok=True)
    stem = Path(input_path).stem
    prefix = name_prefix if name_prefix else stem

    white = np.array([255, 255, 255], dtype=np.float32)

    count = 0
    for i, (x, y, w, h) in enumerate(regions):
        crop = image[y:y + h, x:x + w].copy()

        # 移除白色背景
        bgr = crop[:, :, :3].astype(np.float32)
        dist = np.linalg.norm(bgr - white, axis=2)
        alpha = np.where(dist > tolerance, 255, 0).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
        crop[:, :, 3] = alpha

        filename = f"{prefix}_{i:04d}.png"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, crop)
        count += 1

    return count


def process_directory(
    input_dir: str,
    output_dir: str,
    min_area: int = 100,
    padding: int = 1,
    tolerance: int = 15,
    bg_threshold: int = 240,
) -> int:
    """批量处理 input 目录下的所有雪碧图。

    Args:
        input_dir: 输入目录
        output_dir: 输出根目录
        min_area: 最小轮廓面积
        padding: 裁剪边距
        tolerance: 背景色容差
        bg_threshold: 背景色阈值

    Returns:
        总拆分子图数量
    """
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp")
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(input_dir, ext)))
    files.sort()

    if not files:
        print(f"[提示] input 目录下未找到图片文件: {input_dir}")
        return 0

    total = 0
    for filepath in files:
        filename = os.path.basename(filepath)
        stem = Path(filepath).stem
        sub_output = os.path.join(output_dir, stem)
        print(f"处理: {filename}")
        count = extract_sprites(
            filepath, sub_output,
            min_area=min_area, padding=padding,
            tolerance=tolerance, bg_threshold=bg_threshold
        )
        print(f"  -> 拆分出 {count} 张子图，保存至 {sub_output}/")
        total += count

    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="雪碧图自动拆分工具 / Sprite Sheet Auto Splitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例 / Examples:
  python sprite_extractor.py                        # 使用默认 input/output 目录
  python sprite_extractor.py -i imgs -o results     # 指定输入输出目录
  python sprite_extractor.py --min-area 500         # 过滤面积小于 500px² 的噪点
  python sprite_extractor.py --padding 5            # 每个子图多保留 5px 边距
  python sprite_extractor.py --bg-threshold 250     # 更严格的白色背景检测
""",
    )
    parser.add_argument(
        "-i", "--input",
        default="input",
        help="输入目录路径（默认: input）",
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出目录路径（默认: output）",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=100,
        help="最小轮廓面积，过滤噪点（默认: 100 像素²）",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=1,
        help="裁剪边距填充（默认: 1 像素）",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=15,
        help="背景色容差，值越小边缘越精确（默认: 15）",
    )
    parser.add_argument(
        "--bg-threshold",
        type=int,
        default=240,
        help="白色背景阈值，RGB 三通道都高于此值视为背景（默认: 240）",
    )

    args = parser.parse_args()

    input_dir = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output)

    if not os.path.isdir(input_dir):
        print(f"[错误] 输入目录不存在: {input_dir}")
        sys.exit(1)

    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"背景阈值: {args.bg_threshold}")
    print("-" * 40)

    total = process_directory(
        input_dir, output_dir,
        min_area=args.min_area, padding=args.padding,
        tolerance=args.tolerance, bg_threshold=args.bg_threshold
    )
    print("-" * 40)
    print(f"完成！共拆分出 {total} 张子图。")


if __name__ == "__main__":
    main()
