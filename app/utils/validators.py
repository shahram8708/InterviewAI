import re

def validate_name(name: str) -> tuple[bool, str]:
    if not name or len(name) < 2 or len(name) > 150:
        return False, "Name must be between 2 and 150 characters."
    if not re.match(r'^[\w\s.-]+$', name):
        return False, "Name contains invalid characters."
    return True, ""

def validate_api_key_format(key: str) -> tuple[bool, str]:
    if not key or len(key) < 10 or len(key) > 100:
        return False, "API key must be between 10 and 100 characters."
    return True, ""

def validate_job_role(role: str) -> tuple[bool, str]:
    if not role or not role.strip():
        return False, "Job role cannot be empty."
    if len(role) > 150:
        return False, "Job role must be under 150 characters."
    return True, ""

def validate_company_name(name: str) -> tuple[bool, str]:
    if not name or not name.strip():
        return False, "Company name cannot be empty."
    if len(name) > 150:
        return False, "Company name must be under 150 characters."
    return True, ""

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Normalize whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean
