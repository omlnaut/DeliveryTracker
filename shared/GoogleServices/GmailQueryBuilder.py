from datetime import datetime


class GmailQueryBuilder:
    """Helper class to build Gmail search queries"""

    def __init__(self):
        self._query_parts = []

    def from_email(self, email):
        """Add from: filter"""
        self._query_parts.append(f"from:{email}")
        return self

    def subject(self, text, exact=True):
        """Add subject: filter"""
        if exact:
            self._query_parts.append(f'subject:"{text}"')
        else:
            self._query_parts.append(f"subject:{text}")
        return self

    def after_date(self, date):
        """Add after: filter using Unix timestamp"""
        if isinstance(date, datetime):
            timestamp = int(date.timestamp())
        else:
            timestamp = int(date)
        self._query_parts.append(f"after:{timestamp}")
        return self

    def before_date(self, date):
        """Add before: filter using Unix timestamp"""
        if isinstance(date, datetime):
            timestamp = int(date.timestamp())
        else:
            timestamp = int(date)
        self._query_parts.append(f"before:{timestamp}")
        return self

    def has_attachment(self):
        """Add has:attachment filter"""
        self._query_parts.append("has:attachment")
        return self

    def filename(self, pattern):
        """Add filename: filter"""
        self._query_parts.append(f"filename:{pattern}")
        return self

    def build(self):
        """Build the final query string"""
        return " ".join(self._query_parts)
