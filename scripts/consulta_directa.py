#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

conn = sqlite3.connect('dades/assignatures.sqlite')
cursor = conn.cursor()

# Consultes directes
print("Consultes directes a la base de dades:")
print("=" * 70)

# 1. Total relacions
cursor.execute("SELECT COUNT(*) FROM graus_assignatures")
total = cursor.fetchone()[0]
print(f"Total relacions a graus_assignatures: {total}")

# 2. Relacions per grau
cursor.execute("""
    SELECT g.nom, COUNT(*) as count
    FROM graus_assignatures ga
    JOIN graus g ON ga.grau_id = g.id
    GROUP BY g.id
    ORDER BY g.id
""")
print("\nRelacions per grau:")
for row in cursor.fetchall():
    print(f"  {row[0]:50s}: {row[1]}")

# 3. Assignatures sense relació
cursor.execute("""
    SELECT COUNT(*) 
    FROM assignatures a
    WHERE a.codi NOT IN (SELECT assignatura_codi FROM graus_assignatures)
""")
no_relacionades = cursor.fetchone()[0]
print(f"\nAssignatures sense relació: {no_relacionades}")

# 4. Codis sense relació
cursor.execute("""
    SELECT a.codi 
    FROM assignatures a
    WHERE a.codi NOT IN (SELECT assignatura_codi FROM graus_assignatures)
""")
codis_sense_relacio = [row[0] for row in cursor.fetchall()]
print(f"Codis sense relació: {codis_sense_relacio}")

# 5. Total assignatures
cursor.execute("SELECT COUNT(*) FROM assignatures")
total_assignatures = cursor.fetchone()[0]
print(f"\nTotal assignatures: {total_assignatures}")

# 6. Codis únics a graus_assignatures
cursor.execute("SELECT COUNT(DISTINCT assignatura_codi) FROM graus_assignatures")
unique_relacionades = cursor.fetchone()[0]
print(f"Codis únics relacionats: {unique_relacionades}")

conn.close()
