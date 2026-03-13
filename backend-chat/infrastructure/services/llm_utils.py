import json

def has_error(error: list[dict]) -> bool:
    try:
        if len(error) == 0:
            return False
        content = error[0].get("text")
        parsed = json.loads(content)
        return bool(parsed.get("error"))
    except Exception as e:
        return False