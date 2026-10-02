"""A factory batch must not borrow drive evidence from another year or gearbox."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "batch_runner", Path(__file__).resolve().parents[2] / "scripts/run_base_catalog_batch.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def source_row(year, transmission="Automatic (S6)", drive="Front-Wheel Drive"):
    return dict(
        id=str(year),
        make="Fixture",
        model="Sedan",
        year=str(year),
        displ="2.0",
        trany=transmission,
        drive=drive,
        fuelType1="Regular Gasoline",
    )


def inputs():
    return (
        SimpleNamespace(
            source_id="epa",
            id="fixture-doc",
            sha256="a" * 64,
            locator="https://example.invalid/epa.zip",
        ),
        dict(make="Fixture", model="Sedan", market="US"),
        dict(
            id="fixture",
            year_from=2017,
            year_to=2018,
            allowed_drives=["FWD"],
            epa_drive_match=dict(model=["Sedan"], displ=["2.0"], trany=["Automatic (S6)"]),
        ),
    )


def test_annual_epa_drive_keeps_its_own_provenance_and_does_not_certify_gearbox():
    doc, family, group = inputs()
    refs = runner.epa_drive_references(doc, [source_row(2017), source_row(2018)], family, group)
    assert set(refs) == {(2017, "FWD"), (2018, "FWD")}
    assert all(r["registry_id"] == "epa" for r in refs.values())
    assert refs[2017, "FWD"]["model_year"] == 2017
    assert "2018" not in refs[2017, "FWD"]["locator"]
    assert "Drive evidence only" in refs[2017, "FWD"]["locator"]


@pytest.mark.parametrize(
    "replacement",
    [
        source_row(2019),
        source_row(2018, "Automatic (variable gear ratios)"),
        source_row(2018, drive="All-Wheel Drive"),
    ],
)
def test_neighboring_year_cvt_or_awd_cannot_fill_missing_factory_tuple(replacement):
    doc, family, group = inputs()
    with pytest.raises(ValueError, match="EPA_DRIVE_APPLICABILITY_GAP"):
        runner.epa_drive_references(doc, [source_row(2017), replacement], family, group)
