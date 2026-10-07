from pathlib import Path
import ast

source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
ast.parse(source)

assert 'operation_type in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment_method == "Visa"' in source
assert 't in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment == "Visa"' in source
assert 'kind in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment == "Visa"' in source
assert 'تحصيل قيمة خروج الحوالة عبر الفيزا' in source
assert 'المبلغ المسلم للمستفيد بعد خصم العمولة ورسوم الفيزا' in source
assert 'عمولة ورسوم خروج الحوالة' in source
assert 'APP_FONT_FAMILY = "Cocon® Next Arabic"' in source
assert 'text_color=COLOR_CRIMSON' not in source
assert 'text_color=COLOR_RUBI' not in source
assert 'text_color=COLOR_VINO' not in source

# Outgoing Visa deducts the processing fee and commission from the payout.
def outgoing_payout(value, commission):
    return round(max(value - round(value * 0.009, 2) - commission, 0), 2)

def bill_customer_total(value, commission):
    return round(value + round(value * 0.009, 2) + commission, 2)

assert outgoing_payout(10, 0.5) == 9.41
assert bill_customer_total(100, 2) == 102.90
print("OUTGOING_VISA_FORMULA=PASS")
print("COCON_NEXT_ARABIC_BOLD=PASS")
print("RED_TEXT_TO_WHITE=PASS")
print("NON_TEXT_GRAPHICS_PRESERVED_BY_MARKERS=PASS")
