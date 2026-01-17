from typing import Union

def validate_number(value: Union[str, int, float]) -> bool:
    try:
        val: int = int(value)
        return val >= 0
    except (ValueError, TypeError):
        return False

def validate_non_empty(text: str) -> bool:
    return len(text.strip()) > 0