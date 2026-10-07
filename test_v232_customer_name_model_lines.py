from pathlib import Path
import ast, sqlite3
s=Path(__file__).with_name('main.py').read_text(encoding='utf-8')
ast.parse(s)
for marker in ['CTkTextbox(box,height=82','entries["phone_model"].get("1.0", "end-1c")','customer_name = ctk.CTkEntry','SELECT name, points FROM customers WHERE phone=? OR phone=?','"client": client_name']:
    assert marker in s, marker
con=sqlite3.connect(':memory:'); con.execute('CREATE TABLE customers(phone TEXT PRIMARY KEY,name TEXT,points INTEGER)'); con.execute('INSERT INTO customers VALUES (?,?,?)',('791234567','أحمد',25))
raw='0791234567'; alt=raw[1:] if raw.startswith('0') else '0'+raw
row=con.execute('SELECT name,points FROM customers WHERE phone=? OR phone=?',(raw,alt)).fetchone()
assert row==('أحمد',25)
print('V232_CUSTOMER_NAME_AND_MODEL_LINES=PASS')
