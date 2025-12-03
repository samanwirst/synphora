def seconds_to_minutes(seconds: int):
    if seconds < 0:
        raise ValueError("Only positive integers can be converted.")

    minutes = seconds // 60
    remainder = seconds % 60
    return [minutes, remainder]

def format_duration(seconds: int) -> str:
    if seconds < 0:
        raise ValueError("Only positive integers can be formatted.")

    minutes, remainder = seconds_to_minutes(seconds)
    if minutes > 0:
        return f"{minutes} minutes" + (f" and {remainder} seconds" if remainder != 0 else "")
    return f"{remainder} seconds"

def download_audio(message_id: int, path: str):
    return