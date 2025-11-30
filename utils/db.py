import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import functools

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# -----------------------------------------------------------------------
# CONNECT TO SUPABASE POSTGRES
# -----------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


@functools.lru_cache(maxsize=32)
def get_table_columns(table_name: str):
    """Return a set of column names for the given table (cached)."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s;",
            (table_name,)
        )
        rows = cur.fetchall()
        conn.close()
        return set(r['column_name'] for r in rows)
    except Exception:
        return set()


# -----------------------------------------------------------------------
# RUN A SELECT QUERY AND RETURN A PANDAS DATAFRAME
# -----------------------------------------------------------------------

def fetch_df(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------
# RUN ANY SQL (INSERT, UPDATE, DELETE)
# -----------------------------------------------------------------------

def run_sql(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------
# RUN SAFE SELECT RETURNING PYTHON LIST / DICT
# -----------------------------------------------------------------------

def fetch_all(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_one(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    if params is None:
        cur.execute(query)
    else:
        cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


# -----------------------------------------------------------------------
# VECTOR SEARCH (USED BY AI SEARCH LATER)
# -----------------------------------------------------------------------

def vector_search(query_vec, limit=10):
    """
    query_vec must be "[0.123, -0.443, ...]" format
    """
    sql = """
        SELECT
            alumni_internal_id,
            linkedin_id,
            combined_text,
            embedding <-> %s::vector AS distance
        FROM alumni_embeddings
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
    """

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (query_vec, query_vec, limit))
    rows = cur.fetchall()
    conn.close()
    return rows
