import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "erp_dev"),
        user=os.getenv("DB_USER", "erp_user"),
        password=os.getenv("DB_PASS", "erp_pass"),
    )


def query(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
