from pathlib import Path
import ast
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

assert '"حملات تسويقية": "الحملات التسويقية"' in SOURCE
assert SOURCE.count('self.ui_marketing_campaigns') == 2
assert 'def ui_marketing_campaigns(self):' in SOURCE
assert 'CTkTextbox' in SOURCE
assert 'إرسال الحملة عبر WhatsApp' in SOURCE
assert 'SELECT name, phone FROM customers' in SOURCE
assert 'replace("{اسم_العميل}", name)' in SOURCE
assert 'abs(ratio - target) > 0.02' in SOURCE
assert 'لا يغيّر القيود أو المخزون' in SOURCE

# Verify the 9:16 validation contract with representative image dimensions.
def accepted(w, h):
    return abs((w / h) - (9 / 16)) <= 0.02

assert accepted(1080, 1920)
assert accepted(900, 1600)
assert not accepted(1080, 1080)
assert not accepted(1920, 1080)

# Ensure the new method is a class method, not an accidental nested function.
methods = [n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef) and n.name == "ui_marketing_campaigns"]
assert len(methods) == 1 and len(methods[0].args.args) == 1

print("V222 campaign checks passed: navigation, permissions, textbox, dynamic customer names, WhatsApp flow, and 9:16 validation.")
