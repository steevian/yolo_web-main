"""Phase 1: generate and validate data_3seasonweeddet10.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

from dataset_taxonomy import CLASS_NAMES, class_id_from_name


IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Generate and validate YOLO data yaml")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=repo_root / "datasets" / "processed_3seasonweeddet10",
    )
    parser.add_argument(
        "--output-yaml",
        type=Path,
        default=repo_root / "training" / "configs" / "data_3seasonweeddet10.yaml",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=repo_root / "experiments" / "logs" / "data_yaml_validation.md",
    )
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def count_images(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS)


def count_labels(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.glob("*.txt") if p.stat().st_size > 0)


def collect_label_ids(path: Path) -> set[int]:
    label_ids: set[int] = set()
    if not path.exists():
        return label_ids
    for label_file in path.glob("*.txt"):
        for line in label_file.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 5:
                continue
            try:
                label_ids.add(int(parts[0]))
            except ValueError:
                continue
    return label_ids


def collect_annotation_ids(path: Path) -> set[int]:
    annotation_ids: set[int] = set()
    if not path.exists():
        return annotation_ids
    for xml_file in path.glob("*.xml"):
        root = ET.parse(xml_file).getroot()
        for obj in root.findall("object"):
            class_id = class_id_from_name((obj.findtext("name") or "").strip())
            if class_id is not None:
                annotation_ids.add(class_id)
    return annotation_ids


def format_class_ids(ids: set[int]) -> str:
    if not ids:
        return "none"
    return ", ".join(f"{idx}:{CLASS_NAMES[idx]}" for idx in sorted(ids))


def validate_dataset(ds_root: Path) -> tuple[bool, list[str]]:
    checks: list[str] = []
    ok = True

    classes_file = ds_root / "classes.txt"
    if not classes_file.exists():
        ok = False
        checks.append("- [FAIL] classes.txt missing")
    else:
        got = [l.strip() for l in classes_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        if got != CLASS_NAMES:
            ok = False
            checks.append("- [FAIL] classes.txt order/content mismatch")
        else:
            checks.append("- [PASS] classes.txt order/content ok")

    for split in ("train", "val", "test"):
        img_dir = ds_root / "images" / split
        lbl_dir = ds_root / "labels" / split
        ann_dir = ds_root / "annotations" / split
        img_count = count_images(img_dir)
        lbl_count = count_labels(lbl_dir)
        ann_ids = collect_annotation_ids(ann_dir)
        lbl_ids = collect_label_ids(lbl_dir)

        if not img_dir.exists():
            ok = False
            checks.append(f"- [FAIL] images/{split} missing")
        else:
            checks.append(f"- [PASS] images/{split} exists ({img_count} files)")

        if not lbl_dir.exists():
            ok = False
            checks.append(f"- [FAIL] labels/{split} missing")
        else:
            checks.append(f"- [PASS] labels/{split} exists ({lbl_count} non-empty txt)")

        if img_count == 0 or lbl_count == 0:
            ok = False
            checks.append(f"- [FAIL] split {split} has zero samples")

        if ann_ids != lbl_ids:
            ok = False
            checks.append(
                f"- [FAIL] {split} annotation/label class mismatch | annotations: {format_class_ids(ann_ids)} | labels: {format_class_ids(lbl_ids)}"
            )
        else:
            checks.append(f"- [PASS] {split} annotation/label class coverage consistent: {format_class_ids(lbl_ids)}")

        missing_ids = set(range(len(CLASS_NAMES))) - ann_ids
        if missing_ids:
            checks.append(f"- [INFO] {split} source annotations missing classes: {format_class_ids(missing_ids)}")

    return ok, checks


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    ds_root = args.dataset_root.resolve()
    yaml_path = args.output_yaml.resolve()
    md_log = args.report_path.resolve()

    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    md_log.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "train": str((ds_root / "images" / "train").resolve()),
        "val": str((ds_root / "images" / "val").resolve()),
        "test": str((ds_root / "images" / "test").resolve()),
        "nc": len(CLASS_NAMES),
        "names": CLASS_NAMES,
    }

    if not args.validate_only:
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    ok, checks = validate_dataset(ds_root)

    report_lines = [
        "# data.yaml Validation",
        "",
        f"- yaml_path: `{yaml_path}`",
        f"- dataset_root: `{ds_root}`",
        f"- result: {'PASS' if ok else 'FAIL'}",
        "",
        "## Checks",
    ]
    report_lines.extend(checks)
    md_log.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("[DONE] phase1_generate_data_yaml")
    print(f"yaml: {yaml_path}")
    print(f"validation report: {md_log}")
    print(f"result: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
