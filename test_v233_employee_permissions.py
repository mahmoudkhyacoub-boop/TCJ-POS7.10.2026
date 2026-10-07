from pathlib import Path
import ast
s=Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(s)
assert 'if self._has_permission("مرتجع / تالف"):' in s
assert 'if not self._has_permission("مرتجع / تالف"):' in s
assert 'show_cost = self.current_role == "admin"' in s
assert 'price_column = "buy_price" if show_cost else "sell_price"' in s
assert 'Financial Policies Panel (V112) — manager-only settings.' in s
# The employee branch must use sale price and must not build a purchase-cost label.
start=s.index('    def open_inventory_adjustment_product_search')
end=s.index('    def open_inventory_adjustment_operation_search', start)
segment=s[start:end]
assert 'price_head = "تكلفة الشراء" if show_cost else "سعر البيع"' in segment
print('V233_EMPLOYEE_PERMISSIONS=PASS')
