from pathlib import Path

p = Path('/home/ubuntu/tcjpos60_work/main.py')
s = p.read_text(encoding='utf-8')

# Add navigation icon mapping.
old = '            "سجل استلام وتسليم الأجهزة": "operations.png",\n'
new = old + '            "حملات تسويقية": "reports.png",\n'
if old not in s:
    raise SystemExit('navigation icon anchor not found')
s = s.replace(old, new, 1)

# Add campaign navigation to both employee and manager customer groups.
old = 'add_nav_group("العملاء والذمم", [("إدارة العملاء", self.ui_customers), ("إدارة الديون والذمم ⚖️", self.ui_debts), ("نظام الولاء", self.ui_loyalty)], COLOR_TEAL)'
new = 'add_nav_group("العملاء والذمم", [("إدارة العملاء", self.ui_customers), ("حملات تسويقية", self.ui_marketing_campaigns), ("إدارة الديون والذمم ⚖️", self.ui_debts), ("نظام الولاء", self.ui_loyalty)], COLOR_TEAL)'
if s.count(old) != 2:
    raise SystemExit(f'expected two customer nav anchors, found {s.count(old)}')
s = s.replace(old, new, 2)

anchor = '    def ui_customers(self):\n'
if anchor not in s:
    raise SystemExit('ui_customers anchor not found')

method = r'''    def ui_marketing_campaigns(self):
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

'''
s = s.replace(anchor, method + anchor, 1)
p.write_text(s, encoding='utf-8')
