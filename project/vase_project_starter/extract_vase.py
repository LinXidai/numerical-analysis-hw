"""
OpenCV 半自动提取花瓶右半边轮廓
使用方法：
1. python extract_vase.py
2. 在原图上框选包含坐标网格的绘图区，按 Enter/空格确认
3. 依次点击：原点 O、x=5 刻度点、y=5 刻度点
4. 从花瓶轮廓顶部开始，沿右半边轮廓顺时针/自上而下依次点击
5. 左键添加点；右键撤销最近一点；按 Enter 保存；Esc 退出
输出 vase_points.csv，单位为图中坐标单位。
依赖：pip install opencv-python numpy
"""
import cv2
import csv
import numpy as np
from pathlib import Path

IMAGE_PATH = ""  # 留空则弹出文件选择框；也可填写图片路径
OUTPUT_CSV = "vase_points.csv"
PREVIEW_IMAGE = "contour_review.png"


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
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")]
        )
        root.destroy()
        return path
    except Exception:
        return input("请输入图片路径：").strip().strip('"')


def main():
    path = choose_image()
    if not path:
        print("未选择图片，程序退出。")
        return
    # OpenCV 的 imread 在 Windows 下读取中文路径时可能失败，先按原始字节读入再解码。
    img_array = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        print("图片读取失败，请检查路径：", path)
        return

    print("请框选坐标网格和花瓶轮廓所在区域，按 Enter/空格确认。")
    roi = cv2.selectROI("Select graph ROI", img, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Select graph ROI")
    x0, y0, w, h = map(int, roi)
    if w == 0 or h == 0:
        print("没有选择有效区域。")
        return
    crop = img[y0:y0+h, x0:x0+w].copy()

    # 生成候选暗像素图，只用于人工检查，不直接把所有暗像素当成轮廓
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    cv2.imwrite("threshold_preview.png", binary)
    print("已保存 threshold_preview.png（候选暗像素预览，网格线也会出现）。")

    points = []
    mode = "calibration"
    calib = []
    display = crop.copy()
    title = "Click calibration: O, x=5, y=5; then contour points top-to-bottom"

    def redraw():
        nonlocal display
        display = crop.copy()
        # 标出校准点
        labels = ["O", "x=5", "y=5"]
        for i, p in enumerate(calib):
            cv2.circle(display, p, 6, (0, 0, 255), -1)
            cv2.putText(display, labels[i], (p[0]+8, p[1]-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        for i, p in enumerate(points):
            cv2.circle(display, p, 3, (0, 180, 0), -1)
            if i > 0:
                cv2.line(display, points[i-1], p, (0, 180, 0), 1)
        cv2.putText(display, f"Calibration {len(calib)}/3 | contour points {len(points)}",
                    (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)
        cv2.imshow(title, display)

    def mouse(event, x, y, flags, param):
        nonlocal mode
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(calib) < 3:
                calib.append((x, y))
                if len(calib) == 3:
                    mode = "contour"
                    print("校准完成。现在沿花瓶右半边轮廓从顶部到下方依次点击。")
            else:
                points.append((x, y))
            redraw()
        elif event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()
            redraw()

    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, min(crop.shape[1], 1100), min(crop.shape[0], 850))
    cv2.setMouseCallback(title, mouse)
    redraw()
    print("左键：依次点击 O、x=5、y=5，再点击轮廓；右键：撤销轮廓点；Enter：保存；Esc：退出。")
    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (13, 10):  # Enter
            break
        if key == 27:
            cv2.destroyAllWindows()
            print("用户取消。")
            return
        if key in (8, 127) and points:
            points.pop()
            redraw()

    cv2.destroyAllWindows()
    if len(calib) != 3 or len(points) < 8:
        print("点数不足：至少需要 8 个轮廓点和 3 个校准点。")
        return

    origin, x5, y5 = [np.array(p, dtype=float) for p in calib]
    # x5 用于校准横向像素/单位；y5 用于校准纵向像素/单位
    sx = (x5[0] - origin[0]) / 5.0
    sy = (origin[1] - y5[1]) / 5.0  # 图像 y 向下，数学 y 向上
    if sx <= 0 or sy <= 0:
        print("校准点顺序或位置错误：请按 O、x=5、y=5 的顺序重新运行。")
        return

    rows = []
    for px, py in points:
        x = (px - origin[0]) / sx
        y = (origin[1] - py) / sy
        rows.append((x, y, px + x0, py + y0))

    # 保留点击顺序；参数曲线插值需要按轮廓顺序，而不是简单按 x 排序
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "pixel_x", "pixel_y"])
        writer.writerows(rows)

    # 保存带点击点的检查图
    review = crop.copy()
    for i, p in enumerate(points):
        cv2.circle(review, p, 3, (0, 0, 255), -1)
        if i:
            cv2.line(review, points[i-1], p, (0, 180, 0), 1)
    cv2.imwrite(PREVIEW_IMAGE, review)
    print(f"已保存 {OUTPUT_CSV}，共 {len(rows)} 个点。")
    print(f"已保存 {PREVIEW_IMAGE}，请检查点是否落在真实轮廓上。")
    print(f"横向比例 sx={sx:.3f} px/unit，纵向比例 sy={sy:.3f} px/unit")
    print("如果坐标轴不是等比例显示，分别用 sx、sy 校准是允许的；但应确认刻度标定准确。")


if __name__ == "__main__":
    main()
