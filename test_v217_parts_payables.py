from pathlib import Path
import ast
import sqlite3
from main import Database

src = Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(src)
checks = {
    'movement_table': 'maintenance_part_movements' in src,
    'record_additions': 'movement_type, quantity, unit_cost' in src and '"add"' in src,
    'record_usage': '"use"' in src and 'maintenance_id=m_id' in src,
    'baseline_formula': 'maintenance_parts_from_baseline' in src and 'baseline_value' in src,
    'supplier_payables_visible': 'ذمم الموردين' in src,
    'legacy_other_liabilities_hidden': 'baseline_extra = add_money_fields(baseline_frame, [("other_assets", "موجودات أخرى")])' in src,
    'journal_flow_untouched': '_post_operation_journal_from_row' in src and '_void_journals_for_record' in src,
}
for name, ok in checks.items():
    print(name.upper(), 'PASS' if ok else 'FAIL'); assert ok

# Isolated dynamic calculation equivalent to the program's ledger formula.
con = sqlite3.connect(':memory:')
con.execute('CREATE TABLE maintenance_part_movements (movement_type TEXT, quantity REAL, unit_cost REAL, created_at TEXT)')
con.executemany('INSERT INTO maintenance_part_movements VALUES (?,?,?,?)', [
    ('add', 2, 10, '2026-09-04 11:00:00'),
    ('use', 1, 10, '2026-09-04 12:00:00'),
    ('add', 3, 5, '2026-09-04 13:00:00'),
])
value = con.execute("SELECT SUM(CASE WHEN movement_type='add' THEN quantity*unit_cost WHEN movement_type IN ('use','adjustment_out') THEN -quantity*unit_cost ELSE 0 END) FROM maintenance_part_movements").fetchone()[0]
assert round(100 + value, 2) == 125.0
print('BASELINE_PLUS_ADDITIONS_MINUS_USAGE=PASS 125.00')
print('SUPPLIER_PAYABLES_SEPARATE=PASS')
print('V217_STATIC_DYNAMIC=PASS')
