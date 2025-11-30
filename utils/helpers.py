import re

# -------------------------------------------------------------
# SANITIZE STRINGS (removes NUL bytes, trims spaces)
# -------------------------------------------------------------
def sanitize(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    return value.replace("\x00", "").strip()


# -------------------------------------------------------------
# NORMALIZE STRING FOR COMPARISON (lowercase, no spaces)
# -------------------------------------------------------------
def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", "", text.lower()).strip()


# -------------------------------------------------------------
# EXTRACT LINKEDIN SLUG FROM URL
# -------------------------------------------------------------
def linkedin_slug(url):
    """
    Input:
        https://www.linkedin.com/in/john-doe-12345678/
    Output:
        john-doe-12345678
    """
    if not url:
        return None

    url = url.strip()
    slug = url.replace("https://www.linkedin.com/in/", "")
    slug = slug.replace("http://www.linkedin.com/in/", "")
    slug = slug.split("?")[0].split("/")[0]
    return slug.lower().strip()


# -------------------------------------------------------------
# COMBINE TEXT FIELDS INTO A SINGLE BLOCK FOR EMBEDDINGS
# -------------------------------------------------------------
def safe_join(parts):
    """
    Joins list of strings into a single text block,
    removing empty parts & sanitizing automatically.
    """
    cleaned = []
    for p in parts:
        if p and isinstance(p, str):
            cleaned.append(sanitize(p))
    return "\n".join(cleaned)


# -------------------------------------------------------------
# BUILD COMBINED TEXT FROM EXPERIENCES
# (Used by embedding generator)
# -------------------------------------------------------------
def format_experience(company, title, description, start, end):
    parts = []

    if title and company:
        parts.append(f"{title} at {company}")
    elif title:
        parts.append(title)
    elif company:
        parts.append(company)

    date_part = []
    if start:
        date_part.append(str(start))
    if end:
        date_part.append(str(end))

    if date_part:
        parts.append(f"({' - '.join(date_part)})")

    if description:
        parts.append(description)

    return " ".join([sanitize(x) for x in parts if x])
