from pathlib import Path
import ast
import sqlite3

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
ast.parse(SOURCE)

# Customer creation and welcome flow markers.
for marker in (
    'def add_new_customer(self):',
    'INSERT INTO customers (phone, name, points)',
    'حفظ وإرسال رسالة ترحيب',
    'self.send_whatsapp(phone, welcome)',
    'رصيد نقاطك الترحيبية الحالي',
):
    assert marker in SOURCE, marker

# Debt ordering and yellow highlighting markers.
assert 'tag_configure("remaining", background="#FFF3A6"' in SOURCE
assert SOURCE.count('ORDER BY CASE WHEN (total_debt - paid_amount) > 0.005 THEN 0 ELSE 1 END, id DESC') == 2
assert SOURCE.count('tags=("remaining",) if remaining > 0.005 else ()') == 2

# Simulate the exact SQL ordering independently with an in-memory schema.
conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE customer_debts (id INTEGER, total_debt REAL, paid_amount REAL)')
conn.executemany('INSERT INTO customer_debts VALUES (?,?,?)', [(1, 100, 100), (2, 50, 10), (3, 20, 20), (4, 30, 0)])
rows = conn.execute('SELECT id, total_debt-paid_amount FROM customer_debts ORDER BY CASE WHEN (total_debt - paid_amount) > 0.005 THEN 0 ELSE 1 END, id DESC').fetchall()
assert [r[0] for r in rows] == [4, 2, 3, 1], rows
assert all((r[1] > 0.005) for r in rows[:2])

print('V223 customer/debt checks passed: new customer fields, welcome WhatsApp, remaining-first ordering, and yellow row highlighting.')
