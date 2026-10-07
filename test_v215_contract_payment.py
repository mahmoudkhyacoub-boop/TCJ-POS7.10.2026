from pathlib import Path
import ast

p = Path(__file__).with_name('main.py')
s = p.read_text(encoding='utf-8')
ast.parse(s)
checks = {
    'intake_contract_has_issue_section': 'rtl("الصيانة المطلوبة", body_font, y + 16' in s,
    'intake_contract_has_notes_section': 'rtl("الملاحظات", body_font, y + 16' in s,
    'combined_contract_keeps_issue_separate': 'field("الصيانة المطلوبة", order[8], y, wrap=True)' in s,
    'combined_contract_has_notes_separate': 'field("الملاحظات", order[9], y, wrap=True)' in s,
    'edit_register_separate_issue_widget': 'issue = ctk.CTkTextbox' in s and 'issue_text = issue.get' in s,
    'edit_register_separate_notes_widget': 'notes = ctk.CTkTextbox' in s and 'note_text = notes.get' in s,
    'sale_payment_selector': 'combos["payment"] = ctk.CTkComboBox' in s and 'combos["payment"].set(row[10] or "Cash")' in s,
    'sale_payment_saved': 'payment_method=?, source_id=?' in s and 'new_payment' in s,
    'credit_debt_guard': 'لا يمكن تحويل بيع آجل له دفعة مسجلة' in s,
    'journal_reposted': '_void_journals_for_record(source, rid' in s and '_post_operation_journal_from_row(source, rid)' in s,
}
for k, v in checks.items():
    print(k.upper(), 'PASS' if v else 'FAIL')
    assert v, k
print('V215_STATIC=PASS')
