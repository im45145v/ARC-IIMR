import os
from dotenv import load_dotenv
from .helpers import sanitize, safe_join

# Try importing OpenAI SDK; if unavailable, set a flag and defer errors to runtime
try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize client only if OpenAI package is present and key provided
if HAS_OPENAI and OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None


# -------------------------------------------------------------
# GET EMBEDDING FOR ANY TEXT
# -------------------------------------------------------------
def get_embedding(text, model="text-embedding-3-small"):
    """
    Convert text to embedding using OpenAI.
    Returns: python list of floats
    """
    if not HAS_OPENAI or client is None:
        raise RuntimeError("OpenAI client not available. Install the 'openai' package and set OPENAI_API_KEY in your environment.")

    text = sanitize(text)

    if not text or len(text.strip()) == 0:
        return None

    emb = client.embeddings.create(
        model=model,
        input=text,
    ).data[0].embedding

    return emb


# -------------------------------------------------------------
# FORMAT EMBEDDING LIST INTO PGVECTOR TEXT
# -------------------------------------------------------------
def embedding_to_pgvector(emb):
    """
    Convert python list to pgvector string: "[1.23, -0.44, ...]"
    """
    if not emb:
        return None
    return "[" + ",".join(f"{x:.6f}" for x in emb) + "]"


# -------------------------------------------------------------
# BUILD COMBINED TEXT FOR VECTOR SEARCH
# (Used by chat, summarizer, AI search)
# -------------------------------------------------------------
def build_profile_text(profile, experiences, education, skills):
    """
    Combine all fields into a single searchable text blob.
    Used by embeddings + chatbot.
    """
    parts = []

    # Profile basics
    parts.append(f"Name: {sanitize(profile.get('full_name'))}")
    parts.append(f"Headline: {sanitize(profile.get('headline'))}")
    parts.append(f"About: {sanitize(profile.get('about'))}")

    # Experience formatting
    if experiences:
        exp_lines = []
        for e in experiences:
            line = safe_join([
                f"{e.get('title') or ''} at {e.get('company_name') or ''}",
                f"{e.get('start_date') or ''} - {e.get('end_date') or 'Present'}",
                e.get("description") or ""
            ])
            exp_lines.append(line)
        parts.append("Experiences:\n" + "\n".join(exp_lines))

    # Education formatting
    if education:
        edu_lines = []
        for ed in education:
            edu_lines.append(
                safe_join([
                    f"{ed.get('degree') or ''} at {ed.get('school_name') or ''}",
                    f"{ed.get('start_year') or ''}-{ed.get('end_year') or ''}"
                ])
            )
        parts.append("Education:\n" + "\n".join(edu_lines))

    # Skills list
    if skills:
        skills_text = ", ".join(s.get("skill_name") for s in skills if s.get("skill_name"))
        parts.append("Skills: " + sanitize(skills_text))

    return safe_join(parts)


# -------------------------------------------------------------
# GPT SUMMARIZE A SINGLE ALUMNI PROFILE
# -------------------------------------------------------------
def summarize_profile(profile_text):
    """
    Generates a clean, professional summary of an alumni.
    """
    prompt = f"""
    Summarize the following alumni profile in a clean, structured format:

    {profile_text}

    Provide a short summary including:
    - Key experiences
    - Industry background
    - Skills
    - Education
    """

    if not HAS_OPENAI or client is None:
        raise RuntimeError("OpenAI client not available. Install the 'openai' package and set OPENAI_API_KEY in your environment.")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert resume & profile summarizer."},
            {"role": "user", "content": prompt}
        ]
    )

    # Newer OpenAI SDK returns a ChatCompletionMessage object; access .content
    return getattr(response.choices[0].message, "content", None)


# -------------------------------------------------------------
# GPT QUERY → SQL FILTER OR VECTOR SEARCH DECIDER
# (AI agent to convert chatbot queries to actions)
# -------------------------------------------------------------
def interpret_query(user_query):
    """
    This converts a chatbot query into actions, telling Streamlit:
    - use SQL search
    - or use vector search
    - or use both
    """

    system_prompt = """
    You are an expert semantic router. Decide whether a query should be:
    - a vector search (semantic)
    - a SQL filter (exact)
    - or hybrid (both)
    
    Respond ONLY in JSON:
    {
        "mode": "vector" | "sql" | "hybrid",
        "sql_filters": { ... },
        "vector_query": "..."
    }
    """

    if not HAS_OPENAI or client is None:
        raise RuntimeError("OpenAI client not available. Install the 'openai' package and set OPENAI_API_KEY in your environment.")

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )

    import json
    content = getattr(resp.choices[0].message, "content", None)
    if content is None:
        raise RuntimeError("No content returned from OpenAI chat completion.")
    return json.loads(content)
