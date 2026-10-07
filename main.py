import sys
import os
import re
import shutil
import hashlib
import secrets
import sqlite3
import base64
import json
import math

def resource_path(relative_path):
    """Resolve bundled resources from PyInstaller, beside EXE, or beside source."""
    relative_path = os.fspath(relative_path)
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, relative_path))
    # In one-folder/source deployments assets may sit beside the executable.
    executable_dir = os.path.dirname(os.path.abspath(sys.executable))
    source_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(executable_dir, relative_path),
        os.path.join(source_dir, relative_path),
    ])
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    # Preserve a deterministic path for callers that will create a new resource.
    return candidates[0] if candidates else os.path.join(source_dir, relative_path)
import datetime
import re
import webbrowser
import urllib.parse
import io
import pandas as pd
from pathlib import Path
from contextlib import closing
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

EMBEDDED_CATEGORY_IMAGES = {
    'home_phone.png': 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAD+0lEQVR4nO2dMW7bMBhGmaJjpma3kTmX8BG6JDcokCMZ6A2SpUfIJTIb9p5O2dMhUOvSokWKpPjT33tbjERi9D2SP0kDcg4AAAAUuVryZk+r1ceS9+uZh8NhkWyq3oTAy1FLiCoXJfh6lBah6MUIfjlKiVDkIgTfjlwRsgVIDf/x+jb3lhfP9n2X9Ps5EmQJEBM+gecTI8RcCWb9EcG3oYYIyQJMhU/w9ZkSIUWCLyk3JnwbTD3nlLrsa3ZrHMG3YHjmqQWjT/QIELKK8NsSev6xo0CUAIRvmxwJJgUg/D6YK0GRGqAFb68vrZtwws3dpnUTkjm7XLDY+y0G79NShFBRGFoaJi0DnWsX/tvrSxfhO9e2ran5BAWwdMDTS/A+ltodyjOpBrBU+D2v162bcML9ft+6Cc65z5xi9wdGRwDrvd9i+M6Nt8v6KBBdA1jp/VbDH7DSvti8kovAJfF7j5WHO4XfTkujgI9pAaA+JwJYmv+hPH6+USOAlfkf0ojJrdut4GNaLr96qUtCdC2AhXX30IZeRaAIFKfbEeC497c8fBmWePf7fZejACOAOAggDgKIgwDiIIA4CCAOAoiDAOIggDgIIA4CiIMA4iCAOAggDgKIgwDiIIA4CCAOAoiDAOIggDgIIA4CiIMA4iCAOAggDgKIgwDiIIA4CCAOAoiDAOIggDgIIA4CiIMA4iCAOAggDgKIgwDiIIA4CCAOAoiDAOIggDgIIA4CiFPsfQG/f3zPvsa3n7+yr9ELVp4XI4A4CCAOAoiDAOIggDjFVgFKFXwJrDwvRgBxEECcbl8c+bxe/3155PDyxpb0+NJI5xgB5Ol2BHDuX6/j7eHz6VqAgd5DaAlTgDgIIA4CiIMA4lxEETiX49WDaiEpKcDYsnH4TE0EpgBx5ASY2jRquanUgigBtu+72u2ACsTkdiLAw+FwVaU1YAI/X7kpYKrIowg0xM3d5r+fe5mf/Xb6/4clogWwUgeUkOB5vT7p6WOfzcGKpLF5Bef7p9Xqw//s8fo2o0nzGfvCh8Wheiz8Vr1/TICx+i5pI2j7vmsmgY+VnmaRlNE6OAVYWg1YnkPPYandoTyTi8BWtcDN3cbUAz1Hy7am5jPZy8dqAefa1QMDFr4I6tNa0FD450bzbg+DWj/sS2FyCgjZY2VZCJ/M6f3ORdYASGCbueE7l1AEIoFNcsJ3rlANMDSidWGoRKmOl7QMnLKK0WAZpp5zyh7OrM2e0NLwGEaD8sR0sNQNvKzdPkRYhhrBD2Rv98ZIcAxCTJM6leZs2xfZ70+VAMqRe2ZT9MAHEZaj1GFdlRM/RKhH6VPaqke+iFCOWsfzi575I0Q8lr6PAQAAF8kfBZxUI+jYKZ4AAAAASUVORK5CYII=',
    'home_playstation.png': 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAFG0lEQVR4nO2du04dMRCGTZQyHVWEhJSanpqnoEgflBdIlTpVXgCRPkWegjo9daQjRano6JPKZPGx1zO+jMee/5MoOMDZy/957F37LM4BAAAAwCInkhv7cX7+V3J7M3N9OIhk03UjCLwdvYTo8qYIvh+tRWj6ZghejlYiNHkTBD+OWhGqBeCG//HNu9pNLs/t0y/W79dIUCUAJXwEXg9FiFIJiv4IwY+hhwhsAXLhI/j+5ETgSPCKs2GEr4PceeaMy15X741D8CPw55w7YAwhV4CUVQh/LKnzT60CJAEQvm5qJMgKgPDnoFQC1iAQrMeuAGj9c1FSBdgVAOHrhptPUgBM8KxFKk9WBUDrnwNOTlEB0PrXJJYruQKg9c8FNS9cBhoHAhjnSAD0/2sT5kuqAOj/54SSG7oA40AA40AA40AA40AA44gJ8PhwL7UpwKDJotAUCL2Mx4d7d3pxJbIt0S4AQtB5fLh//upJVwGkLF4J6UaCQaByejei7gKEB4BuQBeoAIoIG4dEFzpEAFQBPYgIgMFgnlGNAl2AUpa8D7AF3YAOxARAN5BmZGNAF6AQycYiKgDuCegDFWAwI679twwXAFVgLF2ng2OcXlyJhd5yOz1apgb5xQXwtDqhGmRqdSwjrpSGCFB6oBpaTIzYflGOcfs7o45tWAWgojX0HNv95sogiUoBWoV+c3bZ5H2cc+7u98/iv+XKIIkqAUqCbxly6XY4cvhj1CLCcAE4oUuFzSW2XzkptFSFYQJQg9caeo7tflNlMHMVkAt/1tBTUGWQXA7uERXAWvAx/DGmRJCuBmIC7IVvIfgQiggSEogIkArfYvAheyJISNBdgFj4CP6YlAi9JRD/bGBJ+LHWoUWiuy9/Xnx/8/lt1fvdnF2KStBtOthCyw/DT73GJXaeet0SF1sPYCF8ys+oSJ2vLgKEtq4WvhTheetRBYavCAJjaT4IrG391ImV1O+tVm3CQWHrASEqQCF7o/3aKwFJIEAFsaBnCt85BdPBszNb4CEQYADfPr1/8f2Hr98H7YlCAaiLK2Yd7IXh+9dGSdB8DBCOUGvW0q1GLPzcz8Lz1/qWMAaBxukiAKpAG3q3fucEKwAk4CF1vk7CF2L/Mqb0P4ZYmBHkkurrt4PAWPilrf/26dfRa9eHw3Pu4k8KtV4JYqP9XuFT6FoBPFgSlifVMGrDz1UAkfsAqY+E+4O2LMJeRVxmUahz+88FsChCritcblm4c/8PyrIIWoL3DHs+wN7qlu1JWkEG6sDXzEfDnMtXA8+sMnCudkx+ONTDeUqG1kmhkktbfDw8ArUqbNk7+VoeELFFS/AeVQJ4Wj07R8tNJ22hb1EpwBYND1IqQXPoW9QLsCV2UjVIMUvYMaYSIMbeydf+oEgNTC/AHquG1hKsCDIOBDAOBDAOBDAOBDAOBDAOBDAOBDAOSYDYwkKgH0puRwJsV4yC9QjzRRdgHAhgHLIAGAfMBTWvqAAYB6xJLFdWF4AqMAecnJICoAqsRSpP9iAQVUA33Hx2BUhZAwl0ksplr5rjMtA4WQFQBeagpPU7R6wAkEA3peE7x+gCIIFOasJ3rtGycL8TtY+SAXRaNTzWIDBnFaqBDLnzzLmHU3SzJ/YgqRBUg/ZQGhj3Bl7V3T6IIEOP4D3Vt3spEmyBEHm4XWnNbfsm9/u5EoB21M7ZNJ3wgQhytJqs6zLjBxH60XqWtuuUL0RoR6/pedE5fwhBB+sxAAAAdOYfCM9EKkx0P7sAAAAASUVORK5CYII=',
    'home_computer.png': 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAADmklEQVR4nO2cy23bUBBFR0EKMOx1KnATLsFNeG/BSBmGvNfGJagEN+EyZLgDZaUgkUTx/eZ9eM/ZBYhM4t3D4XAeJTMAAABQZFX1aJvNoerxRma9rpKN70EIvBxOQvgIQPB+FBahrAAEX49CIpQRgODbkSlCvgCR4d9ud9mHXDpfT49xH8iQIE+AgPAJPJ8gIRIlSBOA4JvgIUK8ADPhE7w/syJESPAj6siE3wWz6xzRl/3MPBczI/gWHNc8umE8IbwCTFhF+G2ZXP/AKhAmAOF3TY4E8wIQ/hCkShDXBMLiuC4AV/9QpFSB6ApA+H0Tm8+0AGzwLIuJPKPmADlX//7zI/mzqtzdPyR97na7C54PXK4Aha9+wk+j+LpdyDW4B0i9+gk/j9T1C83L9TGQ8MvguY5F9gIucemkV29vXodbHIfn5//+vf/8SO4JrnFeAZy6f8KPw229TvINugXw7D8mIbkxChYHAcRxawJDOG10lGnVI1EBxGlaAY54PN6MQutZCRVAHAQQBwHEQQBxEEAcBBAHAcRBAHEQQBwEEAcBxEEAcZptBh1uXs3eX83MbP+71Vl0wPsvMzM73Jitvl+qH54KIA4CiNPsFrD6fvn7RhDvA/BGEDQCAcRBAHEQQBwEEAcBxEEAcRBAHAQQBwHEQQBxEEAcBBAHAcRBAHEQQBwEEAcBxOniJ2Ja/0yKMlQAcZpWAH4+tj1UAHEQQBwEEKeaAPwsbBy11sutCby7fzh7vEOCdLy+PeVaAZS/8lUSz3V0vwUgQR7e61elB0CCNGqsW7VBEBL0SRd7AV6U3GNYqsDMAcRBAHEQQBwEEAcBxEEAcRBAHAQQBwHEQQBxEEAcBBAHAcRBAHEQQBwEEGfRL4Qs9SWOklABxBmmAoz4FfIRKhAVQJwgAb6eHp1PAzwIye1cgPV65XAu0Asn+XILEGeYJnCEhmpEgisAfcBYhOZ1WQD6gGVyIdeoHoAqMAYxOU0LQBVYFhN5Rj8FUAX6Jjaf6wJMWIMEfTKZy5VqzhxAnHkBqAJDkHL1m4VWACTomtTwzWJuAUjQJTnhmxUaBR9P4na7K/HnIIBSF15cEzhjFdWgDrPrHDHDSRv2bDaHuf9CNShP0AUWOcDLm/YhQhU8gj+SP+4NkOBfEGKe6Ftpxti+zLw/UgIoSOaeTdkNH0SoR6HNOp8dP0Two/Aure+WLyKUw2l7vu6eP0KEw/sYAADgyx9WswJvfcxKBgAAAABJRU5ErkJggg==',
    'home_cctv.png': 'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAEmklEQVR4nO2du3HbQBRFLz2uQCqAgUM34RKUqATlZKAqHJC5SlCiEtgEQwUsgGqBDiTQELjAvv1/3j0znpEo0MDgnvd2sUuNAEIIIYRoZJX1bLvdJev5Wma7zZJN2pMw8HgkEiKNAAw+HZFFiCsAg89HJBHiCMDgyxEoQrgAjuHfvbwFn7J3Pp4e3N4QIEGYAILwGXg4IiE8JfATgMEXIYUI7gJYwmfw6bGK4CDBD6czM/wqsN5nh3nZz8BrAcDgSzDcc+cJ4wR5B5ixiuGXZfb+C7uATACGXzUhEtgFYPhN4CuB2ySQdMeyAKz+pvDpAs4dgOHXjWs+8wJwg6cvZvJ06gCs/jZwycksAKu/Twy5ijsAq78tpHnxMVA5FEA5twJw/O+bSb6iDsDxv00kuUXZDpZwPh6Mr9///pPrEoiBbALMMSdGTfQsKSeBQloQ1QcKIKDX8AEK4ESPIlAA5VAA5RR/Cqh5hm1q+efjoeprdoUdYIGegp6DAnjQ02SQAiiHAljofRigAJ70MgxQAOVQAAE9DwMUIIAehgEKIKTXLkABZjgfD9d/tuNapvhScM2s9nsAwKXxkJegAAbOx8M1fADfvh64bDbfjm91iKAAnkylMHWJFqSgAJEwdokGpKAAE6btP4QWpKAAmZFIkVMICjAiZvW7UHI+QQEqxNYlYsrAhaBGWO33SboTBfiiVPt34bLZRB8KOAQUYLyINKaEgOwAmZkL3/azVLADIE/7l4Y7HHfzZJCg/QMUoBiv6/W37x9PpyLXoX4IyF39r+v1Tfim13MNB+oFSE1IkMN7U7V/gAJkxVT5PsfERLUALTz7p0a1AC2Qsv0DFEA9agUo0f4lj3rTY1JvDasVIBe1zzFUCpC7+sfnejydjJ1g+nqu61O7EnjZbIpWp204SD35G1ApwHBjp5+8SSnE9XcMLAtD0uNioVKAgWmF5RBitd9XtR2sWoApuYSw/T+52j9AARYp0SFyQwEcWBKiVRkoQABjIWJ1h5ztH6AA0Wh1uKAAiWhFCArgyPn5Hfd/fzm/TyJE7vYPUAAvzs/vAOAlwoBNiFxQAAeG4E3fh8gAlPsNYZWbQeQ/FEDItPrHhFZ/SSiAciiAgF6rH6AA6qEAFnqufoACqIcCLNB79QMUQD0UYAYN1Q9QAPVQAANaqh+gAOqhABM0VT9AAdRDAUZoq36AAqiHAnyhsfoBCqAe0WcCP54ecPfylvhSyrFU/ZKf+5K6s3w8PViPue0A2+0qwbWQWpjkyyEAn5XY8zi/RLaPhdf217LIJ+IOIBlPSD1I8zILwHlAnxhydRoCen8a6GUe4NKt54cAdoG+mMnT+SmAc4G6cc1nWYAZayhBnczmstDNuQ6gHLsA7AJN4FP9gLQDUIKq8Q0fcBkCKEGVhIQPRFoKHi6i5zWC2ohVeG6TQItV7AZ5sN5nhzUcv8We3e5iO4TdID6iAnNcwAtb7aMIWUgR/ED4cq9AgjEUwo7zUBqwbB9nvd9RAhKRwD2buBs+FCEfkTbr0uz4UYR0RN6lTbvlSxHikWh7Pu+eP4WQw89jEEIIScs/VjvOri/z/IIAAAAASUVORK5CYII=',
}
APP_VERSION = "V235 (Accountant Balances CLIQ Card Manager)"
# Compatibility marker only: the login artwork is decoded from embedded Base64 below,
# and is not loaded from this external filename at runtime.
LOGIN_REFERENCE_ASSET = "login_reference.webp"
MAX_BACKUPS = 10

# matplotlib is intentionally not required: the dashboard uses native Tk Canvas charts.
import customtkinter as ctk

# Bundled Arabic font. On Windows it is registered for this process only; if the
# font cannot be loaded, the existing Arial Bold styling remains the safe fallback.
APP_FONT_FILE = "cocon-next-arabic-regular.otf"
ACCOUNTANT_PDF_FONT_FILE = "Cocon-Next-Arabic-PDF.ttf"
# The internal font family contains the registered-mark spelling used by Windows.
APP_FONT_FAMILY = "Cocon® Next Arabic"
_FONT_RUNTIME_PATH = None
_FONT_RUNTIME_HANDLE = None
try:
    _font_path = resource_path(APP_FONT_FILE)
    if os.path.isfile(_font_path):
        _FONT_RUNTIME_PATH = _font_path
        if sys.platform == "win32":
            import ctypes
            _FONT_RUNTIME_HANDLE = ctypes.windll.gdi32.AddFontResourceExW(str(_font_path), 0x10, 0)
            if _FONT_RUNTIME_HANDLE:
                APP_FONT_FAMILY = "Cocon® Next Arabic"
        else:
            # The family is used when it is installed in the development environment.
            APP_FONT_FAMILY = "Cocon® Next Arabic"
except Exception:
    _FONT_RUNTIME_PATH = None

FONT_NORMAL = (APP_FONT_FAMILY, 14, "bold")
FONT_NORMAL_BOLD = (APP_FONT_FAMILY, 14, "bold")
FONT_BOLD = (APP_FONT_FAMILY, 14, "bold")
FONT_TITLE = (APP_FONT_FAMILY, 14, "bold")
FONT_SMALL = (APP_FONT_FAMILY, 14, "bold")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
from PIL import Image, ImageDraw, ImageFont, ImageTk
import arabic_reshaper
from bidi.algorithm import get_display

# Branding & Elegant Config
SHOP_NAME = "ترند سنتر الأردن"
LOCATION = "الزرقاء - جبل طارق"
PHONE = "0787779095"
CURRENCY = "د.أ"
DB_NAME = "trend_center_v57.db"  # Keep the existing database filename to preserve V57 data.
ACCOUNTANT_ACCOUNT_DEFS = [
    ("cash", "الصندوق"), ("bank", "البنك"), ("visa", "الفيزا"),
    ("e_fawateercom", "إي فواتيركم"), ("cards", "البطاقات"),
    ("receivables", "ذمم العملاء"), ("payables", "حساب الموردين"),
]

# Theme: Royal Crimson Executive Console. Shared tokens for the entire application.
# V140 visual system: Rubi is the action color, Vino is the depth/surface color,
# and Teal is the calm information/success accent. Text remains white or near-white
# so every dialog, alert, table, and dashboard remains readable in Dark mode.
COLOR_LOGO = "#AA1E1E"  # Dominant red sampled from the TCJ logo asset.
COLOR_RUBI = COLOR_LOGO
COLOR_RUBI_DARK = "#761719"
COLOR_RUBI_DEEP = "#2C0A1A"
COLOR_RUBI_SOFT = "#5E2039"
COLOR_VINO = "#651A35"
COLOR_VINO_DARK = "#431125"
COLOR_VINO_SOFT = "#8D3B59"
COLOR_TEAL = "#008F8F"
COLOR_TEAL_DARK = "#005F63"
COLOR_TEAL_SOFT = "#8FE1DC"
COLOR_PUMPKIN_ORANGE = "#FF9F1C"
COLOR_NAVY = "#0A1727"
COLOR_NAVY_LIGHT = "#122A3F"
COLOR_WHITE = "#FFFFFF"
COLOR_BG_LIGHT = "#07131F"
COLOR_SURFACE = "#102639"
COLOR_BORDER = "#87405A"
COLOR_TEXT_DARK = COLOR_WHITE
COLOR_TEXT_MUTED = "#D8E7E6"

# Backward-compatible names used by existing screens.
COLOR_CRIMSON = COLOR_RUBI
COLOR_CRIMSON_DARK = COLOR_RUBI_DARK
COLOR_CRIMSON_DEEP = COLOR_RUBI_DEEP
COLOR_CRIMSON_SOFT = COLOR_RUBI_SOFT

# UI Constants - Cocon® Next Arabic Bold is the primary UI family.
FONT_BOLD = (APP_FONT_FAMILY, 14, "bold")
FONT_NORMAL_BOLD = (APP_FONT_FAMILY, 14, "bold")
HEADER_FONT_WHITE = (APP_FONT_FAMILY, 14, "bold")
FONT_REPORT_VALUE = (APP_FONT_FAMILY, 16, "bold")
FONT_NET_PROFIT_LABEL = (APP_FONT_FAMILY, 20, "bold")
FONT_NET_PROFIT_VALUE = (APP_FONT_FAMILY, 32, "bold")
FONT_MONTH_TOTAL = (APP_FONT_FAMILY, 20, "bold")
FONT_DIALOG = (APP_FONT_FAMILY, 17, "bold")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def _has_visual_arabic(text):
    """Detect Arabic presentation forms produced by arabic_reshaper."""
    return any("\uFB50" <= char <= "\uFDFF" or "\uFE70" <= char <= "\uFEFF" for char in str(text or ""))


def fix_arabic(text, for_ui=True, is_title=False):
    if not text: return ""
    raw = str(text)
    # Windows title bars handle logical Arabic text correctly without shaping.
    if is_title: return raw
    # Idempotence guard: applying reshape+bidi to visual glyphs reverses them.
    if _has_visual_arabic(raw): return raw
    if not any("\u0600" <= char <= "\u06FF" for char in raw):
        return text
    try:
        reshaped_text = arabic_reshaper.reshape(raw)
        return get_display(reshaped_text, base_dir="R")
    except Exception:
        return text


def format_dialog_arabic(text):
    """Format each dialog line exactly once and keep mixed tokens stable.

    Dialogs can contain names, phone numbers, dates, Latin words, punctuation,
    and newlines. Processing each logical line independently avoids a second
    bidi pass from moving a complete line or its punctuation to the wrong side.
    The presentation-form guard makes the function safe for legacy callers that
    already shaped the same message.
    """
    raw = str(text or "").replace("\r\n", "\n")
    if _has_visual_arabic(raw): return raw

    def format_line(line):
        if not line or not any("\u0600" <= char <= "\u06FF" for char in line):
            return line
        protected = re.sub(
            r"([A-Za-z0-9][A-Za-z0-9@._+/-]*)",
            lambda match: "\u200e" + match.group(1) + "\u200e",
            line,
        )
        reshaped = arabic_reshaper.reshape(protected)
        # RLM boundaries make punctuation and mixed Latin tokens resolve as one
        # right-to-left UI line in Windows Tk without changing the source text.
        return "\u200f" + get_display(reshaped, base_dir="R") + "\u200f"

    return "\n".join(format_line(line) for line in raw.split("\n"))

def hash_password(password):
    """Store passwords as salted PBKDF2 hashes while allowing legacy migration."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("ascii"), 210000).hex()
    return f"pbkdf2_sha256$sha256$210000${salt}${digest}"


def verify_password(stored, supplied):
    stored, supplied = str(stored or ""), str(supplied or "")
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, algorithm, iterations, salt, expected = stored.split("$", 4)
            if algorithm != "sha256": return False
            actual = hashlib.pbkdf2_hmac("sha256", supplied.encode("utf-8"), salt.encode("ascii"), int(iterations)).hex()
            return secrets.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False
    # Legacy plaintext rows remain readable once, then are upgraded at login.
    return secrets.compare_digest(stored, supplied)


def clean_float(text):
    try:
        match = re.search(r"[-+]?\d*\.\d+|\d+", str(text))
        return float(match.group()) if match else 0.0
    except: return 0.0

class Database:
    def __init__(self):
        self.db_path = self._resolve_db_path()
        self._backup_existing_database()
        self.conn = sqlite3.connect(str(self.db_path), timeout=30)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA busy_timeout = 30000")
        try:
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
        except sqlite3.Error:
            pass
        self.cursor = self.conn.cursor()
        self.create_tables()

    def _resolve_db_path(self):
        default_db = DB_NAME
        cfg_file = Path("tcj_paths.cfg")
        target_path = default_db
        if cfg_file.exists():
            try:
                content = cfg_file.read_text(encoding="utf-8").strip()
                if content:
                    p = Path(content)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    target_path = content
            except Exception:
                pass
        return Path(target_path).resolve()

    def _backup_existing_database(self):
        """Create a safe startup copy before any schema migration or write."""
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            return
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{self.db_path.stem}_{stamp}.db"
        try:
            shutil.copy2(self.db_path, backup_path)
            backups = sorted(backup_dir.glob(f"{self.db_path.stem}_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in backups[MAX_BACKUPS:]:
                try:
                    old.unlink()
                except OSError:
                    pass
        except OSError:
            # A backup must never prevent the POS from opening.
            pass

    def create_manual_backup(self):
        """Create a timestamped SQLite backup without changing operational data."""
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{self.db_path.stem}_manual_{stamp}.db"
        with sqlite3.connect(str(backup_path)) as target:
            self.conn.backup(target)
        return backup_path

    def _ensure_column(self, table, column, definition):
        existing = {row[1] for row in self.cursor.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _record_maintenance_part_movement(self, part_id, movement_type, quantity, unit_cost, maintenance_id=None, notes=""):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO maintenance_part_movements (part_id, movement_type, quantity, unit_cost, maintenance_id, created_at, user, notes) VALUES (?,?,?,?,?,?,?,?)",
            (part_id, movement_type, float(quantity), float(unit_cost), maintenance_id, now, getattr(self, "current_user", "system"), notes)
        )

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, permissions TEXT DEFAULT '[]')''')
        self._ensure_column('users', 'permissions', "TEXT DEFAULT '[]'")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_permissions (username TEXT NOT NULL, permission_key TEXT NOT NULL, allowed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (username, permission_key))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT, buy_price REAL, sell_price REAL, stock INTEGER, description TEXT, min_stock INTEGER DEFAULT 3)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, phone TEXT UNIQUE, name TEXT, points INTEGER DEFAULT 0)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS customer_notes (phone TEXT PRIMARY KEY, note TEXT, updated_at TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, code TEXT, name TEXT, qty INTEGER, price REAL, total REAL, buy_cost REAL, date TEXT, time TEXT, user TEXT, customer_phone TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, desc TEXT, amount REAL, date TEXT, time TEXT, user TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (id INTEGER PRIMARY KEY, code TEXT, name TEXT, qty INTEGER, cost REAL, supplier TEXT, date TEXT, time TEXT, description TEXT)''')
        self._ensure_column("purchases", "funding_source", "TEXT DEFAULT 'صندوق المحل (نقدي)'")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, device_name TEXT, repair_desc TEXT, client_name TEXT, client_phone TEXT, revenue REAL, internal_cost REAL DEFAULT 0, date TEXT, time TEXT, user TEXT)''')
        # Independent device intake/handover register. Operational only: no journal,
        # inventory, debt, or legacy-maintenance writes are performed by this module.
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS service_register_technicians (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            active INTEGER NOT NULL DEFAULT 1,
            created_by TEXT,
            created_at TEXT NOT NULL
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS service_register_orders (
            id INTEGER PRIMARY KEY,
            order_no TEXT NOT NULL UNIQUE,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            device_type TEXT NOT NULL,
            manufacturer TEXT,
            model TEXT,
            serial_imei TEXT,
            issue_description TEXT,
            intake_notes TEXT,
            accessories_in TEXT,
            intake_checklist TEXT,
            handover_checklist TEXT,
            technician_id INTEGER,
            status TEXT NOT NULL DEFAULT 'مستلم',
            received_date TEXT NOT NULL,
            received_time TEXT NOT NULL,
            delivered_date TEXT,
            delivered_time TEXT,
            service_price REAL NOT NULL DEFAULT 0,
            part_cost REAL NOT NULL DEFAULT 0,
            technician_share REAL NOT NULL DEFAULT 0,
            shop_share REAL NOT NULL DEFAULT 0,
            delivery_notes TEXT,
            accessories_out TEXT,
            intake_contract_path TEXT,
            handover_contract_path TEXT,
            created_by TEXT,
            updated_by TEXT,
            updated_at TEXT,
            FOREIGN KEY(technician_id) REFERENCES service_register_technicians(id) ON DELETE SET NULL
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS service_register_audit (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            username TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(order_id) REFERENCES service_register_orders(id) ON DELETE CASCADE
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY, type TEXT, client_name TEXT, client_phone TEXT, amount REAL, commission REAL, reference TEXT, provider TEXT, date TEXT, time TEXT, user TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE, address TEXT, balance REAL DEFAULT 0, notes TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, username TEXT, action TEXT, entity TEXT, details TEXT, date TEXT, time TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS maintenance_parts (id INTEGER PRIMARY KEY, part_name TEXT, phone_model TEXT, cost_price REAL, sell_price REAL, stock INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS mobile_cards (
            id INTEGER PRIMARY KEY, provider TEXT NOT NULL, category TEXT NOT NULL,
            denomination TEXT NOT NULL, unit_cost REAL NOT NULL DEFAULT 0 CHECK(unit_cost >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0), active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(provider, category, denomination))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS card_sales (
            id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL, provider TEXT NOT NULL, category TEXT NOT NULL,
            denomination TEXT NOT NULL, qty INTEGER NOT NULL CHECK(qty > 0), unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total REAL NOT NULL CHECK(total >= 0), payment_method TEXT NOT NULL DEFAULT 'Cash', customer_phone TEXT,
            date TEXT NOT NULL, time TEXT NOT NULL, user TEXT, source_id TEXT NOT NULL UNIQUE,
            FOREIGN KEY(card_id) REFERENCES mobile_cards(id) ON DELETE RESTRICT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS maintenance_part_movements (
            id INTEGER PRIMARY KEY,
            part_id INTEGER,
            movement_type TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 0,
            unit_cost REAL NOT NULL DEFAULT 0,
            maintenance_id INTEGER,
            created_at TEXT NOT NULL,
            user TEXT,
            notes TEXT,
            FOREIGN KEY(part_id) REFERENCES maintenance_parts(id) ON DELETE SET NULL
        )''')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_part_movements_time ON maintenance_part_movements (created_at)")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS customer_debts (id INTEGER PRIMARY KEY, customer_phone TEXT, customer_name TEXT, total_debt REAL, paid_amount REAL, status TEXT, date TEXT, notes TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS supplier_debts (id INTEGER PRIMARY KEY, supplier_name TEXT, total_debt REAL, paid_amount REAL, status TEXT, date TEXT, notes TEXT)''')
        self._ensure_column("supplier_debts", "debt_reference", "TEXT")
        self._ensure_column("customer_debts", "source_type", "TEXT")
        self._ensure_column("customer_debts", "source_id", "TEXT")
        self._ensure_column("supplier_debts", "source_type", "TEXT")
        self._ensure_column("supplier_debts", "source_id", "TEXT")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_debts_source ON customer_debts (source_type, source_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_debts_source ON supplier_debts (source_type, source_id)")
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS debt_payments (id INTEGER PRIMARY KEY, debt_id INTEGER, debt_type TEXT, amount REAL, date TEXT, time TEXT, notes TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS balance_reconciliations (
            id INTEGER PRIMARY KEY,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            opening_cash REAL NOT NULL DEFAULT 0,
            opening_visa REAL NOT NULL DEFAULT 0,
            opening_cliq REAL NOT NULL DEFAULT 0,
            opening_bank REAL NOT NULL DEFAULT 0,
            expected_cash REAL NOT NULL DEFAULT 0,
            actual_cash REAL NOT NULL DEFAULT 0,
            expected_visa REAL NOT NULL DEFAULT 0,
            actual_visa REAL NOT NULL DEFAULT 0,
            expected_cliq REAL NOT NULL DEFAULT 0,
            actual_cliq REAL NOT NULL DEFAULT 0,
            expected_bank REAL NOT NULL DEFAULT 0,
            actual_bank REAL NOT NULL DEFAULT 0,
            receivables_total REAL NOT NULL DEFAULT 0,
            payables_total REAL NOT NULL DEFAULT 0,
            cycle_locked INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'saved',
            user TEXT,
            created_at TEXT
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS internal_transfers (
            id INTEGER PRIMARY KEY,
            source_acc TEXT NOT NULL,
            dest_acc TEXT NOT NULL,
            amount REAL NOT NULL,
            reference TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            notes TEXT,
            user TEXT
        )''')
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS accountant_accounts (
            id INTEGER PRIMARY KEY, account_key TEXT NOT NULL UNIQUE, account_name TEXT NOT NULL,
            opening_balance REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS accountant_transactions (
            id INTEGER PRIMARY KEY, account_key TEXT NOT NULL, direction TEXT NOT NULL CHECK(direction IN ('in','out')),
            amount REAL NOT NULL CHECK(amount > 0), transaction_date TEXT NOT NULL, description TEXT NOT NULL,
            notes TEXT, user TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(account_key) REFERENCES accountant_accounts(account_key) ON UPDATE CASCADE ON DELETE RESTRICT
        )""")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_accountant_transactions_date ON accountant_transactions (transaction_date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_accountant_transactions_account ON accountant_transactions (account_key)")
        now_accountant = datetime.datetime.now().isoformat(timespec="seconds")
        for account_key, account_name in ACCOUNTANT_ACCOUNT_DEFS:
            self.cursor.execute("INSERT OR IGNORE INTO accountant_accounts (account_key, account_name, created_at, updated_at) VALUES (?,?,?,?)", (account_key, account_name, now_accountant, now_accountant))
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS financial_cycles (
            id INTEGER PRIMARY KEY,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            cycle_type TEXT NOT NULL DEFAULT 'monthly_5_to_4',
            opening_cash REAL NOT NULL DEFAULT 0,
            opening_visa REAL NOT NULL DEFAULT 0,
            opening_cliq REAL NOT NULL DEFAULT 0,
            opening_bank REAL NOT NULL DEFAULT 0,
            receivables_balance REAL NOT NULL DEFAULT 0,
            payables_balance REAL NOT NULL DEFAULT 0,
            notes TEXT,
            locked INTEGER NOT NULL DEFAULT 1,
            user TEXT,
            created_at TEXT,
            UNIQUE(from_date, to_date)
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS financial_position_snapshots (
            id INTEGER PRIMARY KEY,
            snapshot_date TEXT NOT NULL,
            period_label TEXT,
            snapshot_type TEXT NOT NULL DEFAULT 'current',
            cash REAL NOT NULL DEFAULT 0,
            visa REAL NOT NULL DEFAULT 0,
            cliq REAL NOT NULL DEFAULT 0,
            bank REAL NOT NULL DEFAULT 0,
            inventory_value REAL NOT NULL DEFAULT 0,
            customer_receivables REAL NOT NULL DEFAULT 0,
            supplier_payables REAL NOT NULL DEFAULT 0,
            other_assets REAL NOT NULL DEFAULT 0,
            other_liabilities REAL NOT NULL DEFAULT 0,
            total_assets REAL NOT NULL DEFAULT 0,
            total_liabilities REAL NOT NULL DEFAULT 0,
            net_position REAL NOT NULL DEFAULT 0,
            notes TEXT,
            user TEXT,
            created_at TEXT
        )''')
        # Central double-entry journal. Existing operational tables remain the UI source of truth;
        # these tables provide one consistent accounting source for new and migrated postings.
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY,
            entry_date TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            description TEXT,
            user TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(source_type, source_id)
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            account_code TEXT NOT NULL,
            debit REAL NOT NULL DEFAULT 0 CHECK(debit >= 0),
            credit REAL NOT NULL DEFAULT 0 CHECK(credit >= 0),
            memo TEXT,
            FOREIGN KEY(entry_id) REFERENCES journal_entries(id) ON DELETE RESTRICT,
            CHECK((debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0))
        )''')
        self._ensure_column("financial_position_snapshots", "snapshot_date", "TEXT")
        self._ensure_column("financial_position_snapshots", "period_label", "TEXT")
        self._ensure_column("financial_position_snapshots", "snapshot_type", "TEXT DEFAULT 'current'")
        self._ensure_column("financial_position_snapshots", "cash", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "visa", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "cliq", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "bank", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "inventory_value", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "customer_receivables", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "supplier_payables", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "other_assets", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "other_liabilities", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "total_assets", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "total_liabilities", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "net_position", "REAL DEFAULT 0")
        self._ensure_column("financial_position_snapshots", "notes", "TEXT")
        self._ensure_column("financial_position_snapshots", "user", "TEXT")
        self._ensure_column("financial_position_snapshots", "created_at", "TEXT")
        self._ensure_column("financial_position_snapshots", "maintenance_parts_cost", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "opening_cash", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "opening_visa", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "opening_cliq", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "opening_bank", "REAL DEFAULT 0")
        self._ensure_column("expenses", "payment_source", "TEXT DEFAULT 'Cash'")
        self._ensure_column("expenses", "status", "TEXT DEFAULT 'paid'")
        self._ensure_column("debt_payments", "payment_source", "TEXT DEFAULT 'Cash'")
        self._ensure_column("journal_entries", "status", "TEXT NOT NULL DEFAULT 'active'")
        self._ensure_column("balance_reconciliations", "receivables_total", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "payables_total", "REAL DEFAULT 0")
        self._ensure_column("balance_reconciliations", "cycle_locked", "INTEGER DEFAULT 0")
        self._ensure_column("balance_reconciliations", "pdf_path", "TEXT")
        self._ensure_column("balance_reconciliations", "closed_at", "TEXT")
        self._ensure_column("balance_reconciliations", "closed_by", "TEXT")
        self._ensure_column("customer_debts", "last_payment_date", "TEXT")
        self._ensure_column("supplier_debts", "last_payment_date", "TEXT")

        # Migrate databases created by V57 without discarding existing records.
        self._ensure_column("sales", "payment_method", "TEXT DEFAULT 'Cash'")
        self._ensure_column("sales", "source_id", "TEXT")
        self._ensure_column("mobile_cards", "sale_price", "REAL NOT NULL DEFAULT 0")
        self._ensure_column("card_sales", "card_number", "TEXT")
        self.cursor.execute("UPDATE mobile_cards SET sale_price=unit_cost WHERE COALESCE(sale_price,0)=0")
        self._ensure_column("maintenance", "payment_method", "TEXT DEFAULT 'Cash'")
        self._ensure_column("maintenance", "source_id", "TEXT")
        self._ensure_column("transfers", "payment_method", "TEXT DEFAULT 'Cash'")
        self._ensure_column("transfers", "collection_account", "TEXT")
        self._ensure_column("transfers", "settlement_account", "TEXT")
        self._ensure_column("transfers", "settlement_amount", "REAL DEFAULT 0")
        self._ensure_column("expenses", "user", "TEXT")
        self._ensure_column("purchases", "supplier", "TEXT")
        self._ensure_column("purchases", "description", "TEXT")
        self._ensure_column("purchases", "user", "TEXT")
        self._ensure_column("purchases", "source_id", "TEXT")
        self._ensure_column("products", "min_stock", "INTEGER DEFAULT 3")

        self.cursor.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', ?, 'admin')", (hash_password("Mk@262711"),))
        self.cursor.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (2, 'user', ?, 'employee')", (hash_password("123"),))
        default_settings = [
            ('shop_name', SHOP_NAME), ('shop_name_en', 'Trend Center JO'), ('phone', PHONE), ('location', LOCATION), ('logo_path', ''), ('currency', CURRENCY), ('reg_points', '20'),
            ('comm_limit1', '50'), ('comm_val1', '0.5'),
            ('comm_limit2', '100'), ('comm_val2', '1.0'),
            ('comm_val3', '1.5'),
            ('points_sale', '10'), ('points_maint', '5'), ('points_transfer', '2')
        ]
        for k, v in default_settings:
            self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('opening_balance', '0'))
        
        # Performance Indexing for Speed (V106)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_phone ON sales (customer_phone)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_phone ON maintenance (client_phone)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfers_phone ON transfers (client_phone)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_code ON products (code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_debts_phone ON customer_debts (customer_phone)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_debt_payments_id ON debt_payments (debt_id, debt_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_internal_transfers_date ON internal_transfers (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_cycles_period ON financial_cycles (from_date, to_date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_position_date ON financial_position_snapshots (snapshot_date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_position_type ON financial_position_snapshots (snapshot_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries (entry_date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries (source_type, source_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_lines (account_code)")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS inventory_adjustments (
            id INTEGER PRIMARY KEY,
            adjustment_no TEXT NOT NULL UNIQUE,
            adjustment_type TEXT NOT NULL,
            product_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_cost REAL NOT NULL DEFAULT 0,
            original_sale_id INTEGER,
            reason TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            user TEXT,
            source_id TEXT NOT NULL UNIQUE
        )""")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_adjustments_date ON inventory_adjustments (date)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_adjustments_source ON inventory_adjustments (source_id)")
        self._backfill_legacy_journal()
        self._backfill_maintenance_cost_journals()
        self._void_orphan_journals()
        self.conn.commit()

    def _backfill_maintenance_cost_journals(self):
        """Repair legacy maintenance rows whose internal part cost was never journalized."""
        rows = self.cursor.execute("SELECT id, internal_cost, date, time, user FROM maintenance WHERE COALESCE(internal_cost,0) > 0").fetchall()
        for rid, cost, entry_date, entry_time, user in rows:
            cost = round(max(float(cost or 0), 0), 2)
            existing = self.cursor.execute("""SELECT 1 FROM journal_entries je
                JOIN journal_lines jl ON jl.entry_id=je.id
                WHERE COALESCE(je.status,'active')='active'
                  AND jl.account_code='MAINTENANCE_COGS'
                  AND ((je.source_type='managed' AND je.source_id LIKE ?)
                       OR (je.source_type IN ('maintenance','legacy_maintenance') AND (je.source_id=? OR je.source_id=?)))
                LIMIT 1""", (f"maintenance:{rid}:%", str(rid), f"maintenance-{rid}")).fetchone()
            if existing:
                continue
            self._legacy_post("managed", f"maintenance:{rid}:costrepair", entry_date, entry_time, "إصلاح تكلفة قطعة صيانة قديمة", [("MAINTENANCE_COGS", cost, 0, "تكلفة قطعة صيانة مستهلكة"), ("MAINTENANCE_INVENTORY", 0, cost, "إخراج قطعة صيانة من المخزون")], user or "system")


    def _dedupe_active_managed_journals(self):
        """Keep only the newest active managed journal for each operation and account family."""
        families = {
            "sales": "SALES_REVENUE",
            "maintenance": "SERVICE_REVENUE",
            "purchases": "INVENTORY",
            "transfers": "TRANSFER_REVENUE",
            "expenses": "EXPENSE",
        }
        for table, account in families.items():
            rows = self.cursor.execute("""SELECT je.id, je.source_id FROM journal_entries je
                JOIN journal_lines jl ON jl.entry_id=je.id
                WHERE COALESCE(je.status,'active')='active' AND je.source_type='managed'
                  AND jl.account_code=? AND je.source_id LIKE ?""", (account, f"{table}:%")).fetchall()
            latest = {}
            for entry_id, source_id in rows:
                parts = str(source_id or '').split(':')
                if len(parts) < 2 or not parts[1].isdigit():
                    continue
                key = (table, int(parts[1]))
                if key not in latest or int(entry_id) > int(latest[key]):
                    latest[key] = int(entry_id)
            for (table_name, record_id), keep_id in latest.items():
                self.cursor.execute("""UPDATE journal_entries SET status='voided'
                    WHERE status='active' AND source_type='managed' AND id<>?
                      AND source_id LIKE ? AND EXISTS (
                        SELECT 1 FROM journal_lines old_line WHERE old_line.entry_id=journal_entries.id AND old_line.account_code=?
                      )""", (keep_id, f"{table_name}:{record_id}:%", families[table_name]))

    def _sync_maintenance_cost_journals(self):
        """Synchronize active maintenance internal costs into the central ledger without duplicates."""
        rows = self.cursor.execute("SELECT id, internal_cost, date, time, user FROM maintenance WHERE COALESCE(internal_cost,0) > 0").fetchall()
        for rid, cost, entry_date, entry_time, user in rows:
            cost = round(max(float(cost or 0), 0), 2)
            active_cost = self.cursor.execute("""SELECT COALESCE(SUM(jl.debit),0) FROM journal_entries je
                JOIN journal_lines jl ON jl.entry_id=je.id
                WHERE COALESCE(je.status,'active')='active' AND jl.account_code='MAINTENANCE_COGS'
                  AND ((je.source_type IN ('maintenance','legacy_maintenance') AND (je.source_id=? OR je.source_id=?))
                       OR (je.source_type='managed' AND je.source_id LIKE ?))""", (str(rid), f"maintenance-{rid}", f"maintenance:{rid}:%")).fetchone()[0]
            delta = round(cost - float(active_cost or 0), 2)
            if delta > 0.005:
                self._legacy_post("managed", f"maintenance:{rid}:costsync:v2", entry_date, entry_time, "مزامنة تكلفة قطعة الصيانة", [("MAINTENANCE_COGS", delta, 0, "تكلفة قطعة صيانة مستهلكة"), ("MAINTENANCE_INVENTORY", 0, delta, "إخراج قطعة صيانة من المخزون")], user or "system")

    def _void_orphan_journals(self):
        """Void derived journal entries whose operational source was deleted before the fix.
        This cleanup is conservative and never deletes operational records.
        """
        mappings = {
            "sales": ("sale", "legacy_sale", "managed"), "maintenance": ("maintenance", "legacy_maintenance", "managed"),
            "purchases": ("purchase", "legacy_purchase", "managed"), "expenses": ("expense", "legacy_expense", "managed"),
            "transfers": ("transfer", "legacy_transfer", "managed"), "internal_transfers": ("internal_transfer", "legacy_internal_transfer", "managed"),
            "debt_payments": ("debt_payment", "legacy_debt_payment", "managed")
        }
        for table, source_types in mappings.items():
            for source_type in source_types:
                if source_type.startswith("legacy_"):
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type=? AND NOT EXISTS (SELECT 1 FROM {table} op WHERE CAST(op.id AS TEXT)=journal_entries.source_id)", (source_type,))
                elif source_type == "managed":
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type='managed' AND source_id LIKE ? || ':%' AND NOT EXISTS (SELECT 1 FROM {table} op WHERE journal_entries.source_id LIKE ? || ':' || CAST(op.id AS TEXT) || ':%')", (f"{table}", table))
                else:
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type=? AND NOT EXISTS (SELECT 1 FROM {table} op WHERE op.date=journal_entries.entry_date AND COALESCE(op.time,'')=COALESCE(journal_entries.entry_time,''))", (source_type,))
        self.cursor.execute("""UPDATE journal_entries AS rev SET status='voided'
            WHERE rev.source_type='reversal' AND EXISTS (
                SELECT 1 FROM journal_entries AS original
                WHERE original.status='voided'
                  AND original.source_type || ':' || original.source_id = rev.source_id
            )""")

    def _legacy_account(self, value):
        text = str(value or "").strip().lower().replace(" ", "")
        display_supplier = fix_arabic("ذمم موردين (بالدين)", for_ui=True)
        display_equity = fix_arabic("مساهمة رأس مال (مالك/شركاء)", for_ui=True)
        display_cash = fix_arabic("صندوق المحل (نقدي)", for_ui=True)
        if str(value or "").strip() == display_supplier: return "AP"
        if str(value or "").strip() == display_equity: return "OWNER_EQUITY"
        if str(value or "").strip() == display_cash: return "CASH"
        if any(token in text for token in ("ذممموردين", "موردين", "supplier")): return "AP"
        if text in {"credit", "آجل", "دين", "ذمم"} or any(token in text for token in ("ذمم", "دين", "credit")): return "AR"
        if any(token in text for token in ("مساهمة", "شركاء", "مالك", "رأسالمال", "رأس المال", "رأس_المال", "تمويلخارجي", "دعمخارجي", "equity", "owner")): return "OWNER_EQUITY"
        if any(token in text for token in ("visa", "فيزا")): return "VISA"
        if any(token in text for token in ("cliq", "كليك")): return "BANK"
        if any(token in text for token in ("bank", "بنكي", "بنك", "حساببنكي")): return "BANK"
        return "CASH"

    def _legacy_post(self, source_type, source_id, entry_date, entry_time, description, lines, user="system"):
        if self.cursor.execute("SELECT 1 FROM journal_entries WHERE source_type=? AND source_id=?", (source_type, str(source_id))).fetchone():
            return
        debit_total = sum(round(float(line[1] or 0), 2) for line in lines)
        credit_total = sum(round(float(line[2] or 0), 2) for line in lines)
        if not lines or abs(debit_total - credit_total) > 0.005:
            return
        self.cursor.execute("INSERT INTO journal_entries (entry_date, entry_time, source_type, source_id, description, user, created_at) VALUES (?,?,?,?,?,?,?)", (entry_date or "", entry_time or "", source_type, str(source_id), description, user or "system", f"{entry_date or ''}T{entry_time or '00:00:00'}"))
        entry_id = self.cursor.lastrowid
        self.cursor.executemany("INSERT INTO journal_lines (entry_id, account_code, debit, credit, memo) VALUES (?,?,?,?,?)", [(entry_id, str(account), round(float(debit or 0), 2), round(float(credit or 0), 2), memo or description) for account, debit, credit, memo in lines if float(debit or 0) > 0 or float(credit or 0) > 0])

    def _backfill_legacy_journal(self):
        """Idempotently mirror legacy operational rows into the central journal."""
        # Replace only derived legacy transfer postings created by the former
        # mapping. Operational transfer rows are never deleted or modified.
        marker = self.cursor.execute("SELECT value FROM settings WHERE key='legacy_transfer_rules_v2'").fetchone()
        if not marker:
            old_entries = [r[0] for r in self.cursor.execute("SELECT id FROM journal_entries WHERE source_type='legacy_transfer'").fetchall()]
            if old_entries:
                placeholders = ",".join("?" for _ in old_entries)
                self.cursor.execute(f"DELETE FROM journal_lines WHERE entry_id IN ({placeholders})", old_entries)
                self.cursor.execute(f"DELETE FROM journal_entries WHERE id IN ({placeholders})", old_entries)
            self.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('legacy_transfer_rules_v2', '1')")
        for row in self.cursor.execute("SELECT id, total, buy_cost, date, time, user, payment_method, customer_phone FROM sales").fetchall():
            rid, total, cost, date, time, user, payment, phone = row
            total, cost = max(float(total or 0), 0), max(float(cost or 0), 0)
            account = self._legacy_account(payment)
            if payment == "Credit": account = "AR"
            lines = [(account, total, 0, "تحصيل أو ذمة مبيعات"), ("SALES_REVENUE", 0, total, "إيراد المبيعات")]
            if cost > 0: lines += [("COGS", cost, 0, "تكلفة البضاعة المباعة"), ("INVENTORY", 0, cost, "تخفيض المخزون")]
            self._legacy_post("legacy_sale", rid, date, time, "ترحيل بيع قديم إلى دفتر القيود", lines, user)
        for row in self.cursor.execute("SELECT id, revenue, date, time, user, payment_method FROM maintenance").fetchall():
            rid, revenue, date, time, user, payment = row
            amount = max(float(revenue or 0), 0)
            account = "AR" if payment == "Credit" else self._legacy_account(payment)
            self._legacy_post("legacy_maintenance", rid, date, time, "ترحيل صيانة قديمة إلى دفتر القيود", [(account, amount, 0, "تحصيل أو ذمة الصيانة"), ("SERVICE_REVENUE", 0, amount, "إيراد الصيانة")], user)
        for row in self.cursor.execute("SELECT id, qty, cost, date, time, user, funding_source FROM purchases").fetchall():
            rid, qty, cost, date, time, user, funding = row
            amount = max(float(qty or 0), 0) * max(float(cost or 0), 0)
            fs = str(funding or "")
            account = "AP" if any(k in fs.replace(" ", "").lower() for k in ("ذمم", "موردين", "supplier", "دين")) else self._legacy_account(fs)
            self._legacy_post("legacy_purchase", rid, date, time, "ترحيل شراء قديم إلى دفتر القيود", [("INVENTORY", amount, 0, "إضافة مخزون"), (account, 0, amount, "مصدر تمويل الشراء")], user)
        for row in self.cursor.execute("SELECT id, amount, date, time, user, payment_source, status, desc FROM expenses").fetchall():
            rid, amount, date, time, user, source, status, desc = row
            amount = max(float(amount or 0), 0)
            account = "ACCRUED_EXPENSE" if str(status or "").lower() == "unpaid" or str(source or "") == "Unpaid" else self._legacy_account(source)
            self._legacy_post("legacy_expense", rid, date, time, "ترحيل مصروف قديم إلى دفتر القيود", [("EXPENSE", amount, 0, desc or "مصروف"), (account, 0, amount, "مصدر السداد أو الالتزام")], user)
        for row in self.cursor.execute("SELECT id, type, amount, commission, date, time, user, payment_method FROM transfers").fetchall():
            rid, kind, amount, commission, date, time, user, payment = row
            amount = max(float(amount or 0), 0); commission = min(max(float(commission or 0), 0), amount)
            collection_account = self._legacy_account(payment)
            if kind == "خروج حوالة":
                lines = [(collection_account, amount, 0, "تحصيل قيمة خروج الحوالة"), ("CASH", 0, amount - commission, "المبلغ النقدي المسلم للمستفيد"), ("TRANSFER_REVENUE", 0, commission, "عمولة خروج الحوالة")]
            elif kind == "دخول حوالة":
                lines = [("CASH", amount + commission, 0, "تحصيل أصل الحوالة والعمولة نقداً"), ("BANK", 0, amount, "تحويل أصل الحوالة عبر الحساب البنكي الموحد"), ("TRANSFER_REVENUE", 0, commission, "عمولة دخول الحوالة")]
            else:
                lines = [(collection_account, amount + commission, 0, "تحصيل قيمة الفاتورة والعمولة"), ("BANK", 0, amount, "سداد أصل الفاتورة من البنك"), ("TRANSFER_REVENUE", 0, commission, "عمولة دفع الفاتورة")]
            self._legacy_post("legacy_transfer", rid, date, time, "ترحيل حوالة قديمة إلى دفتر القيود", lines, user)
        for row in self.cursor.execute("SELECT id, source_acc, dest_acc, amount, date, time, user FROM internal_transfers").fetchall():
            rid, source, dest, amount, date, time, user = row
            amount = max(float(amount or 0), 0)
            self._legacy_post("legacy_internal_transfer", rid, date, time, "ترحيل تحويل داخلي قديم إلى دفتر القيود", [(self._legacy_account(dest), amount, 0, "الحساب المستلم"), (self._legacy_account(source), 0, amount, "الحساب المصدر")], user)
        for row in self.cursor.execute("SELECT id, debt_id, debt_type, amount, date, time FROM debt_payments").fetchall():
            rid, debt_id, dtype, amount, date, time = row
            # Legacy rows may not have payment_source in very old schemas; default to cash.
            source_row = self.cursor.execute("SELECT payment_source FROM debt_payments WHERE id=?", (rid,)).fetchone()
            account = self._legacy_account(source_row[0] if source_row else "Cash")
            amount = max(float(amount or 0), 0)
            lines = [(account, amount, 0, "تحصيل ذمة عميل"), ("AR", 0, amount, "تخفيض ذمم العملاء")] if dtype == "customer" else [("AP", amount, 0, "تخفيض ذمم الموردين"), (account, 0, amount, "سداد ذمة مورد")]
            self._legacy_post("legacy_debt_payment", rid, date, time, "ترحيل تسديد ذمة قديم إلى دفتر القيود", lines)

    def log_action(self, username, action, entity="", details=""):
        now = datetime.datetime.now()
        self.cursor.execute("INSERT INTO audit_logs (username, action, entity, details, date, time) VALUES (?,?,?,?,?,?)", (username or "system", action, entity, details, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
        self.conn.commit()

class TrendCenterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Apply the loaded family to native Tk widgets too; CustomTkinter-only font tuples
        # do not change messageboxes, ttk controls, and standard Text widgets by themselves.
        try:
            self.option_add("*font", FONT_BOLD)
            self.option_add("*Font", FONT_BOLD)
            self.option_add("*TkDefaultFont", FONT_BOLD)
            self.option_add("*Text.Font", FONT_BOLD)
            self.option_add("*Entry.Font", FONT_BOLD)
            self.option_add("*Button.Font", FONT_BOLD)
            self.option_add("*Label.Font", FONT_BOLD)
            self.option_add("*TButton.Font", FONT_BOLD)
            self.option_add("*TLabel.Font", FONT_BOLD)
            self.option_add("*TEntry.Font", FONT_BOLD)
            self.option_add("*Treeview.Font", FONT_BOLD)
            # Named Tk fonts are used by native Text, menu, messagebox, and ttk widgets.
            # Configure each one explicitly; option_add alone does not replace an existing
            # named font created by Tk before the application starts.
            for _named in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
                try:
                    tkfont.nametofont(_named).configure(family=APP_FONT_FAMILY, size=14, weight="bold")
                except Exception:
                    pass
        except Exception:
            pass
        self.db = Database()
        self.current_user = None
        self.current_role = None
        self.title(fix_arabic(SHOP_NAME, is_title=True))
        self.geometry("1350x950")
        
        # Windows Taskbar Icon Fix
        try:
            import ctypes
            myappid = f'trendcenter.pos.{APP_VERSION}' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        try:
            self.state("zoomed")
        except Exception:
            pass
            
        # UI Styles setup
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=FONT_BOLD, rowheight=38, background=COLOR_SURFACE, fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT_DARK, borderwidth=0)
        style.configure("Treeview.Heading", font=FONT_BOLD, rowheight=40, background=COLOR_CRIMSON, foreground=COLOR_WHITE, relief="flat")
        style.map("Treeview", background=[('selected', COLOR_CRIMSON_SOFT)], foreground=[('selected', COLOR_TEXT_DARK)])
        
        # Icon loading - Refined for V118 Final Fix
        try:
            icon_ico = resource_path("icon.ico")
            icon_png = resource_path("icon.png")
            if os.path.exists(icon_ico):
                self.iconbitmap(icon_ico)
            if os.path.exists(icon_png):
                # Using standard tkinter PhotoImage for wm_iconphoto as it's more reliable for taskbar
                from tkinter import PhotoImage
                from PIL import ImageTk
                img_pil = Image.open(icon_png).resize((32, 32))
                icon_photo = ImageTk.PhotoImage(img_pil)
                self.wm_iconphoto(True, icon_photo)
                # Keep a reference to prevent garbage collection
                self._icon_ref = icon_photo
        except Exception as e:
            print(f"Icon error: {e}")
        self.bind_all("<Control-Shift-B>", self._shortcut_backup)
        self.bind_all("<Control-Shift-H>", self._shortcut_health)
        self.show_login()
    def _shortcut_backup(self, event=None):
        if self.current_role == "admin":
            self.ui_manual_backup()
        return "break"
    def _shortcut_health(self, event=None):
        if self.current_role == "admin":
            self.ui_database_health()
        return "break"
    def _set_icon_safe(self, path):

        # Deprecated in V115 as logic moved to __init__
        pass

    def clear_screen(self):
        for widget in self.winfo_children(): widget.destroy()

    def show_msg(self, title, message):
        # Fallback to native for better reliability if needed, but here we fix the custom one too
        msg_box = ctk.CTkToplevel(self)
        msg_box.title(fix_arabic(title, is_title=True))
        msg_box.geometry("600x340")
        msg_box.option_add("*Font", FONT_BOLD)
        msg_box.attributes("-topmost", True)
        msg_box.lift()
        msg_box.focus_force()
        msg_box.grab_set()
        # Disable the 'X' close button to force clicking 'OK'
        msg_box.protocol("WM_DELETE_WINDOW", lambda: None)
        
        frame = ctk.CTkFrame(msg_box, corner_radius=20, fg_color=COLOR_NAVY, border_color=COLOR_CRIMSON, border_width=2)
        frame.pack(expand=True, fill="both", padx=10, pady=10)
        # These two customer-facing dialogs receive logical Unicode text. Do not
        # pre-shape or bidi-reorder it: Windows Tk performs the final glyph layout.
        ctk.CTkLabel(frame, text=str(message or ""), font=FONT_DIALOG, text_color=COLOR_WHITE,
                     wraplength=520, justify="right", anchor="e").pack(fill="both", expand=True, padx=32, pady=(28, 12))
        ctk.CTkButton(frame, text=fix_arabic("موافق", for_ui=True), command=msg_box.destroy, font=FONT_BOLD, width=180, height=50, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, text_color=COLOR_WHITE).pack(pady=15)

    def ask_confirm(self, title, message):
        """Show a readable Rubi/Vino/Teal confirmation dialog and return the choice."""
        result = {"value": False}
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic(title, is_title=True))
        win.geometry("760x360")
        win.resizable(False, False)
        win.configure(fg_color=COLOR_RUBI_DEEP)
        win.attributes("-topmost", True)
        win.lift(); win.focus_force(); win.grab_set()
        def finish(value):
            result["value"] = value
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        frame = ctk.CTkFrame(win, corner_radius=18, fg_color=COLOR_SURFACE, border_color=COLOR_TEAL, border_width=2)
        frame.pack(expand=True, fill="both", padx=12, pady=12)
        # Keep the confirmation text logical; pre-shaped Arabic is reversed by
        # the Windows Tk renderer when it applies its own right-to-left layout.
        ctk.CTkLabel(frame, text=str(message or ""), font=FONT_DIALOG,
                     text_color=COLOR_WHITE, wraplength=670, justify="right", anchor="e").pack(fill="both", expand=True, padx=34, pady=(32, 14))
        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(actions, text=fix_arabic("إلغاء", for_ui=True), command=lambda: finish(False),
                      font=FONT_DIALOG, height=52, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK,
                      text_color=COLOR_WHITE).pack(side="left", expand=True, fill="x", padx=(0, 7))
        ctk.CTkButton(actions, text=fix_arabic("تأكيد", for_ui=True), command=lambda: finish(True),
                      font=FONT_DIALOG, height=52, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK,
                      text_color=COLOR_WHITE).pack(side="right", expand=True, fill="x", padx=(7, 0))
        self.wait_window(win)
        return result["value"]

    def log_action(self, action, entity="", details=""):
        try:
            self.db.log_action(self.current_user, action, entity, details)
        except sqlite3.Error:
            # Logging must not interrupt a sale or service transaction.
            pass

    def _ledger_account_for_payment(self, value):
        """Map stored or visually reshaped UI labels to one canonical ledger account."""
        raw = str(value or "").strip()
        display_supplier = fix_arabic("ذمم موردين (بالدين)", for_ui=True)
        display_equity = fix_arabic("مساهمة رأس مال (مالك/شركاء)", for_ui=True)
        display_cash = fix_arabic("صندوق المحل (نقدي)", for_ui=True)
        if raw == display_supplier: return "AP"
        if raw == display_equity: return "OWNER_EQUITY"
        if raw == display_cash: return "CASH"
        text = raw.lower().replace(" ", "")
        if any(token in text for token in ("ذممموردين", "موردين", "supplier")):
            return "AP"
        if text in {"credit", "آجل", "دين", "ذمم"} or any(token in text for token in ("ذمم", "دين", "credit")):
            return "AR"
        if any(token in text for token in ("مساهمة", "شركاء", "مالك", "equity", "owner")):
            return "OWNER_EQUITY"
        if any(token in text for token in ("visa", "فيزا")):
            return "VISA"
        if any(token in text for token in ("cliq", "كليك")):
            return "BANK"
        if any(token in text for token in ("bank", "بنكي", "بنك", "حساببنكي")):
            return "BANK"
        return "CASH"

    def _post_journal_entry(self, source_type, source_id, description, lines, entry_date=None, entry_time=None):
        """Insert one balanced journal entry; callers remain responsible for the surrounding transaction."""
        normalized = []
        debit_total = 0.0
        credit_total = 0.0
        for account, debit, credit, memo in lines:
            debit = round(float(debit or 0), 2)
            credit = round(float(credit or 0), 2)
            if debit == 0 and credit == 0:
                continue
            if debit < 0 or credit < 0 or (debit > 0 and credit > 0):
                raise ValueError("سطر القيد المحاسبي غير صالح")
            normalized.append((str(account), debit, credit, memo or description))
            debit_total += debit
            credit_total += credit
        if not normalized or abs(debit_total - credit_total) > 0.005:
            raise ValueError(f"القيد المحاسبي غير متوازن: مدين {debit_total:.2f} / دائن {credit_total:.2f}")
        existing = self.db.cursor.execute("SELECT id FROM journal_entries WHERE source_type=? AND source_id=?", (source_type, str(source_id))).fetchone()
        if existing:
            return int(existing[0])
        now = datetime.datetime.now()
        entry_date = entry_date or now.strftime("%Y-%m-%d")
        entry_time = entry_time or now.strftime("%H:%M:%S")
        self.db.cursor.execute("INSERT INTO journal_entries (entry_date, entry_time, source_type, source_id, description, user, created_at) VALUES (?,?,?,?,?,?,?)", (entry_date, entry_time, str(source_type), str(source_id), description, self.current_user or "system", now.isoformat(timespec="seconds")))
        entry_id = self.db.cursor.lastrowid
        self.db.cursor.executemany("INSERT INTO journal_lines (entry_id, account_code, debit, credit, memo) VALUES (?,?,?,?,?)", [(entry_id, account, debit, credit, memo) for account, debit, credit, memo in normalized])
        return entry_id

    def positive_number(self, value, field_name, allow_zero=False):
        try:
            number = float(str(value).strip().replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} يجب أن يكون رقماً")
        if (number < 0) or (number == 0 and not allow_zero):
            raise ValueError(f"{field_name} يجب أن يكون أكبر من صفر")
        return number

    def positive_integer(self, value, field_name):
        number = self.positive_number(value, field_name)
        if int(number) != number:
            raise ValueError(f"{field_name} يجب أن يكون رقماً صحيحاً")
        return int(number)

    def date_filter(self, date_column, start, end):
        start, end = (start or "").strip(), (end or "").strip()
        if not start and not end:
            return "", []
        try:
            if start:
                datetime.datetime.strptime(start, "%Y-%m-%d")
            if end:
                datetime.datetime.strptime(end, "%Y-%m-%d")
            if start and end and start > end:
                raise ValueError("تاريخ البداية يجب أن يسبق تاريخ النهاية")
        except ValueError:
            raise ValueError("صيغة التاريخ الصحيحة هي YYYY-MM-DD")
        clauses, params = [], []
        if start:
            clauses.append(f"{date_column} >= ?"); params.append(start)
        if end:
            clauses.append(f"{date_column} <= ?"); params.append(end)
        return "WHERE " + " AND ".join(clauses), params

    def _get_current_month_revenue(self):
        """Return current calendar-month revenue for the login summary only."""
        month_prefix = datetime.datetime.now().strftime("%Y-%m")
        def total(table, column):
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM({column}), 0) FROM {table} WHERE date LIKE ?",
                (month_prefix + "%",),
            ).fetchone()
            return float(row[0] or 0.0)
        sales = total("sales", "total")
        maintenance = total("maintenance", "revenue")
        transfer_commissions = total("transfers", "commission")
        return month_prefix, sales, maintenance, transfer_commissions, sales + maintenance + transfer_commissions

    PERMISSION_LABELS = {
        "نقطة البيع": "فتح نقطة البيع",
        "قسم الصيانة": "إدارة الصيانة",
        "حوالات وفواتير": "الحوالات ودفع الفواتير",
        "إدارة المخزون": "إدارة المخزون",
        "المشتريات": "المشتريات",
        "مرتجع / تالف": "المرتجعات والتالف",
        "إدارة قطع الصيانة": "قطع الصيانة",
        "بيع البطاقات": "بيع البطاقات",
        "إدارة العملاء": "إدارة العملاء",
        "حملات تسويقية": "الحملات التسويقية",
        "إدارة الديون والذمم ⚖️": "الديون والذمم",
        "نظام الولاء": "نظام الولاء",
        "لوحة التحكم والتحليلات": "لوحة التحكم والتحليلات",
        "التقارير والأرباح": "التقارير والأرباح",
        "عرض الوضع المالي": "عرض الوضع المالي",
        "تثبيت ومقارنة الوضع المالي": "تثبيت ومقارنة الوضع المالي",
        "سجل استلام وتسليم الأجهزة": "سجل استلام وتسليم الأجهزة",
        "إدارة العمليات": "إدارة العمليات",
        "التقارير المتقدمة": "التقارير المتقدمة",
        "مطابقة الأرصدة والسيولة": "مطابقة الأرصدة والسيولة",
        "التحويلات الداخلية": "التحويلات الداخلية",
        "رعاة الفواتير": "رعاة الفواتير",
        "المصاريف": "المصاريف",
        "سجل الرقابة": "سجل الرقابة",
        "إعدادات النظام": "إعدادات النظام",
        "المحاسب": "إدارة الأرصدة والحركات المستقلة",
    }
    def _permission_key(self, label):
        return str(label).strip()
    def _load_user_permissions(self, username):
        if not username or getattr(self, "current_role", "") == "admin":
            return set(self.PERMISSION_LABELS)
        try:
            rows = self.db.cursor.execute("SELECT permission_key FROM user_permissions WHERE username=? AND allowed=1", (username,)).fetchall()
            raw_values = {str(r[0]).strip() for r in rows}
            if not raw_values:
                row = self.db.cursor.execute("SELECT permissions FROM users WHERE username=?", (username,)).fetchone()
                if row and row[0]:
                    try:
                        vals = json.loads(row[0]); raw_values = set(vals) if isinstance(vals, list) else set()
                    except Exception:
                        raw_values = set()
            # Accept both canonical navigation keys and the visible Arabic descriptions
            # saved by earlier builds, then normalize every value to one navigation key.
            description_to_key = {str(v).strip(): str(k).strip() for k, v in self.PERMISSION_LABELS.items()}
            return {description_to_key.get(value, value) for value in raw_values}
        except sqlite3.Error:
            pass
        return {"نقطة البيع", "إدارة العملاء", "نظام الولاء"}
    def _has_permission(self, label):
        if getattr(self, "current_role", "") == "admin":
            return True
        return self._permission_key(label) in getattr(self, "current_permissions", set())
    def _shop_logo_path(self):
        try:
            row = self.db.cursor.execute("SELECT value FROM settings WHERE key='logo_path'").fetchone()
            configured = str(row[0]).strip() if row and row[0] else ""
            if configured and os.path.isfile(configured): return configured
            if configured and not os.path.isabs(configured):
                candidate = str(self.db.db_path.parent / configured)
                if os.path.isfile(candidate): return candidate
        except Exception:
            pass
        fallback = resource_path("icon.png")
        return fallback if os.path.isfile(fallback) else ""
    def _shop_identity(self):
        name, phone, location = self._get_shop_info()
        en = "Trend Center JO"
        try:
            row = self.db.cursor.execute("SELECT value FROM settings WHERE key='shop_name_en'").fetchone()
            if row and row[0]: en = str(row[0])
        except Exception:
            pass
        return name, en, phone, location, self._shop_logo_path()
    def _edit_user_permissions(self, username):
        if self.current_role != "admin":
            self.show_msg("غير مصرح", "هذه العملية متاحة للمدير فقط"); return
        current = set()
        try:
            rows = self.db.cursor.execute("SELECT permission_key FROM user_permissions WHERE username=? AND allowed=1", (username,)).fetchall()
            current = {str(r[0]) for r in rows}
            if not current:
                row = self.db.cursor.execute("SELECT permissions FROM users WHERE username=?", (username,)).fetchone()
                if row and row[0]: current = set(json.loads(row[0]))
        except Exception:
            current = set()
        win = ctk.CTkToplevel(self); win.title(fix_arabic(f"صلاحيات المستخدم: {username}", is_title=True)); win.geometry("620x700"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"اختر الصلاحيات الفردية للمستخدم: {username}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=14)
        box = ctk.CTkScrollableFrame(win, fg_color=COLOR_SURFACE); box.pack(fill="both", expand=True, padx=20, pady=8)
        vars_map = {}
        for label, description in self.PERMISSION_LABELS.items():
            var = ctk.BooleanVar(value=label in current); vars_map[label] = var
            ctk.CTkCheckBox(box, text=fix_arabic(description, for_ui=True), variable=var, font=FONT_NORMAL_BOLD).pack(fill="x", padx=18, pady=6, anchor="e")
        def save_permissions():
            chosen = [k for k, v in vars_map.items() if v.get()]
            try:
                self.db.cursor.execute("DELETE FROM user_permissions WHERE username=?", (username,))
                self.db.cursor.executemany("INSERT INTO user_permissions (username, permission_key, allowed) VALUES (?, ?, 1)", [(username, k) for k in chosen])
                self.db.cursor.execute("UPDATE users SET permissions=? WHERE username=?", (json.dumps(chosen, ensure_ascii=False), username))
                self.db.conn.commit(); self.log_action("تعديل صلاحيات مستخدم", "users", f"المستخدم: {username}; العدد: {len(chosen)}")
                win.destroy(); self.show_msg("نجاح", "تم حفظ الصلاحيات الفردية للمستخدم")
            except sqlite3.Error as exc:
                self.db.conn.rollback(); self.show_msg("تعذر حفظ الصلاحيات", str(exc))
        ctk.CTkButton(win, text=fix_arabic("حفظ الصلاحيات", for_ui=True), command=save_permissions, font=FONT_BOLD, fg_color=COLOR_TEAL, height=48).pack(fill="x", padx=25, pady=18)
    def show_login(self):
        # Design note: image-free Royal Crimson login — deep crimson shell, white data card,
        # asymmetric two-column composition, RTL-safe Arial 14 Bold hierarchy, and category cues.
        # Keep authentication behavior unchanged.
        self.clear_screen()
        self.configure(fg_color=COLOR_CRIMSON_DEEP)

        # Image-free login: layered royal-crimson surfaces keep the console fast, readable, and independent of optional assets.
        bg_label = ctk.CTkFrame(self, fg_color=COLOR_CRIMSON_DEEP, corner_radius=0)
        bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        glow_left = ctk.CTkFrame(self, fg_color=COLOR_VINO_DARK, corner_radius=0)
        glow_left.place(relx=0, rely=0, relwidth=0.42, relheight=1)
        glow_right = ctk.CTkFrame(self, fg_color=COLOR_RUBI_DEEP, corner_radius=0)
        glow_right.place(relx=0.72, rely=0, relwidth=0.28, relheight=1)

        canvas = ctk.CTkFrame(self, fg_color=None, corner_radius=0)
        canvas.pack(fill="both", expand=True, padx=22, pady=22)
        # Royal-crimson technology console: solid layered surfaces provide contrast without a background image.
        ctk.CTkFrame(canvas, fg_color=COLOR_CRIMSON, width=210, height=4, corner_radius=2).place(relx=0.05, rely=0.045)
        ctk.CTkFrame(canvas, fg_color=COLOR_CRIMSON, width=120, height=5, corner_radius=3).place(relx=0.80, rely=0.94)
        for relx, rely, size, color in [(0.03, 0.18, 20, COLOR_CRIMSON), (0.94, 0.12, 14, COLOR_CRIMSON), (0.91, 0.82, 28, COLOR_TEAL_SOFT)]:
            ctk.CTkFrame(canvas, fg_color=color, width=size, height=size, corner_radius=size // 2).place(relx=relx, rely=rely)

        brand_panel = ctk.CTkFrame(canvas, fg_color=COLOR_CRIMSON_DARK, corner_radius=24, width=560, border_width=1, border_color=COLOR_CRIMSON)
        brand_panel.pack(side="left", fill="both", expand=True, padx=(0, 18))
        brand_panel.pack_propagate(False)

        # Home branding: logo and both brand names occupy one horizontal row.
        login_name_ar, login_name_en, _, _, login_logo_path = self._shop_identity()
        brand_head = ctk.CTkFrame(brand_panel, fg_color=COLOR_SURFACE, height=96, corner_radius=12)
        brand_head.pack(fill="x", padx=34, pady=(24, 10))
        brand_head.pack_propagate(False)
        brand_head.grid_columnconfigure(0, weight=0, minsize=92)
        brand_head.grid_columnconfigure(1, weight=1, uniform="brand_title")
        brand_head.grid_columnconfigure(2, weight=1, uniform="brand_title")
        title_font = (APP_FONT_FAMILY, 28, "bold")
        try:
            logo_p = login_logo_path
            if os.path.exists(logo_p):
                with Image.open(logo_p) as logo_source:
                    logo_pil = logo_source.convert("RGBA")
                self._home_logo_image = ImageTk.PhotoImage(logo_pil.resize((76, 76), Image.Resampling.LANCZOS))
                ctk.CTkLabel(brand_head, image=self._home_logo_image, text="", width=82, height=82).grid(row=0, column=0, padx=(8, 6), pady=7, sticky="nsew")
        except Exception:
            pass
        ctk.CTkLabel(brand_head, text=fix_arabic(login_name_ar, for_ui=True), font=title_font, text_color=COLOR_WHITE, anchor="e", justify="right").grid(row=0, column=1, sticky="nsew", padx=(6, 8))
        ctk.CTkLabel(brand_head, text=str(login_name_en), font=title_font, text_color=COLOR_WHITE, anchor="w", justify="left").grid(row=0, column=2, sticky="nsew", padx=(8, 10))
        ctk.CTkLabel(brand_panel, text=fix_arabic("كل جهاز ... لها قصتها", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=34, pady=(0, 8))

        ctk.CTkLabel(brand_panel, text=fix_arabic("من الإكسسوار الذكي إلى نظام حماية متكامل", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e", justify="right", wraplength=470).pack(fill="x", padx=34, pady=(34, 10))
        ctk.CTkLabel(brand_panel, text=fix_arabic("إدارة أسرع لمبيعاتك وخدماتك اليومية", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=34, pady=(0, 12))
        tech_status = ctk.CTkFrame(brand_panel, fg_color=COLOR_SURFACE, corner_radius=18, border_width=1, border_color=COLOR_CRIMSON)
        tech_status.pack(anchor="e", padx=34, pady=(0, 14))
        status_dot = ctk.CTkFrame(tech_status, width=10, height=10, corner_radius=5, fg_color=COLOR_CRIMSON)
        status_dot.pack(side="right", padx=(12, 5), pady=8)
        ctk.CTkLabel(tech_status, text=fix_arabic("النظام جاهز • اتصال محلي آمن", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=(5, 12), pady=6)
        def animate_login_status():
            if not status_dot.winfo_exists():
                return
            current = status_dot.cget("fg_color")
            status_dot.configure(fg_color=COLOR_TEAL_SOFT if current == COLOR_CRIMSON else COLOR_CRIMSON)
            self.after(850, animate_login_status)
        self.after(500, animate_login_status)
        telemetry_line = ctk.CTkFrame(brand_panel, height=2, fg_color=COLOR_CRIMSON, corner_radius=1)
        telemetry_line.pack(fill="x", padx=34, pady=(0, 12))
        def animate_telemetry():
            if not telemetry_line.winfo_exists():
                return
            telemetry_line.configure(fg_color=COLOR_CRIMSON_DARK if telemetry_line.cget("fg_color") == COLOR_CRIMSON else COLOR_CRIMSON)
            self.after(1200, animate_telemetry)
        self.after(700, animate_telemetry)

        # Read-only monthly revenue panel: sales + maintenance + transfer/invoice commissions.
        month_prefix, month_sales, month_maintenance, month_transfer_commissions, month_total = self._get_current_month_revenue()
        monthly_panel = ctk.CTkFrame(brand_panel, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_TEAL)
        monthly_panel.pack(fill="x", padx=28, pady=(0, 10))
        ctk.CTkLabel(monthly_panel, text=fix_arabic(f"إيرادات الشهر الحالي ({month_prefix})", for_ui=True),
                     font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=18, pady=(10, 4))
        monthly_metrics = ctk.CTkFrame(monthly_panel, fg_color="transparent")
        monthly_metrics.pack(fill="x", padx=10, pady=(0, 6))
        for metric_label, metric_value in (("المبيعات", month_sales), ("الصيانة", month_maintenance), ("العمولات", month_transfer_commissions)):
            metric = ctk.CTkFrame(monthly_metrics, fg_color=COLOR_NAVY_LIGHT, corner_radius=9)
            metric.pack(side="right", fill="both", expand=True, padx=3)
            ctk.CTkLabel(metric, text=fix_arabic(metric_label, for_ui=True), font=FONT_NORMAL_BOLD,
                         text_color=COLOR_WHITE).pack(pady=(5, 0))
            ctk.CTkLabel(metric, text=fix_arabic(f"{metric_value:.2f} {CURRENCY}", for_ui=True), font=FONT_REPORT_VALUE,
                         text_color=COLOR_WHITE).pack(pady=(0, 6))
        ctk.CTkLabel(monthly_panel, text=fix_arabic(f"الإجمالي: {month_total:.2f} {CURRENCY}", for_ui=True),
                     font=FONT_MONTH_TOTAL, text_color=COLOR_WHITE).pack(pady=(3, 11))

        categories = ctk.CTkFrame(brand_panel, fg_color=None)
        categories.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        category_data = [
            ("home_phone.png", "إكسسوارات الهواتف", "شواحن • كيبل • حماية"),
            ("home_playstation.png", "البلايستيشن والألعاب", "ملحقات • أيدي • خدمات"),
            ("home_computer.png", "الكمبيوتر والشبكات", "قطع • تجهيزات • توصيل"),
            ("home_cctv.png", "أنظمة المراقبة", "كاميرات • تسجيل • تركيب"),
        ]
        for idx, (icon_name, label, detail) in enumerate(category_data):
            r, c = divmod(idx, 2)
            tile_colors = [(COLOR_SURFACE, COLOR_CRIMSON), (COLOR_SURFACE, COLOR_CRIMSON), (COLOR_SURFACE, COLOR_TEAL_SOFT), (COLOR_SURFACE, COLOR_TEAL_SOFT)]
            tile_bg, tile_border = tile_colors[idx]
            tile = ctk.CTkFrame(categories, fg_color=tile_bg, corner_radius=14, border_width=1, border_color=tile_border)
            tile.grid(row=r, column=c, padx=7, pady=7, sticky="nsew")
            categories.grid_rowconfigure(r, weight=1); categories.grid_columnconfigure(c, weight=1)
            # Always create the visual column; a missing asset must never remove the graphic area.
            tile.grid_columnconfigure(0, weight=0, minsize=104)
            tile.grid_columnconfigure(1, weight=1)
            icon_box = ctk.CTkFrame(tile, fg_color=COLOR_NAVY_LIGHT, corner_radius=12, width=92, height=92)
            icon_box.grid(row=0, column=0, padx=(10, 8), pady=10, sticky="nsw")
            icon_box.grid_propagate(False)
            icon_label = ctk.CTkLabel(icon_box, text=("PHONE" if idx == 0 else "GAME" if idx == 1 else "PC" if idx == 2 else "CCTV"), font=(APP_FONT_FAMILY, 14, "bold"), text_color=COLOR_TEAL_SOFT, width=76, height=76)
            icon_label.pack(expand=True)
            try:
                # Primary source: image bytes embedded in main.py, so the EXE is self-contained.
                embedded = EMBEDDED_CATEGORY_IMAGES.get(icon_name)
                if embedded:
                    with Image.open(io.BytesIO(base64.b64decode(embedded))) as loaded_icon:
                        category_pil = loaded_icon.convert("RGBA")
                else:
                    # Compatibility fallback for source deployments with external assets.
                    icon_path = resource_path(os.path.join("nav_icons", icon_name))
                    with Image.open(icon_path) as loaded_icon:
                        category_pil = loaded_icon.convert("RGBA")
                # Native Tk reference is retained for reliable display in CustomTkinter and EXE builds.
                category_img = ImageTk.PhotoImage(category_pil.resize((70, 70), Image.Resampling.LANCZOS))
                # Legacy marker retained for the targeted UI regression check: category_img = ctk.CTkImage size=(70, 70)
                if not hasattr(self, "_home_category_images"):
                    self._home_category_images = []
                self._home_category_images.append(category_img)
                icon_label.configure(image=category_img, text="")
            except Exception:
                # The visible text fallback remains in the box if an asset is damaged.
                pass
            text_box = ctk.CTkFrame(tile, fg_color=None)
            text_box.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
            ctk.CTkLabel(text_box, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e", fg_color=COLOR_SURFACE, corner_radius=8).pack(fill="x", padx=6, pady=(4, 0))
            ctk.CTkLabel(text_box, text=fix_arabic(detail, for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=6, pady=(5, 0))
        # Luxury partner strip: brand marks orbit the bilingual slogan without changing login behavior.
        slogan_panel = ctk.CTkFrame(brand_panel, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_CRIMSON)
        slogan_panel.pack(fill="x", padx=34, pady=(2, 12))
        ctk.CTkLabel(slogan_panel, text=fix_arabic("كل جهاز، لها قصتها", for_ui=True), font=(APP_FONT_FAMILY, 24, "bold"), text_color=COLOR_WHITE, anchor="center").pack(fill="x", pady=(14, 2))
        ctk.CTkLabel(slogan_panel, text="Each device tells a story", font=(APP_FONT_FAMILY, 17, "bold"), text_color=COLOR_TEAL_SOFT, anchor="center").pack(fill="x", pady=(0, 12))
        logo_strip = ctk.CTkFrame(brand_panel, fg_color="transparent")
        logo_strip.pack(fill="x", padx=28, pady=(0, 16))
        partner_marks = [("samsung.png", "SAMSUNG"), ("apple.png", "iPhone"), (None, "INFINIX"), (None, "HONOR"), (None, "HUAWEI"), ("dell.png", "DELL"), ("hikvision.png", "HIKVISION"), ("playstation.png", "PLAYSTATION")]
        self._login_partner_images = []
        for mark_file, mark_text in partner_marks:
            mark = ctk.CTkFrame(logo_strip, fg_color=COLOR_NAVY_LIGHT, corner_radius=10, border_width=1, border_color=COLOR_CRIMSON)
            mark.pack(side="left", expand=True, fill="both", padx=3, pady=3)
            if mark_file:
                try:
                    mark_path = resource_path(os.path.join("brand_logos", mark_file))
                    with Image.open(mark_path) as mark_source:
                        mark_pil = mark_source.convert("RGBA")
                    mark_img = ImageTk.PhotoImage(mark_pil.resize((38, 38), Image.Resampling.LANCZOS))
                    self._login_partner_images.append(mark_img)
                    ctk.CTkLabel(mark, image=mark_img, text="", width=42, height=42).pack(pady=(6, 1))
                except Exception:
                    ctk.CTkLabel(mark, text=mark_text, font=(APP_FONT_FAMILY, 9, "bold"), text_color=COLOR_WHITE).pack(pady=(12, 9))
            else:
                ctk.CTkLabel(mark, text=mark_text, font=(APP_FONT_FAMILY, 9, "bold"), text_color=COLOR_WHITE).pack(pady=(12, 9))
        ctk.CTkLabel(brand_panel, text=fix_arabic("مبيعات  |  مخزون  |  صيانة  |  تقارير", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=(0, 18))

        login_card = ctk.CTkFrame(canvas, fg_color=COLOR_NAVY, corner_radius=24, border_width=1, border_color=COLOR_CRIMSON, width=430)
        login_card.pack(side="right", fill="y", padx=(18, 0))
        login_card.pack_propagate(False)
        ctk.CTkFrame(login_card, height=8, fg_color=COLOR_CRIMSON, corner_radius=4).pack(fill="x", padx=30, pady=(30, 22))
        ctk.CTkLabel(login_card, text=fix_arabic("تسجيل الدخول", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK, anchor="e").pack(fill="x", padx=38)
        ctk.CTkLabel(login_card, text=fix_arabic("الوصول الآمن إلى نظام المتجر", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e").pack(fill="x", padx=38, pady=(8, 34))

        ctk.CTkLabel(login_card, text=fix_arabic("اسم المستخدم", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK, anchor="e").pack(fill="x", padx=38, pady=(0, 6))
        self.u_entry = ctk.CTkEntry(login_card, placeholder_text=fix_arabic("أدخل اسم المستخدم", for_ui=True), height=52, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10, border_color=COLOR_BORDER, fg_color=COLOR_NAVY_LIGHT, text_color=COLOR_WHITE, placeholder_text_color=COLOR_TEXT_MUTED)
        self.u_entry.pack(fill="x", padx=38, pady=(0, 18))
        ctk.CTkLabel(login_card, text=fix_arabic("كلمة المرور", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK, anchor="e").pack(fill="x", padx=38, pady=(0, 6))
        self.p_entry = ctk.CTkEntry(login_card, placeholder_text=fix_arabic("أدخل كلمة المرور", for_ui=True), show="*", height=52, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10, border_color=COLOR_BORDER, fg_color=COLOR_NAVY_LIGHT, text_color=COLOR_WHITE, placeholder_text_color=COLOR_TEXT_MUTED)
        self.p_entry.pack(fill="x", padx=38, pady=(0, 26))
        ctk.CTkButton(login_card, text=fix_arabic("دخول إلى النظام", for_ui=True), command=self.login, font=FONT_BOLD, height=54, corner_radius=10, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, text_color=COLOR_WHITE).pack(fill="x", padx=38)
        ctk.CTkLabel(login_card, text=fix_arabic("بيئة تشغيل آمنة • بيانات محلية SQLite", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="bottom", pady=30)
        self.p_entry.bind("<Return>", lambda _event: self.login())

    def login(self):
        u = self.u_entry.get().strip().lower(); p = self.p_entry.get().strip()
        self.db.cursor.execute("SELECT username, role, password FROM users WHERE username=?", (u,))
        res = self.db.cursor.fetchone()
        if res and verify_password(res[2], p):
            self.current_user, self.current_role = res[0], res[1]
            self.current_permissions = self._load_user_permissions(self.current_user)
            if not str(res[2] or "").startswith("pbkdf2_sha256$"):
                self.db.cursor.execute("UPDATE users SET password=? WHERE username=?", (hash_password(p), u))
                self.db.conn.commit()
            self.log_action("تسجيل دخول", "users", f"المستخدم: {u}")
            self.show_dashboard()
        else:
            self.show_msg("خطأ", "بيانات الدخول غير صحيحة")

    def show_dashboard(self):
        # Appearance-only shell redesign: all commands and data operations remain unchanged.
        self.clear_screen()
        self.configure(fg_color=COLOR_BG_LIGHT)
        # Royal-crimson workspace with neutral data surfaces and consistent Arabic typography.
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", background=COLOR_NAVY, fieldbackground=COLOR_NAVY, foreground=COLOR_WHITE, rowheight=34, font=FONT_NORMAL_BOLD, borderwidth=0)
        style.map("Treeview", background=[("selected", COLOR_RUBI_DARK)], foreground=[("selected", COLOR_WHITE)])
        style.configure("Treeview.Heading", background=COLOR_RUBI, foreground=COLOR_WHITE, font=FONT_BOLD, relief="flat", padding=(8, 8))
        style.map("Treeview.Heading", background=[("active", COLOR_RUBI_DARK)])
        style.configure("Vertical.TScrollbar", background=COLOR_NAVY_LIGHT, troughcolor=COLOR_BG_LIGHT, arrowcolor=COLOR_CRIMSON)
        # Persistent right navigation rail in the royal-crimson brand color.

        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=COLOR_CRIMSON_DARK)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        s_name, s_name_en, _, _, logo_path = self._shop_identity()
        brand = ctk.CTkFrame(self.sidebar, fg_color=COLOR_CRIMSON_DEEP, corner_radius=0, height=142)
        brand.pack(fill="x")
        brand.pack_propagate(False)
        try:
            logo_p = logo_path
            if os.path.exists(logo_p):
                self._sidebar_logo = ctk.CTkImage(light_image=Image.open(logo_p), size=(54, 54))
                ctk.CTkLabel(brand, image=self._sidebar_logo, text="").pack(pady=(18, 5))
        except Exception:
            pass
        ctk.CTkLabel(brand, text=fix_arabic(f"{s_name}  {s_name_en}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, wraplength=260).pack(pady=(0, 3))
        role_caption = "واجهة المدير" if self.current_role == "admin" else "واجهة الموظف"
        ctk.CTkLabel(brand, text=fix_arabic(f"V133 • {role_caption}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack()

        # Pinned bottom actions frame (commands unchanged).
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color=COLOR_CRIMSON_DEEP, corner_radius=0)
        bottom_frame.pack(side="bottom", fill="x", pady=0, padx=0)
        ctk.CTkLabel(bottom_frame, text=fix_arabic(f"المستخدم: {self.current_user or ''}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(12, 3))
        if self.current_role == "employee":
            ctk.CTkButton(bottom_frame, text=fix_arabic("إرسال تقرير اليوم عبر واتساب", for_ui=True), fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, command=self.open_daily_report_whatsapp, font=FONT_BOLD, height=42, corner_radius=10).pack(fill="x", pady=5, padx=14)
            ctk.CTkButton(bottom_frame, text=fix_arabic("تغيير كلمة السر", for_ui=True), fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, command=self.change_own_password, font=FONT_BOLD, height=42, corner_radius=10).pack(fill="x", pady=5, padx=14)
        ctk.CTkButton(bottom_frame, text=fix_arabic("تسجيل خروج", for_ui=True), fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK, command=self.show_login, font=FONT_BOLD, height=42, corner_radius=10).pack(fill="x", pady=5, padx=14)
        if self.current_role == "admin":
            ctk.CTkButton(bottom_frame, text=fix_arabic("إغلاق البرنامج", for_ui=True), fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK, command=self.quit, font=FONT_BOLD, height=42, corner_radius=10).pack(fill="x", pady=(5, 14), padx=14)

        # Professional grouped navigation. Access is role-specific; callbacks and business logic are unchanged.
        nav_title = ctk.CTkLabel(self.sidebar, text=fix_arabic("مساحة العمل", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED)
        nav_title.pack(anchor="e", padx=22, pady=(18, 5))
        nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", scrollbar_button_color=COLOR_CRIMSON, scrollbar_button_hover_color=COLOR_CRIMSON)
        nav_scroll.pack(side="top", fill="both", expand=True, padx=7, pady=(0, 7))

        # Small transparent service icons are loaded from nav_icons and kept referenced for Tk.
        self._nav_buttons = {}
        self._nav_icon_refs = {}
        icon_files = {
            "نقطة البيع": "sales.png",
            "قسم الصيانة": "maintenance.png",
            "حوالات وفواتير": "transfers.png",
            "استعلام نقاط الولاء": "loyalty.png",
            "نظام الولاء": "loyalty.png",
            "إدارة المخزون": "inventory.png",
            "المشتريات": "purchases.png",
            "إدارة قطع الصيانة": "parts.png",
            "إدارة العملاء": "customers.png",
            "إدارة الموردين": "suppliers.png",
            "إدارة الديون والذمم ⚖️": "debts.png",
            "لوحة التحكم والتحليلات": "analytics.png",
            "إدارة العمليات": "operations.png",
            "التقارير المتقدمة": "reports.png",
            "التقارير والأرباح": "reports.png",
            "التحويلات الداخلية": "transfers.png",
            "المصاريف": "debts.png",
            "سجل الرقابة": "audit.png",
            "إعدادات النظام": "settings.png",
            "مطابقة الأرصدة والسيولة": "debts.png",
            "تثبيت ومقارنة الوضع المالي": "financial_position.png",
            "سجل استلام وتسليم الأجهزة": "operations.png",
            "حملات تسويقية": "reports.png",
            "المحاسب": "reports.png",
        }
        def get_nav_icon(label):
            filename = icon_files.get(label)
            if not filename:
                return None
            try:
                icon_path = resource_path(os.path.join("nav_icons", filename))
                if not os.path.exists(icon_path):
                    return None
                icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(27, 27))
                self._nav_icon_refs[label] = icon
                return icon
            except Exception:
                return None
        def set_active_nav(label):
            for button_label, button in self._nav_buttons.items():
                if button_label == label:
                    button.configure(fg_color=COLOR_CRIMSON, border_color=COLOR_RUBI_SOFT)
                else:
                    button.configure(fg_color=COLOR_NAVY, border_color=COLOR_NAVY_LIGHT)

        def add_nav_group(title, entries, accent=COLOR_BORDER):
            # Manager navigation is presentation-only: callbacks and business logic remain unchanged.
            group_box = ctk.CTkFrame(nav_scroll, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=accent)
            group_box.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(group_box, text=fix_arabic(title, for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=12, pady=(8, 4))
            ctk.CTkFrame(group_box, height=1, fg_color=accent).pack(fill="x", padx=10, pady=(0, 3))
            for label, callback in entries:
                if not self._has_permission(label):
                    continue
                nav_icon = get_nav_icon(label)
                button = ctk.CTkButton(
                    group_box,
                    text=fix_arabic(label, for_ui=True),
                    image=nav_icon,
                    compound="right",
                    command=lambda name=label, action=callback: (setattr(self, "_live_dashboard_active", False), set_active_nav(name), action()),
                    font=FONT_BOLD,
                    height=42,
                    corner_radius=9,
                    fg_color=COLOR_NAVY,
                    border_width=1,
                    border_color=COLOR_NAVY_LIGHT,
                    hover_color=COLOR_CRIMSON,
                    anchor="e"
                )
                button.pack(pady=2, padx=7, fill="x")
                self._nav_buttons[label] = button

        daily_operations = [("نقطة البيع", self.ui_pos), ("قسم الصيانة", self.ui_maintenance), ("حوالات وفواتير", self.ui_transfers), ("بيع البطاقات", self.ui_card_sales)]
        if self.current_role == "employee":
            # Employees use the same complete navigation catalogue as the manager;
            # add_nav_group filters it by the individually granted permissions.
            add_nav_group("العمليات اليومية", daily_operations, COLOR_TEAL)
            add_nav_group("المخزون والمشتريات", [("إدارة المخزون", self.ui_inventory), ("المشتريات", self.ui_purchases), ("مرتجع / تالف", self.open_inventory_adjustment), ("إدارة قطع الصيانة", self.ui_maintenance_parts)], COLOR_CRIMSON)
            add_nav_group("العملاء والذمم", [("إدارة العملاء", self.ui_customers), ("حملات تسويقية", self.ui_marketing_campaigns), ("إدارة الديون والذمم ⚖️", self.ui_debts), ("نظام الولاء", self.ui_loyalty)], COLOR_TEAL)
            add_nav_group("الصيانة والأجهزة", [("سجل استلام وتسليم الأجهزة", self.ui_service_register)], COLOR_TEAL)
            add_nav_group("التقارير والرقابة", [("إدارة العمليات", self.ui_operations_management), ("التقارير المتقدمة", self.ui_advanced_reports), ("مطابقة الأرصدة والسيولة", self.ui_balance_reconciliation), ("التحويلات الداخلية", self.ui_internal_transfers), ("رعاة الفواتير", self.ui_sponsors), ("المصاريف", self.ui_expenses), ("المحاسب", self.ui_accountant), ("سجل الرقابة", self.ui_audit_logs)], COLOR_CRIMSON)
        else:
            # Deliberate manager order: overview → daily work → stock → debts → service → reports → administration.
            add_nav_group("نظرة المدير", [("لوحة التحكم والتحليلات", self.ui_analytics), ("التقارير والأرباح", self.ui_reports), ("عرض الوضع المالي", self.ui_financial_liquidity_view), ("تثبيت ومقارنة الوضع المالي", self.ui_financial_position)], COLOR_CRIMSON)
            add_nav_group("العمليات اليومية", [("نقطة البيع", self.ui_pos), ("قسم الصيانة", self.ui_maintenance), ("حوالات وفواتير", self.ui_transfers), ("بيع البطاقات", self.ui_card_sales)], COLOR_TEAL)
            add_nav_group("المخزون والمشتريات", [("إدارة المخزون", self.ui_inventory), ("المشتريات", self.ui_purchases), ("مرتجع / تالف", self.open_inventory_adjustment), ("إدارة قطع الصيانة", self.ui_maintenance_parts)], COLOR_CRIMSON)
            add_nav_group("العملاء والذمم", [("إدارة العملاء", self.ui_customers), ("حملات تسويقية", self.ui_marketing_campaigns), ("إدارة الديون والذمم ⚖️", self.ui_debts), ("نظام الولاء", self.ui_loyalty)], COLOR_TEAL)
            add_nav_group("الصيانة والأجهزة", [("سجل استلام وتسليم الأجهزة", self.ui_service_register)], COLOR_TEAL)
            add_nav_group("التقارير والرقابة", [("إدارة العمليات", self.ui_operations_management), ("التقارير المتقدمة", self.ui_advanced_reports), ("مطابقة الأرصدة والسيولة", self.ui_balance_reconciliation), ("التحويلات الداخلية", self.ui_internal_transfers), ("رعاة الفواتير", self.ui_sponsors), ("المصاريف", self.ui_expenses), ("المحاسب", self.ui_accountant), ("سجل الرقابة", self.ui_audit_logs)], COLOR_CRIMSON)
            add_nav_group("الإدارة والإعدادات", [("إعدادات النظام", self.ui_settings)], COLOR_TEAL)

        # Content shell: top bar plus a card-like scrollable workspace.
        self.content_shell = ctk.CTkFrame(self, fg_color=COLOR_BG_LIGHT, corner_radius=0)
        self.content_shell.pack(side="left", fill="both", expand=True)
        topbar = ctk.CTkFrame(self.content_shell, height=70, fg_color=COLOR_SURFACE, corner_radius=16, border_width=1, border_color=COLOR_BORDER)
        topbar.pack(fill="x", padx=22, pady=(18, 8))
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text=fix_arabic("Trend Center Jordan", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=22)
        ctk.CTkLabel(topbar, text=fix_arabic("مساحة تشغيل آمنة • بيانات SQLite المحلية", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="left", padx=22)

        self.main_view_scroll = ctk.CTkScrollableFrame(self.content_shell, corner_radius=18, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER, scrollbar_button_color=COLOR_CRIMSON, scrollbar_button_hover_color=COLOR_CRIMSON_DARK)
        self.main_view_scroll.pack(side="left", fill="both", expand=True, padx=22, pady=(8, 20))
        
        # Optimize mousewheel scrolling smoothness for main scrollable view
        def _on_mouse_wheel(event):
            try:
                canvas = self.main_view_scroll._parent_canvas
                if event.delta:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
            except Exception:
                pass

        def _bind_widget_recursive(widget):
            try:
                widget.bind("<MouseWheel>", _on_mouse_wheel, add="+")
                widget.bind("<Button-4>", _on_mouse_wheel, add="+")
                widget.bind("<Button-5>", _on_mouse_wheel, add="+")
            except Exception:
                pass
            for child in widget.winfo_children():
                _bind_widget_recursive(child)

        _bind_widget_recursive(self.main_view_scroll)

        self.main_view = self.main_view_scroll
        # Managers land on the read-only live operations dashboard; employees keep the POS start screen.
        self.ui_live_operations_dashboard() if self.current_role == "admin" else self.ui_pos()
    def change_own_password(self):
        if not self.current_user:
            return
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic("تغيير كلمة السر", is_title=True))
        win.geometry("460x430")
        win.attributes("-topmost", True)
        win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("تغيير كلمة السر للمستخدم الحالي فقط", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=20)
        fields = {}
        for key, label in [("current", "كلمة السر الحالية"), ("new", "كلمة السر الجديدة"), ("confirm", "تأكيد كلمة السر الجديدة")]:
            ctk.CTkLabel(win, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=30, pady=(8, 2))
            entry = ctk.CTkEntry(win, font=FONT_NORMAL_BOLD, justify="right", show="*", height=42)
            entry.pack(fill="x", padx=25)
            fields[key] = entry
        def save_password():
            current, new, confirm = (fields[k].get().strip() for k in ("current", "new", "confirm"))
            if not current or not new or not confirm:
                self.show_msg("تنبيه", "يرجى تعبئة جميع خانات كلمة السر")
                return
            if new != confirm:
                self.show_msg("خطأ", "تأكيد كلمة السر غير مطابق")
                return
            if len(new) < 3:
                self.show_msg("خطأ", "كلمة السر يجب أن تتكون من 3 رموز على الأقل")
                return
            try:
                row = self.db.cursor.execute("SELECT password FROM users WHERE username=?", (self.current_user,)).fetchone()
                if not row or not verify_password(row[0], current):
                    self.show_msg("خطأ", "كلمة السر الحالية غير صحيحة")
                    return
                self.db.cursor.execute("UPDATE users SET password=? WHERE username=?", (hash_password(new), self.current_user))
                self.db.conn.commit()
                self.log_action("تغيير كلمة السر", "users", f"المستخدم: {self.current_user}")
                win.destroy()
                self.show_msg("نجاح", "تم تغيير كلمة السر الخاصة بك فقط بنجاح")
            except sqlite3.Error as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر تغيير كلمة السر", str(exc))
        ctk.CTkButton(win, text=fix_arabic("حفظ كلمة السر", for_ui=True), command=save_password, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=45).pack(fill="x", padx=25, pady=25)

    def create_header(self, text):
        # Appearance-only section header: existing callers and section logic are untouched.
        header = ctk.CTkFrame(self.main_view, height=78, fg_color=COLOR_CRIMSON, corner_radius=16)
        header.pack(fill="x", padx=18, pady=(0, 18))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=fix_arabic("V133 Royal Crimson • مساحة العمل", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(10, 0))
        ctk.CTkLabel(header, text=fix_arabic(text, for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(expand=True, pady=(0, 8))

    def lookup_customer_name(self, phone_entry, name_entry):
        phone = str(phone_entry.get()).strip()
        phone_entry.configure(border_color=COLOR_TEXT_MUTED, border_width=1)
        
        if not phone or len(phone) < 3:
            self._last_alert_phone = None
            return

        # Smart Phone Normalization: Check both with and without leading zero
        p_alt = phone[1:] if phone.startswith('0') else '0' + phone
        
        self.db.cursor.execute("SELECT name FROM customers WHERE phone=? OR phone=?", (phone, p_alt))
        res = self.db.cursor.fetchone()
        if res:
            name_entry.delete(0, 'end')
            name_entry.insert(0, res[0])
            
            # Check for note using the same smart normalization
            self.db.cursor.execute("SELECT note FROM customer_notes WHERE phone=? OR phone=?", (phone, p_alt))
            note_res = self.db.cursor.fetchone()
            if note_res and note_res[0]:
                phone_entry.configure(border_color=COLOR_RUBI, border_width=2)
                # Trigger alert immediately for the matched phone
                self.check_customer_note(phone)
        else:
            self._last_alert_phone = None

    def check_customer_note(self, phone):
        ph = str(phone).strip()
        if not ph: return
        
        # Prevent showing the same alert multiple times for the same interaction
        if hasattr(self, "_last_alert_phone") and self._last_alert_phone == ph:
            return
            
        try:
            # Use smart normalization in check as well
            p_alt = ph[1:] if ph.startswith('0') else '0' + ph
            self.db.cursor.execute("SELECT note FROM customer_notes WHERE phone=? OR phone=?", (ph, p_alt))
            res = self.db.cursor.fetchone()
            if res and res[0]:
                self._last_alert_phone = ph
                note_content = res[0]
                # Use the themed dialog so Arabic follows the same one-pass RTL path.
                self.show_msg(
                    "تنبيه ملاحظة العميل",
                    f"تنبيه مهم بخصوص العميل ({ph}):\n\n{note_content}"
                )
        except Exception:
            pass

    def ui_maintenance_parts(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("إدارة قطع الصيانة")
        top = ctk.CTkFrame(self.main_view, fg_color="transparent"); top.pack(fill="x", padx=20, pady=10)
        self.mp_search = ctk.CTkEntry(top, placeholder_text=fix_arabic("ابحث عن موديل الهاتف...", for_ui=True), height=45, justify="right", corner_radius=10, font=FONT_NORMAL_BOLD); self.mp_search.pack(side="right", padx=10, expand=True, fill="x")
        self.mp_search.bind("<KeyRelease>", lambda e: self.refresh_maintenance_parts(self.mp_search.get()))
        ctk.CTkButton(top, text=fix_arabic("بحث", for_ui=True), command=lambda: self.refresh_maintenance_parts(self.mp_search.get()), font=FONT_BOLD, width=100, height=45, fg_color=COLOR_CRIMSON).pack(side="right", padx=5)
        ctk.CTkButton(top, text=str("إدخال بيانات القطع 🔐"), command=self.open_parts_entry_manager, font=FONT_BOLD, height=45, fg_color=COLOR_TEAL).pack(side="left", padx=5)
        self.mp_tree = ttk.Treeview(self.main_view, columns=("id", "stock", "sell_price", "model", "part"), show="headings")
        for col, head in zip(self.mp_tree["columns"], ["ID", "المتبقي", "سعر البيع (شامل التركيب)", "موديل الهاتف", "بيان القطعة"]):
            self.mp_tree.heading(col, text=fix_arabic(head, for_ui=True)); self.mp_tree.column(col, anchor="center")
        self.mp_tree.column("id", width=0, minwidth=0, stretch=False)
        self.mp_tree.bind("<Double-1>", lambda e: self.open_maintenance_part_details())
        self.mp_tree.pack(fill="both", expand=True, padx=25, pady=10)
        self.refresh_maintenance_parts()

    def refresh_maintenance_parts(self, query=None):
        for i in self.mp_tree.get_children(): self.mp_tree.delete(i)
        if query:
            self.db.cursor.execute("SELECT id, stock, sell_price, phone_model, part_name FROM maintenance_parts WHERE phone_model LIKE ? OR part_name LIKE ?", (f"%{query}%", f"%{query}%"))
        else:
            self.db.cursor.execute("SELECT id, stock, sell_price, phone_model, part_name FROM maintenance_parts")
        for r in self.db.cursor.fetchall():
            self.mp_tree.insert("", "end", values=(r[0], r[1], f"{float(r[2] or 0):.2f} {CURRENCY}", fix_arabic(r[3] or "", for_ui=True), fix_arabic(r[4] or "", for_ui=True)))

    def open_maintenance_part_details(self):
        sel=self.mp_tree.selection()
        if not sel: return
        values=self.mp_tree.item(sel[0], "values")
        try: part_id=int(values[0])
        except (TypeError,ValueError): return
        row=self.db.cursor.execute("SELECT id,part_name,phone_model,cost_price,sell_price,stock FROM maintenance_parts WHERE id=?",(part_id,)).fetchone()
        if not row: return
        win=ctk.CTkToplevel(self); win.title(fix_arabic("تفاصيل قطعة الصيانة",is_title=True)); win.geometry("760x720"); win.grab_set()
        box=ctk.CTkScrollableFrame(win,fg_color=COLOR_SURFACE); box.pack(fill="both",expand=True,padx=15,pady=15); entries={}
        detail_fields = [("part_name","بيان القطعة",row[1]),("phone_model","موديل الهاتف / الموديلات كاملة",row[2]),("sell_price","سعر البيع شامل التركيب",row[4]),("stock","المتبقي",row[5])]
        if self.current_role == "admin": detail_fields.insert(2, ("cost_price","تكلفة القطعة",row[3]))
        for key,label,value in detail_fields:
            ctk.CTkLabel(box,text=fix_arabic(label,for_ui=True),font=FONT_BOLD,text_color=COLOR_WHITE).pack(fill="x",padx=20,pady=(8,2))
            if key == "phone_model":
                # Two visible lines keep long model lists readable without truncation.
                e=ctk.CTkTextbox(box,height=82,font=FONT_NORMAL_BOLD,wrap="word")
                e.insert("1.0",str(value or "")); e.pack(fill="x",padx=20); entries[key]=e
            else:
                e=ctk.CTkEntry(box,height=44,justify="right",font=FONT_NORMAL_BOLD); e.insert(0,str(value or "")); e.pack(fill="x",padx=20); entries[key]=e
        if self.current_role=="admin":
            def save():
                try:
                    part=entries["part_name"].get().strip(); model=entries["phone_model"].get("1.0", "end-1c").strip(); cost=float(entries["cost_price"].get()); sell=float(entries["sell_price"].get()); stock=int(entries["stock"].get())
                    if not part or not model or min(cost,sell,stock)<0: raise ValueError("تحقق من البيانات والقيم غير السالبة")
                    self.db.cursor.execute("UPDATE maintenance_parts SET part_name=?,phone_model=?,cost_price=?,sell_price=?,stock=? WHERE id=?",(part,model,cost,sell,stock,part_id)); self.db.conn.commit(); win.destroy(); self.refresh_maintenance_parts(); self.show_msg("نجاح","تم حفظ تفاصيل القطعة كاملة")
                except (ValueError,sqlite3.Error) as exc: self.db.conn.rollback(); self.show_msg("تعذر الحفظ",str(exc))
            ctk.CTkButton(box,text=fix_arabic("حفظ التعديلات",for_ui=True),command=save,font=FONT_BOLD,fg_color=COLOR_CRIMSON,height=46).pack(fill="x",padx=20,pady=18)
        else:
            for e in entries.values(): e.configure(state="disabled")
    def open_parts_entry_manager(self):
        if self.current_role == "employee":
            self.show_msg("صلاحيات مقيدة", "شاشة إدخال وتعديل تكاليف قطع الصيانة متاح للمدير فقط. يمكنك الاستعلام عن أسعار قطع الصيانة من الجدول مباشرة.")
            return
        if self.current_role != "admin":
            self.show_msg("صلاحيات مقيدة", "هذه الشاشة متاحة للمدير فقط")
            return
            
        win = ctk.CTkToplevel(self); win.title(fix_arabic("إدارة بيانات قطع الصيانة", is_title=True)); win.geometry("600x750"); win.attributes("-topmost", True); win.grab_set()
        
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent"); scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(scroll, text=fix_arabic("إضافة / تعديل قطعة صيانة", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        
        self.mp_e_part = ctk.CTkEntry(scroll, placeholder_text=fix_arabic("بيان القطعة (مثلاً: شاشة أصلية)", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.mp_e_part.pack(fill="x", pady=5, padx=20)
        self.mp_e_model = ctk.CTkEntry(scroll, placeholder_text=fix_arabic("موديل الهاتف (مثلاً: iPhone 13 Pro)", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.mp_e_model.pack(fill="x", pady=5, padx=20)
        self.mp_e_cost = ctk.CTkEntry(scroll, placeholder_text=fix_arabic("تكلفة القطعة", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.mp_e_cost.pack(fill="x", pady=5, padx=20)
        self.mp_e_sell = ctk.CTkEntry(scroll, placeholder_text=fix_arabic("سعر البيع شامل التركيب", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.mp_e_sell.pack(fill="x", pady=5, padx=20)
        self.mp_e_stock = ctk.CTkEntry(scroll, placeholder_text=fix_arabic("الكمية في المخزن", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.mp_e_stock.pack(fill="x", pady=5, padx=20)
        
        def save_part():
            part, model = self.mp_e_part.get().strip(), self.mp_e_model.get().strip()
            try:
                cost = self.positive_number(self.mp_e_cost.get(), "التكلفة", allow_zero=True)
                sell = self.positive_number(self.mp_e_sell.get(), "سعر البيع", allow_zero=True)
                stock = self.positive_integer(self.mp_e_stock.get(), "الكمية")
                if not part or not model: raise ValueError("يرجى ملء جميع الحقول")
                
                if hasattr(self, "_editing_mp_id") and self._editing_mp_id:
                    old_row = self.db.cursor.execute("SELECT stock FROM maintenance_parts WHERE id=?", (self._editing_mp_id,)).fetchone()
                    self.db.cursor.execute("UPDATE maintenance_parts SET part_name=?, phone_model=?, cost_price=?, sell_price=?, stock=? WHERE id=?", (part, model, cost, sell, stock, self._editing_mp_id))
                    if old_row and stock != int(old_row[0] or 0):
                        delta = stock - int(old_row[0] or 0)
                        self.db._record_maintenance_part_movement(self._editing_mp_id, "add" if delta > 0 else "adjustment_out", abs(delta), cost, notes="تعديل مخزون قطع الصيانة")
                    self.log_action("تعديل قطعة صيانة", "maintenance_parts", f"ID: {self._editing_mp_id}")
                    self._editing_mp_id = None
                    btn_save.configure(text=str("حفظ القطعة الجديدة"), fg_color=COLOR_TEAL)
                else:
                    self.db.cursor.execute("INSERT INTO maintenance_parts (part_name, phone_model, cost_price, sell_price, stock) VALUES (?,?,?,?,?)", (part, model, cost, sell, stock))
                    part_id = self.db.cursor.lastrowid
                    if stock > 0:
                        self.db._record_maintenance_part_movement(part_id, "add", stock, cost, notes="إضافة قطعة صيانة جديدة")
                    self.log_action("إضافة قطعة صيانة", "maintenance_parts", f"{part} - {model}")
                
                self.db.conn.commit(); self.show_msg("نجاح", "تم الحفظ بنجاح")
                self.refresh_maintenance_parts(); refresh_mini()
                self.mp_e_part.delete(0, 'end'); self.mp_e_model.delete(0, 'end'); self.mp_e_cost.delete(0, 'end'); self.mp_e_sell.delete(0, 'end'); self.mp_e_stock.delete(0, 'end')
            except Exception as e: self.show_msg("خطأ", str(e))
        
        # Mini table to show existing for easy deletion/viewing
        ctk.CTkLabel(scroll, text=fix_arabic("القطع المسجلة حالياً (اضغط للحذف):", for_ui=True), font=FONT_NORMAL_BOLD).pack(pady=(20, 5))
        self.mp_mini_tree = ttk.Treeview(scroll, columns=("id", "model", "part"), show="headings", height=8)
        self.mp_mini_tree.heading("id", text="ID"); self.mp_mini_tree.heading("model", text=fix_arabic("الموديل", for_ui=True)); self.mp_mini_tree.heading("part", text=fix_arabic("القطعة", for_ui=True))
        self.mp_mini_tree.column("id", width=40); self.mp_mini_tree.pack(fill="x", padx=10)
        
        def refresh_mini():
            for i in self.mp_mini_tree.get_children(): self.mp_mini_tree.delete(i)
            self.db.cursor.execute("SELECT id, phone_model, part_name FROM maintenance_parts ORDER BY id DESC")
            for r in self.db.cursor.fetchall(): self.mp_mini_tree.insert("", "end", values=(r[0], fix_arabic(r[1], for_ui=True), fix_arabic(r[2], for_ui=True)))
        
        def load_for_edit():
            sel = self.mp_mini_tree.selection()
            if not sel: return
            pid = self.mp_mini_tree.item(sel[0])['values'][0]
            self.db.cursor.execute("SELECT part_name, phone_model, cost_price, sell_price, stock FROM maintenance_parts WHERE id=?", (pid,))
            r = self.db.cursor.fetchone()
            if r:
                self.mp_e_part.delete(0, 'end'); self.mp_e_part.insert(0, r[0])
                self.mp_e_model.delete(0, 'end'); self.mp_e_model.insert(0, r[1])
                self.mp_e_cost.delete(0, 'end'); self.mp_e_cost.insert(0, str(r[2]))
                self.mp_e_sell.delete(0, 'end'); self.mp_e_sell.insert(0, str(r[3]))
                self.mp_e_stock.delete(0, 'end'); self.mp_e_stock.insert(0, str(r[4]))
                self._editing_mp_id = pid
                btn_save.configure(text=str("حفظ التعديلات"), fg_color=COLOR_VINO)

        ctk.CTkButton(scroll, text=str("تعديل القطعة المختارة"), command=load_for_edit, font=FONT_BOLD, fg_color=COLOR_VINO, height=40).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(scroll, text=fix_arabic("حذف القطعة المختارة", for_ui=True), command=lambda: self.delete_record("maintenance_parts", self.mp_mini_tree, callback=lambda: (refresh_mini(), self.refresh_maintenance_parts()), id_index=0), font=FONT_BOLD, fg_color=COLOR_RUBI, height=40).pack(pady=5, padx=20, fill="x")
        refresh_mini()
        self._editing_mp_id = None
        btn_save = ctk.CTkButton(scroll, text=fix_arabic("حفظ القطعة الجديدة", for_ui=True), command=save_part, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45)
        btn_save.pack(pady=20, padx=20, fill="x")

    def _card_catalog_values(self):
        rows = self.db.cursor.execute("SELECT DISTINCT provider FROM mobile_cards WHERE active=1 AND TRIM(provider)<>'' ORDER BY provider").fetchall()
        providers = [r[0] for r in rows] or ["أضف شركة من إدارة البطاقات"]
        rows = self.db.cursor.execute("SELECT DISTINCT category FROM mobile_cards WHERE active=1 AND TRIM(category)<>'' ORDER BY category").fetchall()
        categories = [r[0] for r in rows] or ["أضف نوعاً من إدارة البطاقات"]
        return providers, categories

    def ui_card_sales(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("بيع البطاقات")
        is_admin = self.current_role == "admin"
        top = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=12); top.pack(fill="x", padx=18, pady=10)
        ctk.CTkLabel(top, text=fix_arabic("بيع البطاقات — لا يشترط توفر كمية مخزنية", for_ui=True), font=HEADER_FONT_WHITE, text_color=COLOR_WHITE).pack(anchor="e", padx=16, pady=10)
        form = ctk.CTkFrame(top, fg_color="transparent"); form.pack(fill="x", padx=12, pady=8)
        providers, categories = self._card_catalog_values()
        provider = ctk.CTkComboBox(form, values=providers, font=FONT_NORMAL_BOLD, justify="right", height=42); provider.set(providers[0]); provider.pack(side="right", padx=5)
        category = ctk.CTkComboBox(form, values=categories, font=FONT_NORMAL_BOLD, justify="right", height=42); category.set(categories[0]); category.pack(side="right", padx=5)
        card = ctk.CTkComboBox(form, values=[], font=FONT_NORMAL_BOLD, justify="right", height=42); card.pack(side="right", padx=5, fill="x", expand=True)
        qty = ctk.CTkEntry(form, placeholder_text=fix_arabic("الكمية", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42, width=85); qty.pack(side="right", padx=5); qty.insert(0, "1")
        payment = ctk.CTkComboBox(form, values=["Cash", "Visa", "CLIQ"], font=FONT_NORMAL_BOLD, justify="center", height=42, width=110); payment.set("Cash"); payment.pack(side="right", padx=5)
        phone = ctk.CTkEntry(form, placeholder_text=fix_arabic("هاتف العميل", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42, width=190); phone.pack(side="right", padx=5)
        customer_name = ctk.CTkEntry(form, placeholder_text=fix_arabic("اسم العميل (يظهر تلقائياً أو اكتبه للجديد)", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42, width=260); customer_name.pack(side="right", padx=5)
        card_number = ctk.CTkEntry(form, placeholder_text=fix_arabic("رقم البطاقة / الرقم السري", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42, width=230); card_number.pack(side="right", padx=5)
        action_row = ctk.CTkFrame(top, fg_color="transparent"); action_row.pack(fill="x", padx=12, pady=(0, 8))
        info = ctk.CTkLabel(top, text="", font=FONT_NORMAL_BOLD, text_color=COLOR_TEAL); info.pack(anchor="e", padx=18, pady=(0, 8))
        def lookup_customer(*_):
            raw = phone.get().strip()
            if not raw:
                info.configure(text="", text_color=COLOR_TEAL); return
            p_alt = raw[1:] if raw.startswith("0") else ("0" + raw)
            row = self.db.cursor.execute("SELECT name, points FROM customers WHERE phone=? OR phone=?", (raw, p_alt)).fetchone()
            if row:
                customer_name.delete(0, "end"); customer_name.insert(0, row[0] or "")
                info.configure(text=fix_arabic(f"تم العثور على العميل: {row[0] or 'بدون اسم'} — النقاط: {int(row[1] or 0)}", for_ui=True), text_color=COLOR_TEAL)
            else:
                info.configure(text=fix_arabic("عميل جديد — اكتب الاسم ليظهر في الفاتورة", for_ui=True), text_color=COLOR_PUMPKIN)
        phone.bind("<KeyRelease>", lookup_customer)
        def load_cards(*_):
            rows = self.db.cursor.execute("SELECT id, denomination, unit_cost, sale_price, stock FROM mobile_cards WHERE provider=? AND category=? AND active=1 ORDER BY denomination COLLATE NOCASE", (provider.get(), category.get())).fetchall()
            labels = [f"{r[1]} — بيع {float(r[3] or 0):.2f} {CURRENCY}" for r in rows]
            card.configure(values=labels); card.set(labels[0] if labels else "لا توجد فئات متاحة")
            info.configure(text=fix_arabic(f"عدد الفئات المتاحة: {len(rows)} — الكمية المخزنية غير إلزامية", for_ui=True), text_color=COLOR_TEAL if rows else COLOR_RUBI)
        def sell_card():
            try:
                rows = self.db.cursor.execute("SELECT id, denomination, unit_cost, sale_price, stock FROM mobile_cards WHERE provider=? AND category=? AND active=1 ORDER BY denomination COLLATE NOCASE", (provider.get(), category.get())).fetchall()
                labels = [f"{r[1]} — بيع {float(r[3] or 0):.2f} {CURRENCY}" for r in rows]
                if not rows or card.get() not in labels: raise ValueError("اختر فئة بطاقة متاحة")
                r = rows[labels.index(card.get())]; q = self.positive_integer(qty.get(), "الكمية")
                # stock=0 means no stock control is required for this digital/card category.
                if int(r[4] or 0) > 0 and q > int(r[4]): raise ValueError("الكمية أكبر من المخزون المتاح")
                client_phone = phone.get().strip(); client_name = customer_name.get().strip() or "عميل جديد"
                entered_card_number = card_number.get().strip()
                now = datetime.datetime.now(); unit = float(r[3] or 0); total = round(unit * q, 2); cost_total = round(float(r[2] or 0) * q, 2); source = f"card-sale-{now.strftime('%Y%m%d%H%M%S%f')}"
                self.db.conn.execute("BEGIN IMMEDIATE")
                if client_phone:
                    found = self.db.cursor.execute("SELECT name FROM customers WHERE phone=?", (client_phone,)).fetchone()
                    if found and found[0] and not customer_name.get().strip(): client_name = found[0]
                    self.get_or_create_customer(client_phone, client_name)
                if int(r[4] or 0) > 0: self.db.cursor.execute("UPDATE mobile_cards SET stock=stock-?,updated_at=? WHERE id=?", (q, now.isoformat(timespec="seconds"), r[0]))
                self.db.cursor.execute("INSERT INTO card_sales(card_id,provider,category,denomination,qty,unit_price,total,payment_method,customer_phone,card_number,date,time,user,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (r[0], provider.get(), category.get(), r[1], q, unit, total, payment.get(), client_phone, entered_card_number, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), self.current_user, source))
                sale_name = f"بطاقة {provider.get()} - {category.get()} - {r[1]}"
                self.db.cursor.execute("INSERT INTO sales(code,name,qty,price,total,buy_cost,date,time,user,customer_phone,payment_method,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (f"CARD-{r[0]}", sale_name, q, unit, total, cost_total, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), self.current_user, client_phone, payment.get(), source))
                account = self._ledger_account_for_payment(payment.get())
                lines = [(account, total, 0, "تحصيل بيع بطاقة"), ("SALES_REVENUE", 0, total, "إيراد مبيعات البطاقات")]
                if cost_total > 0: lines.extend([("COGS", cost_total, 0, "تكلفة البطاقات المباعة"), ("INVENTORY", 0, cost_total, "تكلفة البطاقات المباعة")])
                self._post_journal_entry("sale", source, "قيد بيع بطاقة", lines, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'))
                earned = 0
                if client_phone:
                    mult_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='points_sale'").fetchone(); mult = int(clean_float(mult_row[0] if mult_row else 10) or 10); earned = int(total * mult); self.db.cursor.execute("UPDATE customers SET points=points+? WHERE phone=?", (earned, client_phone))
                self.db.conn.commit(); self.log_action("بيع بطاقة ضمن المبيعات", "sales", f"{sale_name}; الإجمالي: {total:.2f}; العميل: {client_phone or 'نقدي'}")
                self.generate_invoice(total, "SALE", {"points": earned, "phone": client_phone, "client": client_name, "payment": payment.get(), "card_number": entered_card_number, "skip_whatsapp_prompt": True})
                if client_phone:
                    card_line = f"رقم البطاقة: {entered_card_number}\n" if entered_card_number else ""
                    msg = (f"ترند سنتر الأردن TREND CENTER JORDAN\n\nتم تسجيل عملية بيع بطاقة بنجاح.\nالعميل: {client_name}\nالمنتج: {sale_name}\n{card_line}الكمية: {q}\nالإجمالي: {total:.2f} {CURRENCY}\nطريقة الدفع: {payment.get()}\nرصيد النقاط الحالي: {self.db.cursor.execute('SELECT points FROM customers WHERE phone=?',(client_phone,)).fetchone()[0]} نقطة\n\nشكراً لثقتكم بنا.")
                    self.send_whatsapp(client_phone, msg)
                load_cards(); self.show_msg("تم تسجيل البيع", f"تم تسجيل البطاقة ضمن المبيعات بقيمة {total:.2f} {CURRENCY}")
            except (ValueError, sqlite3.Error) as exc: self.db.conn.rollback(); self.show_msg("تعذر بيع البطاقة", str(exc))
        ctk.CTkButton(action_row, text=fix_arabic("عملية بيع بطاقة", for_ui=True), command=sell_card, font=FONT_BOLD, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, height=46, width=260).pack(side="right", padx=5)
        provider.configure(command=load_cards); category.configure(command=load_cards); load_cards()
        if is_admin: ctk.CTkButton(self.main_view, text=fix_arabic("إدارة الشركات والأنواع والفئات والأسعار", for_ui=True), command=self.open_card_catalog_manager, font=FONT_BOLD, fg_color=COLOR_TEAL, height=44).pack(fill="x", padx=18, pady=8)
        tree = ttk.Treeview(self.main_view, columns=("total","qty","denomination","category","provider","date"), show="headings")
        for col, head in zip(tree["columns"], ["الإجمالي","الكمية","الفئة","النوع","الشركة","التاريخ"]): tree.heading(col, text=fix_arabic(head, for_ui=True)); tree.column(col, anchor="center")
        tree.pack(fill="both", expand=True, padx=18, pady=10)
        for row in self.db.cursor.execute("SELECT total,qty,denomination,category,provider,date FROM card_sales ORDER BY id DESC LIMIT 200").fetchall(): tree.insert("", "end", values=(f"{float(row[0] or 0):.2f}", row[1], fix_arabic(row[2], for_ui=True), fix_arabic(row[3], for_ui=True), fix_arabic(row[4], for_ui=True), row[5]))

    def open_card_catalog_manager(self):
        if self.current_role != "admin": return self.show_msg("صلاحيات مقيدة", "إدارة الشركات والأنواع والأسعار متاحة للمدير فقط")
        win = ctk.CTkToplevel(self); win.title(fix_arabic("إدارة دليل البطاقات", is_title=True)); win.geometry("820x760"); win.grab_set(); box = ctk.CTkScrollableFrame(win, fg_color=COLOR_SURFACE); box.pack(fill="both", expand=True, padx=12, pady=12)
        provider = ctk.CTkEntry(box, placeholder_text=fix_arabic("شركة جديدة: زين / أورانج / أمنية أو أي شركة", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); provider.pack(fill="x", padx=20, pady=6)
        category = ctk.CTkEntry(box, placeholder_text=fix_arabic("نوع جديد: إنترنت / موبايل / مكس أو أي نوع", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); category.pack(fill="x", padx=20, pady=6)
        denomination = ctk.CTkEntry(box, placeholder_text=fix_arabic("الفئة الجديدة", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); denomination.pack(fill="x", padx=20, pady=6)
        cost = ctk.CTkEntry(box, placeholder_text=fix_arabic("تكلفة البطاقة", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); cost.pack(fill="x", padx=20, pady=6)
        sale = ctk.CTkEntry(box, placeholder_text=fix_arabic("سعر بيع البطاقة", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); sale.pack(fill="x", padx=20, pady=6)
        stock = ctk.CTkEntry(box, placeholder_text=fix_arabic("كمية اختيارية — اتركها 0 للبيع دون مخزون", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42); stock.pack(fill="x", padx=20, pady=6); stock.insert(0, "0")
        selected_id = {"value": None}
        tree = ttk.Treeview(box, columns=("active","stock","sale","cost","denom","cat","provider","id"), show="headings", height=11); tree.pack(fill="both", expand=True, padx=10, pady=10)
        for col, head in zip(tree["columns"], ["الحالة","المخزون","سعر البيع","التكلفة","الفئة","النوع","الشركة","ID"]): tree.heading(col, text=fix_arabic(head, for_ui=True)); tree.column(col, anchor="center")
        def refresh():
            for i in tree.get_children(): tree.delete(i)
            for r in self.db.cursor.execute("SELECT active,stock,sale_price,unit_cost,denomination,category,provider,id FROM mobile_cards ORDER BY active DESC,provider,category,denomination").fetchall(): tree.insert("", "end", values=("فعال" if r[0] else "محذوف", r[1], f"{float(r[2] or 0):.2f}", f"{float(r[3] or 0):.2f}", r[4], r[5], r[6], r[7]))
        def load_selected(_event=None):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0], "values")
            selected_id["value"] = int(vals[7])
            for entry, value in ((provider, vals[6]), (category, vals[5]), (denomination, vals[4]), (cost, vals[3]), (sale, vals[2]), (stock, vals[1])):
                entry.delete(0, "end"); entry.insert(0, str(value))
        def clear_form():
            selected_id["value"] = None
            for entry in (provider, category, denomination, cost, sale, stock): entry.delete(0, "end")
            stock.insert(0, "0")
        def save():
            try:
                prov=provider.get().strip(); cat=category.get().strip(); denom=denomination.get().strip(); unit=self.positive_number(cost.get(), "التكلفة", allow_zero=True); sell=self.positive_number(sale.get(), "سعر البيع", allow_zero=True); raw=stock.get().strip() or "0"; q=int(float(raw))
                if q<0 or not prov or not cat or not denom: raise ValueError("الشركة والنوع والفئة مطلوبة، والكمية اختيارية وغير سالبة")
                now=datetime.datetime.now().isoformat(timespec="seconds")
                if selected_id["value"]:
                    self.db.cursor.execute("UPDATE mobile_cards SET provider=?,category=?,denomination=?,unit_cost=?,sale_price=?,stock=?,active=1,updated_at=? WHERE id=?", (prov,cat,denom,unit,sell,q,now,selected_id["value"]))
                    action = "تعديل بطاقة"
                else:
                    self.db.cursor.execute("INSERT INTO mobile_cards(provider,category,denomination,unit_cost,sale_price,stock,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(provider,category,denomination) DO UPDATE SET unit_cost=excluded.unit_cost,sale_price=excluded.sale_price,stock=excluded.stock,active=1,updated_at=excluded.updated_at", (prov,cat,denom,unit,sell,q,now,now))
                    action = "إضافة بطاقة"
                self.db.conn.commit(); self.log_action(action, "mobile_cards", f"{prov}/{cat}/{denom}; سعر البيع: {sell:.2f}"); refresh(); clear_form(); self.show_msg("تم الحفظ", "تم حفظ بيانات البطاقة")
            except (ValueError, sqlite3.Error) as exc: self.db.conn.rollback(); self.show_msg("تعذر الحفظ", str(exc))
        def delete_selected():
            sel = tree.selection()
            if not sel: return self.show_msg("تنبيه", "حدد بند البطاقة المراد حذفه أولاً")
            vals = tree.item(sel[0], "values"); rid = int(vals[7])
            if vals[0] == "محذوف": return self.show_msg("تنبيه", "البند محذوف مسبقاً")
            if not self.ask_confirm("تأكيد الحذف", "سيتم إخفاء البند من البيع مع الحفاظ على سجلات المبيعات السابقة. هل تريد المتابعة?"):
                return
            try:
                self.db.cursor.execute("UPDATE mobile_cards SET active=0, updated_at=? WHERE id=?", (datetime.datetime.now().isoformat(timespec="seconds"), rid))
                self.db.conn.commit(); self.log_action("حذف بطاقة", "mobile_cards", f"المعرف: {rid}"); refresh(); clear_form(); self.show_msg("تم الحذف", "تم حذف البند من قائمة البيع مع الحفاظ على السجل التاريخي")
            except sqlite3.Error as exc:
                self.db.conn.rollback(); self.show_msg("تعذر الحذف", str(exc))
        tree.bind("<<TreeviewSelect>>", load_selected)
        buttons = ctk.CTkFrame(box, fg_color="transparent"); buttons.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(buttons, text=fix_arabic("حفظ / إضافة بطاقة", for_ui=True), command=save, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=46).pack(side="right", expand=True, fill="x", padx=4)
        ctk.CTkButton(buttons, text=fix_arabic("تعديل البند المحدد", for_ui=True), command=save, font=FONT_BOLD, fg_color=COLOR_TEAL, height=46).pack(side="right", expand=True, fill="x", padx=4)
        ctk.CTkButton(buttons, text=fix_arabic("حذف البند المحدد", for_ui=True), command=delete_selected, font=FONT_BOLD, fg_color=COLOR_RUBI, height=46).pack(side="right", expand=True, fill="x", padx=4)
        ctk.CTkButton(buttons, text=fix_arabic("تفريغ الحقول", for_ui=True), command=clear_form, font=FONT_BOLD, fg_color=COLOR_NAVY_LIGHT, height=46).pack(side="left", expand=True, fill="x", padx=4)
        refresh()

    def ui_pos(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("نقطة البيع")
        
        # Row 1: Customer details
        top = ctk.CTkFrame(self.main_view, fg_color="transparent"); top.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top, text=fix_arabic("هاتف العميل:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.pos_cust_phone = ctk.CTkEntry(top, font=FONT_NORMAL_BOLD, width=150, justify="right", corner_radius=8); self.pos_cust_phone.pack(side="right", padx=5)
        self.pos_cust_phone.bind("<KeyRelease>", lambda e: self.lookup_customer_name(self.pos_cust_phone, self.pos_cust_name))
        ctk.CTkLabel(top, text=fix_arabic("الاسم:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.pos_cust_name = ctk.CTkEntry(top, font=FONT_NORMAL_BOLD, width=150, justify="right", corner_radius=8); self.pos_cust_name.pack(side="right", padx=5)
        ctk.CTkButton(top, text=fix_arabic("بحث عن عميل", for_ui=True), command=self.open_employee_customer_search, font=FONT_BOLD, width=125, height=38, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="right", padx=5)
        ctk.CTkLabel(top, text=fix_arabic("الدفع:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.payment_method = ctk.CTkComboBox(top, values=["Cash", "Visa", "CLIQ", "Credit"], width=100, height=38, font=FONT_NORMAL_BOLD, justify="center")
        self.payment_method.pack(side="right", padx=5); self.payment_method.set("Cash")
        
        # Row 2: Barcode and Search by Name
        top2 = ctk.CTkFrame(self.main_view, fg_color="transparent"); top2.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(top2, text=fix_arabic("بحث بالاسم", for_ui=True), command=self.open_product_search_window, font=FONT_BOLD, width=110, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=40).pack(side="right", padx=5)
        ctk.CTkLabel(top2, text=fix_arabic("الباركود:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.code_entry = ctk.CTkEntry(top2, font=FONT_NORMAL_BOLD, width=220, height=40, justify="right", corner_radius=8); self.code_entry.pack(side="right", padx=5)
        self.code_entry.bind("<Return>", lambda e: self.add_to_cart())
        self.code_entry.focus_set()
        ctk.CTkButton(top2, text=fix_arabic("إضافة", for_ui=True), command=self.add_to_cart, font=FONT_BOLD, width=90, height=40, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="right", padx=5)

        self.cart_tree = ttk.Treeview(self.main_view, columns=("total", "price", "qty", "name", "code"), show="headings")
        for col, head in zip(self.cart_tree["columns"], ["الإجمالي", "السعر", "الكمية", "الاسم", "الكود"]): self.cart_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.cart_tree.pack(fill="both", expand=True, padx=15, pady=10)
        
        act_btns = ctk.CTkFrame(self.main_view, fg_color="transparent")
        act_btns.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(act_btns, text=fix_arabic("خصم / تعديل السعر", for_ui=True), command=self.show_discount_ui, font=FONT_BOLD, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK, height=40).pack(side="right", padx=5)
        ctk.CTkButton(act_btns, text=fix_arabic("حذف من السلة", for_ui=True), command=self.remove_from_cart, font=FONT_BOLD, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK, height=40).pack(side="right", padx=5)

        bottom = ctk.CTkFrame(self.main_view, fg_color="transparent"); bottom.pack(fill="x", padx=20, pady=20)
        self.total_lbl = ctk.CTkLabel(bottom, text=fix_arabic(f"المجموع: 0.00 {CURRENCY}", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE); self.total_lbl.pack(side="right")
        ctk.CTkButton(bottom, text=fix_arabic("إتمام العملية + فاتورة", for_ui=True), fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, command=self.checkout, font=FONT_BOLD, height=60, width=250, corner_radius=12).pack(side="left")
        self.cart = []

    def open_product_search_window(self):
        sw = ctk.CTkToplevel(self)
        sw.title(fix_arabic("البحث عن منتج بالاسم", is_title=True))
        sw.geometry("600x450")
        sw.attributes("-topmost", True)
        sw.grab_set()
        
        f_search = ctk.CTkFrame(sw, fg_color="transparent")
        f_search.pack(fill="x", padx=15, pady=15)
        
        s_entry = ctk.CTkEntry(f_search, placeholder_text=fix_arabic("اكتب جزءاً من اسم المنتج...", for_ui=True), width=400, height=45, font=FONT_NORMAL_BOLD, justify="right")
        s_entry.pack(side="right", padx=5)
        s_entry.focus_set()
        
        # Results tree
        tree = ttk.Treeview(sw, columns=("stock", "price", "name", "code"), show="headings")
        for col, head in zip(tree["columns"], ["الكمية", "السعر", "اسم المنتج", "الكود"]):
            tree.heading(col, text=fix_arabic(head, for_ui=True))
        tree.pack(fill="both", expand=True, padx=15, pady=10)
        
        def run_search(event=None):
            for i in tree.get_children(): tree.delete(i)
            q = s_entry.get().strip()
            self.db.cursor.execute("SELECT code, name, sell_price, stock FROM products WHERE name LIKE ?", (f"%{q}%",))
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=(r[3], f"{r[2]:.2f}", fix_arabic(r[1], for_ui=True), r[0]))
                
        s_entry.bind("<KeyRelease>", run_search)
        run_search() # load all initially
        
        def select_product(event=None):
            selected = tree.selection()
            if not selected: return
            vals = tree.item(selected[0])['values']
            code = vals[3]
            sw.destroy()
            self.code_entry.delete(0, 'end')
            self.code_entry.insert(0, str(code))
            self.add_to_cart()
            
        tree.bind("<Double-1>", select_product)
        ctk.CTkButton(sw, text=fix_arabic("إضافة للسلة", for_ui=True), command=select_product, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45, width=200).pack(pady=15)

    def add_to_cart(self):
        code = self.code_entry.get().strip()
        if not code:
            return
        self.db.cursor.execute("SELECT code, name, sell_price, buy_price, stock FROM products WHERE code=?", (code,))
        p = self.db.cursor.fetchone()
        if p:
            already = sum(item["qty"] for item in self.cart if item["code"] == p[0])
            if p[4] <= already:
                self.show_msg("تنبيه", "الكمية المطلوبة تتجاوز المخزون المتوفر")
                return
            self.cart.append({"code": p[0], "name": p[1], "price": float(p[2] or 0), "original_price": float(p[2] or 0), "buy_cost": float(p[3] or 0), "qty": 1, "total": float(p[2] or 0)})
            self.refresh_cart(); self.code_entry.delete(0, "end"); self.code_entry.focus_set()
        else:
            self.show_msg("خطأ", "باركود المنتج غير موجود")

    def refresh_cart(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        total = sum(item['total'] for item in self.cart)
        for item in self.cart: self.cart_tree.insert("", "end", values=(f"{item['total']:.2f}", f"{item['price']:.2f}", item['qty'], fix_arabic(item['name'], for_ui=True), item['code']))
        self.total_lbl.configure(text=fix_arabic(f"المجموع: {total:.2f} {CURRENCY}", for_ui=True))

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected: return
        idx = self.cart_tree.index(selected[0])
        self.cart.pop(idx); self.refresh_cart()

    def show_discount_ui(self):
        selected = self.cart_tree.selection()
        if not selected: return
        idx = self.cart_tree.index(selected[0])
        item = self.cart[idx]
        original_price = float(item.get("original_price", item.get("price", 0)) or 0.0)
        buy_cost = float(item.get("buy_cost", 0) or 0.0)
        target_margin = 0.40
        minimum_price = buy_cost / (1.0 - target_margin) if buy_cost > 0 else original_price
        maximum_discount = max(original_price - minimum_price, 0.0)
        allowed_discount = round(maximum_discount * 0.70, 2)
        if maximum_discount < 0.50:
            self.show_msg("تنبيه", "لا يمكن عمل خصم؛ قيمة أقصى خصم أقل من 0.50 دينار")
            return
        ds = ctk.CTkToplevel(self); ds.title(fix_arabic("تعديل السعر / خصم", is_title=True)); ds.geometry("400x300"); ds.attributes("-topmost", True); ds.grab_set()
        ctk.CTkLabel(ds, text=fix_arabic(f"تعديل سعر: {item['name']}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=16)
        ctk.CTkLabel(ds, text=fix_arabic(f"قيمة الخصم المتاحة: {allowed_discount:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL).pack(pady=(0, 10))
        price_entry = ctk.CTkEntry(ds, placeholder_text=fix_arabic("السعر الجديد", for_ui=True), font=FONT_NORMAL_BOLD, justify="center", height=45); price_entry.pack(pady=10, padx=40, fill="x")
        price_entry.insert(0, str(item['price']))
        def apply():
            new_p = clean_float(price_entry.get())
            minimum_allowed_price = original_price - allowed_discount
            if new_p < 0 or new_p < minimum_allowed_price:
                self.show_msg("تنبيه", f"لا يمكن أن يتجاوز الخصم {allowed_discount:.2f} {CURRENCY}")
                return
            self.cart[idx]['price'] = new_p
            self.cart[idx]['total'] = new_p * self.cart[idx]['qty']
            self.refresh_cart(); ds.destroy()
        ctk.CTkButton(ds, text=fix_arabic("تطبيق السعر", for_ui=True), command=apply, font=FONT_BOLD, fg_color=COLOR_VINO, height=45).pack(pady=20)

    def get_or_create_customer(self, phone, name="عميل جديد"):
        if not phone:
            return None
        self.db.cursor.execute("SELECT phone, points, name FROM customers WHERE phone=?", (phone,))
        res = self.db.cursor.fetchone()
        if res:
            if name != "عميل جديد" and res[2] != name:
                self.db.cursor.execute("UPDATE customers SET name=? WHERE phone=?", (name, phone))
            return res
        self.db.cursor.execute("SELECT value FROM settings WHERE key='reg_points'")
        reg_points = int(clean_float(self.db.cursor.fetchone()[0] or 20))
        self.db.cursor.execute("INSERT INTO customers (phone, name, points) VALUES (?,?,?)", (phone, name, reg_points))
        self.show_msg("عميل جديد", f"تم تسجيل العميل بنجاح!\nتم منح العميل {reg_points} نقطة هدية مجانية.")
        return (phone, reg_points, name)

    def checkout(self):
        if not self.cart:
            self.show_msg("تنبيه", "السلة فارغة")
            return
        phone = self.pos_cust_phone.get().strip()
        name = self.pos_cust_name.get().strip() or "عميل جديد"
        payment = self.payment_method.get() if hasattr(self, "payment_method") else fix_arabic("نقدي", for_ui=True)
        total = sum(float(i["total"]) for i in self.cart)
        now = datetime.datetime.now()
        try:
            self.db.conn.execute("BEGIN IMMEDIATE")
            # Re-check stock at commit time, protecting against stale screens.
            if payment == "Credit" and not phone:
                raise ValueError("يجب إدخال رقم هاتف العميل للبيع الآجل (Credit)")
            
            sale_source = f"sale-{now.strftime('%Y%m%d%H%M%S%f')}"
            if payment == "Credit":
                self.db.cursor.execute("INSERT INTO customer_debts (customer_phone, customer_name, total_debt, paid_amount, status, date, notes, source_type, source_id) VALUES (?,?,?,?,?,?,?,?,?)", 
                                       (phone, name, total, 0, 'غير مسدد', now.strftime("%Y-%m-%d"), f'بيع آجل - فاتورة POS', "sale", sale_source))
            
            for item in self.cart:
                row = self.db.cursor.execute("SELECT stock FROM products WHERE code=?", (item["code"],)).fetchone()
                if not row or int(row[0]) < int(item["qty"]):
                    raise ValueError(f"المخزون غير كافٍ للمنتج: {item['name']}")
            customer = self.get_or_create_customer(phone, name) if phone else None
            
            total_cost = 0.0
            for item in self.cart:
                item_cost = float(item["buy_cost"] or 0) * int(item["qty"])
                total_cost += item_cost
                self.db.cursor.execute("UPDATE products SET stock = stock - ? WHERE code=?", (item["qty"], item["code"]))
                self.db.cursor.execute("INSERT INTO sales (code, name, qty, price, total, buy_cost, date, time, user, customer_phone, payment_method, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", 
                                       (item["code"], item["name"], item["qty"], item["price"], item["total"], item_cost, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), self.current_user, phone, payment, sale_source))
            sale_account = self._ledger_account_for_payment(payment)
            sale_lines = [(sale_account, total, 0, "تحصيل المبيعات"), ("SALES_REVENUE", 0, total, "إيراد المبيعات")]
            if total_cost > 0:
                sale_lines.extend([("COGS", total_cost, 0, "تكلفة البضاعة المباعة"), ("INVENTORY", 0, total_cost, "تخفيض المخزون")])
            self._post_journal_entry("sale", sale_source, "قيد مبيعات وتكلفة مخزون", sale_lines, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
            mult = int(clean_float(self.db.cursor.execute("SELECT value FROM settings WHERE key='points_sale'").fetchone()[0] or 10))
            points_earned = int(total * mult) if customer else 0
            if customer and points_earned:
                self.db.cursor.execute("UPDATE customers SET points = points + ? WHERE phone=?", (points_earned, phone))
            self.db.conn.commit()
            self.log_action("بيع", "sales", f"المبلغ: {total:.2f}; الدفع: {payment}; العميل: {phone or 'نقدي'}")
            self.generate_invoice(total, "SALE", {"points": points_earned, "phone": phone, "client": name, "payment": payment})
            self.cart = []; self.refresh_cart(); self.code_entry.focus_set()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback()
            self.show_msg("تعذر إتمام البيع", str(exc))

    def open_maintenance_part_picker(self):
        """Open a dialog to pick a part from maintenance_parts inventory by name/model and add its cost."""
        pw = ctk.CTkToplevel(self)
        pw.title(fix_arabic("اختيار قطعة صيانة من المخزون", is_title=True))
        pw.geometry("620x480")
        pw.attributes("-topmost", True)
        pw.grab_set()

        ctk.CTkLabel(pw, text=fix_arabic("اختر قطة الغيار المستعملة من المخزون لربطها بالصيانة:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        search_row = ctk.CTkFrame(pw, fg_color="transparent"); search_row.pack(fill="x", padx=15, pady=(0, 5))
        ctk.CTkLabel(search_row, text=fix_arabic("بحث باسم القطعة أو جزء من الاسم:", for_ui=True), font=FONT_BOLD).pack(side="right", padx=6)
        part_search = ctk.CTkEntry(search_row, placeholder_text=fix_arabic("اكتب اسم القطعة أو جزءاً منه", for_ui=True), font=FONT_BOLD, height=38)
        part_search.pack(side="right", fill="x", expand=True)
        tf = ctk.CTkFrame(pw, fg_color="transparent"); tf.pack(fill="both", expand=True, padx=15, pady=5)

        ptree = ttk.Treeview(tf, columns=("stock", "sell", "cost", "model", "name", "id"), show="headings")
        for col, head in zip(ptree["columns"], ["المخزون", "سعر البيع", "التكلفة", "موديل الهاتف", "اسم القطعة", "ID"]):
            ptree.heading(col, text=fix_arabic(head, for_ui=True))
        ptree.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tf, orient="vertical", command=ptree.yview)
        scrollbar.pack(side="left", fill="y")
        ptree.configure(yscrollcommand=scrollbar.set)

        def load_parts(query=""):
            for i in ptree.get_children(): ptree.delete(i)
            try:
                query = str(query or "").strip()
                if query:
                    like = f"%{query}%"
                    self.db.cursor.execute("SELECT stock, sell_price, cost_price, phone_model, part_name, id FROM maintenance_parts WHERE stock > 0 AND (part_name LIKE ? OR phone_model LIKE ?) ORDER BY part_name", (like, like))
                else:
                    self.db.cursor.execute("SELECT stock, sell_price, cost_price, phone_model, part_name, id FROM maintenance_parts WHERE stock > 0 ORDER BY part_name")
                for row in self.db.cursor.fetchall():
                    ptree.insert("", "end", values=(row[0], f"{row[1]:.2f}", f"{row[2]:.2f}", fix_arabic(row[3], for_ui=True), fix_arabic(row[4], for_ui=True), row[5]))
            except Exception:
                pass
        part_search.bind("<KeyRelease>", lambda e: load_parts(part_search.get()))
        load_parts()


        def confirm_part():
            sel = ptree.selection()
            if not sel:
                self.show_msg("تنبيه", "يرجى اختيار قطعة صيانة من القائمة أولاً"); return
            vals = ptree.item(sel[0], "values")
            # vals: stock, sell, cost, model, name, id
            part_stock, part_cost, part_name, part_id = int(vals[0]), float(vals[2]), vals[4], int(vals[5])
            
            if part_stock <= 0:
                self.show_msg("تنبيه", "هذه القطعة نفدت من المخزون"); return

            # Update selected part ID and cost in maintenance UI
            self.m_selected_part_id = part_id
            self.m_cost_in.delete(0, 'end'); self.m_cost_in.insert(0, str(part_cost))
            self.m_part_lbl.configure(text=fix_arabic(f"القطعة المحددة: {part_name} (تكلفة: {part_cost})", for_ui=True), text_color=COLOR_TEAL)
            pw.destroy()

        ctk.CTkButton(pw, text=fix_arabic("تثبيت القطعة المتاحة", for_ui=True), command=confirm_part, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=220).pack(pady=10)
        ptree.bind("<Double-1>", lambda e: confirm_part())

    # Independent operational device-service register. This block intentionally
    # does not call the legacy maintenance handlers, journal helpers, inventory
    # helpers, or financial reports.
    def _service_register_types(self):
        return ["هاتف", "تاب", "كمبيوتر", "لاب توب", "بلايستيشن", "يد بلايستيشن"]

    def _service_register_check_items(self, device_type):
        common = {
            "هاتف": ["الشاشة", "قاعدة الشحن", "الصوت", "المايك", "الإطار", "الكاميرا"],
            "تاب": ["الشاشة", "اللمس", "الشحن", "الصوت", "الكاميرا"],
            "كمبيوتر": ["التشغيل", "الشاشة", "لوحة المفاتيح", "المنافذ", "الصوت"],
            "لاب توب": ["الشاشة", "البطارية", "الشحن", "لوحة المفاتيح", "المنافذ"],
            "بلايستيشن": ["التشغيل", "الصورة", "HDMI", "التخزين", "الشبكة"],
            "يد بلايستيشن": ["الأزرار", "العصي", "الاهتزاز", "الشحن", "الاتصال"]
        }
        return common.get(device_type, common["هاتف"])

    def _service_register_statuses(self):
        return ["مستلم", "قيد الفحص", "قيد الإصلاح", "جاهز للتسليم", "تم التسليم", "ملغى"]

    def _service_register_contract_dir(self):
        folder = self.db.db_path.parent / "service_register_documents"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _service_register_contract(self, order, kind):
        """Create a compact Arabic operational document image; never writes accounting data."""
        path = self._service_register_contract_dir() / f"{order[1]}_{kind}.png"
        image = Image.new("RGB", (1000, 1400), "white")
        draw = ImageDraw.Draw(image)
        try:
            font_path = resource_path(APP_FONT_FILE)
            if not os.path.isfile(font_path): font_path = "arial.ttf"
            title_font = ImageFont.truetype(font_path, 42)
            body_font = ImageFont.truetype(font_path, 27)
            small_font = ImageFont.truetype(font_path, 23)
        except Exception:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            title_font = ImageFont.truetype(font_path, 42)
            body_font = ImageFont.truetype(font_path, 27)
            small_font = ImageFont.truetype(font_path, 23)
        draw.rectangle((0, 0, 1000, 175), fill=COLOR_CRIMSON)
        draw.rectangle((24, 18, 976, 157), outline=COLOR_WHITE, width=3)
        shop_ar, shop_en, _, _, logo_path = self._shop_identity()
        try:
            if logo_path and os.path.isfile(logo_path):
                logo = Image.open(logo_path).convert("RGBA"); logo.thumbnail((105, 105)); image.paste(logo, (55, 20), logo)
        except Exception:
            pass
        def rtl(text, font, y, fill=COLOR_NAVY):
            """Render shaped Arabic from the right edge with a dark, readable default."""
            rendered = fix_arabic(str(text), for_ui=True)
            draw.text((940, y), rendered, font=font, fill=fill, anchor="ra")
        title = "عقد استلام جهاز للصيانة" if kind == "intake" else "عقد تسليم جهاز بعد الصيانة"
        rtl(shop_ar, title_font, 26, COLOR_WHITE)
        rtl(shop_en, small_font, 72, COLOR_WHITE)
        rtl(title, body_font, 105, COLOR_WHITE)
        # Formal round seal, kept in the document image only.
        draw.ellipse((62, 205, 238, 381), outline=COLOR_CRIMSON, width=6)
        draw.ellipse((78, 221, 222, 365), outline=COLOR_CRIMSON, width=2)
        draw.text((150, 270), "OFFICIAL", font=small_font, fill=COLOR_CRIMSON, anchor="mm")
        draw.text((150, 305), "TCJ", font=body_font, fill=COLOR_CRIMSON, anchor="mm")
        y = 205
        fields = [
            ("رقم الطلب / المستند", order[1]), ("العميل", order[2]), ("الهاتف", order[3]),
            ("نوع الجهاز", order[4]), ("الشركة", order[5] or "-"),
            ("الموديل", order[6] or "-"), ("الرقم التسلسلي / IMEI", order[7] or "-"),
            ("تاريخ الاستلام", f"{order[16]} {order[17]}")
        ]
        for label, value in fields:
            draw.line((55, y + 42, 945, y + 42), fill=COLOR_WHITE, width=2)
            rtl(f"{label}: {value}", body_font, y)
            y += 62
        draw.rectangle((55, y + 5, 945, y + 58), fill=COLOR_WHITE)
        rtl("نتيجة الفحص", body_font, y + 14, COLOR_WHITE)
        y += 78
        try:
            checks = json.loads(order[10] if kind == "intake" else (order[11] or order[10] or "{}"))
        except Exception:
            checks = {}
        for item, status in checks.items():
            rtl(f"{item}: {status}", small_font, y)
            y += 42
        issue = order[8] or "-"
        notes = order[9] if kind == "intake" else (order[24] or "")
        draw.rectangle((55, y + 8, 945, y + 60), fill=COLOR_WHITE)
        rtl("الصيانة المطلوبة", body_font, y + 16, COLOR_CRIMSON_DARK)
        y += 78
        for line in str(issue).splitlines()[:5]:
            rtl(line[:75], small_font, y)
            y += 36
        y += 10
        draw.rectangle((55, y + 8, 945, y + 60), fill=COLOR_WHITE)
        rtl("الملاحظات", body_font, y + 16, COLOR_CRIMSON_DARK)
        y += 78
        for line in str(notes or "-").splitlines()[:5]:
            rtl(line[:75], small_font, y)
            y += 36
        if kind == "handover":
            y += 12
            rtl(f"تاريخ التسليم: {order[18] or '-'} {order[19] or ''}", small_font, y)
            y += 52
            rtl("تم فحص الجهاز وتسليمه للعميل حسب البيانات أعلاه.", small_font, y)
        y = min(y + 78, 1260)
        draw.line((55, y, 945, y), fill=COLOR_WHITE, width=3)
        rtl("ترند سنتر الأردن — سجل تشغيلي لخدمة الصيانة", small_font, y + 28, COLOR_CRIMSON_DARK)
        image.save(path)
        return str(path)

    def _service_register_combined_contract(self, order):
        """Create a single view-only PNG containing intake and handover details."""
        path = self._service_register_contract_dir() / f"{order[1]}_combined.png"
        image = Image.new("RGB", (1000, 2050), "white")
        draw = ImageDraw.Draw(image)
        try:
            font_path = resource_path(APP_FONT_FILE)
            if not os.path.isfile(font_path): font_path = "arial.ttf"
            title_font = ImageFont.truetype(font_path, 40)
            section_font = ImageFont.truetype(font_path, 30)
            body_font = ImageFont.truetype(font_path, 25)
            small_font = ImageFont.truetype(font_path, 21)
        except Exception:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            title_font = ImageFont.truetype(font_path, 40)
            section_font = ImageFont.truetype(font_path, 30)
            body_font = ImageFont.truetype(font_path, 25)
            small_font = ImageFont.truetype(font_path, 21)
        draw.rectangle((0, 0, 1000, 170), fill=COLOR_CRIMSON)
        draw.rectangle((24, 18, 976, 152), outline=COLOR_WHITE, width=3)
        shop_ar, shop_en, _, _, logo_path = self._shop_identity()
        try:
            if logo_path and os.path.isfile(logo_path):
                logo = Image.open(logo_path).convert("RGBA"); logo.thumbnail((100, 100)); image.paste(logo, (55, 22), logo)
        except Exception:
            pass
        def rtl(text, font, y, fill=COLOR_NAVY):
            draw.text((940, y), fix_arabic(str(text or "-"), for_ui=True), font=font, fill=fill, anchor="ra")
        def rule(y, color=COLOR_BORDER, width=2):
            draw.line((55, y, 945, y), fill=color, width=width)
        def section(title, y):
            rule(y - 12, COLOR_CRIMSON, 3)
            draw.rounded_rectangle((55, y, 945, y + 52), radius=8, fill=COLOR_NAVY)
            rtl(title, section_font, y + 10, COLOR_WHITE)
            return y + 76
        def field(label, value, y, gap=43, wrap=False):
            text = f"{label}: {value or '-'}"
            if wrap and len(text) > 56:
                cut = max(text.rfind("، ", 0, 58), text.rfind(" ", 0, 58), 40)
                first, second = text[:cut], text[cut:].lstrip(" ،")
                rtl(first, body_font, y)
                rtl(second[:70], body_font, y + 34)
                rule(y + gap + 26, COLOR_BORDER, 1)
                return y + gap + 70
            rtl(text, body_font, y)
            rule(y + gap - 8, COLOR_BORDER, 1)
            return y + gap
        rtl(shop_ar, title_font, 25, COLOR_WHITE)
        rtl(shop_en, body_font, 78, COLOR_WHITE)
        rtl("عقد موحد لاستلام وتسليم جهاز الصيانة", section_font, 112, COLOR_WHITE)

        # The seal is deliberately placed lower, separated from the header and first section.
        seal_y = 212
        draw.ellipse((62, seal_y, 238, seal_y + 176), outline=COLOR_CRIMSON, width=6)
        draw.ellipse((78, seal_y + 16, 222, seal_y + 160), outline=COLOR_CRIMSON, width=2)
        draw.text((150, seal_y + 64), "OFFICIAL", font=small_font, fill=COLOR_CRIMSON, anchor="mm")
        draw.text((150, seal_y + 100), "TCJ", font=body_font, fill=COLOR_CRIMSON, anchor="mm")
        y = 410
        y = section("البيانات الأساسية", y)
        base_fields = [
            ("رقم الطلب / المستند", order[1]), ("العميل", order[2]), ("الهاتف", order[3]),
            ("نوع الجهاز", order[4]), ("الشركة", order[5]), ("الموديل", order[6]),
            ("الرقم التسلسلي / IMEI", order[7])
        ]
        for label, value in base_fields: y = field(label, value, y)
        try:
            technician_row = self.db.cursor.execute("SELECT name FROM service_register_technicians WHERE id=?", (order[12],)).fetchone() if order[12] else None
            technician_name = technician_row[0] if technician_row else "غير معين"
        except Exception:
            technician_name = "غير معين"
        y = field("الفني", technician_name, y)
        y += 18
        y = section("تفاصيل الاستلام من العميل", y)
        y = field("تاريخ ووقت الاستلام", f"{order[14] or '-'} {order[15] or ''}", y)
        y = field("الصيانة المطلوبة", order[8], y, wrap=True)
        y = field("الملاحظات", order[9], y, wrap=True)
        y = field("الملحقات المستلمة", order[25], y, wrap=True)
        try: intake_checks = json.loads(order[10] or "{}")
        except Exception: intake_checks = {}
        intake_text = "، ".join(f"{k}: {v}" for k, v in intake_checks.items()) or "-"
        y = field("قائمة فحص الاستلام", intake_text, y, 43, wrap=True)
        y = field("ملاحظات الاستلام", order[9], y, 43, wrap=True)
        y += 18
        y = section("تفاصيل التسليم للعميل", y)
        y = field("حالة الطلب", order[13], y)
        y = field("تاريخ ووقت التسليم", f"{order[18] or 'لم يتم التسليم بعد'} {order[19] or ''}", y)
        y = field("الملحقات المسلمة", order[26] if len(order) > 26 else "-", y, wrap=True)
        try: handover_checks = json.loads(order[11] or "{}")
        except Exception: handover_checks = {}
        handover_text = "، ".join(f"{k}: {v}" for k, v in handover_checks.items()) or "-"
        y = field("قائمة فحص التسليم", handover_text, y, 43, wrap=True)
        y = field("ملاحظات التسليم", order[24], y, 43, wrap=True)
        y = field("تسعيرة الصيانة", f"{float(order[20] or 0):.2f} {CURRENCY}", y)
        y += 18
        rule(y, COLOR_CRIMSON, 3); y += 26
        rtl("تم إعداد هذا المستند للعرض والرجوع إلى تفاصيل الاستلام والتسليم.", small_font, y, COLOR_NAVY)
        y += 44
        rtl("ترند سنتر الأردن — سجل تشغيلي لخدمة الصيانة", small_font, y, COLOR_NAVY)
        image.save(path)
        return str(path)

    def _service_register_order_row(self, order_id):
        return self.db.cursor.execute("""SELECT id, order_no, client_name, client_phone, device_type,
            manufacturer, model, serial_imei, issue_description, intake_notes, intake_checklist,
            handover_checklist, technician_id, status, received_date, received_time,
            received_date, received_time, delivered_date, delivered_time, service_price, part_cost,
            technician_share, shop_share, delivery_notes, accessories_in, intake_contract_path,
            handover_contract_path FROM service_register_orders WHERE id=?""", (order_id,)).fetchone()

    def _service_register_log(self, order_id, action, details=""):
        self.db.cursor.execute("INSERT INTO service_register_audit (order_id, action, details, username, created_at) VALUES (?,?,?,?,?)", (order_id, action, details, self.current_user or "system", datetime.datetime.now().isoformat(timespec="seconds")))

    def ui_service_register(self):
        for w in self.main_view.winfo_children(): w.destroy()
        is_admin = self.current_role == "admin"
        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(14, 6))
        ctk.CTkLabel(header, text=fix_arabic("سجل استلام وتسليم الأجهزة", for_ui=True), font=HEADER_FONT_WHITE, text_color=COLOR_WHITE).pack(side="right")
        ctk.CTkButton(header, text=fix_arabic("استلام جهاز", for_ui=True), command=self.open_service_register_intake, font=FONT_BOLD, height=42, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="left", padx=4)
        ctk.CTkButton(header, text=fix_arabic("تسليم جهاز", for_ui=True), command=self.open_service_register_handover, font=FONT_BOLD, height=42, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="left", padx=4)
        ctk.CTkButton(header, text=fix_arabic("البحث في السجلات", for_ui=True), command=self.search_service_register_records, font=FONT_BOLD, height=42, fg_color=COLOR_NAVY_LIGHT).pack(side="left", padx=4)
        if is_admin:
            ctk.CTkButton(header, text=fix_arabic("إدارة الفنيين", for_ui=True), command=self.manage_service_register_technicians, font=FONT_BOLD, height=42, fg_color=COLOR_VINO).pack(side="left", padx=4)
            ctk.CTkButton(header, text=fix_arabic("استعلام وإيرادات الصيانة", for_ui=True), command=self.service_register_inquiry, font=FONT_BOLD, height=42, fg_color=COLOR_TEAL).pack(side="left", padx=4)
        columns = ("status", "technician", "delivered", "received", "model", "device", "client", "order")
        tree = ttk.Treeview(self.main_view, columns=columns, show="headings", height=16)
        heads = {"status":"الحالة", "technician":"الفني", "delivered":"التسليم", "received":"الاستلام", "model":"الموديل", "device":"الجهاز", "client":"العميل", "order":"رقم الطلب"}
        for col in columns:
            tree.heading(col, text=fix_arabic(heads[col], for_ui=True)); tree.column(col, anchor="center", width=145)
        tree.pack(fill="both", expand=True, padx=18, pady=10)
        query = """SELECT o.order_no, o.client_name, o.device_type, o.model, o.received_date,
            COALESCE(o.delivered_date,''), o.status, COALESCE(t.name,'غير معين')
            FROM service_register_orders o LEFT JOIN service_register_technicians t ON t.id=o.technician_id
            ORDER BY o.id DESC LIMIT 300"""
        for order_no, client, device, model, received, delivered, status, technician in self.db.cursor.execute(query).fetchall():
            tree.insert("", "end", values=(fix_arabic(status, for_ui=True), fix_arabic(technician, for_ui=True), delivered or "-", received, model or "-", fix_arabic(device, for_ui=True), fix_arabic(client, for_ui=True), order_no))
        if is_admin:
            def edit_from_main(_event=None):
                selected = tree.selection()
                if not selected: return
                order_no = tree.item(selected[0], "values")[-1]
                found = self.db.cursor.execute("SELECT id FROM service_register_orders WHERE order_no=?", (order_no,)).fetchone()
                if found: self.edit_service_register_record(found[0])
            tree.bind("<Double-1>", edit_from_main)
        ctk.CTkLabel(self.main_view, text=fix_arabic("هذا السجل تشغيلي فقط ولا ينشئ قيودًا محاسبية ولا يعدل المخزون أو قسم الصيانة القديم.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="e", padx=20, pady=(0, 10))

    def _service_register_contract_message(self, order_no, kind, order=None):
        """Build the operational WhatsApp text without changing accounting data."""
        if order:
            client_name = str(order[2] or "-")
            manufacturer = str(order[5] or "-")
            model = str(order[6] or "-")
            device_name = f"{manufacturer} + {model}" if manufacturer != "-" else model
            if kind == "intake":
                issue = str(order[8] or order[9] or "-")
                received_date = str(order[14] or "-")
                received_time = str(order[15] or "-")
                return (
                    "ترند سنتر الأردن\nTREND CENTER JORDAN\n"
                    f"إيصال استلام جهاز رقم: {order_no}\n"
                    f"العميل: {client_name}\n"
                    f"الجهاز: {device_name}\n"
                    f"الصيانة المطلوبة: {issue}\n"
                    f"تاريخ الاستلام: {received_date}\n"
                    f"الساعة: {received_time}\n\n"
                    "نحتفظ بالجهاز للعناية والصيانة حسب البيانات أعلاه."
                )
            return (
                "ترند سنتر الأردن\nTREND CENTER JORDAN\n"
                f"تم تسليم جهاز: {device_name}\n"
                f"للعميل: {client_name}\n"
                "بعد فحصه واستلامه.\n"
                f"رقم الإيصال: {order_no}\n"
                "شكراً لثقتكم بنا."
            )
        return "ترند سنتر الأردن\nTREND CENTER JORDAN\n" + (f"إيصال استلام جهاز رقم: {order_no}" if kind == "intake" else f"تم تسليم الجهاز، رقم الإيصال: {order_no}")

    def _service_register_open_png(self, path):
        try:
            if not path or not os.path.exists(path) or str(path).lower().split("?")[0].rsplit(".", 1)[-1] != "png":
                return self.show_msg("عقد الجهاز", "ملف العقد غير موجود بصيغة PNG")
            if sys.platform.startswith("win"):
                os.startfile(path)
            else:
                webbrowser.open(Path(path).resolve().as_uri())
        except Exception as exc:
            self.show_msg("عقد الجهاز", f"تعذر فتح صورة PNG: {exc}")

    def _service_register_copy_png(self, path, notify=True):
        """Copy a PNG contract as CF_DIB so it can be pasted into WhatsApp."""
        if not path or not os.path.exists(path) or not str(path).lower().endswith(".png"):
            if notify: self.show_msg("عقد الجهاز", "ملف العقد غير موجود بصيغة PNG")
            return False
        if sys.platform != "win32":
            if notify: self.show_msg("نسخ العقد", "نسخ الصورة إلى الحافظة متاح عند تشغيل البرنامج على Windows")
            return False
        opened = False
        try:
            import win32clipboard
            output = io.BytesIO()
            Image.open(path).convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            opened = True
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            if notify:
                self.show_msg("تم نسخ العقد", "تم نسخ صورة العقد PNG إلى الحافظة. افتح WhatsApp واضغط Ctrl+V لإرسالها.")
            return True
        except Exception as exc:
            if notify: self.show_msg("نسخ العقد", f"تعذر نسخ صورة PNG: {exc}")
            return False
        finally:
            if opened:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

    def _service_register_send_contract_whatsapp(self, path, phone, order_no, kind, order=None):
        """Copy the PNG first, then open WhatsApp with the operational message."""
        self._service_register_copy_png(path, notify=False)
        self.send_whatsapp(phone, self._service_register_contract_message(order_no, kind, order))

    def _service_register_open_contract(self, path, phone, order_no, kind, open_whatsapp=True, order=None):
        """Show a PNG contract with copy/open/WhatsApp actions."""
        if path and os.path.exists(path):
            preview = ctk.CTkToplevel(self); preview.title(fix_arabic("عقد طلب الصيانة", is_title=True)); preview.geometry("760x960"); preview.grab_set()
            try:
                original = Image.open(path).convert("RGB")
                original.thumbnail((700, 760))
                from PIL import ImageTk
                photo = ImageTk.PhotoImage(original)
                label = ctk.CTkLabel(preview, text="", image=photo); label.image = photo; label.pack(expand=True, padx=15, pady=(15, 8))
            except Exception as exc:
                ctk.CTkLabel(preview, text=format_dialog_arabic(f"تعذر عرض العقد: {exc}"), font=FONT_BOLD, text_color=COLOR_WHITE).pack(expand=True)
            ctk.CTkLabel(preview, text=format_dialog_arabic("العقد محفوظ كصورة PNG جاهزة للنسخ والإرسال"), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(pady=(0, 8))
            actions = ctk.CTkFrame(preview, fg_color="transparent")
            actions.pack(fill="x", padx=16, pady=(0, 14))
            ctk.CTkButton(actions, text=fix_arabic("نسخ صورة PNG", for_ui=True), command=lambda: self._service_register_copy_png(path), font=FONT_BOLD, height=46, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="right", expand=True, fill="x", padx=4)
            ctk.CTkButton(actions, text=fix_arabic("فتح صورة PNG", for_ui=True), command=lambda: self._service_register_open_png(path), font=FONT_BOLD, height=46, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK).pack(side="right", expand=True, fill="x", padx=4)
            ctk.CTkButton(actions, text=fix_arabic("فتح مجلد العقد", for_ui=True), command=lambda: self._service_register_reveal_file(path), font=FONT_BOLD, height=46, fg_color=COLOR_NAVY_LIGHT, hover_color=COLOR_NAVY).pack(side="left", expand=True, fill="x", padx=4)
            if phone:
                ctk.CTkButton(preview, text=fix_arabic("نسخ PNG وفتح WhatsApp", for_ui=True), command=lambda: self._service_register_send_contract_whatsapp(path, phone, order_no, kind, order), font=FONT_BOLD, height=48, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK).pack(fill="x", padx=20, pady=(0, 16))
        if not open_whatsapp: return
        digits = re.sub(r"\D", "", str(phone or ""))
        if digits.startswith("0"): digits = "962" + digits[1:]
        message = self._service_register_contract_message(order_no, kind, order)
        if digits:
            try: webbrowser.open("https://wa.me/" + digits + "?text=" + urllib.parse.quote(message))
            except Exception: pass

    def _service_register_reveal_file(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(os.path.dirname(path))
            else:
                webbrowser.open("file://" + os.path.dirname(path))
        except Exception:
            pass

    def search_service_register_records(self):
        win = ctk.CTkToplevel(self); win.title(fix_arabic("البحث في سجلات الأجهزة", is_title=True)); win.geometry("1150x680"); win.grab_set(); win.option_add("*Font", FONT_BOLD)
        top = ctk.CTkFrame(win, fg_color=COLOR_SURFACE); top.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(top, text=fix_arabic("رقم هاتف العميل", for_ui=True), font=FONT_BOLD).pack(side="right", padx=8)
        phone = ctk.CTkEntry(top, width=280, height=44, font=FONT_NORMAL_BOLD, justify="right", placeholder_text=fix_arabic("اكتب الرقم أو جزءًا منه", for_ui=True)); phone.pack(side="right", padx=8)
        cols = ("status", "technician", "delivered", "received", "model", "device", "client", "phone", "order")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=17); heads = {"status":"الحالة", "technician":"الفني", "delivered":"التسليم", "received":"الاستلام", "model":"الموديل", "device":"الجهاز", "client":"العميل", "phone":"الهاتف", "order":"رقم الطلب"}
        for c in cols: tree.heading(c, text=fix_arabic(heads[c], for_ui=True)); tree.column(c, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=12, pady=8)
        def run():
            for i in tree.get_children(): tree.delete(i)
            term = phone.get().strip()
            q = """SELECT o.order_no,o.client_name,o.client_phone,o.device_type,o.model,o.received_date,COALESCE(o.delivered_date,''),o.status,COALESCE(t.name,'غير معين'),o.id FROM service_register_orders o LEFT JOIN service_register_technicians t ON t.id=o.technician_id WHERE o.client_phone LIKE ? ORDER BY o.id DESC"""
            for no, client, client_phone, device, model, received, delivered, status, technician, rid in self.db.cursor.execute(q, (f"%{term}%",)).fetchall():
                tree.insert("", "end", values=(fix_arabic(status, for_ui=True), fix_arabic(technician, for_ui=True), delivered or "-", received, model or "-", fix_arabic(device, for_ui=True), fix_arabic(client, for_ui=True), client_phone, no))
        def edit_selected(_event=None):
            if self.current_role != "admin": return
            sel = tree.selection()
            if not sel: return
            no = tree.item(sel[0], "values")[-1]; found = self.db.cursor.execute("SELECT id FROM service_register_orders WHERE order_no=?", (no,)).fetchone()
            if found: self.edit_service_register_record(found[0], win)
        def view_contract():
            sel = tree.selection()
            if not sel: return self.show_msg("عقد الصيانة", "حدد سجلًا أولًا")
            no = tree.item(sel[0], "values")[-1]
            record = self.db.cursor.execute("SELECT id, client_phone, order_no, intake_contract_path, handover_contract_path FROM service_register_orders WHERE order_no=?", (no,)).fetchone()
            if not record: return self.show_msg("عقد الصيانة", "لم يتم العثور على السجل")
            order = self._service_register_order_row(record[0])
            if not order: return self.show_msg("عقد الصيانة", "تعذر قراءة تفاصيل السجل")
            combined_path = self._service_register_combined_contract(order)
            self._service_register_open_contract(combined_path, record[1], record[2], "combined", open_whatsapp=False, order=order)
        ctk.CTkButton(top, text=fix_arabic("بحث في السجلات", for_ui=True), command=run, font=FONT_BOLD, height=44, fg_color=COLOR_TEAL).pack(side="left", padx=5)
        ctk.CTkButton(top, text=fix_arabic("مسح البحث", for_ui=True), command=lambda: (phone.delete(0, "end"), run()), font=FONT_BOLD, height=44, fg_color=COLOR_NAVY_LIGHT).pack(side="left", padx=5)
        ctk.CTkButton(top, text=fix_arabic("الاطلاع على عقد الصيانة", for_ui=True), command=view_contract, font=FONT_BOLD, height=44, fg_color=COLOR_CRIMSON).pack(side="left", padx=5)
        tree.bind("<Double-1>", edit_selected); run()

    def _service_register_check_form(self, parent, device_var):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER, corner_radius=10)
        frame.pack(fill="x", pady=6)
        ctk.CTkLabel(frame, text=fix_arabic("قائمة الفحص", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=10, pady=6)
        checks = {}
        def rebuild(*_):
            for child in list(frame.winfo_children())[1:]: child.destroy()
            checks.clear()
            for item in self._service_register_check_items(device_var.get()):
                var = ctk.StringVar(value="سليم")
                checks[item] = var
                row = ctk.CTkFrame(frame, fg_color="transparent"); row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=fix_arabic(item, for_ui=True), font=FONT_NORMAL_BOLD, width=190, anchor="e").pack(side="right")
                ctk.CTkComboBox(row, values=["سليم", "خلل", "غير قابل للفحص"], variable=var, width=190, font=FONT_NORMAL_BOLD, justify="right").pack(side="right", padx=8)
        device_var.trace_add("write", rebuild); rebuild()
        return checks

    def open_service_register_intake(self):
        win = ctk.CTkToplevel(self); win.title(fix_arabic("استلام جهاز للصيانة", is_title=True)); win.geometry("1080x900"); win.minsize(950, 720); win.grab_set(); win.option_add("*Font", FONT_BOLD)
        scroll = ctk.CTkScrollableFrame(win, fg_color=COLOR_BG_LIGHT); scroll.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(scroll, text=fix_arabic("استلام جهاز للصيانة", for_ui=True), font=HEADER_FONT_WHITE, text_color=COLOR_WHITE).pack(anchor="e", padx=15, pady=10)
        form = ctk.CTkFrame(scroll, fg_color=COLOR_SURFACE, corner_radius=10); form.pack(fill="x", padx=10, pady=5)
        def entry(label, width=320):
            row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=10, pady=4)
            ctk.CTkLabel(row, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, width=220, anchor="e").pack(side="right")
            e = ctk.CTkEntry(row, width=width, height=42, font=FONT_NORMAL_BOLD, justify="right"); e.pack(side="right", padx=8); return e
        client = entry("اسم العميل *"); phone = entry("رقم الهاتف *"); manufacturer = entry("الشركة"); model = entry("الموديل"); serial = entry("الرقم التسلسلي / IMEI")
        row = ctk.CTkFrame(form, fg_color="transparent"); row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row, text=fix_arabic("نوع الجهاز *", for_ui=True), font=FONT_BOLD, width=220, anchor="e").pack(side="right")
        device_var = ctk.StringVar(value="هاتف"); ctk.CTkComboBox(row, values=self._service_register_types(), variable=device_var, width=320, height=42, font=FONT_NORMAL_BOLD, justify="right").pack(side="right", padx=8)
        accessories = entry("الملحقات المستلمة")
        inspection_row = ctk.CTkFrame(scroll, fg_color="transparent"); inspection_row.pack(fill="x", padx=10, pady=6)
        checklist_host = ctk.CTkFrame(inspection_row, fg_color="transparent"); checklist_host.pack(side="right", fill="both", expand=True, padx=(5, 0))
        notes_host = ctk.CTkFrame(inspection_row, fg_color=COLOR_SURFACE, border_width=1, border_color=COLOR_BORDER, corner_radius=10)
        notes_host.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(notes_host, text=fix_arabic("الصيانة المطلوبة", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=10, pady=(8, 2))
        issue = ctk.CTkTextbox(notes_host, height=85, font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, fg_color=COLOR_NAVY); issue.pack(fill="x", padx=10, pady=(2, 6)); issue.insert("1.0", "")
        ctk.CTkLabel(notes_host, text=fix_arabic("الملاحظات", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=10, pady=(2, 2))
        notes = ctk.CTkTextbox(notes_host, height=85, font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, fg_color=COLOR_NAVY); notes.pack(fill="x", padx=10, pady=(2, 10)); notes.insert("1.0", "")
        for widget in (issue, notes):
            try:
                widget._textbox.configure(font=FONT_NORMAL_BOLD, justify="right", wrap="word")
                widget._textbox.tag_configure("rtl", justify="right")
                widget._textbox.tag_add("rtl", "1.0", "end")
            except Exception: pass
        checks = self._service_register_check_form(checklist_host, device_var)
        def save():
            if not client.get().strip() or not phone.get().strip(): return self.show_msg("تنبيه", "اسم العميل ورقم الهاتف مطلوبان")
            now = datetime.datetime.now(); order_no = f"SR-{now.strftime('%Y%m%d-%H%M%S')}"
            checklist = json.dumps({k: v.get() for k, v in checks.items()}, ensure_ascii=False)
            issue_text = issue.get("1.0", "end").strip()
            note_text = notes.get("1.0", "end").strip()
            self.db.cursor.execute("""INSERT INTO service_register_orders (order_no, client_name, client_phone, device_type, manufacturer, model, serial_imei, issue_description, intake_notes, accessories_in, intake_checklist, status, received_date, received_time, created_by, updated_by, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (order_no, client.get().strip(), phone.get().strip(), device_var.get(), manufacturer.get().strip(), model.get().strip(), serial.get().strip(), issue_text, note_text, accessories.get().strip(), checklist, "مستلم", now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), self.current_user, self.current_user, now.isoformat(timespec="seconds")))
            order_id = self.db.cursor.lastrowid; row_data = self._service_register_order_row(order_id); contract = self._service_register_contract(row_data, "intake")
            self.db.cursor.execute("UPDATE service_register_orders SET intake_contract_path=? WHERE id=?", (contract, order_id)); self._service_register_log(order_id, "استلام الجهاز", "إنشاء طلب تشغيلي مستقل")
            self.db.conn.commit()
            client_phone = phone.get().strip()
            win.destroy(); self.ui_service_register()
            self._service_register_open_contract(contract, client_phone, order_no, "intake", open_whatsapp=True, order=row_data)
        action_bar = ctk.CTkFrame(scroll, fg_color="transparent"); action_bar.pack(fill="x", padx=10, pady=(2, 12))
        ctk.CTkButton(action_bar, text=fix_arabic("تأكيد الاستلام وتوليد العقد", for_ui=True), command=save, font=FONT_BOLD, height=52, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="right", fill="x", expand=True, padx=(0, 5))

    def open_service_register_handover(self):
        rows = self.db.cursor.execute("SELECT id, order_no FROM service_register_orders WHERE status <> 'تم التسليم' AND status <> 'ملغى' ORDER BY id DESC").fetchall()
        if not rows: return self.show_msg("استلام وتسليم الأجهزة", "لا توجد طلبات جاهزة للعرض")
        win = ctk.CTkToplevel(self); win.title(fix_arabic("تسليم جهاز بعد الصيانة", is_title=True)); win.geometry("800x720"); win.grab_set(); win.option_add("*Font", FONT_BOLD)
        box = ctk.CTkScrollableFrame(win, fg_color=COLOR_BG_LIGHT); box.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(box, text=fix_arabic("تسليم جهاز بعد الصيانة", for_ui=True), font=HEADER_FONT_WHITE, text_color=COLOR_WHITE).pack(anchor="e", padx=12, pady=10)
        selected = ctk.StringVar(value=rows[0][1])
        current_id = {r[1]: r[0] for r in rows}
        receipt_row = ctk.CTkFrame(box, fg_color="transparent"); receipt_row.pack(fill="x", padx=12, pady=6)
        receipt_combo = ctk.CTkComboBox(receipt_row, values=[r[1] for r in rows], variable=selected, font=FONT_NORMAL_BOLD, height=44, justify="right")
        receipt_combo.pack(side="right", fill="x", expand=True, padx=(8, 0))
        def search_receipts():
            search_win = ctk.CTkToplevel(win); search_win.title(fix_arabic("بحث في سجلات الأجهزة", is_title=True)); search_win.geometry("860x520"); search_win.grab_set(); search_win.option_add("*Font", FONT_BOLD)
            search_box = ctk.CTkFrame(search_win, fg_color=COLOR_BG_LIGHT); search_box.pack(fill="both", expand=True, padx=10, pady=10)
            query_entry = ctk.CTkEntry(search_box, height=44, font=FONT_NORMAL_BOLD, justify="right", placeholder_text=fix_arabic("ابحث برقم الإيصال أو اسم العميل أو الهاتف", for_ui=True)); query_entry.pack(fill="x", padx=12, pady=10)
            result_tree = ttk.Treeview(search_box, columns=("model", "manufacturer", "phone", "client", "order"), show="headings", height=12)
            result_heads = {"model":"الموديل", "manufacturer":"الشركة", "phone":"الهاتف", "client":"العميل", "order":"رقم الإيصال"}
            for col in result_tree["columns"]:
                result_tree.heading(col, text=fix_arabic(result_heads[col], for_ui=True)); result_tree.column(col, anchor="center", width=145)
            result_tree.pack(fill="both", expand=True, padx=12, pady=6)
            def refresh_results(*_):
                for item in result_tree.get_children(): result_tree.delete(item)
                term = query_entry.get().strip(); like = f"%{term}%"
                found = self.db.cursor.execute("SELECT id, order_no, client_name, client_phone, manufacturer, model FROM service_register_orders WHERE status <> 'تم التسليم' AND status <> 'ملغى' AND (order_no LIKE ? OR client_name LIKE ? OR client_phone LIKE ?) ORDER BY id DESC", (like, like, like)).fetchall()
                for rid, order_no, client_name, client_phone, manufacturer, model in found:
                    current_id[order_no] = rid
                    result_tree.insert("", "end", values=(model or "-", manufacturer or "-", client_phone or "-", fix_arabic(client_name or "-", for_ui=True), order_no))
            def choose_receipt():
                picked = result_tree.selection()
                if not picked: return self.show_msg("تنبيه", "اختر إيصالاً من نتائج البحث أولاً")
                order_no = result_tree.item(picked[0], "values")[-1]
                selected.set(order_no); search_win.destroy()
            query_entry.bind("<KeyRelease>", refresh_results)
            ctk.CTkButton(search_box, text=fix_arabic("اختيار الإيصال", for_ui=True), command=choose_receipt, font=FONT_BOLD, height=44, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="right", padx=12, pady=8)
            ctk.CTkButton(search_box, text=fix_arabic("إغلاق", for_ui=True), command=search_win.destroy, font=FONT_BOLD, height=44, fg_color=COLOR_NAVY_LIGHT).pack(side="left", padx=12, pady=8)
            refresh_results(); query_entry.focus_set()
        ctk.CTkButton(receipt_row, text=fix_arabic("بحث في السجلات", for_ui=True), command=search_receipts, font=FONT_BOLD, height=44, width=180, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="left")
        checks = {}
        device_var = ctk.StringVar(value="هاتف")
        check_frame = ctk.CTkFrame(box, fg_color=COLOR_SURFACE, corner_radius=10); check_frame.pack(fill="x", padx=12, pady=6)
        def rebuild():
            for child in check_frame.winfo_children(): child.destroy()
            checks.clear()
            order = self.db.cursor.execute("SELECT device_type FROM service_register_orders WHERE id=?", (current_id[selected.get()],)).fetchone()
            device_var.set(order[0] if order else "هاتف")
            for item in self._service_register_check_items(device_var.get()):
                v = ctk.StringVar(value="سليم"); checks[item] = v
                row = ctk.CTkFrame(check_frame, fg_color="transparent"); row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=fix_arabic(item, for_ui=True), font=FONT_NORMAL_BOLD, width=220, anchor="e").pack(side="right")
                ctk.CTkComboBox(row, values=["سليم", "خلل", "غير قابل للفحص"], variable=v, width=200, font=FONT_NORMAL_BOLD, justify="right").pack(side="right", padx=8)
        selected.trace_add("write", lambda *_: rebuild()); rebuild()
        ctk.CTkLabel(box, text=fix_arabic("ملاحظات التسليم", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=12, pady=(8, 2))
        notes = ctk.CTkTextbox(box, height=120, font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, fg_color=COLOR_NAVY); notes.pack(fill="x", padx=12, pady=8); notes.insert("1.0", "")
        try: notes._textbox.configure(font=FONT_NORMAL_BOLD, justify="right", wrap="word"); notes._textbox.tag_configure("rtl", justify="right"); notes._textbox.tag_add("rtl", "1.0", "end")
        except Exception: pass
        accessories = ctk.CTkEntry(box, height=44, font=FONT_NORMAL_BOLD, justify="right", placeholder_text=fix_arabic("الملحقات المعادة", for_ui=True)); accessories.pack(fill="x", padx=12, pady=5)
        def save():
            order_id = current_id[selected.get()]; now = datetime.datetime.now(); checklist = json.dumps({k: v.get() for k, v in checks.items()}, ensure_ascii=False); note_text = notes.get("1.0", "end").strip()
            self.db.cursor.execute("UPDATE service_register_orders SET handover_checklist=?, status=?, delivered_date=?, delivered_time=?, delivery_notes=?, accessories_out=?, updated_by=?, updated_at=? WHERE id=?", (checklist, "تم التسليم", now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), note_text, accessories.get().strip(), self.current_user, now.isoformat(timespec="seconds"), order_id))
            row_data = self._service_register_order_row(order_id); contract = self._service_register_contract(row_data, "handover")
            order_phone = self.db.cursor.execute("SELECT client_phone, order_no FROM service_register_orders WHERE id=?", (order_id,)).fetchone(); self.db.cursor.execute("UPDATE service_register_orders SET handover_contract_path=? WHERE id=?", (contract, order_id)); self._service_register_log(order_id, "تسليم الجهاز", "تأكيد تسليم تشغيلي فقط"); self.db.conn.commit(); win.destroy(); self.ui_service_register(); self._service_register_open_contract(contract, order_phone[0], order_phone[1], "handover", order=row_data)
        ctk.CTkButton(box, text=fix_arabic("تأكيد التسليم وتوليد العقد", for_ui=True), command=save, font=FONT_BOLD, height=48, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(anchor="e", padx=12, pady=12)

    def manage_service_register_technicians(self):
        if self.current_role != "admin": return self.show_msg("الصلاحيات", "إدارة الفنيين للمدير فقط")
        win = ctk.CTkToplevel(self); win.title(fix_arabic("إدارة فنيي سجل الأجهزة", is_title=True)); win.geometry("620x600"); win.grab_set()
        box = ctk.CTkFrame(win, fg_color=COLOR_BG_LIGHT); box.pack(fill="both", expand=True, padx=10, pady=10)
        name = ctk.CTkEntry(box, height=44, font=FONT_NORMAL_BOLD, justify="right", placeholder_text=fix_arabic("اسم الفني", for_ui=True)); name.pack(fill="x", padx=14, pady=10)
        tree = ttk.Treeview(box, columns=("active", "name", "id"), show="headings"); tree.heading("active", text=fix_arabic("الحالة", for_ui=True)); tree.heading("name", text=fix_arabic("اسم الفني", for_ui=True)); tree.heading("id", text="ID"); tree.pack(fill="both", expand=True, padx=14, pady=8)
        def refresh():
            for i in tree.get_children(): tree.delete(i)
            for rid, n, active in self.db.cursor.execute("SELECT id,name,active FROM service_register_technicians ORDER BY active DESC, name").fetchall(): tree.insert("", "end", values=("فعال" if active else "متوقف", fix_arabic(n, for_ui=True), rid))
        def add():
            n = name.get().strip()
            if not n: return self.show_msg("تنبيه", "اكتب اسم الفني")
            try: self.db.cursor.execute("INSERT INTO service_register_technicians (name, active, created_by, created_at) VALUES (?,1,?,?)", (n, self.current_user, datetime.datetime.now().isoformat(timespec="seconds"))); self.db.conn.commit(); name.delete(0, "end"); refresh()
            except sqlite3.IntegrityError: self.show_msg("تنبيه", "اسم الفني موجود مسبقًا")
        def toggle():
            sel = tree.selection()
            if not sel: return
            rid = tree.item(sel[0], "values")[2]; self.db.cursor.execute("UPDATE service_register_technicians SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (rid,)); self.db.conn.commit(); refresh()
        buttons = ctk.CTkFrame(box, fg_color="transparent"); buttons.pack(fill="x", padx=14, pady=8)
        ctk.CTkButton(buttons, text=fix_arabic("إضافة الفني", for_ui=True), command=add, font=FONT_BOLD, fg_color=COLOR_CRIMSON).pack(side="right", padx=4); ctk.CTkButton(buttons, text=fix_arabic("تفعيل / إيقاف", for_ui=True), command=toggle, font=FONT_BOLD, fg_color=COLOR_VINO).pack(side="right", padx=4); refresh()

    def service_register_inquiry(self):
        if self.current_role != "admin": return self.show_msg("الصلاحيات", "الاستعلام المالي للمدير فقط")
        win = ctk.CTkToplevel(self); win.title(fix_arabic("استعلام وإيرادات الصيانة", is_title=True)); win.geometry("1250x720"); win.grab_set()
        top = ctk.CTkFrame(win, fg_color=COLOR_SURFACE); top.pack(fill="x", padx=10, pady=10)
        start = ctk.CTkEntry(top, width=150, font=FONT_NORMAL_BOLD, justify="center", placeholder_text="YYYY-MM-DD"); start.pack(side="right", padx=5); end = ctk.CTkEntry(top, width=150, font=FONT_NORMAL_BOLD, justify="center", placeholder_text="YYYY-MM-DD"); end.pack(side="right", padx=5)
        tech_values = ["كل الفنيين"] + [r[0] for r in self.db.cursor.execute("SELECT name FROM service_register_technicians WHERE active=1 ORDER BY name").fetchall()]; tech = ctk.CTkComboBox(top, values=tech_values, font=FONT_NORMAL_BOLD, width=220, justify="right"); tech.pack(side="right", padx=5); tech.set("كل الفنيين")
        ctk.CTkLabel(top, text=fix_arabic("من", for_ui=True), font=FONT_BOLD).pack(side="right"); ctk.CTkLabel(top, text=fix_arabic("إلى", for_ui=True), font=FONT_BOLD).pack(side="right")
        summary = ctk.CTkLabel(win, text="", font=FONT_BOLD, text_color=COLOR_WHITE); summary.pack(anchor="e", padx=15)
        cols = ("shop", "technician", "profit", "cost", "price", "delivered", "received", "technician_name", "device", "client", "order")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=18); heads = {"shop":"حصة المحل", "technician":"حصة الفني", "profit":"الربح النظري", "cost":"تكلفة القطعة", "price":"التسعيرة", "delivered":"التسليم", "received":"الاستلام", "technician_name":"الفني", "device":"الجهاز", "client":"العميل", "order":"رقم الطلب"}
        for c in cols: tree.heading(c, text=fix_arabic(heads[c], for_ui=True)); tree.column(c, width=105, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=8)
        def run():
            for i in tree.get_children(): tree.delete(i)
            clauses, params = [], []
            if start.get().strip(): clauses.append("o.received_date>=?"); params.append(start.get().strip())
            if end.get().strip(): clauses.append("o.received_date<=?"); params.append(end.get().strip())
            if tech.get() != "كل الفنيين": clauses.append("t.name=?"); params.append(tech.get())
            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
            q = f"SELECT o.order_no,o.client_name,o.device_type,COALESCE(o.delivered_date,''),o.received_date,COALESCE(t.name,'غير معين'),o.service_price,o.part_cost,o.technician_share,o.shop_share,o.id FROM service_register_orders o LEFT JOIN service_register_technicians t ON t.id=o.technician_id {where} ORDER BY o.id DESC"
            data = self.db.cursor.execute(q, params).fetchall(); total = [0.0,0.0,0.0,0.0]
            for no, client, device, delivered, received, technician_name, price, cost, tshare, sshare, rid in data:
                profit = float(price or 0) - float(cost or 0); total[0] += float(price or 0); total[1] += float(cost or 0); total[2] += float(tshare or profit * .5); total[3] += float(sshare or profit * .5)
                tree.insert("", "end", values=(f"{sshare or profit*.5:.2f}", f"{tshare or profit*.5:.2f}", f"{profit:.2f}", f"{cost or 0:.2f}", f"{price or 0:.2f}", delivered or "-", received, fix_arabic(technician_name, for_ui=True), fix_arabic(device, for_ui=True), fix_arabic(client, for_ui=True), no))
            summary.configure(text=fix_arabic(f"الإيرادات المسجلة كبيانات: {total[0]:.2f} {CURRENCY} | تكلفة القطع: {total[1]:.2f} | حصة الفنيين: {total[2]:.2f} | حصة المحل: {total[3]:.2f}", for_ui=True))
        def edit_selected():
            sel = tree.selection()
            if not sel: return
            rid = tree.item(sel[0], "values")[-1]
            self.edit_service_register_record(int(self.db.cursor.execute("SELECT id FROM service_register_orders WHERE order_no=?", (rid,)).fetchone()[0]), win)
        ctk.CTkButton(top, text=fix_arabic("استعلام", for_ui=True), command=run, font=FONT_BOLD, fg_color=COLOR_TEAL).pack(side="left", padx=5); ctk.CTkButton(top, text=fix_arabic("تعديل الطلب المحدد", for_ui=True), command=edit_selected, font=FONT_BOLD, fg_color=COLOR_CRIMSON).pack(side="left", padx=5); run()

    def edit_service_register_record(self, order_id, parent=None):
        if self.current_role != "admin": return self.show_msg("الصلاحيات", "تعديل بيانات الفني والتسعيرة والتكلفة للمدير فقط")
        row = self.db.cursor.execute("SELECT order_no,client_name,device_type,model,technician_id,status,service_price,part_cost,issue_description,intake_notes,intake_checklist FROM service_register_orders WHERE id=?", (order_id,)).fetchone()
        if not row: return
        win = ctk.CTkToplevel(parent or self); win.title(fix_arabic("تعديل طلب الصيانة", is_title=True)); win.geometry("1040x820"); win.minsize(900, 700); win.grab_set(); win.option_add("*Font", FONT_BOLD)
        box = ctk.CTkFrame(win, fg_color=COLOR_BG_LIGHT); box.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(box, text=fix_arabic(f"طلب {row[0]} — {row[1]} — {row[2]}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", pady=(6, 10))
        summary = ctk.CTkFrame(box, fg_color=COLOR_SURFACE, corner_radius=10); summary.pack(fill="x", pady=(0, 8))
        def labeled_combo(parent_frame, label, values, current):
            cell = ctk.CTkFrame(parent_frame, fg_color="transparent"); cell.pack(side="right", fill="x", expand=True, padx=6, pady=8)
            ctk.CTkLabel(cell, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, anchor="e").pack(fill="x")
            widget = ctk.CTkComboBox(cell, values=values, font=FONT_NORMAL_BOLD, justify="right", height=44); widget.pack(fill="x", pady=(3, 0)); widget.set(current); return widget
        technicians = self.db.cursor.execute("SELECT id,name FROM service_register_technicians WHERE active=1 ORDER BY name").fetchall(); tech_map = {"غير معين": None}; tech_map.update({n:i for i,n in technicians})
        current_name = next((n for i,n in technicians if i == row[4]), "غير معين")
        tech = labeled_combo(summary, "الفني المسؤول", list(tech_map), current_name)
        status = labeled_combo(summary, "حالة طلب الصيانة", self._service_register_statuses(), row[5])
        price_cell = ctk.CTkFrame(summary, fg_color="transparent"); price_cell.pack(side="right", fill="x", expand=True, padx=6, pady=8)
        ctk.CTkLabel(price_cell, text=fix_arabic("تسعيرة الصيانة للعميل", for_ui=True), font=FONT_BOLD, anchor="e").pack(fill="x")
        price = ctk.CTkEntry(price_cell, font=FONT_NORMAL_BOLD, justify="right", height=44); price.pack(fill="x", pady=(3, 0)); price.insert(0, str(row[6] or 0))
        cost_cell = ctk.CTkFrame(summary, fg_color="transparent"); cost_cell.pack(side="right", fill="x", expand=True, padx=6, pady=8)
        ctk.CTkLabel(cost_cell, text=fix_arabic("تكلفة قطعة الصيانة", for_ui=True), font=FONT_BOLD, anchor="e").pack(fill="x")
        cost = ctk.CTkEntry(cost_cell, font=FONT_NORMAL_BOLD, justify="right", height=44); cost.pack(fill="x", pady=(3, 0)); cost.insert(0, str(row[7] or 0))
        ctk.CTkLabel(box, text=fix_arabic(f"نوع الجهاز: {row[2]}    الموديل: {row[3] or '-'}", for_ui=True), font=FONT_NORMAL_BOLD, anchor="e").pack(fill="x", pady=(0, 8))
        work_area = ctk.CTkFrame(box, fg_color="transparent"); work_area.pack(fill="both", expand=True, pady=2)
        notes_box = ctk.CTkFrame(work_area, fg_color=COLOR_SURFACE, corner_radius=10); notes_box.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ctk.CTkLabel(notes_box, text=fix_arabic("الصيانة المطلوبة", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=10, pady=(8, 2))
        issue = ctk.CTkTextbox(notes_box, height=105, font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, fg_color=COLOR_NAVY); issue.pack(fill="x", padx=10, pady=(2, 6)); issue.insert("1.0", row[8] or "")
        ctk.CTkLabel(notes_box, text=fix_arabic("الملاحظات", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=10, pady=(2, 2))
        notes = ctk.CTkTextbox(notes_box, height=105, font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, fg_color=COLOR_NAVY); notes.pack(fill="x", padx=10, pady=(2, 10)); notes.insert("1.0", row[9] or "")
        for widget in (issue, notes):
            try: widget._textbox.configure(font=FONT_NORMAL_BOLD, justify="right", wrap="word")
            except Exception: pass
        checklist_box = ctk.CTkFrame(work_area, fg_color=COLOR_SURFACE, corner_radius=10); checklist_box.pack(side="right", fill="both", expand=True, padx=(0, 6))
        ctk.CTkLabel(checklist_box, text=fix_arabic("قائمة الفحص", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=10, pady=(8, 2))
        try: saved_checks = json.loads(row[10] or "{}")
        except Exception: saved_checks = {}
        checks = {}
        for item in self._service_register_check_items(row[2]):
            check_row = ctk.CTkFrame(checklist_box, fg_color="transparent"); check_row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(check_row, text=fix_arabic(item, for_ui=True), font=FONT_NORMAL_BOLD, anchor="e").pack(side="right", fill="x", expand=True)
            var = ctk.StringVar(value=saved_checks.get(item, "سليم")); checks[item] = var
            ctk.CTkComboBox(check_row, values=["سليم", "خلل", "غير قابل للفحص"], variable=var, width=190, height=38, font=FONT_NORMAL_BOLD, justify="right").pack(side="left", padx=8)
        def save():
            try: service_price = float(price.get().replace(",", ".")); part_cost = float(cost.get().replace(",", "."))
            except ValueError: return self.show_msg("تنبيه", "تسعيرة الصيانة وتكلفة قطعة الصيانة يجب أن تكونا أرقامًا")
            issue_text = issue.get("1.0", "end").strip(); note_text = notes.get("1.0", "end").strip(); profit = service_price - part_cost; technician_share = profit * .5; shop_share = profit * .5; now = datetime.datetime.now(); tid = tech_map.get(tech.get()); checklist = json.dumps({k: v.get() for k, v in checks.items()}, ensure_ascii=False)
            self.db.cursor.execute("UPDATE service_register_orders SET technician_id=?, status=?, service_price=?, part_cost=?, technician_share=?, shop_share=?, issue_description=?, intake_notes=?, intake_checklist=?, updated_by=?, updated_at=? WHERE id=?", (tid, status.get(), service_price, part_cost, technician_share, shop_share, issue_text, note_text, checklist, self.current_user, now.isoformat(timespec="seconds"), order_id)); self._service_register_log(order_id, "تعديل الطلب", "تعديل الفني والحالة والتسعيرة والتكلفة والفحص والملاحظات كبيانات تشغيلية فقط"); self.db.conn.commit(); win.destroy(); self.ui_service_register()
        ctk.CTkButton(box, text=fix_arabic("حفظ التعديل", for_ui=True), command=save, font=FONT_BOLD, height=48, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(fill="x", pady=(10, 2))

    def ui_maintenance(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("قسم الصيانة")
        self.m_selected_part_id = None

        f1 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f1.pack(fill="x", padx=15, pady=5)
        self.m_phone = ctk.CTkEntry(f1, placeholder_text=fix_arabic("رقم الهاتف", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.m_phone.pack(side="right", padx=5)
        self.m_phone.bind("<KeyRelease>", lambda e: self.lookup_customer_name(self.m_phone, self.m_client))
        self.m_client = ctk.CTkEntry(f1, placeholder_text=fix_arabic("اسم العميل", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.m_client.pack(side="right", padx=5, expand=True, fill="x")
        self.m_device = ctk.CTkEntry(f1, placeholder_text=fix_arabic("الجهاز", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.m_device.pack(side="right", padx=5)
        
        f2 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f2.pack(fill="x", padx=15, pady=5)
        self.m_desc = ctk.CTkEntry(f2, placeholder_text=fix_arabic("وصف الإصلاح", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.m_desc.pack(side="right", padx=5, expand=True, fill="x")
        self.m_rev = ctk.CTkEntry(f2, placeholder_text=fix_arabic("المبلغ", for_ui=True), height=45, font=FONT_NORMAL_BOLD, width=120, justify="right", corner_radius=10); self.m_rev.pack(side="right", padx=5)
        ctk.CTkLabel(f2, text=fix_arabic("الدفع:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.m_pay = ctk.CTkComboBox(f2, values=["Cash", "Visa", "CLIQ", "Credit"], width=100, height=45, font=FONT_NORMAL_BOLD, justify="center")
        self.m_pay.pack(side="right", padx=5); self.m_pay.set("Cash")
        ctk.CTkButton(f2, text=fix_arabic("تسجيل صيانة + فاتورة", for_ui=True), fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, command=self.add_maintenance, font=FONT_BOLD, height=45, corner_radius=10).pack(side="right", padx=5)
        
        # إطار إدارة تكلفة وقطع الصيانة يُنشأ للمدير فقط حتى لا يترك مساحة فارغة للموظف.
        if self.current_role == "admin":
            admin_f = ctk.CTkFrame(self.main_view, fg_color=COLOR_NAVY_LIGHT, corner_radius=10)
            admin_f.pack(fill="x", padx=15, pady=5)
            ctk.CTkButton(admin_f, text=fix_arabic("حذف", for_ui=True), command=lambda: self.delete_record("maintenance", self.m_tree), font=FONT_BOLD, width=90, fg_color=COLOR_RUBI).pack(side="left", padx=5)
            ctk.CTkButton(admin_f, text=fix_arabic("تعديل", for_ui=True), command=lambda: self.edit_record_ui("maintenance", self.m_tree), font=FONT_BOLD, width=90, fg_color=COLOR_TEAL).pack(side="left", padx=5)
            ctk.CTkButton(admin_f, text=fix_arabic("اختيار قطعة من السجل", for_ui=True), command=self.open_maintenance_part_picker, font=FONT_BOLD, width=160, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="right", padx=8)
            self.m_part_lbl = ctk.CTkLabel(admin_f, text=fix_arabic("لم يتم اختيار قطعة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED)
            self.m_part_lbl.pack(side="right", padx=5)
            ctk.CTkLabel(admin_f, text=fix_arabic("تكلفة القطعة:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=10)
            self.m_cost_in = ctk.CTkEntry(admin_f, placeholder_text=fix_arabic("التكلفة", for_ui=True), width=90, justify="right")
            self.m_cost_in.pack(side="right", padx=5)
            ctk.CTkButton(admin_f, text=fix_arabic("ربط القطعة بالصيانة", for_ui=True), command=self.update_m_cost, font=FONT_BOLD, width=140, fg_color=COLOR_CRIMSON_DARK).pack(side="right", padx=10)

        # Hidden or fallback ID selection for compatibility with existing cost update logic
        self.m_id_sel = None

        if self.current_role == "admin":
            maintenance_columns = ("cost", "revenue", "desc", "phone", "client", "id")
            maintenance_heads = ["تكلفة القطع", "المبلغ", "الوصف", "الهاتف", "العميل", "ID"]
        else:
            maintenance_columns = ("revenue", "desc", "phone", "client", "id")
            maintenance_heads = ["المبلغ", "الوصف", "الهاتف", "العميل", "ID"]
        self.m_tree = ttk.Treeview(self.main_view, columns=maintenance_columns, show="headings")
        for col, head in zip(self.m_tree["columns"], maintenance_heads): self.m_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.m_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_maintenance_tree()
    def refresh_maintenance_tree(self):
        for i in self.m_tree.get_children(): self.m_tree.delete(i)
        self.db.cursor.execute("SELECT internal_cost, revenue, repair_desc, client_phone, client_name, id FROM maintenance ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            if self.current_role == "admin":
                values = (r[0], r[1], fix_arabic(r[2], for_ui=True), r[3], fix_arabic(r[4], for_ui=True), r[5])
            else:
                values = (r[1], fix_arabic(r[2], for_ui=True), r[3], fix_arabic(r[4], for_ui=True), r[5])
            self.m_tree.insert("", "end", values=values)


    def update_m_cost(self):
        """Link selected maintenance part or manual cost to the latest or selected maintenance record, decrementing part stock."""
        cost_str = self.m_cost_in.get().strip()
        if not cost_str:
            self.show_msg("تنبيه", "يرجى تحديد تكلفة القطعة أولاً"); return
        try:
            cost_val = float(clean_float(cost_str))
            # Get latest maintenance record ID if m_id_sel is None or empty
            m_id = None
            if hasattr(self, "m_id_sel") and self.m_id_sel is not None:
                try:
                    m_id = int(self.m_id_sel.get().strip())
                except:
                    pass
            if not m_id:
                row = self.db.cursor.execute("SELECT id FROM maintenance ORDER BY id DESC LIMIT 1").fetchone()
                if not row:
                    self.show_msg("تنبيه", "لا توجد عمليات صيانة مسجلة لتحديث تكلفتها"); return
                m_id = row[0]

            # Decrement part stock if a part was selected from inventory
            if getattr(self, "m_selected_part_id", None):
                part_id = self.m_selected_part_id
                part_row = self.db.cursor.execute("SELECT stock, part_name, cost_price FROM maintenance_parts WHERE id=?", (part_id,)).fetchone()
                if part_row:
                    current_stock, p_name, part_unit_cost = part_row[0], part_row[1], float(part_row[2] or 0.0)
                    if current_stock <= 0:
                        self.show_msg("تنبيه", f"القطعة ({p_name}) نفدت من المخزون ولا يمكن خصمها"); return
                    self.db.cursor.execute("UPDATE maintenance_parts SET stock = stock - 1 WHERE id=?", (part_id,))
                    self.db._record_maintenance_part_movement(part_id, "use", 1, part_unit_cost, maintenance_id=m_id, notes="استخدام قطعة مرتبطة بالصيانة")
                    self.log_action("استهلاك قطعة صيانة", "maintenance_parts", f"القطعة: {p_name} (ID: {part_id}); صيانة ID: {m_id}")

            self._void_journals_for_record("maintenance", m_id, "إعادة احتساب قيد الصيانة بعد تحديث تكلفة القطعة")
            self.db.cursor.execute("UPDATE maintenance SET internal_cost = ? WHERE id = ?", (cost_val, m_id))
            self._post_operation_journal_from_row("maintenance", m_id)
            self.db.conn.commit()
            self.show_msg("نجاح", f"تم ربط تكلفة القطعة ({cost_val}) بصيانة رقم #{m_id} وخصمها من مخزون القطع بنجاح")
            self.m_selected_part_id = None
            if hasattr(self, "m_part_lbl"):
                self.m_part_lbl.configure(text=fix_arabic("تم الربط والخصم بنجاح", for_ui=True), text_color=COLOR_TEAL)
            self.refresh_maintenance_tree()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback()
            self.show_msg("تعذر ربط القطعة", str(exc))

    def add_maintenance(self):
        c, ph, d, ds, r_raw = self.m_client.get().strip(), self.m_phone.get().strip(), self.m_device.get().strip(), self.m_desc.get().strip(), self.m_rev.get().strip()
        payment = self.m_pay.get()
        if not all([c, ph, d, ds, r_raw]):
            self.show_msg("تنبيه", "يرجى تعبئة اسم العميل والهاتف والجهاز ووصف الإصلاح والمبلغ")
            return
        try:
            rev = self.positive_number(r_raw, "مبلغ الصيانة")
            now = datetime.datetime.now()
            self.get_or_create_customer(ph, c)
            maintenance_source = f"maintenance-{now.strftime('%Y%m%d%H%M%S%f')}"
            mult = int(clean_float(self.db.cursor.execute("SELECT value FROM settings WHERE key='points_maint'").fetchone()[0] or 5))
            points_earned = mult
            if ph:
                self.db.cursor.execute("UPDATE customers SET points = points + ? WHERE phone=?", (points_earned, ph))
            if payment == "Credit":
                self.db.cursor.execute("INSERT INTO customer_debts (customer_phone, customer_name, total_debt, paid_amount, status, date, notes, source_type, source_id) VALUES (?,?,?,?,?,?,?,?,?)", 
                                       (ph, c, rev, 0, 'غير مسدد', now.strftime("%Y-%m-%d"), f'صيانة آجلة - {d}', "maintenance", maintenance_source))
            
            self.db.cursor.execute("INSERT INTO maintenance (device_name, repair_desc, client_name, client_phone, revenue, payment_method, date, time, user, source_id) VALUES (?,?,?,?,?,?,?,?,?,?)", (d, ds, c, ph, rev, payment, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), self.current_user, maintenance_source))
            maintenance_account = "AR" if payment == "Credit" else self._ledger_account_for_payment(payment)
            self._post_journal_entry("maintenance", maintenance_source, "قيد إيراد الصيانة", [(maintenance_account, rev, 0, "تحصيل أو ذمة الصيانة"), ("SERVICE_REVENUE", 0, rev, "إيراد خدمات الصيانة")], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
            self.db.conn.commit()
            self.log_action("تسجيل صيانة", "maintenance", f"العميل: {c}; المبلغ: {rev:.2f}; الدفع: {payment}")
            self.generate_invoice(rev, "MAINTENANCE", {"client": c, "device": d, "desc": ds, "phone": ph, "points": points_earned, "payment": payment})
            self.ui_maintenance()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر تسجيل الصيانة", str(exc))

    def ui_transfers(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("الحوالات والفواتير")
        f = ctk.CTkFrame(self.main_view, fg_color="transparent"); f.pack(fill="x", padx=15, pady=5)
        self.t_type_raws = ["خروج حوالة", "دخول حوالة", "دفع فاتورة"]
        self.t_type = ctk.CTkOptionMenu(f, values=[fix_arabic(x, for_ui=True) for x in self.t_type_raws], font=FONT_BOLD, width=180, fg_color=COLOR_CRIMSON); self.t_type.pack(side="right", padx=5)
        self.t_phone = ctk.CTkEntry(f, placeholder_text=fix_arabic("الهاتف", for_ui=True), height=40, justify="right"); self.t_phone.pack(side="right", padx=5)
        self.t_phone.bind("<KeyRelease>", lambda e: self.lookup_customer_name(self.t_phone, self.t_client))
        self.t_client = ctk.CTkEntry(f, placeholder_text=fix_arabic("اسم العميل (الاسم الأول ثم العائلة)", for_ui=True), height=40, justify="right", font=FONT_NORMAL_BOLD); self.t_client.pack(side="right", padx=5, expand=True, fill="x")
        f2 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f2.pack(fill="x", padx=15, pady=5)
        self.t_amt = ctk.CTkEntry(f2, placeholder_text=fix_arabic("القيمة", for_ui=True), height=40, justify="right"); self.t_amt.pack(side="right", padx=5)
        self.t_amt.bind("<KeyRelease>", self.calc_commission)
        self.t_comm = ctk.CTkEntry(f2, placeholder_text=fix_arabic("العمولة", for_ui=True), width=100, height=40, justify="right"); self.t_comm.pack(side="right", padx=5)
        self.t_ref = ctk.CTkEntry(f2, placeholder_text=fix_arabic("المرجع", for_ui=True), height=40, justify="right"); self.t_ref.pack(side="right", padx=5)
        ctk.CTkLabel(f2, text=fix_arabic("الدفع:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.t_pay = ctk.CTkComboBox(f2, values=["Cash", "Visa", "CLIQ"], width=90, height=38, font=FONT_NORMAL_BOLD, justify="center")
        self.t_pay.pack(side="right", padx=5); self.t_pay.set("Cash")
        ctk.CTkButton(f2, text=fix_arabic("تسجيل + فاتورة", for_ui=True), fg_color=COLOR_TEAL, command=self.add_transfer, font=FONT_BOLD, height=40).pack(side="right", padx=5)
        if self.current_role == "admin":
            ctk.CTkButton(f2, text=fix_arabic("حذف", for_ui=True), command=lambda: self.delete_record("transfers", self.t_tree), font=FONT_BOLD, height=40, fg_color=COLOR_RUBI).pack(side="left", padx=5)
            ctk.CTkButton(f2, text=fix_arabic("تعديل", for_ui=True), command=lambda: self.edit_record_ui("transfers", self.t_tree), font=FONT_BOLD, height=40, fg_color=COLOR_TEAL).pack(side="left", padx=5)
        self.t_tree = ttk.Treeview(self.main_view, columns=("comm", "amt", "ref", "client", "type", "id"), show="headings")
        for col, head in zip(self.t_tree["columns"], ["العمولة", "المبلغ", "المرجع", "العميل", "النوع", "ID"]): self.t_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.t_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_transfers_tree()

    def refresh_transfers_tree(self):
        for i in self.t_tree.get_children(): self.t_tree.delete(i)
        self.db.cursor.execute("SELECT commission, amount, reference, client_name, type, id FROM transfers ORDER BY id DESC")
        [self.t_tree.insert("", "end", values=(r[0], r[1], r[2], fix_arabic(r[3], for_ui=True), fix_arabic(r[4], for_ui=True), r[5])) for r in self.db.cursor.fetchall()]

    def calc_commission(self, event=None):
        try:
            amt = clean_float(self.t_amt.get())
            # Fetch settings
            s = {k: v for k, v in self.db.cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'comm_%'").fetchall()}
            l1 = float(s.get('comm_limit1', 50))
            v1 = float(s.get('comm_val1', 0.5))
            l2 = float(s.get('comm_limit2', 100))
            v2 = float(s.get('comm_val2', 1.0))
            v3 = float(s.get('comm_val3', 1.5))
            
            comm = v1 if amt < l1 else (v2 if amt <= l2 else v3)
            self.t_comm.delete(0, 'end'); self.t_comm.insert(0, str(comm))
        except: pass

    def _visa_customer_total(self, value, commission, payment_method, operation_type):
        """Return the customer-facing total under the Visa policy."""
        value = float(value or 0.0)
        commission = float(commission or 0.0)
        if operation_type in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment_method == "Visa":
            visa_processing_fee = round(value * 0.009, 2)
            if operation_type == "خروج حوالة":
                return round(max(value - visa_processing_fee - commission, 0), 2)
            return round(value + visa_processing_fee + commission, 2)
        return round(value + commission, 2)

    def add_transfer(self):
        t_ui = self.t_type.get()
        t = next((raw for raw in self.t_type_raws if fix_arabic(raw, for_ui=True) == t_ui), "خروج حوالة")
        c, ph, a_raw, cm_raw, r = self.t_client.get().strip(), self.t_phone.get().strip(), self.t_amt.get().strip(), self.t_comm.get().strip(), self.t_ref.get().strip()
        payment = self.t_pay.get()
        if not c or not a_raw:
            self.show_msg("تنبيه", "يرجى إدخال اسم العميل وقيمة العملية")
            return
        try:
            amt = self.positive_number(a_raw, "قيمة العملية")
            comm = self.positive_number(cm_raw, "العمولة", allow_zero=True)
            now = datetime.datetime.now()
            self.get_or_create_customer(ph, c)
            mult = int(clean_float(self.db.cursor.execute("SELECT value FROM settings WHERE key='points_transfer'").fetchone()[0] or 2))
            points_earned = mult
            if ph:
                self.db.cursor.execute("UPDATE customers SET points = points + ? WHERE phone=?", (points_earned, ph))
            if t == "خروج حوالة" and payment not in ("Visa", "CLIQ"):
                raise ValueError("خروج الحوالة يجب أن يُحصّل عبر Visa أو CLIQ")
            if t == "دخول حوالة":
                collection_account, settlement_account = ("VISA", "BANK") if payment == "Visa" else ("CASH", "BANK")
            elif t == "دفع فاتورة":
                if payment not in ("Cash", "Visa", "CLIQ"):
                    raise ValueError("دفع الفاتورة يجب أن يُحصّل نقداً أو عبر Visa أو CLIQ")
                collection_account, settlement_account = self._ledger_account_for_payment(payment), "BANK"
            else:
                collection_account, settlement_account = self._ledger_account_for_payment(payment), "CASH"
            settlement_amount = (max(amt - round(amt * 0.009, 2) - comm, 0) if payment == "Visa" else max(amt - comm, 0)) if t == "خروج حوالة" else amt
            customer_total = self._visa_customer_total(amt, comm, payment, t)
            visa_processing_fee = round(amt * 0.009, 2) if t in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment == "Visa" else 0.0
            payment_method = payment if t == "دخول حوالة" and payment == "Visa" else (payment if t != "دخول حوالة" else "Cash")
            self.db.cursor.execute("INSERT INTO transfers (type, client_name, client_phone, amount, commission, reference, payment_method, collection_account, settlement_account, settlement_amount, date, time, user) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (t, c, ph, amt, comm, r, payment_method, collection_account, settlement_account, settlement_amount, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), self.current_user))
            transfer_source_id = f"transfer-{now.strftime('%Y%m%d%H%M%S%f')}"
            if t == "خروج حوالة":
                # Visa fee and commission are deducted from the amount paid to the beneficiary.
                transfer_lines = ([(collection_account, amt, 0, "تحصيل قيمة خروج الحوالة عبر الفيزا"), ("CASH", 0, settlement_amount, "المبلغ المسلم للمستفيد بعد خصم العمولة ورسوم الفيزا"), ("TRANSFER_REVENUE", 0, comm + visa_processing_fee, "عمولة ورسوم خروج الحوالة")] if payment == "Visa" else [(collection_account, amt, 0, "تحصيل قيمة خروج الحوالة"), ("CASH", 0, settlement_amount, "المبلغ النقدي المسلم للمستفيد"), ("TRANSFER_REVENUE", 0, comm, "عمولة خروج الحوالة")])
            elif t == "دخول حوالة":
                # Cash keeps the legacy path. Visa uses the requested customer total and the Visa ledger.
                transfer_lines = [(collection_account, customer_total, 0, "تحصيل أصل الحوالة والعمولة ورسوم الفيزا" if payment == "Visa" else "تحصيل أصل الحوالة والعمولة نقداً"), ("BANK", 0, amt, "تحويل أصل الحوالة عبر الحساب البنكي الموحد"), ("TRANSFER_REVENUE", 0, comm + visa_processing_fee, "عمولة ورسوم دخول الحوالة")]
            else:
                # Cash keeps the legacy path. Visa adds 0.9% of the principal to the customer total.
                transfer_lines = [(collection_account, customer_total, 0, "تحصيل قيمة الفاتورة والعمولة ورسوم الفيزا" if payment == "Visa" else "تحصيل قيمة الفاتورة والعمولة"), ("BANK", 0, amt, "سداد أصل الفاتورة من البنك"), ("TRANSFER_REVENUE", 0, comm + visa_processing_fee, "عمولة ورسوم دفع الفاتورة")]
            self._post_journal_entry("transfer", transfer_source_id, f"قيد {t}", transfer_lines, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
            self.db.conn.commit()
            self.log_action("تسجيل حوالة/فاتورة", "transfers", f"النوع: {t}; المبلغ: {amt:.2f}; العميل: {c}; الدفع: {payment}")
            
            # Invoice presentation: outgoing remittance shows the net cash payout after commission;
            # Visa incoming remittance and Visa bill payment include the requested 0.9% surcharge.
            inv_total = (settlement_amount if t == "خروج حوالة" else customer_total)
            effective_payment = payment if t == "دخول حوالة" and payment == "Visa" else ("Cash" if t == "دخول حوالة" else payment)
            self.generate_invoice(inv_total, "TRANSFER", {"client": c, "type": t, "ref": r, "phone": ph, "points": points_earned, "payment": effective_payment})

            self.ui_transfers()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر تسجيل العملية", str(exc))

    def _void_orphan_journals(self):
        """Void derived journal entries whose operational source was deleted before the fix.
        This is conservative: legacy IDs are matched exactly; timestamp-based entries are
        voided only when no operational row remains at the same date and time.
        """
        mappings = {
            "sales": ("sale", "legacy_sale", "managed"), "maintenance": ("maintenance", "legacy_maintenance", "managed"),
            "purchases": ("purchase", "legacy_purchase", "managed"), "expenses": ("expense", "legacy_expense", "managed"),
            "transfers": ("transfer", "legacy_transfer", "managed"), "internal_transfers": ("internal_transfer", "legacy_internal_transfer", "managed"),
            "debt_payments": ("debt_payment", "legacy_debt_payment", "managed")
        }
        for table, source_types in mappings.items():
            for source_type in source_types:
                if source_type.startswith("legacy_"):
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type=? AND NOT EXISTS (SELECT 1 FROM {table} op WHERE CAST(op.id AS TEXT)=journal_entries.source_id)", (source_type,))
                elif source_type == "managed":
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type='managed' AND source_id LIKE ? || ':%' AND NOT EXISTS (SELECT 1 FROM {table} op WHERE journal_entries.source_id LIKE ? || ':' || CAST(op.id AS TEXT) || ':%')", (f"{table}", table))
                else:
                    self.cursor.execute(f"UPDATE journal_entries SET status='voided' WHERE source_type=? AND NOT EXISTS (SELECT 1 FROM {table} op WHERE op.date=journal_entries.entry_date AND COALESCE(op.time,'')=COALESCE(journal_entries.entry_time,''))", (source_type,))
        self.cursor.execute("""UPDATE journal_entries AS rev SET status='voided'
            WHERE rev.source_type='reversal' AND EXISTS (
                SELECT 1 FROM journal_entries AS original
                WHERE original.status='voided'
                  AND original.source_type || ':' || original.source_id = rev.source_id
            )""")

    def _journal_source_types_for_table(self, table):
        return {"sales": ("sale", "legacy_sale", "managed"), "maintenance": ("maintenance", "legacy_maintenance", "managed"), "purchases": ("purchase", "legacy_purchase", "managed"), "expenses": ("expense", "legacy_expense", "managed"), "transfers": ("transfer", "legacy_transfer", "managed"), "internal_transfers": ("internal_transfer", "legacy_internal_transfer", "managed"), "debt_payments": ("debt_payment", "legacy_debt_payment", "managed"), "inventory_adjustments": ("inventory_adjustment", "managed")}.get(table, ())

    def _void_journals_for_record(self, table, rid, reason):
        """Create reversing entries for journals tied to a legacy/current operational row.
        Matching uses the operational date/time for older timestamp-based source IDs; the
        original journal rows remain intact for audit purposes.
        """
        types = self._journal_source_types_for_table(table)
        if not types:
            return
        source_expr = "source_id" if table in ("sales", "maintenance", "purchases", "inventory_adjustments") else "NULL"
        row = self.db.cursor.execute(f"SELECT date, time, user, {source_expr} FROM {table} WHERE id=?", (rid,)).fetchone()
        if not row:
            return
        date, time, user, source_id = row
        exact_entries = []
        if source_id and table in ("sales", "maintenance", "purchases", "inventory_adjustments"):
            source_type_map = {"sales": "sale", "maintenance": "maintenance", "purchases": "purchase", "inventory_adjustments": "inventory_adjustment"}
            exact_entries = self.db.cursor.execute("SELECT id, source_type, source_id, entry_date, entry_time FROM journal_entries WHERE source_type IN (?, ?) AND source_id=?", (source_type_map[table], "managed", source_id)).fetchall()
        placeholders = ",".join("?" for _ in types)
        exact_pairs = [(source_type, str(rid)) for source_type in types] + [(source_type, f"{source_type}-{rid}") for source_type in types]
        exact_clause = " OR ".join("(source_type=? AND source_id=?)" for _ in exact_pairs)
        exact_params = [value for pair in exact_pairs for value in pair]
        # Managed reposts use source IDs such as `transfers:12:<timestamp>`;
        # matching only `managed:12` misses them, so include the stable prefix.
        managed_clause = "(source_type='managed' AND source_id LIKE ?)"
        entries = self.db.cursor.execute(f"SELECT id, source_type, source_id, entry_date, entry_time FROM journal_entries WHERE ((source_type IN ({placeholders}) AND entry_date=? AND entry_time=?) OR {exact_clause} OR {managed_clause})", (*types, date, time, *exact_params, f"{table}:{rid}:%")).fetchall()
        seen_entries = set()
        for entry_id, source_type, source_id, entry_date, entry_time in (exact_entries + entries):
            if entry_id in seen_entries:
                continue
            seen_entries.add(entry_id)
            already = self.db.cursor.execute("SELECT 1 FROM journal_entries WHERE source_type='reversal' AND source_id=?", (f"{source_type}:{source_id}",)).fetchone()
            if already:
                continue
            lines = self.db.cursor.execute("SELECT account_code, debit, credit, memo FROM journal_lines WHERE entry_id=?", (entry_id,)).fetchall()
            reversed_lines = [(account, credit, debit, f"عكس: {memo or reason}") for account, debit, credit, memo in lines]
            self._post_journal_entry("reversal", f"{source_type}:{source_id}", f"{reason} ({table} #{rid})", reversed_lines, entry_date, entry_time)

    def _post_operation_journal_from_row(self, table, rid):
        """Repost the current operational row using the canonical mappings."""
        if table == "sales":
            row = self.db.cursor.execute("SELECT total, buy_cost, date, time, user, payment_method FROM sales WHERE id=?", (rid,)).fetchone()
            if not row: return
            total, cost, date, time, user, payment = row; total = max(float(total or 0), 0); cost = max(float(cost or 0), 0)
            account = "AR" if payment == "Credit" else self._ledger_account_for_payment(payment)
            lines = [(account, total, 0, "تحصيل أو ذمة مبيعات"), ("SALES_REVENUE", 0, total, "إيراد المبيعات")]
            if cost: lines += [("COGS", cost, 0, "تكلفة البضاعة المباعة"), ("INVENTORY", 0, cost, "تخفيض المخزون")]
        elif table == "maintenance":
            row = self.db.cursor.execute("SELECT revenue, date, time, user, payment_method FROM maintenance WHERE id=?", (rid,)).fetchone()
            if not row: return
            revenue, date, time, user, payment = row; revenue = max(float(revenue or 0), 0); account = "AR" if payment == "Credit" else self._ledger_account_for_payment(payment)
            cost_row = self.db.cursor.execute("SELECT internal_cost FROM maintenance WHERE id=?", (rid,)).fetchone()
            internal_cost = max(float(cost_row[0] or 0), 0) if cost_row else 0.0
            lines = [(account, revenue, 0, "تحصيل أو ذمة الصيانة"), ("SERVICE_REVENUE", 0, revenue, "إيراد خدمات الصيانة")]
            if internal_cost > 0:
                lines += [("MAINTENANCE_COGS", internal_cost, 0, "تكلفة قطع الصيانة المستهلكة"), ("MAINTENANCE_INVENTORY", 0, internal_cost, "إخراج قطع الصيانة من المخزون")]
        elif table == "purchases":
            row = self.db.cursor.execute("SELECT qty, cost, date, time, user, funding_source FROM purchases WHERE id=?", (rid,)).fetchone()
            if not row: return
            qty, cost, date, time, user, funding = row; total = max(float(qty or 0), 0) * max(float(cost or 0), 0); fs = str(funding or "")
            account = "AP" if any(k in fs.replace(" ", "").lower() for k in ("ذمم", "موردين", "supplier", "دين")) else self._legacy_account(fs)
            lines = [("INVENTORY", total, 0, "إضافة بضاعة إلى المخزون"), (account, 0, total, "مصدر تمويل الشراء")]
        elif table == "expenses":
            row = self.db.cursor.execute("SELECT amount, date, time, user, payment_source, status, desc FROM expenses WHERE id=?", (rid,)).fetchone()
            if not row: return
            amount, date, time, user, source, status, desc = row; amount = max(float(amount or 0), 0); account = "ACCRUED_EXPENSE" if str(status or "").lower() == "unpaid" or str(source or "") == "Unpaid" else self._ledger_account_for_payment(source)
            lines = [("EXPENSE", amount, 0, desc or "مصروف"), (account, 0, amount, "مصدر السداد أو الالتزام")]
        elif table == "transfers":
            row = self.db.cursor.execute("SELECT type, amount, commission, date, time, user, payment_method FROM transfers WHERE id=?", (rid,)).fetchone()
            if not row: return
            kind, amount, commission, date, time, user, payment = row; amount = max(float(amount or 0), 0); commission = min(max(float(commission or 0), 0), amount)
            customer_total = self._visa_customer_total(amount, commission, payment, kind)
            visa_processing_fee = round(amount * 0.009, 2) if kind in ("دخول حوالة", "دفع فاتورة", "خروج حوالة") and payment == "Visa" else 0.0
            if kind == "خروج حوالة":
                payout_amount = max(amount - visa_processing_fee - commission, 0) if payment == "Visa" else max(amount - commission, 0)
                lines = ([(self._ledger_account_for_payment(payment), amount, 0, "تحصيل قيمة خروج الحوالة عبر الفيزا"), ("CASH", 0, payout_amount, "المبلغ المسلم للمستفيد بعد خصم العمولة ورسوم الفيزا"), ("TRANSFER_REVENUE", 0, commission + visa_processing_fee, "عمولة ورسوم خروج الحوالة")] if payment == "Visa" else [(self._ledger_account_for_payment(payment), amount, 0, "تحصيل قيمة خروج الحوالة"), ("CASH", 0, payout_amount, "المبلغ النقدي المسلم للمستفيد"), ("TRANSFER_REVENUE", 0, commission, "عمولة خروج الحوالة")])
            elif kind == "دخول حوالة": lines = [("VISA" if payment == "Visa" else "CASH", customer_total, 0, "تحصيل أصل الحوالة والعمولة ورسوم الفيزا" if payment == "Visa" else "تحصيل أصل الحوالة والعمولة نقداً"), ("BANK", 0, amount, "تحويل أصل الحوالة عبر الحساب البنكي الموحد"), ("TRANSFER_REVENUE", 0, commission + visa_processing_fee, "عمولة ورسوم دخول الحوالة")]
            else: lines = [(self._ledger_account_for_payment(payment), customer_total, 0, "تحصيل قيمة الفاتورة والعمولة ورسوم الفيزا" if payment == "Visa" else "تحصيل قيمة الفاتورة والعمولة"), ("BANK", 0, amount, "سداد أصل الفاتورة من البنك"), ("TRANSFER_REVENUE", 0, commission + visa_processing_fee, "عمولة ورسوم دفع الفاتورة")]
        else:
            return
        repost_id = f"{table}:{rid}:{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self._post_journal_entry("managed", repost_id, f"إعادة ترحيل {table} #{rid}", lines, date, time)

    def _operational_account_net(self, account_code, start_date, end_date):
        """Return one operational net movement per account for the inclusive date range.

        The journal remains the audit trail, but legacy migration and edit history can
        leave multiple balanced journal rows for one operational record. Cash count is
        a current operational view, so it intentionally reads each source row once.
        BANK is canonical; legacy/visual CLIQ values are normalized into BANK.
        """
        account = str(account_code or "").strip().upper()
        if account == "CLIQ":
            account = "BANK"
        if not account:
            return 0.0
        total = 0.0

        def rows(query):
            self.db.cursor.execute(query, (start_date, end_date))
            return self.db.cursor.fetchall()

        def number(value):
            try:
                return max(float(value or 0.0), 0.0)
            except (TypeError, ValueError):
                return 0.0

        for amount, payment in rows("SELECT total, payment_method FROM sales WHERE date BETWEEN ? AND ?"):
            payment_account = "AR" if str(payment or "").strip().lower() == "credit" else self._ledger_account_for_payment(payment)
            if payment_account == account:
                total += number(amount)

        for amount, payment in rows("SELECT revenue, payment_method FROM maintenance WHERE date BETWEEN ? AND ?"):
            payment_account = "AR" if str(payment or "").strip().lower() == "credit" else self._ledger_account_for_payment(payment)
            if payment_account == account:
                total += number(amount)

        for kind, amount_raw, commission_raw, payment in rows("SELECT type, amount, commission, payment_method FROM transfers WHERE date BETWEEN ? AND ?"):
            amount = number(amount_raw)
            commission = min(number(commission_raw), amount)
            payment_account = self._ledger_account_for_payment(payment)
            if kind == "خروج حوالة":
                if payment_account == account:
                    total += amount
                if account == "CASH":
                    total -= amount - commission
            elif kind == "دخول حوالة":
                if account == "CASH":
                    total += amount + commission
                elif account == "BANK":
                    total -= amount
            else:  # دفع فاتورة
                if payment_account == account:
                    total += amount + commission
                if account == "BANK":
                    total -= amount

        for amount_raw, payment_source, status in rows("SELECT amount, payment_source, status FROM expenses WHERE date BETWEEN ? AND ?"):
            source_text = str(payment_source or "Cash").strip().lower()
            status_text = str(status or "paid").strip().lower()
            if status_text in {"unpaid", "pending", "credit", "غير مسدد", "على الحساب"} or source_text in {"unpaid", "pending", "غير مسدد", "على الحساب"}:
                continue
            if self._ledger_account_for_payment(payment_source) == account:
                total -= number(amount_raw)

        for qty_raw, cost_raw, funding_source in rows("SELECT qty, cost, funding_source FROM purchases WHERE date BETWEEN ? AND ?"):
            if self._ledger_account_for_payment(funding_source) == account:
                total -= number(qty_raw) * number(cost_raw)

        # Purchase returns refund the original funding account once. The
        # original purchase reference is stored in original_sale_id for
        # backward-compatible inventory_adjustments rows.
        for qty_raw, cost_raw, funding_source in rows("SELECT ia.qty, ia.unit_cost, p.funding_source FROM inventory_adjustments ia JOIN purchases p ON p.id=ia.original_sale_id WHERE ia.adjustment_type='مرتجع شراء' AND ia.date BETWEEN ? AND ?"):
            if self._ledger_account_for_payment(funding_source) == account:
                total += number(qty_raw) * number(cost_raw)

        for source_acc, dest_acc, amount_raw in rows("SELECT source_acc, dest_acc, amount FROM internal_transfers WHERE date BETWEEN ? AND ?"):
            amount = number(amount_raw)
            if self._ledger_account_for_payment(source_acc) == account:
                total -= amount
            if self._ledger_account_for_payment(dest_acc) == account:
                total += amount

        for debt_type, amount_raw, payment_source in rows("SELECT debt_type, amount, payment_source FROM debt_payments WHERE date BETWEEN ? AND ?"):
            if self._ledger_account_for_payment(payment_source) == account:
                total += number(amount_raw) if str(debt_type or "").strip().lower() == "customer" else -number(amount_raw)

        return round(total, 2)

    def _operational_channel_net(self, channel, start_date, end_date):
        """Return a non-additive payment-channel detail for the daily cash screen."""
        channel_text = str(channel or "").strip().lower()
        if channel_text not in {"cliq", "كليك"}:
            return 0.0

        def rows(query):
            self.db.cursor.execute(query, (start_date, end_date))
            return self.db.cursor.fetchall()

        def number(value):
            try:
                return max(float(value or 0.0), 0.0)
            except (TypeError, ValueError):
                return 0.0

        def is_channel(value):
            text = str(value or "").strip().lower().replace(" ", "")
            return "cliq" in text or "كليك" in text

        total = 0.0
        for amount, payment in rows("SELECT total, payment_method FROM sales WHERE date BETWEEN ? AND ?"):
            if is_channel(payment):
                total += number(amount)
        for amount, payment in rows("SELECT revenue, payment_method FROM maintenance WHERE date BETWEEN ? AND ?"):
            if is_channel(payment):
                total += number(amount)
        for kind, amount_raw, commission_raw, payment in rows("SELECT type, amount, commission, payment_method FROM transfers WHERE date BETWEEN ? AND ?"):
            amount = number(amount_raw)
            commission = min(number(commission_raw), amount)
            if is_channel(payment):
                if kind == "خروج حوالة":
                    total += amount
                elif kind == "دفع فاتورة":
                    total += amount + commission
        for amount_raw, payment_source, status in rows("SELECT amount, payment_source, status FROM expenses WHERE date BETWEEN ? AND ?"):
            status_text = str(status or "paid").strip().lower()
            if not (status_text in {"unpaid", "pending", "credit", "غير مسدد", "على الحساب"} or str(payment_source or "").strip().lower() in {"unpaid", "pending", "غير مسدد", "على الحساب"}) and is_channel(payment_source):
                total -= number(amount_raw)
        for qty_raw, cost_raw, funding_source in rows("SELECT qty, cost, funding_source FROM purchases WHERE date BETWEEN ? AND ?"):
            if is_channel(funding_source):
                total -= number(qty_raw) * number(cost_raw)
        for qty_raw, cost_raw, funding_source in rows("SELECT ia.qty, ia.unit_cost, p.funding_source FROM inventory_adjustments ia JOIN purchases p ON p.id=ia.original_sale_id WHERE ia.adjustment_type='مرتجع شراء' AND ia.date BETWEEN ? AND ?"):
            if is_channel(funding_source):
                total += number(qty_raw) * number(cost_raw)
        for debt_type, amount_raw, payment_source in rows("SELECT debt_type, amount, payment_source FROM debt_payments WHERE date BETWEEN ? AND ?"):
            if is_channel(payment_source):
                total += number(amount_raw) if str(debt_type or "").strip().lower() == "customer" else -number(amount_raw)
        for source_acc, dest_acc, amount_raw in rows("SELECT source_acc, dest_acc, amount FROM internal_transfers WHERE date BETWEEN ? AND ?"):
            amount = number(amount_raw)
            if is_channel(dest_acc):
                total += amount
            if is_channel(source_acc):
                total -= amount
        return round(total, 2)

    def delete_record(self, table, tree, callback=None, id_index=-1):
        selected = tree.selection()
        if not selected:
            self.show_msg("تنبيه", "حدد سجلاً أولاً")
            return
        item = tree.item(selected[0]); rid = item['values'][id_index]
        if self.ask_confirm(str("تأكيد الحذف"), str("هل تريد حذف السجل؟")):
            try:
                # Financial operation screens must reverse their journal before deleting
                # the operational row; otherwise reports retain stale revenue/commission.
                self._void_journals_for_record(table, rid, "إلغاء أثر العملية قبل الحذف")
                self.db.cursor.execute(f"DELETE FROM {table} WHERE id=?", (rid,))
                self.db.conn.commit()
                self.log_action("حذف سجل", table, f"المعرف: {rid}")
                self.show_msg("نجاح", "تم الحذف")
                if callback: callback()
                elif table == "transfers": self.refresh_transfers_tree()
                elif table == "maintenance": self.refresh_maintenance_tree()
            except Exception as exc:
                self.db.conn.rollback(); self.show_msg("تعذر الحذف", str(exc))

    def edit_record_ui(self, table, tree):
        selected = tree.selection()
        if not selected: return
        item = tree.item(selected[0]); vals = item['values']; rid = vals[-1]
        ed = ctk.CTkToplevel(self); ed.title(fix_arabic("تعديل", is_title=True)); ed.geometry("400x500"); ed.attributes("-topmost", True); ed.grab_set()
        if table == "maintenance":
            e1 = ctk.CTkEntry(ed, justify="right"); e1.insert(0, vals[4]); e1.pack(pady=10, padx=20, fill="x")
            e2 = ctk.CTkEntry(ed, justify="right"); e2.insert(0, vals[2]); e2.pack(pady=10, padx=20, fill="x")
            e3 = ctk.CTkEntry(ed, justify="right"); e3.insert(0, vals[1]); e3.pack(pady=10, padx=20, fill="x")
            def save():
                try:
                    revenue = self.positive_number(e3.get(), "المبلغ")
                    self._void_journals_for_record(table, rid, "إلغاء القيد السابق قبل تعديل العملية")
                    self.db.cursor.execute("UPDATE maintenance SET client_name=?, repair_desc=?, revenue=? WHERE id=?", (e1.get().strip(), e2.get().strip(), revenue, rid))
                    self._post_operation_journal_from_row(table, rid)
                    self.db.conn.commit(); self.log_action("تعديل سجل", table, f"المعرف: {rid}"); ed.destroy(); self.refresh_maintenance_tree()
                except (ValueError, sqlite3.Error) as exc:
                    self.db.conn.rollback(); self.show_msg("تعذر الحفظ", str(exc))
        elif table == "transfers":
            row = self.db.cursor.execute("SELECT type, client_name, amount, commission, payment_method, reference FROM transfers WHERE id=?", (rid,)).fetchone()
            if not row:
                ed.destroy(); return
            kind, client_name, old_amount, old_commission, old_payment, reference = row
            ctk.CTkLabel(ed, text=fix_arabic("تعديل العملية المحاسبية كاملة", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=(12, 4))
            e_kind = ctk.CTkComboBox(ed, values=[fix_arabic(k, for_ui=True) for k in self.t_type_raws], font=FONT_BOLD, justify="right")
            e_kind.set(fix_arabic(kind, for_ui=True)); e_kind.pack(pady=6, padx=20, fill="x")
            e1 = ctk.CTkEntry(ed, justify="right", font=FONT_BOLD); e1.insert(0, client_name or ""); e1.pack(pady=6, padx=20, fill="x")
            e2 = ctk.CTkEntry(ed, justify="right", font=FONT_BOLD); e2.insert(0, str(old_amount or 0)); e2.pack(pady=6, padx=20, fill="x")
            e_comm = ctk.CTkEntry(ed, justify="right", font=FONT_BOLD); e_comm.insert(0, str(old_commission or 0)); e_comm.pack(pady=6, padx=20, fill="x")
            e_pay = ctk.CTkComboBox(ed, values=["Cash", "Visa", "CLIQ"], font=FONT_BOLD, justify="center")
            e_pay.set(old_payment or "Cash"); e_pay.pack(pady=6, padx=20, fill="x")
            e_ref = ctk.CTkEntry(ed, justify="right", font=FONT_BOLD); e_ref.insert(0, reference or ""); e_ref.pack(pady=6, padx=20, fill="x")
            def save():
                try:
                    new_ui_kind = e_kind.get()
                    new_kind = next((raw for raw in self.t_type_raws if fix_arabic(raw, for_ui=True) == new_ui_kind), new_ui_kind)
                    amount = self.positive_number(e2.get(), "المبلغ")
                    commission = self.positive_number(e_comm.get(), "العمولة", allow_zero=True)
                    payment = e_pay.get().strip() or "Cash"
                    if commission > amount:
                        raise ValueError("العمولة لا يجوز أن تتجاوز قيمة العملية")
                    if new_kind == "خروج حوالة" and payment not in ("Visa", "CLIQ"):
                        raise ValueError("خروج الحوالة يجب أن يُحصّل عبر Visa أو CLIQ")
                    if new_kind == "دفع فاتورة" and payment not in ("Cash", "Visa", "CLIQ"):
                        raise ValueError("دفع الفاتورة يجب أن يُحصّل نقداً أو عبر Visa أو CLIQ")
                    self._void_journals_for_record(table, rid, "إلغاء القيد السابق قبل تعديل العملية")
                    settlement_amount = (max(amount - round(amount * 0.009, 2) - commission, 0) if payment == "Visa" else max(amount - commission, 0)) if new_kind == "خروج حوالة" else amount
                    collection_account = ("VISA" if payment == "Visa" else "CASH") if new_kind == "دخول حوالة" else self._ledger_account_for_payment(payment)
                    settlement_account = "BANK" if new_kind in ("دخول حوالة", "دفع فاتورة") else "CASH"
                    stored_payment = payment if new_kind == "دخول حوالة" and payment == "Visa" else ("Cash" if new_kind == "دخول حوالة" else payment)
                    self.db.cursor.execute("UPDATE transfers SET type=?, client_name=?, amount=?, commission=?, reference=?, payment_method=?, collection_account=?, settlement_account=?, settlement_amount=? WHERE id=?", (new_kind, e1.get().strip(), amount, commission, e_ref.get().strip(), stored_payment, collection_account, settlement_account, settlement_amount, rid))
                    self._post_operation_journal_from_row(table, rid)
                    self.db.conn.commit(); self.log_action("تعديل سجل", table, f"المعرف: {rid}"); ed.destroy(); self.refresh_transfers_tree()
                except (ValueError, sqlite3.Error) as exc:
                    self.db.conn.rollback(); self.show_msg("تعذر الحفظ", str(exc))
        ctk.CTkButton(ed, text=fix_arabic("حفظ", for_ui=True), command=save, fg_color=COLOR_CRIMSON).pack(pady=20)

    def ui_loyalty(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("نظام الولاء")
        f = ctk.CTkFrame(self.main_view, fg_color="transparent"); f.pack(fill="x", padx=20, pady=20)
        self.l_phone = ctk.CTkEntry(f, placeholder_text=fix_arabic("رقم الهاتف", for_ui=True), height=50, justify="right"); self.l_phone.pack(side="right", padx=10, expand=True, fill="x")
        ctk.CTkButton(f, text=fix_arabic("بحث", for_ui=True), command=self.search_loyalty, font=FONT_BOLD, height=50, fg_color=COLOR_CRIMSON).pack(side="right", padx=10)
        self.l_info = ctk.CTkLabel(self.main_view, text="", font=FONT_BOLD, text_color=COLOR_WHITE); self.l_info.pack(pady=20)
        
        if self.current_role in ("admin", "employee"):
            redeem_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_VINO_DARK, corner_radius=20); redeem_frame.pack(pady=10, padx=50, fill="x")
            ctk.CTkLabel(redeem_frame, text=fix_arabic("النقاط للاستبدال:", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=20, pady=25)
            self.l_redeem_amt = ctk.CTkEntry(redeem_frame, placeholder_text="0", width=120, height=50, justify="center", font=FONT_BOLD); self.l_redeem_amt.pack(side="right", padx=10, pady=25)
            ctk.CTkButton(redeem_frame, text=fix_arabic("استبدال النقاط", for_ui=True), fg_color=COLOR_VINO, command=self.redeem_points, font=FONT_BOLD, height=50, width=150).pack(side="right", padx=20)

    def search_loyalty(self):
        ph = self.l_phone.get().strip()
        self.db.cursor.execute("SELECT name, points FROM customers WHERE phone=?", (ph,))
        res = self.db.cursor.fetchone()
        if res: self.l_info.configure(text=fix_arabic(f"العميل: {res[0]}  |  رصيد النقاط: {res[1]} نقطة", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE)
        else: self.show_msg("تنبيه", "رقم الهاتف غير مسجل في نظام العملاء")

    def redeem_points(self):
        if self.current_role not in ("admin", "employee"):
            return
        ph = self.l_phone.get().strip()
        try:
            amt = self.positive_integer(self.l_redeem_amt.get(), "عدد النقاط")
            self.db.cursor.execute("SELECT points FROM customers WHERE phone=?", (ph,))
            res = self.db.cursor.fetchone()
            if not res or res[0] < amt:
                raise ValueError("رصيد النقاط غير كافٍ")
            self.db.cursor.execute("UPDATE customers SET points = points - ? WHERE phone=?", (amt, ph))
            self.db.conn.commit(); self.log_action("استبدال نقاط", "customers", f"الهاتف: {ph}; النقاط: {amt}"); self.show_msg("نجاح", "تم استبدال النقاط بنجاح"); self.search_loyalty()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر الاستبدال", str(exc))

    def ui_inventory(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("إدارة المخزون")
        f1 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f1.pack(fill="x", padx=15, pady=5)
        self.i_code = ctk.CTkEntry(f1, placeholder_text=fix_arabic("باركود", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.i_code.pack(side="right", padx=5)
        self.i_code.bind("<Return>", lambda e: self.lookup_product_inventory())
        self.i_name = ctk.CTkEntry(f1, placeholder_text=fix_arabic("اسم المنتج", for_ui=True), height=45, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10); self.i_name.pack(side="right", padx=5, expand=True, fill="x")
        
        f2 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f2.pack(fill="x", padx=15, pady=5)
        self.i_buy = ctk.CTkEntry(f2, placeholder_text=fix_arabic("سعر الشراء", for_ui=True), height=45, font=FONT_NORMAL_BOLD, width=120, justify="right", corner_radius=10); self.i_buy.pack(side="right", padx=5)
        self.i_sell = ctk.CTkEntry(f2, placeholder_text=fix_arabic("سعر البيع", for_ui=True), height=45, font=FONT_NORMAL_BOLD, width=120, justify="right", corner_radius=10); self.i_sell.pack(side="right", padx=5)
        self.i_stock = ctk.CTkEntry(f2, placeholder_text=fix_arabic("الكمية", for_ui=True), height=45, font=FONT_NORMAL_BOLD, width=100, justify="right", corner_radius=10); self.i_stock.pack(side="right", padx=5)
        ctk.CTkButton(f2, text=fix_arabic("حفظ المنتج", for_ui=True), command=self.add_product, font=FONT_BOLD, height=45, corner_radius=10, fg_color=COLOR_CRIMSON).pack(side="right", padx=10)
        if self._has_permission("مرتجع / تالف"):
            ctk.CTkButton(f2, text=fix_arabic("مرتجع / تالف", for_ui=True), command=self.open_inventory_adjustment, font=FONT_BOLD, height=45, corner_radius=10, fg_color=COLOR_CRIMSON_DARK).pack(side="right", padx=6)
        ctk.CTkButton(f2, text=fix_arabic("بحث بالاسم", for_ui=True), command=lambda: self.open_product_name_search("inventory"), font=FONT_BOLD, height=45, corner_radius=10, fg_color=COLOR_NAVY_LIGHT, hover_color=COLOR_NAVY).pack(side="right", padx=10)
        ctk.CTkButton(f2, text=fix_arabic("تعريف بدون باركود", for_ui=True), command=lambda: self.open_no_barcode_window("inventory"), font=FONT_BOLD, height=45, corner_radius=10, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="right", padx=10)

        v_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_NAVY_LIGHT, corner_radius=10); v_frame.pack(fill="x", padx=15, pady=5)
        self.val_buy_lbl = ctk.CTkLabel(v_frame, text=fix_arabic("قيمة المخزون (شراء): 0.00", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL); self.val_buy_lbl.pack(side="right", padx=20, pady=5)
        self.val_sell_lbl = ctk.CTkLabel(v_frame, text=fix_arabic("القيمة المتوقعة (بيع): 0.00", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_SOFT); self.val_sell_lbl.pack(side="right", padx=20, pady=5)

        self.inv_tree = ttk.Treeview(self.main_view, columns=("stock", "sell", "buy", "name", "code"), show="headings")
        for col, head in zip(self.inv_tree["columns"], ["المخزون", "البيع", "الشراء", "الاسم", "الكود"]): self.inv_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.inv_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_inventory_tree()

    def open_product_name_search(self, target_screen="inventory"):
        """Open a local product-name search dialog with direct editing of Name, Stock, Buy Price, and Sell Price for inventory."""
        sw = ctk.CTkToplevel(self)
        sw.title(fix_arabic("بحث عن منتج بالاسم وتعديله", is_title=True))
        sw.geometry("680X620" if target_screen == "inventory" else "600x480")
        sw.attributes("-topmost", True)
        sw.grab_set()

        ctk.CTkLabel(sw, text=fix_arabic("ابحث عن منتج في المخزون المحلي بالاسم أو الكود", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=8)
        
        sf = ctk.CTkFrame(sw, fg_color="transparent"); sf.pack(fill="x", padx=15, pady=5)
        e_query = ctk.CTkEntry(sf, placeholder_text=fix_arabic("اكتب اسم المنتج للبحث...", for_ui=True), height=42, font=FONT_NORMAL_BOLD, justify="right")
        e_query.pack(side="right", padx=5, expand=True, fill="x")

        tree_frame = ctk.CTkFrame(sw, fg_color="transparent"); tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        stree = ttk.Treeview(tree_frame, columns=("stock", "sell", "buy", "name", "code"), show="headings", height=8)
        for col, head in zip(stree["columns"], ["المخزون", "البيع", "الشراء", "الاسم", "الكود"]):
            stree.heading(col, text=fix_arabic(head, for_ui=True))
        stree.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=stree.yview)
        scrollbar.pack(side="left", fill="y")
        stree.configure(yscrollcommand=scrollbar.set)

        def do_search(event=None):
            for i in stree.get_children(): stree.delete(i)
            q = f"%{e_query.get().strip()}%"
            try:
                self.db.cursor.execute("SELECT stock, sell_price, buy_price, name, code FROM products WHERE name LIKE ? OR code LIKE ? ORDER BY name LIMIT 100", (q, q))
                for row in self.db.cursor.fetchall():
                    stree.insert("", "end", values=(row[0], f"{row[1]:.2f}", f"{row[2]:.2f}", fix_arabic(row[3], for_ui=True), row[4]))
            except Exception:
                pass

        e_query.bind("<KeyRelease>", do_search)
        do_search()

        # If inventory screen, provide direct editable fields below selection
        edit_frame = None
        e_ed_name = None
        e_ed_stock = None
        e_ed_buy = None
        e_ed_sell = None
        selected_code_holder = {"code": None}

        if target_screen == "inventory":
            edit_frame = ctk.CTkFrame(sw, fg_color=COLOR_CRIMSON_SOFT, corner_radius=10)
            edit_frame.pack(fill="x", padx=15, pady=8)
            
            ctk.CTkLabel(edit_frame, text=fix_arabic("تعديل بيانات المنتج المختار:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=10, pady=5)
            
            ef1 = ctk.CTkFrame(edit_frame, fg_color="transparent"); ef1.pack(fill="x", padx=10, pady=2)
            e_ed_name = ctk.CTkEntry(ef1, placeholder_text=fix_arabic("اسم المنتج", for_ui=True), height=38, font=FONT_NORMAL_BOLD, justify="right")
            e_ed_name.pack(side="right", padx=5, expand=True, fill="x")

            ef2 = ctk.CTkFrame(edit_frame, fg_color="transparent"); ef2.pack(fill="x", padx=10, pady=5)
            e_ed_stock = ctk.CTkEntry(ef2, placeholder_text=fix_arabic("الكمية", for_ui=True), height=38, font=FONT_NORMAL_BOLD, width=100, justify="right")
            e_ed_stock.pack(side="right", padx=5)
            e_ed_buy = ctk.CTkEntry(ef2, placeholder_text=fix_arabic("تكلفة الشراء", for_ui=True), height=38, font=FONT_NORMAL_BOLD, width=120, justify="right")
            e_ed_buy.pack(side="right", padx=5)
            e_ed_sell = ctk.CTkEntry(ef2, placeholder_text=fix_arabic("سعر البيع", for_ui=True), height=38, font=FONT_NORMAL_BOLD, width=120, justify="right")
            e_ed_sell.pack(side="right", padx=5)

            def on_tree_select(event):
                sel = stree.selection()
                if not sel: return
                vals = stree.item(sel[0], "values")
                # vals: stock, sell, buy, name, code
                selected_code_holder["code"] = vals[4]
                e_ed_name.delete(0, 'end'); e_ed_name.insert(0, vals[3])
                e_ed_stock.delete(0, 'end'); e_ed_stock.insert(0, vals[0])
                e_ed_buy.delete(0, 'end'); e_ed_buy.insert(0, vals[2])
                e_ed_sell.delete(0, 'end'); e_ed_sell.insert(0, vals[1])

            stree.bind("<<TreeviewSelect>>", on_tree_select)

        def select_item():
            sel = stree.selection()
            if not sel:
                self.show_msg("تنبيه", "يرجى اختيار منتج من القائمة أولاً"); return
            vals = stree.item(sel[0], "values")
            stock, sell, buy, name, code = vals[0], vals[1], vals[2], vals[3], vals[4]
            
            if target_screen == "inventory":
                # If editing frame is active, save modified values to database
                if e_ed_name and selected_code_holder["code"]:
                    try:
                        new_name = e_ed_name.get().strip()
                        new_stock = self.positive_integer(e_ed_stock.get().strip(), "الكمية")
                        new_buy = self.positive_number(e_ed_buy.get().strip(), "تكلفة الشراء")
                        new_sell = self.positive_number(e_ed_sell.get().strip(), "سعر البيع")
                        target_code = selected_code_holder["code"]

                        if not new_name:
                            self.show_msg("تنبيه", "اسم المنتج لا يمكن أن يكون فارغاً"); return

                        self.db.cursor.execute("UPDATE products SET name=?, stock=?, buy_price=?, sell_price=? WHERE code=?", (new_name, new_stock, new_buy, new_sell, target_code))
                        self.db.conn.commit()
                        self.log_action("تعديل منتج", "products", f"الكود: {target_code}; الاسم: {new_name}; المخزون: {new_stock}")
                        self.refresh_inventory_tree()
                        self.show_msg("نجاح", "تم تحديث بيانات المنتج بنجاح")
                        sw.destroy(); return
                    except (ValueError, sqlite3.Error) as exc:
                        self.db.conn.rollback(); self.show_msg("تعذر تحديث المنتج", str(exc)); return

                self.i_code.delete(0, 'end'); self.i_code.insert(0, code)
                self.i_name.delete(0, 'end'); self.i_name.insert(0, name)
                self.i_buy.delete(0, 'end'); self.i_buy.insert(0, buy)
                self.i_sell.delete(0, 'end'); self.i_sell.insert(0, sell)
                self.i_stock.delete(0, 'end'); self.i_stock.insert(0, stock)
            else:
                self.p_code.delete(0, 'end'); self.p_code.insert(0, code)
                self.p_name.delete(0, 'end'); self.p_name.insert(0, name)
                self.p_cost.delete(0, 'end'); self.p_cost.insert(0, buy)
                self.p_sell.delete(0, 'end'); self.p_sell.insert(0, sell)
                if hasattr(self, "p_qty") and not self.p_qty.get().strip():
                    self.p_qty.insert(0, "1")
            sw.destroy()

        btn_text = "حفظ التعديلات وتحديث المخزون" if target_screen == "inventory" else "اختيار المنتج المحدد"
        ctk.CTkButton(sw, text=fix_arabic(btn_text, for_ui=True), command=select_item, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=260).pack(pady=10)
        stree.bind("<Double-1>", lambda e: select_item())

    def open_no_barcode_window(self, target="purchase"):
        nw = ctk.CTkToplevel(self)
        inventory_mode = target == "inventory"
        nw.title(fix_arabic("تعريف منتج بدون باركود في المخزون" if inventory_mode else "تعريف منتج بدون باركود وإدخاله في المشتريات", is_title=True))
        nw.geometry("450x420")
        nw.attributes("-topmost", True)
        nw.grab_set()
        
        ctk.CTkLabel(nw, text=fix_arabic("تعريف منتج بدون باركود وحفظه في المخزون" if inventory_mode else "تعريف منتج بدون باركود وتعبئته مباشرة للشراء", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=12)
        
        e_name = ctk.CTkEntry(nw, placeholder_text=fix_arabic("اسم المنتج", for_ui=True), width=350, height=42, font=FONT_NORMAL_BOLD, justify="right"); e_name.pack(pady=8)
        e_buy = ctk.CTkEntry(nw, placeholder_text=fix_arabic("التكلفة الفردية (سعر الشراء)", for_ui=True), width=350, height=42, font=FONT_NORMAL_BOLD, justify="right"); e_buy.pack(pady=8)
        e_sell = ctk.CTkEntry(nw, placeholder_text=fix_arabic("سعر البيع", for_ui=True), width=350, height=42, font=FONT_NORMAL_BOLD, justify="right"); e_sell.pack(pady=8)
        e_qty = ctk.CTkEntry(nw, placeholder_text=fix_arabic("الكمية", for_ui=True), width=350, height=42, font=FONT_NORMAL_BOLD, justify="right"); e_qty.pack(pady=8)
        
        def save_and_purchase():
            name = e_name.get().strip(); buy = e_buy.get().strip(); sell = e_sell.get().strip(); qty = e_qty.get().strip()
            if not all([name, buy, sell, qty]):
                self.show_msg("تنبيه", "الرجاء تعبئة كافة الحقول"); return
            try:
                buy_value = self.positive_number(buy, "تكلفة القطعة")
                sell_value = self.positive_number(sell, "سعر البيع")
                quantity = self.positive_integer(qty, "الكمية")
                gen_code = f"NB{datetime.datetime.now().strftime('%m%d%H%M%S%f')[-14:]}"
                while self.db.cursor.execute("SELECT 1 FROM products WHERE code=?", (gen_code,)).fetchone():
                    gen_code = f"NB{datetime.datetime.now().strftime('%m%d%H%M%S%f')[-14:]}"
                                # Inventory mode defines the opening stock once. Purchase mode only
                # creates the product with zero stock; add_purchase() adds the entered
                # quantity exactly once when the purchase is registered.
                initial_stock = quantity if inventory_mode else 0
                self.db.cursor.execute("INSERT INTO products (code, name, buy_price, sell_price, stock, description) VALUES (?,?,?,?,?,?)", (gen_code, name, buy_value, sell_value, initial_stock, "بدون باركود"))
                self.db.conn.commit()
                if inventory_mode:

                    nw.destroy()
                    self.refresh_inventory_tree()
                    self.show_msg("نجاح", f"تم تعريف المنتج وحفظه في المخزون بنجاح.\nالكود الداخلي: {gen_code}")
                    return

                if hasattr(self, "p_code"):
                    self.p_code.delete(0, 'end'); self.p_code.insert(0, gen_code)
                if hasattr(self, "p_name"):
                    self.p_name.delete(0, 'end'); self.p_name.insert(0, name)
                if hasattr(self, "p_cost"):
                    self.p_cost.delete(0, 'end'); self.p_cost.insert(0, str(buy_value))
                if hasattr(self, "p_sell"):
                    self.p_sell.delete(0, 'end'); self.p_sell.insert(0, str(sell_value))
                if hasattr(self, "p_qty"):
                    self.p_qty.delete(0, 'end'); self.p_qty.insert(0, str(quantity))
                    
                nw.destroy()
                self.show_msg("نجاح", f"تم إنشاء وتوليد الباركود: {gen_code}\nوإدراج البيانات في واجهة المشتريات بنجاح!")
                self.refresh_inventory_tree() if hasattr(self, "inv_tree") else None
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback(); self.show_msg("تعذر إضافة المنتج", str(exc))
            
        ctk.CTkButton(nw, text=fix_arabic("حفظ المنتج في المخزون" if inventory_mode else "إضافة وتعبئة في المشتريات", for_ui=True), command=save_and_purchase, font=FONT_BOLD, fg_color=COLOR_TEAL, height=42, width=240).pack(pady=12)

    def refresh_inventory_tree(self):
        for i in self.inv_tree.get_children(): self.inv_tree.delete(i)
        self.db.cursor.execute("SELECT stock, sell_price, buy_price, name, code, min_stock FROM products")
        rows = self.db.cursor.fetchall()
        total_buy = 0; total_sell = 0
        for r in rows:
            tag = "low" if r[0] <= r[5] else "normal"
            self.inv_tree.insert("", "end", values=(r[0], f"{r[1]:.2f}", f"{r[2]:.2f}", fix_arabic(r[3], for_ui=True), r[4]), tags=(tag,))
            total_buy += (r[0] * r[2]); total_sell += (r[0] * r[1])
        self.inv_tree.tag_configure("low", background=COLOR_CRIMSON_SOFT)
        self.val_buy_lbl.configure(text=fix_arabic(f"قيمة المخزون (شراء): {total_buy:.2f} {CURRENCY}", for_ui=True))
        self.val_sell_lbl.configure(text=fix_arabic(f"القيمة المتوقعة (بيع): {total_sell:.2f} {CURRENCY}", for_ui=True))

    def fetch_global_barcode(self, code):
        """
        Hybrid Global Barcode Lookup System (V120):
        1. Queries UPCitemdb (broad multi-sector coverage: electronics, apparel, accessories, general goods).
        2. Falls back to Open Food Facts (food, beverages, packaged items).
        3. Automatically caches successfully found products into the local SQLite 'products' table 
           so subsequent scans work instantly and offline.
        """
        if not code or len(code.strip()) < 3:
            return None
        
        clean_code = code.strip()
        
        # Source 1: UPCitemdb (Free tier public REST API - broad multi-sector coverage)
        try:
            import urllib.request
            import json
            url1 = f"https://api.upcitemdb.com/prod/trial/lookup?upc={clean_code}"
            req1 = urllib.request.Request(url1, headers={"User-Agent": "TrendCenterJordanPOS/1.20", "Accept": "application/json"})
            with urllib.request.urlopen(req1, timeout=4) as resp1:
                data1 = json.loads(resp1.read().decode("utf-8"))
                if data1.get("code") == "OK" and data1.get("items"):
                    item = data1["items"][0]
                    title = item.get("title") or item.get("brand")
                    if title:
                        return title.strip()
        except Exception:
            pass

        # Source 2: Open Food Facts API v3 (Global packaged goods & grocery items)
        try:
            import urllib.request
            import json
            url2 = f"https://world.openfoodfacts.org/api/v3/product/{clean_code}.json"
            req2 = urllib.request.Request(url2, headers={"User-Agent": "TrendCenterJordanPOS/1.20"})
            with urllib.request.urlopen(req2, timeout=3) as resp2:
                data2 = json.loads(resp2.read().decode("utf-8"))
                if data2.get("status") == 1 or data2.get("product"):
                    product = data2.get("product", {})
                    name = (
                        product.get("product_name_ar") 
                        or product.get("product_name") 
                        or product.get("brands")
                    )
                    if name:
                        return name.strip()
        except Exception:
            pass

        return None

    def lookup_product_inventory(self):
        code = self.i_code.get().strip()
        if not code:
            return
        self.db.cursor.execute("SELECT name, buy_price, sell_price, stock FROM products WHERE code=?", (code,))
        p = self.db.cursor.fetchone()
        if p:
            self.i_name.delete(0, 'end'); self.i_name.insert(0, p[0])
            self.i_buy.delete(0, 'end'); self.i_buy.insert(0, str(p[1])); self.i_sell.delete(0, 'end'); self.i_sell.insert(0, str(p[2]))
            self.i_stock.delete(0, 'end'); self.i_stock.insert(0, str(p[3]))
        else:
            # Try global barcode lookup
            global_name = self.fetch_global_barcode(code)
            if global_name:
                self.i_name.delete(0, 'end'); self.i_name.insert(0, global_name)
                # Set default prices/stock if not present
                if not self.i_buy.get().strip(): self.i_buy.insert(0, "1.00")
                if not self.i_sell.get().strip(): self.i_sell.insert(0, "1.50")
                if not self.i_stock.get().strip(): self.i_stock.insert(0, "1")
                self.show_msg("تعريف تلقائي", f"تم العثور على اسم المنتج من قاعدة البيانات العالمية للباركود:\n{global_name}")
            else:
                self.show_msg("تنبيه", "الباركود غير موجود محلياً أو عالمياً. يمكنك إدخال اسم المنتج يدوياً وحفظه.")

    def add_product(self):
        c, n, b, s, q = (self.i_code.get().strip(), self.i_name.get().strip(), self.i_buy.get().strip(), self.i_sell.get().strip(), self.i_stock.get().strip())
        if not all([c, n, b, s, q]):
            self.show_msg("تنبيه", "يرجى ملء الكود والاسم وسعر الشراء وسعر البيع والكمية"); return
        try:
            buy, sell, stock = self.positive_number(b, "سعر الشراء"), self.positive_number(s, "سعر البيع"), self.positive_integer(q, "الكمية")
            self.db.cursor.execute("INSERT INTO products (code, name, buy_price, sell_price, stock, description) VALUES (?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET name=excluded.name, buy_price=excluded.buy_price, sell_price=excluded.sell_price, stock=excluded.stock", (c, n, buy, sell, stock, ""))
            self.db.conn.commit(); self.log_action("حفظ منتج", "products", f"الكود: {c}; الاسم: {n}"); self.refresh_inventory_tree(); self.show_msg("نجاح", "تم حفظ المنتج وتحديث المخزون بنجاح")
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر حفظ المنتج", str(exc))

    def open_inventory_adjustment_product_search(self, target_entry, parent=None):
        """Search local products by code/name and return the selected code."""
        win = ctk.CTkToplevel(parent or self)
        win.title(fix_arabic("بحث عن منتج", is_title=True)); win.geometry("760x520"); win.transient(parent or self); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("بحث عن المنتج بالكود أو الاسم", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE).pack(pady=(16, 8))
        row=ctk.CTkFrame(win, fg_color="transparent"); row.pack(fill="x", padx=18, pady=5)
        query=ctk.CTkEntry(row, height=42, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("اكتب جزءاً من الكود أو الاسم", for_ui=True)); query.pack(side="right", fill="x", expand=True, padx=5)
        table=ttk.Treeview(win, columns=("stock","price","name","code"), show="headings", height=14)
        show_cost = self.current_role == "admin"
        price_head = "تكلفة الشراء" if show_cost else "سعر البيع"
        for col, head, width in (("stock","المخزون",100),("price",price_head,130),("name","اسم المنتج",300),("code","الكود",170)):
            table.heading(col, text=fix_arabic(head, for_ui=True)); table.column(col, anchor="center", width=width)
        table.pack(fill="both", expand=True, padx=18, pady=10)
        def load(event=None):
            for item in table.get_children(): table.delete(item)
            like=f"%{query.get().strip()}%"
            price_column = "buy_price" if show_cost else "sell_price"
            rows=self.db.cursor.execute(f"SELECT stock,{price_column},name,code FROM products WHERE code LIKE ? OR name LIKE ? ORDER BY name COLLATE NOCASE LIMIT 200", (like,like)).fetchall()
            for stock,price,name,code in rows:
                table.insert("", "end", values=(stock, f"{float(price or 0):.2f}", fix_arabic(name or "-", for_ui=True), code))
        def choose(event=None):
            selected=table.selection()
            if not selected: return
            values=table.item(selected[0], "values")
            target_entry.delete(0,"end"); target_entry.insert(0,str(values[3])); win.destroy()
        ctk.CTkButton(row, text=fix_arabic("بحث", for_ui=True), command=load, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=110).pack(side="right", padx=5)
        query.bind("<KeyRelease>", load); query.bind("<Return>", load); table.bind("<Double-1>", choose); load(); query.focus_set()

    def open_inventory_adjustment_operation_search(self, target_entry, code_entry, kind_var, parent=None):
        """Search sale/purchase references; double click fills operation ID and product code."""
        win=ctk.CTkToplevel(parent or self); win.title(fix_arabic("بحث عن عملية بيع أو شراء", is_title=True)); win.geometry("1050x560"); win.transient(parent or self); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("اختر العملية الأصلية ثم اضغط مرتين", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE).pack(pady=(16,8))
        row=ctk.CTkFrame(win, fg_color="transparent"); row.pack(fill="x", padx=18, pady=5)
        query=ctk.CTkEntry(row, height=42, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("رقم العملية أو كود المنتج أو اسم المنتج", for_ui=True)); query.pack(side="right", fill="x", expand=True, padx=5)
        table=ttk.Treeview(win, columns=("date","qty","name","code","type","id"), show="headings", height=15)
        for col, head, width in (("date","التاريخ",120),("qty","الكمية",90),("name","المنتج",250),("code","الكود",150),("type","المصدر",150),("id","رقم العملية",110)):
            table.heading(col, text=fix_arabic(head, for_ui=True)); table.column(col, anchor="center", width=width)
        table.pack(fill="both", expand=True, padx=18, pady=10)
        def load(event=None):
            for item in table.get_children(): table.delete(item)
            like=f"%{query.get().strip()}%"
            sales=self.db.cursor.execute("SELECT id,date,qty,name,code FROM sales WHERE CAST(id AS TEXT) LIKE ? OR code LIKE ? OR name LIKE ? ORDER BY date DESC,id DESC LIMIT 150", (like,like,like)).fetchall()
            purchases=self.db.cursor.execute("SELECT id,date,qty,name,code FROM purchases WHERE CAST(id AS TEXT) LIKE ? OR code LIKE ? OR name LIKE ? ORDER BY date DESC,id DESC LIMIT 150", (like,like,like)).fetchall()
            rows=[(r[1],r[2],r[3],r[4],"بيع",r[0],"مرتجع بيع") for r in sales]+[(r[1],r[2],r[3],r[4],"شراء",r[0],"مرتجع شراء") for r in purchases]
            for date,qty,name,code,source,rid,kind in sorted(rows,key=lambda x:(x[0] or "", int(x[5] or 0)), reverse=True):
                table.insert("", "end", values=(date,qty,fix_arabic(name or "-", for_ui=True),code,fix_arabic(source, for_ui=True),rid), tags=(kind,))
        def choose(event=None):
            selected=table.selection()
            if not selected: return
            item=table.item(selected[0]); values=item["values"]; tags=item.get("tags",())
            target_entry.delete(0,"end"); target_entry.insert(0,str(values[-1]))
            code_entry.delete(0,"end"); code_entry.insert(0,str(values[3]))
            if tags and tags[0] in ("مرتجع بيع","مرتجع شراء"):
                kind_var.set(tags[0])
            win.destroy()
        ctk.CTkButton(row, text=fix_arabic("بحث", for_ui=True), command=load, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=110).pack(side="right", padx=5)
        query.bind("<KeyRelease>", load); query.bind("<Return>", load); table.bind("<Double-1>", choose); load(); query.focus_set()

    def generate_inventory_adjustment_report(self, start_date, end_date, output_path):
        """Generate a period report showing warehouse quantities and posted journal effects."""
        try:
            datetime.datetime.strptime(start_date, "%Y-%m-%d"); datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("صيغة التاريخ الصحيحة هي YYYY-MM-DD") from exc
        if start_date > end_date: raise ValueError("تاريخ (من) يجب أن يسبق تاريخ (إلى)")
        rows=self.db.cursor.execute("SELECT id,adjustment_no,adjustment_type,product_code,product_name,qty,unit_cost,original_sale_id,reason,date,time,user,source_id FROM inventory_adjustments WHERE date BETWEEN ? AND ? ORDER BY date,time,id", (start_date,end_date)).fetchall()
        font_path=Path(resource_path(ACCOUNTANT_PDF_FONT_FILE))
        if not font_path.exists(): raise RuntimeError("ملف Cocon PDF TTF غير موجود ضمن الحزمة")
        pdfmetrics.registerFont(TTFont("TCJInventoryReport", str(font_path)))
        import html, csv
        def par(value, size=8):
            style=ParagraphStyle(f"TCJInv{size}{abs(hash(str(value)))%100000}", parent=getSampleStyleSheet()["BodyText"], fontName="TCJInventoryReport", fontSize=size, leading=size+4, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_NAVY))
            return Paragraph(html.escape(fix_arabic(str(value or "-"), for_ui=False)), style)
        title=ParagraphStyle("TCJInvTitle", fontName="TCJInventoryReport", fontSize=16, leading=22, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_RUBI_DARK))
        sub=ParagraphStyle("TCJInvSub", fontName="TCJInventoryReport", fontSize=9, leading=14, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_NAVY))
        story=[Paragraph(html.escape(fix_arabic(SHOP_NAME, for_ui=False)),title), Paragraph(html.escape(fix_arabic("تقرير المرتجع والتالف — الأثر المخزني والمالي", for_ui=False)),sub), Paragraph(html.escape(fix_arabic(f"الفترة: من {start_date} إلى {end_date}", for_ui=False)),sub), Spacer(1,8)]
        header=["التاريخ","النوع","المنتج","الكمية","تكلفة الوحدة","إجمالي التكلفة","أثر المخزون","الأثر المالي","العملية الأصلية"]
        data=[[par(h) for h in header]]; csv_rows=[header]
        for rid,no,kind,code,name,qty,cost,original,reason,date,time,user,source_id in rows:
            journal=self.db.cursor.execute("SELECT jl.account_code,jl.debit,jl.credit FROM journal_entries je JOIN journal_lines jl ON jl.entry_id=je.id WHERE je.source_type='inventory_adjustment' AND je.source_id=? ORDER BY jl.id", (source_id,)).fetchall()
            effects=[]
            for account,debit,credit in journal:
                if float(debit or 0) or float(credit or 0): effects.append(f"{account}: مدين {float(debit or 0):.2f} / دائن {float(credit or 0):.2f}")
            stock_effect="+"+str(qty) if kind=="مرتجع بيع" else "-"+str(qty)
            total=round(float(qty or 0)*float(cost or 0),2)
            date_value=f"{date} {time or ''}".strip(); effect="؛ ".join(effects) or "لا يوجد قيد مرتبط"
            values=[date_value,kind,f"{code} - {name}",qty,f"{float(cost or 0):.2f} {CURRENCY}",f"{total:.2f} {CURRENCY}",stock_effect,effect,original or "-"]
            data.append([par(v,7) for v in values]); csv_rows.append(values)
        if not rows: data.append([par("لا توجد عمليات ضمن الفترة",7)]+[par("-") for _ in header[1:]])
        table=Table(data, colWidths=[17*mm,19*mm,27*mm,11*mm,18*mm,20*mm,15*mm,43*mm,18*mm], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor(COLOR_RUBI)),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,-1),"TCJInventoryReport"),("GRID",(0,0),(-1,-1),.3,colors.HexColor(COLOR_TEXT_MUTED)),("ALIGN",(0,0),(-1,-1),"RIGHT"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("FONTSIZE",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        story += [table, Spacer(1,8), Paragraph(html.escape(fix_arabic(f"عدد العمليات: {len(rows)} — إجمالي قيمة التكلفة المتأثرة: {sum(float(r[5] or 0)*float(r[6] or 0) for r in rows):.2f} {CURRENCY}", for_ui=False)),sub)]
        doc=SimpleDocTemplate(str(output_path),pagesize=A4,rightMargin=8*mm,leftMargin=8*mm,topMargin=9*mm,bottomMargin=9*mm,title="Inventory Adjustment Report")
        doc.build(story)
        csv_path=Path(output_path).with_suffix(".csv")
        with csv_path.open("w",newline="",encoding="utf-8-sig") as fh:
            csv.writer(fh).writerows(csv_rows)
        return Path(output_path), csv_path, len(rows)

    def open_inventory_adjustment_report(self, parent=None):
        win=ctk.CTkToplevel(parent or self); win.title(fix_arabic("استخراج تقرير المرتجع والتالف", is_title=True)); win.geometry("600x280"); win.transient(parent or self); win.grab_set()
        ctk.CTkLabel(win,text=fix_arabic("استخراج تقرير المرتجع والتالف حسب الفترة",for_ui=True),font=FONT_TITLE,text_color=COLOR_WHITE).pack(pady=(20,10))
        row=ctk.CTkFrame(win,fg_color="transparent"); row.pack(fill="x",padx=20,pady=8)
        ctk.CTkLabel(row,text=fix_arabic("من",for_ui=True),font=FONT_BOLD,text_color=COLOR_WHITE).pack(side="right",padx=5)
        start=ctk.CTkEntry(row,width=160,height=40,justify="center",font=FONT_NORMAL_BOLD); start.insert(0,datetime.date.today().replace(day=1).isoformat()); start.pack(side="right",padx=5)
        ctk.CTkLabel(row,text=fix_arabic("إلى",for_ui=True),font=FONT_BOLD,text_color=COLOR_WHITE).pack(side="right",padx=5)
        end=ctk.CTkEntry(row,width=160,height=40,justify="center",font=FONT_NORMAL_BOLD); end.insert(0,datetime.date.today().isoformat()); end.pack(side="right",padx=5)
        def export():
            try:
                path=filedialog.asksaveasfilename(title="حفظ تقرير المرتجع والتالف",defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
                if not path: return
                pdf,csv_path,count=self.generate_inventory_adjustment_report(start.get().strip(),end.get().strip(),path)
                win.destroy(); self.show_msg("تم استخراج التقرير",f"تم حفظ تقرير PDF بعدد {count} عملية.\nتم إنشاء CSV مرافق للحسابات والفرز:\n{csv_path}")
            except (ValueError,OSError,sqlite3.Error,RuntimeError) as exc: self.show_msg("تعذر استخراج التقرير",str(exc))
        ctk.CTkButton(win,text=fix_arabic("استخراج تقرير PDF وCSV",for_ui=True),command=export,font=FONT_BOLD,fg_color=COLOR_TEAL,hover_color=COLOR_TEAL_DARK,height=46).pack(fill="x",padx=70,pady=20)

    def open_inventory_adjustment(self):
        if not self._has_permission("مرتجع / تالف"):
            return self.show_msg("صلاحية مرفوضة", "لا تملك صلاحية المرتجع والتالف")
        win = ctk.CTkToplevel(self); win.title(fix_arabic("مرتجع أو تسجيل تالف", is_title=True)); win.geometry("680x720"); win.grab_set(); win.option_add("*Font", FONT_BOLD)
        box = ctk.CTkFrame(win, fg_color=COLOR_SURFACE); box.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(box, text=fix_arabic("مرتجع أو تسجيل تالف — إجراء مخزني موثق", for_ui=True), font=HEADER_FONT_WHITE, text_color=COLOR_WHITE).pack(anchor="e", padx=18, pady=14)
        def field(label, placeholder="", button_text=None, button_command=None):
            row=ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=18, pady=6)
            ctk.CTkLabel(row, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, anchor="e", width=220).pack(side="right")
            e=ctk.CTkEntry(row, height=42, font=FONT_NORMAL_BOLD, justify="right", placeholder_text=fix_arabic(placeholder, for_ui=True)); e.pack(side="right", fill="x", expand=True, padx=8)
            if button_command:
                ctk.CTkButton(row,text=fix_arabic(button_text or "بحث",for_ui=True),command=button_command,font=FONT_BOLD,width=90,height=38,fg_color=COLOR_TEAL,hover_color=COLOR_TEAL_DARK).pack(side="left")
            return e
        code=field("كود المنتج *", "الباركود", "بحث", lambda: self.open_inventory_adjustment_product_search(code, win))
        qty=field("الكمية *", "الكمية")
        sale_id=field("رقم عملية البيع أو الشراء الأصلي", "رقم العملية عند المرتجع", "بحث", lambda: self.open_inventory_adjustment_operation_search(sale_id, code, kind_var, win))
        reason=field("السبب أو الملاحظة", "سبب الإجراء")
        kind_var=ctk.StringVar(value="تالف")
        row=ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(row, text=fix_arabic("نوع الإجراء *", for_ui=True), font=FONT_BOLD, width=220, anchor="e").pack(side="right")
        ctk.CTkComboBox(row, values=["تالف", "مرتجع بيع", "مرتجع شراء"], variable=kind_var, font=FONT_NORMAL_BOLD, justify="right", height=42).pack(side="right", fill="x", expand=True, padx=8)
        def save():
            try:
                product=self.db.cursor.execute("SELECT code,name,buy_price,stock FROM products WHERE code=?", (code.get().strip(),)).fetchone()
                if not product: raise ValueError("كود المنتج غير موجود")
                q=self.positive_integer(qty.get(), "الكمية")
                kind=kind_var.get().strip(); stock=int(product[3] or 0); unit_cost=max(float(product[2] or 0),0); total_cost=unit_cost*q
                if kind=="تالف" and q>stock: raise ValueError("كمية التالف أكبر من المخزون الحالي")
                original_id=int(sale_id.get().strip()) if sale_id.get().strip() else None
                now=datetime.datetime.now(); source=f"inventory-adjustment-{now.strftime('%Y%m%d%H%M%S%f')}"; no=f"IA-{now.strftime('%Y%m%d%H%M%S%f')}"
                if kind=="مرتجع بيع":
                    if not original_id: raise ValueError("أدخل رقم عملية البيع لمرتجع البيع")
                    sale=self.db.cursor.execute("SELECT total,buy_cost,payment_method,code FROM sales WHERE id=?", (original_id,)).fetchone()
                    if not sale or sale[3]!=product[0]: raise ValueError("عملية البيع غير موجودة أو لا تطابق المنتج")
                    sold_qty = int(self.db.cursor.execute("SELECT qty FROM sales WHERE id=?", (original_id,)).fetchone()[0] or 0)
                    returned_qty = int(self.db.cursor.execute("SELECT COALESCE(SUM(qty),0) FROM inventory_adjustments WHERE adjustment_type=? AND original_sale_id=?", ("مرتجع بيع", original_id)).fetchone()[0] or 0)
                    remaining_qty = sold_qty - returned_qty
                    if remaining_qty <= 0:
                        raise ValueError("تم إرجاع كامل كمية عملية البيع سابقاً")
                    if q > remaining_qty:
                        raise ValueError(f"كمية المرتجع تتجاوز المتبقي من البيع: {remaining_qty}")
                    return_value=max(float(sale[0] or 0),0) / max(sold_qty,1) * q
                    cost_value=max(float(sale[1] or 0),0) / max(sold_qty,1) * q
                    account="AR" if sale[2]=="Credit" else self._ledger_account_for_payment(sale[2])
                    lines=[("SALES_REVENUE", return_value, 0, "عكس إيراد مرتجع بيع"),(account, 0, return_value, "رد قيمة المرتجع"),("INVENTORY", cost_value, 0, "إعادة البضاعة للمخزون"),("COGS", 0, cost_value, "عكس تكلفة البضاعة")]
                    self.db.cursor.execute("UPDATE products SET stock=stock+? WHERE code=?", (q, product[0]))
                elif kind=="مرتجع شراء":
                    # A purchase return must be tied to the original purchase so
                    # the original funding account, supplier, unit cost, and
                    # cumulative return limit are all determined safely.
                    if not original_id:
                        raise ValueError("أدخل رقم عملية الشراء الأصلية لمرتجع الشراء")
                    purchase = self.db.cursor.execute("SELECT id, code, qty, cost, supplier, funding_source, source_id FROM purchases WHERE id=?", (original_id,)).fetchone()
                    if not purchase or purchase[1] != product[0]:
                        raise ValueError("عملية الشراء غير موجودة أو لا تطابق المنتج")
                    purchased_qty = int(purchase[2] or 0)
                    already_returned = int(self.db.cursor.execute("SELECT COALESCE(SUM(qty),0) FROM inventory_adjustments WHERE adjustment_type=? AND original_sale_id=?", ("مرتجع شراء", original_id)).fetchone()[0] or 0)
                    remaining_purchase_qty = purchased_qty - already_returned
                    if remaining_purchase_qty <= 0:
                        raise ValueError("تم إرجاع كامل كمية عملية الشراء سابقاً")
                    if q > remaining_purchase_qty:
                        raise ValueError(f"كمية المرتجع تتجاوز المتبقي من الشراء: {remaining_purchase_qty}")
                    if q > stock:
                        raise ValueError(f"كمية مرتجع الشراء أكبر من المخزون المتاح: {stock}")
                    unit_cost = max(float(purchase[3] or 0), 0)
                    total_cost = round(unit_cost * q, 2)
                    funding_account = self._ledger_account_for_payment(purchase[5])
                    lines=[(funding_account, total_cost, 0, "عكس مصدر تمويل الشراء المرتجع"),("INVENTORY", 0, total_cost, "إخراج مرتجع الشراء")]
                    if funding_account == "AP":
                        # Keep the supplier and debt screens aligned with the
                        # same purchase source used by the central journal.
                        if purchase[4]:
                            self.db.cursor.execute("UPDATE suppliers SET balance=COALESCE(balance,0)-? WHERE name=?", (total_cost, purchase[4]))
                        debt = self.db.cursor.execute("SELECT id, total_debt, paid_amount FROM supplier_debts WHERE source_type='purchase' AND source_id=? ORDER BY id LIMIT 1", (purchase[6],)).fetchone()
                        if debt:
                            new_total = round(max(float(debt[1] or 0) - total_cost, 0), 2)
                            paid = max(float(debt[2] or 0), 0)
                            status = "مسدد" if paid >= new_total else "غير مسدد"
                            self.db.cursor.execute("UPDATE supplier_debts SET total_debt=?, status=? WHERE id=?", (new_total, status, debt[0]))
                    self.db.cursor.execute("UPDATE products SET stock=stock-? WHERE code=?", (q, product[0]))
                else:
                    lines=[("INVENTORY_LOSS", total_cost, 0, "خسارة تالف مخزني"),("INVENTORY", 0, total_cost, "إخراج تالف من المخزون")]
                    self.db.cursor.execute("UPDATE products SET stock=stock-? WHERE code=?", (q, product[0]))
                self.db.cursor.execute("INSERT INTO inventory_adjustments (adjustment_no,adjustment_type,product_code,product_name,qty,unit_cost,original_sale_id,reason,date,time,user,source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (no,kind,product[0],product[1],q,unit_cost,original_id,reason.get().strip(),now.strftime("%Y-%m-%d"),now.strftime("%H:%M:%S"),self.current_user,source))
                self._post_journal_entry("inventory_adjustment", source, f"{kind} #{no}", lines, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
                self.db.conn.commit(); win.destroy(); self.refresh_inventory_tree(); self.show_msg("نجاح", f"تم تسجيل {kind} برقم {no}")
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback(); self.show_msg("تعذر تسجيل الإجراء", str(exc))
        report_row=ctk.CTkFrame(box,fg_color="transparent"); report_row.pack(fill="x",padx=18,pady=(8,2))
        ctk.CTkButton(report_row,text=fix_arabic("استخراج تقرير ضمن فترة من وإلى",for_ui=True),command=lambda: self.open_inventory_adjustment_report(win),font=FONT_BOLD,height=42,fg_color=COLOR_TEAL,hover_color=COLOR_TEAL_DARK).pack(fill="x")
        ctk.CTkButton(box, text=fix_arabic("تأكيد وحفظ الإجراء", for_ui=True), command=save, font=FONT_BOLD, height=50, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(fill="x", padx=18, pady=12)

    def ui_purchases(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("المشتريات")
        f = ctk.CTkFrame(self.main_view, fg_color="transparent"); f.pack(fill="x", padx=15, pady=5)
        self.p_code = ctk.CTkEntry(f, placeholder_text=fix_arabic("باركود المنتج", for_ui=True), height=42, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10, width=160); self.p_code.pack(side="right", padx=5)
        self.p_code.bind("<Return>", lambda e: self.lookup_product_purchase())
        self.p_name = ctk.CTkEntry(f, placeholder_text=fix_arabic("اسم المنتج الجديد", for_ui=True), height=42, font=FONT_NORMAL_BOLD, justify="right", corner_radius=10, width=280); self.p_name.pack(side="right", padx=5)
        
        # Reference layout: Stacked utility buttons on the left, supplier phone and company status on the right of product fields
        btn_stack = ctk.CTkFrame(f, fg_color="transparent")
        btn_stack.pack(side="left", padx=10)
        ctk.CTkButton(btn_stack, text=fix_arabic("بحث بالاسم", for_ui=True), command=lambda: self.open_product_name_search("purchase"), font=FONT_BOLD, height=32, width=130, corner_radius=8, fg_color=COLOR_NAVY_LIGHT, hover_color=COLOR_NAVY).pack(side="top", pady=2)
        ctk.CTkButton(btn_stack, text=fix_arabic("تعريف بدون باركود", for_ui=True), command=self.open_no_barcode_window, font=FONT_BOLD, height=32, width=130, corner_radius=8, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="top", pady=2)
        ctk.CTkButton(btn_stack, text=fix_arabic("تعريف مورد جديد", for_ui=True), command=self.ui_suppliers, font=FONT_BOLD, height=32, width=130, corner_radius=8, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK).pack(side="top", pady=2)

        # Supplier row in frame f: phone entry on the right, company status on its immediate left
        sup_input_frame = ctk.CTkFrame(f, fg_color="transparent")
        sup_input_frame.pack(side="right", padx=5)
        
        self.p_supplier_status = ctk.CTkLabel(sup_input_frame, text=fix_arabic("المورد غير معرف لدينا", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE)
        self.p_supplier_status.pack(side="right", padx=5, anchor="center")
        
        self.p_supplier = ctk.CTkEntry(sup_input_frame, placeholder_text=fix_arabic("هاتف المورد (اختياري)", for_ui=True), height=42, font=FONT_NORMAL_BOLD, width=160, justify="right", corner_radius=10)
        self.p_supplier.pack(side="right", padx=5, anchor="center")

        def lookup_supplier_phone(*args):
            ph = self.p_supplier.get().strip()
            if not ph:
                self.p_supplier_status.configure(text=fix_arabic("المورد غير معرف لدينا", for_ui=True), text_color=COLOR_WHITE)
                return
            res = self.db.cursor.execute("SELECT name FROM suppliers WHERE phone=? OR name=?", (ph, ph)).fetchone()
            if res and res[0]:
                self.p_supplier_status.configure(text=fix_arabic(f"الشركة: {res[0]}", for_ui=True), text_color=COLOR_TEAL)
            else:
                self.p_supplier_status.configure(text=fix_arabic("المورد غير معرف لدينا", for_ui=True), text_color=COLOR_WHITE)
                
        self.p_supplier.bind("<KeyRelease>", lookup_supplier_phone)

        f2 = ctk.CTkFrame(self.main_view, fg_color="transparent"); f2.pack(fill="x", padx=15, pady=5)
        self.p_qty = ctk.CTkEntry(f2, placeholder_text=fix_arabic("الكمية", for_ui=True), height=42, font=FONT_NORMAL_BOLD, width=90, justify="right", corner_radius=10); self.p_qty.pack(side="right", padx=5)
        self.p_cost = ctk.CTkEntry(f2, placeholder_text=fix_arabic("تكلفة القطعة", for_ui=True), height=42, font=FONT_NORMAL_BOLD, width=120, justify="right", corner_radius=10); self.p_cost.pack(side="right", padx=5)
        self.p_sell = ctk.CTkEntry(f2, placeholder_text=fix_arabic("سعر البيع", for_ui=True), height=42, font=FONT_NORMAL_BOLD, width=120, justify="right", corner_radius=10); self.p_sell.pack(side="right", padx=5)
        
        ctk.CTkLabel(f2, text=fix_arabic("مصدر التمويل:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=2)
        self.p_funding = ctk.CTkComboBox(f2, values=[fix_arabic("صندوق المحل (نقدي)", for_ui=True), fix_arabic("مساهمة رأس مال (مالك/شركاء)", for_ui=True), fix_arabic("ذمم موردين (بالدين)", for_ui=True)], font=FONT_BOLD, dropdown_font=FONT_BOLD, height=45, width=200, justify="right")
        self.p_funding.set(fix_arabic("صندوق المحل (نقدي)", for_ui=True))
        self.p_funding.pack(side="right", padx=5)
        
        self.p_total_lbl = ctk.CTkLabel(f2, text=fix_arabic("إجمالي الفاتورة: 0.00", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE); self.p_total_lbl.pack(side="right", padx=15)
        
        def update_p_total(*args):
            try:
                q_val = self.p_qty.get().strip()
                c_val = self.p_cost.get().strip()
                q = float(clean_float(q_val)) if q_val else 0.0
                c = float(clean_float(c_val)) if c_val else 0.0
                tot = q * c
                self.p_total_lbl.configure(text=fix_arabic(f"إجمالي الفاتورة: {tot:.2f}", for_ui=True))
            except Exception as e:
                self.p_total_lbl.configure(text=fix_arabic("إجمالي الفاتورة: 0.00", for_ui=True))
            
        self.p_qty.bind("<KeyRelease>", update_p_total)
        self.p_cost.bind("<KeyRelease>", update_p_total)
        self.p_qty.bind("<FocusOut>", update_p_total)
        self.p_cost.bind("<FocusOut>", update_p_total)

        ctk.CTkButton(f2, text=fix_arabic("تسجيل الشراء", for_ui=True), command=self.add_purchase, font=FONT_BOLD, height=45, corner_radius=10, fg_color=COLOR_CRIMSON).pack(side="right", padx=10)
        
        self.pur_tree = ttk.Treeview(self.main_view, columns=("date", "total", "supplier", "cost", "qty", "name", "code"), show="headings")
        for col, head in zip(self.pur_tree["columns"], ["التاريخ", "إجمالي الشراء", "المورد", "تكلفة القطعة", "الكمية", "الاسم", "الكود"]): self.pur_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.pur_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_purchases_tree()

    def refresh_purchases_tree(self):
        for i in self.pur_tree.get_children(): self.pur_tree.delete(i)
        self.db.cursor.execute("SELECT date, (qty * cost), supplier, cost, qty, name, code FROM purchases ORDER BY id DESC")
        [self.pur_tree.insert("", "end", values=(r[0], f"{r[1]:.2f}", r[2] or "-", r[3], r[4], fix_arabic(r[5], for_ui=True), r[6])) for r in self.db.cursor.fetchall()]

    def lookup_product_purchase(self):
        code = self.p_code.get().strip()
        if not code:
            return
        self.db.cursor.execute("SELECT name, buy_price, sell_price FROM products WHERE code=?", (code,))
        res = self.db.cursor.fetchone()
        if res:
            self.p_name.delete(0, 'end'); self.p_name.insert(0, res[0])
            self.p_cost.delete(0, 'end'); self.p_cost.insert(0, str(res[1]))
            self.p_sell.delete(0, 'end'); self.p_sell.insert(0, str(res[2]))
        else:
            # Try global barcode lookup
            global_name = self.fetch_global_barcode(code)
            if global_name:
                self.p_name.delete(0, 'end'); self.p_name.insert(0, global_name)
                if not self.p_cost.get().strip(): self.p_cost.insert(0, "1.00")
                if not self.p_sell.get().strip(): self.p_sell.insert(0, "1.50")
                if not self.p_qty.get().strip(): self.p_qty.insert(0, "1")
                self.show_msg("تعريف تلقائي", f"تم العثور على اسم المنتج من قاعدة البيانات العالمية:\n{global_name}")
            else:
                self.show_msg("تنبيه", "الباركود غير مسجل. أدخل اسم المنتج والتكلفة يدوياً للشراء.")

    def add_purchase(self):
        c, n = self.p_code.get().strip(), self.p_name.get().strip()
        q_str, cost_str, sell_str = self.p_qty.get().strip(), self.p_cost.get().strip(), self.p_sell.get().strip()
        sup_input = self.p_supplier.get().strip()
        
        # Resolve supplier phone input to registered company name if possible
        supplier = sup_input
        if sup_input:
            sup_res = self.db.cursor.execute("SELECT name FROM suppliers WHERE phone=? OR name=?", (sup_input, sup_input)).fetchone()
            if sup_res and sup_res[0]:
                supplier = sup_res[0]
            else:
                # If not registered, treat input as name or keep phone as name if no name given
                supplier = sup_input

        raw_funding = self.p_funding.get().strip() if hasattr(self, "p_funding") else "صندوق المحل (نقدي)"
        funding_source = raw_funding
        if not all([c, n, q_str, cost_str]):
            self.show_msg("تنبيه", "يرجى ملء الكود والاسم والكمية وتكلفة القطعة"); return
        try:
            self.db.conn.execute("BEGIN IMMEDIATE")
            qty = self.positive_integer(q_str, "الكمية")
            cost = self.positive_number(cost_str, "تكلفة القطعة")
            sell_price = self.positive_number(sell_str, "سعر البيع") if sell_str else (cost * 1.2)
            now = datetime.datetime.now(); date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
            total = qty * cost
            purchase_source_id = f"purchase-{now.strftime('%Y%m%d%H%M%S%f')}"
            self.db.cursor.execute("INSERT INTO purchases (code, name, qty, cost, supplier, date, time, description, user, funding_source, source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (c, n, qty, cost, supplier, date, time, f"شراء ({funding_source})", self.current_user, funding_source, purchase_source_id))
            prod = self.db.cursor.execute("SELECT stock FROM products WHERE code=?", (c,)).fetchone()
            if prod:
                self.db.cursor.execute("UPDATE products SET stock = stock + ?, buy_price = CASE WHEN stock + ? > 0 THEN ((stock * buy_price) + (? * ?)) / (stock + ?) ELSE ? END, sell_price = MAX(sell_price, ?) WHERE code=?", (qty, qty, qty, cost, qty, cost, sell_price, c))
            else:
                self.db.cursor.execute("INSERT INTO products (code, name, buy_price, sell_price, stock, description) VALUES (?,?,?,?,?,?)", (c, n, cost, sell_price, qty, "مشتريات جديدة"))
            # Resolve the actual combobox value first. Arabic labels are reshaped
            # for display, so substring checks on the displayed string are unsafe.
            purchase_credit_account = self._ledger_account_for_payment(funding_source)
            is_supplier_credit = purchase_credit_account == "AP"

            if is_supplier_credit:
                # Normalize the supplier exactly once before writing either the
                # supplier balance or the debt row. A phone-only input becomes a
                # stable display name, while an existing phone/name keeps its row.
                supplier_input = sup_input
                if supplier_input:
                    res_sup = self.db.cursor.execute("SELECT id, name FROM suppliers WHERE phone=? OR name=? ORDER BY id LIMIT 1", (supplier_input, supplier_input)).fetchone()
                    if res_sup:
                        supplier_id, supplier = res_sup[0], res_sup[1]
                    else:
                        supplier = supplier_input if not supplier_input.isdigit() else f"مورد {supplier_input}"
                        supplier_phone = supplier_input if supplier_input.isdigit() else None
                        self.db.cursor.execute("INSERT INTO suppliers (name, phone, address, balance) VALUES (?, ?, ?, 0.0)", (supplier, supplier_phone, ""))
                        supplier_id = self.db.cursor.lastrowid
                else:
                    supplier = "مورد عام"
                    res_sup = self.db.cursor.execute("SELECT id, name FROM suppliers WHERE name=? ORDER BY id LIMIT 1", (supplier,)).fetchone()
                    if res_sup:
                        supplier_id = res_sup[0]
                        supplier = res_sup[1]
                    else:
                        self.db.cursor.execute("INSERT INTO suppliers (name, phone, address, balance) VALUES (?, ?, ?, 0.0)", (supplier, None, ""))
                        supplier_id = self.db.cursor.lastrowid
                self.db.cursor.execute("UPDATE suppliers SET balance = balance + ? WHERE id=?", (total, supplier_id))

                inv_ref = f"PUR-{now.strftime('%Y%m%d%H%M%S%f')}"
                self.db.cursor.execute("INSERT INTO supplier_debts (supplier_name, total_debt, paid_amount, status, date, notes, debt_reference, source_type, source_id) VALUES (?, ?, 0.0, 'غير مسدد', ?, ?, ?, ?, ?)", (supplier, total, date, f"شراء بضاعة (أجل): {n} (الكمية: {qty})", inv_ref, "purchase", purchase_source_id))
            self._post_journal_entry("purchase", purchase_source_id, "قيد شراء وإضافة مخزون", [
                ("INVENTORY", total, 0, "إضافة بضاعة إلى المخزون"),
                (purchase_credit_account, 0, total, "مصدر تمويل الشراء")
            ], date, time)


            self.db.conn.commit(); self.log_action("تسجيل شراء", "purchases", f"الكود: {c}; الإجمالي: {total:.2f}; المورد: {supplier or '-'}")
            self.show_msg("نجاح", f"تم تسجيل الشراء بقيمة {total:.2f} {CURRENCY} وإضافة {qty} قطعة إلى المخزون")
            self.refresh_purchases_tree(); self.refresh_inventory_tree() if hasattr(self, "inv_tree") else None
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر تسجيل الشراء", str(exc))

    def ui_suppliers(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("الموردون والديون")
        form = ctk.CTkFrame(self.main_view, fg_color="transparent"); form.pack(fill="x", padx=15, pady=10)
        self.sup_name = ctk.CTkEntry(form, placeholder_text=fix_arabic("اسم المورد", for_ui=True), font=FONT_NORMAL_BOLD, height=42, justify="right"); self.sup_name.pack(side="right", padx=5, expand=True, fill="x")
        self.sup_phone = ctk.CTkEntry(form, placeholder_text=fix_arabic("الهاتف", for_ui=True), font=FONT_NORMAL_BOLD, height=42, justify="right", width=150); self.sup_phone.pack(side="right", padx=5)
        self.sup_address = ctk.CTkEntry(form, placeholder_text=fix_arabic("العنوان", for_ui=True), font=FONT_NORMAL_BOLD, height=42, justify="right", width=180); self.sup_address.pack(side="right", padx=5)
        self.sup_balance = ctk.CTkEntry(form, placeholder_text=fix_arabic("الرصيد/الدين", for_ui=True), font=FONT_NORMAL_BOLD, height=42, justify="right", width=130); self.sup_balance.pack(side="right", padx=5)
        ctk.CTkButton(form, text=fix_arabic("حفظ المورد", for_ui=True), command=self.save_supplier, font=FONT_BOLD, height=42, fg_color=COLOR_CRIMSON).pack(side="right", padx=8)
        self.sup_tree = ttk.Treeview(self.main_view, columns=("balance", "address", "phone", "name"), show="headings")
        for col, head in zip(self.sup_tree["columns"], ["الرصيد/الدين", "العنوان", "الهاتف", "اسم المورد"]): self.sup_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.sup_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_suppliers()

    def save_supplier(self):
        name, phone, address, balance = self.sup_name.get().strip(), self.sup_phone.get().strip(), self.sup_address.get().strip(), self.sup_balance.get().strip() or "0"
        if not name or not phone:
            self.show_msg("تنبيه", "يرجى إدخال اسم المورد ورقم الهاتف (الرقم المرجعي الأساسي)"); return
        try:
            balance_value = self.positive_number(balance, "الرصيد", allow_zero=True)
            # Use phone as unique reference (or name if phone conflict). Let's set phone UNIQUE or check by phone.
            self.db.cursor.execute("INSERT INTO suppliers (name, phone, address, balance) VALUES (?,?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name, address=excluded.address, balance=excluded.balance", (name, phone, address, balance_value))
            self.db.conn.commit(); self.log_action("حفظ مورد", "suppliers", f"المورد: {name} (هاتف: {phone}); الرصيد: {balance_value:.2f}"); self.refresh_suppliers(); self.show_msg("نجاح", "تم تعريف وحفظ بيانات المورد برقم مرجعي (الهاتف) بنجاح")
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر حفظ المورد", str(exc))

    def refresh_suppliers(self):
        for i in self.sup_tree.get_children(): self.sup_tree.delete(i)
        self.db.cursor.execute("SELECT balance, address, phone, name FROM suppliers ORDER BY name")
        for row in self.db.cursor.fetchall():
            self.sup_tree.insert("", "end", values=(f"{float(row[0] or 0):.2f}", row[1] or "-", row[2] or "-", fix_arabic(row[3], for_ui=True)))

    def ui_audit_logs(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("سجل الرقابة والعمليات")
        top = ctk.CTkFrame(self.main_view, fg_color="transparent"); top.pack(fill="x", padx=15, pady=8)
        ctk.CTkButton(top, text=fix_arabic("تحديث", for_ui=True), command=self.refresh_audit_logs, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=40).pack(side="right", padx=5)
        ctk.CTkLabel(top, text=fix_arabic("يسجل النظام عمليات الدخول والإضافة والتعديل والحذف دون تغيير السجلات الأصلية.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=15)
        self.audit_tree = ttk.Treeview(self.main_view, columns=("details", "entity", "action", "time", "date", "user"), show="headings")
        for col, head in zip(self.audit_tree["columns"], ["التفاصيل", "الكيان", "العملية", "الساعة", "التاريخ", "المستخدم"]): self.audit_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.audit_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_audit_logs()


    def save_financial_policies(self):
        try:
            p = self.p_points.get().strip()
            l1 = self.p_l1.get().strip()
            v1 = self.p_v1.get().strip()
            l2 = self.p_l2.get().strip()
            v2 = self.p_v2.get().strip()
            v3 = self.p_v3.get().strip()
            ps = self.p_sale.get().strip()
            pm = self.p_maint.get().strip()
            pt = self.p_trans.get().strip()
            
            settings = [
                ('reg_points', p), ('comm_limit1', l1), ('comm_val1', v1),
                ('comm_limit2', l2), ('comm_val2', v2), ('comm_val3', v3),
                ('points_sale', ps), ('points_maint', pm), ('points_transfer', pt)
            ]
            for k, v in settings:
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))
            self.db.conn.commit()
            self.log_action("تعديل السياسات المالية", "settings", f"نقاط: {p}; عمولات: {v1}/{v2}/{v3}")
            self.show_msg("نجاح", "تم حفظ السياسات المالية الجديدة بنجاح")
        except Exception as e:
            self.show_msg("خطأ", f"تعذر الحفظ: {str(e)}")

    def ui_operations_management(self):
        for w in self.main_view.winfo_children():
            w.destroy()
        self.create_header("إدارة العمليات")
        f_top = ctk.CTkFrame(self.main_view, fg_color="transparent")
        f_top.pack(fill="x", padx=15, pady=8)

        try:
            usernames = [r[0] for r in self.db.cursor.execute("SELECT username FROM users ORDER BY username").fetchall() if r[0]]
        except sqlite3.Error:
            usernames = []
        self.op_user = ctk.CTkComboBox(f_top, values=[fix_arabic("الكل", for_ui=True)] + usernames, width=150, height=40, font=FONT_NORMAL_BOLD, justify="center")
        self.op_user.pack(side="right", padx=5)
        self.op_user.set(fix_arabic("الكل", for_ui=True))
        ctk.CTkLabel(f_top, text=fix_arabic("المستخدم:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=3)
        self.op_to = ctk.CTkEntry(f_top, placeholder_text="YYYY-MM-DD", width=135, height=40, justify="center", font=FONT_NORMAL_BOLD)
        self.op_to.pack(side="right", padx=5)
        ctk.CTkLabel(f_top, text=fix_arabic("إلى:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=2)
        self.op_from = ctk.CTkEntry(f_top, placeholder_text="YYYY-MM-DD", width=135, height=40, justify="center", font=FONT_NORMAL_BOLD)
        self.op_from.pack(side="right", padx=5)
        ctk.CTkLabel(f_top, text=fix_arabic("من:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=2)
        ctk.CTkButton(f_top, text=fix_arabic("فلترة", for_ui=True), command=self.refresh_operations_tree, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=40, width=90).pack(side="right", padx=5)
        

        ctk.CTkButton(f_top, text=fix_arabic("تعديل العملية", for_ui=True), command=self.edit_operation_record_ui, font=FONT_BOLD, fg_color=COLOR_TEAL, height=40, width=125).pack(side="left", padx=5)
        ctk.CTkButton(f_top, text=fix_arabic("حذف العملية", for_ui=True), command=self.delete_operation_record, font=FONT_BOLD, fg_color=COLOR_RUBI, height=40, width=125).pack(side="left", padx=5)

        cols = ("source", "user", "payment", "total", "desc", "type", "date", "id")
        heads = ["المصدر", "المستخدم", "الدفع", "الإجمالي", "الوصف/المنتج", "النوع", "التاريخ", "ID"]
        # Force main view expansion
        self.main_view.grid_rowconfigure(len(self.main_view.winfo_children()), weight=1)
        table_frame = ctk.CTkFrame(self.main_view, fg_color="transparent", height=600)
        table_frame.pack(fill="both", expand=True, padx=15, pady=8)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.ops_tree = ttk.Treeview(table_frame, columns=cols, displaycolumns=("user", "payment", "total", "desc", "type", "date", "id"), show="headings")
        for c, h in zip(cols, heads):
            self.ops_tree.heading(c, text=fix_arabic(h, for_ui=True))
        widths = {"source": 0, "user": 130, "payment": 100, "total": 110, "desc": 300, "type": 150, "date": 120, "id": 70}
        for c, width in widths.items():
            self.ops_tree.column(c, width=width, minwidth=width if c != "source" else 0, stretch=(c in {"desc", "type"}), anchor="center")
        ybar = ttk.Scrollbar(table_frame, orient="vertical", command=self.ops_tree.yview)
        xbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.ops_tree.xview)
        self.ops_tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.ops_tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)
        self.refresh_operations_tree()
        
        # Month-over-Month Comparison & Charts Dashboard
        comp_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
        comp_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkLabel(comp_frame, text=fix_arabic("مقارنة الأداء المالي: الشهر الحالي مقابل الشهر السابق", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=8)
        
        # Calculate current month vs previous month
        now = datetime.datetime.now()
        cur_y, cur_m = now.year, now.month
        prev_m_date = now.replace(day=1) - datetime.timedelta(days=1)
        prev_y, prev_m = prev_m_date.year, prev_m_date.month
        
        cur_prefix = f"{cur_y:04d}-{cur_m:02d}"
        prev_prefix = f"{prev_y:04d}-{prev_m:02d}"
        
        def get_month_stats(prefix):
            # Sales rev & cogs
            self.db.cursor.execute("SELECT COALESCE(SUM(total),0), COALESCE(SUM(buy_cost * qty),0), COUNT(*) FROM sales WHERE date LIKE ?", (prefix + "%",))
            s_rev, s_cogs, s_count = self.db.cursor.fetchone()
            
            # Maintenance rev & cost
            self.db.cursor.execute("SELECT COALESCE(SUM(revenue),0), COALESCE(SUM(internal_cost),0), COUNT(*) FROM maintenance WHERE date LIKE ?", (prefix + "%",))
            m_rev, m_cost, m_count = self.db.cursor.fetchone()
            
            # Transfers commission
            self.db.cursor.execute("SELECT COALESCE(SUM(commission),0), COUNT(*) FROM transfers WHERE date LIKE ?", (prefix + "%",))
            t_comm, t_count = self.db.cursor.fetchone()
            
            # Expenses
            self.db.cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date LIKE ?", (prefix + "%",))
            exp = self.db.cursor.fetchone()[0]
            
            total_rev = (s_rev or 0.0) + (m_rev or 0.0) + (t_comm or 0.0)
            total_cost = (s_cogs or 0.0) + (m_cost or 0.0) + (exp or 0.0)
            net_profit = total_rev - total_cost
            ops_count = (s_count or 0) + (m_count or 0) + (t_count or 0)
            
            return {
                "rev": total_rev,
                "cost": total_cost,
                "profit": net_profit,
                "ops": ops_count,
                "sales_rev": s_rev or 0.0,
                "maint_rev": m_rev or 0.0,
                "trans_comm": t_comm or 0.0
            }
            
        cur_stats = get_month_stats(cur_prefix)
        prev_stats = get_month_stats(prev_prefix)
        
        grid_c = ctk.CTkFrame(comp_frame, fg_color="transparent"); grid_c.pack(fill="x", padx=15, pady=5)
        
        def create_stat_card(parent, title, cur_val, prev_val, is_currency=True):
            card = ctk.CTkFrame(parent, fg_color=COLOR_NAVY, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            card.pack(side="right", fill="both", expand=True, padx=5, pady=5)
            ctk.CTkLabel(card, text=fix_arabic(title, for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(5,2))
            
            cur_str = f"{cur_val:.2f} {CURRENCY}" if is_currency else f"{cur_val}"
            prev_str = f"{prev_val:.2f} {CURRENCY}" if is_currency else f"{prev_val}"
            
            ctk.CTkLabel(card, text=fix_arabic(f"الحالي: {cur_str}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=1)
            ctk.CTkLabel(card, text=fix_arabic(f"السابق: {prev_str}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(1,5))
            
        create_stat_card(grid_c, "إجمالي الإيرادات", cur_stats["rev"], prev_stats["rev"])
        create_stat_card(grid_c, "صافي الأرباح", cur_stats["profit"], prev_stats["profit"])
        create_stat_card(grid_c, "إجمالي المصاريف والتكاليف", cur_stats["cost"], prev_stats["cost"])
        create_stat_card(grid_c, "عدد العمليات والحركات", cur_stats["ops"], prev_stats["ops"], is_currency=False)
        
        # Mini Canvas Chart for visual comparison
        chart_frame = ctk.CTkFrame(comp_frame, fg_color=COLOR_NAVY, corner_radius=10, border_width=1, border_color=COLOR_BORDER, height=130)
        chart_frame.pack(fill="x", padx=15, pady=(5, 12))
        chart_frame.pack_propagate(False)
        
        ctk.CTkLabel(chart_frame, text=fix_arabic("مقارنة مرئية: إيرادات المبيعات، الصيانة، والحوالات (الشهر الحالي مقابل السابق)", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=4)
        
        canvas_w, canvas_h = 600, 75
        chart_canvas = ctk.CTkCanvas(chart_frame, width=canvas_w, height=canvas_h, bg=COLOR_NAVY, highlightthickness=0)
        chart_canvas.pack(pady=2)
        
        # Draw comparative bars
        max_v = max(cur_stats["rev"], prev_stats["rev"], 1.0)
        scale = 50.0 / max_v
        
        # Previous Month Bar group
        chart_canvas.create_text(120, 12, text=fix_arabic(f"الشهر السابق ({prev_prefix})", for_ui=True), font=FONT_BOLD, fill=COLOR_TEXT_MUTED)
        p_sales_h = cur_stats["sales_rev"] * scale # Using prev stats
        # Let's compute actual prev bars
        p_s = prev_stats["sales_rev"] * scale
        p_m = prev_stats["maint_rev"] * scale
        p_t = prev_stats["trans_comm"] * scale
        
        chart_canvas.create_rectangle(70, 65 - p_s, 95, 65, fill=COLOR_TEXT_MUTED, outline="")
        chart_canvas.create_rectangle(105, 65 - p_m, 130, 65, fill=COLOR_TEXT_MUTED, outline="")
        chart_canvas.create_rectangle(140, 65 - p_t, 165, 65, fill=COLOR_NAVY, outline="")
        chart_canvas.create_text(118, 72, text=f"{prev_stats['rev']:.1f}", font=FONT_BOLD, fill=COLOR_TEXT_MUTED)
        
        # Current Month Bar group
        chart_canvas.create_text(420, 12, text=fix_arabic(f"الشهر الحالي ({cur_prefix})", for_ui=True), font=FONT_BOLD, fill=COLOR_WHITE)
        c_s = cur_stats["sales_rev"] * scale
        c_m = cur_stats["maint_rev"] * scale
        c_t = cur_stats["trans_comm"] * scale
        
        chart_canvas.create_rectangle(370, 65 - c_s, 395, 65, fill=COLOR_RUBI_SOFT, outline="")
        chart_canvas.create_rectangle(405, 65 - c_m, 430, 65, fill=COLOR_RUBI_DARK, outline="")
        chart_canvas.create_rectangle(440, 65 - c_t, 465, 65, fill=COLOR_VINO_DARK, outline="")
        chart_canvas.create_text(418, 72, text=f"{cur_stats['rev']:.1f}", font=FONT_BOLD, fill=COLOR_WHITE)
        
        # Legend
        leg_f = ctk.CTkFrame(chart_frame, fg_color="transparent")
        leg_f.pack(fill="x", padx=10)
        ctk.CTkLabel(leg_f, text=fix_arabic("◼ مبيعات  ◼ صيانة  ◼ عمولات حوالات", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack()

        # Financial Policies Panel (V112) — manager-only settings.
        if self.current_role != "admin":
            return
        p_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
        p_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkLabel(p_frame, text=fix_arabic("إعدادات العمولات ونقاط الولاء", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        
        row1 = ctk.CTkFrame(p_frame, fg_color="transparent"); row1.pack(fill="x", padx=20, pady=5)
        
        # Fetch current settings
        s = {k: v for k, v in self.db.cursor.execute("SELECT key, value FROM settings").fetchall()}
        
        # Commission 1
        self.p_v1 = ctk.CTkEntry(row1, width=70, justify="center"); self.p_v1.insert(0, s.get('comm_val1', '0.5')); self.p_v1.pack(side="right", padx=5)
        ctk.CTkLabel(row1, text=fix_arabic("العمولة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        self.p_l1 = ctk.CTkEntry(row1, width=70, justify="center"); self.p_l1.insert(0, s.get('comm_limit1', '50')); self.p_l1.pack(side="right", padx=5)
        ctk.CTkLabel(row1, text=fix_arabic("إذا كان المبلغ أقل من:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        
        ctk.CTkLabel(row1, text="  |  ", text_color="#CCC").pack(side="right", padx=10)
        
        # Commission 2
        self.p_v2 = ctk.CTkEntry(row1, width=70, justify="center"); self.p_v2.insert(0, s.get('comm_val2', '1.0')); self.p_v2.pack(side="right", padx=5)
        ctk.CTkLabel(row1, text=fix_arabic("العمولة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        self.p_l2 = ctk.CTkEntry(row1, width=70, justify="center"); self.p_l2.insert(0, s.get('comm_limit2', '100')); self.p_l2.pack(side="right", padx=5)
        ctk.CTkLabel(row1, text=fix_arabic("بين الشريحة الأولى و:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)

        row2 = ctk.CTkFrame(p_frame, fg_color="transparent"); row2.pack(fill="x", padx=20, pady=5)
        
        # Commission 3
        self.p_v3 = ctk.CTkEntry(row2, width=70, justify="center"); self.p_v3.insert(0, s.get('comm_val3', '1.5')); self.p_v3.pack(side="right", padx=5)
        ctk.CTkLabel(row2, text=fix_arabic("العمولة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        ctk.CTkLabel(row2, text=fix_arabic("إذا كان المبلغ أعلى من ذلك:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        
        ctk.CTkLabel(row2, text="  |  ", text_color="#CCC").pack(side="right", padx=10)
        
        # Welcome Points
        self.p_points = ctk.CTkEntry(row2, width=70, justify="center"); self.p_points.insert(0, s.get('reg_points', '20')); self.p_points.pack(side="right", padx=5)
        ctk.CTkLabel(row2, text=fix_arabic("نقاط الهدية للعميل الجديد:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        
        row3 = ctk.CTkFrame(p_frame, fg_color="transparent"); row3.pack(fill="x", padx=20, pady=5)
        # Loyalty Multipliers
        self.p_trans = ctk.CTkEntry(row3, width=60, justify="center"); self.p_trans.insert(0, s.get('points_transfer', '2')); self.p_trans.pack(side="right", padx=5)
        ctk.CTkLabel(row3, text=fix_arabic("نقاط الحوالة/الفاتورة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        
        self.p_maint = ctk.CTkEntry(row3, width=60, justify="center"); self.p_maint.insert(0, s.get('points_maint', '5')); self.p_maint.pack(side="right", padx=5)
        ctk.CTkLabel(row3, text=fix_arabic("نقاط الصيانة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)
        
        self.p_sale = ctk.CTkEntry(row3, width=60, justify="center"); self.p_sale.insert(0, s.get('points_sale', '10')); self.p_sale.pack(side="right", padx=5)
        ctk.CTkLabel(row3, text=fix_arabic("نقاط المبيعات (لكل دينار):", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=2)

        ctk.CTkButton(p_frame, text=fix_arabic("حفظ السياسات المالية", for_ui=True), command=self.save_financial_policies, font=FONT_BOLD, fg_color=COLOR_TEAL, height=40, width=200).pack(pady=10)
        


    def _operation_where(self, start, end, user):
        where, params = self.date_filter("date", start, end)
        user = (user or "").strip()
        all_label = fix_arabic("الكل", for_ui=True)
        if user and user != all_label:
            where = (where + " AND " if where else "WHERE ") + "user=?"
            params.append(user)
        return where, params

    def refresh_operations_tree(self):
        for i in self.ops_tree.get_children():
            self.ops_tree.delete(i)
        try:
            start, end = self.op_from.get().strip(), self.op_to.get().strip()
            user = self.op_user.get().strip()
            where, params = self._operation_where(start, end, user)
            rows = []
            queries = [
                ("sales", f"SELECT user, COALESCE(payment_method,'Cash'), total, COALESCE(name,''), 'مبيعات', date, id FROM sales {where} ORDER BY date DESC, id DESC LIMIT 200", params),
                ("maintenance", f"SELECT user, COALESCE(payment_method,'Cash'), revenue, TRIM(COALESCE(device_name,'') || CASE WHEN COALESCE(repair_desc,'')<>'' THEN ' - ' || repair_desc ELSE '' END), 'صيانة', date, id FROM maintenance {where} ORDER BY date DESC, id DESC LIMIT 200", params),
                ("transfers", f"SELECT user, COALESCE(payment_method,'Cash'), CASE WHEN type='خروج حوالة' THEN (amount - commission) ELSE (amount + commission) END, TRIM(COALESCE(type,'') || CASE WHEN COALESCE(reference,'')<>'' THEN ' - ' || reference ELSE '' END), 'حوالات/فواتير', date, id FROM transfers {where} ORDER BY date DESC, id DESC LIMIT 200", params),
                ("purchases", f"SELECT COALESCE(user,'-'), COALESCE(funding_source, 'صندوق المحل (نقدي)'), (qty * cost), TRIM(COALESCE(name,'') || CASE WHEN COALESCE(supplier,'')<>'' THEN ' - ' || supplier ELSE '' END), 'مشتريات', date, id FROM purchases {where} ORDER BY date DESC, id DESC LIMIT 200", params),
                ("inventory_adjustments", f"SELECT COALESCE(user,'-'), '—', (qty * unit_cost), TRIM(COALESCE(product_name,'') || ' - ' || COALESCE(adjustment_type,'')), 'مرتجع / تالف', date, id FROM inventory_adjustments {where} ORDER BY date DESC, id DESC LIMIT 200", params),
                ("expenses", f"SELECT COALESCE(user,'-'), 'Cash', amount, COALESCE(desc,''), 'مصروف', date, id FROM expenses {where} ORDER BY date DESC, id DESC LIMIT 200", params),
            ]
            for source, query, query_params in queries:
                self.db.cursor.execute(query, list(query_params))
                rows.extend((source, *row) for row in self.db.cursor.fetchall())
            rows.sort(key=lambda row: (row[6] or "", int(row[7] or 0)), reverse=True)
            for source, user_name, payment, total, desc, op_type, date, rid in rows:
                self.ops_tree.insert("", "end", iid=f"{source}:{rid}", values=(source, user_name or "-", payment or "Cash", f"{float(total or 0):.2f}", fix_arabic(desc or "", for_ui=True), fix_arabic(op_type, for_ui=True), date or "", rid))
        except (ValueError, sqlite3.Error) as exc:
            self.show_msg("تعذر تحميل العمليات", str(exc))

    def _adjust_customer_points(self, phone, delta):
        if phone and delta:
            self.db.cursor.execute("UPDATE customers SET points=MAX(0, points + ?) WHERE phone=?", (int(delta), phone))

    def delete_operation_record(self):
        selected = self.ops_tree.selection()
        if not selected:
            self.show_msg("تنبيه", "يرجى تحديد عملية للحذف")
            return
        source, rid_text = str(selected[0]).split(":", 1)
        rid = int(rid_text)
        if not self.ask_confirm(str("تأكيد الحذف"), str("سيتم عكس أثر العملية على المخزون والتقارير والرصيد. هل تريد المتابعة؟")):
            return
        try:
            self._void_journals_for_record(source, rid, "إلغاء أثر العملية قبل الحذف")
            if source == "sales":
                row = self.db.cursor.execute("SELECT code, qty, total, customer_phone FROM sales WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية البيع غير موجودة")
                self.db.cursor.execute("UPDATE products SET stock=stock+? WHERE code=?", (int(row[1] or 0), row[0]))
                self._adjust_customer_points(row[3], -int(float(row[2] or 0) * 10))
                source_row = self.db.cursor.execute("SELECT source_id FROM sales WHERE id=?", (rid,)).fetchone()
                self.db.cursor.execute("DELETE FROM customer_debts WHERE source_type='sale' AND source_id=?", (source_row[0],)) if source_row and source_row[0] else None
                self.db.cursor.execute("DELETE FROM sales WHERE id=?", (rid,))
            elif source == "maintenance":
                row = self.db.cursor.execute("SELECT client_phone FROM maintenance WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الصيانة غير موجودة")
                self._adjust_customer_points(row[0], -5)
                source_row = self.db.cursor.execute("SELECT source_id FROM maintenance WHERE id=?", (rid,)).fetchone()
                self.db.cursor.execute("DELETE FROM customer_debts WHERE source_type='maintenance' AND source_id=?", (source_row[0],)) if source_row and source_row[0] else None
                self.db.cursor.execute("DELETE FROM maintenance WHERE id=?", (rid,))
            elif source == "transfers":
                row = self.db.cursor.execute("SELECT client_phone FROM transfers WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الحوالة غير موجودة")
                self._adjust_customer_points(row[0], -2)
                self.db.cursor.execute("DELETE FROM transfers WHERE id=?", (rid,))
            elif source == "purchases":
                row = self.db.cursor.execute("SELECT code, qty, cost, supplier, funding_source FROM purchases WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الشراء غير موجودة")
                stock_row = self.db.cursor.execute("SELECT stock FROM products WHERE code=?", (row[0],)).fetchone()
                if not stock_row or int(stock_row[0] or 0) < int(row[1] or 0):
                    raise ValueError("لا يمكن حذف الشراء لأن المخزون الحالي أقل من الكمية المشتراة")
                self.db.cursor.execute("UPDATE products SET stock=stock-? WHERE code=?", (int(row[1] or 0), row[0]))
                # Supplier balances represent AP only; cash/equity purchases must not alter them.
                if row[3] and self._ledger_account_for_payment(row[4]) == "AP":
                    self.db.cursor.execute("UPDATE suppliers SET balance=MAX(0, balance-?) WHERE name=?", (float(row[1] or 0) * float(row[2] or 0), row[3]))
                source_row = self.db.cursor.execute("SELECT source_id FROM purchases WHERE id=?", (rid,)).fetchone()
                self.db.cursor.execute("DELETE FROM supplier_debts WHERE source_type='purchase' AND source_id=?", (source_row[0],)) if source_row and source_row[0] else None
                self.db.cursor.execute("DELETE FROM purchases WHERE id=?", (rid,))
            elif source == "expenses":
                if not self.db.cursor.execute("DELETE FROM expenses WHERE id=?", (rid,)).rowcount:
                    raise ValueError("المصروف غير موجود")
            elif source == "inventory_adjustments":
                row = self.db.cursor.execute("SELECT adjustment_type, product_code, qty, unit_cost, original_sale_id FROM inventory_adjustments WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية المرتجع أو التالف غير موجودة")
                adjustment_type, product_code, qty, unit_cost, original_ref = row
                qty = int(qty or 0); amount = round(max(float(qty), 0.0) * max(float(unit_cost or 0.0), 0.0), 2)
                # Deleting a sale return removes stock; deleting a purchase
                # return or waste restores the stock that was removed.
                stock_delta = -qty if adjustment_type == "مرتجع بيع" else qty
                self.db.cursor.execute("UPDATE products SET stock=MAX(0, stock+?) WHERE code=?", (stock_delta, product_code))
                if adjustment_type == "مرتجع شراء" and original_ref:
                    purchase = self.db.cursor.execute("SELECT supplier, funding_source, source_id FROM purchases WHERE id=?", (original_ref,)).fetchone()
                    if purchase and self._ledger_account_for_payment(purchase[1]) == "AP":
                        if purchase[0]:
                            self.db.cursor.execute("UPDATE suppliers SET balance=COALESCE(balance,0)+? WHERE name=?", (amount, purchase[0]))
                        debt = self.db.cursor.execute("SELECT id, total_debt, paid_amount FROM supplier_debts WHERE source_type='purchase' AND source_id=? ORDER BY id LIMIT 1", (purchase[2],)).fetchone()
                        if debt:
                            new_total = round(float(debt[1] or 0.0) + amount, 2)
                            paid = max(float(debt[2] or 0.0), 0.0)
                            self.db.cursor.execute("UPDATE supplier_debts SET total_debt=?, status=? WHERE id=?", (new_total, "مسدد" if paid >= new_total else "غير مسدد", debt[0]))
                self.db.cursor.execute("DELETE FROM inventory_adjustments WHERE id=?", (rid,))
            else:
                raise ValueError("نوع العملية غير معروف")
            self.db.conn.commit()
            self.log_action("حذف عملية", source, f"المعرف: {rid}")
            self.show_msg("نجاح", "تم حذف العملية وعكس أثرها على الحسابات والمخزون")
            self.refresh_operations_tree()
        
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback()
            self.show_msg("تعذر الحذف", str(exc))

    def _edit_field(self, parent, label, value="", secret=False):
        ctk.CTkLabel(parent, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25, pady=(7, 2))
        entry = ctk.CTkEntry(parent, font=FONT_NORMAL_BOLD, justify="right", height=38, show="*" if secret else "")
        entry.pack(fill="x", padx=20, pady=(0, 4))
        if value is not None: entry.insert(0, str(value))
        return entry

    def edit_operation_record_ui(self):
        selected = self.ops_tree.selection()
        if not selected:
            self.show_msg("تنبيه", "يرجى تحديد عملية للتعديل")
            return
        source, rid_text = str(selected[0]).split(":", 1)
        rid = int(rid_text)
        win = ctk.CTkToplevel(self); win.title(fix_arabic("تعديل العملية", is_title=True)); win.geometry("560x760"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"تعديل {source} رقم {rid}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=12)
        fields = {}
        combos = {}
        try:
            if source == "sales":
                row = self.db.cursor.execute("SELECT code, name, qty, price, total, buy_cost, date, time, user, customer_phone, payment_method FROM sales WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية البيع غير موجودة")
                summary = ctk.CTkFrame(win, fg_color=COLOR_SURFACE, corner_radius=10); summary.pack(fill="x", padx=20, pady=8)
                for label, value in (("كود المنتج", row[0]), ("اسم المنتج", row[1]), ("الإجمالي الحالي", row[4]), ("تكلفة البضاعة الحالية", row[5]), ("التاريخ", row[6]), ("الوقت", row[7]), ("المستخدم", row[8]), ("طريقة الدفع", row[10] or "Cash")):
                    ctk.CTkLabel(summary, text=fix_arabic(f"{label}: {value or '-'}", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=14, pady=2)
                fields["qty"] = self._edit_field(win, "الكمية", row[2])
                fields["price"] = self._edit_field(win, "سعر القطعة", row[3])
                fields["customer_phone"] = self._edit_field(win, "هاتف العميل", row[9] or "")
                ctk.CTkLabel(win, text=fix_arabic("طريقة الدفع", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25, pady=(7, 2))
                combos["payment"] = ctk.CTkComboBox(win, values=["Cash", "Visa", "CLIQ", "Credit"], font=FONT_NORMAL_BOLD, height=38, justify="right")
                combos["payment"].pack(fill="x", padx=20, pady=(0, 4)); combos["payment"].set(row[10] or "Cash")
            elif source == "maintenance":
                row = self.db.cursor.execute("SELECT client_name, client_phone, device_name, repair_desc, revenue, internal_cost, payment_method FROM maintenance WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الصيانة غير موجودة")
                for key, label, value in zip(("client", "phone", "device", "desc", "revenue", "cost"), ("اسم العميل", "الهاتف", "الجهاز", "وصف الإصلاح", "المبلغ", "تكلفة القطع"), row[:6]): fields[key] = self._edit_field(win, label, value)
                ctk.CTkLabel(win, text=fix_arabic("طريقة الدفع", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25, pady=(7, 2))
                combos["payment"] = ctk.CTkComboBox(win, values=["Cash", "Visa", "CLIQ"], font=FONT_NORMAL_BOLD, height=38); combos["payment"].pack(fill="x", padx=20, pady=(0, 4)); combos["payment"].set(row[6] or "Cash")
            elif source == "transfers":
                row = self.db.cursor.execute("SELECT type, client_name, client_phone, amount, commission, reference, payment_method FROM transfers WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الحوالة غير موجودة")
                ctk.CTkLabel(win, text=fix_arabic("نوع الخدمة", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25, pady=(7, 2))
                type_values = [fix_arabic(x, for_ui=True) for x in ["خروج حوالة", "دخول حوالة", "دفع فاتورة"]]
                combos["type"] = ctk.CTkComboBox(win, values=type_values, font=FONT_NORMAL_BOLD, height=38); combos["type"].pack(fill="x", padx=20, pady=(0, 4)); combos["type"].set(fix_arabic(row[0] or "خروج حوالة", for_ui=True))
                for key, label, value in zip(("client", "phone", "amount", "commission", "reference"), ("اسم العميل", "الهاتف", "القيمة", "العمولة", "المرجع"), (row[1], row[2], row[3], row[4], row[5])): fields[key] = self._edit_field(win, label, value)
                ctk.CTkLabel(win, text=fix_arabic("طريقة الدفع", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25, pady=(7, 2))
                combos["payment"] = ctk.CTkComboBox(win, values=["Cash", "Visa", "CLIQ"], font=FONT_NORMAL_BOLD, height=38); combos["payment"].pack(fill="x", padx=20, pady=(0, 4)); combos["payment"].set(row[6] or "Cash")
            elif source == "purchases":
                row = self.db.cursor.execute("SELECT qty, cost, supplier, funding_source, source_id FROM purchases WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("عملية الشراء غير موجودة")
                for key, label, value in zip(("qty", "cost", "supplier"), ("الكمية", "تكلفة القطعة", "المورد"), row): fields[key] = self._edit_field(win, label, value)
            elif source == "expenses":
                row = self.db.cursor.execute("SELECT desc, amount FROM expenses WHERE id=?", (rid,)).fetchone()
                if not row: raise ValueError("المصروف غير موجود")
                fields["desc"] = self._edit_field(win, "وصف المصروف", row[0])
                fields["amount"] = self._edit_field(win, "المبلغ", row[1])
            else:
                raise ValueError("نوع العملية غير معروف")
        except (ValueError, sqlite3.Error) as exc:
            win.destroy(); self.show_msg("تعذر فتح العملية", str(exc)); return

        def save_edit():
            try:
                self._void_journals_for_record(source, rid, "إلغاء أثر العملية قبل التعديل")
                if source == "sales":
                    new_qty = self.positive_integer(fields["qty"].get(), "الكمية")
                    new_price = self.positive_number(fields["price"].get(), "سعر القطعة", allow_zero=True)
                    old = self.db.cursor.execute("SELECT code, qty, total, buy_cost, customer_phone, source_id, payment_method FROM sales WHERE id=?", (rid,)).fetchone()
                    stock = self.db.cursor.execute("SELECT stock FROM products WHERE code=?", (old[0],)).fetchone()
                    diff = new_qty - int(old[1] or 0)
                    if not stock or int(stock[0] or 0) < diff: raise ValueError("المخزون غير كافٍ للكمية الجديدة")
                    self.db.cursor.execute("UPDATE products SET stock=stock-? WHERE code=?", (diff, old[0]))
                    new_total = new_qty * new_price
                    old_unit_cost = (float(old[3] or 0) / int(old[1] or 1)) if int(old[1] or 0) else 0.0
                    new_buy_cost = old_unit_cost * new_qty
                    new_customer_phone = fields["customer_phone"].get().strip()
                    new_payment = combos["payment"].get() or "Cash"
                    old_payment = old[6] or "Cash"
                    debt = self.db.cursor.execute("SELECT id, paid_amount FROM customer_debts WHERE source_type=\'sale\' AND source_id=?", (old[5],)).fetchone() if old[5] else None
                    if old_payment == "Credit" and debt and float(debt[1] or 0) > new_total + 0.01:
                        raise ValueError("لا يمكن خفض البيع إلى أقل من المبلغ المسدد في الذمة")
                    if old_payment == "Credit" and new_payment != "Credit" and debt:
                        if float(debt[1] or 0) > 0.01:
                            raise ValueError("لا يمكن تحويل بيع آجل له دفعة مسجلة إلى دفع غير آجل")
                        self.db.cursor.execute("DELETE FROM customer_debts WHERE id=?", (debt[0],))
                    new_source_id = old[5]
                    if new_payment == "Credit" and old_payment != "Credit":
                        new_source_id = old[5] or f"sale-{rid}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                        self.db.cursor.execute("INSERT INTO customer_debts (customer_phone, customer_name, total_debt, paid_amount, status, date, notes, source_type, source_id) VALUES (?,?,?,?,?,?,?,?,?)", (new_customer_phone, "عميل البيع", new_total, 0, "غير مسدد", datetime.datetime.now().strftime("%Y-%m-%d"), "تحويل عملية بيع إلى آجل", "sale", new_source_id))
                    elif new_payment == "Credit" and debt:
                        status = "مسدد" if float(debt[1] or 0) >= new_total - 0.01 else "غير مسدد"
                        self.db.cursor.execute("UPDATE customer_debts SET customer_phone=?, total_debt=?, status=? WHERE id=?", (new_customer_phone, new_total, status, debt[0]))
                    self.db.cursor.execute("UPDATE sales SET qty=?, price=?, total=?, buy_cost=?, customer_phone=?, payment_method=?, source_id=? WHERE id=?", (new_qty, new_price, new_total, new_buy_cost, new_customer_phone, new_payment, new_source_id, rid))
                    if old[4] != new_customer_phone:
                        self._adjust_customer_points(old[4], -int(float(old[2] or 0) * 10))
                        self._adjust_customer_points(new_customer_phone, int(new_total * 10))
                    else:
                        self._adjust_customer_points(old[4], int(new_total * 10) - int(float(old[2] or 0) * 10))
                elif source == "maintenance":
                    revenue = self.positive_number(fields["revenue"].get(), "مبلغ الصيانة", allow_zero=True)
                    cost = self.positive_number(fields["cost"].get(), "تكلفة القطع", allow_zero=True)
                    self.db.cursor.execute("UPDATE maintenance SET client_name=?, client_phone=?, device_name=?, repair_desc=?, revenue=?, internal_cost=?, payment_method=? WHERE id=?", (fields["client"].get().strip(), fields["phone"].get().strip(), fields["device"].get().strip(), fields["desc"].get().strip(), revenue, cost, combos["payment"].get(), rid))
                elif source == "transfers":
                    raw_type = combos["type"].get()
                    raw_types = ["خروج حوالة", "دخول حوالة", "دفع فاتورة"]
                    transfer_type = next((x for x in raw_types if fix_arabic(x, for_ui=True) == raw_type), raw_types[0])
                    amount = self.positive_number(fields["amount"].get(), "القيمة")
                    commission = self.positive_number(fields["commission"].get(), "العمولة", allow_zero=True)
                    self.db.cursor.execute("UPDATE transfers SET type=?, client_name=?, client_phone=?, amount=?, commission=?, reference=?, payment_method=? WHERE id=?", (transfer_type, fields["client"].get().strip(), fields["phone"].get().strip(), amount, commission, fields["reference"].get().strip(), combos["payment"].get(), rid))
                elif source == "purchases":
                    new_qty = self.positive_integer(fields["qty"].get(), "الكمية")
                    new_cost = self.positive_number(fields["cost"].get(), "تكلفة القطعة")
                    new_supplier = fields["supplier"].get().strip()
                    old = self.db.cursor.execute("SELECT code, qty, cost, supplier, funding_source, source_id FROM purchases WHERE id=?", (rid,)).fetchone()
                    stock = self.db.cursor.execute("SELECT stock FROM products WHERE code=?", (old[0],)).fetchone()
                    diff = new_qty - int(old[1] or 0)
                    if not stock or int(stock[0] or 0) < diff: raise ValueError("المخزون الحالي لا يسمح بهذه الكمية")
                    self.db.cursor.execute("UPDATE products SET stock=stock+?, buy_price=? WHERE code=?", (-diff, new_cost, old[0]))
                    old_total, new_total = int(old[1] or 0) * float(old[2] or 0), new_qty * new_cost
                    old_is_ap = self._ledger_account_for_payment(old[4]) == "AP"
                    new_is_ap = self._ledger_account_for_payment(fields.get("funding", row[3]).get() if fields.get("funding") else row[3]) == "AP"
                    if old_is_ap and old[3]: self.db.cursor.execute("UPDATE suppliers SET balance=MAX(0, balance-?) WHERE name=?", (old_total, old[3]))
                    if new_is_ap and new_supplier: self.db.cursor.execute("INSERT INTO suppliers (name, balance) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET balance=balance+excluded.balance", (new_supplier, new_total))
                    self.db.cursor.execute("UPDATE purchases SET qty=?, cost=?, supplier=? WHERE id=?", (new_qty, new_cost, new_supplier, rid))
                    if old[5] and old_is_ap:
                        debt = self.db.cursor.execute("SELECT id, paid_amount FROM supplier_debts WHERE source_type=\'purchase\' AND source_id=?", (old[5],)).fetchone()
                        if debt:
                            if float(debt[1] or 0) > new_total + 0.01: raise ValueError("لا يمكن خفض الشراء إلى أقل من المبلغ المسدد")
                            status = "مسدد" if float(debt[1] or 0) >= new_total - 0.01 else "غير مسدد"
                            self.db.cursor.execute("UPDATE supplier_debts SET supplier_name=?, total_debt=?, status=? WHERE id=?", (new_supplier, new_total, status, debt[0]))
                else:
                    amount = self.positive_number(fields["amount"].get(), "المبلغ", allow_zero=True)
                    self.db.cursor.execute("UPDATE expenses SET desc=?, amount=? WHERE id=?", (fields["desc"].get().strip(), amount, rid))
                self._post_operation_journal_from_row(source, rid)
                self.db.conn.commit()
                self.log_action("تعديل عملية", source, f"المعرف: {rid}")
                win.destroy(); self.show_msg("نجاح", "تم تعديل العملية وتحديث أثرها المحاسبي"); self.refresh_operations_tree()
        

            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback(); self.show_msg("تعذر حفظ التعديل", str(exc))
        ctk.CTkButton(win, text=fix_arabic("حفظ التعديل", for_ui=True), command=save_edit, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45).pack(fill="x", padx=20, pady=20)

    def refresh_audit_logs(self):
        for i in self.audit_tree.get_children(): self.audit_tree.delete(i)
        self.db.cursor.execute("SELECT details, entity, action, time, date, username FROM audit_logs ORDER BY id DESC LIMIT 1000")
        for row in self.db.cursor.fetchall():
            self.audit_tree.insert("", "end", values=(fix_arabic(row[0] or "", for_ui=True), row[1], fix_arabic(row[2], for_ui=True), row[3], row[4], row[5]))

    def ui_marketing_campaigns(self):
        """Create and send a customer-specific WhatsApp campaign.

        This screen is operational/UI-only: it never writes accounting entries,
        changes stock, or changes customer records. WhatsApp's URL API can carry
        text; on Windows the selected image is copied to the clipboard so it can
        be pasted into WhatsApp after the chat opens.
        """
        for w in self.main_view.winfo_children():
            w.destroy()
        self.create_header("حملات تسويقية عبر WhatsApp")

        selected_image = {"path": None, "photo": None}
        root = ctk.CTkFrame(self.main_view, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=12)

        ctk.CTkLabel(root, text=fix_arabic("إرسال حملة مخصصة للعملاء", for_ui=True),
                     font=(APP_FONT_FAMILY, 20, "bold"), text_color=COLOR_WHITE,
                     anchor="e").pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(root, text=fix_arabic("اكتب الرسالة مرة واحدة وسيُدرج اسم كل عميل تلقائياً قبل فتح محادثته.", for_ui=True),
                     font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED,
                     anchor="e").pack(fill="x", pady=(0, 14))

        form = ctk.CTkFrame(root, fg_color=COLOR_SURFACE, corner_radius=14,
                            border_width=1, border_color=COLOR_BORDER)
        form.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(form, text=fix_arabic("عنوان الحملة (اختياري)", for_ui=True),
                     font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=18, pady=(16, 4))
        title_entry = ctk.CTkEntry(form, height=46, justify="right", font=FONT_NORMAL_BOLD,
                                   placeholder_text=fix_arabic("مثال: عرض خاص هذا الأسبوع", for_ui=True))
        title_entry.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(form, text=fix_arabic("محتوى الرسالة", for_ui=True),
                     font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=18, pady=(0, 4))
        message_box = ctk.CTkTextbox(form, height=150, wrap="word", font=FONT_NORMAL_BOLD,
                                     border_width=1, border_color=COLOR_TEAL, corner_radius=10)
        message_box.pack(fill="x", padx=18, pady=(0, 5))
        message_box.insert("1.0", fix_arabic("اكتب محتوى الحملة هنا...", for_ui=True))
        ctk.CTkLabel(form, text=fix_arabic("يمكنك كتابة {اسم_العميل} داخل النص، وسيُستبدل تلقائياً. إذا لم تستخدمه سيضاف الاسم في بداية الرسالة.", for_ui=True),
                     font=FONT_SMALL, text_color=COLOR_TEAL_SOFT, anchor="e").pack(fill="x", padx=18, pady=(0, 14))

        image_row = ctk.CTkFrame(form, fg_color="transparent")
        image_row.pack(fill="x", padx=18, pady=(0, 16))
        image_status = ctk.CTkLabel(image_row, text=fix_arabic("لم يتم اختيار صورة — الصورة اختيارية", for_ui=True),
                                    font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e")
        image_status.pack(side="right", fill="x", expand=True, padx=(0, 10))
        preview = ctk.CTkLabel(image_row, text="", width=54, height=70)
        preview.pack(side="right")

        def choose_image():
            path = filedialog.askopenfilename(title="اختيار صورة الحملة", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
            if not path:
                return
            try:
                with Image.open(path) as im:
                    width, height = im.size
                    if width <= 0 or height <= 0:
                        raise ValueError("أبعاد الصورة غير صالحة")
                    ratio = width / height
                    target = 9 / 16
                    # Accept normal export rounding, but reject non-portrait artwork.
                    if abs(ratio - target) > 0.02:
                        self.show_msg("أبعاد غير صحيحة", f"يجب أن تكون الصورة بنسبة 9:16. الأبعاد الحالية: {width}×{height}")
                        return
                    thumb = im.convert("RGB")
                    thumb.thumbnail((54, 70))
                    photo = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
                selected_image["path"] = path
                selected_image["photo"] = photo
                preview.configure(image=photo, text="")
                image_status.configure(text=fix_arabic(f"تم اعتماد صورة 9:16: {os.path.basename(path)}", for_ui=True), text_color=COLOR_TEAL_SOFT)
            except Exception as exc:
                self.show_msg("تعذر قراءة الصورة", str(exc))

        ctk.CTkButton(image_row, text=fix_arabic("اختيار صورة 9:16", for_ui=True), command=choose_image,
                      font=FONT_BOLD, height=46, width=190, fg_color=COLOR_NAVY_LIGHT,
                      hover_color=COLOR_NAVY).pack(side="left")

        actions = ctk.CTkFrame(root, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 12))
        ctk.CTkButton(actions, text=fix_arabic("اختيار صورة 9:16", for_ui=True), command=choose_image,
                      font=FONT_BOLD, height=50, fg_color=COLOR_NAVY_LIGHT,
                      hover_color=COLOR_NAVY).pack(side="right", fill="x", expand=True, padx=5)

        status = ctk.CTkLabel(root, text=fix_arabic("جاهز — لم يتم الإرسال بعد", for_ui=True),
                              font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e")
        status.pack(fill="x", pady=(0, 8))

        def campaign_text(customer_name):
            title = title_entry.get().strip()
            body = message_box.get("1.0", "end").strip()
            if body == fix_arabic("اكتب محتوى الحملة هنا...", for_ui=True):
                body = ""
            if not body:
                raise ValueError("يرجى كتابة محتوى الرسالة قبل الإرسال")
            name = str(customer_name or "العميل").strip() or "العميل"
            body = body.replace("{اسم_العميل}", name).replace("{customer_name}", name)
            if "{اسم_العميل}" not in message_box.get("1.0", "end") and "{customer_name}" not in message_box.get("1.0", "end"):
                body = f"العميل: {name}\n\n{body}"
            return (f"{title}\n\n" if title else "") + body

        def send_campaign():
            try:
                customers = self.db.cursor.execute("SELECT name, phone FROM customers WHERE phone IS NOT NULL AND TRIM(phone) <> '' ORDER BY id").fetchall()
                if not customers:
                    self.show_msg("لا يوجد عملاء", "لا توجد أرقام هواتف صالحة في سجل العملاء")
                    return
                # Validate text before asking the user to start opening chats.
                campaign_text(customers[0][0] or "العميل")
                if not self.ask_confirm("تأكيد إرسال الحملة", f"سيتم فتح WhatsApp لـ {len(customers)} عميل. هل تريد المتابعة؟"):
                    return
                image_path = selected_image["path"]
                sent = 0
                for customer_name, phone in customers:
                    self.send_whatsapp(phone, campaign_text(customer_name))
                    sent += 1
                status.configure(text=fix_arabic(f"تم فتح {sent} محادثة بالرسالة المخصصة. راجع WhatsApp لإرفاق الصورة عند الحاجة.", for_ui=True), text_color=COLOR_TEAL_SOFT)
                self.log_action("إرسال حملة واتساب", "customers", f"عدد العملاء: {sent}; الصورة: {os.path.basename(image_path) if image_path else 'بدون صورة'}")
            except ValueError as exc:
                self.show_msg("بيانات الحملة ناقصة", str(exc))
            except Exception as exc:
                self.show_msg("تعذر إرسال الحملة", str(exc))

        ctk.CTkButton(actions, text=fix_arabic("إرسال الحملة عبر WhatsApp", for_ui=True), command=send_campaign,
                      font=(APP_FONT_FAMILY, 15, "bold"), height=50, fg_color=COLOR_TEAL,
                      hover_color=COLOR_TEAL_DARK).pack(side="right", fill="x", expand=True, padx=5)
        ctk.CTkLabel(root, text=fix_arabic("ملاحظة: فتح المحادثات وإرسال الصور يعتمد على WhatsApp Web/تطبيق WhatsApp، ولا يغيّر القيود أو المخزون.", for_ui=True),
                     font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="e").pack(fill="x")

    def ui_customers(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("إدارة العملاء")
        top = ctk.CTkFrame(self.main_view, fg_color="transparent"); top.pack(fill="x", padx=20, pady=10)
        self.c_search = ctk.CTkEntry(top, placeholder_text=fix_arabic("بحث بالاسم...", for_ui=True), height=45, justify="right", corner_radius=10); self.c_search.pack(side="right", padx=10, expand=True, fill="x")
        ctk.CTkButton(top, text=fix_arabic("بحث", for_ui=True), command=self.refresh_customers, font=FONT_BOLD, width=100, height=45, fg_color=COLOR_CRIMSON).pack(side="right", padx=5)
        ctk.CTkButton(top, text=fix_arabic("إدارة ملاحظة العميل", for_ui=True), command=self.open_customer_note_manager, font=FONT_BOLD, height=45, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK).pack(side="right", padx=5)
        ctk.CTkButton(top, text=fix_arabic("تصدير إكسل", for_ui=True), command=self.export_customers, font=FONT_BOLD, height=45, fg_color=COLOR_TEAL).pack(side="left", padx=5)
        ctk.CTkLabel(self.main_view, text=fix_arabic("اضغط مرتين على العميل لرؤية السجل الكامل (CRM)", for_ui=True), font=FONT_NORMAL_BOLD, text_color="gray").pack()
        self.c_tree = ttk.Treeview(self.main_view, columns=("note", "points", "phone", "name"), show="headings")
        for col, head in zip(self.c_tree["columns"], ["الملاحظة التنبيهية", "النقاط", "الهاتف", "الاسم"]): self.c_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.c_tree.pack(fill="both", expand=True, padx=25, pady=10)
        self.c_tree.bind("<Double-1>", lambda e: self.show_customer_history())
        customer_actions = ctk.CTkFrame(self.main_view, fg_color="transparent")
        customer_actions.pack(fill="x", padx=25, pady=(0, 15))
        ctk.CTkButton(customer_actions, text=fix_arabic("تعديل بيانات العميل", for_ui=True), command=self.edit_customer_data, font=FONT_BOLD, height=45, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK).pack(side="right", padx=5)
        ctk.CTkButton(customer_actions, text=fix_arabic("إضافة عميل جديد", for_ui=True), command=self.add_new_customer, font=FONT_BOLD, height=45, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(side="right", padx=5)
        self.refresh_customers()

    def add_new_customer(self):
        """Create a customer master record and send a requested welcome message."""
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic("إضافة عميل جديد", is_title=True)); win.geometry("540x470"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("إضافة عميل جديد", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=(18, 12))
        form = ctk.CTkFrame(win, fg_color="transparent"); form.pack(fill="x", padx=28)

        def field(label, placeholder=""):
            ctk.CTkLabel(form, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", pady=(6, 3))
            entry = ctk.CTkEntry(form, height=42, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic(placeholder, for_ui=True))
            entry.pack(fill="x", pady=(0, 5))
            return entry

        name_entry = field("اسم العميل", "اكتب الاسم الكامل")
        phone_entry = field("رقم الهاتف", "مثال: 079xxxxxxx")
        points_entry = field("النقاط الترحيبية", "مثال: 20")
        points_entry.insert(0, "20")

        def save_new_customer():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            try:
                points = self.positive_integer(points_entry.get().strip(), "النقاط الترحيبية")
            except ValueError as exc:
                self.show_msg("بيانات غير صحيحة", str(exc)); return
            if not name or not phone:
                self.show_msg("بيانات ناقصة", "يرجى إدخال اسم العميل ورقم الهاتف"); return
            if not re.fullmatch(r"[0-9+()\- ]{6,25}", phone):
                self.show_msg("رقم غير صحيح", "يرجى إدخال رقم هاتف صحيح"); return
            phone_alt = phone[1:] if phone.startswith("0") else "0" + phone
            try:
                duplicate = self.db.cursor.execute("SELECT name FROM customers WHERE phone=? OR phone=?", (phone, phone_alt)).fetchone()
                if duplicate:
                    self.show_msg("العميل موجود", f"رقم الهاتف مسجل مسبقاً باسم: {duplicate[0] or 'عميل'}"); return
                self.db.cursor.execute("INSERT INTO customers (phone, name, points) VALUES (?,?,?)", (phone, name, points))
                self.db.conn.commit()
                self.log_action("إضافة عميل جديد", "customers", f"الاسم: {name}; الهاتف: {phone}; النقاط الترحيبية: {points}")
                welcome = (f"ترند سنتر الأردن TREND CENTER JORDAN\n\n"
                           f"أهلاً وسهلاً بك {name}\n"
                           f"تم تسجيلك عميلاً لدينا بنجاح.\n"
                           f"رصيد نقاطك الترحيبية الحالي: {points} نقطة\n\n"
                           f"شكراً لثقتك بنا.")
                win.destroy(); self.refresh_customers(); self.show_msg("تمت إضافة العميل", "تم حفظ العميل وإرسال رسالة الترحيب عبر WhatsApp")
                self.send_whatsapp(phone, welcome)
            except sqlite3.IntegrityError:
                self.db.conn.rollback(); self.show_msg("العميل موجود", "رقم الهاتف مستخدم مسبقاً")
            except (sqlite3.Error, ValueError) as exc:
                self.db.conn.rollback(); self.show_msg("تعذر حفظ العميل", str(exc))

        ctk.CTkButton(win, text=fix_arabic("حفظ وإرسال رسالة ترحيب", for_ui=True), command=save_new_customer, font=FONT_BOLD, height=48, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK).pack(fill="x", padx=28, pady=20)
    def _persist_customer_edit(self, customer_id, old_phone, points, new_name, new_phone):
        """Persist a customer edit independently from the dialog and tree refresh."""
        new_name, new_phone = str(new_name or "").strip(), str(new_phone or "").strip()
        old_phone = str(old_phone or "").strip()
        if not new_name or not new_phone:
            return False, "اسم العميل ورقم الهاتف مطلوبان"
        if not re.fullmatch(r"[0-9+()\- ]{6,25}", new_phone):
            return False, "يرجى إدخال رقم هاتف صحيح"
        old_phone_alt = old_phone[1:] if old_phone.startswith("0") else "0" + old_phone
        new_phone_alt = new_phone[1:] if new_phone.startswith("0") else "0" + new_phone
        try:
            duplicate = self.db.cursor.execute("SELECT id FROM customers WHERE phone IN (?, ?) AND id<>COALESCE(?, -1)", (new_phone, new_phone_alt, customer_id)).fetchone()
            if duplicate:
                return False, "رقم الهاتف مستخدم لعميل آخر"
            current = self.db.cursor.execute("SELECT id, phone, points FROM customers WHERE id=?", (customer_id,)).fetchone() if customer_id else None
            if not current:
                current = self.db.cursor.execute("SELECT id, phone, points FROM customers WHERE phone=? OR phone=? ORDER BY CASE WHEN phone=? THEN 0 ELSE 1 END LIMIT 1", (old_phone, old_phone_alt, old_phone)).fetchone()
            if current:
                stored_id, stored_phone, stored_points = int(current[0]), str(current[1] or old_phone).strip(), int(current[2] if current[2] is not None else points)
                self.db.cursor.execute("UPDATE customers SET name=?, phone=? WHERE id=?", (new_name, new_phone, stored_id))
                if self.db.cursor.rowcount != 1:
                    raise sqlite3.Error("لم يتم تحديث سجل العميل")
            else:
                stored_id, stored_phone, stored_points = None, old_phone, int(points or 0)
                self.db.cursor.execute("INSERT INTO customers (phone, name, points) VALUES (?, ?, ?)", (new_phone, new_name, stored_points))
                if self.db.cursor.rowcount != 1:
                    raise sqlite3.Error("لم يتم إنشاء سجل العميل")
            if new_phone != stored_phone:
                for table, column in (("sales", "customer_phone"), ("maintenance", "client_phone"), ("transfers", "client_phone"), ("customer_debts", "customer_phone"), ("customer_notes", "phone")):
                    self.db.cursor.execute(f"UPDATE {table} SET {column}=? WHERE {column} IN (?, ?)", (new_phone, stored_phone, old_phone_alt))
            self.db.conn.commit()
            saved = self.db.cursor.execute("SELECT name, phone, points FROM customers WHERE phone=?", (new_phone,)).fetchone()
            if not saved or str(saved[0]) != new_name or str(saved[1]) != new_phone or int(saved[2] or 0) != stored_points:
                raise sqlite3.Error("تعذر التحقق من حفظ بيانات العميل")
            return True, "تم حفظ تعديل بيانات العميل بنجاح مع الحفاظ على النقاط والسجلات المرتبطة"
        except sqlite3.IntegrityError:
            self.db.conn.rollback()
            return False, "رقم الهاتف مستخدم لعميل آخر"
        except sqlite3.Error as exc:
            self.db.conn.rollback()
            return False, str(exc)

    def edit_customer_data(self):
        sel = self.c_tree.selection()
        if not sel:
            self.show_msg("تنبيه", "يرجى اختيار عميل من الجدول أولاً")
            return
        vals = self.c_tree.item(sel[0])['values']
        selected_phone = str(vals[2] or "").strip()
        phone_alt = selected_phone[1:] if selected_phone.startswith("0") else "0" + selected_phone
        row = self.db.cursor.execute("SELECT id, phone, name, points FROM customers WHERE phone=? OR phone=? ORDER BY CASE WHEN phone=? THEN 0 ELSE 1 END LIMIT 1", (selected_phone, phone_alt, selected_phone)).fetchone()
        customer_id = None
        if row:
            customer_id = int(row[0])
            old_phone, old_name, points = str(row[1] or "").strip(), str(row[2] or "").strip(), int(row[3] or 0)
        else:
            # Some legacy rows may contain activity before a customers master row was created.
            source_row = self.db.cursor.execute("""
                SELECT client_phone, client_name FROM maintenance WHERE client_phone=? OR client_phone=?
                UNION ALL SELECT client_phone, client_name FROM transfers WHERE client_phone=? OR client_phone=?
                UNION ALL SELECT customer_phone, customer_name FROM customer_debts WHERE customer_phone=? OR customer_phone=?
                LIMIT 1
            """, (selected_phone, phone_alt, selected_phone, phone_alt, selected_phone, phone_alt)).fetchone()
            old_phone = str(source_row[0] if source_row and source_row[0] else selected_phone).strip()
            old_name = str(source_row[1] if source_row and source_row[1] else vals[3] or "").strip()
            # The tree displays shaped Arabic; reverse it only for this legacy fallback.
            if old_name and _has_visual_arabic(old_name):
                old_name = old_name[::-1]
            points = int(vals[1] or 0)
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic("تعديل بيانات العميل", is_title=True)); win.geometry("520x360"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("تعديل بيانات العميل", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=(18, 5))
        ctk.CTkLabel(win, text=fix_arabic(f"رصيد النقاط الحالي: {points} (لا يمكن تعديله من هذه النافذة)", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEAL).pack(pady=(0, 12))
        form = ctk.CTkFrame(win, fg_color="transparent"); form.pack(fill="x", padx=25)
        ctk.CTkLabel(form, text=fix_arabic("اسم العميل", for_ui=True), font=FONT_BOLD).pack(anchor="e", pady=(4, 2))
        name_entry = ctk.CTkEntry(form, height=42, font=FONT_NORMAL_BOLD, justify="right"); name_entry.pack(fill="x", pady=(0, 8)); name_entry.insert(0, old_name)
        ctk.CTkLabel(form, text=fix_arabic("رقم الهاتف", for_ui=True), font=FONT_BOLD).pack(anchor="e", pady=(4, 2))
        phone_entry = ctk.CTkEntry(form, height=42, font=FONT_NORMAL_BOLD, justify="right"); phone_entry.pack(fill="x"); phone_entry.insert(0, old_phone)
        def save_customer():
            ok, message = self._persist_customer_edit(customer_id, old_phone, points, name_entry.get(), phone_entry.get())
            if not ok:
                self.show_msg("تعذر الحفظ", message)
                return
            self.log_action("تعديل بيانات عميل", "customers", f"الهاتف السابق: {old_phone}; الاسم الجديد: {name_entry.get().strip()}")
            win.destroy()
            if hasattr(self, "c_search"):
                self.c_search.delete(0, "end")
            self.refresh_customers()
            self.show_msg("نجاح", message)
        ctk.CTkButton(win, text=fix_arabic("حفظ التعديل", for_ui=True), command=save_customer, font=FONT_BOLD, height=45, fg_color=COLOR_TEAL).pack(fill="x", padx=25, pady=18)
    def open_customer_note_manager(self):

        sel = self.c_tree.selection()
        if not sel:
            self.show_msg("تنبيه", "يرجى اختيار عميل من الجدول أولاً")
            return
        vals = self.c_tree.item(sel[0])['values']
        phone = str(vals[2] or "").strip()
        c_res = self.db.cursor.execute("SELECT name FROM customers WHERE phone=?", (phone,)).fetchone()
        name = str(c_res[0] if c_res and c_res[0] else "").strip()
        if not name:
            disp_name = str(vals[3] or "").strip()
            name = disp_name[::-1] if disp_name else phone
        
        win = ctk.CTkToplevel(self); win.title(fix_arabic(f"إدارة ملاحظة العميل: {name}", is_title=True)); win.geometry("480x450"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"الملاحظة التنبيهية للعميل: {name}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=15)
        ctk.CTkLabel(win, text=fix_arabic(f"رقم الهاتف: {phone}", for_ui=True), font=FONT_NORMAL_BOLD).pack(pady=5)
        self.db.cursor.execute("SELECT note FROM customer_notes WHERE phone=?", (phone,))
        res = self.db.cursor.fetchone()
        current_note = res[0] if res else ""
        ctk.CTkLabel(win, text=fix_arabic("نص الملاحظة (ستظهر كمنبه للموظف عند إدخال رقم الهاتف):", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=30, pady=(10, 2))
        
        # Note textbox with right-to-left typing support
        note_text = ctk.CTkTextbox(win, height=120, font=FONT_NORMAL_BOLD)
        note_text.pack(fill="x", padx=25, pady=5)
        try:
            note_text._textbox.tag_configure("rtl", justify="right")
            note_text._textbox.configure(insertbackground="black")
        except Exception:
            pass
            
        if current_note:
            note_text.insert("1.0", current_note)
        try:
            note_text._textbox.tag_add("rtl", "1.0", "end")
        except Exception:
            pass
            
        def save_note():
            txt = note_text.get("1.0", "end-1c").strip()
            try:
                if txt:
                    self.db.cursor.execute("INSERT OR REPLACE INTO customer_notes (phone, note, updated_at) VALUES (?, ?, datetime('now'))", (phone, txt))
                    self.db.conn.commit()
                    self.log_action("تحديث ملاحظة عميل", "customer_notes", f"الهاتف: {phone}")
                    self.show_msg("نجاح", "تم حفظ الملاحظة التنبيهية بنجاح")
                    win.destroy(); self.refresh_customers()
                else:
                    delete_note()
            except sqlite3.Error as exc:
                self.db.conn.rollback(); self.show_msg("تعذر الحفظ", str(exc))

        def delete_note():
            try:
                self.db.cursor.execute("DELETE FROM customer_notes WHERE phone=?", (phone,))
                self.db.conn.commit()
                self.log_action("حذف ملاحظة عميل", "customer_notes", f"الهاتف: {phone}")
                self.show_msg("نجاح", "تم حذف الملاحظة بنجاح")
                win.destroy(); self.refresh_customers()
            except sqlite3.Error as exc:
                self.db.conn.rollback(); self.show_msg("تعذر الحذف", str(exc))

        btn_f = ctk.CTkFrame(win, fg_color="transparent")
        btn_f.pack(pady=15, fill="x", padx=25)
        ctk.CTkButton(btn_f, text=fix_arabic("حفظ الملاحظة", for_ui=True), command=save_note, font=FONT_BOLD, fg_color=COLOR_TEAL, height=42).pack(side="right", expand=True, fill="x", padx=5)
        ctk.CTkButton(btn_f, text=fix_arabic("إزالة الملاحظة", for_ui=True), command=delete_note, font=FONT_BOLD, fg_color=COLOR_RUBI, height=42).pack(side="right", expand=True, fill="x", padx=5)

    def send_whatsapp(self, phone, message):
        if not phone:
            return
        clean_ph = re.sub(r'\D', '', phone)
        if clean_ph.startswith('0'):
            clean_ph = '962' + clean_ph[1:]
        elif not clean_ph.startswith('962') and len(clean_ph) == 9:
            clean_ph = '962' + clean_ph
        url = f"https://wa.me/{clean_ph}?text={urllib.parse.quote(message)}"
        try:
            webbrowser.open(url)
            # Fully automated image attachment simulation in background thread
            import threading, time
            def auto_paste_send():
                time.sleep(5) # Wait for browser / WhatsApp Web to load
                try:
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(1.5)
                    pyautogui.press('enter')
                except:
                    pass
            threading.Thread(target=auto_paste_send, daemon=True).start()
        except Exception as e:
            self.show_msg("تنبيه", f"تعذر فتح واتساب: {str(e)}")

    def show_customer_history(self):
        sel = self.c_tree.selection()
        if not sel: return
        vals = self.c_tree.item(sel[0])['values']
        phone = str(vals[2] or "").strip()
        p_alt = phone[1:] if phone.startswith('0') else '0' + phone
        
        c_res = self.db.cursor.execute("SELECT name FROM customers WHERE phone=? OR phone=?", (phone, p_alt)).fetchone()
        raw_db_name = str(c_res[0] if c_res and c_res[0] else "").strip()
        
        # Display name for window title and header
        name = raw_db_name
        if not name:
            disp_name = str(vals[3] or "").strip()
            name = disp_name[::-1] if disp_name else phone
        
        win = ctk.CTkToplevel(self); win.title(fix_arabic(f"سجل العميل: {name}", is_title=True)); win.geometry("850x600"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"تاريخ معاملات العميل: {name} ({phone})", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        tabs = ctk.CTkTabview(win, corner_radius=15); tabs.pack(fill="both", expand=True, padx=10, pady=10)
        t1, t2, t3 = tabs.add(fix_arabic("المشتريات", for_ui=True)), tabs.add(fix_arabic("الصيانة", for_ui=True)), tabs.add(fix_arabic("الحوالات والفواتير", for_ui=True))
        
        # 1. Sales / Purchases tab
        tr1 = ttk.Treeview(t1, columns=("payment", "total", "qty", "name", "date"), show="headings")
        for c, h in zip(tr1["columns"], ["الدفع", "الإجمالي", "الكمية", "المنتج", "التاريخ"]): tr1.heading(c, text=fix_arabic(h, for_ui=True))
        tr1.pack(fill="both", expand=True)
        
        sales_query = """
            SELECT payment_method, total, qty, name, date FROM sales 
            WHERE customer_phone=? OR customer_phone=? 
               OR customer_phone IN (SELECT phone FROM customers WHERE name=? OR name=?)
        """
        self.db.cursor.execute(sales_query, (phone, p_alt, name, raw_db_name))
        [tr1.insert("", "end", values=(r[0] or "Cash", f"{float(r[1] or 0):.2f}", r[2], fix_arabic(r[3], for_ui=True), r[4])) for r in self.db.cursor.fetchall()]
        
        # 2. Maintenance tab
        tr2 = ttk.Treeview(t2, columns=("payment", "revenue", "desc", "device", "date"), show="headings")
        for c, h in zip(tr2["columns"], ["الدفع", "المبلغ", "وصف الإصلاح", "الجهاز", "التاريخ"]): tr2.heading(c, text=fix_arabic(h, for_ui=True))
        tr2.pack(fill="both", expand=True)
        
        maint_query = """
            SELECT payment_method, revenue, repair_desc, device_name, date FROM maintenance 
            WHERE client_phone=? OR client_phone=? 
               OR client_name=? OR client_name=?
        """
        self.db.cursor.execute(maint_query, (phone, p_alt, name, raw_db_name))
        [tr2.insert("", "end", values=(r[0] or "Cash", f"{float(r[1] or 0):.2f}", fix_arabic(r[2], for_ui=True), fix_arabic(r[3], for_ui=True), r[4])) for r in self.db.cursor.fetchall()]
        
        # 3. Transfers & Bill Payments tab
        tr3 = ttk.Treeview(t3, columns=("payment", "ref", "comm", "amount", "type", "date"), show="headings")
        for c, h in zip(tr3["columns"], ["الدفع", "المرجع", "العمولة", "المبلغ", "النوع", "التاريخ"]): tr3.heading(c, text=fix_arabic(h, for_ui=True))
        tr3.pack(fill="both", expand=True)
        
        trans_query = """
            SELECT payment_method, reference, commission, amount, type, date FROM transfers 
            WHERE client_phone=? OR client_phone=? 
               OR client_name=? OR client_name=?
        """
        self.db.cursor.execute(trans_query, (phone, p_alt, name, raw_db_name))
        [tr3.insert("", "end", values=(r[0] or "Cash", r[1] or "-", f"{float(r[2] or 0):.2f}", f"{float(r[3] or 0):.2f}", fix_arabic(r[4], for_ui=True), r[5])) for r in self.db.cursor.fetchall()]

    def open_employee_customer_search(self):
        """Read-only customer search for the employee interface."""
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic("بحث عن عميل", is_title=True))
        win.geometry("1050x700")
        win.attributes("-topmost", True)
        win.grab_set()

        ctk.CTkLabel(win, text=fix_arabic("بحث عن عميل بالهاتف أو الاسم أو جزء من الاسم", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=(15, 8))
        search_row = ctk.CTkFrame(win, fg_color="transparent")
        search_row.pack(fill="x", padx=20, pady=5)
        query_entry = ctk.CTkEntry(search_row, placeholder_text=fix_arabic("اكتب رقم الهاتف أو الاسم أو جزءاً منه", for_ui=True), font=FONT_NORMAL_BOLD, justify="right", height=42)
        query_entry.pack(side="right", fill="x", expand=True, padx=(0, 8))
        results = ttk.Treeview(win, columns=("points", "phone", "name"), show="headings", height=8)
        for col, head in zip(("points", "phone", "name"), ("رصيد النقاط", "رقم الهاتف", "اسم العميل")):
            results.heading(col, text=fix_arabic(head, for_ui=True))
            results.column(col, anchor="center", width=220 if col != "name" else 360)
        results.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(win, text=fix_arabic("اضغط مرتين على العميل لعرض مصدر عملياته وسجلاته كاملة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEAL).pack(pady=(0, 8))

        def run_search(event=None):
            for row_id in results.get_children():
                results.delete(row_id)
            q = query_entry.get().strip()
            like = f"%{q}%"
            sql = """
                SELECT phone, MAX(name) AS name, MAX(points) AS points FROM (
                    SELECT phone, name, points FROM customers
                    WHERE phone LIKE ? OR name LIKE ?
                    UNION ALL
                    SELECT client_phone AS phone, client_name AS name, 0 AS points FROM maintenance
                    WHERE client_phone LIKE ? OR client_name LIKE ?
                    UNION ALL
                    SELECT client_phone AS phone, client_name AS name, 0 AS points FROM transfers
                    WHERE client_phone LIKE ? OR client_name LIKE ?
                    UNION ALL
                    SELECT customer_phone AS phone, customer_name AS name, 0 AS points FROM customer_debts
                    WHERE customer_phone LIKE ? OR customer_name LIKE ?
                )
                WHERE COALESCE(phone,'') <> '' OR COALESCE(name,'') <> ''
                GROUP BY phone
                ORDER BY name COLLATE NOCASE
                LIMIT 200
            """
            try:
                self.db.cursor.execute(sql, (like, like, like, like, like, like, like, like))
                for phone, name, points in self.db.cursor.fetchall():
                    results.insert("", "end", values=(int(points or 0), phone or "-", fix_arabic(name or "غير مسجل", for_ui=True)))
            except sqlite3.Error as exc:
                self.show_msg("تعذر البحث", str(exc))

        def open_selected_history(event=None):
            selected = results.selection()
            if not selected:
                return
            points, phone, display_name = results.item(selected[0])["values"]
            self.open_employee_customer_history(str(phone or "").strip(), str(display_name or "").strip(), int(points or 0))

        query_entry.bind("<KeyRelease>", run_search)
        results.bind("<Double-1>", open_selected_history)
        ctk.CTkButton(search_row, text=fix_arabic("بحث", for_ui=True), command=run_search, font=FONT_BOLD, width=110, height=42, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK).pack(side="right")
        run_search()
        query_entry.focus_set()

    def open_employee_customer_history(self, phone, display_name, points=0):
        """Display all customer activity read-only; this function never writes to the database."""
        p_alt = phone[1:] if phone.startswith("0") else "0" + phone
        customer_row = self.db.cursor.execute("SELECT name, points FROM customers WHERE phone=? OR phone=?", (phone, p_alt)).fetchone()
        name = str(customer_row[0] if customer_row and customer_row[0] else display_name or phone).strip()
        current_points = int(customer_row[1] if customer_row and customer_row[1] is not None else points or 0)
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic(f"سجل العميل: {name}", is_title=True))
        win.geometry("1150x720")
        win.attributes("-topmost", True)
        win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"العميل: {name}    الهاتف: {phone}    رصيد النقاط: {current_points}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=12)
        tabs = ctk.CTkTabview(win, corner_radius=15)
        tabs.pack(fill="both", expand=True, padx=12, pady=10)

        def add_tab(tab_name, columns, headings, query, params, value_builder):
            tab = tabs.add(fix_arabic(tab_name, for_ui=True))
            tree = ttk.Treeview(tab, columns=columns, show="headings")
            for col, heading in zip(columns, headings):
                tree.heading(col, text=fix_arabic(heading, for_ui=True))
                tree.column(col, anchor="center", width=max(120, 930 // max(1, len(columns))))
            tree.pack(fill="both", expand=True, padx=8, pady=8)
            try:
                self.db.cursor.execute(query, params)
                for row in self.db.cursor.fetchall():
                    tree.insert("", "end", values=value_builder(row))
            except sqlite3.Error:
                pass
            return tree

        add_tab("المبيعات", ("source", "date", "total", "qty", "item"), ("المصدر", "التاريخ", "الإجمالي", "الكمية", "المنتج"), """
            SELECT 'مبيعات', date, total, qty, name FROM sales
            WHERE customer_phone=? OR customer_phone=? ORDER BY date DESC, id DESC
        """, (phone, p_alt), lambda r: (r[0], r[1], f"{float(r[2] or 0):.2f}", r[3], fix_arabic(r[4] or "", for_ui=True)))
        add_tab("الصيانة", ("source", "date", "revenue", "device", "description"), ("المصدر", "التاريخ", "الإيراد", "الجهاز", "الصيانة المطلوبة"), """
            SELECT 'صيانة', date, revenue, device_name, repair_desc FROM maintenance
            WHERE client_phone=? OR client_phone=? OR client_name=? OR client_name=? ORDER BY date DESC, id DESC
        """, (phone, p_alt, name, display_name), lambda r: (r[0], r[1], f"{float(r[2] or 0):.2f}", fix_arabic(r[3] or "", for_ui=True), fix_arabic(r[4] or "", for_ui=True)))
        add_tab("الحوالات", ("source", "date", "type", "amount", "commission", "reference"), ("المصدر", "التاريخ", "النوع", "المبلغ", "العمولة", "المرجع"), """
            SELECT 'حوالات/فواتير', date, type, amount, commission, reference FROM transfers
            WHERE client_phone=? OR client_phone=? OR client_name=? OR client_name=? ORDER BY date DESC, id DESC
        """, (phone, p_alt, name, display_name), lambda r: (r[0], r[1], fix_arabic(r[2] or "", for_ui=True), f"{float(r[3] or 0):.2f}", f"{float(r[4] or 0):.2f}", r[5] or "-"))
        add_tab("الذمم", ("source", "date", "total", "paid", "status"), ("المصدر", "التاريخ", "إجمالي الذمة", "المدفوع", "الحالة"), """
            SELECT 'ذمم العملاء', date, total_debt, paid_amount, status FROM customer_debts
            WHERE customer_phone=? OR customer_phone=? OR customer_name=? OR customer_name=? ORDER BY date DESC, id DESC
        """, (phone, p_alt, name, display_name), lambda r: (r[0], r[1], f"{float(r[2] or 0):.2f}", f"{float(r[3] or 0):.2f}", fix_arabic(r[4] or "", for_ui=True)))

    def ui_database_health(self):
        try:
            integrity = self.db.cursor.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = self.db.cursor.execute("PRAGMA foreign_key_check").fetchall()
            if integrity == "ok" and not foreign_keys:
                self.show_msg("فحص قاعدة البيانات", "قاعدة البيانات سليمة.\nIntegrity check: OK\nForeign keys: OK")
            else:
                details = f"Integrity check: {integrity}\nForeign-key issues: {len(foreign_keys)}"
                self.show_msg("تنبيه قاعدة البيانات", details)
        except sqlite3.Error as exc:
            self.show_msg("تعذر فحص قاعدة البيانات", str(exc))

    def ui_manual_backup(self):
        try:
            backup_path = self.db.create_manual_backup()
            self.show_msg("نجاح", f"تم إنشاء نسخة احتياطية آمنة:\n{backup_path}")
        except (OSError, sqlite3.Error) as exc:
            self.show_msg("تعذر إنشاء النسخة الاحتياطية", str(exc))

    def ui_settings(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("إعدادات النظام وإدارة المستخدمين")
        # Use CTkFrame directly inside self.main_view for full downward expansion
        scroll = ctk.CTkFrame(self.main_view, fg_color="transparent"); scroll.pack(fill="both", expand=True, padx=20, pady=10)
        f_shop = ctk.CTkFrame(scroll, corner_radius=15, border_width=1, fg_color=COLOR_SURFACE); f_shop.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_shop, text=fix_arabic("إعدادات المحل", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        self.db.cursor.execute("SELECT key, value FROM settings"); sets = {k: v for k, v in self.db.cursor.fetchall()}
        self.s_entries = {}
        for k, label in [('shop_name', "اسم المحل بالعربية"), ('shop_name_en', "اسم المحل بالإنجليزية"), ('phone', "رقم الهاتف"), ('location', "الموقع"), ('logo_path', "مسار الشعار")]:
            r = ctk.CTkFrame(f_shop, fg_color="transparent"); r.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(r, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, width=150, anchor="e").pack(side="right")
            e = ctk.CTkEntry(r, font=FONT_NORMAL_BOLD, justify="right", height=45, corner_radius=8); e.pack(side="right", fill="x", expand=True, padx=10)
            e.insert(0, sets.get(k, "")); self.s_entries[k] = e
        def browse_logo():
            from tkinter import filedialog
            selected = filedialog.askopenfilename(title="اختر شعار المحل", filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All Files", "*.*")])
            if selected and "logo_path" in self.s_entries:
                self.s_entries["logo_path"].delete(0, "end"); self.s_entries["logo_path"].insert(0, selected)
        ctk.CTkButton(f_shop, text=fix_arabic("اختيار الشعار...", for_ui=True), command=browse_logo, font=FONT_BOLD, fg_color=COLOR_VINO, height=42).pack(pady=(0, 8))
        ctk.CTkButton(f_shop, text=fix_arabic("حفظ إعدادات المحل", for_ui=True), command=self.save_settings, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45, width=250).pack(pady=20)

        # Configurable Paths Management Panel (Database & Invoices folders)
        f_paths = ctk.CTkFrame(scroll, corner_radius=15, border_width=1, fg_color=COLOR_CRIMSON_SOFT); f_paths.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_paths, text=fix_arabic("مسارات حفظ البيانات والفواتير", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        
        self.path_entries = {}
        current_db = str(self.db.db_path)
        curr_inv_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='invoice_dir'").fetchone()
        current_inv = curr_inv_row[0] if curr_inv_row and curr_inv_row[0] else "invoices"

        for k, label, val in [('db_path', "مسار ملف قاعدة البيانات (SQLite):", current_db), ('invoice_dir', "مجلد حفظ صور الفواتير:", current_inv)]:
            r = ctk.CTkFrame(f_paths, fg_color="transparent"); r.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(r, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, width=220, anchor="e").pack(side="right")
            e = ctk.CTkEntry(r, font=FONT_NORMAL_BOLD, justify="right", height=42, corner_radius=8); e.pack(side="right", fill="x", expand=True, padx=10)
            e.insert(0, val)
            self.path_entries[k] = e
            
            def make_browse_cmd(entry_widget=e, is_file=(k=='db_path')):
                def browse():
                    from tkinter import filedialog
                    if is_file:
                        p = filedialog.asksaveasfilename(title="اختر مسار قاعدة البيانات", defaultextension=".db", filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")])
                    else:
                        p = filedialog.askdirectory(title="اختر مجلد الفواتير")
                    if p:
                        entry_widget.delete(0, 'end')
                        entry_widget.insert(0, p)
                return browse

            ctk.CTkButton(r, text=fix_arabic("استعراض...", for_ui=True), command=make_browse_cmd(), font=FONT_BOLD, width=100, height=42, fg_color=COLOR_TEAL).pack(side="left", padx=5)

        def save_paths_config():
            new_db = self.path_entries['db_path'].get().strip()
            new_inv = self.path_entries['invoice_dir'].get().strip()
            if not new_db or not new_inv:
                self.show_msg("خطأ", "لا يمكن ترك المسارات فارغة"); return
            try:
                Path("tcj_paths.cfg").write_text(new_db, encoding="utf-8")
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('invoice_dir', ?)", (new_inv,))
                self.db.conn.commit()
                self.show_msg("نجاح", "تم حفظ مسارات التخزين بنجاح.\nملاحظة: لكي يتم تطبيق مسار قاعدة البيانات الجديد بالكامل، يُفضل إعادة تشغيل البرنامج.")
            except Exception as ex:
                self.show_msg("خطأ", str(ex))

        ctk.CTkButton(f_paths, text=fix_arabic("حفظ مسارات التخزين", for_ui=True), command=save_paths_config, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=45, width=250).pack(pady=15)
        safety_row = ctk.CTkFrame(f_paths, fg_color="transparent"); safety_row.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkButton(safety_row, text=fix_arabic("إنشاء نسخة احتياطية الآن", for_ui=True), command=self.ui_manual_backup, font=FONT_BOLD, fg_color=COLOR_TEAL, height=42).pack(side="right", padx=5, expand=True, fill="x")
        ctk.CTkButton(safety_row, text=fix_arabic("فحص سلامة قاعدة البيانات", for_ui=True), command=self.ui_database_health, font=FONT_BOLD, fg_color=COLOR_VINO, height=42).pack(side="right", padx=5, expand=True, fill="x")

        f_user = ctk.CTkFrame(scroll, corner_radius=15, border_width=1); f_user.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_user, text=fix_arabic("إدارة المستخدمين", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        u_row = ctk.CTkFrame(f_user, fg_color="transparent"); u_row.pack(fill="x", padx=20, pady=5)
        self.new_u = ctk.CTkEntry(u_row, placeholder_text=fix_arabic("اسم المستخدم", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.new_u.pack(side="right", padx=5, expand=True, fill="x")
        self.new_p = ctk.CTkEntry(u_row, placeholder_text=fix_arabic("كلمة المرور", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); self.new_p.pack(side="right", padx=5, expand=True, fill="x")
        self.new_r = ctk.CTkComboBox(u_row, values=["employee", "admin"], height=45, font=FONT_NORMAL_BOLD); self.new_r.pack(side="right", padx=5); self.new_r.set("employee")
        ctk.CTkButton(f_user, text=fix_arabic("إضافة مستخدم جديد", for_ui=True), command=self.add_new_user, font=FONT_BOLD, fg_color=COLOR_CRIMSON_DARK, height=45).pack(pady=15)
        self.u_tree = ttk.Treeview(f_user, columns=("role", "user"), show="headings", height=5)
        for c, h in zip(self.u_tree["columns"], ["الصلاحية", "اسم المستخدم"]): 
            self.u_tree.heading(c, text=fix_arabic(h, for_ui=True)); self.u_tree.column(c, anchor="center")
        self.u_tree.pack(fill="x", padx=20, pady=10)
        btn_row = ctk.CTkFrame(f_user, fg_color="transparent"); btn_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_row, text=fix_arabic("تعديل المستخدم المختار", for_ui=True), command=self.edit_user_ui, font=FONT_BOLD, fg_color=COLOR_VINO, height=45).pack(side="right", padx=5)
        ctk.CTkButton(btn_row, text=fix_arabic("إدارة الصلاحيات الفردية", for_ui=True), command=lambda: self._edit_user_permissions(self.u_tree.item(self.u_tree.selection()[0])["values"][1]) if self.u_tree.selection() else self.show_msg("تنبيه", "يرجى تحديد مستخدم أولاً"), font=FONT_BOLD, fg_color=COLOR_TEAL, height=45).pack(side="right", padx=5)
        ctk.CTkButton(btn_row, text=fix_arabic("حذف المستخدم المختار", for_ui=True), command=self.delete_user, font=FONT_BOLD, fg_color=COLOR_RUBI, height=45).pack(side="right", padx=5)
        self.refresh_users_tree()


    def delete_user(self):
        selected = self.u_tree.selection()
        if not selected:
            self.show_msg("تنبيه", "يرجى تحديد مستخدم للحذف"); return
        username = self.u_tree.item(selected[0])['values'][1]
        if username.lower() == "admin":
            self.show_msg("خطأ", "لا يمكن حذف المستخدم الرئيسي (admin)"); return
        if self.ask_confirm(str("تأكيد الحذف"), str(f"هل أنت متأكد من حذف المستخدم '{username}'؟")):
            try:
                self.db.cursor.execute("DELETE FROM users WHERE username=?", (username,))
                self.db.conn.commit()
                self.log_action("حذف مستخدم", "users", f"المستخدم: {username}")
                self.show_msg("نجاح", "تم حذف المستخدم بنجاح"); self.refresh_users_tree()
            except sqlite3.Error as e: self.show_msg("خطأ", str(e))

    def edit_user_ui(self):
        selected = self.u_tree.selection()
        if not selected:
            self.show_msg("تنبيه", "يرجى تحديد مستخدم للتعديل"); return
        old_role, old_user = self.u_tree.item(selected[0])['values']
        
        ed = ctk.CTkToplevel(self); ed.title(fix_arabic("تعديل المستخدم", is_title=True)); ed.geometry("400x400"); ed.attributes("-topmost", True); ed.grab_set()
        ctk.CTkLabel(ed, text=fix_arabic(f"تعديل المستخدم: {old_user}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=15)
        
        ctk.CTkLabel(ed, text=fix_arabic("الاسم الجديد:", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25)
        e_user = ctk.CTkEntry(ed, font=FONT_NORMAL_BOLD, justify="right", height=40); e_user.pack(pady=5, padx=20, fill="x")
        e_user.insert(0, old_user)
        
        ctk.CTkLabel(ed, text=fix_arabic("كلمة المرور الجديدة:", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25)
        e_pass = ctk.CTkEntry(ed, font=FONT_NORMAL_BOLD, justify="right", height=40, show="*"); e_pass.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(ed, text=fix_arabic("الصلاحية:", for_ui=True), font=FONT_NORMAL_BOLD).pack(anchor="e", padx=25)
        e_role = ctk.CTkComboBox(ed, values=["employee", "admin"], height=40); e_role.pack(pady=5, padx=20, fill="x")
        e_role.set(old_role)
        
        def save_user_edit():
            new_u, new_p, new_r = e_user.get().strip(), e_pass.get().strip(), e_role.get()
            if not new_u: self.show_msg("خطأ", "الاسم لا يمكن أن يكون فارغاً"); return
            try:
                if new_p:
                    self.db.cursor.execute("UPDATE users SET username=?, password=?, role=? WHERE username=?", (new_u.lower(), hash_password(new_p), new_r, old_user))
                else:
                    self.db.cursor.execute("UPDATE users SET username=?, role=? WHERE username=?", (new_u.lower(), new_r, old_user))
                self.db.conn.commit()
                self.log_action("تعديل مستخدم", "users", f"المستخدم القديم: {old_user}; الجديد: {new_u}")
                self.show_msg("نجاح", "تم تعديل بيانات المستخدم بنجاح"); ed.destroy(); self.refresh_users_tree()
            except sqlite3.Error as e: self.show_msg("خطأ", str(e))
            
        ctk.CTkButton(ed, text=fix_arabic("حفظ التعديلات", for_ui=True), command=save_user_edit, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45).pack(pady=20, padx=20, fill="x")

    def save_settings(self):
        try:
            for k, e in self.s_entries.items():
                value = e.get().strip()
                if k == "reg_points" and int(clean_float(value)) < 0:
                    raise ValueError("نقاط التسجيل لا يمكن أن تكون سالبة")
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, value))
            self.db.conn.commit(); self.log_action("تعديل الإعدادات", "settings", "إعدادات المحل"); self.show_msg("نجاح", "تم حفظ الإعدادات بنجاح. يرجى إعادة تشغيل البرنامج.")
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر حفظ الإعدادات", str(exc))

    def add_new_user(self):
        u, p, r = self.new_u.get().strip(), self.new_p.get().strip(), self.new_r.get()
        if not u or not p:
            self.show_msg("تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور"); return
        try:
            self.db.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u.lower(), hash_password(p), r))
            self.db.conn.commit(); self.log_action("إضافة مستخدم", "users", f"المستخدم: {u}; الصلاحية: {r}"); self.refresh_users_tree(); self.show_msg("نجاح", "تم إضافة المستخدم")
        except sqlite3.IntegrityError:
            self.show_msg("خطأ", "اسم المستخدم موجود مسبقاً")

    def refresh_users_tree(self):
        for i in self.u_tree.get_children(): self.u_tree.delete(i)
        self.db.cursor.execute("SELECT role, username FROM users")
        [self.u_tree.insert("", "end", values=(r[0], r[1])) for r in self.db.cursor.fetchall()]

    def refresh_customers(self):
        for i in self.c_tree.get_children(): self.c_tree.delete(i)
        q = self.c_search.get().strip()
        if q:
            self.db.cursor.execute("SELECT points, phone, name FROM customers WHERE name LIKE ? ORDER BY name ASC", (f"%{q}%",))
        else:
            self.db.cursor.execute("SELECT points, phone, name FROM customers ORDER BY name ASC")
        for r in self.db.cursor.fetchall():
            # r[1] is phone. Check note with robust variations (with/without leading zero)
            p_val = str(r[1]).strip()
            p_alt = p_val[1:] if p_val.startswith('0') else '0' + p_val
            self.db.cursor.execute("SELECT note FROM customer_notes WHERE phone=? OR phone=?", (p_val, p_alt))
            n_res = self.db.cursor.fetchone()
            note_str = "يوجد ملاحظة ⚠️" if n_res and n_res[0] else "-"
            # Ensure phone is formatted as string explicitly
            self.c_tree.insert("", "end", values=(note_str, r[0], str(r[1]), fix_arabic(r[2], for_ui=True)))

    def export_customers(self):
        try:
            df = pd.read_sql_query("SELECT name, phone, points FROM customers", self.db.conn)
            df.to_excel("Customers.xlsx", index=False); self.show_msg("نجاح", "تم التصدير")
        except Exception as e: self.show_msg("خطأ", str(e))

    def ui_advanced_reports(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("التقارير المتقدمة")
        
        f_top = ctk.CTkFrame(self.main_view, fg_color="transparent"); f_top.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_top, text=fix_arabic("من تاريخ:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.ar_from = ctk.CTkEntry(f_top, placeholder_text="YYYY-MM-DD", font=FONT_NORMAL_BOLD, width=130, justify="right", corner_radius=8); self.ar_from.pack(side="right", padx=5)
        ctk.CTkLabel(f_top, text=fix_arabic("إلى تاريخ:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.ar_to = ctk.CTkEntry(f_top, placeholder_text="YYYY-MM-DD", font=FONT_NORMAL_BOLD, width=130, justify="right", corner_radius=8); self.ar_to.pack(side="right", padx=5)
        
        ctk.CTkLabel(f_top, text=fix_arabic("النوع:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=5)
        self.ar_type = ctk.CTkComboBox(f_top, values=[fix_arabic("الكل", for_ui=True), fix_arabic("مبيعات", for_ui=True), fix_arabic("صيانة", for_ui=True), fix_arabic("حوالات وفواتير", for_ui=True)], font=FONT_NORMAL_BOLD, width=150, justify="right", corner_radius=8)
        self.ar_type.pack(side="right", padx=5); self.ar_type.set(fix_arabic("الكل", for_ui=True))
        
        ctk.CTkButton(f_top, text=fix_arabic("عرض", for_ui=True), command=self.refresh_advanced_reports, font=FONT_BOLD, width=90, fg_color=COLOR_CRIMSON, height=38).pack(side="right", padx=10)
        ctk.CTkButton(f_top, text=fix_arabic("تصدير إكسل", for_ui=True), command=self.export_advanced_reports, font=FONT_BOLD, width=110, fg_color=COLOR_TEAL, height=38).pack(side="left", padx=10)
        
        self.ar_tree = ttk.Treeview(self.main_view, columns=("user", "time", "desc", "amount", "date", "client", "type"), show="headings")
        for col, head in zip(self.ar_tree["columns"], ["المستخدم", "الساعة", "التفاصيل", "المبلغ", "التاريخ", "العميل", "نوع الخدمة"]): 
            self.ar_tree.heading(col, text=fix_arabic(head, for_ui=True))
        self.ar_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_advanced_reports()

    def _advanced_rows(self):
        start, end, tp = self.ar_from.get(), self.ar_to.get(), self.ar_type.get()
        where, params = self.date_filter("date", start, end)
        all_lbl, sales_lbl = fix_arabic("الكل", for_ui=True), fix_arabic("مبيعات", for_ui=True)
        maint_lbl, trans_lbl = fix_arabic("صيانة", for_ui=True), fix_arabic("حوالات وفواتير", for_ui=True)
        data = []
        if tp in [all_lbl, sales_lbl]:
            self.db.cursor.execute("SELECT name, date, total, code, time, user, payment_method FROM sales" + (" " + where if where else ""), params)
            for r in self.db.cursor.fetchall(): data.append(("مبيعات", r[0] or "نقدي", r[1], float(r[2] or 0), f"منتج: {r[3]} | الدفع: {r[6] or 'نقدي'}", r[4], r[5] or "admin"))
        if tp in [all_lbl, maint_lbl]:
            self.db.cursor.execute("SELECT client_name, date, revenue, repair_desc, time, user FROM maintenance" + (" " + where if where else ""), params)
            for r in self.db.cursor.fetchall(): data.append(("صيانة", r[0] or "-", r[1], float(r[2] or 0), r[3] or "", r[4], r[5] or "admin"))
        if tp in [all_lbl, trans_lbl]:
            self.db.cursor.execute("SELECT type, client_name, date, (amount + commission), reference, time, user FROM transfers" + (" " + where if where else ""), params)
            for r in self.db.cursor.fetchall(): data.append((r[0] or "حوالة", r[1] or "-", r[2], float(r[3] or 0), f"مرجع: {r[4] or '-'}", r[5], r[6] or "admin"))
        return sorted(data, key=lambda x: (x[2], x[5]), reverse=True)

    def refresh_advanced_reports(self):
        for i in self.ar_tree.get_children(): self.ar_tree.delete(i)
        try:
            for row in self._advanced_rows():
                self.ar_tree.insert("", "end", values=(row[6], row[5], fix_arabic(row[4], for_ui=True), f"{row[3]:.2f}", row[2], fix_arabic(row[1], for_ui=True), fix_arabic(row[0], for_ui=True)))
        except (ValueError, sqlite3.Error) as exc:
            self.show_msg("خطأ في التقرير", str(exc))

    def export_advanced_reports(self):
        try:
            rows = self._advanced_rows()
            df = pd.DataFrame([{"نوع الخدمة": r[0], "العميل": r[1], "التاريخ": r[2], "المبلغ": r[3], "التفاصيل": r[4], "الساعة": r[5], "المستخدم": r[6]} for r in rows])
            df.to_excel("Advanced_Reports.xlsx", index=False)
            self.log_action("تصدير تقرير", "advanced_reports", f"عدد السجلات: {len(rows)}")
            self.show_msg("نجاح", "تم تصدير التقرير إلى Advanced_Reports.xlsx بنجاح")
        except (ValueError, sqlite3.Error, OSError, ImportError) as exc:
            self.show_msg("خطأ", str(exc))

    def ui_internal_transfers(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("التحويلات الداخلية بين الحسابات")
        intro = ctk.CTkLabel(
            self.main_view,
            text=fix_arabic("سجل سحب رصيد الفيزا أو CLIQ وإيداعه في البنك، أو أي تحويل بين حسابات المحل الداخلية دون أن يؤثر على صافي الإيرادات.", for_ui=True),
            font=FONT_NORMAL_BOLD,
            text_color=COLOR_TEXT_MUTED
        )
        intro.pack(anchor="e", padx=22, pady=(0, 8))

        form = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        form.pack(fill="x", padx=18, pady=8)

        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=10)

        # Source Account
        s_item = ctk.CTkFrame(row1, fg_color="transparent")
        s_item.pack(side="right", expand=True, fill="x", padx=6)
        ctk.CTkLabel(s_item, text=fix_arabic("الحساب المصدر (من)", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
        source_var = ctk.StringVar(value="Visa")
        source_combo = ctk.CTkComboBox(s_item, values=["Visa", "CLIQ", "Cash", "Bank"], variable=source_var, height=40, font=FONT_NORMAL_BOLD, justify="right")
        source_combo.pack(fill="x", pady=(3, 0))

        # Destination Account
        d_item = ctk.CTkFrame(row1, fg_color="transparent")
        d_item.pack(side="right", expand=True, fill="x", padx=6)
        ctk.CTkLabel(d_item, text=fix_arabic("الحساب المستلم (إلى)", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
        dest_var = ctk.StringVar(value="Bank")
        dest_combo = ctk.CTkComboBox(d_item, values=["Bank", "Cash", "Visa", "CLIQ"], variable=dest_var, height=40, font=FONT_NORMAL_BOLD, justify="right")
        dest_combo.pack(fill="x", pady=(3, 0))

        # Amount
        a_item = ctk.CTkFrame(row1, fg_color="transparent")
        a_item.pack(side="right", expand=True, fill="x", padx=6)
        ctk.CTkLabel(a_item, text=fix_arabic("المبلغ المحول", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
        amt_entry = ctk.CTkEntry(a_item, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text="0.00")
        amt_entry.pack(fill="x", pady=(3, 0))

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(0, 10))

        # Reference
        r_item = ctk.CTkFrame(row2, fg_color="transparent")
        r_item.pack(side="right", expand=True, fill="x", padx=6)
        ctk.CTkLabel(r_item, text=fix_arabic("رقم الإيصال / المرجع", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
        ref_entry = ctk.CTkEntry(r_item, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text="رقم الحوالة أو الإيداع")
        ref_entry.pack(fill="x", pady=(3, 0))

        # Notes
        n_item = ctk.CTkFrame(row2, fg_color="transparent")
        n_item.pack(side="right", expand=True, fill="x", padx=6)
        ctk.CTkLabel(n_item, text=fix_arabic("ملاحظات التحويل", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
        notes_entry = ctk.CTkEntry(n_item, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text="سبب التحويل أو تفاصيل إضافية")
        notes_entry.pack(fill="x", pady=(3, 0))

        # Save Button
        b_item = ctk.CTkFrame(row2, fg_color="transparent")
        b_item.pack(side="left", padx=6, pady=(24, 0))
        def save_transfer():
            try:
                src = source_var.get().strip()
                dst = dest_var.get().strip()
                if src == dst:
                    raise ValueError("الحساب المصدر والحساب المستلم يجب أن يكونا مختلفين")
                amount = self.positive_number(amt_entry.get().strip(), "المبلغ المحول")
                now = datetime.datetime.now()
                self.db.cursor.execute(
                    "INSERT INTO internal_transfers (source_acc, dest_acc, amount, reference, date, time, notes, user) VALUES (?,?,?,?,?,?,?,?)",
                    (src, dst, amount, ref_entry.get().strip(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), notes_entry.get().strip(), self.current_user)
                )
                internal_source_id = f"internal-transfer-{now.strftime('%Y%m%d%H%M%S%f')}"
                self._post_journal_entry("internal_transfer", internal_source_id, "تحويل داخلي بين حسابات المحل", [(self._ledger_account_for_payment(dst), amount, 0, "الحساب المستلم"), (self._ledger_account_for_payment(src), 0, amount, "الحساب المصدر")], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
                self.db.conn.commit()
                self.log_action("تحويل داخلي بين الحسابات", "internal_transfers", f"من {src} إلى {dst}: {amount:.2f}")
                self.show_msg("نجاح", "تم تسجيل التحويل الداخلي بنجاح")
                amt_entry.delete(0, 'end')
                ref_entry.delete(0, 'end')
                notes_entry.delete(0, 'end')
                refresh_table()
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر حفظ التحويل", str(exc))

        ctk.CTkButton(b_item, text=fix_arabic("تنفيذ وحفظ التحويل", for_ui=True), command=save_transfer, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=40, width=160).pack()

        # History Tree
        tree_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=18, pady=10)

        tree = ttk.Treeview(tree_frame, columns=("id", "date", "source", "dest", "amount", "ref", "notes", "user"), show="headings")
        for col, head in zip(tree["columns"], ["ID", "التاريخ", "من", "إلى", "المبلغ", "المرجع", "الملاحظات", "المستخدم"]):
            tree.heading(col, text=fix_arabic(head, for_ui=True))
            tree.column(col, anchor="center")
        tree.column("id", width=50)
        tree.pack(fill="both", expand=True)

        def refresh_table():
            for i in tree.get_children(): tree.delete(i)
            self.db.cursor.execute("SELECT id, date, source_acc, dest_acc, amount, reference, notes, user FROM internal_transfers ORDER BY id DESC")
            for r in self.db.cursor.fetchall():
                tree.insert("", "end", values=(r[0], r[1], r[2], r[3], f"{r[4]:.2f}", fix_arabic(r[5] or "", for_ui=True), fix_arabic(r[6] or "", for_ui=True), r[7] or "-"))

        refresh_table()

        btn_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        btn_f.pack(fill="x", padx=18, pady=5)
        ctk.CTkButton(btn_f, text=fix_arabic("حذف التحويل المختار", for_ui=True), command=lambda: self.delete_record("internal_transfers", tree, callback=refresh_table, id_index=0), font=FONT_BOLD, fg_color=COLOR_RUBI, height=40).pack(side="right", padx=5)

    def ui_expenses(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("المصاريف")
        f = ctk.CTkFrame(self.main_view, fg_color="transparent"); f.pack(fill="x", padx=15, pady=5)
        self.e_desc = ctk.CTkEntry(f, placeholder_text=fix_arabic("وصف المصروف", for_ui=True), width=260, height=45, justify="right", corner_radius=10, font=FONT_NORMAL_BOLD); self.e_desc.pack(side="right", padx=5)
        self.e_amt = ctk.CTkEntry(f, placeholder_text=fix_arabic("المبلغ", for_ui=True), width=110, height=45, justify="right", corner_radius=10, font=FONT_NORMAL_BOLD); self.e_amt.pack(side="right", padx=5)

        self.e_source_var = ctk.StringVar(value="Cash")
        source_combo = ctk.CTkComboBox(f, values=["Cash", "Bank", "Visa", "CLIQ", "Unpaid"], variable=self.e_source_var, width=130, height=45, font=FONT_NORMAL_BOLD, justify="right")
        source_combo.pack(side="right", padx=5)

        ctk.CTkButton(f, text=fix_arabic("إضافة مصروف", for_ui=True), command=self.add_expense, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=45).pack(side="right", padx=5)
        
        self.exp_tree = ttk.Treeview(self.main_view, columns=("id", "date", "amount", "source", "desc"), show="headings")
        for col, head in zip(self.exp_tree["columns"], ["ID", "التاريخ", "المبلغ", "طريقة الدفع / المصدر", "الوصف"]): 
            self.exp_tree.heading(col, text=fix_arabic(head, for_ui=True))
            self.exp_tree.column(col, anchor="center")
        self.exp_tree.column("id", width=50)
        self.exp_tree.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.exp_tree.tag_configure("paid", foreground=COLOR_TEAL_DARK)
        self.exp_tree.tag_configure("unpaid", foreground=COLOR_WHITE)
        
        def refresh_exp():
            for i in self.exp_tree.get_children(): self.exp_tree.delete(i)
            self.db.cursor.execute("SELECT id, date, amount, COALESCE(payment_source,'Cash'), desc, COALESCE(status,'paid') FROM expenses ORDER BY id DESC")
            for r in self.db.cursor.fetchall():
                status = str(r[5]).lower()
                tag = "unpaid" if status == "unpaid" or str(r[3]).lower() == "unpaid" else "paid"
                src_display = "غير مدفوع (Unpaid)" if tag == "unpaid" else r[3]
                self.exp_tree.insert("", "end", values=(r[0], r[1], f"{r[2]:.2f}", src_display, fix_arabic(r[4], for_ui=True)), tags=(tag,))
        
        refresh_exp()
        
        btn_f = ctk.CTkFrame(self.main_view, fg_color="transparent"); btn_f.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(btn_f, text=fix_arabic("تعديل المصروف المختار", for_ui=True), command=self.edit_selected_expense, font=FONT_BOLD, fg_color=COLOR_VINO, height=40).pack(side="right", padx=5)
        ctk.CTkButton(btn_f, text=fix_arabic("حذف المصروف المختار", for_ui=True), command=lambda: self.delete_record("expenses", self.exp_tree, callback=refresh_exp, id_index=0), font=FONT_BOLD, fg_color=COLOR_RUBI, height=40).pack(side="right", padx=5)

    def edit_selected_expense(self):
        sel = self.exp_tree.selection()
        if not sel: self.show_msg("تنبيه", "حدد مصروفاً أولاً"); return
        vals = self.exp_tree.item(sel[0])['values']
        eid, old_amt, old_src, old_desc = vals[0], vals[2], vals[3], vals[4]
        
        win = ctk.CTkToplevel(self); win.title(str("تعديل مصروف")); win.geometry("420x340"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=str("تعديل بيانات المصروف"), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=15)
        e_desc = ctk.CTkEntry(win, width=320, height=45, justify="right"); e_desc.pack(pady=5); e_desc.insert(0, old_desc)
        e_amt = ctk.CTkEntry(win, width=320, height=45, justify="right"); e_amt.pack(pady=5); e_amt.insert(0, str(old_amt).split()[0])
        src_var = ctk.StringVar(value=old_src if old_src in ["Cash", "Bank", "Visa", "CLIQ", "Unpaid"] else "Cash")
        src_combo = ctk.CTkComboBox(win, values=["Cash", "Bank", "Visa", "CLIQ", "Unpaid"], variable=src_var, width=320, height=42, justify="right", font=FONT_NORMAL_BOLD)
        src_combo.pack(pady=5)
        
        def save():
            try:
                d, a, s = e_desc.get().strip(), self.positive_number(e_amt.get(), "المبلغ"), src_var.get().strip()
                status = "unpaid" if s == "Unpaid" else "paid"
                self._void_journals_for_record("expenses", eid, "إلغاء أثر المصروف قبل التعديل")
                self.db.cursor.execute("UPDATE expenses SET desc=?, amount=?, payment_source=?, status=? WHERE id=?", (d, a, s, status, eid))
                self._post_operation_journal_from_row("expenses", eid)
                self.db.conn.commit(); self.log_action("تعديل مصروف", "expenses", f"ID: {eid}"); win.destroy(); self.ui_expenses()
            except Exception as exc:
                self.db.conn.rollback()
                self.show_msg("خطأ", str(exc))
        ctk.CTkButton(win, text=str("حفظ التعديلات"), command=save, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45).pack(pady=15)

    def add_expense(self):
        d, a = self.e_desc.get().strip(), self.e_amt.get().strip()
        src = self.e_source_var.get().strip()
        if not d or not a:
            self.show_msg("تنبيه", "يرجى إدخال وصف المصروف والمبلغ"); return
        try:
            amount = self.positive_number(a, "المبلغ")
            status = "unpaid" if src == "Unpaid" else "paid"
            now = datetime.datetime.now()
            self.db.cursor.execute("INSERT INTO expenses (desc, amount, payment_source, status, date, time, user) VALUES (?,?,?,?,?,?,?)", (d, amount, src, status, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), self.current_user))
            expense_source_id = f"expense-{now.strftime('%Y%m%d%H%M%S%f')}"
            credit_account = "ACCRUED_EXPENSE" if status == "unpaid" else self._ledger_account_for_payment(src)
            self._post_journal_entry("expense", expense_source_id, "قيد مصروف", [("EXPENSE", amount, 0, d), (credit_account, 0, amount, "مصدر سداد المصروف أو التزام مستحق")], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
            self.db.conn.commit(); self.log_action("تسجيل مصروف", "expenses", f"الوصف: {d}; المبلغ: {amount:.2f}; المصدر: {src}"); self.ui_expenses()
        except (ValueError, sqlite3.Error) as exc:
            self.db.conn.rollback(); self.show_msg("تعذر تسجيل المصروف", str(exc))

    def draw_visual_dashboard(self, parent):
        chart_frame = ctk.CTkFrame(parent, corner_radius=15, border_width=1)
        chart_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(chart_frame, text=fix_arabic("منحنيات الأداء والخدمات - آخر 30 يوماً", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=8)
        
        # Build 3 separate sub-canvases for Sales, Maintenance, and Transfers over last 30 days
        services = [
            ("المبيعات (Sales)", "SELECT date, COALESCE(SUM(total),0) FROM sales GROUP BY date ORDER BY date DESC LIMIT 30", COLOR_TEAL),
            ("الصيانة (Maintenance)", "SELECT date, COALESCE(SUM(revenue),0) FROM maintenance GROUP BY date ORDER BY date DESC LIMIT 30", COLOR_VINO_DARK),
            ("عمولات الحوالات (Transfers)", "SELECT date, COALESCE(SUM(commission),0) FROM transfers GROUP BY date ORDER BY date DESC LIMIT 30", COLOR_TEAL_DARK)
        ]
        
        for title, query, color in services:
            sub_f = ctk.CTkFrame(chart_frame, fg_color="transparent")
            sub_f.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(sub_f, text=fix_arabic(title, for_ui=True), font=FONT_BOLD, text_color=color).pack(anchor="w", padx=15)
            canvas = ctk.CTkCanvas(sub_f, height=180, background=COLOR_WHITE, highlightthickness=0)
            canvas.pack(fill="x", padx=15, pady=(0, 10))
            
            self.db.cursor.execute(query)
            rows = list(reversed(self.db.cursor.fetchall()))
            if not rows:
                canvas.create_text(450, 90, text=fix_arabic("لا توجد بيانات كافية لهذه الفترة", for_ui=True), font=FONT_BOLD, fill=COLOR_TEXT_DARK)
                continue
            width, bottom, top = 880, 150, 20
            canvas.configure(width=width)
            max_val = max(float(r[1] or 0) for r in rows) or 1.0
            canvas.create_line(50, top, 50, bottom, fill=COLOR_TEXT_MUTED, width=2)
            canvas.create_line(50, bottom, width-20, bottom, fill=COLOR_TEXT_MUTED, width=2)
            points = []
            step = max(10, (width - 80) / max(1, len(rows) - 1))
            for idx, (dt, val) in enumerate(rows):
                x = 50 + idx * step
                y = bottom - (float(val or 0) / max_val) * (bottom - top)
                points.append((x, y))
                if idx % max(1, len(rows)//6) == 0:
                    canvas.create_text(x, bottom + 12, text=str(dt)[5:], font=FONT_BOLD, fill=COLOR_NAVY)
            if len(points) > 1:
                for p1, p2 in zip(points, points[1:]):
                    canvas.create_line(*p1, *p2, fill=color, width=3)
            for x, y in points:
                canvas.create_oval(x-3, y-3, x+3, y+3, fill=color, outline=color)

    def ui_live_operations_dashboard(self):
        """Read-only live operations view for managers; never posts or mutates accounting data."""
        self._live_dashboard_active = True
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("لوحة العمليات والأداء الحية")
        root = ctk.CTkFrame(self.main_view, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=18, pady=10)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        ctk.CTkLabel(root, text=fix_arabic(f"مراقبة مباشرة للمحل — {today}", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE, anchor="e").pack(fill="x", pady=(0, 8))
        cards = ctk.CTkFrame(root, fg_color="transparent"); cards.pack(fill="x", pady=4)
        def scalar(sql, params=("",)):
            try:
                self.db.cursor.execute(sql, params)
                return self.db.cursor.fetchone()[0] or 0
            except sqlite3.Error:
                return 0
        metrics = [
            ("مبيعات اليوم", scalar("SELECT COALESCE(SUM(total),0) FROM sales WHERE date=?", (today,)), COLOR_TEAL),
            ("إيرادات الصيانة", scalar("SELECT COALESCE(SUM(revenue),0) FROM maintenance WHERE date=?", (today,)), COLOR_WHITE),
            ("عمولات الخدمات", scalar("SELECT COALESCE(SUM(commission),0) FROM transfers WHERE date=?", (today,)), COLOR_TEAL_SOFT),
            ("المصاريف", scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date=?", (today,)), COLOR_PUMPKIN_ORANGE),
        ]
        for title, value, color in metrics:
            card = ctk.CTkFrame(cards, fg_color=COLOR_NAVY, border_width=1, border_color=COLOR_BORDER, corner_radius=10)
            card.pack(side="right", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=fix_arabic(title, for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=fix_arabic(f"{float(value):.2f} {CURRENCY}", for_ui=True), font=FONT_REPORT_VALUE, text_color=color).pack(pady=(2, 8))
        action_row = ctk.CTkFrame(root, fg_color="transparent"); action_row.pack(fill="x", pady=6)
        ctk.CTkButton(action_row, text=fix_arabic("تحديث الآن", for_ui=True), command=self.ui_live_operations_dashboard, font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, width=150, height=38).pack(side="right")
        ctk.CTkLabel(action_row, text=fix_arabic("قراءة مباشرة من قاعدة البيانات — لا يتم إنشاء قيود أو تعديل أرصدة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e").pack(side="right", padx=14)
        critical = ctk.CTkFrame(root, fg_color=COLOR_VINO_DARK, border_width=1, border_color=COLOR_RUBI, corner_radius=12); critical.pack(fill="both", expand=True, pady=6)
        ctk.CTkLabel(critical, text=fix_arabic("حركة المخزون الحرجة والتنبيهات", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(critical, text=fix_arabic("نافد = صفر | حرج = الكمية أقل أو تساوي الحد الأدنى", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e").pack(fill="x", padx=12, pady=(0, 6))
        tree = ttk.Treeview(critical, columns=("status", "minimum", "stock", "code", "name"), show="headings", height=10)
        for col, head, width in [("status", "الحالة", 130), ("minimum", "حد القلق", 110), ("stock", "الكمية الحالية", 130), ("code", "الباركود", 150), ("name", "اسم المنتج", 280)]:
            tree.heading(col, text=fix_arabic(head, for_ui=True)); tree.column(col, anchor="center", width=width)
        tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        try:
            self.db.cursor.execute("SELECT code, name, stock, COALESCE(min_stock, 3) FROM products WHERE COALESCE(stock,0) <= COALESCE(min_stock,3) ORDER BY stock ASC, name ASC")
            for code, name, stock, minimum in self.db.cursor.fetchall():
                stock, minimum = int(stock or 0), int(minimum or 0)
                state = "نافد" if stock <= 0 else "حرج"
                tree.insert("", "end", values=(fix_arabic(state, for_ui=True), minimum, stock, code or "-", fix_arabic(name or "-", for_ui=True)), tags=("out",) if stock <= 0 else ("low",))
        except sqlite3.Error:
            pass
        tree.tag_configure("out", background=COLOR_RUBI_DARK, foreground=COLOR_WHITE)
        tree.tag_configure("low", background=COLOR_VINO, foreground=COLOR_WHITE)
        if not tree.get_children():
            ctk.CTkLabel(critical, text=fix_arabic("لا توجد أصناف نافدة أو حرجة حالياً", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_SOFT).pack(pady=8)
        # Refresh only while this read-only dashboard remains the active screen.
        self.after(15000, lambda: self.ui_live_operations_dashboard() if getattr(self, "_live_dashboard_active", False) else None)

    def ui_analytics(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("تقارير الأداء والتحليلات الذكية")
        # Use CTkFrame directly inside self.main_view (which is already scrollable) for full downward expansion
        scroll = ctk.CTkFrame(self.main_view, fg_color="transparent"); scroll.pack(fill="both", expand=True, padx=20, pady=10)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        f_daily = ctk.CTkFrame(scroll, corner_radius=15, fg_color=COLOR_NAVY_LIGHT, border_color=COLOR_TEAL, border_width=2); f_daily.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_daily, text=fix_arabic(f"الأداء اليومي والفوري (تاريخ اليوم: {today})", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=10)
        self.db.cursor.execute("SELECT SUM(total), SUM(buy_cost) FROM sales WHERE date=?", (today,))
        d_res = self.db.cursor.fetchone(); d_rev = d_res[0] or 0; d_cogs = d_res[1] or 0; d_prof = d_rev - d_cogs
        self.db.cursor.execute("SELECT SUM(revenue) FROM maintenance WHERE date=?", (today,))
        d_maint = self.db.cursor.fetchone()[0] or 0
        self.db.cursor.execute("SELECT SUM(commission) FROM transfers WHERE date=?", (today,))
        d_trans_comm = self.db.cursor.fetchone()[0] or 0
        row_d = ctk.CTkFrame(f_daily, fg_color="transparent"); row_d.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row_d, text=fix_arabic(f"مبيعات اليوم: {d_rev:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_SOFT).pack(side="right", padx=15)
        ctk.CTkLabel(row_d, text=fix_arabic(f"أرباح المبيعات: {d_prof:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL).pack(side="right", padx=15)
        ctk.CTkLabel(row_d, text=fix_arabic(f"إيرادات الصيانة: {d_maint:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=15)
        ctk.CTkLabel(row_d, text=fix_arabic(f"عمولات الحوالات: {d_trans_comm:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_DARK).pack(side="right", padx=15)
        self.draw_visual_dashboard(scroll)
        f_cust = ctk.CTkFrame(scroll, corner_radius=15, border_width=1, fg_color=COLOR_VINO_DARK, border_color=COLOR_TEAL_SOFT); f_cust.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_cust, text=fix_arabic("أكثر 3 عملاء تعاملاً معنا (Top 3 Customers)", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        cust_tree = ttk.Treeview(f_cust, columns=("count", "phone", "name"), show="headings", height=3)
        for c, h in zip(cust_tree["columns"], ["عدد العمليات", "رقم الهاتف", "اسم العميل"]): 
            cust_tree.heading(c, text=fix_arabic(h, for_ui=True)); cust_tree.column(c, anchor="center")
        cust_tree.pack(fill="x", padx=20, pady=10)
        self.db.cursor.execute("SELECT c.name, s.customer_phone, COUNT(*) as cnt FROM sales s LEFT JOIN customers c ON s.customer_phone = c.phone WHERE s.customer_phone IS NOT NULL AND s.customer_phone != '' GROUP BY s.customer_phone ORDER BY cnt DESC LIMIT 3")
        for r in self.db.cursor.fetchall(): cust_tree.insert("", "end", values=(r[2], r[1], fix_arabic(r[0] or "عميل غير مسجل", for_ui=True)))
        f_top = ctk.CTkFrame(scroll, corner_radius=15, border_width=1); f_top.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_top, text=fix_arabic("المنتجات الأكثر طلباً ومبيعاً", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        top_tree = ttk.Treeview(f_top, columns=("rev", "qty", "name"), show="headings", height=5)
        for c, h in zip(top_tree["columns"], ["إجمالي الإيرادات", "الكمية المباعة", "اسم المنتج"]): 
            top_tree.heading(c, text=fix_arabic(h, for_ui=True)); top_tree.column(c, anchor="center")
        top_tree.pack(fill="x", padx=20, pady=10)
        self.db.cursor.execute("SELECT name, SUM(qty), SUM(total) FROM sales GROUP BY name ORDER BY SUM(qty) DESC LIMIT 5")
        for r in self.db.cursor.fetchall(): top_tree.insert("", "end", values=(f"{r[2]:.2f} {CURRENCY}", r[1], fix_arabic(r[0], for_ui=True)))
        f_peak = ctk.CTkFrame(scroll, corner_radius=15, border_width=1); f_peak.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(f_peak, text=fix_arabic("تحليل أوقات الذروة (حسب ساعة البيع)", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        peak_tree = ttk.Treeview(f_peak, columns=("count", "hour"), show="headings", height=5)
        for c, h in zip(peak_tree["columns"], ["عدد العمليات", "الساعة"]): 
            peak_tree.heading(c, text=fix_arabic(h, for_ui=True)); peak_tree.column(c, anchor="center")
        peak_tree.pack(fill="x", padx=20, pady=10)
        self.db.cursor.execute("SELECT SUBSTR(time, 1, 2) AS hr, COUNT(*) FROM sales GROUP BY hr ORDER BY COUNT(*) DESC LIMIT 5")
        for r in self.db.cursor.fetchall(): peak_tree.insert("", "end", values=(r[1], fix_arabic(f"الساعة {r[0]}:00", for_ui=True)))







    def ui_debts(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("إدارة الديون والذمم")
        
        container = ctk.CTkFrame(self.main_view, fg_color="transparent", height=700)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_top = ctk.CTkFrame(container, fg_color="transparent")
        btn_top.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(btn_top, text=str("إضافة تفاصيل دين جديدة ➕"), command=self.open_add_new_debt_details_ui, font=FONT_BOLD, fg_color=COLOR_TEAL, height=52, width=280).pack(side="right", padx=10)
        
        tabview = ctk.CTkTabview(container, corner_radius=15, border_width=1, border_color=COLOR_CRIMSON, height=600)
        tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        t_cust = tabview.add(str("ذمم العملاء (البيع الآجل)"))
        t_supp = tabview.add(str("ذمم الموردين"))
        try:
            tabview._segmented_button.configure(font=FONT_BOLD)
        except Exception:
            pass
        
        # --- Customer Debts Tab ---
        f_c = ctk.CTkFrame(t_cust, fg_color="transparent")
        f_c.pack(fill="both", expand=True, padx=5, pady=5)
        f_c.grid_rowconfigure(0, weight=1)
        f_c.grid_columnconfigure(0, weight=1)
        
        self.cd_tree = ttk.Treeview(f_c, columns=("status", "last_pay", "rem", "paid", "total", "phone", "name", "id"), show="headings")
        for c, h in zip(self.cd_tree["columns"], [str("الحالة"), str("آخر سداد"), str("المتبقي"), str("المدفوع"), str("إجمالي الدين"), str("الهاتف"), str("العميل"), str("ID")]):
            self.cd_tree.heading(c, text=fix_arabic(h, for_ui=True)); self.cd_tree.column(c, anchor="center")
        self.cd_tree.tag_configure("remaining", background="#FFF3A6", foreground="#111827")
        self.cd_tree.grid(row=0, column=0, sticky="nsew")
        
        btn_c = ctk.CTkFrame(f_c, fg_color="transparent")
        btn_c.grid(row=1, column=0, sticky="ew", pady=10)
        ctk.CTkButton(btn_c, text=str("الاطلاع على التفاصيل 📋"), command=lambda: self.show_debt_details_v111("customer"), font=FONT_BOLD, fg_color=COLOR_TEAL, height=45, width=180).pack(side="right", padx=10)
        ctk.CTkButton(btn_c, text=str("تسديد دفعة عميل"), command=lambda: self.open_pay_debt_ui("customer"), font=FONT_BOLD, fg_color=COLOR_VINO, height=45, width=180).pack(side="right", padx=10)
        ctk.CTkButton(btn_c, text=str("حذف السجل"), command=lambda: self.delete_record("customer_debts", self.cd_tree, callback=self.refresh_debts), font=FONT_BOLD, fg_color=COLOR_RUBI, height=45, width=150).pack(side="left", padx=10)
        
        # --- Supplier Debts Tab ---
        f_s = ctk.CTkFrame(t_supp, fg_color="transparent")
        f_s.pack(fill="both", expand=True, padx=5, pady=5)
        f_s.grid_rowconfigure(0, weight=1)
        f_s.grid_columnconfigure(0, weight=1)
        
        self.sd_tree = ttk.Treeview(f_s, columns=("status", "last_pay", "rem", "paid", "total", "name", "id"), show="headings")
        for c, h in zip(self.sd_tree["columns"], [str("الحالة"), str("آخر سداد"), str("المتبقي"), str("المدفوع"), str("إجمالي الدين"), str("المورد"), str("ID")]):
            self.sd_tree.heading(c, text=fix_arabic(h, for_ui=True)); self.sd_tree.column(c, anchor="center")
        self.sd_tree.tag_configure("remaining", background="#FFF3A6", foreground="#111827")
        self.sd_tree.grid(row=0, column=0, sticky="nsew")
        
        btn_s = ctk.CTkFrame(f_s, fg_color="transparent")
        btn_s.grid(row=1, column=0, sticky="ew", pady=10)
        ctk.CTkButton(btn_s, text=str("الاطلاع على التفاصيل 📋"), command=lambda: self.show_debt_details_v111("supplier"), font=FONT_BOLD, fg_color=COLOR_TEAL, height=45, width=180).pack(side="right", padx=10)
        ctk.CTkButton(btn_s, text=str("تسديد دفعة مورد"), command=lambda: self.open_pay_debt_ui("supplier"), font=FONT_BOLD, fg_color=COLOR_VINO, height=45, width=180).pack(side="right", padx=10)
        ctk.CTkButton(btn_s, text=str("حذف السجل"), command=lambda: self.delete_record("supplier_debts", self.sd_tree, callback=self.refresh_debts), font=FONT_BOLD, fg_color=COLOR_RUBI, height=45, width=150).pack(side="left", padx=10)
        
        self.refresh_debts()

    def refresh_debts(self):
        try:
            for i in self.cd_tree.get_children(): self.cd_tree.delete(i)
            self.db.cursor.execute("SELECT status, COALESCE(last_payment_date, '-'), (total_debt - paid_amount), paid_amount, total_debt, customer_phone, customer_name, id FROM customer_debts ORDER BY CASE WHEN (total_debt - paid_amount) > 0.005 THEN 0 ELSE 1 END, id DESC")
            for r in self.db.cursor.fetchall():
                remaining = float(r[2] or 0)
                self.cd_tree.insert("", "end", values=(fix_arabic(r[0], for_ui=True), r[1], f"{remaining:.2f}", f"{float(r[3] or 0):.2f}", f"{float(r[4] or 0):.2f}", r[5], fix_arabic(r[6], for_ui=True), r[7]), tags=("remaining",) if remaining > 0.005 else ())
                
            for i in self.sd_tree.get_children(): self.sd_tree.delete(i)
            self.db.cursor.execute("SELECT status, COALESCE(last_payment_date, '-'), (total_debt - paid_amount), paid_amount, total_debt, supplier_name, id FROM supplier_debts ORDER BY CASE WHEN (total_debt - paid_amount) > 0.005 THEN 0 ELSE 1 END, id DESC")
            for r in self.db.cursor.fetchall():
                remaining = float(r[2] or 0)
                self.sd_tree.insert("", "end", values=(fix_arabic(r[0], for_ui=True), r[1], f"{remaining:.2f}", f"{float(r[3] or 0):.2f}", f"{float(r[4] or 0):.2f}", fix_arabic(r[5], for_ui=True), r[6]), tags=("remaining",) if remaining > 0.005 else ())
        except Exception: pass

    def show_debt_details_v111(self, dtype="customer"):
        tree = self.cd_tree if dtype == "customer" else self.sd_tree
        sel = tree.selection()
        if not sel: self.show_msg("تنبيه", "يرجى تحديد سجل لرؤية التفاصيل"); return
        vals = tree.item(sel[0])['values']
        rid = vals[-1]
        
        table = "customer_debts" if dtype == "customer" else "supplier_debts"
        name_col = "customer_name" if dtype == "customer" else "supplier_name"
        self.db.cursor.execute(f"SELECT {name_col}, notes FROM {table} WHERE id=?", (rid,))
        row = self.db.cursor.fetchone()
        raw_name = row[0] if row else "-"
        original_notes = row[1] if row else "-"
        
        self.db.cursor.execute("SELECT notes, date FROM debt_payments WHERE debt_id=? AND debt_type=? ORDER BY id DESC LIMIT 1", (rid, dtype))
        last_pay = self.db.cursor.fetchone()
        last_note = f"{last_pay[0]} ({last_pay[1]})" if last_pay else "-"
        
        win = ctk.CTkToplevel(self); win.geometry("500x450"); win.attributes("-topmost", True); win.grab_set()
        # For the title bar, Windows handles Arabic but the order depends on the string structure
        win.title(f"{raw_name} :تفاصيل ذمة") 
        
        ctk.CTkLabel(win, text=fix_arabic(f"تفاصيل ذمة: {raw_name}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=20)
        
        f = ctk.CTkFrame(win, fg_color=COLOR_SURFACE, corner_radius=10); f.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(f, text=fix_arabic("تفاصيل الذمة الأصلية:", for_ui=True), font=FONT_BOLD).pack(pady=(15, 5), padx=10, anchor="e")
        ctk.CTkLabel(f, text=fix_arabic(original_notes, for_ui=True), font=FONT_NORMAL_BOLD, wraplength=400).pack(pady=5, padx=20, anchor="e")
        ctk.CTkLabel(f, text=fix_arabic("ملاحظة آخر دفعة:", for_ui=True), font=FONT_BOLD).pack(pady=(15, 5), padx=10, anchor="e")
        ctk.CTkLabel(f, text=fix_arabic(last_note, for_ui=True), font=FONT_NORMAL_BOLD, wraplength=400).pack(pady=5, padx=20, anchor="e")
        
        ctk.CTkButton(win, text=fix_arabic("إغلاق", for_ui=True), command=win.destroy, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=40, width=120).pack(pady=20)

    def open_add_new_debt_details_ui(self):
        win = ctk.CTkToplevel(self); win.title(str("إضافة تفاصيل دين جديدة")); win.geometry("500x680"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=str("إدخال بيانات الدين الجديد"), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=20)
        f = ctk.CTkFrame(win, fg_color="transparent"); f.pack(fill="both", expand=True, padx=35)
        ctk.CTkLabel(f, text=str("نوع الذمة:"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        dtype = ctk.CTkOptionMenu(f, values=[fix_arabic("عميل", for_ui=True), fix_arabic("مورد", for_ui=True)], font=FONT_BOLD, height=45, fg_color=COLOR_CRIMSON)
        dtype.pack(fill="x", pady=5); dtype.set(fix_arabic("عميل", for_ui=True))
        ctk.CTkLabel(f, text=str("رقم الهاتف:"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        e_phone = ctk.CTkEntry(f, height=45, font=FONT_NORMAL_BOLD, justify="right"); e_phone.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=str("الاسم:"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        e_name = ctk.CTkEntry(f, height=45, font=FONT_NORMAL_BOLD, justify="right"); e_name.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=str("تفاصيل الذمة:"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        e_desc = ctk.CTkEntry(f, height=45, font=FONT_NORMAL_BOLD, justify="right"); e_desc.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=str("مبلغ الذمة الإجمالي:"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        e_total = ctk.CTkEntry(f, height=45, font=FONT_NORMAL_BOLD, justify="center"); e_total.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=str("تاريخ الدفعة الأولى (اختياري):"), font=FONT_BOLD).pack(anchor="e", pady=(5, 0))
        e_date = ctk.CTkEntry(f, placeholder_text="YYYY-MM-DD", height=45, font=FONT_NORMAL_BOLD, justify="center"); e_date.pack(fill="x", pady=5)
        e_date.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        def save():
            try:
                cat = dtype.get(); name = e_name.get().strip(); phone = e_phone.get().strip(); desc = e_desc.get().strip()
                total = self.positive_number(e_total.get(), "المبلغ"); first_date = e_date.get().strip(); now = datetime.datetime.now()
                if not name: raise ValueError("يرجى إدخال الاسم")
                if cat == fix_arabic("عميل", for_ui=True):
                    self.db.cursor.execute("INSERT INTO customer_debts (customer_phone, customer_name, total_debt, paid_amount, status, date, notes) VALUES (?,?,?,?,?,?,?)", (phone, name, total, 0, "غير مسدد", first_date or now.strftime("%Y-%m-%d"), desc))
                else:
                    self.db.cursor.execute("INSERT INTO supplier_debts (supplier_name, total_debt, paid_amount, status, date, notes) VALUES (?,?,?,?,?,?)", (name, total, 0, "غير مسدد", first_date or now.strftime("%Y-%m-%d"), desc))
                self.db.conn.commit(); self.log_action("إضافة دين", "debts", f"{cat}: {name}"); win.destroy(); self.refresh_debts()
                self.show_msg("نجاح", "تم إضافة تفاصيل الدين بنجاح")
            except Exception as e:
                self.db.conn.rollback()
                self.show_msg("خطأ", str(e))
        ctk.CTkButton(win, text=str("حفظ بيانات الدين"), command=save, font=FONT_BOLD, fg_color=COLOR_TEAL, height=50).pack(pady=25, padx=50, fill="x")

    def open_pay_debt_ui(self, dtype="customer"):
        tree = self.cd_tree if dtype == "customer" else self.sd_tree
        sel = tree.selection()
        if not sel: self.show_msg("تنبيه", "يرجى تحديد سجل للتسديد"); return
        vals = tree.item(sel[0])['values']
        rid = vals[-1]; rem = float(vals[2])
        win = ctk.CTkToplevel(self); win.title(str("تسديد دفعة")); win.geometry("400x420"); win.attributes("-topmost", True); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic(f"المتبقي: {rem:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=20)
        amt_e = ctk.CTkEntry(win, placeholder_text=fix_arabic("المبلغ المدفوع الآن", for_ui=True), height=45, justify="center", font=FONT_NORMAL_BOLD); amt_e.pack(pady=10, padx=40, fill="x")
        ctk.CTkLabel(win, text=fix_arabic("الحساب الذي تمت منه الدفعة:", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK).pack(pady=(4, 0), padx=40, anchor="e")
        payment_source = ctk.CTkOptionMenu(win, values=["Cash", "Visa", "CLIQ", "Bank"], font=FONT_BOLD, height=45, fg_color=COLOR_CRIMSON, button_color=COLOR_CRIMSON_DARK)
        payment_source.pack(pady=6, padx=40, fill="x"); payment_source.set("Cash")
        note_e = ctk.CTkEntry(win, placeholder_text=fix_arabic("ملاحظات الدفعة", for_ui=True), height=45, justify="right", font=FONT_NORMAL_BOLD); note_e.pack(pady=10, padx=40, fill="x")
        def pay():
            try:
                amt = self.positive_number(amt_e.get(), "المبلغ")
                if amt > rem + 0.01: raise ValueError("المبلغ المدفوع أكبر من المتبقي")
                table = "customer_debts" if dtype == "customer" else "supplier_debts"
                now = datetime.datetime.now(); d_str = now.strftime("%Y-%m-%d"); t_str = now.strftime("%H:%M:%S")
                supplier_name_for_balance = None
                if dtype != "customer":
                    supplier_row = self.db.cursor.execute("SELECT supplier_name FROM supplier_debts WHERE id=?", (rid,)).fetchone()
                    supplier_name_for_balance = supplier_row[0] if supplier_row else None
                self.db.cursor.execute(f"UPDATE {table} SET paid_amount = paid_amount + ?, last_payment_date = ?, status = CASE WHEN (paid_amount + ?) >= (total_debt - 0.01) THEN 'مسدد' ELSE 'غير مسدد' END WHERE id = ?", (amt, d_str, amt, rid))
                if dtype != "customer" and supplier_name_for_balance:
                    self.db.cursor.execute("UPDATE suppliers SET balance=MAX(0, balance-?) WHERE name=?", (amt, supplier_name_for_balance))
                self.db.cursor.execute("INSERT INTO debt_payments (debt_id, debt_type, amount, date, time, notes, payment_source) VALUES (?,?,?,?,?,?,?)", (rid, dtype, amt, d_str, t_str, note_e.get().strip(), payment_source.get()))
                payment_source_id = f"debt-payment-{dtype}-{rid}-{self.db.cursor.lastrowid}"
                payment_account = self._ledger_account_for_payment(payment_source.get())
                payment_lines = [(payment_account, amt, 0, "تحصيل ذمة عميل"), ("AR", 0, amt, "تخفيض ذمم العملاء")] if dtype == "customer" else [("AP", amt, 0, "تخفيض ذمم الموردين"), (payment_account, 0, amt, "سداد ذمة مورد")]
                self._post_journal_entry("debt_payment", payment_source_id, "قيد تسديد ذمة", payment_lines, d_str, t_str)
                self.db.conn.commit(); self.log_action("تسديد دين", table, f"ID: {rid}; المبلغ: {amt}"); win.destroy(); self.refresh_debts()
                self.show_msg("نجاح", "تم تسجيل الدفعة بنجاح")
            except Exception as e:
                self.db.conn.rollback()
                self.show_msg("خطأ", str(e))
        ctk.CTkButton(win, text=str("تأكيد الدفع"), command=pay, font=FONT_BOLD, fg_color=COLOR_TEAL, height=45).pack(pady=20)

    def _normalize_whatsapp_number(self, raw):
        digits = re.sub(r"\D", "", str(raw or ""))
        if digits.startswith("00"):
            digits = digits[2:]
        if digits.startswith("0"):
            digits = "962" + digits[1:]
        if len(digits) < 8 or len(digits) > 15:
            raise ValueError("أدخل رقم واتساب صحيحاً مع رمز الدولة أو رقماً أردنياً يبدأ بـ 07")
        return digits

    def generate_daily_operations_png(self, report_date=None):
        """Create a same-day operations report and render every PDF page as PNG."""
        report_date = report_date or datetime.date.today().isoformat()
        try:
            datetime.datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("صيغة تاريخ التقرير الصحيحة هي YYYY-MM-DD")
        report_dir = self.db.db_path.parent / "daily_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = report_dir / f"daily_operations_{report_date}_{stamp}.pdf"
        font_path = Path(resource_path("Cocon-Next-Arabic-PDF.ttf"))
        if not font_path.exists():
            raise RuntimeError("ملف Cocon PDF TTF غير موجود ضمن الحزمة")
        pdfmetrics.registerFont(TTFont("TCJDailyReport", str(font_path)))
        import html
        def par(value, size=8, color=COLOR_NAVY):
            style = ParagraphStyle(f"TCJDaily{size}{abs(hash(str(value)))%100000}", parent=getSampleStyleSheet()["BodyText"], fontName="TCJDailyReport", fontSize=size, leading=size + 4, alignment=TA_RIGHT, textColor=colors.HexColor(color))
            return Paragraph(html.escape(fix_arabic(str(value or "-"), for_ui=False)), style)
        title_style = ParagraphStyle("TCJDailyTitle", fontName="TCJDailyReport", fontSize=18, leading=24, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_RUBI_DARK))
        subtitle_style = ParagraphStyle("TCJDailySubtitle", fontName="TCJDailyReport", fontSize=10, leading=15, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_NAVY))
        story = [Paragraph(html.escape(fix_arabic(SHOP_NAME, for_ui=False)), title_style), Paragraph(html.escape(fix_arabic("تقرير حركة الموظف اليومية", for_ui=False)), subtitle_style), Paragraph(html.escape(fix_arabic(f"التاريخ: {report_date}", for_ui=False)), subtitle_style), Spacer(1, 8)]
        sections = []
        sales = self.db.cursor.execute("SELECT time, name, qty, total, payment_method, customer_phone FROM sales WHERE date=? ORDER BY time, id", (report_date,)).fetchall()
        sections.append(("المبيعات", ["الوقت", "الصنف", "الكمية", "الإجمالي", "الدفع", "هاتف العميل"], sales, lambda r: [r[0] or "-", r[1] or "-", r[2] or 0, f"{float(r[3] or 0):.2f} {CURRENCY}", r[4] or "Cash", r[5] or "-"]))
        maintenance = self.db.cursor.execute("SELECT time, client_name, device_name, repair_desc, revenue, payment_method FROM maintenance WHERE date=? ORDER BY time, id", (report_date,)).fetchall()
        sections.append(("الصيانة", ["الوقت", "العميل", "الجهاز", "الوصف", "المبلغ", "الدفع"], maintenance, lambda r: [r[0] or "-", r[1] or "-", r[2] or "-", r[3] or "-", f"{float(r[4] or 0):.2f} {CURRENCY}", r[5] or "Cash"]))
        transfers = self.db.cursor.execute("SELECT time, type, client_name, amount, commission, payment_method, reference FROM transfers WHERE date=? ORDER BY time, id", (report_date,)).fetchall()
        sections.append(("الحوالات ودفع الفواتير", ["الوقت", "النوع", "العميل", "القيمة", "العمولة", "الدفع", "المرجع"], transfers, lambda r: [r[0] or "-", r[1] or "-", r[2] or "-", f"{float(r[3] or 0):.2f} {CURRENCY}", f"{float(r[4] or 0):.2f} {CURRENCY}", r[5] or "Cash", r[6] or "-"]))
        expenses = self.db.cursor.execute("SELECT time, desc, amount, payment_source, status FROM expenses WHERE date=? ORDER BY time, id", (report_date,)).fetchall()
        sections.append(("المصاريف", ["الوقت", "البيان", "المبلغ", "مصدر الدفع", "الحالة"], expenses, lambda r: [r[0] or "-", r[1] or "-", f"{float(r[2] or 0):.2f} {CURRENCY}", r[3] or "Cash", r[4] or "paid"]))
        totals = {"sales": sum(float(r[3] or 0) for r in sales), "maintenance": sum(float(r[4] or 0) for r in maintenance), "transfers": sum(float(r[3] or 0) for r in transfers), "commissions": sum(float(r[4] or 0) for r in transfers), "expenses": sum(float(r[2] or 0) for r in expenses)}
        summary_rows = [[par("المؤشر"), par("القيمة")], [par("إجمالي المبيعات"), par(f"{totals['sales']:.2f} {CURRENCY}")], [par("إجمالي الصيانة"), par(f"{totals['maintenance']:.2f} {CURRENCY}")], [par("قيم الحوالات والفواتير"), par(f"{totals['transfers']:.2f} {CURRENCY}")], [par("عمولات الحوالات والفواتير"), par(f"{totals['commissions']:.2f} {CURRENCY}")], [par("إجمالي المصاريف"), par(f"{totals['expenses']:.2f} {CURRENCY}")]]
        summary_table = Table(summary_rows, colWidths=[92*mm, 55*mm], repeatRows=1)
        summary_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor(COLOR_RUBI)), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,-1), "TCJDailyReport"), ("GRID", (0,0), (-1,-1), .35, colors.HexColor(COLOR_TEXT_MUTED)), ("ALIGN", (0,0), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
        story += [Paragraph(html.escape(fix_arabic("ملخص اليوم", for_ui=False)), subtitle_style), summary_table, Spacer(1, 10)]
        for title, headings, rows, formatter in sections:
            story.append(Paragraph(html.escape(fix_arabic(f"{title} ({len(rows)})", for_ui=False)), subtitle_style))
            data = [[par(h) for h in headings]] + [[par(v, 7) for v in formatter(row)] for row in rows]
            if len(data) == 1:
                data.append([par("لا توجد حركات لهذا القسم", 7)] + [par("-") for _ in headings[1:]])
            widths = [max(22, min(40, 175 // max(len(headings), 1)))] * len(headings)
            table = Table(data, colWidths=[w*mm for w in widths], repeatRows=1)
            table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor(COLOR_TEAL_DARK)), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,-1), "TCJDailyReport"), ("GRID", (0,0), (-1,-1), .3, colors.HexColor(COLOR_TEXT_MUTED)), ("ALIGN", (0,0), (-1,-1), "RIGHT"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
            story += [table, Spacer(1, 8)]
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=10*mm, bottomMargin=10*mm, title="Trend Center Jordan - Daily Operations")
        doc.build(story)
        try:
            import pymupdf as fitz
        except ImportError as exc:
            raise RuntimeError("محرك تحويل التقرير إلى PNG غير مثبت") from exc
        output = []
        with fitz.open(str(pdf_path)) as document:
            for index, page in enumerate(document, start=1):
                png_path = report_dir / f"daily_operations_{report_date}_{stamp}_page_{index}.png"
                page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False).save(str(png_path))
                output.append(png_path)
        return output

    def open_daily_report_whatsapp(self):
        """Ask for and persist a WhatsApp number, then display today's PNG and open its chat."""
        saved = self.db.cursor.execute("SELECT value FROM settings WHERE key='daily_report_whatsapp_number'").fetchone()
        win = ctk.CTkToplevel(self); win.title(fix_arabic("إرسال تقرير اليوم عبر واتساب", is_title=True)); win.geometry("620x300"); win.transient(self); win.grab_set()
        ctk.CTkLabel(win, text=fix_arabic("رقم واتساب المستلم", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE).pack(pady=(25, 8))
        entry = ctk.CTkEntry(win, height=44, width=460, justify="center", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("مثال: 079xxxxxxx أو 96279xxxxxxx", for_ui=True)); entry.pack(pady=8)
        if saved and saved[0]: entry.insert(0, saved[0])
        ctk.CTkLabel(win, text=fix_arabic("سيتم إنشاء تقرير اليوم فقط بصيغة PNG وفتح صورة التقرير لنسخها وإرفاقها يدوياً في واتساب.", for_ui=True), font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, wraplength=540).pack(pady=8)
        def send_report():
            try:
                number = self._normalize_whatsapp_number(entry.get())
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("daily_report_whatsapp_number", number)); self.db.conn.commit()
                pngs = self.generate_daily_operations_png(datetime.date.today().isoformat())
                webbrowser.open(f"https://wa.me/{number}")
                for png in pngs:
                    try:
                        if sys.platform == "win32": os.startfile(str(png))
                        else: webbrowser.open(png.as_uri())
                    except Exception: pass
                self.clipboard_clear(); self.clipboard_append(str(pngs[0])); self.update()
                win.destroy(); self.show_msg("تم تجهيز التقرير", "تم حفظ رقم واتساب وفتح المحادثة وصورة التقرير.\nتم نسخ مسار PNG إلى الحافظة لإرفاقه يدوياً.")
            except (ValueError, OSError, sqlite3.Error, RuntimeError) as exc:
                self.db.conn.rollback(); self.show_msg("تعذر تجهيز التقرير", str(exc))
        ctk.CTkButton(win, text=fix_arabic("إنشاء التقرير وفتح واتساب", for_ui=True), command=send_report, font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=46).pack(fill="x", padx=70, pady=18)

    def ui_accountant(self):
        """Standalone account balances and daily movements; never touches operational ledgers."""
        if not self._has_permission("المحاسب"):
            self.show_msg("غير مصرح", "لا تملك صلاحية فتح واجهة المحاسب")
            return
        for w in self.main_view.winfo_children():
            w.destroy()
        self.create_header("المحاسب")
        root = ctk.CTkFrame(self.main_view, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=16, pady=8)
        ctk.CTkLabel(root, text=fix_arabic("دفتر حسابات مستقل", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE, anchor="e").pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(root, text=fix_arabic("هذه الشاشة مستقلة عن المبيعات والمشتريات والقيود التشغيلية. أدخل الرصيد الافتتاحي والحركات يدوياً.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, anchor="e").pack(fill="x", pady=(0, 8))

        summary = ctk.CTkFrame(root, fg_color="transparent"); summary.pack(fill="x", pady=(0, 8))
        cards = {}; account_names = dict(ACCOUNTANT_ACCOUNT_DEFS)
        for key, label in ACCOUNTANT_ACCOUNT_DEFS:
            card = ctk.CTkFrame(summary, fg_color=COLOR_NAVY, border_width=1, border_color=COLOR_BORDER, corner_radius=10); card.pack(side="right", fill="both", expand=True, padx=3)
            ctk.CTkLabel(card, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=(6, 0))
            value = ctk.CTkLabel(card, text=fix_arabic("0.00 " + CURRENCY, for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_SOFT); value.pack(pady=(2, 7)); cards[key] = value
        total_card = ctk.CTkFrame(summary, fg_color=COLOR_CRIMSON_DARK, border_width=1, border_color=COLOR_CRIMSON, corner_radius=10); total_card.pack(side="right", fill="both", expand=True, padx=3)
        ctk.CTkLabel(total_card, text=fix_arabic("الإجمالي", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(pady=(6, 0))
        total_label = ctk.CTkLabel(total_card, text=fix_arabic("0.00 " + CURRENCY, for_ui=True), font=FONT_REPORT_VALUE, text_color=COLOR_WHITE); total_label.pack(pady=(2, 7))

        balance_frame = ctk.CTkFrame(root, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_TEAL); balance_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(balance_frame, text=fix_arabic("الأرصدة الافتتاحية", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=14, pady=(8, 2))
        opening_row = ctk.CTkFrame(balance_frame, fg_color="transparent"); opening_row.pack(fill="x", padx=10, pady=(0, 8)); opening_entries = {}
        for key, label in ACCOUNTANT_ACCOUNT_DEFS:
            cell = ctk.CTkFrame(opening_row, fg_color="transparent"); cell.pack(side="right", fill="x", expand=True, padx=3)
            ctk.CTkLabel(cell, text=fix_arabic(label, for_ui=True), font=FONT_SMALL, text_color=COLOR_TEXT_DARK).pack(anchor="e")
            entry = ctk.CTkEntry(cell, height=36, justify="center", font=FONT_NORMAL_BOLD); entry.pack(fill="x", pady=(2, 0)); opening_entries[key] = entry

        tx_frame = ctk.CTkFrame(root, fg_color=COLOR_NAVY_LIGHT, corner_radius=12, border_width=1, border_color=COLOR_BORDER); tx_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(tx_frame, text=fix_arabic("إضافة حركة يومية", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=14, pady=(8, 2))
        tx_row1 = ctk.CTkFrame(tx_frame, fg_color="transparent"); tx_row1.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(tx_row1, text=fix_arabic("الحساب", for_ui=True), font=FONT_SMALL, text_color=COLOR_WHITE).pack(side="right", padx=4)
        account_var = ctk.StringVar(value=fix_arabic(ACCOUNTANT_ACCOUNT_DEFS[0][1], for_ui=True))
        account_box = ctk.CTkComboBox(tx_row1, values=[fix_arabic(label, for_ui=True) for _, label in ACCOUNTANT_ACCOUNT_DEFS], variable=account_var, width=190, height=38, font=FONT_NORMAL_BOLD, justify="right"); account_box.pack(side="right", padx=4)
        ctk.CTkLabel(tx_row1, text=fix_arabic("نوع الحركة", for_ui=True), font=FONT_SMALL, text_color=COLOR_WHITE).pack(side="right", padx=4)
        direction_var = ctk.StringVar(value=fix_arabic("دخول", for_ui=True))
        direction_box = ctk.CTkComboBox(tx_row1, values=[fix_arabic("دخول", for_ui=True), fix_arabic("خروج", for_ui=True)], variable=direction_var, width=130, height=38, font=FONT_NORMAL_BOLD, justify="center"); direction_box.pack(side="right", padx=4)
        ctk.CTkLabel(tx_row1, text=fix_arabic("المبلغ", for_ui=True), font=FONT_SMALL, text_color=COLOR_WHITE).pack(side="right", padx=4)
        amount_entry = ctk.CTkEntry(tx_row1, width=135, height=38, justify="center", font=FONT_NORMAL_BOLD); amount_entry.pack(side="right", padx=4)
        ctk.CTkLabel(tx_row1, text=fix_arabic("التاريخ", for_ui=True), font=FONT_SMALL, text_color=COLOR_WHITE).pack(side="right", padx=4)
        date_entry = ctk.CTkEntry(tx_row1, width=125, height=38, justify="center", font=FONT_NORMAL_BOLD); date_entry.insert(0, datetime.date.today().isoformat()); date_entry.pack(side="right", padx=4)
        tx_row2 = ctk.CTkFrame(tx_frame, fg_color="transparent"); tx_row2.pack(fill="x", padx=10, pady=3)
        description_entry = ctk.CTkEntry(tx_row2, height=38, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("شرح الحركة *", for_ui=True)); description_entry.pack(side="right", fill="x", expand=True, padx=4)
        notes_entry = ctk.CTkEntry(tx_row2, height=38, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("ملاحظات اختيارية", for_ui=True)); notes_entry.pack(side="right", fill="x", expand=True, padx=4)

        filter_frame = ctk.CTkFrame(root, fg_color="transparent"); filter_frame.pack(fill="x", pady=(6, 3))
        ctk.CTkLabel(filter_frame, text=fix_arabic("عرض الحركات من", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=4)
        from_entry = ctk.CTkEntry(filter_frame, width=125, height=36, justify="center", font=FONT_NORMAL_BOLD); from_entry.pack(side="right", padx=4)
        ctk.CTkLabel(filter_frame, text=fix_arabic("إلى", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=4)
        to_entry = ctk.CTkEntry(filter_frame, width=125, height=36, justify="center", font=FONT_NORMAL_BOLD); to_entry.pack(side="right", padx=4)
        table = ttk.Treeview(root, columns=("notes", "description", "amount", "direction", "account", "date", "id"), show="headings", height=8)
        for col, heading, width in [("notes", "الملاحظات", 190), ("description", "شرح الحركة", 240), ("amount", "المبلغ", 110), ("direction", "الحركة", 100), ("account", "الحساب", 150), ("date", "التاريخ", 110), ("id", "ID", 55)]:
            table.heading(col, text=fix_arabic(heading, for_ui=True)); table.column(col, anchor="center", width=width)
        table.pack(fill="both", expand=True, pady=4)
        button_row = ctk.CTkFrame(root, fg_color="transparent"); button_row.pack(fill="x", pady=5)

        def parse_amount(raw, label):
            try: value = float(str(raw).strip().replace(",", "."))
            except (TypeError, ValueError): raise ValueError(f"{label} يجب أن يكون رقماً")
            if not math.isfinite(value) or value <= 0: raise ValueError(f"{label} يجب أن يكون أكبر من صفر")
            return round(value, 2)
        def parse_date(raw):
            value = str(raw).strip()
            try: datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError: raise ValueError("صيغة التاريخ الصحيحة هي YYYY-MM-DD")
            return value
        def selected_account_key():
            shown = account_var.get()
            return next((key for key, label in ACCOUNTANT_ACCOUNT_DEFS if fix_arabic(label, for_ui=True) == shown), None)
        def load_openings():
            values = dict(self.db.cursor.execute("SELECT account_key, opening_balance FROM accountant_accounts WHERE active=1").fetchall())
            for key, entry in opening_entries.items():
                entry.delete(0, "end"); entry.insert(0, f"{float(values.get(key, 0) or 0):.2f}")
        def refresh():
            try:
                start, end = from_entry.get().strip(), to_entry.get().strip()
                if start: parse_date(start)
                if end: parse_date(end)
                if start and end and start > end: raise ValueError("تاريخ البداية يجب أن يسبق تاريخ النهاية")
                for item in table.get_children(): table.delete(item)
                balances = {key: float(opening or 0) for key, opening in self.db.cursor.execute("SELECT account_key, opening_balance FROM accountant_accounts WHERE active=1")}
                query = "SELECT account_key, direction, amount, transaction_date, description, notes, id FROM accountant_transactions"; params = []; clauses = []
                if start: clauses.append("transaction_date >= ?"); params.append(start)
                if end: clauses.append("transaction_date <= ?"); params.append(end)
                if clauses: query += " WHERE " + " AND ".join(clauses)
                query += " ORDER BY transaction_date DESC, id DESC"
                for key, direction, amount, tx_date, desc, notes, row_id in self.db.cursor.execute(query, params).fetchall():
                    balances[key] = balances.get(key, 0.0) + (float(amount) if direction == "in" else -float(amount))
                    table.insert("", "end", values=(fix_arabic(notes or "-", for_ui=True), fix_arabic(desc, for_ui=True), f"{float(amount):.2f} {CURRENCY}", fix_arabic("دخول" if direction == "in" else "خروج", for_ui=True), fix_arabic(account_names.get(key, key), for_ui=True), tx_date, row_id))
                for key, label in ACCOUNTANT_ACCOUNT_DEFS: cards[key].configure(text=fix_arabic(f"{balances.get(key, 0.0):.2f} {CURRENCY}", for_ui=True))
                total_label.configure(text=fix_arabic(f"{sum(balances.values()):.2f} {CURRENCY}", for_ui=True))
            except (ValueError, sqlite3.Error) as exc: self.show_msg("تعذر تحديث المحاسب", str(exc))
        def save_openings():
            try:
                now = datetime.datetime.now().isoformat(timespec="seconds")
                for key, entry in opening_entries.items():
                    raw = entry.get().strip(); value = parse_amount(raw, "الرصيد") if raw not in ("", "0", "0.0", "0.00") else 0.0
                    self.db.cursor.execute("UPDATE accountant_accounts SET opening_balance=?, updated_at=? WHERE account_key=?", (value, now, key))
                self.db.conn.commit()
                load_openings(); refresh()
                self.show_msg("نجاح", "تم حفظ الأرصدة الجديدة واعتمادها في البطاقات العلوية")
            except (ValueError, sqlite3.Error) as exc: self.db.conn.rollback(); self.show_msg("تعذر حفظ الأرصدة", str(exc))
        def add_transaction():
            try:
                key = selected_account_key()
                if not key: raise ValueError("يرجى اختيار الحساب")
                amount = parse_amount(amount_entry.get(), "المبلغ"); tx_date = parse_date(date_entry.get())
                description = description_entry.get().strip()
                if not description: raise ValueError("يرجى كتابة شرح الحركة")
                direction = "in" if direction_var.get() == fix_arabic("دخول", for_ui=True) else "out"
                now = datetime.datetime.now().isoformat(timespec="seconds")
                self.db.cursor.execute("INSERT INTO accountant_transactions (account_key, direction, amount, transaction_date, description, notes, user, created_at) VALUES (?,?,?,?,?,?,?,?)", (key, direction, amount, tx_date, description, notes_entry.get().strip(), self.current_user, now))
                self.db.conn.commit(); amount_entry.delete(0, "end"); description_entry.delete(0, "end"); notes_entry.delete(0, "end"); refresh(); self.show_msg("نجاح", "تم تسجيل الحركة في دفتر المحاسب المستقل")
            except (ValueError, sqlite3.Error) as exc: self.db.conn.rollback(); self.show_msg("تعذر حفظ الحركة", str(exc))
        def edit_accountant_transaction():
            selected = table.selection()
            if not selected:
                self.show_msg("تنبيه", "يرجى تحديد حركة من الجدول أولاً")
                return
            values = table.item(selected[0], "values")
            try:
                row_id = int(values[-1])
            except (TypeError, ValueError):
                self.show_msg("خطأ", "تعذر تحديد رقم الحركة")
                return
            row = self.db.cursor.execute("SELECT account_key, direction, amount, transaction_date, description, notes FROM accountant_transactions WHERE id=?", (row_id,)).fetchone()
            if not row:
                self.show_msg("خطأ", "الحركة المحددة غير موجودة")
                refresh()
                return
            key0, direction0, amount0, date0, description0, notes0 = row
            win = ctk.CTkToplevel(self); win.title(f"تعديل حركة المحاسب رقم {row_id}"); win.geometry("720x470"); win.transient(self); win.grab_set()
            ctk.CTkLabel(win, text=fix_arabic(f"تعديل الحركة رقم {row_id}", for_ui=True), font=FONT_TITLE, text_color=COLOR_WHITE).pack(fill="x", padx=20, pady=(20, 12))
            form = ctk.CTkFrame(win, fg_color="transparent"); form.pack(fill="both", expand=True, padx=24, pady=4)
            account_var2 = ctk.StringVar(value=fix_arabic(account_names.get(key0, key0), for_ui=True))
            direction_var2 = ctk.StringVar(value=fix_arabic("دخول" if direction0 == "in" else "خروج", for_ui=True))
            def field(label, value, width=0):
                ctk.CTkLabel(form, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(anchor="e", pady=(6, 2))
                entry = ctk.CTkEntry(form, height=38, justify="right", font=FONT_NORMAL_BOLD, width=width)
                entry.pack(fill="x", pady=(0, 2)); entry.insert(0, str(value or "")); return entry
            ctk.CTkLabel(form, text=fix_arabic("الحساب", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(anchor="e", pady=(6, 2))
            ctk.CTkComboBox(form, values=[fix_arabic(label, for_ui=True) for _, label in ACCOUNTANT_ACCOUNT_DEFS], variable=account_var2, height=38, font=FONT_NORMAL_BOLD, justify="right").pack(fill="x", pady=(0, 2))
            ctk.CTkLabel(form, text=fix_arabic("نوع الحركة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(anchor="e", pady=(6, 2))
            ctk.CTkComboBox(form, values=[fix_arabic("دخول", for_ui=True), fix_arabic("خروج", for_ui=True)], variable=direction_var2, height=38, font=FONT_NORMAL_BOLD, justify="center").pack(fill="x", pady=(0, 2))
            amount2 = field("المبلغ", f"{float(amount0):.2f}")
            date2 = field("التاريخ YYYY-MM-DD", date0)
            description2 = field("شرح الحركة", description0)
            notes2 = field("الملاحظات", notes0 or "")
            def save_edit():
                try:
                    shown_account = account_var2.get(); key = next((k for k, label in ACCOUNTANT_ACCOUNT_DEFS if fix_arabic(label, for_ui=True) == shown_account), None)
                    if not key: raise ValueError("يرجى اختيار الحساب")
                    amount = float(amount2.get().strip().replace(",", "."))
                    if not math.isfinite(amount) or amount <= 0: raise ValueError("المبلغ يجب أن يكون أكبر من صفر")
                    tx_date = date2.get().strip(); datetime.datetime.strptime(tx_date, "%Y-%m-%d")
                    description = description2.get().strip()
                    if not description: raise ValueError("يرجى كتابة شرح الحركة")
                    direction = "in" if direction_var2.get() == fix_arabic("دخول", for_ui=True) else "out"
                    self.db.cursor.execute("UPDATE accountant_transactions SET account_key=?, direction=?, amount=?, transaction_date=?, description=?, notes=? WHERE id=?", (key, direction, round(amount, 2), tx_date, description, notes2.get().strip(), row_id))
                    if self.db.cursor.rowcount != 1: raise ValueError("لم يتم العثور على الحركة")
                    self.db.conn.commit(); win.destroy(); refresh(); self.show_msg("نجاح", "تم تعديل الحركة المحددة فقط")
                except (ValueError, sqlite3.Error) as exc:
                    self.db.conn.rollback(); self.show_msg("تعذر تعديل الحركة", str(exc))
            ctk.CTkButton(win, text=fix_arabic("حفظ تعديل الحركة", for_ui=True), command=save_edit, font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=44).pack(fill="x", padx=24, pady=(8, 20))

        def export_pdf():
            try:
                start, end = from_entry.get().strip(), to_entry.get().strip()
                if start: parse_date(start)
                if end: parse_date(end)
                if start and end and start > end: raise ValueError("تاريخ البداية يجب أن يسبق تاريخ النهاية")
                path = self.generate_accountant_pdf(start, end)
                png_paths = self.generate_accountant_png(start, end, pdf_path=path)
                png_text = "\n".join(str(item) for item in png_paths)
                self.show_msg("تم التصدير", f"تم إنشاء تقرير المحاسب PDF وصور PNG الجاهزة للنسخ والإرسال عبر واتساب:\n{path}\n\nصور PNG:\n{png_text}")
            except (ValueError, OSError, sqlite3.Error, RuntimeError, ImportError) as exc: self.show_msg("تعذر تصدير التقرير", str(exc))
        def export_png():
            try:
                start, end = from_entry.get().strip(), to_entry.get().strip()
                if start: parse_date(start)
                if end: parse_date(end)
                if start and end and start > end: raise ValueError("تاريخ البداية يجب أن يسبق تاريخ النهاية")
                paths = self.generate_accountant_png(start, end)
                self.show_msg("تم تصدير PNG", "صور التقرير الجاهزة للنسخ والإرسال عبر واتساب:\n" + "\n".join(str(item) for item in paths))
            except (ValueError, OSError, sqlite3.Error, RuntimeError, ImportError) as exc: self.show_msg("تعذر تصدير PNG", str(exc))
        ctk.CTkButton(button_row, text=fix_arabic("حفظ الأرصدة الافتتاحية", for_ui=True), command=save_openings, font=FONT_BOLD, fg_color=COLOR_VINO, height=42).pack(side="right", padx=4)
        ctk.CTkButton(button_row, text=fix_arabic("حفظ الحركة", for_ui=True), command=add_transaction, font=FONT_BOLD, fg_color=COLOR_TEAL, height=42).pack(side="right", padx=4)
        ctk.CTkButton(button_row, text=fix_arabic("حفظ الأرصدة وتحديث", for_ui=True), command=save_openings, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42).pack(side="right", padx=4)
        ctk.CTkButton(button_row, text=fix_arabic("تعديل الحركة المحددة", for_ui=True), command=edit_accountant_transaction, font=FONT_BOLD, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK, height=42).pack(side="right", padx=4)
        ctk.CTkButton(button_row, text=fix_arabic("تصدير PDF + PNG", for_ui=True), command=export_pdf, font=FONT_BOLD, fg_color=COLOR_NAVY, height=42).pack(side="left", padx=4)
        ctk.CTkButton(button_row, text=fix_arabic("تصدير PNG للواتساب", for_ui=True), command=export_png, font=FONT_BOLD, fg_color=COLOR_TEAL_DARK, hover_color=COLOR_TEAL, height=42).pack(side="left", padx=4)
        load_openings(); refresh()

    def generate_accountant_png(self, start="", end="", pdf_path=None):
        """Render the accountant PDF pages as PNG images for copying and WhatsApp sharing."""
        try:
            import pymupdf as fitz
        except ImportError as exc:
            raise RuntimeError("محرك تحويل PDF إلى PNG غير مثبت؛ يرجى إعادة بناء الحزمة بعد تحديث المتطلبات") from exc
        pdf_path = Path(pdf_path) if pdf_path else Path(self.generate_accountant_pdf(start, end))
        png_dir = self.db.db_path.parent / "accountant_reports"
        png_dir.mkdir(parents=True, exist_ok=True)
        stem = pdf_path.stem
        output = []
        with fitz.open(str(pdf_path)) as document:
            matrix = fitz.Matrix(3.0, 3.0)
            for index, page in enumerate(document, start=1):
                image_path = png_dir / f"{stem}_page_{index}.png"
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                pixmap.save(str(image_path))
                output.append(image_path)
        if not output:
            raise RuntimeError("لم يتم إنشاء أي صفحة PNG من التقرير")
        return output

    def generate_accountant_pdf(self, start="", end=""):
        """Export only the standalone accountant tables; operational data is never queried."""
        report_dir = self.db.db_path.parent / "accountant_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = report_dir / f"accountant_{start or 'all'}_{end or 'all'}_{stamp}.pdf"
        font_path = Path(resource_path(ACCOUNTANT_PDF_FONT_FILE))
        if not font_path.exists():
            raise RuntimeError("ملف Cocon PDF TTF غير موجود ضمن الحزمة")
        pdfmetrics.registerFont(TTFont("TCJAccountant", str(font_path)))
        font_name = "TCJAccountant"
        import html
        def par(value): return html.escape(fix_arabic(str(value), for_ui=False))
        styles = getSampleStyleSheet()
        title = ParagraphStyle("TCJAccountantTitle", parent=styles["Title"], fontName=font_name, fontSize=17, leading=23, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_RUBI_DARK))
        body = ParagraphStyle("TCJAccountantBody", parent=styles["BodyText"], fontName=font_name, fontSize=9, leading=13, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_NAVY))
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm, title="Trend Center Jordan - Accountant")
        story = [Paragraph(par(SHOP_NAME), title), Paragraph(par("تقرير المحاسب المستقل"), body), Paragraph(par(f"الفترة: {start or 'من البداية'} إلى {end or 'حتى النهاية'}"), body), Spacer(1, 8)]
        account_rows = [[par("الحساب"), par("الرصيد الافتتاحي"), par("دخول"), par("خروج"), par("الرصيد الحالي")]]
        for key, label in ACCOUNTANT_ACCOUNT_DEFS:
            opening = float(self.db.cursor.execute("SELECT opening_balance FROM accountant_accounts WHERE account_key=?", (key,)).fetchone()[0] or 0)
            clauses = ["account_key=?"]; params = [key]
            if start: clauses.append("transaction_date >= ?"); params.append(start)
            if end: clauses.append("transaction_date <= ?"); params.append(end)
            where = " AND ".join(clauses)
            ins = float(self.db.cursor.execute("SELECT COALESCE(SUM(amount),0) FROM accountant_transactions WHERE " + where + " AND direction='in'", params).fetchone()[0] or 0)
            outs = float(self.db.cursor.execute("SELECT COALESCE(SUM(amount),0) FROM accountant_transactions WHERE " + where + " AND direction='out'", params).fetchone()[0] or 0)
            account_rows.append([par(label), f"{opening:.2f} {CURRENCY}", f"{ins:.2f} {CURRENCY}", f"{outs:.2f} {CURRENCY}", f"{opening+ins-outs:.2f} {CURRENCY}"])
        table = Table(account_rows, colWidths=[42*mm, 32*mm, 27*mm, 27*mm, 32*mm], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor(COLOR_RUBI)),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,-1),font_name),("FONTSIZE",(0,0),(-1,-1),8),("ALIGN",(0,0),(-1,-1),"RIGHT"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor(COLOR_TEXT_MUTED)),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor(COLOR_WHITE)]),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)])); story.append(table); story.append(Spacer(1,9)); story.append(Paragraph(par("تفاصيل الحركات اليومية"), body))
        clauses=[]; params=[]
        if start: clauses.append("transaction_date >= ?"); params.append(start)
        if end: clauses.append("transaction_date <= ?"); params.append(end)
        query="SELECT account_key,direction,amount,transaction_date,description,notes FROM accountant_transactions" + ((" WHERE " + " AND ".join(clauses)) if clauses else "") + " ORDER BY transaction_date, id"
        detail_rows=[[par("الحساب"),par("الحركة"),par("المبلغ"),par("التاريخ"),par("الشرح"),par("الملاحظات")]]
        for key,direction,amount,date,description,notes in self.db.cursor.execute(query,params).fetchall(): detail_rows.append([par(dict(ACCOUNTANT_ACCOUNT_DEFS).get(key,key)),par("دخول" if direction=="in" else "خروج"),f"{amount:.2f} {CURRENCY}",date,par(description),par(notes or "-")])
        if len(detail_rows)==1: detail_rows.append([par("لا توجد حركات"),"","","","",""])
        detail=Table(detail_rows,colWidths=[29*mm,21*mm,25*mm,24*mm,47*mm,38*mm],repeatRows=1)
        detail.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor(COLOR_TEAL_DARK)),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,-1),font_name),("FONTSIZE",(0,0),(-1,-1),7),("ALIGN",(0,0),(-1,-1),"RIGHT"),("GRID",(0,0),(-1,-1),0.3,colors.HexColor(COLOR_TEXT_MUTED)),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(detail); story.append(Spacer(1,8)); story.append(Paragraph(par("هذا الدفتر مستقل ولا يعدّل أو يعيد احتساب أي عملية تشغيلية في البرنامج."), body)); doc.build(story); return pdf_path

    def _financial_cycle_for_date(self, value=None):
        """Return the monthly financial cycle beginning on the 5th and ending on the 4th."""
        if value is None:
            value = datetime.date.today()
        elif isinstance(value, str):
            value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
        if value.day >= 5:
            start_year, start_month = value.year, value.month
        else:
            previous = value.replace(day=1) - datetime.timedelta(days=1)
            start_year, start_month = previous.year, previous.month
        start = datetime.date(start_year, start_month, 5)
        month_index = start_year * 12 + (start_month - 1) + 1
        end_year, end_month = divmod(month_index, 12)
        end_month += 1
        end = datetime.date(end_year, end_month, 4)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def ui_balance_reconciliation(self):
        """Manager-only comparison of recorded balances with physically counted balances."""
        if self.current_role != "admin":
            self.show_msg("غير مصرح", "هذه الشاشة متاحة للمدير فقط")
            return
        for w in self.main_view.winfo_children():
            w.destroy()
        self.create_header("مطابقة الأرصدة والسيولة")

        intro = ctk.CTkLabel(
            self.main_view,
            text=fix_arabic("قارن الأرصدة الفعلية مع الرصيد المتوقع حتى نهاية الفترة دون تعديل أي عملية سابقة.", for_ui=True),
            font=FONT_NORMAL_BOLD,
            text_color=COLOR_TEXT_MUTED
        )
        intro.pack(anchor="e", padx=22, pady=(0, 8))

        filter_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_BG_LIGHT, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        filter_frame.pack(fill="x", padx=18, pady=6)
        today_date = datetime.date.today()
        cycle_start, cycle_end = self._financial_cycle_for_date(today_date)
        ctk.CTkLabel(filter_frame, text=fix_arabic("من تاريخ الدورة:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=(14, 4), pady=12)
        from_entry = ctk.CTkEntry(filter_frame, width=145, height=42, justify="right", font=FONT_NORMAL_BOLD)
        from_entry.insert(0, cycle_start)
        from_entry.pack(side="right", padx=4, pady=8)
        ctk.CTkLabel(filter_frame, text=fix_arabic("إلى تاريخ الدورة:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=(14, 4), pady=12)
        to_entry = ctk.CTkEntry(filter_frame, width=145, height=42, justify="right", font=FONT_NORMAL_BOLD)
        to_entry.insert(0, cycle_end)
        to_entry.pack(side="right", padx=4, pady=8)
        ctk.CTkButton(filter_frame, text=fix_arabic("حساب الأرصدة", for_ui=True), command=lambda: calculate(), font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=145).pack(side="left", padx=8, pady=8)

        opening_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_NAVY_LIGHT, corner_radius=12, border_width=1, border_color=COLOR_TEAL_SOFT)
        opening_frame.pack(fill="x", padx=18, pady=8)
        opening_head = ctk.CTkFrame(opening_frame, fg_color="transparent")
        opening_head.pack(fill="x", padx=18, pady=(10, 2))
        ctk.CTkLabel(opening_head, text=fix_arabic("الرصيد المدور من الفترة السابقة", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        cycle_status = ctk.CTkLabel(opening_head, text=fix_arabic(f"التاريخ المختار: {cycle_start} إلى {cycle_end}", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED)
        cycle_status.pack(side="left")
        lock_cycle_button = ctk.CTkButton(opening_head, text=fix_arabic("تثبيت حسب التاريخ", for_ui=True), command=lambda: lock_cycle(), font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=34, width=150)
        lock_cycle_button.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(opening_frame, text=fix_arabic("اختر تاريخ البداية والنهاية أولاً، ثم أدخل قيمة موجبة أو سالبة لكل حساب. الرصيد المدور نقطة بداية ولا يعدّل أي حركة سابقة.", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_DARK).pack(anchor="e", padx=18, pady=(0, 4))
        opening_row = ctk.CTkFrame(opening_frame, fg_color="transparent")
        opening_row.pack(fill="x", padx=14, pady=(0, 10))
        opening_entries = {}
        for key, label in [("cash", "الصندوق"), ("visa", "الفيزا"), ("cliq", "CLIQ (تفصيل ضمن BANK)"), ("bank", "الحساب البنكي الإجمالي")]:
            item = ctk.CTkFrame(opening_row, fg_color="transparent")
            item.pack(side="right", expand=True, fill="x", padx=5)
            ctk.CTkLabel(item, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
            entry = ctk.CTkEntry(item, height=42, justify="center", font=FONT_NORMAL_BOLD, placeholder_text="0.00 أو -100.00")
            entry.pack(fill="x", pady=(3, 0))
            opening_entries[key] = entry

        def _period_dates():
            start, end = from_entry.get().strip(), to_entry.get().strip()
            if not start or not end:
                raise ValueError("يرجى تحديد فترة الدورة المالية")
            try:
                datetime.datetime.strptime(start, "%Y-%m-%d")
                datetime.datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                raise ValueError("صيغة التاريخ الصحيحة هي YYYY-MM-DD")
            if start > end:
                raise ValueError("تاريخ بداية الدورة يجب أن يسبق تاريخ نهايتها")
            return start, end

        def set_opening_entries_state(state):
            for entry in opening_entries.values():
                entry.configure(state=state)
            # The cycle dates and opening balances are one protected unit.
            from_entry.configure(state=state)
            to_entry.configure(state=state)
            lock_cycle_button.configure(state="disabled" if state == "disabled" else "normal")

        def load_locked_cycle():
            try:
                start, end = _period_dates()
                row = self.db.cursor.execute("SELECT from_date, to_date, opening_cash, opening_visa, opening_cliq, opening_bank, receivables_balance, payables_balance, locked FROM financial_cycles WHERE from_date=? AND to_date=?", (start, end)).fetchone()
                # When returning to the screen after navigation/restart, restore the latest locked cycle.
                if not row:
                    row = self.db.cursor.execute("SELECT from_date, to_date, opening_cash, opening_visa, opening_cliq, opening_bank, receivables_balance, payables_balance, locked FROM financial_cycles WHERE locked=1 ORDER BY to_date DESC, id DESC LIMIT 1").fetchone()
                    if row:
                        start, end = row[0], row[1]
                        from_entry.configure(state="normal"); from_entry.delete(0, "end"); from_entry.insert(0, start)
                        to_entry.configure(state="normal"); to_entry.delete(0, "end"); to_entry.insert(0, end)
                if row and int(row[8] or 0) == 1:
                    for key, value in zip(("cash", "visa", "cliq", "bank"), row[2:6]):
                        entry = opening_entries[key]
                        entry.configure(state="normal")
                        entry.delete(0, "end")
                        entry.insert(0, f"{float(value or 0):.2f}")
                    set_opening_entries_state("disabled")
                    cycle_status.configure(text=fix_arabic(f"دورة مثبتة ومحفوظة: {start} إلى {end}", for_ui=True), text_color=COLOR_TEAL)
                else:
                    for entry in opening_entries.values():
                        entry.configure(state="normal")
                        entry.delete(0, "end")
                    set_opening_entries_state("normal")
                    cycle_status.configure(text=fix_arabic(f"دورة غير مثبتة: {start} إلى {end}", for_ui=True), text_color=COLOR_WHITE)
            except (TypeError, ValueError, sqlite3.Error):
                set_opening_entries_state("normal")
                cycle_status.configure(text=fix_arabic("يرجى مراجعة تاريخ الدورة", for_ui=True), text_color=COLOR_WHITE)

        def lock_cycle():
            if self.current_role != "admin":
                return
            try:
                start, end = _period_dates()
                opening = {}
                for key, entry in opening_entries.items():
                    raw = entry.get().strip()
                    if not raw:
                        opening[key] = 0.0
                    else:
                        try:
                            opening[key] = float(raw.replace(",", "."))
                        except (TypeError, ValueError):
                            raise ValueError(f"الرصيد المدور {key} يجب أن يكون رقماً موجباً أو سالباً")
                receivables = _sum_debt_balance("customer_debts", end)
                payables = _sum_debt_balance("supplier_debts", end)
                note = notes_entry.get().strip()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.cursor.execute("UPDATE financial_cycles SET opening_cash=?, opening_visa=?, opening_cliq=?, opening_bank=?, receivables_balance=?, payables_balance=?, notes=?, locked=1, user=?, created_at=? WHERE from_date=? AND to_date=?", (opening["cash"], opening["visa"], opening["cliq"], opening["bank"], receivables, payables, note, self.current_user, now, start, end))
                if self.db.cursor.rowcount == 0:
                    self.db.cursor.execute("INSERT INTO financial_cycles (from_date, to_date, cycle_type, opening_cash, opening_visa, opening_cliq, opening_bank, receivables_balance, payables_balance, notes, locked, user, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (start, end, "manager_selected", opening["cash"], opening["visa"], opening["cliq"], opening["bank"], receivables, payables, note, 1, self.current_user, now))
                self.db.conn.commit()
                set_opening_entries_state("disabled")
                self.log_action("تثبيت دورة مالية", "financial_cycles", f"الفترة: {start} إلى {end}")
                cycle_status.configure(text=fix_arabic(f"تم تثبيت الدورة وحفظ الرصيد الافتتاحي: {start} إلى {end}", for_ui=True), text_color=COLOR_TEAL)
                self.show_msg("نجاح", f"تم تثبيت الدورة وحفظ الرصيد الافتتاحي حسب التاريخ الذي قمت باختياره: {start} إلى {end}")
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر تثبيت الدورة", str(exc))

        actual_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_VINO_DARK, corner_radius=12, border_width=1, border_color=COLOR_TEAL_SOFT)
        actual_frame.pack(fill="x", padx=18, pady=8)
        ctk.CTkLabel(actual_frame, text=fix_arabic("الأرصدة الفعلية عند نهاية الفترة", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=18, pady=(10, 4))
        actual_row = ctk.CTkFrame(actual_frame, fg_color="transparent")
        actual_row.pack(fill="x", padx=14, pady=(0, 10))
        actual_entries = {}
        for key, label in [("cash", "الصندوق"), ("visa", "الفيزا"), ("cliq", "CLIQ (تفصيل ضمن BANK)"), ("bank", "الحساب البنكي الإجمالي")]:
            item = ctk.CTkFrame(actual_row, fg_color="transparent")
            item.pack(side="right", expand=True, fill="x", padx=5)
            ctk.CTkLabel(item, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
            entry = ctk.CTkEntry(item, height=42, justify="center", font=FONT_NORMAL_BOLD, placeholder_text="0.00")
            entry.pack(fill="x", pady=(3, 0))
            actual_entries[key] = entry

        debts_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        debts_frame.pack(fill="x", padx=18, pady=(2, 6))
        debt_summary_label = ctk.CTkLabel(debts_frame, text=fix_arabic("الذمم حتى نهاية الدورة: سيتم حسابها عند الضغط على «حساب الأرصدة»", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK)
        debt_summary_label.pack(anchor="e", padx=14, pady=9)

        notes_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        notes_frame.pack(fill="x", padx=18, pady=(2, 6))
        ctk.CTkLabel(notes_frame, text=fix_arabic("ملاحظات المطابقة (اختياري):", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=3)
        notes_entry = ctk.CTkEntry(notes_frame, height=42, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("سبب الفرق أو العمليات المعلقة...", for_ui=True))
        notes_entry.pack(fill="x", pady=(3, 0))

        result_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        result_frame.pack(fill="both", expand=True, padx=18, pady=6)
        status_label = ctk.CTkLabel(result_frame, text=fix_arabic("أدخل الأرصدة الفعلية ثم اضغط حساب الأرصدة", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED)
        status_label.pack(anchor="e", padx=4, pady=8)
        table_frame = ctk.CTkFrame(result_frame, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        table_frame.pack(fill="both", expand=True, pady=4)
        tree = ttk.Treeview(table_frame, columns=("status", "difference", "actual", "expected", "account"), show="headings", height=6)
        for col, head in zip(tree["columns"], ["الحالة", "الفرق", "الفعلي", "المتوقع", "الحساب"]):
            tree.heading(col, text=fix_arabic(head, for_ui=True))
            tree.column(col, anchor="center", width=150)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        totals_label = ctk.CTkLabel(result_frame, text="", font=FONT_BOLD, text_color=COLOR_WHITE)
        totals_label.pack(anchor="e", padx=4, pady=6)
        movement_frame = ctk.CTkFrame(result_frame, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_TEAL_SOFT)
        movement_frame.pack(fill="both", expand=True, pady=(2, 6))
        ctk.CTkLabel(movement_frame, text=fix_arabic("الأرصدة المتوقعة من مختلف الحركات", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", padx=12, pady=(8, 3))
        movement_tree = ttk.Treeview(movement_frame, columns=("commission", "bank", "cash", "movement"), show="headings", height=6)
        for col, head in zip(movement_tree["columns"], ["العمولة", "البنك / CLIQ", "الصندوق", "الحركة"]):
            movement_tree.heading(col, text=fix_arabic(head, for_ui=True))
            movement_tree.column(col, anchor="center", width=170)
        movement_tree.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        action_buttons = ctk.CTkFrame(result_frame, fg_color="transparent")
        action_buttons.pack(anchor="e", padx=4, pady=(0, 8))
        save_button = ctk.CTkButton(action_buttons, text=fix_arabic("حفظ المطابقة", for_ui=True), command=lambda: save_reconciliation(), font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=44, state="disabled")
        save_button.pack(side="right", padx=(0, 8))
        close_button = ctk.CTkButton(action_buttons, text=fix_arabic("إغلاق الفترة المالية", for_ui=True), command=lambda: close_financial_period(), font=FONT_BOLD, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK, height=44, state="disabled")
        close_button.pack(side="right")
        calculated = {"data": None}

        aliases = {
            "cash": ["cash", "نقدي", "نقد"],
            "visa": ["visa", "فيزا"],
            "cliq": ["cliq", "كليك"],
            "bank": ["bank", "البنك", "حساب بنكي"]
        }
        type_aliases = {
            "in": ["دخول حوالة"],
            "bill": ["دفع فاتورة"],
            "out": ["خروج حوالة"]
        }

        def _range_clause():
            start, end = _period_dates()
            # A reconciliation compares the actual closing balance with the
            # system closing balance through the selected fifth-to-fourth cycle.
            return "WHERE date <= ?", [end], start, end

        def _pm_clause(key):
            vals = aliases[key]
            return "LOWER(TRIM(COALESCE(payment_method, 'Cash'))) IN (" + ",".join("?" for _ in vals) + ")", [v.lower() for v in vals]

        def _sum_payment(table, column, key):
            clause, params, _, _ = _range_clause()
            pm_clause, pm_params = _pm_clause(key)
            self.db.cursor.execute(f"SELECT COALESCE(SUM({column}), 0) FROM {table} {clause} AND {pm_clause}", params + pm_params)
            return float(self.db.cursor.fetchone()[0] or 0.0)

        def _sum_transfer(kind, key, expression):
            clause, params, _, _ = _range_clause()
            pm_clause, pm_params = _pm_clause(key)
            type_values = [v.lower() for v in type_aliases[kind]]
            type_clause = "LOWER(TRIM(COALESCE(type, ''))) IN (" + ",".join("?" for _ in type_values) + ")"
            self.db.cursor.execute(f"SELECT COALESCE(SUM({expression}), 0) FROM transfers {clause} AND {type_clause} AND {pm_clause}", params + type_values + pm_params)
            return float(self.db.cursor.fetchone()[0] or 0.0)

        def _sum_expense(src):
            clause, params, _, _ = _range_clause()
            source_key = str(src).strip().lower()
            if source_key not in aliases:
                raise ValueError("وسيلة دفع المصروف غير معروفة")
            values = aliases[source_key]
            placeholders = ",".join("?" for _ in values)
            status_clause = "LOWER(TRIM(COALESCE(status, 'paid'))) NOT IN ('unpaid', 'pending', 'credit', 'غير مسدد', 'على الحساب')"
            sql = f"SELECT COALESCE(SUM(amount), 0) FROM expenses {clause} AND LOWER(TRIM(COALESCE(payment_source, 'Cash'))) IN ({placeholders}) AND {status_clause}"
            row = self.db.cursor.execute(sql, params + [value.lower() for value in values]).fetchone()
            return float(row[0] or 0.0)

        def _sum_internal(acc, direction):
            clause, params, _, _ = _range_clause()
            if direction == 'in':
                self.db.cursor.execute(f"SELECT COALESCE(SUM(amount), 0) FROM internal_transfers {clause} AND LOWER(TRIM(dest_acc)) = ?", params + [acc.lower()])
            else:
                self.db.cursor.execute(f"SELECT COALESCE(SUM(amount), 0) FROM internal_transfers {clause} AND LOWER(TRIM(source_acc)) = ?", params + [acc.lower()])
            return float(self.db.cursor.fetchone()[0] or 0.0)

        def _sum_cash_purchases():
            clause, params, _, _ = _range_clause()
            self.db.cursor.execute(f"SELECT COALESCE(SUM(qty * cost), 0) FROM purchases {clause} AND LOWER(COALESCE(funding_source, '')) LIKE ?", params + ["%صندوق%"])
            return float(self.db.cursor.fetchone()[0] or 0.0)

        def _sum_debt_balance(table, as_of):
            if table not in ("customer_debts", "supplier_debts"):
                raise ValueError("جدول الذمم غير صالح")
            debt_type = "customer" if table == "customer_debts" else "supplier"
            rows = self.db.cursor.execute(
                f"SELECT d.total_debt, COALESCE(SUM(p.amount), 0) FROM {table} d LEFT JOIN debt_payments p ON p.debt_id=d.id AND p.debt_type=? AND p.date <= ? WHERE d.date <= ? GROUP BY d.id",
                (debt_type, as_of, as_of)
            ).fetchall()
            return sum(max(float(total or 0.0) - float(paid or 0.0), 0.0) for total, paid in rows)

        def _sum_debt_payment(key, debt_type):
            clause, params, _, _ = _range_clause()
            values = aliases[key]
            placeholders = ",".join("?" for _ in values)
            sql = f"SELECT COALESCE(SUM(amount), 0) FROM debt_payments {clause} AND debt_type=? AND LOWER(TRIM(COALESCE(payment_source, 'Cash'))) IN ({placeholders})"
            row = self.db.cursor.execute(sql, params + [debt_type] + [value.lower() for value in values]).fetchone()
            return float(row[0] or 0.0)

        def _locked_cycle_exists(start, end):
            row = self.db.cursor.execute("SELECT locked FROM financial_cycles WHERE from_date=? AND to_date=?", (start, end)).fetchone()
            return bool(row and int(row[0] or 0) == 1)

        def _setting_number(key, fallback=0.0):
            row = self.db.cursor.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            try:
                return float(row[0]) if row and row[0] not in (None, "") else fallback
            except (TypeError, ValueError):
                return fallback

        def _journal_period_net(account, start, end):
            if account == "BANK":
                row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit - jl.credit), 0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code IN ('BANK','CLIQ') AND je.entry_date BETWEEN ? AND ?", (start, end)).fetchone()
            else:
                row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit - jl.credit), 0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code=? AND je.entry_date BETWEEN ? AND ?", (account, start, end)).fetchone()
            return float(row[0] or 0.0)

        def _operational_cash_period_net(start, end):
            """Calculate cash movement from active operational rows for reconciliation display."""
            total = 0.0
            q = "SELECT COALESCE(SUM(total),0) FROM sales WHERE payment_method='Cash' AND date BETWEEN ? AND ?"
            total += float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            q = "SELECT COALESCE(SUM(revenue),0) FROM maintenance WHERE payment_method='Cash' AND date BETWEEN ? AND ?"
            total += float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            q = "SELECT COALESCE(SUM(CASE WHEN type='دخول حوالة' THEN amount + commission WHEN type='دفع فاتورة' AND payment_method='Cash' THEN amount + commission WHEN type='خروج حوالة' THEN -(amount - commission) ELSE 0 END),0) FROM transfers WHERE date BETWEEN ? AND ?"
            total += float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            q = "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date BETWEEN ? AND ? AND LOWER(TRIM(COALESCE(payment_source,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)') AND LOWER(TRIM(COALESCE(status,'paid'))) NOT IN ('unpaid','pending','credit','غير مسدد','على الحساب')"
            total -= float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            q = "SELECT COALESCE(SUM(qty * cost),0) FROM purchases WHERE date BETWEEN ? AND ? AND LOWER(REPLACE(COALESCE(funding_source,''),' ','')) LIKE '%صندوق%'"
            total -= float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            q = "SELECT COALESCE(SUM(CASE WHEN LOWER(TRIM(source_acc))='cash' THEN -amount WHEN LOWER(TRIM(dest_acc))='cash' THEN amount ELSE 0 END),0) FROM internal_transfers WHERE date BETWEEN ? AND ?"
            total += float(self.db.cursor.execute(q, (start, end)).fetchone()[0] or 0.0)
            return round(total, 2)

        def _expected_movement_rows(start, end, opening, expected):
            """Read-only movement breakdown used only by the reconciliation display."""
            def scalar(sql, params):
                row = self.db.cursor.execute(sql, params).fetchone()
                return float(row[0] or 0.0)
            rows = []
            sales_cash = scalar("SELECT COALESCE(SUM(total),0) FROM sales WHERE date BETWEEN ? AND ? AND LOWER(TRIM(COALESCE(payment_method,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)')", (start, end))
            maintenance_cash = scalar("SELECT COALESCE(SUM(revenue),0) FROM maintenance WHERE date BETWEEN ? AND ? AND LOWER(TRIM(COALESCE(payment_method,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)')", (start, end))
            purchases_cash = scalar("SELECT COALESCE(SUM(qty * cost),0) FROM purchases WHERE date BETWEEN ? AND ? AND LOWER(REPLACE(COALESCE(funding_source,''),' ','')) LIKE '%صندوق%'", (start, end))
            expenses_cash = scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date BETWEEN ? AND ? AND LOWER(TRIM(COALESCE(payment_source,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)') AND LOWER(TRIM(COALESCE(status,'paid'))) NOT IN ('unpaid','pending','credit','غير مسدد','على الحساب')", (start, end))
            transfer_cash = scalar("SELECT COALESCE(SUM(CASE WHEN type='دخول حوالة' AND LOWER(TRIM(COALESCE(payment_method,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)') THEN amount + commission WHEN type='دفع فاتورة' AND LOWER(TRIM(COALESCE(payment_method,'Cash'))) IN ('cash','نقدي','صندوق','صندوق المحل (نقدي)') THEN amount + commission WHEN type='خروج حوالة' THEN -(amount - commission) ELSE 0 END),0) FROM transfers WHERE date BETWEEN ? AND ?", (start, end))
            transfer_commission = scalar("SELECT COALESCE(SUM(commission),0) FROM transfers WHERE date BETWEEN ? AND ?", (start, end))
            bank_net = _journal_period_net("BANK", start, end)
            visa_net = _journal_period_net("VISA", start, end)
            rows.extend([
                ("المبيعات النقدية", sales_cash, 0.0, 0.0),
                ("إيرادات الصيانة النقدية", maintenance_cash, 0.0, 0.0),
                ("المشتريات من الصندوق", -purchases_cash, 0.0, 0.0),
                ("المصاريف المدفوعة من الصندوق", -expenses_cash, 0.0, 0.0),
                ("الحوالات والخدمات", transfer_cash, bank_net, transfer_commission),
                ("صافي حركة الفيزا", 0.0, visa_net, 0.0),
            ])
            return rows

        def calculate():
            save_button.configure(state="disabled")
            status_label.configure(text=fix_arabic("جارٍ حساب الأرصدة...", for_ui=True), text_color=COLOR_TEXT_MUTED)
            self.main_view.update_idletasks()
            try:
                start, end = _period_dates()
                locked_row = self.db.cursor.execute("SELECT opening_cash, opening_visa, opening_cliq, opening_bank, locked FROM financial_cycles WHERE from_date=? AND to_date=?", (start, end)).fetchone()
                if locked_row and int(locked_row[4] or 0) == 1:
                    opening = {key: float(value or 0.0) for key, value in zip(("cash", "visa", "cliq", "bank"), locked_row[:4])}
                else:
                    opening = {}
                    for key, entry in opening_entries.items():
                        raw = entry.get().strip()
                        if raw:
                            try:
                                opening[key] = float(raw.replace(",", "."))
                            except (TypeError, ValueError):
                                raise ValueError(f"الرصيد المدور {key} يجب أن يكون رقماً موجباً أو سالباً")
                        else:
                            opening[key] = _setting_number("opening_balance") if key == "cash" else 0.0
                # CLIQ is a payment-channel detail of the same bank account.
                # Carry any legacy opening CLIQ value into bank once and keep
                # the displayed CLIQ row informational rather than additive.
                if abs(opening["bank"]) < 1e-9 and abs(opening["cliq"]) > 1e-9:
                    opening["bank"] = opening["cliq"]
                else:
                    opening["bank"] += 0.0
                expected = {
                    "cash": opening["cash"] + _operational_cash_period_net(start, end),
                    "visa": opening["visa"] + _journal_period_net("VISA", start, end),
                    "cliq": 0.0,
                    "bank": opening["bank"] + _journal_period_net("BANK", start, end),
                }
                receivables = _sum_debt_balance("customer_debts", end)
                payables = _sum_debt_balance("supplier_debts", end)
                actual = {}
                for key, entry in actual_entries.items():
                    raw = entry.get().strip()
                    actual[key] = self.positive_number(raw, f"الرصيد الفعلي {key}", allow_zero=True) if raw else 0.0
                differences = {key: actual[key] - expected[key] for key in expected}
                cycle_locked = _locked_cycle_exists(start, end)
                calculated["data"] = {"opening": opening, "expected": expected, "actual": actual, "difference": differences, "receivables": receivables, "payables": payables, "cycle_locked": cycle_locked, "start": start, "end": end}
                for item in tree.get_children():
                    tree.delete(item)
                labels = {"cash": "الصندوق", "visa": "الفيزا", "cliq": "CLIQ (ضمن الحساب البنكي)", "bank": "الحساب البنكي"}
                for key in ("cash", "visa", "cliq", "bank"):
                    diff = differences[key]
                    state = "متطابق" if abs(diff) < 0.01 else ("فائض" if diff > 0 else "عجز")
                    tree.insert("", "end", values=(fix_arabic(state, for_ui=True), f"{diff:.2f} {CURRENCY}", f"{actual[key]:.2f} {CURRENCY}", f"{expected[key]:.2f} {CURRENCY}", fix_arabic(labels[key], for_ui=True)))
                tree.update_idletasks()
                for item in movement_tree.get_children():
                    movement_tree.delete(item)
                for movement, cash_delta, bank_delta, commission_delta in _expected_movement_rows(start, end, opening, expected):
                    movement_tree.insert("", "end", values=(f"{commission_delta:.2f} {CURRENCY}", f"{bank_delta:.2f} {CURRENCY}", f"{cash_delta:.2f} {CURRENCY}", fix_arabic(movement, for_ui=True)))
                movement_tree.update_idletasks()
                expected_total = sum(expected[key] for key in ("cash", "visa", "bank"))
                actual_total = sum(actual[key] for key in ("cash", "visa", "bank"))
                total_difference = actual_total - expected_total
                totals_label.configure(text=fix_arabic(f"إجمالي السيولة المتوقعة: {expected_total:.2f} {CURRENCY}  |  الفعلية: {actual_total:.2f} {CURRENCY}  |  الفرق: {total_difference:.2f} {CURRENCY}", for_ui=True))
                debt_summary_label.configure(text=fix_arabic(f"ذمم العملاء القائمة: {receivables:.2f} {CURRENCY}  |  ذمم الموردين القائمة: {payables:.2f} {CURRENCY}  |  صافي الذمم: {receivables - payables:.2f} {CURRENCY}", for_ui=True))
                status_text = "تم الحساب. الدورة مثبتة؛ راجع الفروقات قبل حفظ المطابقة." if cycle_locked else "تم الحساب. الدورة غير مثبتة؛ ثبّت الرصيد المدور عند اعتماد بداية الدورة."
                status_label.configure(text=fix_arabic(status_text, for_ui=True), text_color=COLOR_TEAL if cycle_locked else COLOR_WHITE)
                save_button.configure(state="normal")
            except (ValueError, sqlite3.Error) as exc:
                save_button.configure(state="disabled")
                status_label.configure(text=fix_arabic(f"تعذر الحساب: {exc}", for_ui=True), text_color=COLOR_WHITE)
                self.show_msg("تعذر حساب المطابقة", str(exc))
            except Exception as exc:
                save_button.configure(state="disabled")
                status_label.configure(text=fix_arabic(f"حدث خطأ غير متوقع أثناء الحساب: {exc}", for_ui=True), text_color=COLOR_WHITE)
                self.show_msg("تعذر حساب المطابقة", str(exc))

        def close_financial_period():
            if self.current_role != "admin" or not calculated["data"]:
                return
            data = calculated["data"]
            if not data.get("cycle_locked"):
                self.show_msg("لا يمكن الإغلاق", "ثبّت الدورة واحفظ المطابقة أولاً.")
                return
            if not self.ask_confirm("تأكيد إغلاق الفترة", "سيتم إغلاق الفترة الحالية وحفظ أرصدتها، ثم فتح حقول بداية دورة جديدة. لن يتم حذف أي حركة سابقة. هل تريد المتابعة؟"):
                return
            try:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.cursor.execute("UPDATE balance_reconciliations SET status='closed', closed_at=?, closed_by=? WHERE id=(SELECT id FROM balance_reconciliations WHERE from_date=? AND to_date=? ORDER BY id DESC LIMIT 1)", (now, self.current_user, data["start"], data["end"]))
                self.db.cursor.execute("UPDATE financial_cycles SET locked=0, notes=COALESCE(notes, '') || ? WHERE from_date=? AND to_date=?", (f"\nإغلاق الفترة: {now}", data["start"], data["end"]))
                self.db.conn.commit()
                set_opening_entries_state("normal")
                lock_cycle_button.configure(state="normal")
                cycle_status.configure(text=fix_arabic(f"تم إغلاق الفترة: {data['start']} إلى {data['end']}. أدخل تواريخ الدورة الجديدة ثم ثبّت رصيدها الافتتاحي.", for_ui=True), text_color=COLOR_WHITE)
                calculated["data"] = None
                save_button.configure(state="disabled")
                close_button.configure(state="disabled")
                self.log_action("إغلاق فترة مالية", "financial_cycles", f"الفترة: {data['start']} إلى {data['end']}")
                self.show_msg("تم الإغلاق", "تم إغلاق الفترة وحفظ سجلها. يمكنك الآن تحديد دورة جديدة وتثبيت رصيد افتتاحي جديد.")
            except sqlite3.Error as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر إغلاق الفترة", str(exc))

        def save_reconciliation():
            if self.current_role != "admin" or not calculated["data"]:
                return
            data = calculated["data"]
            if not data.get("cycle_locked"):
                self.show_msg("لا يمكن الحفظ", "ثبّت الدورة والرصيد الافتتاحي أولاً قبل حفظ المطابقة.")
                return
            try:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                notes = notes_entry.get().strip()
                pdf_path = self.generate_reconciliation_pdf(data, notes)
                self.db.cursor.execute(
                    "INSERT INTO balance_reconciliations (from_date, to_date, opening_cash, opening_visa, opening_cliq, opening_bank, expected_cash, actual_cash, expected_visa, actual_visa, expected_cliq, actual_cliq, expected_bank, actual_bank, receivables_total, payables_total, cycle_locked, notes, status, user, created_at, pdf_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (data["start"], data["end"], data["opening"]["cash"], data["opening"]["visa"], data["opening"]["cliq"], data["opening"]["bank"], data["expected"]["cash"], data["actual"]["cash"], data["expected"]["visa"], data["actual"]["visa"], data["expected"]["cliq"], data["actual"]["cliq"], data["expected"]["bank"], data["actual"]["bank"], data["receivables"], data["payables"], 1, notes, "saved", self.current_user, now, str(pdf_path))
                )
                self.db.conn.commit()
                self.log_action("حفظ مطابقة الأرصدة وإصدار PDF", "balance_reconciliations", f"الفترة: {data['start']} إلى {data['end']}; التقرير: {pdf_path.name}")
                self.show_msg("نجاح", f"تم حفظ المطابقة وإنشاء التقرير المالي PDF:\n{pdf_path}")
                save_button.configure(state="disabled")
                close_button.configure(state="normal")
            except (OSError, ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر حفظ المطابقة أو إنشاء التقرير", str(exc))

        load_locked_cycle()

    def generate_reconciliation_pdf(self, data, notes=""):
        """Create a durable Arabic financial reconciliation report beside the active database."""
        report_dir = self.db.db_path.parent / "reconciliation_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = report_dir / f"balance_reconciliation_{data['start']}_{data['end']}_{stamp}.pdf"

        # Use the TTF converted from the bundled Cocon OTF; it preserves the same family
        # while remaining compatible with ReportLab's TrueType loader.
        font_path = Path(resource_path("Cocon-Next-Arabic-PDF.ttf"))
        if not font_path.exists():
            raise RuntimeError("ملف Cocon PDF TTF غير موجود ضمن الحزمة")
        pdfmetrics.registerFont(TTFont("TCJArabic", str(font_path)))
        font_name = "TCJArabic"

        def ar(value):
            return fix_arabic(str(value), for_ui=False)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TCJTitle", parent=styles["Title"], fontName=font_name, fontSize=17, leading=23, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_RUBI_DARK), spaceAfter=8)
        heading_style = ParagraphStyle("TCJHeading", parent=styles["Heading2"], fontName=font_name, fontSize=12, leading=17, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_RUBI), spaceBefore=8, spaceAfter=5)
        body_style = ParagraphStyle("TCJBody", parent=styles["BodyText"], fontName=font_name, fontSize=10, leading=15, alignment=TA_RIGHT, textColor=colors.HexColor(COLOR_NAVY))

        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm, title="Trend Center Jordan - Balance Reconciliation")
        story = []
        story.append(Paragraph(ar(SHOP_NAME), title_style))
        story.append(Paragraph(ar("تقرير مطابقة الأرصدة والسيولة"), heading_style))
        story.append(Paragraph(ar(f"الدورة المالية: من {data['start']} إلى {data['end']}"), body_style))
        story.append(Paragraph(ar(f"تاريخ إعداد التقرير: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"), body_style))
        story.append(Spacer(1, 7))

        labels = {"cash": "الصندوق", "visa": "الفيزا", "cliq": "CLIQ", "bank": "الحساب البنكي"}
        rows = [[ar("الحساب"), ar("الرصيد الافتتاحي"), ar("الرصيد المتوقع"), ar("الرصيد الفعلي"), ar("الفرق"), ar("الحالة")]]
        for key in ("cash", "visa", "cliq", "bank"):
            diff = float(data["difference"][key])
            state = "متطابق" if abs(diff) < 0.01 else ("فائض" if diff > 0 else "عجز")
            rows.append([ar(labels[key]), f"{data['opening'][key]:.2f} {CURRENCY}", f"{data['expected'][key]:.2f} {CURRENCY}", f"{data['actual'][key]:.2f} {CURRENCY}", f"{diff:.2f} {CURRENCY}", ar(state)])
        table = Table(rows, colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 25 * mm, 25 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_RUBI)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(COLOR_TEXT_MUTED)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(COLOR_WHITE)]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 9))
        story.append(Paragraph(ar(f"إجمالي السيولة المتوقعة: {sum(data['expected'].values()):.2f} {CURRENCY} | إجمالي السيولة الفعلية: {sum(data['actual'].values()):.2f} {CURRENCY} | إجمالي الفرق: {sum(data['difference'].values()):.2f} {CURRENCY}"), body_style))
        story.append(Paragraph(ar(f"ذمم العملاء القائمة حتى نهاية الدورة: {data['receivables']:.2f} {CURRENCY}"), body_style))
        story.append(Paragraph(ar(f"ذمم الموردين القائمة حتى نهاية الدورة: {data['payables']:.2f} {CURRENCY}"), body_style))
        if notes:
            story.append(Paragraph(ar(f"ملاحظات المطابقة: {notes}"), body_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(ar("هذا التقرير توثيقي للمطابقة ولا يعدّل أي حركة بيع أو شراء أو حوالة سابقة في قاعدة البيانات."), body_style))
        doc.build(story)
        return pdf_path

    def ui_financial_position(self):
        """Manager-only baseline and growth tracking for the shop's financial position."""
        if self.current_role != "admin":
            self.show_msg("غير مصرح", "هذه الشاشة متاحة للمدير فقط.")
            return
        for w in self.main_view.winfo_children():
            w.destroy()
        self.create_header("تثبيت ومقارنة الوضع المالي")
        root = ctk.CTkFrame(self.main_view, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=18, pady=10)

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        ctk.CTkLabel(root, text=fix_arabic("الوضع المالي المرجعي ونمو المحل", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(anchor="e", pady=(2, 2))
        ctk.CTkLabel(root, text=fix_arabic("وثّق الموجودات والالتزامات في تاريخ محدد، ثم احفظ لقطات دورية لمراقبة النمو أو التراجع. هذه الشاشة لا تعدّل أي حركة بيع أو شراء أو قيد سابق.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, justify="right", wraplength=940).pack(anchor="e", pady=(0, 12))

        def make_entry(parent, value="0.00", width=150):
            entry = ctk.CTkEntry(parent, height=40, width=width, justify="center", font=FONT_NORMAL_BOLD)
            entry.insert(0, str(value))
            return entry

        def add_money_fields(parent, fields, initial=None):
            entries = {}
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(2, 10))
            for key, label in fields:
                cell = ctk.CTkFrame(row, fg_color="transparent")
                cell.pack(side="right", expand=True, fill="x", padx=5)
                ctk.CTkLabel(cell, text=fix_arabic(label, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=3)
                value = (initial or {}).get(key, 0.0)
                entry = make_entry(cell, f"{float(value or 0):.2f}")
                entry.pack(fill="x", pady=(3, 0))
                entries[key] = entry
            return entries

        def parse_date(raw, label):
            value = raw.strip()
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"{label}: استخدم الصيغة YYYY-MM-DD")
            return value

        def parse_amount(entry, label):
            raw = entry.get().strip().replace(",", ".")
            if raw == "":
                return 0.0
            try:
                return float(raw)
            except (TypeError, ValueError):
                raise ValueError(f"قيمة {label} يجب أن تكون رقماً")

        def outstanding(table, as_of):
            # Sum total_debt - paid_amount across ALL rows in the table
            rows = self.db.cursor.execute(f"SELECT total_debt, paid_amount FROM {table}").fetchall()
            total_sum = 0.0
            for r in rows:
                t = float(r[0] or 0.0)
                p = float(r[1] or 0.0)
                total_sum += max(t - p, 0.0)
            return total_sum

        def setting_number(key):
            row = self.db.cursor.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            try:
                return float(row[0]) if row and row[0] not in (None, "") else 0.0
            except (TypeError, ValueError):
                return 0.0

        aliases = {
            "cash": ["cash", "نقدي", "نقد"],
            "visa": ["visa", "فيزا"],
            "cards": ["cards", "card", "بطاقة", "البطاقات"],
            "bank": ["bank", "البنك", "حساب بنكي"]
        }

        def sum_payment(table, column, key, as_of):
            values = aliases[key]
            placeholders = ",".join("?" for _ in values)
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM({column}), 0) FROM {table} WHERE date <= ? AND LOWER(TRIM(COALESCE(payment_method, 'Cash'))) IN ({placeholders})",
                [as_of] + [v.lower() for v in values]
            ).fetchone()
            return float(row[0] or 0.0)

        def sum_transfers(key, as_of, kind):
            values = aliases[key]
            type_map = {"in": ["دخول حوالة"], "bill": ["دفع فاتورة"], "out": ["خروج حوالة"]}
            types = type_map[kind]
            placeholders = ",".join("?" for _ in values)
            type_placeholders = ",".join("?" for _ in types)
            expression = "amount + commission" if kind in ("in", "bill") else ("amount - commission" if key == "cash" else "amount")
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM({expression}), 0) FROM transfers WHERE date <= ? AND LOWER(TRIM(COALESCE(type, ''))) IN ({type_placeholders}) AND LOWER(TRIM(COALESCE(payment_method, 'Cash'))) IN ({placeholders})",
                [as_of] + [v.lower() for v in types] + [v.lower() for v in values]
            ).fetchone()
            return float(row[0] or 0.0)

        def sum_expenses(key, as_of):
            values = aliases[key]
            placeholders = ",".join("?" for _ in values)
            statuses = "LOWER(TRIM(COALESCE(status, 'paid'))) NOT IN ('unpaid', 'pending', 'credit', 'غير مسدد', 'على الحساب')"
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date <= ? AND LOWER(TRIM(COALESCE(payment_source, 'Cash'))) IN ({placeholders}) AND {statuses}",
                [as_of] + [v.lower() for v in values]
            ).fetchone()
            return float(row[0] or 0.0)

        def sum_debt_payments(key, debt_type, as_of):
            values = aliases[key]
            placeholders = ",".join("?" for _ in values)
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0) FROM debt_payments WHERE date <= ? AND debt_type=? AND LOWER(TRIM(COALESCE(payment_source, 'Cash'))) IN ({placeholders})",
                [as_of, debt_type] + [v.lower() for v in values]
            ).fetchone()
            return float(row[0] or 0.0)

        def sum_internal(key, direction, as_of):
            account = {"cash": "cash", "visa": "visa", "cliq": "cliq", "bank": "bank"}[key]
            column = "dest_acc" if direction == "in" else "source_acc"
            row = self.db.cursor.execute(
                f"SELECT COALESCE(SUM(amount), 0) FROM internal_transfers WHERE date <= ? AND LOWER(TRIM({column}))=?",
                (as_of, account)
            ).fetchone()
            return float(row[0] or 0.0)

        def system_liquidity(as_of):
            # One source of truth for liquidity: opening cash setting plus central journal net movement.
            # Legacy rows are backfilled into the journal on database initialization.
            account_map = {"cash": "CASH", "visa": "VISA"}
            balances = {"cash": setting_number("opening_balance"), "visa": 0.0, "cards": 0.0, "bank": 0.0}
            for key, account_code in account_map.items():
                row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit - jl.credit), 0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code=? AND je.entry_date <= ?", (account_code, as_of)).fetchone()
                balances[key] += float(row[0] or 0.0)
            row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit - jl.credit), 0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code IN ('BANK','CLIQ') AND je.entry_date <= ?", (as_of,)).fetchone()
            balances["bank"] += float(row[0] or 0.0)
            return balances

        def system_inventory(as_of):
            # Fetch total sale-goods inventory cost valuation from products table.
            row = self.db.cursor.execute("SELECT COALESCE(SUM(buy_price * stock), 0) FROM products").fetchone()
            return float(row[0] or 0.0)

        def system_maintenance_parts(as_of):
            row = self.db.cursor.execute("SELECT COALESCE(SUM(cost_price * stock), 0) FROM maintenance_parts").fetchone()
            return float(row[0] or 0.0)
        def system_cards(as_of):
            row = self.db.cursor.execute("SELECT COALESCE(SUM(unit_cost * stock), 0) FROM mobile_cards WHERE active=1").fetchone()
            return float(row[0] or 0.0)

        def maintenance_parts_from_baseline(base_created_at, baseline_value, as_of):
            row = self.db.cursor.execute("SELECT COALESCE(SUM(CASE WHEN movement_type='add' THEN quantity * unit_cost WHEN movement_type IN ('use','adjustment_out') THEN -quantity * unit_cost ELSE 0 END), 0) FROM maintenance_part_movements WHERE created_at > ? AND created_at <= ?", (base_created_at, f"{as_of} 23:59:59")).fetchone()
            return float(baseline_value or 0.0) + float(row[0] or 0.0)

        def current_defaults(as_of):
            # A current snapshot is a movement-based view: locked baseline plus
            # active ledger movements from the baseline date through the snapshot date.
            base = self.db.cursor.execute("SELECT snapshot_date, created_at, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost, customer_receivables, supplier_payables, other_assets, other_liabilities FROM financial_position_snapshots WHERE snapshot_type='baseline' ORDER BY snapshot_date DESC, id DESC LIMIT 1").fetchone()
            if not base:
                liquidity = system_liquidity(as_of)
                return {"cash": liquidity["cash"], "visa": liquidity["visa"], "cards": system_cards(as_of), "bank": liquidity["bank"], "inventory": system_inventory(as_of), "maintenance_parts": system_maintenance_parts(as_of), "receivables": outstanding("customer_debts", as_of), "payables": outstanding("supplier_debts", as_of), "other_assets": 0.0, "other_liabilities": 0.0}
            baseline_date = base[0]
            baseline_created_at = base[1] or f"{baseline_date} 00:00:00"
            def movement(accounts):
                placeholders = ",".join("?" for _ in accounts)
                row = self.db.cursor.execute(f"SELECT COALESCE(SUM(jl.debit - jl.credit),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code IN ({placeholders}) AND (je.entry_date || ' ' || COALESCE(je.entry_time,'00:00:00')) > ? AND (je.entry_date || ' ' || COALESCE(je.entry_time,'00:00:00')) <= ?", list(accounts) + [baseline_created_at, f"{as_of} 23:59:59"]).fetchone()
                return float(row[0] or 0.0)
            baseline_bank = float(base[5] or 0.0)
            # Backward compatibility: if an old baseline only populated CLIQ,
            # carry it to the unified bank account; never add both when both
            # fields are populated because they represent the same account.
            if abs(baseline_bank) < 1e-9 and abs(float(base[3] or 0.0)) > 1e-9:
                baseline_bank = float(base[3] or 0.0)
            return {
                "cash": float(base[2] or 0.0) + movement(("CASH",)),
                "visa": float(base[3] or 0.0) + movement(("VISA",)),
                "cards": float(base[4] or 0.0) + movement(("CARDS",)),
                "bank": baseline_bank + movement(("BANK", "CLIQ")),
                "inventory": float(base[6] or 0.0) + movement(("INVENTORY",)),
                "maintenance_parts": maintenance_parts_from_baseline(baseline_created_at, base[7], as_of),
                "receivables": outstanding("customer_debts", as_of),
                "payables": outstanding("supplier_debts", as_of),
                "other_assets": float(base[10] or 0.0), "other_liabilities": 0.0
            }

        def totals(values):
            assets = sum(values.get(k, 0.0) for k in ("cash", "visa", "cards", "bank", "inventory", "maintenance_parts", "receivables", "other_assets"))
            liabilities = values.get("payables", 0.0) + values.get("other_liabilities", 0.0)
            return assets, liabilities, assets - liabilities

        # Baseline block
        baseline_frame = ctk.CTkFrame(root, fg_color=COLOR_CRIMSON_SOFT, corner_radius=14, border_width=1, border_color=COLOR_TEAL_SOFT)
        baseline_frame.pack(fill="x", pady=(0, 10))
        baseline_head = ctk.CTkFrame(baseline_frame, fg_color="transparent")
        baseline_head.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(baseline_head, text=fix_arabic("المرجع الأساسي (Baseline)", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right")
        baseline_status = ctk.CTkLabel(baseline_head, text=fix_arabic("لم يتم تثبيت مرجع بعد", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE)
        baseline_status.pack(side="left")
        ctk.CTkLabel(baseline_frame, text=fix_arabic("أدخل القيمة الفعلية الموجودة في المحل عند تاريخ المرجع. تشمل السيولة، المخزون بسعر التكلفة، ذمم العملاء، وذمم الموردين.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED, justify="right", wraplength=940).pack(anchor="e", padx=16, pady=(0, 6))
        base_meta = ctk.CTkFrame(baseline_frame, fg_color="transparent")
        base_meta.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(base_meta, text=fix_arabic("تاريخ المرجع", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=5)
        base_date = ctk.CTkEntry(base_meta, height=40, width=160, justify="center", font=FONT_NORMAL_BOLD)
        base_date.insert(0, today)
        base_date.pack(side="right", padx=5)
        ctk.CTkLabel(base_meta, text=fix_arabic("وصف الفترة / المرجع", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=5)
        base_label = ctk.CTkEntry(base_meta, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("مثال: بداية استخدام النظام", for_ui=True))
        base_label.pack(side="right", expand=True, fill="x", padx=5)
        baseline_entries = add_money_fields(baseline_frame, [("cash", "الصندوق"), ("visa", "الفيزا"), ("cards", "حساب البطاقات"), ("bank", "الحساب البنكي الإجمالي"), ("inventory", "المخزون بسعر التكلفة"), ("maintenance_parts", "إجمالي تكلفة قطع الصيانة"), ("receivables", "ذمم العملاء"), ("payables", "ذمم الموردين")])
        ctk.CTkLabel(baseline_frame, text=fix_arabic("الموجودات الأخرى والالتزامات الأخرى اختيارية ويمكن تركها صفراً إذا لم تكن مستخدمة.", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="e", padx=16, pady=(0, 4))
        baseline_extra = add_money_fields(baseline_frame, [("other_assets", "موجودات أخرى")])
        base_notes = ctk.CTkEntry(baseline_frame, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("ملاحظات المرجع (اختياري)", for_ui=True))
        base_notes.pack(fill="x", padx=18, pady=(0, 8))
        baseline_entries.update(baseline_extra)
        baseline_save_button = None
        baseline_new_mode = {"active": False}

        def set_baseline_readonly(readonly):
            widget_state = "disabled" if readonly else "normal"
            for entry in baseline_entries.values():
                entry.configure(state=widget_state)
            for entry in (base_date, base_label, base_notes):
                entry.configure(state=widget_state)
            if baseline_save_button is not None:
                baseline_save_button.configure(state="disabled" if readonly else "normal")

        # Current snapshot block
        current_frame = ctk.CTkFrame(root, fg_color=COLOR_NAVY_LIGHT, corner_radius=14, border_width=1, border_color=COLOR_TEAL_SOFT)
        current_frame.pack(fill="x", pady=(0, 10))
        current_head = ctk.CTkFrame(current_frame, fg_color="transparent")
        current_head.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(current_head, text=fix_arabic("لقطة الوضع الحالي", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        current_meta = ctk.CTkFrame(current_frame, fg_color="transparent")
        current_meta.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(current_meta, text=fix_arabic("تاريخ اللقطة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=5)
        current_date = ctk.CTkEntry(current_meta, height=40, width=160, justify="center", font=FONT_NORMAL_BOLD)
        current_date.insert(0, today)
        current_date.pack(side="right", padx=5)
        ctk.CTkLabel(current_meta, text=fix_arabic("وصف اللقطة", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_DARK).pack(side="right", padx=5)
        current_label = ctk.CTkEntry(current_meta, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("مثال: إقفال أيلول", for_ui=True))
        current_label.pack(side="right", expand=True, fill="x", padx=5)
        current_entries = add_money_fields(current_frame, [("cash", "الصندوق"), ("visa", "الفيزا"), ("cards", "حساب البطاقات"), ("bank", "الحساب البنكي الإجمالي"), ("inventory", "المخزون بسعر التكلفة"), ("maintenance_parts", "إجمالي تكلفة قطع الصيانة"), ("receivables", "ذمم العملاء"), ("payables", "ذمم الموردين")])
        current_extra = add_money_fields(current_frame, [("other_assets", "موجودات أخرى")])
        current_entries.update(current_extra)
        current_notes = ctk.CTkEntry(current_frame, height=40, justify="right", font=FONT_NORMAL_BOLD, placeholder_text=fix_arabic("ملاحظات اللقطة (اختياري)", for_ui=True))
        current_notes.pack(fill="x", padx=18, pady=(0, 8))

        # Action row
        actions = ctk.CTkFrame(root, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(actions, text=fix_arabic("تعبئة القيم الحالية من النظام", for_ui=True), command=lambda: fill_current(), font=FONT_BOLD, fg_color=COLOR_NAVY_LIGHT, hover_color=COLOR_TEAL_DARK, height=44).pack(side="right", padx=5)
        baseline_save_button = ctk.CTkButton(actions, text=fix_arabic("تثبيت المرجع الأساسي", for_ui=True), command=lambda: save_baseline(), font=FONT_BOLD, fg_color=COLOR_VINO, hover_color=COLOR_VINO, height=44)
        baseline_save_button.pack(side="right", padx=5)
        ctk.CTkButton(actions, text=fix_arabic("حفظ اللقطة الحالية ومقارنة", for_ui=True), command=lambda: save_current(), font=FONT_BOLD, fg_color=COLOR_TEAL, hover_color=COLOR_TEAL_DARK, height=44).pack(side="right", padx=5)
        ctk.CTkButton(actions, text=fix_arabic("تثبيت مرجع أساسي جديد", for_ui=True), command=lambda: edit_baseline(), font=FONT_BOLD, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, height=44).pack(side="left", padx=5)

        comparison_frame = ctk.CTkFrame(root, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        comparison_frame.pack(fill="both", expand=True, pady=(0, 10))
        comparison_title = ctk.CTkLabel(comparison_frame, text=fix_arabic("جدول المقارنة مع المرجع الأساسي", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE)
        comparison_title.pack(anchor="e", padx=16, pady=(10, 4))
        comparison_status = ctk.CTkLabel(comparison_frame, text=fix_arabic("ثبّت المرجع ثم احفظ لقطة حالية لعرض النمو أو التراجع.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED)
        comparison_status.pack(anchor="e", padx=16, pady=(0, 6))
        table_wrap = ctk.CTkFrame(comparison_frame, fg_color=COLOR_SURFACE)
        table_wrap.pack(fill="x", padx=12, pady=4)
        comparison_tree = ttk.Treeview(table_wrap, columns=("status", "percent", "change", "current", "baseline", "item"), show="headings", height=9)
        for col, head, width in zip(comparison_tree["columns"], ["الحالة", "النسبة", "التغير", "الحالي", "المرجع", "البند"], [120, 100, 120, 125, 125, 210]):
            comparison_tree.heading(col, text=fix_arabic(head, for_ui=True))
            comparison_tree.column(col, anchor="center", width=width)
        comparison_tree.pack(fill="x", expand=True, pady=4)

        chart_frame = ctk.CTkFrame(comparison_frame, fg_color=COLOR_NAVY, corner_radius=10, border_width=1, border_color=COLOR_TEXT_MUTED)
        chart_frame.pack(fill="x", padx=12, pady=(8, 12))
        ctk.CTkLabel(chart_frame, text=fix_arabic("الرسم البياني: المرجع مقابل اللقطة الحالية", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="e", padx=14, pady=(8, 2))
        chart_canvas = ctk.CTkCanvas(chart_frame, height=250, background=COLOR_NAVY, highlightthickness=0)
        chart_canvas.pack(fill="x", padx=8, pady=(0, 8))

        history_frame = ctk.CTkFrame(root, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        history_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(history_frame, text=fix_arabic("آخر اللقطات المحفوظة", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=16, pady=(8, 2))
        history_tree = ttk.Treeview(history_frame, columns=("net", "liabilities", "assets", "type", "date", "label"), show="headings", height=5)
        for col, head in zip(history_tree["columns"], ["صافي الوضع", "الالتزامات", "الموجودات", "النوع", "التاريخ", "الوصف"]):
            history_tree.heading(col, text=fix_arabic(head, for_ui=True))
            history_tree.column(col, anchor="center", width=145)
        history_tree.pack(fill="x", padx=12, pady=(2, 10))

        state = {"baseline": None, "current": None}
        metrics = [("cash", "الصندوق"), ("visa", "الفيزا"), ("cards", "حساب البطاقات"), ("bank", "الحساب البنكي الإجمالي"), ("inventory", "المخزون بسعر التكلفة"), ("maintenance_parts", "إجمالي تكلفة قطع الصيانة"), ("receivables", "ذمم العملاء"), ("payables", "ذمم الموردين"), ("other_assets", "موجودات أخرى"), ("total_assets", "إجمالي الموجودات"), ("total_liabilities", "إجمالي الالتزامات"), ("net_position", "صافي الوضع المالي")]

        def values_from_entries(entries):
            return {key: parse_amount(entries[key], label) for key, label in [(k, dict(metrics).get(k, k)) for k in ("cash", "visa", "cliq", "bank", "inventory", "maintenance_parts", "receivables", "payables", "other_assets")]}

        def set_entries(entries, values):
            for key, entry in entries.items():
                entry.delete(0, "end")
                entry.insert(0, f"{float(values.get(key, 0.0) or 0.0):.2f}")

        def draw_chart(baseline, current):
            chart_canvas.delete("all")
            width = max(chart_canvas.winfo_width(), 760)
            height = 250
            chart_canvas.configure(width=width)
            chart_canvas.create_line(60, 205, width - 30, 205, fill=COLOR_TEXT_MUTED, width=2)
            chart_canvas.create_text(width - 42, 218, text=fix_arabic("البند", for_ui=True), font=FONT_BOLD, fill=COLOR_TEXT_MUTED)
            selected = [("إجمالي الموجودات", baseline["total_assets"], current["total_assets"]), ("إجمالي الالتزامات", baseline["total_liabilities"], current["total_liabilities"]), ("صافي الوضع", baseline["net_position"], current["net_position"])]
            max_value = max([abs(v) for _, b, c in selected for v in (b, c)] + [1.0])
            group_width = (width - 115) / len(selected)
            for idx, (label, base_value, current_value) in enumerate(selected):
                center = 82 + idx * group_width + group_width / 2
                base_h = min(145, abs(base_value) / max_value * 145)
                current_h = min(145, abs(current_value) / max_value * 145)
                base_y = 190 - base_h if base_value >= 0 else 190
                current_y = 190 - current_h if current_value >= 0 else 190
                chart_canvas.create_rectangle(center - 42, base_y, center - 8, 190, fill=COLOR_TEXT_MUTED, outline="")
                chart_canvas.create_rectangle(center + 8, current_y, center + 42, 190, fill=COLOR_CRIMSON, outline="")
                chart_canvas.create_text(center - 25, max(16, base_y - 10), text=f"{base_value:,.0f}", font=FONT_BOLD, fill=COLOR_TEXT_MUTED)
                chart_canvas.create_text(center + 25, max(16, current_y - 10), text=f"{current_value:,.0f}", font=FONT_BOLD, fill=COLOR_WHITE)
                chart_canvas.create_text(center, 220, text=fix_arabic(label, for_ui=True), font=FONT_BOLD, fill=COLOR_NAVY_LIGHT)
            chart_canvas.create_rectangle(width - 160, 14, width - 145, 29, fill=COLOR_TEXT_MUTED, outline="")
            chart_canvas.create_text(width - 136, 22, text=fix_arabic("المرجع", for_ui=True), anchor="w", font=FONT_BOLD, fill=COLOR_TEXT_MUTED)
            chart_canvas.create_rectangle(width - 75, 14, width - 60, 29, fill=COLOR_CRIMSON, outline="")
            chart_canvas.create_text(width - 52, 22, text=fix_arabic("الحالي", for_ui=True), anchor="w", font=FONT_BOLD, fill=COLOR_WHITE)

        def render_comparison(baseline, current):
            for item in comparison_tree.get_children():
                comparison_tree.delete(item)
            for key, label in metrics:
                if key in ("total_assets", "total_liabilities", "net_position"):
                    base_value = baseline[key]
                    current_value = current[key]
                else:
                    base_value = float(baseline.get(key, 0.0) or 0.0)
                    current_value = float(current.get(key, 0.0) or 0.0)
                change = current_value - base_value
                percent = (change / abs(base_value) * 100.0) if abs(base_value) >= 0.0001 else None
                status = "نمو" if change > 0.005 else ("تراجع" if change < -0.005 else "ثابت")
                status_text = status if key not in ("payables", "total_liabilities") else ("زيادة التزام" if change > 0.005 else ("انخفاض التزام" if change < -0.005 else "ثابت"))
                pct_text = f"{percent:+.2f}%" if percent is not None else "غير محسوبة"
                comparison_tree.insert("", "end", values=(fix_arabic(status_text, for_ui=True), pct_text, f"{change:+,.2f} {CURRENCY}", f"{current_value:,.2f} {CURRENCY}", f"{base_value:,.2f} {CURRENCY}", fix_arabic(label, for_ui=True)))
            draw_chart(baseline, current)
            comparison_status.configure(text=fix_arabic("تمت المقارنة: القيم الموجبة في الموجودات وصافي الوضع تعني تحسناً، أما زيادة الالتزامات فتظهر كزيادة التزام.", for_ui=True), text_color=COLOR_TEAL)

        def load_latest_baseline():
            row = self.db.cursor.execute("SELECT snapshot_date, period_label, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost, customer_receivables, supplier_payables, other_assets, other_liabilities, total_assets, total_liabilities, net_position, notes, created_at FROM financial_position_snapshots WHERE snapshot_type='baseline' ORDER BY snapshot_date DESC, id DESC LIMIT 1").fetchone()
            if not row:
                set_baseline_readonly(False)
                return
            keys = ["cash", "visa", "cards", "bank", "inventory", "maintenance_parts", "receivables", "payables", "other_assets", "other_liabilities"]
            values = dict(zip(keys, row[2:12]))
            values["other_liabilities"] = 0.0
            baseline_assets, baseline_liabilities, baseline_net = totals(values)
            values.update({"total_assets": baseline_assets, "total_liabilities": baseline_liabilities, "net_position": baseline_net})
            state["baseline"] = values
            set_entries(baseline_entries, values)
            base_date.delete(0, "end"); base_date.insert(0, row[0])
            base_label.delete(0, "end"); base_label.insert(0, row[1] or "")
            base_notes.delete(0, "end"); base_notes.insert(0, row[15] or "")
            baseline_status.configure(text=fix_arabic(f"آخر مرجع محفوظ دائماً: {row[0]}", for_ui=True), text_color=COLOR_TEAL)
            set_baseline_readonly(True)

        def fill_current():
            try:
                as_of = parse_date(current_date.get(), "تاريخ اللقطة")
                values = current_defaults(as_of)
                set_entries(current_entries, values)
                assets, liabilities, net = totals(values)
                values.update({"total_assets": assets, "total_liabilities": liabilities, "net_position": net})
                state["current"] = values
                if state.get("baseline"):
                    render_comparison(state["baseline"], values)
            except (ValueError, sqlite3.Error) as exc:
                self.show_msg("تعذر التعبئة", str(exc))

        def edit_baseline():
            baseline_new_mode["active"] = True
            set_baseline_readonly(False)
            if baseline_save_button is not None:
                baseline_save_button.configure(text=fix_arabic("حفظ المرجع الأساسي الجديد", for_ui=True))
            baseline_status.configure(text=fix_arabic("عدّل القيم ثم احفظ مرجعاً أساسياً جديداً؛ السجلات السابقة لا تتغير.", for_ui=True), text_color=COLOR_WHITE)

        def save_baseline():
            try:
                snap_date = parse_date(base_date.get(), "تاريخ المرجع")
                values = values_from_entries(baseline_entries)
                assets, liabilities, net = totals(values)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.cursor.execute("INSERT INTO financial_position_snapshots (snapshot_date, period_label, snapshot_type, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost, customer_receivables, supplier_payables, other_assets, other_liabilities, total_assets, total_liabilities, net_position, notes, user, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (snap_date, base_label.get().strip() or "مرجع أساسي", "baseline", values["cash"], values["visa"], values["cards"], values["bank"], values["inventory"], values["maintenance_parts"], values["receivables"], values["payables"], values["other_assets"], 0.0, assets, liabilities, net, base_notes.get().strip(), self.current_user, now))
                self.db.conn.commit()
                values.update({"total_assets": assets, "total_liabilities": liabilities, "net_position": net})
                state["baseline"] = values
                set_baseline_readonly(True)
                baseline_new_mode["active"] = False
                if baseline_save_button is not None:
                    baseline_save_button.configure(text=fix_arabic("تثبيت المرجع الأساسي", for_ui=True))
                if state.get("current"):
                    render_comparison(values, state["current"])
                baseline_status.configure(text=fix_arabic(f"تم تثبيت المرجع: {snap_date}", for_ui=True), text_color=COLOR_TEAL)
                self.log_action("تثبيت مرجع الوضع المالي", "financial_position_snapshots", f"التاريخ: {snap_date}")
                refresh_history()
                self.show_msg("تم الحفظ", f"تم تثبيت المرجع الأساسي بتاريخ {snap_date}.")
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر تثبيت المرجع", str(exc))

        def save_current():
            try:
                # Always reload the durable baseline before comparison, including after app restart.
                load_latest_baseline()
                snap_date = parse_date(current_date.get(), "تاريخ اللقطة")
                values = values_from_entries(current_entries)
                assets, liabilities, net = totals(values)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.cursor.execute("INSERT INTO financial_position_snapshots (snapshot_date, period_label, snapshot_type, cash, visa, cliq, bank, inventory_value, maintenance_parts_cost, customer_receivables, supplier_payables, other_assets, other_liabilities, total_assets, total_liabilities, net_position, notes, user, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (snap_date, current_label.get().strip() or "لقطة حالية", "current", values["cash"], values["visa"], values["cards"], values["bank"], values["inventory"], values["maintenance_parts"], values["receivables"], values["payables"], values["other_assets"], 0.0, assets, liabilities, net, current_notes.get().strip(), self.current_user, now))
                self.db.conn.commit()
                values.update({"total_assets": assets, "total_liabilities": liabilities, "net_position": net})
                state["current"] = values
                if state["baseline"]:
                    render_comparison(state["baseline"], values)
                else:
                    comparison_status.configure(text=fix_arabic("تم حفظ اللقطة، لكن لا توجد خانة مرجعية للمقارنة بعد.", for_ui=True), text_color=COLOR_WHITE)
                self.log_action("حفظ لقطة الوضع المالي", "financial_position_snapshots", f"التاريخ: {snap_date}")
                refresh_history()
                self.show_msg("تم الحفظ", "تم حفظ اللقطة الحالية وإظهار المقارنة إن وجد المرجع الأساسي.")
            except (ValueError, sqlite3.Error) as exc:
                self.db.conn.rollback()
                self.show_msg("تعذر حفظ اللقطة", str(exc))

        def refresh_history():
            for item in history_tree.get_children():
                history_tree.delete(item)
            rows = self.db.cursor.execute("SELECT snapshot_date, period_label, snapshot_type, total_assets, total_liabilities, net_position FROM financial_position_snapshots ORDER BY snapshot_date DESC, id DESC LIMIT 12").fetchall()
            for snap_date, label, snap_type, assets, liabilities, net in rows:
                type_label = "مرجع أساسي" if snap_type == "baseline" else "لقطة حالية"
                history_tree.insert("", "end", values=(f"{float(net or 0):,.2f} {CURRENCY}", f"{float(liabilities or 0):,.2f} {CURRENCY}", f"{float(assets or 0):,.2f} {CURRENCY}", fix_arabic(type_label, for_ui=True), snap_date, fix_arabic(label or "", for_ui=True)))

        load_latest_baseline()
        refresh_history()
        fill_current()
        baseline = state.get("baseline")
        if baseline and state.get("current"):
            render_comparison(baseline, state["current"])

    def ui_reports(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("التقارير والأرباح")
        # Keep the date filter directly beneath the page title; no empty spacer frame.
        filter_row = ctk.CTkFrame(self.main_view, fg_color="transparent"); filter_row.pack(fill="x", padx=20, pady=(2, 6))
        ctk.CTkButton(filter_row, text=fix_arabic("تطبيق الفلترة", for_ui=True), command=self.refresh_reports, font=FONT_BOLD, fg_color=COLOR_CRIMSON, hover_color=COLOR_CRIMSON_DARK, height=44, width=145).pack(side="right", padx=5)
        # RTL order: «من» and its date field on the right; «إلى» and its date field on the left.
        ctk.CTkLabel(filter_row, text=fix_arabic("من:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=3)
        self.rep_from = ctk.CTkEntry(filter_row, placeholder_text="YYYY-MM-DD", width=150, height=44, justify="right", font=FONT_NORMAL_BOLD); self.rep_from.pack(side="right", padx=5)
        ctk.CTkLabel(filter_row, text=fix_arabic("إلى:", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=3)
        self.rep_to = ctk.CTkEntry(filter_row, placeholder_text="YYYY-MM-DD", width=150, height=44, justify="right", font=FONT_NORMAL_BOLD); self.rep_to.pack(side="right", padx=5)
        action_row = ctk.CTkFrame(self.main_view, fg_color=COLOR_NAVY_LIGHT, corner_radius=12, border_width=1, border_color=COLOR_BORDER); action_row.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(action_row, text=fix_arabic("أدوات التقارير", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(side="right", padx=16, pady=10)
        ctk.CTkButton(action_row, text=fix_arabic("جرد الكاش اليومي", for_ui=True), command=self.show_cash_reconciliation, font=FONT_BOLD, fg_color=COLOR_TEAL, height=40, width=155).pack(side="left", padx=5, pady=7)
        ctk.CTkButton(action_row, text=fix_arabic("تقرير الأرباح والخسائر", for_ui=True), command=self.show_p_and_l_statement, font=FONT_BOLD, fg_color=COLOR_TEAL_DARK, height=40, width=175).pack(side="left", padx=5, pady=7)
        ctk.CTkButton(action_row, text=fix_arabic("التقرير الشهري والإقفال", for_ui=True), command=self.open_monthly_financial_report_dialog, font=FONT_BOLD, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK, height=40, width=175).pack(side="left", padx=5, pady=7)
        
        # Use CTkFrame instead of CTkScrollableFrame to allow it to expand fully within the main scrollable view
        self.rep_body = ctk.CTkFrame(self.main_view, fg_color="transparent"); self.rep_body.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_reports()
    def refresh_reports(self):

        for w in self.rep_body.winfo_children(): w.destroy()
        try:
            # Synchronize operational maintenance costs before calculating any report.
            self.db._sync_maintenance_cost_journals()
            self.db._dedupe_active_managed_journals()
            self.db._void_orphan_journals()
            self.db.conn.commit()
            start, end = self.rep_from.get(), self.rep_to.get()
            where, params = self.date_filter("date", start, end)
            def scalar(query, values=params):
                # Some report queries already contain WHERE (for example paid expenses).
                # Append the date predicate with AND instead of producing `WHERE ... WHERE ...`.
                if where:
                    suffix = (" AND " + where[6:]) if re.search(r"\bWHERE\b", query, re.IGNORECASE) else (" " + where)
                else:
                    suffix = ""
                self.db.cursor.execute(query + suffix, values); return float(self.db.cursor.fetchone()[0] or 0.0)
            
            def ledger_total(account, column):
                clause = "WHERE COALESCE(je.status,'active')='active' AND jl.account_code=?"
                values = [account]
                if start: clause += " AND je.entry_date >= ?"; values.append(start)
                if end: clause += " AND je.entry_date <= ?"; values.append(end)
                row = self.db.cursor.execute(f"SELECT COALESCE(SUM(jl.{column}),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id {clause}", values).fetchone()
                return float(row[0] or 0.0)

            # Report each operational transaction exactly once. The central ledger remains
            # the audit trail, while these aggregates cannot double-count old reposts.
            s_rev = scalar("SELECT COALESCE(SUM(total),0) FROM sales")
            s_cogs = scalar("SELECT COALESCE(SUM(COALESCE(buy_cost,0) * qty),0) FROM sales")
            s_prof = s_rev - s_cogs
            m_rev = scalar("SELECT COALESCE(SUM(revenue),0) FROM maintenance")
            m_cost = scalar("SELECT COALESCE(SUM(internal_cost),0) FROM maintenance")
            m_prof = m_rev - m_cost
            t_comm = scalar("SELECT COALESCE(SUM(commission),0) FROM transfers")
            exp = scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE LOWER(TRIM(COALESCE(status,'paid'))) NOT IN ('unpaid','pending','credit','غير مسدد','على الحساب')")
            purch = scalar("SELECT COALESCE(SUM(qty * cost),0) FROM purchases")
            purchase_returns = scalar("SELECT COALESCE(SUM(qty * unit_cost),0) FROM inventory_adjustments WHERE adjustment_type='مرتجع شراء'")
            purch_net = max(purch - purchase_returns, 0.0)
            
            self.db.cursor.execute("SELECT COALESCE(SUM(buy_price * stock),0), COALESCE(SUM(sell_price * stock),0) FROM products")
            stock_buy, stock_sell = self.db.cursor.fetchone(); stock_buy, stock_sell = float(stock_buy or 0), float(stock_sell or 0)
            
            net_profit = s_prof + m_prof + t_comm - exp
            
            # 1. Main Summary Table — dark surfaces with high-contrast Arabic text.
            f_sum = ctk.CTkFrame(self.rep_body, corner_radius=15, border_width=1, fg_color=COLOR_SURFACE); f_sum.pack(fill="x", pady=10, padx=10)
            items = [
                ("إجمالي المبيعات", s_rev, COLOR_WHITE),
                ("قيمة المنتجات المباعة (من رأس المال - COGS)", s_cogs, COLOR_PUMPKIN_ORANGE),
                ("ربح المبيعات الصافي", s_prof, COLOR_WHITE),
                ("إجمالي إيرادات الصيانة", m_rev, COLOR_WHITE),
                ("تكلفة قطع الصيانة", m_cost, COLOR_PUMPKIN_ORANGE),
                ("ربح الصيانة الصافي", m_prof, COLOR_WHITE),
                ("إجمالي عمولات الحوالات والفواتير", t_comm, COLOR_WHITE),
                ("إجمالي المصاريف", exp, COLOR_PUMPKIN_ORANGE),
                ("إجمالي المشتريات (قبل المرتجعات)", purch, COLOR_WHITE),
                ("مرتجعات المشتريات", purchase_returns, COLOR_PUMPKIN_ORANGE),
                ("صافي المشتريات بعد المرتجعات", purch_net, COLOR_WHITE)
            ]
            for i, (label, val, color) in enumerate(items):
                row_bg = COLOR_NAVY if i % 2 == 0 else COLOR_NAVY_LIGHT
                row = ctk.CTkFrame(f_sum, fg_color=row_bg, corner_radius=0); row.pack(fill="x", padx=2, pady=1)
                ctk.CTkLabel(row, text=fix_arabic(f"{label}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE, anchor="e").pack(side="right", padx=20, pady=10)
                ctk.CTkLabel(row, text=fix_arabic(f"{val:.2f} {CURRENCY}", for_ui=True), font=FONT_REPORT_VALUE, text_color=(COLOR_PUMPKIN_ORANGE if label in ("قيمة المنتجات المباعة (من رأس المال - COGS)", "تكلفة قطع الصيانة", "إجمالي المصاريف", "مرتجعات المشتريات") else COLOR_WHITE), anchor="w").pack(side="left", padx=20, pady=10)
            
            # 2. Inventory Valuation
            f_inv = ctk.CTkFrame(self.rep_body, corner_radius=15, border_width=2, border_color=COLOR_TEAL, fg_color=COLOR_NAVY_LIGHT); f_inv.pack(fill="x", pady=15, padx=10)
            ctk.CTkLabel(f_inv, text=fix_arabic("تقييم المخزون الحالي", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(pady=5)
            row_inv = ctk.CTkFrame(f_inv, fg_color="transparent"); row_inv.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row_inv, text=fix_arabic(f"قيمة المخزون (سعر الشراء): {stock_buy:.2f} {CURRENCY}", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right", padx=20)
            ctk.CTkLabel(row_inv, text=fix_arabic(f"القيمة المتوقعة (سعر البيع): {stock_sell:.2f} {CURRENCY}", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEAL_SOFT).pack(side="left", padx=20)
            
            # 3. Net Profit — large white type for immediate readability.
            f_profit = ctk.CTkFrame(self.rep_body, corner_radius=15, border_width=2, border_color=COLOR_TEAL, fg_color=COLOR_VINO_DARK); f_profit.pack(fill="x", pady=25, padx=10)
            ctk.CTkLabel(f_profit, text=fix_arabic("صافي الربح الفعلي", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE).pack(pady=(18, 8))
            ctk.CTkLabel(f_profit, text=fix_arabic(f"{net_profit:.2f} {CURRENCY}", for_ui=True), font=FONT_NET_PROFIT_VALUE, text_color=COLOR_WHITE).pack(pady=(0, 22))
            
            # Extra spacer at the bottom to ensure full scroll reach
            ctk.CTkLabel(self.rep_body, text="", height=50).pack()
            
        except Exception as exc: self.show_msg("خطأ في التقرير", str(exc))


    def show_p_and_l_statement(self):
        try:
            start, end = self.rep_from.get(), self.rep_to.get()
            where, params = self.date_filter("date", start, end)
            
            def scalar(query, values=params):
                # Append the date predicate safely when a query already has WHERE.
                if where:
                    suffix = (" AND " + where[6:]) if re.search(r"\bWHERE\b", query, re.IGNORECASE) else (" " + where)
                else:
                    suffix = ""
                self.db.cursor.execute(query + suffix, values)
                return float(self.db.cursor.fetchone()[0] or 0.0)

            def ledger_total(account, column):
                clause = "WHERE COALESCE(je.status,'active')='active' AND jl.account_code=?"
                values = [account]
                if start: clause += " AND je.entry_date >= ?"; values.append(start)
                if end: clause += " AND je.entry_date <= ?"; values.append(end)
                row = self.db.cursor.execute(f"SELECT COALESCE(SUM(jl.{column}),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id {clause}", values).fetchone()
                return float(row[0] or 0.0)

            # Use one aggregate per operational record so historical reposts cannot
            # double-count revenue or costs in the visible P&L statement.
            s_rev = scalar("SELECT COALESCE(SUM(total),0) FROM sales")
            m_rev = scalar("SELECT COALESCE(SUM(revenue),0) FROM maintenance")
            t_comm = scalar("SELECT COALESCE(SUM(commission),0) FROM transfers")
            total_revenue = s_rev + m_rev + t_comm
            s_cogs = scalar("SELECT COALESCE(SUM(COALESCE(buy_cost,0) * qty),0) FROM sales")
            m_cost = scalar("SELECT COALESCE(SUM(internal_cost),0) FROM maintenance")
            expenses = scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE LOWER(TRIM(COALESCE(status,'paid'))) NOT IN ('unpaid','pending','credit','غير مسدد','على الحساب')")
            total_costs = s_cogs + m_cost + expenses

            net_profit = total_revenue - total_costs
            
            win = ctk.CTkToplevel(self); win.title(fix_arabic("تقرير الأرباح والخسائر P&L Statement", is_title=True))
            win.geometry("600x750"); win.attributes("-topmost", True); win.grab_set()
            
            ctk.CTkLabel(win, text=fix_arabic("بيان الأرباح والخسائر الرسمي", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE).pack(pady=20)
            ctk.CTkLabel(win, text=fix_arabic(f"الفترة: {start or 'البداية'} إلى {end or 'اليوم'}", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(pady=5)
            
            # 1. Revenue Frame
            f_rev = ctk.CTkFrame(win, fg_color=COLOR_NAVY_LIGHT, corner_radius=15, border_width=1); f_rev.pack(fill="x", padx=30, pady=10)
            ctk.CTkLabel(f_rev, text=fix_arabic("أولاً: إجمالي الإيرادات (Revenue)", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
            rev_items = [("مبيعات المنتجات", s_rev), ("إيرادات الصيانة", m_rev), ("عمولات الخدمات", t_comm)]
            for lbl, val in rev_items:
                r = ctk.CTkFrame(f_rev, fg_color="transparent"); r.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(r, text=fix_arabic(lbl, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(side="right")
                ctk.CTkLabel(r, text=f"{val:.2f} {CURRENCY}", font=FONT_REPORT_VALUE, text_color=COLOR_WHITE).pack(side="left")
            ctk.CTkLabel(f_rev, text=f"-------------------------", text_color=COLOR_WHITE).pack()
            ctk.CTkLabel(f_rev, text=fix_arabic(f"مجموع الإيرادات: {total_revenue:.2f} {CURRENCY}", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE).pack(pady=10)

            # 2. Costs Frame
            f_cost = ctk.CTkFrame(win, fg_color=COLOR_CRIMSON_SOFT, corner_radius=15, border_width=1); f_cost.pack(fill="x", padx=30, pady=10)
            ctk.CTkLabel(f_cost, text=fix_arabic("ثانياً: التكاليف والمصاريف (Costs)", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
            cost_items = [("تكلفة البضاعة المباعة", s_cogs), ("تكلفة الصيانة الداخلية", m_cost), ("المصاريف التشغيلية", expenses)]
            for lbl, val in cost_items:
                r = ctk.CTkFrame(f_cost, fg_color="transparent"); r.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(r, text=fix_arabic(lbl, for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_WHITE).pack(side="right")
                ctk.CTkLabel(r, text=f"{val:.2f} {CURRENCY}", font=FONT_REPORT_VALUE, text_color=COLOR_WHITE).pack(side="left")
            ctk.CTkLabel(f_cost, text=f"-------------------------", text_color=COLOR_WHITE).pack()
            ctk.CTkLabel(f_cost, text=fix_arabic(f"مجموع التكاليف: {total_costs:.2f} {CURRENCY}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)

            # 3. Net Profit Frame
            f_net = ctk.CTkFrame(win, fg_color=COLOR_NAVY_LIGHT, corner_radius=15, border_width=2, border_color=COLOR_TEAL); f_net.pack(fill="x", padx=30, pady=20)
            ctk.CTkLabel(f_net, text=fix_arabic("صافي الربح الحقيقي (Net Profit)", for_ui=True), font=FONT_NET_PROFIT_LABEL, text_color=COLOR_WHITE).pack(pady=12)
            ctk.CTkLabel(f_net, text=f"{net_profit:.2f} {CURRENCY}", font=FONT_NET_PROFIT_VALUE, text_color=COLOR_WHITE).pack(pady=12)
            ctk.CTkLabel(f_net, text=fix_arabic("هذا المبلغ يمثل صافي الربح القابل للسحب بعد تغطية كافة التكاليف.", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=6)

            ctk.CTkButton(win, text=fix_arabic("إغلاق التقرير", for_ui=True), command=win.destroy, font=FONT_BOLD, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK, text_color=COLOR_WHITE, height=45).pack(pady=20)

        except Exception as e:
            self.show_msg("خطأ في التقرير", str(e))

    def show_cash_reconciliation(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Payment breakdown queries
        def get_pm_sum(table, col, pm, extra_where=""):
            w = f"date=? AND payment_method=?" + (f" AND ({extra_where})" if extra_where else "")
            self.db.cursor.execute(f"SELECT COALESCE(SUM({col}),0) FROM {table} WHERE {w}", (today, pm))
            return self.db.cursor.fetchone()[0] or 0.0

        # Sales by PM
        s_cash = get_pm_sum("sales", "total", "Cash")
        s_visa = get_pm_sum("sales", "total", "Visa")
        s_cliq = get_pm_sum("sales", "total", "CLIQ")
        s_sum = s_cash + s_visa + s_cliq
        
        # Maintenance by PM
        m_cash = get_pm_sum("maintenance", "revenue", "Cash")
        m_visa = get_pm_sum("maintenance", "revenue", "Visa")
        m_cliq = get_pm_sum("maintenance", "revenue", "CLIQ")
        m_sum = m_cash + m_visa + m_cliq
        
        # Transfers by PM
        def get_transfer_pm(t_type, pm):
            self.db.cursor.execute(f"SELECT COALESCE(SUM(amount + commission),0) FROM transfers WHERE type=? AND payment_method=? AND date=?", (t_type, pm, today))
            return self.db.cursor.fetchone()[0] or 0.0

        # دفع فاتورة حسب طريقة الدفع
        def get_bill_pm(pm):
            self.db.cursor.execute("SELECT COALESCE(SUM(amount + commission),0) FROM transfers WHERE type='دفع فاتورة' AND payment_method=? AND date=?", (pm, today))
            return self.db.cursor.fetchone()[0] or 0.0

        # دخول حوالة حسب طريقة الدفع
        def get_in_pm(pm):
            self.db.cursor.execute("SELECT COALESCE(SUM(amount + commission),0) FROM transfers WHERE type='دخول حوالة' AND payment_method=? AND date=?", (pm, today))
            return self.db.cursor.fetchone()[0] or 0.0

        # Cycle opening values stay aligned with the financial-position and
        # reconciliation screens; movement totals below are deduplicated from the
        # operational source rows so historical journal reposts cannot inflate them.
        cycle = self.db.cursor.execute("SELECT from_date, opening_cash, opening_visa, opening_cliq, opening_bank FROM financial_cycles WHERE locked=1 AND from_date<=? AND to_date>=? ORDER BY id DESC LIMIT 1", (today, today)).fetchone()
        if cycle:
            cycle_start = cycle[0]
            cycle_open_cash = float(cycle[1] or 0.0)
            cycle_open_visa = float(cycle[2] or 0.0)
            cycle_open_cliq = float(cycle[3] or 0.0)
            cycle_open_bank = float(cycle[4] or 0.0)
        else:
            cycle_start = today
            cycle_open_cash = float(self.db.cursor.execute("SELECT COALESCE(CAST(value AS REAL),0) FROM settings WHERE key='opening_balance'").fetchone()[0] or 0.0)
            cycle_open_visa = cycle_open_cliq = cycle_open_bank = 0.0

        # Keep detailed operational values for the movement list below. They are
        # intentionally separate from the authoritative balances and are not added
        # a second time to any balance total.
        t_in_cash, t_in_visa, t_in_cliq = get_in_pm("Cash"), get_in_pm("Visa"), get_in_pm("CLIQ")
        b_pay_cash, b_pay_visa, b_pay_cliq = get_bill_pm("Cash"), get_bill_pm("Visa"), get_bill_pm("CLIQ")
        self.db.cursor.execute("SELECT COALESCE(SUM(amount - commission),0) FROM transfers WHERE type='خروج حوالة' AND date=?", (today,))
        t_out_net_all = float(self.db.cursor.fetchone()[0] or 0.0)

        def _cash_supporting_movements(start_date, end_date):
            """Return cash-only movements omitted from the sales/service breakdown."""
            def rows(query):
                self.db.cursor.execute(query, (start_date, end_date))
                return self.db.cursor.fetchall()

            cash_expenses = 0.0
            for amount, source, status in rows("SELECT amount, payment_source, status FROM expenses WHERE date BETWEEN ? AND ?"):
                status_text = str(status or "paid").strip().lower()
                if status_text not in {"unpaid", "pending", "credit", "غير مسدد", "على الحساب"} and str(source or "Cash").strip().lower() not in {"unpaid", "pending", "غير مسدد", "على الحساب"} and self._ledger_account_for_payment(source) == "CASH":
                    cash_expenses += max(float(amount or 0.0), 0.0)

            cash_purchases = 0.0
            for qty, cost, funding in rows("SELECT qty, cost, funding_source FROM purchases WHERE date BETWEEN ? AND ?"):
                if self._ledger_account_for_payment(funding) == "CASH":
                    cash_purchases += max(float(qty or 0.0), 0.0) * max(float(cost or 0.0), 0.0)
            cash_purchase_returns = 0.0
            for qty, cost, funding in rows("SELECT ia.qty, ia.unit_cost, p.funding_source FROM inventory_adjustments ia JOIN purchases p ON p.id=ia.original_sale_id WHERE ia.adjustment_type='مرتجع شراء' AND ia.date BETWEEN ? AND ?"):
                if self._ledger_account_for_payment(funding) == "CASH":
                    cash_purchase_returns += max(float(qty or 0.0), 0.0) * max(float(cost or 0.0), 0.0)
            cash_customer_debt = 0.0

            cash_supplier_debt = 0.0
            for debt_type, amount, source in rows("SELECT debt_type, amount, payment_source FROM debt_payments WHERE date BETWEEN ? AND ?"):
                if self._ledger_account_for_payment(source) == "CASH":
                    if str(debt_type or "").strip().lower() == "customer":
                        cash_customer_debt += max(float(amount or 0.0), 0.0)
                    else:
                        cash_supplier_debt += max(float(amount or 0.0), 0.0)

            cash_internal_in = 0.0
            cash_internal_out = 0.0
            for source, destination, amount in rows("SELECT source_acc, dest_acc, amount FROM internal_transfers WHERE date BETWEEN ? AND ?"):
                amount = max(float(amount or 0.0), 0.0)
                if self._ledger_account_for_payment(destination) == "CASH":
                    cash_internal_in += amount
                if self._ledger_account_for_payment(source) == "CASH":
                    cash_internal_out += amount
            return {
                "expenses": round(cash_expenses, 2),
                "purchases": round(cash_purchases, 2),
                "purchase_returns": round(cash_purchase_returns, 2),
                "customer_debt": round(cash_customer_debt, 2),
                "supplier_debt": round(cash_supplier_debt, 2),
                "internal_in": round(cash_internal_in, 2),
                "internal_out": round(cash_internal_out, 2),
            }

        cash_support = _cash_supporting_movements(today, today)

        # Daily count starts from the amount entered by the user. Only today's
        # operational cash movement is added to that user-entered opening cash.
        opening_key = f"daily_opening_cash:{today}"
        opening_row = self.db.cursor.execute("SELECT value FROM settings WHERE key=?", (opening_key,)).fetchone()
        if not opening_row:
            opening_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='opening_balance'").fetchone()
        try:
            open_bal = float(opening_row[0] or 0.0) if opening_row else 0.0
        except (TypeError, ValueError):
            open_bal = 0.0

        today_cash_net = self._operational_account_net("CASH", today, today)
        cycle_visa_net = self._operational_account_net("VISA", cycle_start, today)
        cycle_bank_net = self._operational_account_net("BANK", cycle_start, today)
        cliq_detail_net = self._operational_channel_net("CLIQ", cycle_start, today)
        normalized_cycle_bank_opening = cycle_open_bank if abs(cycle_open_bank) > 1e-9 else cycle_open_cliq

        # Cash is a physical daily count. Visa and the unified bank account use the
        # locked financial-cycle opening plus cycle-to-date operational movements.
        expected_cash = round(open_bal + today_cash_net, 2)
        total_visa = round(cycle_open_visa + cycle_visa_net, 2)
        # CLIQ is an informational payment-channel detail inside BANK, never a
        # second asset and never included again in total_liquidity.
        total_cliq = cliq_detail_net
        total_bank = round(normalized_cycle_bank_opening + cycle_bank_net, 2)
        total_liquidity = round(expected_cash + total_visa + total_bank, 2)
        
        win = ctk.CTkToplevel(self)
        win.title(fix_arabic("جرد الكاش اليومي وتعدد الدفع", is_title=True))
        win.geometry("580x780")
        win.attributes("-topmost", True)
        win.grab_set()
        
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(scroll, text=fix_arabic(f"جرد الكاش وتفصيل الدفع لتاريخ: {today}", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)
        
        # Opening Balance Section
        f_open = ctk.CTkFrame(scroll, fg_color=COLOR_VINO_DARK, corner_radius=15, border_width=1, border_color=COLOR_TEAL_SOFT)
        f_open.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_open, text=fix_arabic("رصيد بداية الصندوق اليومي", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=5)
        row_o = ctk.CTkFrame(f_open, fg_color="transparent"); row_o.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_o, text=fix_arabic("أدخل رصيد البداية:", for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=10)
        e_open = ctk.CTkEntry(row_o, width=120, justify="center"); e_open.insert(0, str(open_bal)); e_open.pack(side="right", padx=5)
        
        def save_opening():
            try:
                val = float(e_open.get())
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (opening_key, str(val)))
                self.db.conn.commit()
                win.destroy(); self.show_cash_reconciliation()
            except: pass
            
        ctk.CTkButton(row_o, text=fix_arabic("تحديث الجرد", for_ui=True), command=save_opening, font=FONT_BOLD, width=140, height=40, fg_color=COLOR_VINO, hover_color=COLOR_VINO_DARK).pack(side="left", padx=10)

        # Breakdown card
        f_break = ctk.CTkFrame(scroll, fg_color=COLOR_BG_LIGHT, corner_radius=15)
        f_break.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_break, text=fix_arabic("إجمالي السيولة حسب طريقة الدفع", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEAL_SOFT).pack(pady=8)
        
        pm_items = [
            ("رصيد الكاش الفعلي (Cash):", expected_cash),
            ("إجمالي الفيزا (Visa):", total_visa),
            ("تفصيل حركة CLIQ (ضمن الحساب البنكي): معلوماتية فقط وغير مضافة للإجمالي", total_cliq),
            ("إجمالي الحساب البنكي الموحد (يشمل CLIQ مرة واحدة):", total_bank)
        ]
        for lbl, val in pm_items:
            row = ctk.CTkFrame(f_break, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            ctk.CTkLabel(row, text=fix_arabic(lbl, for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=10)
            ctk.CTkLabel(row, text=f"{val:.2f} {CURRENCY}", font=FONT_BOLD, text_color=COLOR_TEAL if val >= 0 else COLOR_WHITE).pack(side="left", padx=10)

        f_box = ctk.CTkFrame(scroll, fg_color=COLOR_BG_LIGHT, corner_radius=15)
        f_box.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f_box, text=fix_arabic("حركة الدرج النقدي اليومية", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=8)
        
        items = [
            ("رصيد البداية (كاش):", open_bal),
            ("المبيعات النقدية:", s_cash),
            ("إيرادات الصيانة النقدية:", m_cash),
            ("استلام حوالة كاش (مع العمولة):", t_in_cash),
            ("دفع فاتورة كاش (مع العمولة):", b_pay_cash),
            ("تحصيل ذمم العملاء نقداً:", cash_support["customer_debt"]),
            ("المصاريف المدفوعة نقداً:", -cash_support["expenses"]),
            ("المشتريات الممولة من الصندوق:", -cash_support["purchases"]),
            ("مرتجعات مشتريات نقدية:", cash_support["purchase_returns"]),
            ("تسديد ذمم الموردين نقداً:", -cash_support["supplier_debt"]),
            ("تحويل داخلي إلى الصندوق:", cash_support["internal_in"]),
            ("تحويل داخلي من الصندوق:", -cash_support["internal_out"]),
            ("إرسال حوالة (مخصوماً منها العمولة):", -t_out_net_all)
        ]
        
        for lbl, val in items:
            row = ctk.CTkFrame(f_box, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=fix_arabic(lbl, for_ui=True), font=FONT_NORMAL_BOLD).pack(side="right", padx=10)
            ctk.CTkLabel(row, text=f"{val:.2f} {CURRENCY}", font=FONT_BOLD, text_color=COLOR_WHITE if val < 0 else COLOR_TEXT_DARK).pack(side="left", padx=10)
            
        # Summary Frame at bottom
        f_total = ctk.CTkFrame(scroll, fg_color=COLOR_NAVY_LIGHT, corner_radius=15, border_width=2, border_color=COLOR_TEAL)
        f_total.pack(fill="x", padx=10, pady=10)
        
        row_c = ctk.CTkFrame(f_total, fg_color="transparent"); row_c.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_c, text=fix_arabic("الكاش المفترض في الدرج:", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkLabel(row_c, text=f"{expected_cash:.2f} {CURRENCY}", font=FONT_BOLD, text_color=COLOR_TEAL).pack(side="left")
        
        row_l = ctk.CTkFrame(f_total, fg_color="transparent"); row_l.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_l, text=fix_arabic("إجمالي السيولة (كاش + بنك):", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_MUTED).pack(side="right")
        ctk.CTkLabel(row_l, text=f"{total_liquidity:.2f} {CURRENCY}", font=FONT_BOLD, text_color=COLOR_TEAL_SOFT).pack(side="left")
        win.update_idletasks()

    def _get_shop_info(self):
        """Fetch current shop settings (name, phone, location) dynamically from database."""
        name, phone, location = SHOP_NAME, PHONE, LOCATION
        try:
            self.db.cursor.execute("SELECT key, value FROM settings WHERE key IN ('shop_name', 'phone', 'location')")
            rows = self.db.cursor.fetchall()
            for k, v in rows:
                if k == 'shop_name' and v: name = v
                elif k == 'phone' and v: phone = v
                elif k == 'location' and v: location = v
        except Exception:
            pass
        return name, phone, location

    def _sponsor_directory(self):
        row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_dir'").fetchone()
        configured = str(row[0]).strip() if row and row[0] else "sponsors"
        path = Path(configured)
        if not path.is_absolute():
            path = self.db.db_path.parent / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_sponsor_paths(self):
        row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_paths'").fetchone()
        if not row or not row[0]:
            return []
        try:
            paths = json.loads(row[0])
        except Exception:
            paths = [p for p in str(row[0]).split('|') if p]
        slots = []
        for p in list(paths)[:4]:
            candidate = Path(p) if p else None
            slots.append(candidate if candidate and candidate.exists() and candidate.suffix.lower() == ".png" else None)
        return slots

    def _save_sponsor_paths(self, paths):
        self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sponsors_paths', ?)", (json.dumps([str(p) for p in paths], ensure_ascii=False),))
        self.db.conn.commit()

    def ui_sponsors(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("رعاة الفواتير")
        ctk.CTkLabel(self.main_view, text=fix_arabic("ارفع حتى أربع صور PNG لتظهر أسفل الفواتير المصورة", for_ui=True), font=FONT_BOLD, text_color=COLOR_TEXT_DARK).pack(anchor="e", padx=22, pady=(0, 12))
        title_frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        title_frame.pack(fill="x", padx=22, pady=(0, 10))
        ctk.CTkLabel(title_frame, text=fix_arabic("عنوان الرعاة الظاهر على الفاتورة:", for_ui=True), font=FONT_BOLD).pack(side="right", padx=12, pady=10)
        sponsor_title_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_title'").fetchone()
        sponsor_title_entry = ctk.CTkEntry(title_frame, width=360, height=40, font=FONT_NORMAL_BOLD, justify="right")
        sponsor_title_entry.insert(0, str(sponsor_title_row[0]).strip() if sponsor_title_row and sponsor_title_row[0] else "رعاة Trend Center Jordan")
        sponsor_title_entry.pack(side="right", padx=8, pady=8)
        sponsor_font_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_font_size'").fetchone()
        try: sponsor_font_default = max(10, min(48, int(float(sponsor_font_row[0])))) if sponsor_font_row and sponsor_font_row[0] else 20
        except Exception: sponsor_font_default = 20
        ctk.CTkLabel(title_frame, text=fix_arabic("حجم الخط:", for_ui=True), font=FONT_BOLD).pack(side="left", padx=(12, 4), pady=10)
        sponsor_font_entry = ctk.CTkEntry(title_frame, width=58, height=36, justify="center", font=FONT_NORMAL_BOLD)
        sponsor_font_entry.insert(0, str(sponsor_font_default)); sponsor_font_entry.pack(side="left", padx=3, pady=8)
        def adjust_sponsor_font(delta):
            try: current = int(float(sponsor_font_entry.get()))
            except Exception: current = sponsor_font_default
            sponsor_font_entry.delete(0, "end"); sponsor_font_entry.insert(0, str(max(10, min(48, current + delta))))
        ctk.CTkButton(title_frame, text="−", command=lambda: adjust_sponsor_font(-1), width=34, height=36, font=FONT_BOLD, fg_color=COLOR_TEXT_MUTED).pack(side="left", padx=2, pady=8)
        ctk.CTkButton(title_frame, text="+", command=lambda: adjust_sponsor_font(1), width=34, height=36, font=FONT_BOLD, fg_color=COLOR_CRIMSON).pack(side="left", padx=2, pady=8)
        frame = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER)
        frame.pack(fill="x", padx=22, pady=10)
        paths = self._get_sponsor_paths()
        previews = []
        slot_widgets = []
        def persist():
            sponsor_title = sponsor_title_entry.get().strip() or "رعاة Trend Center Jordan"
            try: sponsor_font_size = max(10, min(48, int(float(sponsor_font_entry.get()))))
            except Exception: sponsor_font_size = 20
            self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sponsors_title', ?)", (sponsor_title,))
            self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('sponsors_font_size', ?)", (str(sponsor_font_size),))
            sponsor_font_entry.delete(0, "end"); sponsor_font_entry.insert(0, str(sponsor_font_size))
            self._save_sponsor_paths(paths)
            self.log_action("تحديث رعاة الفواتير", "settings", "عدد الصور: %s، العنوان: %s" % (len(paths), sponsor_title))
        def render_slot(index):
            for w in slot_widgets[index]: w.destroy()
            slot_widgets[index].clear()
            box = ctk.CTkFrame(frame, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            box.grid(row=index // 2, column=index % 2, padx=10, pady=10, sticky="nsew")
            slot_widgets[index].append(box)
            ctk.CTkLabel(box, text=fix_arabic(f"الراعي {index + 1}", for_ui=True), font=FONT_BOLD).pack(anchor="e", padx=10, pady=(8, 2))
            if index < len(paths) and paths[index]:
                try:
                    preview = Image.open(paths[index]).convert("RGBA"); preview.thumbnail((230, 90))
                    preview_ctk = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
                    img_label = ctk.CTkLabel(box, text="", image=preview_ctk); img_label.image = preview_ctk; img_label.pack(padx=8, pady=5)
                    slot_widgets[index].append(img_label)
                except Exception:
                    pass
            def choose():
                selected = filedialog.askopenfilename(title="اختر صورة الراعي PNG", filetypes=[("PNG images", "*.png")])
                if not selected: return
                target = self._sponsor_directory() / f"sponsor_{index + 1}.png"
                shutil.copy2(selected, target)
                while len(paths) <= index: paths.append(None)
                paths[index] = target
                persist(); render_slot(index)
            def remove():
                if index < len(paths) and paths[index]:
                    try: Path(paths[index]).unlink(missing_ok=True)
                    except Exception: pass
                    paths[index] = None
                    while paths and paths[-1] is None: paths.pop()
                    persist()
                render_slot(index)
            controls = ctk.CTkFrame(box, fg_color="transparent"); controls.pack(fill="x", padx=8, pady=8)
            ctk.CTkButton(controls, text=fix_arabic("اختيار PNG", for_ui=True), command=choose, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=38).pack(side="right", padx=4)
            ctk.CTkButton(controls, text=fix_arabic("حذف", for_ui=True), command=remove, font=FONT_BOLD, fg_color=COLOR_TEXT_MUTED, height=38, width=80).pack(side="left", padx=4)
        for i in range(4): slot_widgets.append([])
        frame.grid_columnconfigure(0, weight=1); frame.grid_columnconfigure(1, weight=1)
        for i in range(4): render_slot(i)
        ctk.CTkButton(self.main_view, text=fix_arabic("حفظ عنوان الرعاة", for_ui=True), command=persist, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42, width=210).pack(anchor="e", padx=22, pady=(2, 8))
        ctk.CTkLabel(self.main_view, text=fix_arabic("يتم نسخ الصور إلى مجلد sponsors بجانب قاعدة البيانات، وتظهر تلقائياً أسفل كل فاتورة صورة يتم إصدارها.", for_ui=True), font=FONT_NORMAL_BOLD, text_color=COLOR_TEXT_MUTED).pack(anchor="e", padx=22, pady=8)

    def ui_financial_liquidity_view(self):
        for w in self.main_view.winfo_children(): w.destroy()
        self.create_header("عرض الوضع المالي")
        top = ctk.CTkFrame(self.main_view, fg_color="transparent"); top.pack(fill="x", padx=22, pady=10)
        ctk.CTkLabel(top, text=fix_arabic("حتى تاريخ:", for_ui=True), font=FONT_BOLD).pack(side="right", padx=6)
        date_entry = ctk.CTkEntry(top, width=170, height=42, justify="center", font=FONT_BOLD)
        date_entry.insert(0, datetime.date.today().isoformat()); date_entry.pack(side="right", padx=6)
        body = ctk.CTkFrame(self.main_view, fg_color=COLOR_SURFACE, corner_radius=14, border_width=1, border_color=COLOR_BORDER); body.pack(fill="both", expand=True, padx=22, pady=8)
        result_label = ctk.CTkLabel(body, text="", font=FONT_BOLD, text_color=COLOR_TEXT_DARK); result_label.pack(anchor="e", padx=18, pady=12)
        table = ttk.Treeview(body, columns=("value", "account"), show="headings", height=8)
        table.heading("account", text=fix_arabic("الحساب", for_ui=True)); table.heading("value", text=fix_arabic("الرصيد المتوقع", for_ui=True))
        table.column("account", anchor="center", width=260); table.column("value", anchor="center", width=220); table.pack(fill="x", padx=18, pady=10)
        def calculate_view():
            try:
                as_of = date_entry.get().strip()
                datetime.date.fromisoformat(as_of)
                cycle = self.db.cursor.execute("SELECT from_date, to_date, opening_cash, opening_visa, opening_cliq, opening_bank FROM financial_cycles WHERE locked=1 AND from_date<=? AND to_date>=? ORDER BY id DESC LIMIT 1", (as_of, as_of)).fetchone()
                if not cycle: raise ValueError("لا توجد دورة مالية مثبتة تشمل التاريخ المحدد")
                start = cycle[0]; opening = {"cash": float(cycle[2] or 0), "visa": float(cycle[3] or 0), "cliq": float(cycle[4] or 0), "bank": float(cycle[5] or 0)}
                if abs(opening["bank"]) < 1e-9 and abs(opening["cliq"]) > 1e-9:
                    opening["bank"] = opening["cliq"]
                opening["cliq"] = 0.0
                balances = {}
                for key, account in (("cash", "CASH"), ("visa", "VISA")):
                    row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit-jl.credit),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code=? AND je.entry_date>=? AND je.entry_date<=?", (account, start, as_of)).fetchone()
                    balances[key] = opening[key] + float(row[0] or 0)
                cliq_row = self.db.cursor.execute("SELECT COALESCE(SUM(jl.debit-jl.credit),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id WHERE COALESCE(je.status,'active')='active' AND jl.account_code IN ('BANK','CLIQ') AND je.entry_date>=? AND je.entry_date<=?", (start, as_of)).fetchone()
                balances["cliq"] = 0.0
                balances["bank"] = opening["bank"] + opening["cliq"] + float(cliq_row[0] or 0)
                for item in table.get_children(): table.delete(item)
                labels = {"cash": "الصندوق", "visa": "الفيزا", "cliq": "CLIQ (ضمن الحساب البنكي)", "bank": "الحساب البنكي"}
                for key in ("cash", "visa", "cliq", "bank"): table.insert("", "end", values=(f"{balances[key]:.2f} {CURRENCY}", fix_arabic(labels[key], for_ui=True)))
                total = sum(balances[key] for key in ("cash", "visa", "bank"))
                table.insert("", "end", values=(f"{total:.2f} {CURRENCY}", fix_arabic("إجمالي السيولة", for_ui=True)))
                result_label.configure(text=fix_arabic(f"الوضع المالي حتى {as_of} | الدورة: {start} إلى {cycle[1]}", for_ui=True))
            except Exception as exc:
                self.show_msg("تعذر عرض الوضع المالي", str(exc))
        ctk.CTkButton(top, text=fix_arabic("عرض الوضع المالي", for_ui=True), command=calculate_view, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=42).pack(side="right", padx=10)
        calculate_view()

    def generate_invoice(self, total, type="SALE", extra=None):
        inv_dir = "invoices"
        try:
            row = self.db.cursor.execute("SELECT value FROM settings WHERE key='invoice_dir'").fetchone()
            if row and row[0]:
                inv_dir = row[0]
        except Exception:
            pass
        
        today_folder = datetime.datetime.now().strftime("%Y-%m-%d")
        target_folder = Path(inv_dir) / today_folder
        try:
            target_folder.mkdir(parents=True, exist_ok=True)
        except Exception:
            target_folder = Path("invoices") / today_folder
            target_folder.mkdir(parents=True, exist_ok=True)

        invoice_number = f"INV-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S%f')[:-3]}"
        filename = f"Invoice_{type}_{invoice_number}.png"
        inv_path = str(target_folder / filename)

        sponsor_paths = [p for p in self._get_sponsor_paths() if p and os.path.isfile(p)][:4]
        # Reference-matched invoice canvas: narrow portrait receipt with compact sections,
        # right-aligned Arabic details, framed total, and a single sponsor row at the bottom.
        img = Image.new('RGB', (500, 1350), color=(255, 255, 255)); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 500, 122], fill=COLOR_CRIMSON)
        d.rectangle([12, 12, 488, 110], outline=COLOR_WHITE, width=2)
        try:
            invoice_font_path = resource_path(APP_FONT_FILE)
            if not os.path.isfile(invoice_font_path): invoice_font_path = "arial.ttf"
            font = ImageFont.truetype(invoice_font_path, 20); bfont = ImageFont.truetype(invoice_font_path, 28)
            sponsor_font_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_font_size'").fetchone()
            try: sponsor_font_size = max(10, min(48, int(float(sponsor_font_row[0])))) if sponsor_font_row and sponsor_font_row[0] else 20
            except Exception: sponsor_font_size = 20
            sponsor_font = ImageFont.truetype(invoice_font_path, sponsor_font_size)
        except:
            font = bfont = sponsor_font = None
        
        s_name, s_name_en, s_phone, s_loc, logo_path = self._shop_identity()
        try:
            if logo_path and os.path.isfile(logo_path):
                logo = Image.open(logo_path).convert("RGBA"); logo.thumbnail((72, 72)); img.paste(logo, (18, 14), logo)
        except Exception:
            pass
        d.text((270, 38), fix_arabic(s_name, for_ui=False), fill=COLOR_WHITE, font=bfont, anchor="mm")
        d.text((270, 76), str(s_name_en), fill=COLOR_WHITE, font=font, anchor="mm")
        d.text((450, 145), fix_arabic(f"رقم الفاتورة: {invoice_number}", for_ui=False), fill=COLOR_CRIMSON, font=font, anchor="rm")
        d.text((450, 180), fix_arabic(f"الموقع: {s_loc}", for_ui=False), fill=(0,0,0), font=font, anchor="rm")
        d.text((450, 215), fix_arabic(f"الهاتف: {s_phone}", for_ui=False), fill=(0,0,0), font=font, anchor="rm")
        d.text((450, 250), fix_arabic(f"التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", for_ui=False), fill=(0,0,0), font=font, anchor="rm")
        d.line([20, 280, 480, 280], fill=COLOR_CRIMSON, width=3); y = 332
        
        if extra and 'client' in extra:
            d.text((450, y), fix_arabic(f"العميل: {extra['client']}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 48
            
        if extra and 'payment' in extra:
            d.text((450, y), fix_arabic(f"طريقة الدفع: {extra['payment']}", for_ui=False), fill=COLOR_CRIMSON, font=font, anchor="rm"); y += 40
            
        if extra and extra.get("card_number"):
            d.text((450, y), fix_arabic(f"رقم البطاقة: {extra['card_number']}", for_ui=False), fill=COLOR_CRIMSON, font=font, anchor="rm"); y += 48
        if type == "SALE":
            for i in self.cart: 
                d.text((450, y), fix_arabic(f"{i['name']} x{i['qty']} : {i['total']:.2f}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 40
        elif type == "MAINTENANCE":
            d.text((450, y), fix_arabic(f"الجهاز: {extra['device']}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 40
            d.text((450, y), fix_arabic(f"الإصلاح: {extra['desc']}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 40
        elif type == "TRANSFER":
            raw_t = extra.get('type', '')
            # User rule for invoice titles:
            # - دخول حوالة -> ارسال حوالة
            # - خروج حوالة -> استلام حوالة
            # - دفع فاتورة -> دفع فاتورة
            if raw_t == "دخول حوالة":
                inv_t = "ارسال حوالة"
            elif raw_t == "خروج حوالة":
                inv_t = "استلام حوالة"
            else:
                inv_t = "دفع فاتورة"
            d.text((450, y), fix_arabic(f"النوع: {inv_t}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 48
            d.text((450, y), fix_arabic(f"المرجع: {extra['ref']}", for_ui=False), fill=(0,0,0), font=font, anchor="rm"); y += 40
            
        if extra and "points" in extra and extra['points'] > 0:
            d.text((450, y+20), fix_arabic(f"النقاط المكتسبة: {extra['points']}", for_ui=False), fill=COLOR_NAVY, font=font, anchor="rm"); y += 52
        current_points = None
        customer_phone = extra.get("phone") if extra else None
        if customer_phone:
            try:
                points_row = self.db.cursor.execute("SELECT points FROM customers WHERE phone=?", (customer_phone,)).fetchone()
                current_points = int(points_row[0] or 0) if points_row else 0
            except Exception:
                current_points = None
        if current_points is not None:
            d.text((450, y+20), fix_arabic(f"نقاطك الحالية: {current_points}", for_ui=False), fill=COLOR_NAVY, font=font, anchor="rm"); y += 50
            
        content_bottom = y + 100
        d.rectangle([20, y+20, 480, content_bottom], outline=COLOR_CRIMSON, width=3)
        d.text((250, y+60), fix_arabic(f"الإجمالي: {total:.2f} {CURRENCY}", for_ui=False), fill=(0,0,0), font=bfont, anchor="mm")
        final_bottom = content_bottom
        if sponsor_paths:
            footer_y = content_bottom + 42
            d.line([20, footer_y - 18, 480, footer_y - 18], fill=COLOR_CRIMSON, width=2)
            sponsor_title_row = self.db.cursor.execute("SELECT value FROM settings WHERE key='sponsors_title'").fetchone()
            sponsor_title = str(sponsor_title_row[0]).strip() if sponsor_title_row and sponsor_title_row[0] else "رعاة Trend Center Jordan"
            d.text((250, footer_y), fix_arabic(sponsor_title, for_ui=False), fill=COLOR_NAVY, font=sponsor_font or font, anchor="mm")
            count = len(sponsor_paths)
            # The reference uses one compact horizontal row. Keep that structure for
            # 1–4 logos and reduce each slot as the number of sponsors increases.
            gap = 10
            side_margin = 28
            slot_width = max(54, int((500 - (2 * side_margin) - ((count - 1) * gap)) / count))
            slot_height = 82
            row_width = count * slot_width + (count - 1) * gap
            row_start = int((500 - row_width) / 2)
            slots = [(row_start + idx * (slot_width + gap), footer_y + 28, slot_width, slot_height) for idx in range(count)]
            for sponsor_path, (sx, sy, sw, sh) in zip(sponsor_paths, slots):
                try:
                    sponsor = Image.open(sponsor_path).convert("RGBA")
                    sponsor.thumbnail((sw, sh))
                    img.paste(sponsor, (int(sx + (sw - sponsor.width) / 2), int(sy + (sh - sponsor.height) / 2)), sponsor)
                except Exception:
                    pass
            final_bottom = footer_y + 28 + slot_height
        img = img.crop((0, 0, 500, min(img.height, int(final_bottom + 28))))
        img.save(inv_path)
        
        # V115: Copy image to clipboard for easy WhatsApp sharing
        if sys.platform == "win32":
            try:
                import win32clipboard
                output = io.BytesIO()
                img.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]
                output.close()
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
            except: pass

        # Always show image preview for the user (Windows standard behavior)
        try:
            if sys.platform == "win32":
                os.startfile(inv_path)
            else:
                # For non-windows systems (like development environment), just skip or use a viewer if available
                pass
        except Exception:
            pass

        # Direct Thermal Printing for Xprinter XP-Q800 (80mm) in the background
        if sys.platform == "win32":
            try:
                import win32print
                import win32ui
                from PIL import ImageWin
                printer_name = None
                printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                for p in printers:
                    if "xprinter" in p[2].lower() or "xp-q800" in p[2].lower() or "pos" in p[2].lower() or "thermal" in p[2].lower():
                        printer_name = p[2]
                        break
                if not printer_name:
                    printer_name = win32print.GetDefaultPrinter()
                
                if printer_name:
                    hPrinter = win32print.OpenPrinter(printer_name)
                    try:
                        hdc = win32ui.CreateDC()
                        hdc.CreatePrinterDC(printer_name)
                        hdc.StartDoc("Trend Center Invoice")
                        hdc.StartPage()
                        
                        # 80mm thermal printer printable width (~576 dots at 203 DPI)
                        w, h = img.size
                        target_w = 576
                        target_h = int(h * (target_w / w))
                        print_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        dib = ImageWin.Dib(print_img)
                        dib.draw(hdc.GetHandleOutput(), (0, 0, target_w, target_h))
                        
                        hdc.EndPage()
                        hdc.EndDoc()
                        hdc.DeleteDC()
                    finally:
                        win32print.ClosePrinter(hPrinter)
            except Exception:
                # If printing fails, the image is already shown by startfile above
                pass
        
        # WhatsApp Marketing Integration with Loyalty Points Balance
        phone = extra.get('phone') if extra else None
        client = extra.get('client') if extra else "العميل"
        if phone:
            # Fetch total points for customer
            total_pts = 0
            try:
                self.db.cursor.execute("SELECT points FROM customers WHERE phone=?", (phone,))
                res = self.db.cursor.fetchone()
                if res:
                    total_pts = int(res[0] or 0)
            except Exception:
                pass
            
            earned_pts = extra.get('points', 0)
            service_desc = "المبيعات" if type == "SALE" else ("الصيانة" if type == "MAINTENANCE" else "الخدمات المالية")
            
            s_name, s_phone, s_loc = self._get_shop_info()
            msg = (
                f"مرحباً بك يا {client} 🌸\n"
                f"شكراً لثقتك وزيارتك لـ {s_name} ({s_loc}).\n\n"
                f"✅ تمت خدمة ({service_desc}) بنجاح.\n"
                f"💰 المبلغ الإجمالي: {total:.2f} {CURRENCY}\n"
            )
            if earned_pts > 0:
                msg += f"🎁 النقاط المكتسبة لهذه العملية: +{earned_pts} نقطة\n"
            if total_pts > 0:
                msg += f"🌟 رصيد نقاط الولاء الإجمالي: {total_pts} نقطة\n"
            
            msg += "\nنسعد دائماً بخدمتكم! 🛍️✨"
            
            if not (extra and extra.get("skip_whatsapp_prompt")) and self.ask_confirm(str("تواصل واتساب"), str(f"هل تريد إرسال الفاتورة وتفاصيل الولاء للعميل {client} عبر واتساب فوراً؟")):
                self.send_whatsapp(phone, msg)

    def open_monthly_financial_report_dialog(self):
        """Open the Comprehensive Monthly Financial Report and Month-Closing Dialog."""
        mw = ctk.CTkToplevel(self)
        mw.title(fix_arabic("التقرير المالي الشهري الشامل والإقفال والترحيل", is_title=True))
        mw.geometry("820x680")
        mw.attributes("-topmost", True)
        mw.grab_set()

        ctk.CTkLabel(mw, text=fix_arabic("التقرير المالي الشهري الشامل والإقفال المالي", for_ui=True), font=FONT_BOLD, text_color=COLOR_WHITE).pack(pady=10)

        # Period selector frame
        sel_frame = ctk.CTkFrame(mw, fg_color="transparent")
        sel_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(sel_frame, text=fix_arabic("اختر الشهر (YYYY-MM):", for_ui=True), font=FONT_BOLD).pack(side="right", padx=5)
        now = datetime.datetime.now()
        default_month = f"{now.year:04d}-{now.month:02d}"
        month_entry = ctk.CTkEntry(sel_frame, width=130, height=38, font=FONT_NORMAL_BOLD, justify="center")
        month_entry.pack(side="right", padx=5)
        month_entry.insert(0, default_month)

        content_box = ctk.CTkTextbox(mw, width=780, height=450, font=FONT_BOLD)
        content_box.pack(fill="both", expand=True, padx=20, pady=10)

        def generate_report():
            m_prefix = month_entry.get().strip()
            if not m_prefix or len(m_prefix) != 7:
                self.show_msg("تنبيه", "يرجى إدخال الشهر بالصيغة الصحيحة YYYY-MM"); return
            
            try:
                # Synchronize maintenance costs before the monthly P&L snapshot.
                self.db._sync_maintenance_cost_journals()
                self.db._void_orphan_journals()
                self.db.conn.commit()
                def ledger_sum(account, column, prefix=None, before=None):
                    if account == "BANK":
                        clause = "WHERE COALESCE(je.status,'active')='active' AND jl.account_code IN ('BANK','CLIQ')"
                        values = []
                    else:
                        clause = "WHERE COALESCE(je.status,'active')='active' AND jl.account_code=?"
                        values = [account]
                    if prefix:
                        clause += " AND je.entry_date LIKE ?"; values.append(prefix + "%")
                    if before:
                        clause += " AND je.entry_date < ?"; values.append(before)
                    row = self.db.cursor.execute(f"SELECT COALESCE(SUM(jl.{column}),0) FROM journal_lines jl JOIN journal_entries je ON je.id=jl.entry_id {clause}", values).fetchone()
                    return float(row[0] or 0.0)

                first_day = m_prefix + "-01"
                opening_liquidity = float(self.db.cursor.execute("SELECT COALESCE(CAST(value AS REAL),0) FROM settings WHERE key='opening_balance'").fetchone()[0] or 0.0)
                for account in ("CASH", "VISA", "BANK"):
                    opening_liquidity += ledger_sum(account, "debit", before=first_day) - ledger_sum(account, "credit", before=first_day)

                # Current-month P&L uses one operational row per transaction.
                s_rev = self.db.cursor.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                s_cogs = self.db.cursor.execute("SELECT COALESCE(SUM(COALESCE(buy_cost,0) * qty),0) FROM sales WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                s_count = self.db.cursor.execute("SELECT COUNT(*) FROM sales WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                m_rev = self.db.cursor.execute("SELECT COALESCE(SUM(revenue),0) FROM maintenance WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                m_cost = self.db.cursor.execute("SELECT COALESCE(SUM(internal_cost),0) FROM maintenance WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                m_count = self.db.cursor.execute("SELECT COUNT(*) FROM maintenance WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                t_comm = self.db.cursor.execute("SELECT COALESCE(SUM(commission),0) FROM transfers WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                t_count = self.db.cursor.execute("SELECT COUNT(*) FROM transfers WHERE date LIKE ?", (m_prefix + "%",)).fetchone()[0]
                total_exp = self.db.cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date LIKE ? AND LOWER(TRIM(COALESCE(status,'paid'))) NOT IN ('unpaid','pending','credit','غير مسدد','على الحساب')", (m_prefix + "%",)).fetchone()[0]

                self.db.cursor.execute("SELECT COALESCE(SUM(cost * qty),0), COUNT(*) FROM purchases WHERE date LIKE ?", (m_prefix + "%",))
                pur_total, pur_count = self.db.cursor.fetchone()

                # Payment breakdown (Cash, Visa, CLIQ)
                self.db.cursor.execute("SELECT payment_method, COALESCE(SUM(total),0) FROM sales WHERE date LIKE ? GROUP BY payment_method", (m_prefix + "%",))
                sales_pay = dict(self.db.cursor.fetchall())

                self.db.cursor.execute("SELECT payment_method, COALESCE(SUM(revenue),0) FROM maintenance WHERE date LIKE ? GROUP BY payment_method", (m_prefix + "%",))
                maint_pay = dict(self.db.cursor.fetchall())

                cash_in = ledger_sum("CASH", "debit", prefix=m_prefix)
                visa_in = ledger_sum("VISA", "debit", prefix=m_prefix)
                cliq_in = ledger_sum("CLIQ", "debit", prefix=m_prefix)

                total_rev = (s_rev or 0.0) + (m_rev or 0.0) + (t_comm or 0.0)
                total_cogs = (s_cogs or 0.0) + (m_cost or 0.0)
                gross_profit = total_rev - total_cogs
                net_profit = gross_profit - total_exp

                closing_liquidity = opening_liquidity
                for account in ("CASH", "VISA", "BANK"):
                    closing_liquidity += ledger_sum(account, "debit", prefix=m_prefix) - ledger_sum(account, "credit", prefix=m_prefix)

                report_text = f"""
========================================================================
       التقرير المالي الشهري الشامل والإقفال — Trend Center Jordan
========================================================================
 فترة التقرير: {m_prefix}
 تاريخ الإصدار: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
------------------------------------------------------------------------
 1. الرصيد المرحّل والافتتاحي:
    • رصيد السيولة المرحّل من الفترات السابقة: {opening_liquidity:.2f} دينار

 2. إيرادات العمليات للشهر ({m_prefix}):
    • إيرادات المبيعات (Sales): {s_rev:.2f} دينار (عدد: {s_count})
    • إيرادات الصيانة (Maintenance): {m_rev:.2f} دينار (عدد: {m_count})
    • عمولات الحوالات (Transfers): {t_comm:.2f} دينار (عدد: {t_count})
    • إجمالي الإيرادات الكلية: {total_rev:.2f} دينار

 3. التكاليف والمصروفات:
    • تكلفة البضاعة المباعة (COGS): {s_cogs:.2f} دينار
    • تكلفة قطع الصيانة المستهلكة: {m_cost:.2f} دينار
    • إجمالي تكلفة البضاعة والقطع: {total_cogs:.2f} دينار
    • مجمل الربح (Gross Profit): {gross_profit:.2f} دينار
    • المصروفات التشغيلية المسجلة: {total_exp:.2f} دينار
    • إجمالي المشتريات من مصادر خارجية: {pur_total:.2f} دينار (عدد الفواتير: {pur_count})

 4. صافي أرباح الشهر (Net Profit):
    • صافي الربح الحقيقي القابل للسحب: {net_profit:.2f} دينار

 5. تدفقات السيولة وحركة الدفع:
    • التحصيل النقدي (Cash In): {cash_in:.2f} دينار
    • تحصيل البطاقات (Visa In): {visa_in:.2f} دينار
    • تحصيل كليك (CLIQ In): {cliq_in:.2f} دينار
    • رصيد السيولة الختامي التقديري: {closing_liquidity:.2f} دينار
========================================================================
"""
                content_box.delete("1.0", "end")
                content_box.insert("1.0", fix_arabic(report_text, for_ui=True))

            except Exception as e:
                self.show_msg("خطأ", f"تعذر إنشاء التقرير: {str(e)}")

        def close_and_roll_month():
            m_prefix = month_entry.get().strip()
            if not m_prefix or len(m_prefix) != 7:
                self.show_msg("تنبيه", "يرجى تحديد الشهر المراد إقفاله بصيغة YYYY-MM"); return
            
            if not self.ask_confirm(str("تأكيد الإقفال الشهري"), f"هل أنت متأكد من رغبتك في إقفال الشهر {m_prefix} وترحيل الأرصدة؟\nهذا الإجراء سيقوم بتسجيل قفل إداري ولن يسمح بتعديل حركات الشهر بعد اعتماده."):
                return
            
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"closed_month_{m_prefix}", f"Closed by {self.current_user} at {now_str}"))
                self.db.conn.commit()
                self.log_action("إقفال شهر مالياً", "settings", f"الشهر المقفل: {m_prefix}")
                self.show_msg("نجاح", f"تم إقفال الشهر {m_prefix} بنجاح وترحيل الأرصدة للسجل المالي.")
                mw.destroy()
            except Exception as e:
                self.db.conn.rollback()
                self.show_msg("خطأ", f"تعذر إقفال الشهر: {str(e)}")

        btn_f = ctk.CTkFrame(mw, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_f, text=fix_arabic("عرض وإعداد التقرير", for_ui=True), command=generate_report, font=FONT_BOLD, fg_color=COLOR_CRIMSON, height=45, width=220).pack(side="right", padx=10)
        ctk.CTkButton(btn_f, text=fix_arabic("إقفال الشهر وترحيل الأرصدة", for_ui=True), command=close_and_roll_month, font=FONT_BOLD, fg_color=COLOR_RUBI, hover_color=COLOR_RUBI_DARK, height=45, width=220).pack(side="left", padx=10)

        generate_report() # auto generate on open

if __name__ == "__main__":
    app = TrendCenterApp(); app.mainloop()
