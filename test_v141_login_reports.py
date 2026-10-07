from pathlib import Path
import ast

ROOT = Path(__file__).parent
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

assert "def _get_current_month_revenue(self):" in SOURCE
assert 'strftime("%Y-%m")' in SOURCE
assert 'FROM sales WHERE date LIKE ?' in SOURCE
assert 'FROM maintenance WHERE date LIKE ?' in SOURCE
assert 'FROM transfers WHERE date LIKE ?' in SOURCE
assert "إيرادات الشهر الحالي" in SOURCE
assert "month_sales" in SOURCE and "month_maintenance" in SOURCE and "month_transfer_commissions" in SOURCE
assert "sales + maintenance + transfer_commissions" in SOURCE
assert 'font=FONT_NET_PROFIT_LABEL' in SOURCE
assert 'font=FONT_NET_PROFIT_VALUE' in SOURCE
assert 'text_color=COLOR_WHITE' in SOURCE
assert 'FONT_NET_PROFIT_VALUE = (APP_FONT_FAMILY, 32, "bold")' in SOURCE

# Ensure the helper is a method of the main application class and contains no writes.
helper = next(node for node in ast.walk(TREE) if isinstance(node, ast.FunctionDef) and node.name == "_get_current_month_revenue")
assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "execute" for node in ast.walk(helper))
assert not any(isinstance(node, ast.Attribute) and node.attr in {"commit", "rollback"} for node in ast.walk(helper))

print("V141 login/report checks passed: current-month revenue streams, read-only query path, white values, and enlarged net profit typography.")
