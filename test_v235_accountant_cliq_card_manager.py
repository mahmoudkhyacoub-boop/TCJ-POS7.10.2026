from pathlib import Path
import ast

source = Path('main.py').read_text(encoding='utf-8')
ast.parse(source)
workflow = Path('.github/workflows/build.yml').read_text(encoding='utf-8')

# Accountant refresh must reload saved values before recalculating the top summary cards.
assert 'load_openings(); refresh()' in source
assert 'تم حفظ الأرصدة الجديدة واعتمادها في البطاقات العلوية' in source

# Card-sales UI offers CLIQ instead of Credit, and maps it through the canonical ledger mapper.
card_screen = source[source.index('    def ui_card_sales(self):'):source.index('    def open_card_catalog_manager(self):')]
assert 'values=["Cash", "Visa", "CLIQ"]' in card_screen
assert 'payment.get() == "Credit"' not in card_screen
assert 'account = self._ledger_account_for_payment(payment.get())' in card_screen

# Manager-only catalog supports edit and safe soft-delete while preserving historical sales.
manager = source[source.index('    def open_card_catalog_manager(self):'):source.index('    def ui_pos(self):')]
assert 'if self.current_role != "admin"' in manager
assert 'تعديل البند المحدد' in manager
assert 'حذف البند المحدد' in manager
assert 'UPDATE mobile_cards SET active=0' in manager
assert 'الحفاظ على السجل التاريخي' in manager

# Build pipeline is aligned on V235 and one EXE name.
assert 'V235' in workflow
assert 'Accountant_Balances_CLIQ_Card_Manager.exe' in workflow
assert 'Inventory_Adjustments' not in workflow
print('V235_ACCOUNTANT_CLIQ_CARD_MANAGER=PASS')
