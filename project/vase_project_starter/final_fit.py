"""
分段花瓶轮廓拟合。

输入 vase_points.csv 中的右半轮廓，输出到 fit_output/final_*：
* final_fit_right_curve.csv：最终右半轮廓
* final_fit_full_vase.csv：关于 y 轴镜像后的完整轮廓
* final_fit_summary.csv：分段方法和输入点误差诊断
* final_fit_comparison.png：输入点、分段结果和镜像结果

点必须按轮廓顺序排列。当前数据的顺序是：顶部中心 -> 瓶底 -> 顶部外缘
-> 顶部中心。分段边界由最低点、最宽点和 y 阈值自动确定，适用于本项目
的同类 vase_points.csv。
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import (
    Akima1DInterpolator,
    CubicSpline,
    PchipInterpolator,
)


INPUT = "vase_points.csv"
OUTDIR = "fit_output"
N_EVAL = 1200


def remove_consecutive_duplicates(x, y):
    keep = np.ones(len(x), dtype=bool)
    keep[1:] = np.hypot(np.diff(x), np.diff(y)) > 1e-8
    return x[keep], y[keep]


def chord_parameter(x, y):
    distance = np.hypot(np.diff(x), np.diff(y))
    t = np.r_[0.0, np.cumsum(distance)]
    if t[-1] <= 0:
        raise ValueError("所有点重合，无法建立弧长参数。")
    return t / t[-1]


def segment_boundaries(x, y):
    """根据轮廓极值和局部高度确定五个具有几何意义的分段。"""
    bottom = int(np.argmin(y))
    widest = int(np.argmax(x))
    if not (0 < bottom < widest < len(x) - 1):
        raise ValueError("点序列不像本项目的顶部到底部再回到顶部的右轮廓。")

    bottom_end_candidates = np.flatnonzero(
        (np.arange(len(y)) > bottom) & (y > y[bottom] + 1.15)
    )
    bottom_end = int(bottom_end_candidates[0]) if len(bottom_end_candidates) else bottom + 1

    shoulder_candidates = np.flatnonzero(
        (np.arange(len(y)) > widest) & (y > 0.45)
    )
    shoulder_start = int(shoulder_candidates[0]) if len(shoulder_candidates) else widest + 1

    rim_candidates = np.flatnonzero(
        (np.arange(len(y)) > shoulder_start) & (y > y.max() - 2.0)
    )
    rim_start = int(rim_candidates[0]) if len(rim_candidates) else len(y) - 5

    boundaries = [0, bottom, bottom_end, widest, shoulder_start, rim_start, len(y) - 1]
    boundaries = np.maximum.accumulate(boundaries)
    if np.any(np.diff(boundaries) < 2):
        raise ValueError(f"自动分段失败，边界为 {boundaries.tolist()}。")
    return boundaries


def make_interpolator(kind, t, values):
    if kind == "pchip":
        return PchipInterpolator(t, values)
    if kind == "akima":
        return Akima1DInterpolator(t, values)
    if kind == "cubic":
        return CubicSpline(t, values, bc_type="natural")
    raise ValueError(f"未知拟合方法: {kind}")


def fit_piece(x, y, t, start, end, kind, count):
    """拟合包含两端点的片段，返回不重复的片段采样点。"""
    local_t = t[start : end + 1]
    query = np.linspace(local_t[0], local_t[-1], count)
    fx = make_interpolator(kind, local_t, x[start : end + 1])
    fy = make_interpolator(kind, local_t, y[start : end + 1])
    return query, np.asarray(fx(query), dtype=float), np.asarray(fy(query), dtype=float)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    data = pd.read_csv(INPUT)
    if not {"x", "y"}.issubset(data.columns):
        raise ValueError("输入 CSV 必须包含 x 和 y 两列。")
    x, y = remove_consecutive_duplicates(
        data["x"].to_numpy(float), data["y"].to_numpy(float)
    )
    if len(x) < 12:
        raise ValueError("有效点太少，至少需要 12 个轮廓点。")

    t = chord_parameter(x, y)
    b = segment_boundaries(x, y)
    specs = [
        ("top_neck_down", b[0], b[1], "pchip"),
        ("rounded_base", b[1], b[2], "cubic"),
        ("lower_body", b[2], b[3], "pchip"),
        ("shoulder", b[3], b[5], "akima"),
        ("rim_and_top", b[5], b[6], "pchip"),
    ]

    pieces = []
    segment_rows = []
    for name, start, end, kind in specs:
        count = max(24, int(N_EVAL * (t[end] - t[start])))
        tq, xq, yq = fit_piece(x, y, t, start, end, kind, count)
        if pieces:
            tq, xq, yq = tq[1:], xq[1:], yq[1:]
        pieces.append((tq, xq, yq))
        segment_rows.append(
            {
                "segment": name,
                "method": kind,
                "input_start": start,
                "input_end": end,
                "input_points": end - start + 1,
                "x_min": xq.min(),
                "x_max": xq.max(),
                "y_min": yq.min(),
                "y_max": yq.max(),
            }
        )

    tq = np.concatenate([piece[0] for piece in pieces])
    xq = np.concatenate([piece[1] for piece in pieces])
    yq = np.concatenate([piece[2] for piece in pieces])

    # 统一重采样，保证输出点数固定，且不会改变分段曲线。
    uniform_t = np.linspace(tq[0], tq[-1], N_EVAL)
    x_uniform = np.interp(uniform_t, tq, xq)
    y_uniform = np.interp(uniform_t, tq, yq)
    right = pd.DataFrame({"t": uniform_t, "x": x_uniform, "y": y_uniform})
    right.to_csv(os.path.join(OUTDIR, "final_fit_right_curve.csv"), index=False)

    full_x = np.r_[-x_uniform[::-1], x_uniform]
    full_y = np.r_[y_uniform[::-1], y_uniform]
    pd.DataFrame({"x": full_x, "y": full_y}).to_csv(
        os.path.join(OUTDIR, "final_fit_full_vase.csv"), index=False
    )

    input_x = np.interp(t, uniform_t, x_uniform)
    input_y = np.interp(t, uniform_t, y_uniform)
    errors = np.hypot(input_x - x, input_y - y)
    diagnostics = pd.DataFrame(segment_rows)
    diagnostics["overall_rmse"] = np.sqrt(np.mean(errors**2))
    diagnostics["overall_max_error"] = errors.max()
    diagnostics.to_csv(os.path.join(OUTDIR, "final_fit_summary.csv"), index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    axes[0].plot(x, y, "ko", ms=3, label="input points")
    axes[0].plot(x_uniform, y_uniform, "b-", lw=1.6, label="segmented final fit")
    for name, start, end, kind in specs:
        axes[0].axvline(x[start], color="0.75", lw=0.6)
        axes[0].text(x[start], y.max(), name, rotation=90, va="top", fontsize=7)
    axes[0].set_title("Right contour")
    axes[1].plot(full_x, full_y, "b-", lw=1.6, label="mirrored final fit")
    axes[1].plot(
        np.r_[-x[::-1], x], np.r_[y[::-1], y], "k.", ms=2, label="input + mirror"
    )
    axes[1].set_title("Full vase contour")
    for ax in axes:
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.axis("equal")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "final_fit_comparison.png"), dpi=180)
    plt.close(fig)

    print(f"完成：{len(specs)} 个分段，{len(x)} 个输入点，{N_EVAL} 个输出点。")
    print("分段边界:", b.tolist())
    print(f"输入点 RMSE: {np.sqrt(np.mean(errors**2)):.6g}")
    print(f"输入点最大误差: {errors.max():.6g}")
    print("结果已写入 fit_output/final_*")


if __name__ == "__main__":
    main()
