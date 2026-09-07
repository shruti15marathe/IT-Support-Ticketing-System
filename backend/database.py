import mysql.connector
from mysql.connector import Error
from flask import current_app

def get_connection():
    return mysql.connector.connect(**current_app.config['DB_CONFIG'])

def query(sql, params=(), fetch=False, many=False, commit=False):
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    try:
        if many: cur.executemany(sql, params)
        else: cur.execute(sql, params)
        if commit:
            conn.commit(); return cur.lastrowid
        return cur.fetchall() if fetch else None
    finally:
        cur.close(); conn.close()
