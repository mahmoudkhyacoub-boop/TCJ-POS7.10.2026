from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from main import TrendCenterApp

root = Path(tempfile.mkdtemp(prefix='tcj_v211_docs_'))
conn = sqlite3.connect(':memory:')
cur = conn.cursor()
cur.execute('CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)')
cur.execute("INSERT INTO settings VALUES ('invoice_dir', ?)", (str(root / 'invoices'),))
cur.execute("INSERT INTO settings VALUES ('sponsors_font_size', '18')")
cur.execute("INSERT INTO settings VALUES ('sponsors_title', 'رعاة Trend Center Jordan')")
conn.commit()
app = TrendCenterApp.__new__(TrendCenterApp)
app.db = SimpleNamespace(cursor=cur, db_path=root / 'shop.db')
app.cart = []
app._get_sponsor_paths = lambda: []
app._shop_identity = lambda: ('ترند سنتر الأردن', 'Trend Center JO', '0790000000', 'Amman - Jordan', '')
app.ask_confirm = lambda *args: False
invoice = app.generate_invoice(9.41, 'TRANSFER', {'client':'عميل اختبار', 'type':'خروج حوالة', 'ref':'TEST-211', 'phone':'', 'points':0, 'payment':'Visa'})
order = (1, 'SR-211', 'عميل اختبار', '0790000000', 'هاتف', 'Samsung', 'S24', 'IMEI-211', 'تبديل شاشة', 'فحص الجهاز', '{"الشاشة":"سليم"}', '{"الشاشة":"تم الفحص"}', None, 'مستلم', '2026-09-01', '14:00', '2026-09-01', '14:00', None, None, 0, 0, 0, 0, 'تم التسليم', 'شاحن')
contract = app._service_register_contract(order, 'intake')
print('INVOICE_SAMPLE=', invoice)
print('CONTRACT_SAMPLE=', contract)
