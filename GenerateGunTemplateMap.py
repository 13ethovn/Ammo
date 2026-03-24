import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
GUNS_DIR = WORKSPACE_DIR / "data" / "tacz" / "data" / "guns"
INDEX_GUNS_DIR = WORKSPACE_DIR / "data" / "tacz" / "index" / "guns"
AMMO_CSV_PATH = BASE_DIR / "Ammo.csv"
AMMO_MAP_PATH = BASE_DIR / "tacz_default_ammo_map.csv"
TEMPLATE_DIR = BASE_DIR / "json_output"
OUTPUT_MAP_PATH = BASE_DIR / "tacz_default_gun_template_map_draft.csv"

FIELDNAMES = [
    "gun_id",
    "tacz_type",
    "tacz_ammo",
    "ammo_csv_name",
    "template_gun_class",
    "template_json",
    "status",
    "preserve_extra_bullet_fields",
    "notes",
]

STANDARD_BULLET_KEYS = {
    "life",
    "bullet_amount",
    "damage",
    "tracer_count_interval",
    "speed",
    "gravity",
    "knockback",
    "friction",
    "ignite_entity_time",
    "pierce",
    "extra_damage",
}


def sanitize_filename(name):
    return (
        name.replace("*", "x")
        .replace("/", "_")
        .replace(" ", "_")
        .replace("Winchester", "Win")
        .replace("Magnum", "Mag")
        .replace("SOCOM", "SOC")
        .replace("Government", "Gov")
        .replace("Goverment", "Gov")
        .replace("Fury", "")
        .replace("__", "_")
        .strip("_")
    )


def load_csv_rows(path):
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                return list(csv.DictReader(file))
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Unable to decode CSV file: {path}")


def load_existing_map():
    rows = load_csv_rows(OUTPUT_MAP_PATH)
    return {(row.get("gun_id") or "").strip(): row for row in rows if (row.get("gun_id") or "").strip()}


def load_ammo_csv_index():
    indexed = set()
    current_gun_class = None
    for row in load_csv_rows(AMMO_CSV_PATH):
        gun_class = (row.get("Gun") or "").strip()
        ammo_name = (row.get("Ammo") or "").strip()
        if gun_class:
            current_gun_class = gun_class
        if ammo_name and ammo_name != "Range(m)" and current_gun_class:
            indexed.add((current_gun_class, ammo_name))
    return indexed


def load_ammo_map():
    ammo_map = {}
    for row in load_csv_rows(AMMO_MAP_PATH):
        tacz_ammo_id = (row.get("tacz_ammo_id") or "").strip()
        candidates = [item.strip() for item in ((row.get("ammo_csv_candidates") or "").split("|")) if item.strip()]
        ammo_map[tacz_ammo_id] = candidates
    return ammo_map


def load_gun_types():
    type_map = {}
    for path in INDEX_GUNS_DIR.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        marker = '"type": "'
        if marker in text:
            type_map[path.stem] = text.split(marker, 1)[1].split('"', 1)[0]
    return type_map


def resolve_tacz_ammo_id(full_ammo_name):
    return full_ammo_name.split(":", 1)[1] if ":" in full_ammo_name else full_ammo_name


def template_exists(template_gun_class, ammo_name):
    template_name = f"{template_gun_class}_{sanitize_filename(ammo_name)}.json"
    return template_name if (TEMPLATE_DIR / template_name).exists() else ""


def has_extra_bullet_fields(gun_json):
    bullet = gun_json.get("bullet", {})
    bullet_keys = set(bullet.keys())
    return bullet_keys - STANDARD_BULLET_KEYS


def choose_sniper_mapping(gun_id, ammo_candidates, ammo_csv_index):
    if gun_id == "ai_awp" and ("SPR", ".338 Lap Mag") in ammo_csv_index:
        template_name = template_exists("SPR", ".338 Lap Mag")
        if template_name:
            return ".338 Lap Mag", "SPR", template_name, "auto", "AWM 使用 .338 Lap Mag；按 sniper -> SPR 自动确定"

    if len(ammo_candidates) == 1:
        ammo_name = ammo_candidates[0]
        if ("SPR", ammo_name) in ammo_csv_index:
            template_name = template_exists("SPR", ammo_name)
            if template_name:
                return ammo_name, "SPR", template_name, "auto", "按 sniper -> SPR 自动确定"
    return "", "SPR", "", "manual", "sniper 暂保留为手动；可后续复核"


def choose_rifle_mapping(ammo_candidates, ammo_csv_index):
    if len(ammo_candidates) != 1:
        return "", "", "", "manual", "rifle 弹种存在歧义，暂不自动映射"

    ammo_name = ammo_candidates[0]
    if ("AR", ammo_name) in ammo_csv_index:
        template_name = template_exists("AR", ammo_name)
        if template_name:
            return ammo_name, "AR", template_name, "auto", "按 rifle 优先匹配到 AR 中已有弹种自动判定"

    for fallback_class in ("BR", "EBR", "DMR", "SPR"):
        if (fallback_class, ammo_name) in ammo_csv_index:
            return "", fallback_class, "", "manual", f"rifle 未命中 AR，建议后续人工判断为 {fallback_class}"

    return "", "", "", "manual", "rifle 暂无可用模板候选"


