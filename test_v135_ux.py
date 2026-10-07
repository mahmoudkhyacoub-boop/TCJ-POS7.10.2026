from pathlib import Path
import ast

ROOT = Path(__file__).parent
SOURCE = ROOT / "main.py"
text = SOURCE.read_text(encoding="utf-8")
ast.parse(text, filename=str(SOURCE))

required = {
    "dark_alert": 'fg_color=COLOR_NAVY, border_color=COLOR_CRIMSON',
    "white_alert_text": 'text_color=COLOR_WHITE,',
    "dark_report_rows": 'row_bg = COLOR_NAVY if i % 2 == 0 else COLOR_NAVY_LIGHT',
    "white_report_labels": 'text_color=COLOR_WHITE, anchor="e"',
    "rtl_intake_notes": 'notes._textbox.tag_configure("rtl", justify="right")',
    "handover_search": 'def search_receipts():',
    "receipt_search_button": 'بحث في السجلات',
    "brand_footer_white": 'text_color=COLOR_WHITE).pack(pady=(0, 18))',
    "intake_message_header": 'ترند سنتر الأردن\\nTREND CENTER JORDAN\\n',
    "intake_message_fields": 'إيصال استلام جهاز رقم:',
    "handover_message": 'تم تسليم جهاز:',
}
missing = [name for name, snippet in required.items() if snippet not in text]
if missing:
    raise AssertionError(f"Missing V135 requirements: {missing}")

contract_start = text.index('    def _service_register_contract(')
contract_end = text.index('    def _service_register_order_row(', contract_start)
contract = text[contract_start:contract_end]
for forbidden in ('توقيع الموظف', 'تأكيد العميل', 'توقيع العميل'):
    if forbidden in contract:
        raise AssertionError(f"Signature field remains in contract: {forbidden}")

assert 'rtl("تم فحص الجهاز وتسليمه للعميل حسب البيانات أعلاه."' in contract
assert 'rtl("ترند سنتر الأردن — سجل تشغيلي لخدمة الصيانة"' in contract
print("V135 UX checks passed: syntax, contrast tokens, RTL notes, search, WhatsApp messages, and signature removal.")
