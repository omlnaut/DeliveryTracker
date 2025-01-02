from datetime import datetime, date, timedelta

def is_at_most_one_day_old(input_date: date|datetime) -> bool:
    """
    Check if the given date/datetime is at most one day older than today.
    
    Args:
        input_date: A date or datetime object to check
        
    Returns:
        bool: True if the date is today or at most one day old, False otherwise
    """
    # Convert datetime to date if needed
    if isinstance(input_date, datetime):
        input_date = input_date.date()
    
    today = date.today()
    one_day_ago = today - timedelta(days=1)
    
    return input_date >= one_day_ago
