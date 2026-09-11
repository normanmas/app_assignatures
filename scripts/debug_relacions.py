#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

conn = sqlite3.connect('dades/assignatures.sqlite')
cursor = conn.cursor()

# Comptar relacions per grau
print("Relacions a graus_assignatures per grau:")
cursor.execute("SELECT grau_id, COUNT(*) as count FROM graus_assignatures GROUP BY grau_id ORDER BY grau_id")
results = cursor.fetchall()

for grau_id, count in results:
    cursor.execute("SELECT nom FROM graus WHERE id = ?", (grau_id,))
    grau_nom = cursor.fetchone()[0]
    print(f"  Grau {grau_id} ({grau_nom[:50]}): {count} relacions")

# Total relacions
cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
total = cursor.fetchone()[0]
print(f"\nTotal relacions: {total}")

# Comptar assignatures uniques a graus_assignatures
cursor.execute("SELECT COUNT(DISTINCT assignatura_codi) FROM graus_assignatures")
unique_codes = cursor.fetchone()[0]
print(f"Codis únics a graus_assignatures: {unique_codes}")

# Comptar assignatures a la taula assignatures
cursor.execute("SELECT COUNT(*) FROM assignatures")
total_assignatures = cursor.fetchone()[0]
print(f"Total assignatures a la taula assignatures: {total_assignatures}")

conn.close()
