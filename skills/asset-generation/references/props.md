# 道具资产

## 生成

1. 根据用途确定道具的视角、朝向和展示大小；已有同一道具的参考图时，将其作为图片输入，保持造型、材质及项目画风一致。
2. 单张只展示一个道具，完整保留轮廓、附件和镂空区域，四周留出抠图余量；不出现人物、手部、桌面或其他场景元素，除非用户明确要求。
3. 提示词加入：`Single isolated prop, fully visible with generous margins. Flat solid chroma-key green background, RGB(0, 255, 0), HEX #00FF00, uniform across the entire canvas and all gaps; no gradients, texture, ground plane, cast shadows, green spill or green tint on the prop.`
4. 检查主体及空隙、玻璃等半透明部分，确认未被背景色污染；道具本身含绿色时，标明需要保留的区域，不按底色直接删除。

## 抠图与交付

1. 保留绿底原图，按[抠图流程](background-removal.md)生成独立透明 PNG；将命令中的输入、输出路径替换为道具路径。
2. 检查细小零件、镂空、半透明边缘和残绿，在黑、灰、彩色背景上确认完整性；有问题时修正 trimap 后重做。
3. 同一道具的状态或角度变体使用相同展示比例；切换用素材保持画幅和定位一致，未经要求不覆盖已有版本。
