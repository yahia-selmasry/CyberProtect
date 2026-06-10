"""Pure utility functions with no Flask dependency."""


def seconds_to_display(seconds: float) -> str:
    """Convert total seconds to mm:ss.cc display string."""
    minutes = int(seconds) // 60
    remaining = seconds - minutes * 60
    whole = int(remaining)
    centis = round((remaining - whole) * 100)
    if centis == 100:
        whole += 1
        centis = 0
    return f"{minutes}:{whole:02d}.{centis:02d}"


def display_to_seconds(time_str: str) -> float:
    """Convert mm:ss.cc display string to total seconds."""
    minutes_part, rest = time_str.split(":")
    seconds_part, centis_part = rest.split(".")
    return int(minutes_part) * 60 + int(seconds_part) + int(centis_part) / 100
