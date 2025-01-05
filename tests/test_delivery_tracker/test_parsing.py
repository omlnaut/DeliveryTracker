from shared.GoogleServices import GmailService
from pathlib import Path


def test_parses_correct_information_from_raw_html():
    html = open(Path(__file__).parent / "dhl_test.html", "r").read()
    parsed = GmailService._parse_dhl_pickup_email_html(html)

    assert parsed["tracking_number"] == "JJD000390016890406943"
    assert parsed["pickup_location"] == "Packstation 158, Südhöhe 38"
    assert parsed["due_date"] == "10.01.2025"
