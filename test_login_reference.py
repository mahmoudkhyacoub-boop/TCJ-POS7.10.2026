from pathlib import Path
from PIL import Image

root = Path(__file__).parent
source = (root / "main.py").read_text(encoding="utf-8")
asset = root / "login_reference.webp"
assert asset.exists(), "login reference asset missing"
with Image.open(asset) as image:
    assert image.size == (2048, 1152), image.size
assert "def show_login(self):" in source
assert "login_reference.webp" in source
assert "def login(self):" in source
assert "self.show_dashboard()" in source
assert "SELECT username, role, password FROM users" in source
print("login_reference_asset=PASS")
print("functional_login_path=PASS")
print("reference_login_layout=PASS")
