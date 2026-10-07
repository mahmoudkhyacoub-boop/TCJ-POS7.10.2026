from pathlib import Path
import ast, re
s=Path('main.py').read_text(encoding='utf-8')
ast.parse(s)
for marker in ['card_number', 'رقم البطاقة / الرقم السري', 'عملية بيع بطاقة', 'skip_whatsapp_prompt']:
    assert marker in s, marker
assert 'self._ensure_column("card_sales", "card_number", "TEXT")' in s
assert 'card_number,date,time,user,source_id' in s
assert 'رقم البطاقة: {entered_card_number}' in s
assert 'extra[\'card_number\']' in s
assert 'if not entered_card_number: raise ValueError' not in s
print('V234_CARD_NUMBER=PASS')
