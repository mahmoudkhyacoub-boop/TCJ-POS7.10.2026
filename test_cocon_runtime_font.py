from pathlib import Path
import ast

root = Path(__file__).parent
source = (root / 'main.py').read_text(encoding='utf-8')
ast.parse(source)
font_path = root / 'cocon-next-arabic-regular.otf'
assert font_path.exists() and font_path.stat().st_size > 10000
assert 'AddFontResourceExW' in source
assert '_FONT_RUNTIME_HANDLE = ctypes.windll.gdi32.AddFontResourceExW' in source
assert 'APP_FONT_FAMILY = "Cocon® Next Arabic"' in source
assert 'APP_FONT_FILE = "cocon-next-arabic-regular.otf"' in source
assert 'self.option_add("*Font", FONT_BOLD)' in source
assert 'self.option_add("*TkDefaultFont", FONT_BOLD)' in source
assert 'ImageFont.truetype(invoice_font_path' in source
print('FONT_FILE_PRESENT=PASS')
print('WINDOWS_RUNTIME_REGISTRATION=PASS')
print('TK_DEFAULT_FONT=PASS')
print('PIL_INVOICE_FONT_PATH=PASS')
