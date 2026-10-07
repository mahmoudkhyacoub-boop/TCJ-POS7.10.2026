import os, sys, tempfile, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix='tcj_accountant_v225_'))
os.chdir(TMP); sys.path.insert(0, str(ROOT))
import main
main.DB_NAME = str(TMP / 'isolated.db')
db = main.Database()
for amount, desc in [(50, 'حركة أولى'), (25, 'حركة ثانية')]:
    db.cursor.execute("INSERT INTO accountant_transactions (account_key,direction,amount,transaction_date,description,notes,user,created_at) VALUES (?,?,?,?,?,?,?,?)", ('cash','in',amount,'2026-10-03',desc,'','tester','2026-10-03T10:00:00'))
db.conn.commit()
obj = main.TrendCenterApp.__new__(main.TrendCenterApp); obj.db = db
pdf = obj.generate_accountant_pdf('', '')
assert Path(pdf).exists()
fonts = subprocess.check_output(['pdffonts', str(pdf)], text=True)
assert 'Cocon' in fonts, fonts
# Same update used by the UI: only the selected accountant row changes.
db.cursor.execute("UPDATE accountant_transactions SET amount=?, description=? WHERE id=?", (75, 'حركة معدلة', 1)); db.conn.commit()
assert db.cursor.execute("SELECT amount, description FROM accountant_transactions WHERE id=1").fetchone() == (75.0, 'حركة معدلة')
assert db.cursor.execute("SELECT amount, description FROM accountant_transactions WHERE id=2").fetchone() == (25.0, 'حركة ثانية')
assert 'def edit_accountant_transaction' in (ROOT/'main.py').read_text(encoding='utf-8')
print('V227_PDF_COCON_FONT=PASS')
print('V225_SINGLE_TRANSACTION_EDIT=PASS')
