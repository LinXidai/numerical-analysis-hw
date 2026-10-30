"""
OpenCV 半自动/人工协同提取花瓶右半轮廓。

流程：
1. 选择图像和 ROI，依次点击 O、x=5、y=5；
2. 轮廓阶段点击少量锚点，程序将锚点吸附到附近的强边缘；
3. 按 Enter 后，程序在锚点之间加密，并对加密点进行局部边缘吸附；
4. 检查 contour_review.png，确认无误后使用 vase_points.csv。

按键：
* 左键：添加轮廓锚点；
* 右键或 Backspace：撤销最后一个锚点；
* A：在“显示自动加密候选”与“仅显示锚点”之间切换；
* Enter：生成并保存加密轮廓；
* Esc：退出。

该程序不会把所有暗像素直接当成轮廓：网格线和坐标轴会造成大量伪边缘，
因此仍保留人工锚点和最终检查。
"""
import csv
from pathlib import Path

import cv2
import numpy as np


IMAGE_PATH = ""
OUTPUT_CSV = "vase_points.csv"
PREVIEW_IMAGE = "contour_review.png"
THRESHOLD_PREVIEW = "threshold_preview.png"
ANCHOR_SPACING = 5.0
SNAP_RADIUS = 12


def choose_image():
    if IMAGE_PATH.strip():
        return IMAGE_PATH.strip()
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="选择题目截图",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return path
    except Exception:
        return input("请输入图片路径：").strip().strip('"')


def edge_map(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    gradient = cv2.Laplacian(gray, cv2.CV_32F)
    strength = cv2.normalize(np.abs(gradient), None, 0, 255, cv2.NORM_MINMAX)
    edges = cv2.Canny(gray, 35, 120)
    return gray, strength, edges


def snap_to_edge(point, strength, edges, radius=SNAP_RADIUS):
    """在点击点附近选择强边缘，距离项防止吸附到较远网格线。"""
    x, y = point
    height, width = edges.shape
    x1, x2 = max(0, x - radius), min(width, x + radius + 1)
    y1, y2 = max(0, y - radius), min(height, y + radius + 1)
    local_edges = edges[y1:y2, x1:x2] > 0
    candidates = np.argwhere(local_edges)
    if len(candidates) == 0:
        return (int(x), int(y))

    best = None
    best_score = -np.inf
    for cy, cx in candidates:
        px, py = x1 + int(cx), y1 + int(cy)
        distance = np.hypot(px - x, py - y)
        score = float(strength[py, px]) - 2.0 * distance
        if score > best_score:
            best_score = score
            best = (px, py)
    return best if best is not None else (int(x), int(y))


def densify_and_snap(anchors, strength, edges):
    if len(anchors) < 2:
        return anchors[:]
    output = [anchors[0]]
    for first, second in zip(anchors[:-1], anchors[1:]):
        distance = np.hypot(second[0] - first[0], second[1] - first[1])
        count = max(1, int(np.ceil(distance / ANCHOR_SPACING)))
        for i in range(1, count + 1):
            alpha = i / count
            predicted = (
                int(round(first[0] * (1 - alpha) + second[0] * alpha)),
                int(round(first[1] * (1 - alpha) + second[1] * alpha)),
            )
            snapped = snap_to_edge(predicted, strength, edges)
            if np.hypot(snapped[0] - output[-1][0], snapped[1] - output[-1][1]) > 1:
                output.append(snapped)
    return output


def main():
    path = choose_image()
    if not path:
        print("未选择图片，程序退出。")
        return
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        print("图片读取失败：", path)
        return

    print("请框选坐标绘图区，按 Enter/空格确认。")
    roi = cv2.selectROI("Select graph ROI", image, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Select graph ROI")
    x0, y0, width, height = map(int, roi)
    if width == 0 or height == 0:
        print("没有选择有效区域。")
        return
    crop = image[y0 : y0 + height, x0 : x0 + width].copy()
    gray, strength, edges = edge_map(crop)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    cv2.imwrite(THRESHOLD_PREVIEW, binary)

    calibration = []
    anchors = []
    mode = "calibration"
    show_assisted = True
    title = "Hybrid contour extraction"

    def redraw():
        display = crop.copy()
        labels = ["O", "x=5", "y=5"]
        for i, point in enumerate(calibration):
            cv2.circle(display, point, 6, (0, 0, 255), -1)
            cv2.putText(
                display, labels[i], (point[0] + 8, point[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2,
            )
        for index, point in enumerate(anchors):
            cv2.circle(display, point, 4, (0, 180, 0), -1)
            if index:
                cv2.line(display, anchors[index - 1], point, (0, 180, 0), 1)
        if mode == "contour" and show_assisted and len(anchors) >= 2:
            assisted = densify_and_snap(anchors, strength, edges)
            for first, second in zip(assisted[:-1], assisted[1:]):
                cv2.line(display, first, second, (255, 160, 0), 1)
        text = (
            f"Calibration {len(calibration)}/3 | anchors {len(anchors)} | "
            f"A assisted {'on' if show_assisted else 'off'}"
        )
        cv2.putText(display, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)
        cv2.imshow(title, display)

    def mouse(event, x, y, flags, param):
        nonlocal mode
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(calibration) < 3:
                calibration.append((x, y))
                if len(calibration) == 3:
                    mode = "contour"
                    print("校准完成。请沿轮廓顺序点击锚点，建议每隔 10--30 像素点击一次。")
            else:
                snapped = snap_to_edge((x, y), strength, edges)
                anchors.append(snapped)
            redraw()
        elif event == cv2.EVENT_RBUTTONDOWN and anchors:
            anchors.pop()
            redraw()

    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, min(width, 1100), min(height, 850))
    cv2.setMouseCallback(title, mouse)
    redraw()
    print("左键：校准或添加锚点；右键/Backspace：撤销；A：切换辅助预览；Enter：保存。")
    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (13, 10):
            break
        if key == 27:
            cv2.destroyAllWindows()
            print("用户取消。")
            return
        if key in (8, 127) and anchors:
            anchors.pop()
            redraw()
        if key in (ord("a"), ord("A")) and mode == "contour":
            show_assisted = not show_assisted
            redraw()
    cv2.destroyAllWindows()

    if len(calibration) != 3 or len(anchors) < 4:
        print("点数不足：需要 3 个校准点和至少 4 个轮廓锚点。")
        return

    points = densify_and_snap(anchors, strength, edges)
    origin, x5, y5 = [np.array(point, dtype=float) for point in calibration]
    sx = (x5[0] - origin[0]) / 5.0
    sy = (origin[1] - y5[1]) / 5.0
    if sx <= 0 or sy <= 0:
        print("校准点顺序或位置错误。")
        return

    rows = []
    for px, py in points:
        x = (px - origin[0]) / sx
        y = (origin[1] - py) / sy
        rows.append((x, y, px + x0, py + y0))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["x", "y", "pixel_x", "pixel_y"])
        writer.writerows(rows)

    review = crop.copy()
    for first, second in zip(points[:-1], points[1:]):
        cv2.line(review, first, second, (0, 180, 0), 1)
    for point in anchors:
        cv2.circle(review, point, 4, (0, 0, 255), -1)
    cv2.imwrite(PREVIEW_IMAGE, review)
    print(f"已保存 {OUTPUT_CSV}，锚点 {len(anchors)} 个，加密点 {len(rows)} 个。")
    print(f"已保存 {PREVIEW_IMAGE}，红点为人工锚点，绿线为自动加密结果。")
    print(f"sx={sx:.3f} px/unit，sy={sy:.3f} px/unit")


if __name__ == "__main__":
    main()
