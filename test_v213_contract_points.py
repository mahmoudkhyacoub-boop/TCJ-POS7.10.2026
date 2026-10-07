from pathlib import Path
import ast
s = Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(s)
checks = {
 'seal_lowered': 'seal_y = 212' in s,
 'technician_in_contract': 'technician_name' in s and 'الفني' in s,
 'intake_wrap': 'intake_text' in s and 'قائمة فحص الاستلام' in s and 'wrap=True' in s,
 'handover_wrap': 'handover_text' in s and 'قائمة فحص التسليم' in s and 'wrap=True' in s,
 'part_cost_removed_from_combined': 'y = field("تكلفة القطعة"' not in s[s.index('def _service_register_combined_contract'):s.index('def _service_register_order_row')],
 'service_price_kept': 'تسعيرة الصيانة' in s[s.index('def _service_register_combined_contract'):s.index('def _service_register_order_row')],
 'current_points_visible': 'نقاطك الحالية' in s and 'fill=COLOR_NAVY' in s[s.index('نقاطك الحالية')-180:s.index('نقاطك الحالية')+160],
 'no_accounting_change_marker': 'view-only PNG' in s,
}
for name, ok in checks.items():
 print(name.upper(), 'PASS' if ok else 'FAIL'); assert ok, name
print('V213_CONTRACT_POINTS_STATIC=PASS')
