import csv
import json
from copy import deepcopy
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
GUNS_DIR = WORKSPACE_DIR / "data" / "tacz" / "data" / "guns"
OUTPUT_DIR = BASE_DIR / "generated_guns"
MAP_PATH = BASE_DIR / "tacz_default_gun_template_map_draft.csv"
AMMO_MAP_PATH = BASE_DIR / "tacz_default_ammo_map.csv"
AMMO_CSV_PATH = BASE_DIR / "Ammo.csv"
TEMPLATE_DIR = BASE_DIR / "json_output"


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
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                return list(csv.DictReader(file))
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("csv", b"", 0, 1, f"Unable to decode CSV file: {path}")


def load_ammo_csv_index():
    indexed = set()
    current_gun_class = None

    with AMMO_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            gun_class = (row.get("Gun") or "").strip()
            ammo_name = (row.get("Ammo") or "").strip()

            if gun_class:
                current_gun_class = gun_class

            if ammo_name and ammo_name != "Range(m)" and current_gun_class:
                indexed.add((current_gun_class, ammo_name))
    return indexed


def load_ammo_map():
    rows = load_csv_rows(AMMO_MAP_PATH)
    ammo_map = {}
    for row in rows:
        tacz_ammo_id = (row.get("tacz_ammo_id") or "").strip()
        candidates_raw = (row.get("ammo_csv_candidates") or "").strip()
        candidates = [item.strip() for item in candidates_raw.split("|") if item.strip()]
        ammo_map[tacz_ammo_id] = candidates
    return ammo_map


def resolve_tacz_ammo_id(full_ammo_name):
    return full_ammo_name.split(":", 1)[1] if ":" in full_ammo_name else full_ammo_name


def infer_template_for_manual_row(row, gun_json, ammo_map, ammo_csv_index):
    template_gun_class = (row.get("template_gun_class") or "").strip()
    if not template_gun_class:
        return None, None

    tacz_ammo_full = (gun_json.get("ammo") or row.get("tacz_ammo") or "").strip()
    tacz_ammo_id = resolve_tacz_ammo_id(tacz_ammo_full)

    if template_gun_class == "ShotGun" and tacz_ammo_id == "12g":
        ammo_name = "12g"
        if (template_gun_class, ammo_name) in ammo_csv_index:
            template_name = f"{template_gun_class}_{sanitize_filename(ammo_name)}.json"
            return ammo_name, template_name
        return None, None

    candidates = ammo_map.get(tacz_ammo_id, [])
    if len(candidates) != 1:
        return None, None

    ammo_name = candidates[0]
    if (template_gun_class, ammo_name) not in ammo_csv_index:
        return None, None

    template_name = f"{template_gun_class}_{sanitize_filename(ammo_name)}.json"
    return ammo_name, template_name


def merge_bullet_preserving_extras(original_bullet, template_bullet):
    merged = deepcopy(original_bullet)
    for key, value in template_bullet.items():
        if key == "extra_damage" and isinstance(value, dict):
            merged_extra = deepcopy(merged.get("extra_damage", {}))
            merged_extra.update(deepcopy(value))
            merged["extra_damage"] = merged_extra
        else:
            merged[key] = deepcopy(value)
    return merged


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    ammo_map = load_ammo_map()
    ammo_csv_index = load_ammo_csv_index()
    mapping_rows = load_csv_rows(MAP_PATH)

    summary = {"written": 0, "inferred_manual": 0, "skipped": 0}

    for row in mapping_rows:
        gun_id = (row.get("gun_id") or "").strip()
        status = (row.get("status") or "").strip()
        preserve_extras = (row.get("preserve_extra_bullet_fields") or "").strip().lower() == "yes"
        gun_path = GUNS_DIR / f"{gun_id}_data.json"

        if not gun_path.exists():
            summary["skipped"] += 1
            continue

        with gun_path.open("r", encoding="utf-8") as file:
            gun_json = json.load(file)

        ammo_name = (row.get("ammo_csv_name") or "").strip()
        template_name = (row.get("template_json") or "").strip()

        if status != "auto":
            inferred_ammo_name, inferred_template_name = infer_template_for_manual_row(
                row, gun_json, ammo_map, ammo_csv_index
            )
            if inferred_template_name:
                ammo_name = inferred_ammo_name
                template_name = inferred_template_name
                summary["inferred_manual"] += 1
            else:
                summary["skipped"] += 1
                continue

        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            summary["skipped"] += 1
            continue

        with template_path.open("r", encoding="utf-8") as file:
            template_json = json.load(file)

        template_bullet = template_json["bullet"]
        original_bullet = gun_json.get("bullet", {})
        gun_json["bullet"] = (
            merge_bullet_preserving_extras(original_bullet, template_bullet)
            if preserve_extras
            else deepcopy(template_bullet)
        )

        output_path = OUTPUT_DIR / gun_path.name
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(gun_json, file, indent=2, ensure_ascii=False)
            file.write("\n")

        summary["written"] += 1

    print(
        "批量写入完成："
        f" 写入 {summary['written']} 个，"
        f" 非 auto 二次匹配成功 {summary['inferred_manual']} 个，"
        f" 跳过 {summary['skipped']} 个。"
    )


if __name__ == "__main__":
    main()
