import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Ammo.csv"
DEFAULTS_PATH = BASE_DIR / "bullet_defaults.json"
OUTPUT_DIR = BASE_DIR / "json_output"


def sanitize_filename(name):
    """Sanitize ammo names for stable JSON filenames."""
    return (
        name.replace("*", "x")
        .replace("/", "_")
        .replace(" ", "_")
        .replace("Winchester", "Win")
        .replace("Magnum", "Mag")
        .replace("SOCOM", "SOC")
        .replace("Government", "Gov")
        .replace("Fury", "")
        .replace("__", "_")
        .strip("_")
    )


def process_range_value(value):
    """Normalize range values, mapping inf to TACZ's infinite marker."""
    cleaned = value.strip()
    if cleaned.lower() == "inf":
        return "infinite"
    try:
        return int(cleaned)
    except ValueError:
        return cleaned


def load_defaults():
    with DEFAULTS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_default_key(gun_type, ammo_name):
    if gun_type == "ShotGun":
        lowered = ammo_name.lower()
        if "slug" in lowered:
            return "ShotGun_Slug"
        else:
            return "ShotGun"
    return gun_type


def build_damage_adjust(ranges, damages):
    return [
        {"distance": ranges[index], "damage": damages[index]}
        for index in range(len(damages))
    ]


def build_bullet_template(defaults, speed, life, damages, damage_adjust, armor_ignore):
    return {
        "life": life,
        "bullet_amount": defaults["bullet_amount"],
        "damage": damages[0],
        "tracer_count_interval": defaults["tracer_count_interval"],
        "speed": speed,
        "gravity": defaults["gravity"],
        "knockback": defaults["knockback"],
        "friction": defaults["friction"],
        "ignite_entity_time": defaults["ignite_entity_time"],
        "pierce": defaults["pierce"],
        "extra_damage": {
            "armor_ignore": armor_ignore,
            "head_shot_multiplier": defaults["head_shot_multiplier"],
            "damage_adjust": damage_adjust,
        },
    }


def main():
    defaults_map = load_defaults()
    OUTPUT_DIR.mkdir(exist_ok=True)

    current_gun = None
    current_range = None
    file_count = 0

    with CSV_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            if not any(cell.strip() for cell in row):
                continue

            if len(row) < 9:
                row += [""] * (9 - len(row))

            gun = row[0].strip()
            ammo = row[1].strip()

            if gun:
                current_gun = gun

            if ammo == "Range(m)":
                range_values = [row[4].strip(), row[5].strip(), row[6].strip(), row[7].strip()]
                current_range = [process_range_value(value) for value in range_values]
                continue

            if not ammo or not current_gun or not current_range:
                continue

            try:
                speed = float(row[2].strip())
                life = float(row[3].strip())
                damages = [
                    float(row[4].strip()),
                    float(row[5].strip()),
                    float(row[6].strip()),
                    float(row[7].strip()),
                ]
                armor_ignore = float(row[8].strip())
            except ValueError:
                continue

            default_key = get_default_key(current_gun, ammo)
            if default_key not in defaults_map:
                raise KeyError(f"Missing bullet defaults for gun type: {default_key}")

            defaults = defaults_map[default_key]
            bullet_amount = int(float(row[9].strip())) if len(row) > 9 and row[9].strip() else defaults["bullet_amount"]
            tracer_count_interval = int(float(row[10].strip())) if len(row) > 10 and row[10].strip() else defaults["tracer_count_interval"]
            gravity = float(row[11].strip()) if len(row) > 11 and row[11].strip() else defaults["gravity"]
            knockback = float(row[12].strip()) if len(row) > 12 and row[12].strip() else defaults["knockback"]
            friction = float(row[13].strip()) if len(row) > 13 and row[13].strip() else defaults["friction"]
            ignite_entity_time = int(float(row[14].strip())) if len(row) > 14 and row[14].strip() else defaults["ignite_entity_time"]
            pierce = int(float(row[15].strip())) if len(row) > 15 and row[15].strip() else defaults["pierce"]
            head_shot_multiplier = float(row[16].strip()) if len(row) > 16 and row[16].strip() else defaults["head_shot_multiplier"]

            damage_adjust = build_damage_adjust(current_range, damages)
            bullet_template = {
                "life": life,
                "bullet_amount": bullet_amount,
                "damage": damages[0],
                "tracer_count_interval": tracer_count_interval,
                "speed": speed,
                "gravity": gravity,
                "knockback": knockback,
                "friction": friction,
                "ignite_entity_time": ignite_entity_time,
                "pierce": pierce,
                "extra_damage": {
                    "armor_ignore": armor_ignore,
                    "head_shot_multiplier": head_shot_multiplier,
                    "damage_adjust": damage_adjust,
                },
            }

            filename = f"{current_gun}_{sanitize_filename(ammo)}.json"
            output_path = OUTPUT_DIR / filename
            with output_path.open("w", encoding="utf-8") as output_file:
                json.dump({"bullet": bullet_template}, output_file, indent=2, ensure_ascii=False)
                output_file.write("\n")

            file_count += 1

    print(f"转换完成！共生成 {file_count} 个 JSON 文件到 {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
