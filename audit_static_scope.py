from pathlib import Path
import ast
import re

source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
tree = ast.parse(source)
methods = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
required = {
    'login', 'checkout', 'add_purchase', 'add_transfer', 'add_expense',
    'add_maintenance', 'delete_record', 'edit_record_ui', 'ui_reports',
    'show_p_and_l_statement', 'show_cash_reconciliation', 'ui_inventory',
    'ui_service_register' if 'ui_service_register' in methods else 'open_service_register_intake',
    'ui_customers', 'edit_customer_data', 'ui_settings', 'add_new_user',
    'ui_database_health', 'ui_manual_backup', 'ui_live_operations_dashboard',
}
missing = sorted(required - methods)
assert not missing, missing
assert len(re.findall(r'^    def login\(self\):', source, re.M)) == 1
assert '_visa_customer_total' in source
assert '0.009' in source
assert 'command=self.login' in source
assert 'def _persist_customer_edit' in source
assert 'def _void_journals_for_record' in source
assert 'def _post_operation_journal_from_row' in source
assert 'def ui_reports' in source
assert 'def ui_settings' in source
print('AST_PARSE=PASS')
print('REQUIRED_OPERATION_METHODS=PASS', len(required))
print('SINGLE_LOGIN_METHOD=PASS')
print('VISA_FORMULA_MARKERS=PASS')
print('JOURNAL_REVERSAL_MARKERS=PASS')
print('CUSTOMER_EDIT_MARKERS=PASS')
print('REPORTS_SETTINGS_MARKERS=PASS')
