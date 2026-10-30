"""
统一的评价指标脚本：对 fit_methods.py 的七种方法与 final_fit.py 的分段拟合
计算同一套指标，并校验已有 fit_output/method_numerical_comparison.csv。

指标协议（与报告一致）：
* 弦长参数 t 由全部 84 个输入点确定，并在 LOOCV 中保持不变（参数化不属于
  被检验的拟合步骤）；
* Train RMSE：在输入参数 t_i 处求值并与输入点比较；
* LOOCV：去掉第 i 个点后用其余点重建方法（平滑样条的 s 与多项式次数
  作为方法超参数保持不变），在 t_i 处预测被去掉的点。端点折（i=0 与
  i=n-1）被排除：去掉端点后其余点不再包含该参数，预测退化为外推，
  对局部插值方法不适定；
* 弧长：1200 个等参采样点的折线长度；
* Outside：1200 个采样点中落在输入点包围盒外超过 1e-9 的百分比
  （容差用于忽略平直段插值产生的 1 ULP 浮点噪声）。

分段拟合的 LOOCV 同样重建整条流水线（自动分段边界 + 各段插值），被去掉点
按其全集参数 t_i 落入缩减参数化的对应分段求值（端点处夹紧）。
"""
import os

import numpy as np
import pandas as pd
from scipy.interpolate import (
    Akima1DInterpolator,
    CubicSpline,
    PchipInterpolator,
    UnivariateSpline,
    interp1d,
    make_interp_spline,
)

import final_fit

INPUT = "vase_points.csv"
OUTDIR = "fit_output"
N_EVAL = 1200


def load_points():
    df = pd.read_csv(INPUT)
    x, y = final_fit.remove_consecutive_duplicates(
        df["x"].to_numpy(float), df["y"].to_numpy(float)
    )
    return x, y


def method_builders(x, y, t):
    """返回 {名称: 接受 (t_sub, v_sub) 并返回 callable 的构造器}。"""
    scale2 = np.var(x) + np.var(y)
    smooth_s = max(len(x) * scale2 * 0.0005, 1e-10)
    poly_deg = min(5, len(x) - 1)
    return {
        "linear": lambda tt, vv: interp1d(
            tt, vv, kind="linear", fill_value="extrapolate"
        ),
        "cubic_spline": lambda tt, vv: CubicSpline(tt, vv, bc_type="natural"),
        "pchip": PchipInterpolator,
        "akima": Akima1DInterpolator,
        "bspline_cubic": lambda tt, vv: make_interp_spline(tt, vv, k=3),
        "smoothing_spline": lambda tt, vv: UnivariateSpline(tt, vv, s=smooth_s, k=3),
        f"poly_lstsq_deg{poly_deg}": lambda tt, vv: np.polyfit(tt, vv, poly_deg),
    }, smooth_s


def eval_builder(kind, model, tq):
    if kind.startswith("poly_lstsq"):
        return np.polyval(model, tq)
    if kind == "bspline_cubic":
        return np.asarray(model(tq, extrapolate=True), dtype=float)
    return np.asarray(model(tq), dtype=float)


BBOX_TOL = 1e-9


def curve_metrics(xq, yq, x, y):
    arc = float(np.hypot(np.diff(xq), np.diff(yq)).sum())
    outside = 100.0 * float(
        np.mean(
            (xq < x.min() - BBOX_TOL)
            | (xq > x.max() + BBOX_TOL)
            | (yq < y.min() - BBOX_TOL)
            | (yq > y.max() + BBOX_TOL)
        )
    )
    return arc, outside


def metrics_for_method(kind, builder, x, y, t):
    tq = np.linspace(0.0, 1.0, N_EVAL)
    fx = builder(t, x)
    fy = builder(t, y)
    xq, yq = eval_builder(kind, fx, tq), eval_builder(kind, fy, tq)
    train = np.hypot(eval_builder(kind, fx, t) - x, eval_builder(kind, fy, t) - y)
    loo = []
    for i in range(1, len(t) - 1):
        mask = np.ones(len(t), dtype=bool)
        mask[i] = False
        gx = builder(t[mask], x[mask])
        gy = builder(t[mask], y[mask])
        loo.append(
            np.hypot(
                eval_builder(kind, gx, t[i]) - x[i],
                eval_builder(kind, gy, t[i]) - y[i],
            )
        )
    loo = np.asarray(loo)
    arc, outside = curve_metrics(xq, yq, x, y)
    return {
        "method": kind,
        "n": len(t),
        "train_rmse": float(np.sqrt(np.mean(train**2))),
        "train_max": float(train.max()),
        "loo_rmse": float(np.sqrt(np.mean(loo**2))),
        "loo_max": float(loo.max()),
        "arc_length": arc,
        "bbox_outside_pct": outside,
    }


