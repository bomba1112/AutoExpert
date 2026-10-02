"""Heterogeneous factory-table guards for the batch facts already in the catalogue."""

import pytest
from app.services.factory_bulk_tables import common_table_facts, parse_factory_table


def table(body):
    return (
        '<table class="specifications-table">'
        '<tr class="specifications-table__header"><th></th><th>Base</th><th>Sport</th></tr>'
        + body
        + "</table>"
    ).encode()


def test_colspan_rowspan_and_multiple_factory_fields_are_processed_together():
    result = parse_factory_table(
        table(
            '<tr><td colspan="3">Exterior Dimensions</td></tr>'
            '<tr><td>Length (in.)</td><td rowspan="2">172.6 in.</td>'
            '<td rowspan="2">172.6 in.</td></tr>'
            "<tr><td>Width (in.)</td></tr>"
            '<tr><td>Wheelbase (in.)</td><td colspan="2">101.6 in.</td></tr>'
            '<tr><td colspan="3">Interior Dimensions</td></tr>'
            '<tr><td>Seating capacity</td><td colspan="2">5 passenger</td></tr>'
        )
    )
    assert result.trims == ("Base", "Sport")
    facts, quarantine = common_table_facts(result)
    assert facts["length_in"]["value"] == 172.6
    assert facts["wheelbase_in"]["value"] == 101.6
    assert facts["seats"]["value"] == 5
    assert "width_in" not in facts  # Rowspan text is not a second width measurement.
    assert any(e["field"] == "width_in" for e in quarantine)


@pytest.mark.parametrize(
    ("cells", "reason"),
    [
        ("<td>5 passenger</td><td>7 passenger</td>", "MISSING_DIFFERENT_OR_CONDITIONAL_COLUMN"),
        (
            "<td>5 / 7 passenger (available)</td><td>7 passenger</td>",
            "MISSING_DIFFERENT_OR_CONDITIONAL_COLUMN",
        ),
        ("<td>5 passenger<sup>1</sup></td><td>5 passenger</td>", "QUALIFIED_ROW"),
        ("<td>5 passenger</td><td></td>", "MISSING_DIFFERENT_OR_CONDITIONAL_COLUMN"),
    ],
)
def test_option_and_missing_seating_are_not_universal(cells, reason):
    facts, quarantine = common_table_facts(
        parse_factory_table(
            table(
                '<tr><td colspan="3">Interior Dimensions</td></tr>'
                f"<tr><td>Seating capacity</td>{cells}</tr>"
            )
        )
    )
    assert "seats" not in facts
    assert quarantine[0]["reason"] == reason


def test_unconditional_aki_minimum_is_preserved_but_not_invented_from_regular():
    facts, _ = common_table_facts(
        parse_factory_table(
            table(
                '<tr><td colspan="3">Engine</td></tr>'
                '<tr><td>Fuel Requirement</td>'
                '<td colspan="2">Regular unleaded (87 Octane or higher)</td></tr>'
            )
        )
    )
    assert facts["octane_aki"]["value"] == 87
    assert facts["octane_aki"]["unit"] == "AKI minimum"
    unknown, _ = common_table_facts(
        parse_factory_table(
            table(
                '<tr><td colspan="3">Engine</td></tr>'
                '<tr><td>Fuel Requirement</td><td colspan="2">Regular Unleaded</td></tr>'
            )
        )
    )
    assert "octane_aki" not in unknown


def test_qualified_drive_dimensions_and_uncertain_service_capacity_stay_out():
    facts, quarantine = common_table_facts(
        parse_factory_table(
            table(
                '<tr><td colspan="3">Exterior Dimensions</td></tr>'
                '<tr><td>Height (in.), FWD / AWD</td><td colspan="2">64.4 / 64.8 in.</td></tr>'
                "<tr><td>Length (in.)</td><td>182.7 in. (est.)</td><td>182.7 in.</td></tr>"
                '<tr><td colspan="3">Engine</td></tr>'
                '<tr><td>Engine Oil Capacity (liters)</td><td colspan="2">4.8 liters</td></tr>'
                "<tr><td>Fuel tank capacity (gal.)</td><td>14.8 gal.</td><td>15.8 gal.</td></tr>"
            )
        )
    )
    assert not facts
    assert {e["field"] for e in quarantine} == {"length_in", "fuel_tank_us_gal"}


def test_duplicate_conflicting_row_is_quarantined():
    facts, quarantine = common_table_facts(
        parse_factory_table(
            table(
                '<tr><td colspan="3">Exterior Dimensions</td></tr>'
                '<tr><td>Width (in.)</td><td colspan="2">70.1 in.</td></tr>'
                '<tr><td>Width (in.)</td><td colspan="2">70.9 in.</td></tr>'
            )
        )
    )
    assert "width_in" not in facts
    assert any(e["reason"] == "CONFLICTING_DUPLICATE_ROW" for e in quarantine)


def test_malformed_column_and_unresolved_rowspan_fail_closed():
    with pytest.raises(ValueError, match="COLUMN_DRIFT"):
        parse_factory_table(
            table(
                '<tr><td colspan="3">Engine</td></tr>'
                "<tr><td>Fuel tank capacity (gal.)</td><td>11.9 gal.</td></tr>"
            )
        )
    with pytest.raises(ValueError, match="DANGLING_ROWSPAN"):
        parse_factory_table(
            table(
                '<tr><td colspan="3">Engine</td></tr>'
                '<tr><td rowspan="2">Fuel tank capacity (gal.)</td>'
                "<td>11.9 gal.</td><td>11.9 gal.</td></tr>"
            )
        )
