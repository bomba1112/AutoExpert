"""Synthetic table cases protect against assigning a neighbouring trim's aggregate."""

import pytest
from app.services.factory_tables import columns, common_facts, matched_columns

TABLE = b"""<table class="specifications-table">
<tr class="specifications-table__header"><th></th><th>Base</th><th>Plus</th><th>Sport</th></tr>
<tr><td colspan="4">Engine</td></tr>
<tr><td>Type</td><td colspan="2">2.5 GDI</td><td>2.5 Turbo GDI</td></tr>
<tr><td>Displacement (cc)</td><td colspan="3">2,497</td></tr>
<tr><td colspan="4">8-speed Automatic Transmission</td></tr>
<tr><td>First</td><td colspan="2">4.8</td><td>-</td></tr>
<tr><td colspan="4">8-speed Dual Clutch Transmission</td></tr>
<tr><td>First</td><td colspan="2">-</td><td>3.4</td></tr>
</table>"""


def catalog(aspiration=None):
    facts = {"engine_displacement": {"value": "2.5"}}
    if aspiration:
        facts["aspiration"] = {"value": aspiration}
    return {"facts": facts}


def test_colspan_is_expanded_without_shifting_trim_columns():
    matches = matched_columns(catalog("NATURALLY_ASPIRATED"), columns(TABLE))
    assert [m["trim"] for m in matches] == ["Base", "Plus"]
    assert common_facts(matches) == {
        "engine_description": "2.5 GDI",
        "transmission_description": "8-speed Automatic Transmission",
    }
    turbo = common_facts(matched_columns(catalog("TURBO"), columns(TABLE)))
    assert turbo["transmission_description"] == "8-speed Dual Clutch Transmission"


def test_ambiguous_same_displacement_does_not_invent_engine_transmission_pair():
    assert common_facts(matched_columns(catalog(), columns(TABLE))) == {}


def test_electric_configuration_is_not_matched_to_ice_columns():
    assert not matched_columns({"facts": {"powertrain": {"value": "BEV"}}}, columns(TABLE))


def test_changed_table_shape_fails_closed():
    with pytest.raises(ValueError, match="COLUMN_DRIFT"):
        columns(TABLE.replace(b'colspan="2">2.5 GDI', b'colspan="1">2.5 GDI'))
