from datetime import datetime, timedelta, timezone
from shared.GoogleServices import GmailQueryBuilder
from shared.GoogleServices.gmail.service import GmailService


def get_amazon_return_mails(gmail_service: GmailService, hours: int = 1) -> list[str]:
    # Calculate time threshold
    time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Build query
    query = (
        GmailQueryBuilder()
        .from_email("rueckgabe@amazon.de")
        .after_date(time_threshold)
        .subject("Ihre Rücksendung von")
        .build()
    )

    messages = gmail_service.query_messages_with_body(query)

    return messages
