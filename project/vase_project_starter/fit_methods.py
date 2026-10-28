"""
多种参数曲线插值/拟合 + 关于 y 轴镜像重构
依赖：pip install numpy scipy matplotlib pandas
输入：vase_points.csv（由 extract_vase.py 生成）
注意：点必须沿轮廓顺序排列，不要按 x 排序。
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import (
    interp1d, CubicSpline, PchipInterpolator,
    Akima1DInterpolator, make_interp_spline, UnivariateSpline
)

INPUT = "vase_points.csv"
OUTDIR = "fit_output"
N_EVAL = 1200
os.makedirs(OUTDIR, exist_ok=True)


def chord_parameter(x, y):
    ds = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    t = np.concatenate([[0.0], np.cumsum(ds)])
    if t[-1] == 0:
        raise ValueError("所有点重合，无法建立参数。")
    return t / t[-1]


def main():
    df = pd.read_csv(INPUT)
    x = df["x"].to_numpy(float)
    y = df["y"].to_numpy(float)
    if len(x) < 8:
        raise ValueError("点太少，建议至少 8 个点，复杂轮廓建议 30-100 个点。")

    # 删除连续重复点，避免插值参数重复
    keep = np.ones(len(x), dtype=bool)
    keep[1:] = (np.hypot(np.diff(x), np.diff(y)) > 1e-8)
    x, y = x[keep], y[keep]
    t = chord_parameter(x, y)
    tq = np.linspace(0, 1, N_EVAL)

    methods = {}

    # 1. 分段线性插值
    methods["linear"] = (
        interp1d(t, x, kind="linear")(tq),
        interp1d(t, y, kind="linear")(tq)
    )

    # 2. 自然三次样条
    methods["cubic_spline"] = (
        CubicSpline(t, x, bc_type="natural")(tq),
        CubicSpline(t, y, bc_type="natural")(tq)
    )

    # 3. PCHIP 保形插值
    methods["pchip"] = (
        PchipInterpolator(t, x)(tq),
        PchipInterpolator(t, y)(tq)
    )

    # 4. Akima 局部插值
    methods["akima"] = (
        Akima1DInterpolator(t, x)(tq),
        Akima1DInterpolator(t, y)(tq)
    )

    # 5. 三次 B 样条插值
    methods["bspline_cubic"] = (
        make_interp_spline(t, x, k=3)(tq),
        make_interp_spline(t, y, k=3)(tq)
    )

    # 6. 平滑样条（这是拟合而非严格穿过每个点；s 值应做实验调整）
    # s=0 是插值；这里使用与坐标尺度相关的温和非零平滑参数
    scale2 = np.var(x) + np.var(y)
    smooth_s = max(len(x) * scale2 * 0.0005, 1e-10)
    methods["smoothing_spline"] = (
        UnivariateSpline(t, x, s=smooth_s, k=3)(tq),
        UnivariateSpline(t, y, s=smooth_s, k=3)(tq)
    )

    # 7. 多项式最小二乘：仅作为对照，不建议用高阶全局多项式描述复杂轮廓
    poly_deg = min(5, len(x)-1)
    methods[f"poly_lstsq_deg{poly_deg}"] = (
        np.polyval(np.polyfit(t, x, poly_deg), tq),
        np.polyval(np.polyfit(t, y, poly_deg), tq)
    )

    # 将右半边按 x -> -x 镜像，保存完整轮廓。
    # 为避免重复拼接端点：左侧反向 + 右侧正向。
    summary = []
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(x, y, "ko", ms=3, label="input points")

    for name, (xq, yq) in methods.items():
        ax.plot(xq, yq, lw=1.5, label=name)
        # full contour: mirrored left side reversed, then right side
        full_x = np.concatenate([-xq[::-1], xq])
        full_y = np.concatenate([yq[::-1], yq])
        pd.DataFrame({"x": full_x, "y": full_y}).to_csv(
            os.path.join(OUTDIR, f"{name}_full_vase.csv"), index=False
        )
        pd.DataFrame({"t": tq, "x": xq, "y": yq}).to_csv(
            os.path.join(OUTDIR, f"{name}_right_curve.csv"), index=False
        )
        summary.append({
            "method": name,
            "eval_points": len(tq),
            "input_points": len(x),
            "smoothing_parameter": smooth_s if name == "smoothing_spline" else np.nan,
            "note": "visual comparison; use held-out points for meaningful validation error"
        })

    ax.set_title("Right-half contour: interpolation/fitting comparison")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "method_comparison.png"), dpi=180)
    plt.close(fig)

    # 绘制所有完整花瓶轮廓
    fig, ax = plt.subplots(figsize=(8, 8))
    for name, (xq, yq) in methods.items():
        ax.plot(np.r_[-xq[::-1], xq], np.r_[yq[::-1], yq], lw=1.3, label=name)
    ax.set_title("Full vase contour comparison")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "full_vase_comparison.png"), dpi=180)
    plt.close(fig)

    pd.DataFrame(summary).to_csv(os.path.join(OUTDIR, "method_summary.csv"), index=False)
    print("完成。结果保存在：", OUTDIR)
    print("请检查 method_comparison.png 和 full_vase_comparison.png。")
    print("提醒：多项式拟合、平滑样条不是严格插值；需要在报告中区分。")


if __name__ == "__main__":
    main()