class PiecewiseFit:
    """final_fit.py 流水线的可求值封装。"""

    def __init__(self, x, y, boundaries=None):
        self.x, self.y = final_fit.remove_consecutive_duplicates(x, y)
        self.t = final_fit.chord_parameter(self.x, self.y)
        b = final_fit.segment_boundaries(self.x, self.y) if boundaries is None else boundaries
        self.b = b
        self.specs = [
            (b[0], b[1], "pchip"),
            (b[1], b[2], "cubic"),
            (b[2], b[3], "pchip"),
            (b[3], b[5], "akima"),
            (b[5], b[6], "pchip"),
        ]
        self.segs = []
        for start, end, kind in self.specs:
            lt = self.t[start : end + 1]
            self.segs.append(
                (
                    lt[0],
                    lt[-1],
                    final_fit.make_interpolator(kind, lt, self.x[start : end + 1]),
                    final_fit.make_interpolator(kind, lt, self.y[start : end + 1]),
                )
            )

    def eval(self, tq):
        tq = np.atleast_1d(np.asarray(tq, dtype=float))
        out_x = np.empty_like(tq)
        out_y = np.empty_like(tq)
        for k, tv in enumerate(tq):
            lo, hi, fx, fy = self._segment_for(tv)
            tc = min(max(tv, lo), hi)
            out_x[k] = float(fx(tc))
            out_y[k] = float(fy(tc))
        return out_x, out_y

    def _segment_for(self, tv):
        for seg in self.segs:
            if tv <= seg[1] + 1e-12:
                return seg
        return self.segs[-1]

    def uniform_curve(self):
        pieces_t, pieces_x, pieces_y = [], [], []
        for (start, end, _), (lo, hi, fx, fy) in zip(self.specs, self.segs):
            count = max(24, int(N_EVAL * (hi - lo)))
            qt = np.linspace(lo, hi, count)
            if pieces_t:
                qt, fxq, fyq = qt[1:], np.asarray(fx(qt[1:])), np.asarray(fy(qt[1:]))
            else:
                fxq, fyq = np.asarray(fx(qt)), np.asarray(fy(qt))
            pieces_t.append(qt)
            pieces_x.append(fxq)
            pieces_y.append(fyq)
        tq = np.concatenate(pieces_t)
        xq = np.concatenate(pieces_x)
        yq = np.concatenate(pieces_y)
        uniform_t = np.linspace(tq[0], tq[-1], N_EVAL)
        return uniform_t, np.interp(uniform_t, tq, xq), np.interp(uniform_t, tq, yq)


def metrics_for_final(x, y):
    t = final_fit.chord_parameter(*final_fit.remove_consecutive_duplicates(x, y))
    fit = PiecewiseFit(x, y)
    ix, iy = fit.eval(t)
    train = np.hypot(ix - fit.x, iy - fit.y)
    # 端到端 LOOCV：每折重新自动分段；固定分段 LOOCV：分段边界取自全集
    # （删除点之后的索引平移），只检验各段插值本身。
    loo, loo_fixed = [], []
    failures = 0
    for i in range(1, len(t) - 1):
        xr, yr = np.delete(fit.x, i), np.delete(fit.y, i)
        shifted = np.maximum.accumulate(
            [k - 1 if k > i else k for k in fit.b]
        )
        try:
            reduced = PiecewiseFit(xr, yr)
            px, py = reduced.eval(t[i])
            fixed = PiecewiseFit(xr, yr, boundaries=shifted)
            fx_, fy_ = fixed.eval(t[i])
        except ValueError:
            failures += 1
            continue
        loo.append(np.hypot(px - fit.x[i], py - fit.y[i]))
        loo_fixed.append(np.hypot(fx_ - fit.x[i], fy_ - fit.y[i]))
    loo = np.asarray(loo)
    loo_fixed = np.asarray(loo_fixed)
    _, xq, yq = fit.uniform_curve()
    arc, outside = curve_metrics(xq, yq, fit.x, fit.y)
    return {
        "method": "final_piecewise",
        "n": len(t),
        "train_rmse": float(np.sqrt(np.mean(train**2))),
        "train_max": float(train.max()),
        "loo_rmse": float(np.sqrt(np.mean(loo**2))),
        "loo_max": float(loo.max()),
        "arc_length": arc,
        "bbox_outside_pct": outside,
        "loo_rmse_fixed_segments": float(np.sqrt(np.mean(loo_fixed**2))),
        "loo_max_fixed_segments": float(loo_fixed.max()),
        "loo_failures": failures,
    }, t


def main():
    x, y = load_points()
    t = final_fit.chord_parameter(x, y)
    builders, smooth_s = method_builders(x, y, t)
    print(f"smoothing s = {smooth_s:.10g}")

    rows = [metrics_for_method(k, b, x, y, t) for k, b in builders.items()]

    final_row, _ = metrics_for_final(x, y)
    print("分段最终拟合指标：")
    for k, v in final_row.items():
        print(f"  {k:18s} {v}")

    out = pd.DataFrame(rows + [final_row])
    cols = [
        "method", "n", "train_rmse", "train_max",
        "loo_rmse", "loo_max", "arc_length", "bbox_outside_pct",
    ]
    out = out[cols]
    out.to_csv(os.path.join(OUTDIR, "method_numerical_comparison.csv"), index=False)
    print("\n已写入 fit_output/method_numerical_comparison.csv（含 final_piecewise 行）")
    print(out.to_string(index=False, float_format=lambda v: f"{v:.4f}"))


if __name__ == "__main__":
    main()
