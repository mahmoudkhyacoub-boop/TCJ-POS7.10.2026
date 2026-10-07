from pathlib import Path

source = Path(__file__).with_name('main.py').read_text(encoding='utf-8')


def require(fragment, label):
    if fragment not in source:
        raise AssertionError(f'Missing {label}: {fragment}')


# Dialog text is passed through the one-pass formatter without RLM injection.
require('def format_dialog_arabic(text):', 'dialog Arabic formatter')
require('text=str(message or ""), font=FONT_DIALOG', 'logical confirmation dialog renderer')
require('return "\\u200f" + get_display(reshaped, base_dir="R") + "\\u200f"', 'one-pass dialog shaping with RLM boundaries')
require('lambda match: "\\u200e" + match.group(1) + "\\u200e"', 'safe token direction protection')

# Login brand strip is intentionally present beside the bilingual slogan, while service categories remain.
require('partner_marks = [', 'login partner logo strip')
require('samsung.png', 'Samsung partner logo')
require('playstation.png', 'PlayStation partner logo')
require('category_data = [', 'login service categories')

# Contracts are PNG files and have open, copy, and WhatsApp actions.
require('def _service_register_open_png(self, path):', 'PNG open helper')
require('def _service_register_copy_png(self, path, notify=True):', 'PNG clipboard helper')
require('def _service_register_send_contract_whatsapp(self, path, phone, order_no, kind, order=None):', 'PNG WhatsApp helper')
require('نسخ صورة PNG', 'copy PNG button')
require('فتح صورة PNG', 'open PNG button')
require('نسخ PNG وفتح WhatsApp', 'copy and WhatsApp button')
require('f"{order[1]}_{kind}.png"', 'PNG contract path')

# Original operational entry points remain intact.
for marker in ('def send_whatsapp(self, phone, message):', 'def open_service_register_intake(self):', 'def open_service_register_handover(self):', 'def search_service_register_records(self):'):
    require(marker, marker)

print('V144 device register assertions passed.')
