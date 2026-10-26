---
name: prewrite-md
description: 为 Alibaba 发动机零配件上架项目预写标准化产品描述 markdown（产品描述_*.md）。当产品文件夹缺少 md、需要按固定 schema 生成含零件号/交叉件号/西语名/卖点/适用机型的标准化描述并写回文件夹时使用。This skill should be used when a product folder in the Alibaba upload library lacks a 产品描述_*.md file, or when asked to pre-write, generate, or backfill standardized product description markdown for engine spare parts before running the upload pipeline. It covers the md schema, the metadata-collection workflow, and the idempotent write-back rule.
agent_created: true
---

# Prewrite Md（预写产品描述 markdown）

## Overview

为 Alibaba 发动机零配件上架流水线预写标准化产品描述 `产品描述_*.md`。该 md 是后续 `run` 阶段的高置信数据源（优于联网检索），也是 `check-md` 校验关卡的审查对象。本技能提炼固定 schema、元数据收集工作流与写回规则，使"预写 md"成为可独立触发、可复用的能力。

权威实现仍在本项目的 `src/md_generator.py` 与 `src/orchestrator.py::_stage_gen_md`；本技能是将其抽离出的独立、可迁移版本。

## When To Use

- 产品文件夹缺少 `产品描述_*.md`，需要补写。
- 用户要求"预写 md / 生成产品描述 / 回填描述文档 / 给每个文件夹写一份说明"。
- 跑主流程（`pipeline.py run`）之前，先批量生成 md 供人工过目或 `check-md` 校验。
- 注意：本技能只产出 md 文件，不处理图片、不写 Excel 模板（那些是流水线其他阶段）。

## Fixed Schema（固定模板）

生成的 md 必须严格对齐 `references/md-schema.md` 中的模板，核心结构如下（完整字段与解析规则见该文件）：

```
# <主件号> <英文品名>

## 表格信息

| 字段 | 内容 |
| --- | --- |
| 标题 | <model+description+partno+for+brand+other> |
| 类型 Type | <Title Phrase> |
| 发动机型号 | <model> |
| 商品规格/型号 | <主件号；交叉件号：x、y> |
| 西班牙文品名 | <es name> |
| 美国HS编码 | 8409.99 |
| 商品卖点 | <selling points> |

**适用机型**：<applications>

## 产品描述（英文）

<description>
```

硬性约束：
- **西班牙文品名**为必填字段（双语上架必需），缺失则 `check-md` 标红。无现成西语名时用英→西词表兜底（valve→válvula, injector→inyector）。
- **商品规格/型号**写入主件号，并附 `交叉件号：x、y`（交叉件号来自检索/库）。
- 标题遵循 `model + description + part_number + for + brand + other` 规则。

## Workflow

执行预写 md 时，按以下步骤操作（每个产品文件夹独立、错误隔离）：

### Step 1 — 检测是否已有 md（幂等）
检查文件夹内是否已存在 `产品描述_*.md`。若已存在，**跳过**，不覆盖（gen-md 阶段重复运行应保持幂等）。

### Step 2 — 收集元数据
从以下来源按优先级补齐字段（零件号 / 交叉件号 / 英文品名 / 西语名 / 适用机型 / 卖点）：
1. 解析**文件夹名**：提取零件号（如 `490-1729`）、发动机型号（如 `C9.3`）、零件名（如 `intake exhaust valve`）。
2. 若文件夹名**无零件号**（仅型号+品名），用 LLM / WebSearch 搜索匹配零件号；找不到则保持空，不臆造。
3. 若产品无 md，用 LLM 补全"干净的英文品名 + 适用机型"（修正文件夹拼写错误，如 `exhasut`→`exhaust`）。
4. 交叉件号、西语名、HS 编码、卖点优先取自检索结果或供应商库；缺失用确定性兜底（西语名走英→西词表，HS 默认 `8409.99`）。

### Step 3 — 生成 md 文本
- 优先用 LLM 生成完整 md（要求严格遵循 `references/md-schema.md` 模板，且必须含`西班牙文品名`）。
- 无 LLM / 缓存缺失时，用确定性生成器 `scripts/gen_product_md.py` 基于已收集的真实数据产出 md，保证不空白。

### Step 4 — 写回文件夹
文件名：`产品描述_<主件号>_<slug>.md`（`slug` 取文件夹名 ASCII 化；无主件号时省略件号段）。写回位置由 `md.write_to` 决定：`out`（默认，写入 `out/<产品>/`，与成品图同目录，便于一起查看）／`folder`（写回产品源文件夹，便于版本化）／`work`（仅写 `work/md/`，零改动源库的隔离模式）。**仅新增该 md 文件，绝不修改原图或其他文件。**

### Step 5 — 回读校验
用 `references/md-schema.md` 的解析规则回读生成的 md，确认表格字段、`交叉件号`、`适用机型`、英文描述均可被解析；失败则修正后重写。

## Rules

- **源库只读原则**：除写回这份 md 文件外，不得修改图库内任何原图或原文件。
- **不编造商业数据**：零件号、价格、重量、HS 等要么检索得到，要么用显式默认值（HS `8409.99`、可售 600 等）；西语名允许词表兜底，但件号不可臆造。
- **幂等**：已存在 md 跳过；重跑不产生重复文件。
- **西语名必填**：缺西语名的 md 在 `check-md` 会被标红，需在写回前补齐。

## Resources

- `references/md-schema.md` — 完整 md 模板、字段定义与解析规则（兼容 `md_parser`）。
- `scripts/gen_product_md.py` — 独立的确定性生成器：给定文件夹（及可选 `--meta` JSON 元数据），按固定 schema 生成并写回 md，无外部依赖，可直接执行。
