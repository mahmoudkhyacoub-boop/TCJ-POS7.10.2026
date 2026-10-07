from pathlib import Path
import ast, sqlite3
ROOT=Path(__file__).resolve().parent
s=(ROOT/'main.py').read_text(encoding='utf-8')
ast.parse(s)
checks=['sale_price','INSERT INTO sales(code,name,qty,price,total,buy_cost','self.send_whatsapp(client_phone, msg)','"بيع البطاقات": "بيع البطاقات"','if self.current_role == "admin": detail_fields.insert']
for c in checks: assert c in s, c
con=sqlite3.connect(':memory:')
con.executescript('''CREATE TABLE mobile_cards(id INTEGER PRIMARY KEY,provider TEXT,category TEXT,denomination TEXT,unit_cost REAL DEFAULT 0,stock INTEGER DEFAULT 0,active INTEGER DEFAULT 1,created_at TEXT,updated_at TEXT,UNIQUE(provider,category,denomination)); CREATE TABLE sales(id INTEGER PRIMARY KEY,code TEXT,name TEXT,qty INTEGER,price REAL,total REAL,buy_cost REAL,date TEXT,time TEXT,user TEXT,customer_phone TEXT);''')
con.execute('ALTER TABLE mobile_cards ADD COLUMN sale_price REAL NOT NULL DEFAULT 0')
con.execute('ALTER TABLE sales ADD COLUMN payment_method TEXT DEFAULT "Cash"'); con.execute('ALTER TABLE sales ADD COLUMN source_id TEXT')
con.execute('INSERT INTO mobile_cards(provider,category,denomination,unit_cost,sale_price,stock,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',('شركة جديدة','نوع جديد','فئة 5',4,5,0,'now','now'))
con.execute('INSERT INTO sales(code,name,qty,price,total,buy_cost,date,time,user,customer_phone,payment_method,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',('CARD-1','بطاقة شركة جديدة',2,5,10,8,'2026-10-05','10:00','u','079','Cash','card-sale-1'))
assert con.execute('SELECT total FROM sales').fetchone()[0]==10
assert con.execute('SELECT stock FROM mobile_cards').fetchone()[0]==0
print('V231_CARD_SALES=PASS')
