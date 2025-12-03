class CommonUtils:
    @staticmethod
    def seconds_to_minutes(seconds: int) -> list[int]:
        if seconds < 0:
            raise ValueError("Only positive integers can be converted.")

        minutes = seconds // 60
        remainder = seconds % 60
        return [minutes, remainder]

    @staticmethod
    def format_duration(seconds: int) -> str:
        if seconds < 0:
            raise ValueError("Only positive integers can be formatted.")

        minutes, remainder = CommonUtils.seconds_to_minutes(seconds)
        if minutes > 0:
            return f"{minutes} minutes" + (f" and {remainder} seconds" if remainder != 0 else "")
        return f"{remainder} seconds"