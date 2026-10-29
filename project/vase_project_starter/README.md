# 花瓶轮廓提取、数值拟合与 OpenGL 三维重建

本项目从带坐标网格的花瓶图像中提取右半边轮廓，将像素坐标转换为数学坐标，
使用分段数值方法拟合二维轮廓，再利用关于 `y` 轴的对称性恢复完整轮廓，并在
OpenGL 中将二维母线绕竖直轴旋转，生成可交互观察的三维花瓶。

项目重点是：

- 图像坐标标定和轮廓点提取；
- 弦长参数化下的参数曲线插值；
- 根据花瓶不同部位选择合适的局部数值方法；
- 关于 `y` 轴的对称重构；
- OpenGL 旋转曲面和交互式显示。

## 项目结构

```text
vase_project_starter/
├─ extract_vase.py              # 人工主导的轮廓提取
├─ extract_vase_hybrid.py       # 人工锚点 + 自动边缘吸附
├─ final_fit.py                 # 最终分段拟合和对称重构
├─ fit_methods.py               # 多种拟合方法的对比实验
├─ vase_points.csv              # 提取后的输入轮廓点
├─ fit_output/                  # 拟合结果、CSV、汇总表和图片
├─ report/
│  ├─ report.tex                # LaTeX 项目报告
│  └─ report.pdf                # 编译后的项目报告
├─ viewer/
│  ├─ CMakeLists.txt            # OpenGL/GLUT 构建配置
│  ├─ src/main.cpp              # 三维旋转曲面程序
│  ├─ include/gl/glut.h         # GLUT 头文件
│  ├─ lib/                      # GLUT 的 .lib 和 .dll
│  └─ build/                    # CMake 构建目录，需自行生成
├─ contour_review.png           # 轮廓点检查图
├─ threshold_preview.png        # 阈值候选像素预览
└─ requirements.txt             # Python 依赖
```

## 环境要求

### Python

建议使用 Python 3.10 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

主要依赖：

- OpenCV；
- NumPy；
- SciPy；
- pandas；
- Matplotlib。

### C++ / OpenGL

三维显示部分使用 Windows OpenGL、GLU 和 GLUT。项目已经提供：

```text
viewer/include/gl/glut.h
viewer/lib/glut32.lib
viewer/lib/glut32.dll
```

也支持回退使用 `glut.lib` 和 `glut.dll`。建议使用 Visual Studio 2022
或其他能够链接 Windows `.lib` 导入库的 C++ 工具链。

## 第一步：提取轮廓坐标

项目提供两种坐标提取方式，两者都会生成兼容后续拟合的 `vase_points.csv`。

### 方式一：人工主导提取

```powershell
python extract_vase.py
```

操作流程：

1. 选择包含坐标网格和花瓶的 ROI；
2. 依次点击原点 `O`、`x=5` 刻度点、`y=5` 刻度点；
3. 从顶部开始，沿花瓶右半边轮廓按顺序逐点点击；
4. 左键添加轮廓点；
5. 右键或 Backspace 撤销最后一个轮廓点；
6. 按 Enter 保存，按 Esc 取消。

输出：

```text
vase_points.csv
contour_review.png
threshold_preview.png
```

人工方法不会自动改变点击位置，适合瓶口、瓶底、瓶肩等边缘复杂或网格线干扰
较强的区域。

### 方式二：人工锚点 + 自动吸附

```powershell
python extract_vase_hybrid.py
```

操作流程与人工方法相同，但在轮廓阶段只需要点击较少的锚点。程序会：

1. 在点击点附近搜索 Canny 边缘；
2. 根据边缘强度和距离惩罚，将锚点吸附到附近候选边缘；
3. 在相邻锚点之间自动加密；
4. 对加密点再次进行局部边缘吸附；
5. 输出较密集的轮廓点。

该方法可以降低鼠标定位误差并使点间距更均匀，但不能保证不会吸附到网格线。
使用后必须检查 `contour_review.png`：

- 红点：人工锚点；
- 绿色线：自动加密后的轮廓。

如果绿色线跳到网格线或坐标轴上，应增加人工锚点，或改用
`extract_vase.py` 在该区域逐点采集。

### 两种提取方法的选择

| 项目 | `extract_vase.py` | `extract_vase_hybrid.py` |
|---|---|---|
| 点的来源 | 全部人工点击 | 人工锚点加自动吸附 |
| 鼠标定位误差 | 较依赖人工精度 | 通常较小 |
| 点间距 | 可能不均匀 | 自动加密，较均匀 |
| 网格线风险 | 人工可主动避开 | 可能吸附到网格线 |
| 复杂转折 | 人工判断能力强 | 需要增加锚点 |
| 操作成本 | 点击点数较多 | 点击锚点较少 |
| 推荐场景 | 边缘模糊或局部复杂 | 边缘清晰、轮廓较长 |

推荐的实际工作方式是：先使用混合方法快速获得轮廓，再对瓶口、瓶底、瓶肩和
网格线交叉处进行人工检查和修正。

## 第二步：运行最终分段拟合

```powershell
python final_fit.py
```

输入：

```text
vase_points.csv
```

输出到 `fit_output/`：

```text
final_fit_right_curve.csv   # 右半边拟合曲线，列为 t,x,y
final_fit_full_vase.csv     # 关于 y 轴镜像后的完整轮廓，列为 x,y
final_fit_summary.csv       # 分段方法和误差诊断
final_fit_comparison.png    # 右半轮廓和完整轮廓对比图
```

