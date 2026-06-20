#!/usr/bin/env python3
"""Deterministic checks for terraform_import resource name validation."""

import csv
import importlib.util
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "terraform_import.py"


def load_module():
    spec = importlib.util.spec_from_file_location("terraform_import", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load terraform_import.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_raises(expected_error, fn):
    try:
        fn()
    except expected_error:
        return
    raise AssertionError(f"Expected {expected_error.__name__}")


def main() -> int:
    terraform_import = load_module()

    valid = terraform_import.ResourceToImport(
        resource_type="aws_instance",
        resource_name="web_server_01",
        resource_id="i-1234567890",
    )
    invalid = terraform_import.ResourceToImport(
        resource_type="aws_instance",
        resource_name="web-server-01",
        resource_id="i-1234567890",
    )

    assert terraform_import.terraform_resource_address(valid) == "aws_instance.web_server_01"
    assert_raises(
        terraform_import.TerraformResourceNameError,
        lambda: terraform_import.terraform_resource_address(invalid),
    )

    importer = terraform_import.TerraformImporter(terraform_binary="terraform")
    dry_run = importer.import_batch([valid], dry_run=True)
    assert dry_run.skipped_count == 1
    assert dry_run.failure_count == 0
    assert dry_run.results[0]["address"] == "aws_instance.web_server_01"

    invalid_dry_run = importer.import_batch([invalid], dry_run=True)
    assert invalid_dry_run.failure_count == 1
    assert invalid_dry_run.results[0]["status"] == "invalid_name"
    assert "aws_instance" in invalid_dry_run.results[0]["error"]
    assert "web-server-01" in invalid_dry_run.results[0]["error"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        script_path = tmp_path / "import.sh"
        script = importer.generate_import_script([valid], str(script_path))
        assert "aws_instance.web_server_01" in script

        assert_raises(
            terraform_import.TerraformResourceNameError,
            lambda: importer.generate_import_script([invalid], str(script_path)),
        )

        csv_path = tmp_path / "resources.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["type", "name", "id"])
            writer.writeheader()
            writer.writerow({
                "type": "aws_instance",
                "name": "web-server-01",
                "id": "i-1234567890",
            })

        with csv_path.open("r", newline="") as f:
            row = next(csv.DictReader(f))
        csv_resource = terraform_import.ResourceToImport(
            resource_type=row["type"],
            resource_name=row["name"],
            resource_id=row["id"],
        )
        assert_raises(
            terraform_import.TerraformResourceNameError,
            lambda: terraform_import.terraform_resource_address(csv_resource),
        )

    print("terraform import resource name validation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
