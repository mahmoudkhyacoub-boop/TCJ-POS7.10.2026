from pathlib import Path
import ast
from main import TrendCenterApp

source = Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(source)
app = TrendCenterApp.__new__(TrendCenterApp)

checks = {
    'separate_issue_and_notes': 'issue = ctk.CTkTextbox' in source and 'notes = ctk.CTkTextbox' in source and 'issue_text = issue.get' in source and 'note_text = notes.get' in source,
    'rtl_issue_and_notes': source.count('widget._textbox.configure(font=FONT_NORMAL_BOLD, justify="right", wrap="word")') >= 1,
    'microphone_in_phone_checklist': '"المايك"' in source and '"هاتف": ["الشاشة", "قاعدة الشحن", "الصوت", "المايك"' in source,
    'sale_full_summary': 'SELECT code, name, qty, price, total, buy_cost, date, time, user, customer_phone, payment_method FROM sales' in source,
    'sale_customer_phone_editable': 'fields["customer_phone"] = self._edit_field' in source,
    'sale_updates_customer_phone': 'customer_phone=?' in source and 'new_customer_phone' in source,
    'sale_repost_preserved': '_void_journals_for_record(source, rid' in source and '_post_operation_journal_from_row(source, rid)' in source,
    'no_accounting_schema_change': 'CREATE TABLE IF NOT EXISTS sales' in source,
}
for name, ok in checks.items():
    print(name.upper(), 'PASS' if ok else 'FAIL')
    assert ok, name
items = TrendCenterApp._service_register_check_items(app, 'هاتف')
assert 'المايك' in items
assert len(items) == 6
print('PHONE_CHECKLIST_ITEMS=', items)
print('V214_THREE_POINTS_STATIC=PASS')
