# Ammo

Tools and data for managing TACZ ammo templates, generating complete `bullet`
JSON fragments from `Ammo.csv`, building gun-to-template mapping drafts, and
applying those templates to copied TACZ gun data files in a safe workspace.

## What This Project Does

This project is used to:

- maintain a single ammo master table in `Ammo.csv`
- generate reusable `bullet` templates into `json_output/`
- generate a draft mapping from TACZ default guns to ammo templates
- apply templates to copied gun data files without directly editing the live
  game pack

The working assumption is:

- `Ammo.csv` is the main source of truth for ammo balance
- template JSON files are generated outputs
- copied TACZ gun data in the workspace is used for testing and iteration

## Project Layout

- `Ammo.csv`
  Main ammo data table. This includes damage ranges and most `bullet` fields.

- `AmmoDataTrans.py`
  Reads `Ammo.csv` and generates complete `bullet` template files in
  `json_output/`.

- `json_output/`
  Generated template files. Each file represents one gun-class/ammo template,
  such as `AR_7.62x39mm.json` or `SPR_.50_BMG.json`.

- `tacz_default_ammo_map.csv`
  Mapping from TACZ default pack ammo ids to ammo names used in `Ammo.csv`.

- `GenerateGunTemplateMap.py`
  Builds or refreshes the default gun-to-template draft mapping table.

- `tacz_default_gun_template_map_draft.csv`
  Draft mapping from TACZ default guns to template files.

- `ApplyBulletTemplates.py`
  Applies generated templates to copied TACZ gun data files and writes results
  into `generated_guns/`.

- `generated_guns/`
  Output directory for processed gun data files.

## Recommended Workflow

1. Edit `Ammo.csv`
2. Run `AmmoDataTrans.py`
3. Run `GenerateGunTemplateMap.py`
4. Review and adjust `tacz_default_gun_template_map_draft.csv`
5. Run `ApplyBulletTemplates.py`
6. Inspect the results in `generated_guns/`

## Notes

- This project works on copied TACZ data inside the workspace rather than
  directly editing the live game pack.
- Some guns contain extra `bullet` fields such as `explosion`. The apply step
  preserves those fields when the mapping table marks them for preservation.
- The default gun mapping draft is intentionally only partly automatic. Manual
  review is still expected for guns whose TACZ categories are too coarse.