## 分段数值方法

`final_fit.py` 使用弦长参数 `t` 表示轮廓位置：

```text
点序列 → 累计弦长 → 归一化参数 t → 分别拟合 x(t)、y(t)
```

当前最终方法如下：

| 花瓶部位 | 方法 | 原因 |
|---|---|---|
| 顶部窄颈至底部 | PCHIP | 保持近似竖直趋势，避免过冲 |
| 瓶底圆角 | 自然三次样条 | 获得平滑圆角过渡 |
| 下部瓶身 | PCHIP | 保持外扩趋势和局部形状 |
| 瓶肩过渡 | Akima | 局部平滑，降低振荡 |
| 瓶口与顶部 | PCHIP | 保持转折、端点和局部范围 |

没有使用五次全局多项式作为最终曲线，因为全局多项式会让一个区域的误差影响
整条轮廓，并且容易导致瓶身缩窄、瓶口偏移和局部形状失真。

## 第三步：构建 OpenGL 三维程序

进入 OpenGL 项目目录：

```powershell
cd viewer
```

使用 CMake 配置和构建：

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```

如果使用默认生成器，也可以：

```powershell
cmake -S . -B build
cmake --build build --config Release
```

构建完成后，程序通常位于：

```text
viewer/build/Release/VaseReconstruction.exe
```

程序构建后会自动把对应的 GLUT DLL 复制到可执行文件目录。

## 第四步：运行三维重建

从 `viewer` 目录运行时，程序会自动寻找最终右半曲线：

```powershell
.\build\Release\VaseReconstruction.exe
```

也可以显式传入 CSV：

```powershell
.\build\Release\VaseReconstruction.exe `
  ..\fit_output\final_fit_right_curve.csv
```

程序读取 `final_fit_right_curve.csv` 中的 `x` 和 `y` 列，将：

```text
radius = x
height = y
```

作为旋转母线，绕 `y` 轴生成三维曲面。注意该 CSV 的列顺序为：

```csv
t,x,y
```

程序通过表头寻找 `x` 和 `y`，不会把 `t` 错当成半径。

## OpenGL 交互控制

| 按键 | 功能 |
|---|---|
| 方向键 | 旋转模型 |
| `W/A/S/D` | 旋转模型 |
| `+` / `-` | 缩放 |
| `PageUp/PageDown` | 缩放 |
| `I/J/K/L` | 平移视角 |
| `F` | 开关光照 |
| `1` | 暖色光 |
| `2` | 冷色光 |
| `3` | 白色光 |
| `T` | 切换实体/线框模式 |
| `O` | 显示/隐藏坐标轴 |
| `Space` | 开关自动旋转 |
| `R` | 重置视角 |
| `Q` 或 `Esc` | 退出程序 |

CSV 在程序启动时读取一次。重新运行 `final_fit.py` 生成新的 CSV 后，不需要重新
编译 C++ 程序，只需要关闭并重新启动 OpenGL 程序。

只有修改以下内容时才需要重新编译：

- `viewer/src/main.cpp`；
- `viewer/CMakeLists.txt`；
- OpenGL 交互逻辑；
- 曲面网格生成逻辑；
- 法向量、光照或材质实现。

## 方法对比实验

如果需要比较不同拟合方法，可以运行：

```powershell
python fit_methods.py
```

输出包括：

```text
fit_output/*_right_curve.csv
fit_output/*_full_vase.csv
fit_output/method_comparison.png
fit_output/full_vase_comparison.png
fit_output/method_summary.csv
```

该脚本用于方法对比，不是最终推荐方法。最终三维重建应优先使用：

```text
fit_output/final_fit_right_curve.csv
```

## 报告


报告包括：

- 项目结构和处理流程；
- OpenCV 坐标提取和校准理论；
- 人工提取与混合提取方法比较；
- 弦长参数化；
- 线性、三次样条、PCHIP、Akima 等数值方法；
- 分段拟合的设计依据；
- 对称性重构；
- OpenGL 旋转曲面和交互显示；
- 误差分析和结果图占位。

## 常见问题

### 1. 拟合结果不准确

先检查：

- 轮廓点是否按边界顺序排列；
- 是否误点了网格线；
- 是否漏掉瓶口、瓶底和瓶肩转折点；
- 三个校准点是否依次为 `O`、`x=5`、`y=5`；
- 是否查看了 `contour_review.png`。

### 2. 混合提取跳到了网格线

增加该区域的人工锚点，缩短锚点间距；如果仍然错误，使用
`extract_vase.py` 手动逐点提取该区域。

### 3. OpenGL 程序打不开 CSV

确认：

- 已经运行 `python final_fit.py`；
- `fit_output/final_fit_right_curve.csv` 存在；
- 当前传入的路径正确；
- CSV 包含 `x` 和 `y` 表头。

### 4. OpenGL 程序缺少 DLL

确认 `glut32.dll` 或 `glut.dll` 位于可执行文件同一目录，或者位于系统 PATH
中的目录。使用 CMake 构建时，项目会尝试自动复制 DLL。

## 项目结论

本项目采用“OpenCV 提取坐标 + SciPy 分段数值拟合 + 对称性重构 +
OpenGL 旋转曲面显示”的完整流程。对于当前花瓶数据，分段方法比单一全局方法
更能兼顾平滑性、准确性和鲁棒性；人工主导提取提供可靠的几何判断，混合提取则
降低了像素级定位误差。最终生成的右半轮廓 CSV 可以直接作为 OpenGL 旋转曲面的
母线数据。
