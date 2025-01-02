from datetime import date, datetime, timedelta
import pytest
from .date_utils import is_at_most_one_day_old

def test_is_at_most_one_day_old_with_date():
    today = date.today()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    tomorrow = today + timedelta(days=1)

    assert is_at_most_one_day_old(today) is True
    assert is_at_most_one_day_old(yesterday) is True
    assert is_at_most_one_day_old(two_days_ago) is False
    assert is_at_most_one_day_old(tomorrow) is True

def test_is_at_most_one_day_old_with_datetime():
    today = date.today()
    now = datetime.combine(today, datetime.min.time())
    
    today_morning = now.replace(hour=9, minute=0)
    today_evening = now.replace(hour=21, minute=0)
    yesterday_night = (now - timedelta(days=1)).replace(hour=23, minute=59)
    two_days_ago = (now - timedelta(days=2)).replace(hour=12, minute=0)

    assert is_at_most_one_day_old(today_morning) is True
    assert is_at_most_one_day_old(today_evening) is True
    assert is_at_most_one_day_old(yesterday_night) is True
    assert is_at_most_one_day_old(two_days_ago) is False

def test_is_at_most_one_day_old_edge_cases():
    today = date.today()
    
    # Test exactly one day ago
    one_day_ago = today - timedelta(days=1)
    assert is_at_most_one_day_old(one_day_ago) is True

    # Test exactly one day ago with datetime
    one_day_ago_dt = datetime.combine(one_day_ago, datetime.min.time())
    assert is_at_most_one_day_old(one_day_ago_dt) is True
