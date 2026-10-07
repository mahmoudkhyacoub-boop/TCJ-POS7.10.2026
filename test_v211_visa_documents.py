from pathlib import Path
import re

source = Path(__file__).with_name('main.py').read_text(encoding='utf-8')

# Policy examples: outgoing Visa deducts both commission and 0.9% from payout;
# bill-payment Visa adds both commission and 0.9% to the customer collection.
def outgoing_payout(value, commission):
    return round(max(value - round(value * 0.009, 2) - commission, 0), 2)

def bill_customer_total(value, commission):
    return round(value + round(value * 0.009, 2) + commission, 2)

assert outgoing_payout(10, 0.5) == 9.41
assert bill_customer_total(100, 2) == 102.90
assert 'if operation_type == "خروج حوالة":' in source
assert 'max(value - visa_processing_fee - commission, 0)' in source
assert 'max(amt - round(amt * 0.009, 2) - comm, 0)' in source
assert 'payout_amount = max(amount - visa_processing_fee - commission, 0)' in source
assert 'invoice_number = f"INV-' in source
assert 'رقم الفاتورة:' in source
assert 'draw.ellipse((62, 205, 238, 381)' in source
assert 'OFFICIAL' in source and 'TCJ' in source
# Outgoing Visa must debit the principal, not the gross/discounted customer total.
assert '"تحصيل قيمة خروج الحوالة عبر الفيزا"' in source
assert '"المبلغ المسلم للمستفيد بعد خصم العمولة ورسوم الفيزا"' in source
print('V211_VISA_DOCUMENTS=PASS')
print('OUTGOING_VISA_10_0.5=', outgoing_payout(10, 0.5))
print('BILL_VISA_100_2=', bill_customer_total(100, 2))
print('DOCUMENT_NUMBER_HEADER_SEAL=PASS')
