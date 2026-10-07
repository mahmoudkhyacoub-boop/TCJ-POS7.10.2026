from pathlib import Path
import ast

s = Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(s)
checks = {
    'maintenance_parts_column': 'maintenance_parts_cost' in s and 'self._ensure_column("financial_position_snapshots", "maintenance_parts_cost", "REAL DEFAULT 0")' in s,
    'maintenance_parts_valuation': 'SUM(cost_price * stock)' in s and 'system_maintenance_parts' in s,
    'maintenance_parts_in_assets': '"maintenance_parts"' in s and 'إجمالي تكلفة قطع الصيانة' in s,
    'new_baseline_button_left': 'تثبيت مرجع أساسي جديد' in s and 'side="left"' in s,
    'new_baseline_edit_flow': 'def edit_baseline()' in s and 'baseline_new_mode' in s,
    'new_baseline_insert': 'snapshot_type, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost' in s,
    'current_snapshot_insert': 'values["maintenance_parts"]' in s,
    'movement_after_baseline_timestamp': "(je.entry_date || ' ' || COALESCE(je.entry_time,'00:00:00')) > ?" in s,
    'journal_unchanged': 'journal_entries' in s and '_post_operation_journal_from_row' in s,
}
for name, ok in checks.items():
    print(name.upper(), 'PASS' if ok else 'FAIL')
    assert ok, name
print('V216_STATIC=PASS')
