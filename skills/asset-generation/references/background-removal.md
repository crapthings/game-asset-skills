# 背景去除

## 执行流程

1. 用 `scripts/key_white.py` 生成 trimap 草稿；绿底指定 `--background green`，旧白底指定 `--background white`。
2. 检查并修正 trimap：黑色为背景、白色为前景、灰色为待估计区域。重点检查同色衣物、发丝、手指及封闭空隙。
3. 输入检查后的 trimap，执行 PyMatting Alpha 估计及 `estimate_foreground_ml` 前景去污染。绿底模式同时清理小块高饱和残绿，并在透明轮廓附近抑制绿色污染、保留 Alpha；脚本自动扩展完全透明区域的 RGB。
4. 检查输出的黑、灰、彩色背景图，确认边缘及主体完整；有问题时修正 trimap 或参数后另存新版，保留母版。

## 命令

从项目根目录执行；依赖由 uv 和配套锁文件管理，不手动 pip 安装。先将 `skill_dir` 设置为本次读取的 `SKILL.md` 所在目录的绝对路径，不假定技能安装在项目内。资产路径相对项目根目录；输出文件名须未被占用。

```sh
skill_dir='/absolute/path/to/asset-generation'
keyer="$skill_dir/scripts/key_white.py"
asset_dir='references/assets/characters/角色名称'
source_image="$asset_dir/turnaround.png"

uv run --locked "$keyer" "$source_image" "$asset_dir/trimap.png" --prepare --background green

# 检查并修正 trimap 后执行。
uv run --locked "$keyer" "$source_image" "$asset_dir/turnaround-transparent.png" --trimap "$asset_dir/trimap.png" --background green
```

已有透明 PNG 仅需清理残绿时：

```sh
uv run --locked "$keyer" "$asset_dir/turnaround-transparent.png" "$asset_dir/turnaround-game.png" --clean-green
```

## 调整参数

- `--radius`：trimap 待估计边缘半径，默认 3 像素。
- `--green-difference`：绿底识别色差 `G - max(R, B)`，默认 60。
- `--white-threshold`：白底识别阈值，默认 245。
- `--green-max-area` / `--green-edge-radius`：残绿块最大面积 / 距透明区域的最大距离，默认 64 像素 / 32 像素；小型绿色饰品可能误判，须检查输出。
- `--bleed-only`：仅扩展透明 RGB，保持 Alpha 不变，不清理残绿。
- `--prepare` 和 `--trimap` 输入不透明原图；`--clean-green` 和 `--bleed-only` 输入已有透明图。所有输出保持原始分辨率，不覆盖已有文件。

修改依赖后更新锁文件：

```sh
uv lock --script "$keyer"
```
