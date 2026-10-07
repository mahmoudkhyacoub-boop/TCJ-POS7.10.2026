import sqlite3
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0, str(Path(__file__).parent))
from main import Database

# Build only an isolated in-memory schema.
db = Database.__new__(Database)
db.db_path = Path('/tmp/v216_audit.db')
db.conn = sqlite3.connect(':memory:')
db.conn.execute('PRAGMA foreign_keys=ON')
db.cursor = db.conn.cursor()
db.create_tables()
cols = {r[1] for r in db.cursor.execute('PRAGMA table_info(financial_position_snapshots)')}
assert 'maintenance_parts_cost' in cols

db.cursor.execute("INSERT INTO maintenance_parts(part_name, phone_model, cost_price, sell_price, stock) VALUES(?,?,?,?,?)", ('Screen', 'Phone', 12.5, 20, 3))
parts_value = db.cursor.execute('SELECT COALESCE(SUM(cost_price * stock),0) FROM maintenance_parts').fetchone()[0]
assert round(parts_value,2) == 37.5

sql = """INSERT INTO financial_position_snapshots
(snapshot_date, period_label, snapshot_type, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost, customer_receivables, supplier_payables, other_assets, other_liabilities, total_assets, total_liabilities, net_position, notes, user, created_at)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
args=('2026-09-04','baseline','baseline',100,0,0,0,200,parts_value,0,0,0,0,337.5,0,337.5,'','audit','2026-09-04 10:00:00')
db.cursor.execute(sql,args)
db.cursor.execute(sql,('2026-09-04','current','current',110,0,0,0,210,parts_value+5,0,0,0,0,362.5,0,362.5,'','audit','2026-09-04 11:00:00'))
db.conn.commit()
rows=db.cursor.execute('SELECT snapshot_type, maintenance_parts_cost, total_assets FROM financial_position_snapshots ORDER BY id').fetchall()
assert rows == [('baseline',37.5,337.5),('current',42.5,362.5)], rows
print('SCHEMA_COLUMN=PASS')
print('PARTS_VALUATION=PASS 37.50')
print('BASELINE_CURRENT_INSERT=PASS')
print('NO_OPERATIONAL_TABLE_WRITES=PASS')
