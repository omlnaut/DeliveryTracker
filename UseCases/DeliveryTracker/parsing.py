from dataclasses import dataclass
from datetime import datetime
import re

from bs4 import BeautifulSoup

# German month names mapping
GERMAN_MONTHS: dict[str, int] = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


@dataclass
class EmailData:
    """Class to represent the parsed email data."""

    tracking_number: str | None
    pickup_location: str
    due_date: str | None
    preview: str


def parse_dhl_pickup_email_html(html_content: str) -> EmailData:
    """

    Parse the HTML content of a DHL pickup email to extract relevant information.

    Args:
        html_content (str): The HTML content of the email

    Returns:
        dict: Dictionary containing parsed information (tracking_number, pickup_location, due_date)
    """
    # Parse HTML content
    soup = BeautifulSoup(html_content, "html.parser")
    text_content = soup.get_text()

    # Extract tracking number (format: JJD000390016984620494)
    tracking_match = re.search(r"Tracking-Nummer lautet:\s*([A-Z0-9]+)", text_content)
    tracking_number = str(tracking_match.group(1)) if tracking_match else None

    # Extract pickup location
    # First find the ABHOLORT section
    location_text = find_adress(soup)

    # Extract due date
    due_date_match = re.search(
        r"ABHOLUNG BIS ZUM\s*\n\s*([^,\n]+),\s*(\d+\.\s*([^\n]+))",
        text_content,
    )
    due_date = None
    if due_date_match:
        day_str = due_date_match.group(2).strip()  # e.g., "30. November"
        try:
            # Parse the German date manually
            day = int(re.search(r"(\d+)\.", day_str).group(1))  # type: ignore
            month_name = (
                re.search(r"\d+\.\s*(\w+)", day_str).group(1).strip()  # type: ignore
            )
            month = GERMAN_MONTHS.get(month_name)

            if month:
                # Set the year (assuming next occurrence if month is in the past)
                current_date = datetime.now()
                year = current_date.year

                # Create date object
                date_obj = datetime(year, month, day)

                # If the date is in the past, use next year
                if date_obj < current_date:
                    date_obj = date_obj.replace(year=year + 1)

                # Format as DD.MM.YYYY
                due_date = date_obj.strftime("%d.%m.%Y")
        except (ValueError, AttributeError):
            due_date = None

    preview = find_preview(soup)

    return EmailData(
        tracking_number=tracking_number,
        pickup_location=location_text,
        due_date=due_date,
        preview=preview,
    )


def find_adress(soup: BeautifulSoup) -> str:
    """
    Extract the address from DHL notification email HTML.
    Returns formatted address like "Packstation 158, Südhöhe 38"
    """
    # Find the span containing "ABHOLORT"
    abholort_span = soup.find("span", string=re.compile(r"ABHOLORT"))
    if not abholort_span:
        return "Address not found"

    # Navigate to the tr that contains the address information
    abholort_tr = abholort_span.find_parent("tr")
    if not abholort_tr:
        return "Address not found"

    # The location name is in the 2nd tr after the header
    location_tr = abholort_tr.find_next_sibling("tr").find_next_sibling("tr")  # type: ignore
    if not location_tr:
        return "Address not found"

    # The street address is in the next tr
    address_tr = location_tr.find_next_sibling("tr")
    if not address_tr:
        return "Address not found"

    # Extract the text and clean it
    location_text = location_tr.get_text(strip=True)
    address_text = address_tr.get_text(strip=True)

    # Format the complete address
    full_address = f"{location_text}, {address_text}"

    return full_address


def find_preview(soup: BeautifulSoup) -> str:

    # Step 1: Find the <span> that contains the text "ARTIKEL"
    artikel_span = soup.find(
        "span", class_="rio_15_grey", string=re.compile(r"\bARTIKEL\b")
    )
    if not artikel_span:
        return "Unknown item"

    # Step 2: Get the parent <tr> that holds this <span>
    artikel_tr = artikel_span.find_parent("tr")
    if not artikel_tr:
        return "Unknown item"

    # Step 3: Get the next <tr> sibling
    next_tr = artikel_tr.find_next_sibling("tr")
    if not next_tr:
        return "Unknown item"

    # Step 4: Extract the text you want.
    # If you want the entire row's text, preserving &reg;:
    item_html = next_tr.decode_contents(formatter="html").strip()  # type: ignore

    # OPTIONAL: If you only want a specific <span> inside the next <tr>
    # that might hold the item name, e.g. <span class="rio_15_heavy_black"> Reorda&reg; Metallband...</span>:
    item_span = next_tr.find("span", class_="rio_15_heavy_black")  # type: ignore
    if item_span:
        # decode_contents(formatter="html") preserves &reg; instead of converting it to ®
        item_text = item_span.decode_contents(formatter="html").strip()  # type: ignore
        return item_text

    return "Unknown item"
