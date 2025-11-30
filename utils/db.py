import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# -----------------------------------------------------------------------
# CONNECT TO SUPABASE POSTGRES
# -----------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# -----------------------------------------------------------------------
# RUN A SELECT QUERY AND RETURN A PANDAS DATAFRAME
# -----------------------------------------------------------------------

def fetch_df(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    conn.close()
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------
# RUN ANY SQL (INSERT, UPDATE, DELETE)
# -----------------------------------------------------------------------

def run_sql(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------
# RUN SAFE SELECT RETURNING PYTHON LIST / DICT
# -----------------------------------------------------------------------

def fetch_all(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_one(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
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
