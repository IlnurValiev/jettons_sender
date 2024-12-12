from sqlite3 import connect 
from typing import Union

async def create(db_path: Union[str, bytes], table: str, columns: dict, get_last_row: bool = False):
    conn = connect(db_path)
    cursor = conn.cursor()
    
    if not get_last_row:
        cursor.execute(
            f"INSERT INTO {table}({','.join(columns)}) VALUES({','.join('?'*len(columns))})", 
            tuple(columns.values()))
        res = None
    else:
        cursor.execute(
            f"INSERT INTO {table}({','.join(columns)}) VALUES({','.join('?'*len(columns))})", 
            tuple(columns.values()))
        res = cursor.execute("SELECT last_insert_rowid()").fetchone()
    
    conn.commit()
    conn.close()

    return res

async def read(db_path: Union[str, bytes], table: str, columns: str, conditions: str, in_dict=False):
    conn = connect(db_path)
    cursor = conn.cursor()

    if conditions:
        res = cursor.execute(f"SELECT {columns} FROM {table} WHERE {conditions}").fetchall()
    else:
        res = cursor.execute(f"SELECT {columns} FROM {table}").fetchall()

    if in_dict:
        column_names = [description[0] for description in cursor.description]
        res = dict(zip(column_names, res))

    conn.close()

    return res

async def update(db_path: Union[str, bytes], table: str, columns: dict, conditions: str):
    conn = connect(db_path)
    cursor = conn.cursor()

    if conditions:
        cursor.execute(f"UPDATE {table} SET {'=?,'.join(columns)}=? WHERE {conditions}", tuple(columns.values(),))
    else:
        cursor.execute(f"UPDATE {table} SET {'=?,'.join(columns)}=?", tuple(columns.values(),))

    conn.commit()
    conn.close()

async def delete(db_path: Union[str, bytes], table: str, conditions: str):
    conn = connect(db_path)
    cursor = conn.cursor()

    if conditions:
        cursor.execute(f"DELETE FROM {table} WHERE {conditions}")
    else:
        cursor.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()