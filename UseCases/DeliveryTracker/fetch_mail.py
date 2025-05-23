from datetime import datetime, timedelta, timezone
from shared.GoogleServices import GmailQueryBuilder
from shared.GoogleServices.gmail.service import GmailService


def get_amazon_dhl_pickup_emails(
    gmail_service: GmailService, hours: int = 1
) -> list[str]:
    # Calculate time threshold
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Build query
    query = (
        GmailQueryBuilder()
        .from_email("order-update@amazon.de")
        .subject("Ihr Paket kann bei DHL", exact=True)
        .after_date(time_threshold)
        .build()
    )

    messages = gmail_service.query_messages_with_body(query)

    return messages
