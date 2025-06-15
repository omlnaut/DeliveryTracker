from UseCases.ReturnTracker.parsing import parse_return_info
from pathlib import Path


def test_return_parsing_correct_information_from_raw_html():

    html = open(Path(__file__).parent / "amazon_rueckgabe_test.html", "r").read()
    parsed = parse_return_info(html)

    assert parsed.return_date == "5. Juli 2025"
    assert parsed.order_number == "302-9238863-3187535"
    assert (
        parsed.pickup_location
        == "DHL Abgabe an Packstation – weder Verpackung noch Drucker erforderlich"
    )
    assert parsed.item_title == "IceUnicorn Krabbelschuhe Baby..."
