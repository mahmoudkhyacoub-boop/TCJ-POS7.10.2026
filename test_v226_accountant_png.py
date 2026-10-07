import os, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent; TMP=Path(tempfile.mkdtemp(prefix='tcj_accountant_png_'))
os.chdir(TMP); sys.path.insert(0,str(ROOT))
import main
main.DB_NAME=str(TMP/'isolated.db')
db=main.Database()
db.cursor.execute("UPDATE accountant_accounts SET opening_balance=150 WHERE account_key='cash'")
db.cursor.execute("INSERT INTO accountant_transactions (account_key,direction,amount,transaction_date,description,notes,user,created_at) VALUES (?,?,?,?,?,?,?,?)",('cash','in',50,'2026-10-03','إيداع للاختبار','PDF PNG','tester','2026-10-03T10:00:00'))
db.conn.commit()
obj=main.TrendCenterApp.__new__(main.TrendCenterApp); obj.db=db
pdf=obj.generate_accountant_pdf('', '')
pngs=obj.generate_accountant_png('', '', pdf_path=pdf)
assert pngs and all(p.exists() and p.suffix=='.png' and p.stat().st_size>10000 for p in pngs)
from PIL import Image
with Image.open(pngs[0]) as im:
    assert im.width >= 1700 and im.height >= 2300, (im.width, im.height)
print('V226_ACCOUNTANT_PNG=PASS', pngs[0], im.size)
