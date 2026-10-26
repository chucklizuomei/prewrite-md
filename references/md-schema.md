# 产品描述 markdown 固定 Schema

本文件是 `prewrite-md` 技能的权威格式定义，同时与项目内 `src/md_parser.py` 的解析逻辑兼容。
生成 md（无论 LLM 还是确定性脚本）都必须严格遵循此模板。

## 模板（权威格式）

```
# <主件号> <英文品名>

## 表格信息

| 字段 | 内容 |
| --- | --- |
| 标题 | <model+description+partno+for+brand+other> |
| 类型 Type | <Title Phrase of 英文品名> |
| 发动机型号 | <model，如 C9.3> |
| 商品规格/型号 | <主件号；交叉件号：x、y> |
| 西班牙文品名 | <es name，必填> |
| 美国HS编码 | 8409.99 |
| 商品卖点 | <selling points> |

**适用机型**：<applications，顿号/逗号分隔>

## 产品描述（英文）

<英文描述正文>
```

## 字段定义
- **标题**：规则 `model + description + part_number + for + brand + other`；仅放主件号（交叉件写在规格列）。
- **类型 Type**：英文品名的标题化（and/with/for/of 等连词介词小写，首词除外）。
- **发动机型号**：如 `C9.3`、`C7`、`3406`。
- **商品规格/型号**：主件号 + `；交叉件号：x、y`（交叉件号以顿号、逗号或斜杠分隔）。
- **西班牙文品名**：双语上架必填；缺失用英→西词表兜底（valve→válvula, injector→inyector, pump→bomba, turbo→turbo, ring→anillo, liner→camisa, guide→guía, seat→asiento, piston→pistón, gasket→junta, filter→filtro, belt→correa, head→culata, block→bloque）。
- **美国HS编码**：默认 `8409.99`（发动机零件）。
- **商品卖点 / 英文描述**：用真实品名、件号、型号拼装的确定性文案，不编造参数。

## 解析规则（供 md_parser 兼容 / 回读校验）
- **表格**：`## 表格信息` 之后到下一个 `##` 之前的 `| 字段 | 内容 |` 行，逐行取键值。
- **交叉件号**：从 `商品规格/型号` 的值里取 `交叉件号：` 之后的部分，按 `、 ， , /` 切分。
- **适用机型**：从 `**适用机型**：` 之后按 `、 ， , /` 切分。
- **英文描述**：`## 产品描述（英文）` 之后到下一个 `##` 或文末。

## LLM 生成提示要点
- 严格输出上述模板，不得增删字段、不得改成无序列表。
- 必须包含 `西班牙文品名` 行且内容真实（可词表兜底）。
- 无可靠数据时，零件号留空（不要臆造）；西语名允许词表兜底。
- 文件名约定：`产品描述_<主件号>_<slug>.md`（无主件号时省略件号段）。
