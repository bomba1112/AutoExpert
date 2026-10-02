"""Source discovery must select observed annual documents, never invent links."""

from scripts.discover_us_brochures import select_documents


def test_selects_latest_observed_brochure_and_records_unavailable_years():
    html = (
        b"<p>2015 Toyota Highlander PDF Brochure "
        b'<a href="/makes/Toyota/Highlander/v1.pdf">PDF</a></p>'
        b"<p>2015 Toyota Highlander v2 PDF Brochure "
        b'<a href="/makes/Toyota/Highlander/v2.pdf">PDF</a></p>'
        b"<p>2016 Toyota Highlander PDF Brochure "
        b'<a href="/makes/Toyota/Highlander/2016.pdf">PDF</a></p>'
    )
    found, missing = select_documents(
        html,
        "https://www.auto-brochures.com/toyota.html",
        "Toyota",
        "Highlander",
        [2015, 2016, 2017],
    )
    assert [(item["year"], item["version"]) for item in found] == [(2015, 2), (2016, 1)]
    assert found[0]["url"] == "https://www.auto-brochures.com/makes/Toyota/Highlander/v2.pdf"
    assert missing == [2017]


def test_rejects_external_or_non_document_links_even_with_matching_label():
    html = b"""<p>2017 Audi Q3 PDF Brochure <a href="https://elsewhere.example/makes/Audi/Q3/2017.pdf">PDF</a></p>
    <p>2018 Audi Q3 PDF Brochure <a href="/private/Audi/Q3/2018.pdf">PDF</a></p>
    <p>2019 Audi Q3 PDF Brochure <a href="/makes/Audi/Q3/2019.pdf?download=1">PDF</a></p>"""
    found, missing = select_documents(
        html, "https://www.auto-brochures.com/audi.html", "Audi", "Q3", [2017, 2018, 2019]
    )
    assert found == []
    assert missing == [2017, 2018, 2019]
