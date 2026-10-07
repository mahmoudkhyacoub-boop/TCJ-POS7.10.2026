from pathlib import Path

source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
checks = {
    "english_brand": "Trend Center JO" in source,
    "cable_spelling": "شواحن • كيبل • حماية" in source and "شواحن • كيابل • حماية" not in source,
    "category_graphics": "category_img = ctk.CTkImage" in source and ("size=(64, 64)" in source or "size=(70, 70)" in source),
    "home_categories": all(name in source for name in ["إكسسوارات الهواتف", "البلايستيشن والألعاب", "الكمبيوتر والشبكات", "أنظمة المراقبة"]),
    "accounting_entry": "def _post_journal_entry" in source,
    "sales_purchase_paths": "def add_purchase" in source and "def add_transfer" in source,
}
for name, passed in checks.items():
    print(f"{name}={'PASS' if passed else 'FAIL'}")
assert all(checks.values())
print("HOME_UI_V173_TARGETED=PASS")