def choose_mapping(gun_id, tacz_type, tacz_ammo_id, ammo_candidates, ammo_csv_index):
    if tacz_type == "pistol" and len(ammo_candidates) == 1:
        ammo_name = ammo_candidates[0]
        if ("Pistol", ammo_name) in ammo_csv_index:
            template_name = template_exists("Pistol", ammo_name)
            if template_name:
                return ammo_name, "Pistol", template_name, "auto", "可由 type + ammo 自动确定"

    if tacz_type == "smg" and len(ammo_candidates) == 1:
        ammo_name = ammo_candidates[0]
        if ("SMG", ammo_name) in ammo_csv_index:
            template_name = template_exists("SMG", ammo_name)
            if template_name:
                return ammo_name, "SMG", template_name, "auto", "可由 type + ammo 自动确定"

    if tacz_type == "shotgun":
        ammo_name = "12g"
        if ("ShotGun", ammo_name) in ammo_csv_index:
            template_name = template_exists("ShotGun", ammo_name)
            if template_name:
                return ammo_name, "ShotGun", template_name, "auto", "shotgun 先统一按 12g 模板自动确定"
        return "", "ShotGun", "", "manual", "shotgun 当前未找到 12g 模板"

    if tacz_type == "rifle":
        return choose_rifle_mapping(ammo_candidates, ammo_csv_index)

    if tacz_type == "sniper":
        return choose_sniper_mapping(gun_id, ammo_candidates, ammo_csv_index)

    if tacz_type == "mg":
        ammo_name = ammo_candidates[0] if len(ammo_candidates) == 1 else ""
        return ammo_name if ("LMG", ammo_name) in ammo_csv_index else "", "LMG", "", "manual", "MG 暂不自动映射"

    if tacz_type == "rpg":
        return "", "", "", "skip", "当前 Ammo.csv 未包含爆炸投射物模板"

    return "", "", "", "manual", "未命中自动规则"


def fill_from_manual_template_class(
    manual_template_gun_class, tacz_ammo_id, ammo_candidates, ammo_csv_index
):
    if not manual_template_gun_class:
        return "", ""

    if manual_template_gun_class == "ShotGun" and tacz_ammo_id == "12g":
        ammo_name = "12g"
        if (manual_template_gun_class, ammo_name) in ammo_csv_index:
            return ammo_name, template_exists(manual_template_gun_class, ammo_name)
        return "", ""

    if len(ammo_candidates) != 1:
        return "", ""

    ammo_name = ammo_candidates[0]
    if (manual_template_gun_class, ammo_name) not in ammo_csv_index:
        return "", ""

    return ammo_name, template_exists(manual_template_gun_class, ammo_name)


def main():
    existing_map = load_existing_map()
    ammo_csv_index = load_ammo_csv_index()
    ammo_map = load_ammo_map()
    type_map = load_gun_types()

    rows = []
    for gun_path in sorted(GUNS_DIR.glob("*_data.json")):
        gun_id = gun_path.stem.replace("_data", "")
        gun_json = json.loads(gun_path.read_text(encoding="utf-8"))
        tacz_type = type_map.get(gun_id, "")
        tacz_ammo = (gun_json.get("ammo") or "").strip()
        tacz_ammo_id = resolve_tacz_ammo_id(tacz_ammo)
        ammo_candidates = ammo_map.get(tacz_ammo_id, [])

        ammo_name, template_gun_class, template_json, status, notes = choose_mapping(
            gun_id, tacz_type, tacz_ammo_id, ammo_candidates, ammo_csv_index
        )

        existing = existing_map.get(gun_id, {})
        existing_template_gun_class = (existing.get("template_gun_class") or "").strip()
        if existing_template_gun_class:
            template_gun_class = existing_template_gun_class
            notes = (existing.get("notes") or "").strip() or notes

            existing_ammo_name = (existing.get("ammo_csv_name") or "").strip()
            existing_template_json = (existing.get("template_json") or "").strip()

            if existing_ammo_name:
                ammo_name = existing_ammo_name
            if existing_template_json:
                template_json = existing_template_json

            inferred_ammo_name, inferred_template_json = fill_from_manual_template_class(
                template_gun_class, tacz_ammo_id, ammo_candidates, ammo_csv_index
            )

            if not ammo_name and inferred_ammo_name:
                ammo_name = inferred_ammo_name
            if not template_json and inferred_template_json:
                template_json = inferred_template_json

            status = "auto" if template_json else "manual"

        preserve_extra = "yes" if has_extra_bullet_fields(gun_json) else "no"

        rows.append(
            {
                "gun_id": gun_id,
                "tacz_type": tacz_type,
                "tacz_ammo": tacz_ammo,
                "ammo_csv_name": ammo_name,
                "template_gun_class": template_gun_class,
                "template_json": template_json,
                "status": status,
                "preserve_extra_bullet_fields": preserve_extra,
                "notes": notes,
            }
        )

    with OUTPUT_MAP_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    auto_count = sum(1 for row in rows if row["status"] == "auto")
    manual_count = sum(1 for row in rows if row["status"] == "manual")
    skip_count = sum(1 for row in rows if row["status"] == "skip")
    print(f"生成完成：auto {auto_count}，manual {manual_count}，skip {skip_count}。输出：{OUTPUT_MAP_PATH}")


if __name__ == "__main__":
    main()
