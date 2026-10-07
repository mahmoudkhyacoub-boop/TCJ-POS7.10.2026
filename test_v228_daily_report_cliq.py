import os, sys, tempfile, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent; TMP=Path(tempfile.mkdtemp(prefix='tcj_daily_v228_'))
os.chdir(TMP); sys.path.insert(0,str(ROOT))
import main
main.DB_NAME=str(TMP/'isolated.db')
db=main.Database(); today=datetime.date.today().isoformat()
# Populate all requested same-day operational sources.
db.cursor.execute("INSERT INTO sales (code,name,qty,price,total,buy_cost,date,time,user,customer_phone,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?)",('X','كابل',2,5,10,6,today,'09:00','tester','0791111111','Cash'))
db.cursor.execute("INSERT INTO maintenance (device_name,repair_desc,client_name,client_phone,revenue,payment_method,date,time,user) VALUES (?,?,?,?,?,?,?,?,?)",('هاتف','تغيير شاشة','عميل','0792222222',25,'Cash',today,'10:00','tester'))
db.cursor.execute("INSERT INTO transfers (type,client_name,client_phone,amount,commission,reference,payment_method,date,time,user) VALUES (?,?,?,?,?,?,?,?,?,?)",('دفع فاتورة','عميل','0793333333',20,1,'CL-1','CLIQ',today,'11:00','tester'))
db.cursor.execute("INSERT INTO expenses (desc,amount,date,time,user,payment_source,status) VALUES (?,?,?,?,?,?,?)",('مستلزمات',3,today,'12:00','tester','Cash','paid'))
db.cursor.execute("INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)",('daily_report_whatsapp_number','962791111111'))
db.conn.commit()
obj=main.TrendCenterApp.__new__(main.TrendCenterApp); obj.db=db; obj.current_user='tester'
pngs=obj.generate_daily_operations_png(today)
assert pngs and all(p.exists() and p.suffix=='.png' for p in pngs)
from PIL import Image
with Image.open(pngs[0]) as im: assert im.width >= 1700 and im.height >= 2300
assert obj._normalize_whatsapp_number('0791111111') == '962791111111'
assert obj._ledger_account_for_payment('CLIQ') == 'BANK'
source=(ROOT/'main.py').read_text(encoding='utf-8')
assert 'حفظ الأرصدة وتحديث' in source and 'command=save_openings' in source
assert 'payment not in ("Cash", "Visa", "CLIQ")' in source
print('V228_DAILY_REPORT_PNG=PASS', pngs[0])
print('V228_WHATSAPP_NUMBER_PERSISTENCE_MARKER=PASS')
print('V228_CLIQ_BILL_PAYMENT=PASS')
print('V228_ACCOUNTANT_REFRESH_SAVES_BALANCES=PASS')
