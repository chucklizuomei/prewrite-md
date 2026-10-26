#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_product_md.py — 预写 md 的确定性生成器（prewrite-md 技能配套脚本）。

给定产品文件夹（及可选 --meta JSON 元数据），按固定 schema 生成标准化的
产品描述 markdown 并写回文件夹。无外部依赖，可直接执行。

用法:
  python gen_product_md.py <folder> [--meta meta.json] [--dry]
  python gen_product_md.py "/path/to/C9.3 intake exhaust valve" --meta meta.json

meta.json 可覆盖字段（均为可选）:
  {
    "part_nos": ["490-1729"],
    "cross_refs": ["490-1728"],
    "en_name": "Intake and Exhaust Valve",
    "es_name": "Válvula de admisión y escape",
    "model": "C9.3",
    "applications": ["Caterpillar C9.3 Engine"],
    "selling_points": "OEM quality; precise fit.",
    "hs_code": "8409.99",
    "title": "C9.3 Intake and Exhaust Valve 490-1729 for Caterpillar Diesel Engine"
  }
"""
import os
import re
import sys
import json
import argparse


def slugify(name):
    s = re.sub(r"[^\w]+", "-", name.strip(), flags=re.UNICODE).strip("-").lower()
    return s or "part"


# 带连字符/下划线的件号：175-6344 / 490-1729 / 255_8665
DASH_PN_RE = re.compile(r"\b\d{2,4}[-_]\d{2,4}\b")
# 纯字母+数字件号：490-1729 之外的 1W1748 / 7C2424 / 1W5200 / 490B1234
ALNUM_PN_RE = re.compile(r"\b(?:\d{1,2}[A-Za-z]\d{3,}|[A-Za-z]\d{3,})\b")
# 发动机型号：C9.3 / G3616 / G3508 / C15
MODEL_RE = re.compile(r"\b([A-Za-z]\d[\d.A-Za-z]*)\b")
# G 系列（G3616/G3508/G3512/G3516）是机型，不是件号
G_SERIES_RE = re.compile(r"(?i)^g\d{3,4}$")


def parse_folder(folder_name):
    """从文件夹名尽力解析 零件号（主件号+交叉件）/ 型号 / 品名。

    卡特件号常见三种形态：175-6344（带连字符）、7C2424 / 1W1753（数字+字母+数字）、
    G3616（G 系列机型，必须排除，不能当件号）。
    """
    dash_pns = DASH_PN_RE.findall(folder_name)

    # 型号取第一个非件号的「字母+数字」token
    model = ""
    for m in MODEL_RE.finditer(folder_name):
        tok = m.group(1)
        if G_SERIES_RE.match(tok) or tok not in dash_pns:
            model = tok
            break

    # 主件号优先取带连字符的；没有带连字符件号时，把首个字母数字件号升为主件号
    part_nos = list(dash_pns)
    cross = []
    for m in ALNUM_PN_RE.finditer(folder_name):
        tok = m.group(0).upper()
        if tok == model.upper() or G_SERIES_RE.match(tok):
            continue
        if tok not in [p.upper() for p in part_nos]:
            cross.append(tok)
    strip_tokens = list(part_nos) + list(cross)  # 清洗品名用，promotion 前先记下
    if not part_nos and cross:
        part_nos.append(cross.pop(0))

    # 清洗品名：剔除件号、型号、残留纯数字（多为机型号如 3508/3512）
    name = folder_name
    for tok in strip_tokens + ([model] if model else []):
        name = re.sub(r"\b" + re.escape(tok) + r"\b", " ", name, flags=re.I)
    name = re.sub(r"\b\d{2,}\b", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -_")
    return {"part_nos": part_nos, "cross_refs": cross, "model": model, "name": name or "Part"}


ES_DICT = {
    "piston": "pistón", "ring": "anillo", "liner": "camisa", "cylinder": "cilindro",
    "injector": "inyector", "pump": "bomba", "turbo": "turbo", "valve": "válvula",
    "guide": "guía", "seat": "asiento", "plate": "placa", "kit": "kit",
    "crankshaft": "cigüeñal", "gasket": "junta", "filter": "filtro", "belt": "correa",
    "intake": "admisión", "exhaust": "escape", "fuel": "combustible", "engine": "motor",
    "head": "culata", "block": "bloque", "sensor": "sensor", "switch": "interruptor",
}


def translate_es(en_name):
    toks = re.split(r"[^a-z0-9]+", en_name.lower())
    return " ".join(ES_DICT.get(t, t) for t in toks if t)


def title_phrase(name):
    small = {"and", "with", "for", "of", "the", "a", "an", "to", "in", "on"}
    out = []
    for i, w in enumerate(name.split()):
        if i == 0:
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(w if w.lower() in small else (w[:1].upper() + w[1:]))
    return " ".join(out)


def build_md(meta):
    part_nos = meta.get("part_nos") or []
    main_pn = part_nos[0] if part_nos else ""
    cross = meta.get("cross_refs") or []
    model = meta.get("model") or ""
    name = meta.get("en_name") or meta.get("name") or "Part"

    es = meta.get("es_name") or translate_es(name)
    apps = meta.get("applications") or []
    apps_str = "、".join(apps) if apps else "Diesel Engine"
    spec_parts = []
    if main_pn:
        spec_parts.append(main_pn)
    if cross:
        spec_parts.append("交叉件号：" + "、".join(cross))
    spec = "；".join(spec_parts)
    sp = meta.get("selling_points") or f"High quality {name} for {model or 'engine'}.".strip()
    heading = " ".join(p for p in [main_pn, name] if p).strip()
    other = apps[0] if apps else "Diesel Engine"
    brand = "Caterpillar"
    if other.lower().startswith(brand.lower()):
        brand = ""
    title_parts = [model, name, main_pn, "for", brand, other]
    title = meta.get("title") or " ".join(p for p in title_parts if p).strip()
    hs = meta.get("hs_code") or "8409.99"

    lines = [
        f"# {heading}",
        "",
        "## 表格信息",
        "",
        "| 字段 | 内容 |",
        "| --- | --- |",
        f"| 标题 | {title} |",
        f"| 类型 Type | {title_phrase(name)} |",
        f"| 发动机型号 | {model} |",
        f"| 商品规格/型号 | {spec} |",
        f"| 西班牙文品名 | {es} |",
        f"| 美国HS编码 | {hs} |",
        f"| 商品卖点 | {sp} |",
        "",
        f"**适用机型**：{apps_str}",
        "",
        "## 产品描述（英文）",
        "",
        sp,
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="预写产品描述 md 的确定性生成器")
    ap.add_argument("folder", help="产品文件夹路径")
    ap.add_argument("--meta", help="可选 JSON 元数据，覆盖解析结果")
    ap.add_argument("--dry", action="store_true", help="只打印不写文件")
    args = ap.parse_args()

    folder = args.folder
    folder_name = os.path.basename(os.path.normpath(folder))
    meta = parse_folder(folder_name)
    if args.meta and os.path.exists(args.meta):
        try:
            meta.update(json.load(open(args.meta, encoding="utf-8")))
        except Exception as e:
            print(f"[warn] 读取 meta 失败: {e}", file=sys.stderr)
    if not meta.get("name"):
        meta["name"] = folder_name

    text = build_md(meta)

    part = (meta.get("part_nos") or [""])[0]
    slu = slugify(folder_name)
    fname = f"产品描述_{part}_{slu}.md" if part else f"产品描述_{slu}.md"
    out_path = os.path.join(folder, fname)

    if args.dry:
        print(text)
        print(f"\n[dry] 将写入: {out_path}")
        return

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"已生成 md -> {out_path}")


if __name__ == "__main__":
    main()
