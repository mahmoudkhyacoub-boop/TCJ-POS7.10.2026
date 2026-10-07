from pathlib import Path
import ast

source = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
ast.parse(source)
assert "def show_login(self):" in source
assert "def login(self):" in source
assert "slogan_panel = ctk.CTkFrame" in source
assert "monthly_panel = ctk.CTkFrame" in source
assert "category_data" in source
assert "command=self.login" in source
assert 'f_top = ctk.CTkFrame(self.main_view, fg_color="transparent"); f_top.pack(fill="x", padx=20, pady=(10, 15))' not in source
assert 'filter_row = ctk.CTkFrame(self.main_view, fg_color="transparent"); filter_row.pack(fill="x", padx=20, pady=(2, 6))' in source
print("ORIGINAL_V194_LOGIN_LAYOUT=PASS")
print("REPORT_HEADER_SPACER_REMOVED=PASS")
print("LOGIN_FUNCTIONAL_CONTROLS=PASS")
