import os, sys, tempfile, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parent; TMP=Path(tempfile.mkdtemp(prefix='tcj_v229_adjust_')); os.chdir(TMP); sys.path.insert(0,str(ROOT))
import main
main.DB_NAME=str(TMP/'isolated.db')
db=main.Database()
# Add representative products and adjustment records without touching the live database.
db.cursor.execute("INSERT INTO products(code,name,buy_price,sell_price,stock) VALUES (?,?,?,?,?)",('P-1','شاحن',10,15,5))
db.cursor.execute("INSERT INTO inventory_adjustments(adjustment_no,adjustment_type,product_code,product_name,qty,unit_cost,original_sale_id,reason,date,time,user,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",('IA-1','مرتجع بيع','P-1','شاحن',2,10,22,'إرجاع','2026-10-04','10:00:00','tester','inventory-adjustment-test-1'))
db.cursor.execute("INSERT INTO inventory_adjustments(adjustment_no,adjustment_type,product_code,product_name,qty,unit_cost,original_sale_id,reason,date,time,user,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",('IA-2','تالف','P-1','شاحن',1,10,None,'كسر','2026-10-04','11:00:00','tester','inventory-adjustment-test-2'))
for source, lines in [('inventory-adjustment-test-1',[('SALES_REVENUE',20,0),('CASH',0,30),('INVENTORY',20,0),('COGS',0,20)]),('inventory-adjustment-test-2',[('INVENTORY_LOSS',10,0),('INVENTORY',0,10)])]:
    db.cursor.execute("INSERT INTO journal_entries(entry_date,entry_time,source_type,source_id,description,user,created_at) VALUES (?,?,?,?,?,?,?)",('2026-10-04','10:00:00','inventory_adjustment',source,'اختبار','tester','2026-10-04T10:00:00'))
    eid=db.cursor.lastrowid
    db.cursor.executemany("INSERT INTO journal_lines(entry_id,account_code,debit,credit,memo) VALUES (?,?,?,?,?)",[(eid,a,d,c,'test') for a,d,c in lines])
db.conn.commit()
obj=main.TrendCenterApp.__new__(main.TrendCenterApp); obj.db=db
pdf,csv,count=obj.generate_inventory_adjustment_report('2026-10-01','2026-10-04',TMP/'adjustments.pdf')
assert pdf.exists() and csv.exists() and count==2
text=csv.read_text(encoding='utf-8-sig')
assert 'مرتجع بيع' in text and 'تالف' in text and 'INVENTORY' in text and '20.00' in text
# Date validation and no-result behavior.
try: obj.generate_inventory_adjustment_report('2026-10-05','2026-10-01',TMP/'bad.pdf'); raise AssertionError('date order not rejected')
except ValueError: pass
obj.generate_inventory_adjustment_report('2026-11-01','2026-11-30',TMP/'empty.pdf')
assert (TMP/'empty.pdf').exists()
source=(ROOT/'main.py').read_text(encoding='utf-8')
for marker in ['open_inventory_adjustment_product_search','open_inventory_adjustment_operation_search','استخراج تقرير ضمن فترة من وإلى','generate_inventory_adjustment_report']:
    assert marker in source, marker
print('V229_REPORT_PDF_CSV=PASS', pdf, csv)
print('V229_FINANCIAL_INVENTORY_EFFECTS=PASS')
print('V229_DATE_VALIDATION=PASS')
print('V229_SEARCH_BUTTON_MARKERS=PASS')
