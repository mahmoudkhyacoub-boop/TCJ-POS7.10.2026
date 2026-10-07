import os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix='tcj_accountant_v224_'))
os.chdir(TMP); sys.path.insert(0, str(ROOT))
import main
main.DB_NAME = str(TMP / 'isolated.db')
db = main.Database()
assert db.cursor.execute('SELECT COUNT(*) FROM accountant_accounts').fetchone()[0] == 7
db.cursor.execute("UPDATE accountant_accounts SET opening_balance=100 WHERE account_key='cash'")
db.cursor.execute("INSERT INTO accountant_transactions (account_key,direction,amount,transaction_date,description,notes,user,created_at) VALUES (?,?,?,?,?,?,?,?)", ('cash','in',50,'2026-10-01','إيداع اختبار','ملاحظة','tester','2026-10-01T10:00:00'))
db.cursor.execute("INSERT INTO accountant_transactions (account_key,direction,amount,transaction_date,description,notes,user,created_at) VALUES (?,?,?,?,?,?,?,?)", ('cash','out',20,'2026-10-02','مصروف اختبار','ملاحظة','tester','2026-10-02T10:00:00'))
db.conn.commit()
balance = db.cursor.execute("SELECT opening_balance + COALESCE((SELECT SUM(CASE WHEN direction='in' THEN amount ELSE -amount END) FROM accountant_transactions t WHERE t.account_key=a.account_key),0) FROM accountant_accounts a WHERE account_key='cash'").fetchone()[0]
assert round(balance, 2) == 130
obj = main.TrendCenterApp.__new__(main.TrendCenterApp); obj.db = db
pdf = obj.generate_accountant_pdf('2026-10-01', '2026-10-02')
assert Path(pdf).exists() and Path(pdf).stat().st_size > 1000
assert db.cursor.execute('SELECT COUNT(*) FROM sales').fetchone()[0] == 0
print('V224_ACCOUNTANT=PASS')
print('BALANCE=130.00')
print('PDF=PASS')
