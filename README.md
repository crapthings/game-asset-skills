# Game Asset Skills

用于 Codex 的游戏资产技能组，可按需安装，持续补充。

| 技能 | 用途 |
| --- | --- |
| [asset-analysis](skills/asset-analysis/SKILL.md) | 从剧本及已有素材整理资产需求、变体和演出安排 |
| [asset-generation](skills/asset-generation/SKILL.md) | 生成角色、场景、道具，处理透明背景并交付文件 |

## 安装

在终端执行（需安装 Node.js，提供 `npx`）：

```bash
npx skills add crapthings/game-asset-skills
```

按提示选择 Codex、需要的技能及安装范围。命令直接从 GitHub 获取技能，无需等待 skills.sh 收录。

也可以在 Codex 中调用内置技能安装器：

```text
$skill-installer 从 crapthings/game-asset-skills 安装 skills/asset-analysis 和 skills/asset-generation
```

也可以将所需技能文件夹复制到 `~/.codex/skills/`（自定义 `CODEX_HOME` 时使用其下的 `skills/`），或项目的 `.agents/skills/`。安装后在下一轮对话中使用。

## 使用

```text
$asset-analysis 根据这段剧本整理资产需求，并检查已有素材可以如何复用。
$asset-generation 根据资产需求生成角色或道具，并处理成透明 PNG。
```

资产生成依赖 Codex 的 Image Gen（`$imagegen`）能力；抠图使用 uv 管理依赖，脚本要求 Python 3.11–3.13。无需手动 pip 安装。项目风格从目标项目的 `AGENTS.md` 读取，资产输出到目标项目的 `references/assets/`。

## 维护

通过 `npx skills` 安装后，在相应安装范围内执行以下命令更新已安装的技能：

```bash
npx skills update
```

通过 Codex 内置安装器或手动复制安装的副本，需用新版替换对应技能目录。

每个技能独立放在 `skills/<技能名称>/`。维护时修改对应 `SKILL.md`、引用文件或脚本，提交并推送到 GitHub；已安装的副本不会随仓库提交自动更新。
