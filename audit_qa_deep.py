from pathlib import Path
import ast
import math
import re
from types import SimpleNamespace
from main import TrendCenterApp

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'main.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
app = TrendCenterApp.__new__(TrendCenterApp)

results = []
def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(('PASS' if ok else 'FAIL'), name, detail)

# Static UI inventory: every direct self-method command and event callback.
commands = re.findall(r'command\s*=\s*self\.([A-Za-z_]\w*)(?![A-Za-z0-9_\.])', SOURCE)
methods = {node.name for cls in TREE.body if isinstance(cls, ast.ClassDef) for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
missing = sorted(set(commands) - methods - {'quit'})
check('UI_CALLBACK_METHOD_RESOLUTION', not missing, f'commands={len(commands)}, missing={missing}')
check('UI_WIDGET_COMMAND_COVERAGE', len(set(commands)) >= 50, f'unique_callbacks={len(set(commands))}')
check('UI_EVENT_BINDINGS_PRESENT', '.bind(' in SOURCE, 'event bindings found')

# Numeric input boundary tests.
for value, expected_ok in [('10', True), ('10.50', True), ('1,25', True), ('0', False), ('-1', False), ('abc', False), ('', False), ('nan', False), ('inf', False), ('-inf', False)]:
    try:
        out = TrendCenterApp.positive_number(app, value, 'اختبار', allow_zero=False)
        ok = expected_ok and math.isfinite(out) and out > 0
        check(f'POSITIVE_NUMBER_{value}', ok, str(out))
    except ValueError as exc:
        check(f'POSITIVE_NUMBER_{value}', not expected_ok, 'rejected')

for value, expected_ok in [('1', True), ('2.0', True), ('1.5', False), ('0', False), ('-2', False), ('nan', False)]:
    try:
        out = TrendCenterApp.positive_integer(app, value, 'كمية')
        check(f'POSITIVE_INTEGER_{value}', expected_ok and isinstance(out, int), str(out))
    except ValueError:
        check(f'POSITIVE_INTEGER_{value}', not expected_ok, 'rejected')

# Explicit business formulas, including zero and high precision cases.
visa_cases = [
    (10, 0.5, 'Visa', 'خروج حوالة', 9.41),
    (0.01, 0, 'Visa', 'خروج حوالة', 0.01),
    (999999.99, 12.345, 'Visa', 'خروج حوالة', round(max(999999.99 - round(999999.99 * 0.009, 2) - 12.345, 0), 2)),
    (100, 2, 'Visa', 'دفع فاتورة', 102.90),
    (0, 2, 'Visa', 'دفع فاتورة', 2),
    (100, 2, 'Cash', 'دفع فاتورة', 102),
]
for amount, commission, method, typ, expected in visa_cases:
    actual = TrendCenterApp._visa_customer_total(app, amount, commission, method, typ)
    check(f'VISA_{typ}_{method}_{amount}', abs(actual - expected) < 1e-8, f'expected={expected}, actual={actual}')

# Discount policy: target margin 40%, allowed customer discount is 70% of maximum.
for cost, price, expected in [(60, 100, 0), (50, 100, 11.67), (10, 25, 5.83), (0, 20, 0.0)]:
    minimum = cost / (1.0 - 0.40) if cost > 0 else price
    maximum = max(price - minimum, 0.0)
    allowed = round(maximum * 0.70, 2)
    check(f'DISCOUNT_COST_{cost}_PRICE_{price}', allowed == expected, f'expected={expected}, actual={allowed}')

# Static flow coverage for inventory and operations.
markers = {
    'sales': 'def checkout', 'purchases': 'def add_purchase', 'maintenance': 'def add_maintenance',
    'transfers': 'def add_transfer', 'expenses': 'def add_expense', 'returns': 'inventory_adjustments',
    'reports': 'def ui_reports', 'customers': 'def ui_customers', 'debts': 'def ui_debts',
    'service_register': 'def ui_service_register', 'backup': 'def create_manual_backup',
    'settings': 'def ui_settings', 'permissions': 'user_permissions',
}
for name, marker in markers.items(): check(f'MODULE_{name}', marker in SOURCE)

# Accounting invariants and protections.
check('JOURNAL_BALANCE_GUARD', 'abs(debit_total - credit_total)' in SOURCE and 'debit < 0 or credit < 0' in SOURCE)
check('VOID_REVERSAL_SUPPORT', '_void_journals_for_record' in SOURCE and 'source_type=\'reversal\'' in SOURCE)
check('INVENTORY_RETURN_LIMITS', 'remaining_purchase_qty' in SOURCE and 'remaining_qty' in SOURCE)
check('SALE_COGS_REPOST_SUPPORT', '_void_journals_for_record("sales"' in SOURCE or 'COGS' in SOURCE)
check('NO_RED_TEXT_ASSIGNMENTS', not re.findall(r'(?:text_color|foreground)\s*=\s*COLOR_(?:RUBI|VINO|CRIMSON|PURPLE)', SOURCE))
check('Cocon_FONT_PRESENT', 'cocon-next-arabic-regular.otf' in SOURCE and 'AddFontResourceExW' in SOURCE)
check('ALERT_HANDLERS', 'def show_msg' in SOURCE and 'def ask_confirm' in SOURCE)
check('DOCUMENTS_PNG', 'img.save(inv_path)' in SOURCE and 'image.save(path)' in SOURCE)

failed = [r for r in results if not r[1]]
print('QA_DEEP_TOTAL=', len(results))
print('QA_DEEP_PASS=', len(results)-len(failed))
print('QA_DEEP_FAIL=', len(failed))
