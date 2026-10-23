# 角色资产

## 通用要求

- 提示词加入：`Flat solid chroma-key green background, RGB(0, 255, 0), HEX #00FF00, uniform across the entire canvas and all gaps; no gradients, texture, cast shadows, green spill or green tint on the character.` 生成后检查背景及空隙，不能只凭提示词判断达标。
- 衍生素材必须将 turnaround 母版作为参考图输入；保持外观、服装、身体比例及画风一致，仅改变本次指定的部分。
- 已有母版时直接复用；缺少时先生成母版。未经用户明确要求，不修改或覆盖母版。

## Turnaround 母版

1. 生成正面（front）、四分之三侧面（three-quarter）、正侧面（profile）、背面（back）四个角度，并排放在同一张图中。
2. 检查各视图完整展示全身，角色设计、展示比例和脚底基线一致。
3. 保存原始绿底图，作为后续角色素材的母版。

## 半身立绘

1. 加载该角色的 turnaround 母版，按对话需求设置朝向、表情与手势。
2. 单张只展示一个角色、一个姿态；默认腰上构图，完整保留头部及入镜的双手，不在手腕或手指处裁切。
3. 同一角色的多张立绘保持展示比例及头部位置一致。
4. 保存绿底原图；需要透明版本时按[抠图流程](background-removal.md)另存 PNG。
