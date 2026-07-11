from datetime import date


def parse_date_value(value: str | date | None) -> date:
    if value is None or value == "today":
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
