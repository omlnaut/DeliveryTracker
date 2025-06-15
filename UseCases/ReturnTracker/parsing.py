from dataclasses import dataclass
import re

from bs4 import BeautifulSoup


@dataclass
class ReturnInfo:
    """Class to represent the parsed return information."""

    return_date: str
    order_number: str
    pickup_location: str
    item_title: str


def _find_tr_by_text(soup, text):
    text_element = soup.find(string=text)
    if not text_element:
        return None
    return text_element.find_parent("tr")


def _extract_return_date(soup) -> str:
    """Extract return date from the HTML."""
    return_text_tr = _find_tr_by_text(soup, "Rückgabe bis:")

    if not return_text_tr:
        raise ValueError("Could not find return date in the provided HTML.")

    sep_tr = return_text_tr.find_next_sibling("tr")
    if not sep_tr:
        raise ValueError("Could not find separator row after return date.")

    return_date_tr = sep_tr.find_next_sibling("tr")

    if not return_date_tr:
        raise ValueError("Could not find return date value row.")

    return return_date_tr.text.strip()


def _extract_pickup_location(soup) -> str:
    """Extract pickup location from the HTML."""
    location_tr = _find_tr_by_text(soup, "Abgabestandort")
    if not location_tr:
        raise ValueError("Could not find pickup location label in the provided HTML.")

    next_tr = location_tr.find_next_sibling("tr")
    if not next_tr:
        raise ValueError("Could not find row after pickup location label.")

    location_value_tr = next_tr.find_next_sibling("tr")
    if not location_value_tr:
        raise ValueError("Could not find pickup location value row.")

    return location_value_tr.text.strip()


def _extract_item_title(soup) -> str:
    """Extract item title from the HTML."""
    anzahl_tr = _find_tr_by_text(soup, re.compile("""^Anzahl:"""))
    if not anzahl_tr:
        raise ValueError("Could not find 'Anzahl' row in the provided HTML.")

    prev_tr = anzahl_tr.find_previous_sibling("tr")
    if not prev_tr:
        raise ValueError("Could not find row before 'Anzahl' row.")

    title_tr = prev_tr.find_previous_sibling("tr")
    if not title_tr:
        raise ValueError("Could not find item title row.")

    return title_tr.text.strip()


def _extract_order_number(soup) -> str:
    """Extract order number from the HTML."""
    order_number_element = soup.find(string=re.compile("^Bestellnummer"))
    if not order_number_element:
        raise ValueError("Could not find order number in the provided HTML.")

    parts = order_number_element.split(" ")
    if len(parts) < 2:
        raise ValueError("Order number format is not as expected.")

    return parts[1].strip()


def parse_return_info(html: str) -> ReturnInfo:
    soup = BeautifulSoup(html, "html.parser")

    return_date = _extract_return_date(soup)
    order_number = _extract_order_number(soup)
    pickup_location = _extract_pickup_location(soup)
    item_title = _extract_item_title(soup)

    return ReturnInfo(
        return_date=return_date,
        order_number=order_number,
        pickup_location=pickup_location,
        item_title=item_title,
    )
