# prewrite-md · 预写产品描述 md（WorkBuddy 技能）

为 Alibaba 上架流水线预写标准化产品描述 markdown（`产品描述_*.md`）的可复用技能。

给定一个「按 SKU 分文件夹」的发动机零配件图库，本技能为缺少 md 的产品文件夹生成一份固定 schema 的产品描述，包含零件号 / 交叉件号 / 西语品名 / 卖点 / 适用机型 / HS 编码。生成的 md 既是人工过目的审查对象，也是后续批量上传流水线的高置信数据源。

## 适用场景

- 产品文件夹缺少 `产品描述_*.md`，需要补写
- 要求「预写 md / 生成产品描述 / 回填描述文档 / 给每个文件夹写一份说明」
- 跑上传主流程之前，先批量产出 md 供人工核对

只产出 md 文件，不处理图片、不写 Excel 模板。

## 安装

技能是纯本地文件。两种安装方式：

```bash
# 方式一：装到本机（跨所有项目可用）
git clone <this-repo> ~/.workbuddy/skills/prewrite-md

# 方式二：装到某个项目（随项目共享）
git clone <this-repo> <your-project>/.workbuddy/skills/prewrite-md
```

安装后在 WorkBuddy 对话里说「给这个文件夹预写产品描述 md」即可触发。

## 目录结构

```
prewrite-md/
├── SKILL.md                     # 触发条件 / 固定 schema / 五步工作流 / 硬性规则
├── references/
│   └── md-schema.md            # md 模板、字段定义与解析规则
├── scripts/
│   └── gen_product_md.py       # 零依赖确定性生成器（--meta / --dry）
├── README.md
└── LICENSE
```

## md 固定 schema

```markdown
# <主件号> <英文品名>

## 表格信息

| 字段 | 内容 |
| --- | --- |
| 标题 | <model + description + part number + for + brand + other> |
| 类型 Type | <Title Phrase> |
| 发动机型号 | <model> |
| 商品规格/型号 | <主件号；交叉件号：x、y> |
| 西班牙文品名 | <西语名> |
| 美国HS编码 | 8409.99 |
| 商品卖点 | <selling points> |

**适用机型**：<applications>

## 产品描述（英文）

<description>
```

硬性约束：

- **西班牙文品名必填** —— 双语上架必需，缺失会被校验关卡标红；无现成西语名时用英→西词表兜底（valve→válvula, injector→inyector）。
- **商品规格/型号** 写主件号，并附 `交叉件号：x、y`。
- **标题** 遵循 `model + description + part_number + for + brand + other`。

## 生成器用法

`scripts/gen_product_md.py` 是纯标准库实现，无第三方依赖，可离线运行。

```bash
# 仅预览（不落盘）
python3 scripts/gen_product_md.py "G3616 valve guide 175-6344 7C2424 1W1753" --dry

# 生成并写入该文件夹
python3 scripts/gen_product_md.py "/path/to/folder"

# 用元数据覆盖解析结果（推荐：件号/西语名/适用机型来自检索结果时）
cat > meta.json <<'EOF'
{
  "part_nos": ["490-1729"],
  "cross_refs": ["490-1728", "490-1730"],
  "en_name": "Intake and Exhaust Valve",
  "es_name": "Válvula de admisión y escape",
  "model": "C9.3",
  "applications": ["Caterpillar C9.3"],
  "selling_points": "OEM quality; precise fit; corrosion resistant."
}
EOF
python3 scripts/gen_product_md.py "/path/to/folder" --meta meta.json
```

### 文件夹名解析能力

支持三种卡特件号形态，并把 G 系列机型排除出件号：

| 输入文件夹名 | 主件号 | 交叉件 | 型号 | 品名 |
| --- | --- | --- | --- | --- |
| `G3616 valve guide 175-6344 7C2424 1W1753` | `175-6344` | `7C2424`、`1W1753` | `G3616` | `valve guide` |
| `G3616 oil cooler 1W5200` | `1W5200` | — | `G3616` | `oil cooler` |
| `G3616 3508 3512 3516 spring 1W1748` | `1W1748` | — | `G3616` | `spring` |
| `C9.3 intake exhaust valve` | — | — | `C9.3` | `intake exhaust valve` |

- 带连字符件号（`175-6344`）优先作主件号；没有时首个「数字+字母+数字」件号升为主件号。
- `G3616` / `G3508` / `G3512` / `G3516` 等 G 系列、以及 `3508` 这类裸机型数字，都判为机型而非件号。

## 硬性规则

- **源库只读**：除新增这份 md 外，不修改图库内任何原图或原文件。
- **不编造商业数据**：零件号、价格、重量、HS 等要么检索得到，要么用显式默认值；件号绝不臆造，找不到就留空。
- **幂等**：已存在 md 跳过，重跑不产生重复文件。
- **西语名必填**：写回前补齐，否则会被校验关卡拦截。

## License

MIT
