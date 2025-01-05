from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import base64
import re
from bs4 import BeautifulSoup

# German month names mapping
GERMAN_MONTHS = {
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


class GmailService:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API."""
        # TODO figure out the type of the service
        self.service = build(
            "gmail", "v1", credentials=self.credentials, cache_discovery=False
        )

    def get_recent_emails(self, days=2):
        """
        Fetch emails received in the last specified hours.

        Args:
            hours (int): Number of hours to look back (default: 1)

        Returns:
            list: List of dictionaries containing email details
        """
        if not self.service:
            self.authenticate()

        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(days=days)
        query = f"after:{int(time_threshold.timestamp())}"

        try:
            results = (
                self.service.users().messages().list(userId="me", q=query).execute()  # type: ignore
            )

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                msg_details = (
                    self.service.users()  # type: ignore
                    .messages()
                    .get(
                        userId="me",
                        id=message["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )

                headers = msg_details["payload"]["headers"]
                email_data = {
                    "id": message["id"],
                    "from": next(
                        (h["value"] for h in headers if h["name"] == "From"), ""
                    ),
                    "subject": next(
                        (h["value"] for h in headers if h["name"] == "Subject"), ""
                    ),
                    "date": next(
                        (h["value"] for h in headers if h["name"] == "Date"), ""
                    ),
                    "snippet": msg_details.get("snippet", ""),
                }
                emails.append(email_data)

            return emails

        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []

    @staticmethod
    def _find_preview(soup: BeautifulSoup) -> str:

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
        # If you want the entire row’s text, preserving &reg;:
        item_html = next_tr.decode_contents(formatter="html").strip()

        # OPTIONAL: If you only want a specific <span> inside the next <tr>
        # that might hold the item name, e.g. <span class="rio_15_heavy_black"> Reorda&reg; Metallband...</span>:
        item_span = next_tr.find("span", class_="rio_15_heavy_black")
        if item_span:
            # decode_contents(formatter="html") preserves &reg; instead of converting it to ®
            item_text = item_span.decode_contents(formatter="html").strip()
            return item_text

        return "Unknown item"

    @staticmethod
    def _parse_dhl_pickup_email_html(html_content: str) -> dict:
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
        tracking_match = re.search(
            r"Tracking-Nummer lautet:\s*([A-Z0-9]+)", text_content
        )
        tracking_number = tracking_match.group(1) if tracking_match else None

        # Extract pickup location
        # First find the ABHOLORT section
        location_text = ""
        abholort_match = re.search(
            r"ABHOLORT\s*\n\s*DHL\s*\n\s*(.*?)\s*Öffnungszeiten",
            text_content,
            re.DOTALL,
        )
        if abholort_match:
            # Clean up the location text and only keep Packstation and address
            location_lines = [
                line.strip()
                for line in abholort_match.group(1).split("\n")
                if line.strip()
            ]
            # Only keep Packstation and street address
            packstation = next(
                (line for line in location_lines if "Packstation" in line), ""
            )
            street = next(
                (
                    line
                    for line in location_lines
                    if any(c.isdigit() for c in line) and "Packstation" not in line
                ),
                "",
            )
            location_text = f"{packstation}, {street}" if packstation and street else ""

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

        preview = GmailService._find_preview(soup)

        return {
            "tracking_number": tracking_number,
            "pickup_location": location_text,
            "due_date": due_date,
            "preview": preview,
        }

    def get_amazon_dhl_pickup_emails(self, hours=1):
        """
        Fetch Amazon DHL pickup notification emails from the last specified days.

        Args:
            days (int): Number of days to look back (default: 2)

        Returns:
            list: List of dictionaries containing email details including pickup location,
                  due date, and tracking number
        """
        if not self.service:
            self.authenticate()

        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = (
            f"from:order-update@amazon.de "
            f'subject:"Ihr Paket kann bei DHL abgeholt werden" '
            f"after:{int(time_threshold.timestamp())}"
        )

        try:
            results = (
                self.service.users().messages().list(userId="me", q=query).execute()  # type: ignore
            )

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                # Get the full message content
                msg_details = (
                    self.service.users()  # type: ignore
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )

                headers = msg_details["payload"]["headers"]

                # Get email body
                if "parts" in msg_details["payload"]:
                    parts = msg_details["payload"]["parts"]
                    body = ""
                    for part in parts:
                        if part["mimeType"] == "text/html":
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"].encode("utf-8")
                            ).decode("utf-8")
                            break
                else:
                    body = base64.urlsafe_b64decode(
                        msg_details["payload"]["body"]["data"].encode("utf-8")
                    ).decode("utf-8")

                # Parse the email content
                parsed_data = self._parse_dhl_pickup_email_html(body)

                emails.append(parsed_data)

            return emails

        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
