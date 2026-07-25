import sqlite3
c = sqlite3.connect('data.db')
tables = ['sales', 'subs', 'expenses', 'customers', 'funnel']
for t in tables:
    print(t, c.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0])
