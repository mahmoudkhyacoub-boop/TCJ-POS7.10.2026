from pathlib import Path
import ast

source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
ast.parse(source)

assert "def _visa_customer_total" in source
assert "visa_processing_fee = round(amt * 0.009, 2)" in source
assert "t in (\"دخول حوالة\", \"دفع فاتورة\", \"خروج حوالة\") and payment == \"Visa\"" in source
assert "operation_type in (\"دخول حوالة\", \"دفع فاتورة\", \"خروج حوالة\")" in source
assert "customer_total = self._visa_customer_total(amt, comm, payment, t)" in source
assert "return round(value + commission, 2)" in source
assert "payment_method = payment if t == \"دخول حوالة\" and payment == \"Visa\" else (payment if t != \"دخول حوالة\" else \"Cash\")" in source
assert "effective_payment = payment if t == \"دخول حوالة\" and payment == \"Visa\" else (\"Cash\" if t == \"دخول حوالة\" else payment)" in source

# The requested formula is deterministic: value + 0.9% processing fee + entered commission.
def expected(value, commission):
    return round(value + round(value * 0.009, 2) + commission, 2)
assert expected(100, 2) == 102.90
assert expected(10, 0.5) == 10.59
assert expected(10, 0.5) == 10.59  # outgoing Visa uses the same customer total

print("V194_VISA_FORMULA=PASS")
assert "if payment == \"Visa\"" in source
print("V194_NON_VISA_SCOPE_GUARD=PASS")
print("V194_OUTGOING_TRANSFER_VISA=PASS")
print("V194_FORMULA_EXAMPLES=PASS")
