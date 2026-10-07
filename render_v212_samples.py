from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from PIL import Image, ImageDraw
from main import TrendCenterApp

root = Path(tempfile.mkdtemp(prefix='tcj_v212_docs_'))
sponsor = root / 'sponsor_1.png'
logo = root / 'logo.png'
for path, label, color in ((sponsor, 'SPONSOR', (40, 70, 110, 255)), (logo, 'TCJ', (165, 18, 38, 255))):
    image = Image.new('RGBA', (240, 80), 'white')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, 238, 78), radius=10, outline=color, width=4)
    draw.text((120, 40), label, fill=color, anchor='mm')
    image.save(path)

conn = sqlite3.connect(':memory:')
cur = conn.cursor()
cur.execute('CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)')
settings = [
    ('invoice_dir', str(root / 'invoices')), ('sponsors_font_size', '22'),
    ('sponsors_title', 'رعاة Trend Center Jordan'), ('sponsors_paths', str([str(sponsor)])),
]
cur.executemany('INSERT INTO settings VALUES (?,?)', settings)
conn.commit()
app = TrendCenterApp.__new__(TrendCenterApp)
app.db = SimpleNamespace(cursor=cur, db_path=root / 'shop.db')
app.cart = [{'name': 'شاحن اختبار', 'qty': 1, 'total': 12.5}]
app._shop_identity = lambda: ('ترند سنتر الأردن', 'Trend Center JO', '0790000000', 'Amman - Jordan', str(logo))
app.send_whatsapp = lambda *args: None
invoice = app.generate_invoice(12.50, 'SALE', {'client':'عميل اختبار', 'payment':'Cash', 'phone':'', 'points':0})
order = (1, 'SR-212', 'عميل اختبار', '0790000000', 'هاتف', 'Samsung', 'S24', 'IMEI-212', 'تبديل شاشة', 'ملاحظات الاستلام', '{"شاحن":"سليم"}', '{"الشاشة":"تم الفحص"}', None, 'تم التسليم', '2026-09-02', '15:00', '2026-09-02', '15:00', '2026-09-02', '16:00', 25.0, 8.0, 8.5, 16.5, 'تم التسليم بعد الفحص', 'شاحن وعلبة', 'شاحن وعلبة', '')
combined = app._service_register_combined_contract(order)
print('ROOT=', root)
print('INVOICE=', root / 'invoices' / __import__('datetime').datetime.now().strftime('%Y-%m-%d'))
print('COMBINED=', combined)
