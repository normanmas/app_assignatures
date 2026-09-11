#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

conn = sqlite3.connect('dades/assignatures.sqlite')
cursor = conn.cursor()

# Comptar relacions a graus_assignatures
cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
total_relacions = cursor.fetchone()[0]
print(f"Total relacions a graus_assignatures: {total_relacions}")

# Veure algunes relacions
cursor.execute("SELECT grau_id, assignatura_codi FROM graus_assignatures LIMIT 20")
print("\nPrimeres 20 relacions:")
for row in cursor.fetchall():
    print(f"  Grau {row[0]}: {row[1]}")

# Comptar per grau
print("\nRelacions per grau:")
cursor.execute("SELECT grau_id, COUNT(*) FROM graus_assignatures GROUP BY grau_id ORDER BY grau_id")
for row in cursor.fetchall():
    grau_id = row[0]
    cursor.execute("SELECT nom FROM graus WHERE id = ?", (grau_id,))
    grau_nom = cursor.fetchone()[0]
    print(f"  Grau {grau_id} ({grau_nom[:40]}...): {row[1]} assignatures")

conn.close()
