from pathlib import Path
import ast

source = Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(source)
checks = {
    'combined_contract_method': 'def _service_register_combined_contract(self, order):' in source,
    'view_uses_combined': 'combined_path = self._service_register_combined_contract(order)' in source,
    'intake_section': 'تفاصيل الاستلام من العميل' in source,
    'handover_section': 'تفاصيل التسليم للعميل' in source,
    'invoice_spacing': 'd.line([20, 280, 480, 280], fill=COLOR_CRIMSON, width=3); y = 332' in source,
    'sponsor_title_persist': "('sponsors_title', ?)" in source,
    'sponsor_title_draw': 'd.text((250, footer_y), fix_arabic(sponsor_title' in source,
    'shop_identity': 's_name, s_name_en, s_phone, s_loc, logo_path = self._shop_identity()' in source,
    'invoice_number': 'invoice_number = f"INV-' in source,
    'png_output': 'image.save(path)' in source and 'img.save(inv_path)' in source,
}
for name, ok in checks.items():
    print(name.upper(), 'PASS' if ok else 'FAIL')
    assert ok, name
print('V212_DOCUMENTS_STATIC=PASS')
