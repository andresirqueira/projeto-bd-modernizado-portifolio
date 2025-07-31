#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona a coluna 'status' na tabela 'cabos' se não existir.
Uso: python add_status_column_cabos.py <banco.db>
"""
import sqlite3
import sys
import os

def add_status_column(db_file):
    if not os.path.exists(db_file):
        print(f'Arquivo {db_file} não encontrado!')
        return
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(cabos)")
    columns = [row[1] for row in cur.fetchall()]
    if 'status' not in columns:
        cur.execute("ALTER TABLE cabos ADD COLUMN status TEXT DEFAULT 'funcionando'")
        conn.commit()
        print("Coluna 'status' adicionada com sucesso!")
    else:
        print("Coluna 'status' já existe.")
    conn.close()

def main():
    if len(sys.argv) < 2:
        print('Uso: python add_status_column_cabos.py <banco.db>')
        return
    add_status_column(sys.argv[1])

if __name__ == "__main__":
    main()