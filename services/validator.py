def validate_number(value):
    try:
        val = int(value)
        return val >= 0
    except ValueError:
        return False

def validate_non_empty(text):
    return len(text.strip()) > 0