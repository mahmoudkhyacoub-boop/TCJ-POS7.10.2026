# Trend Center Jordan — V210 Final OTF and Text Color Fix

تم استخدام ملف المستخدم المرفق حرفياً: `cocon-next-arabic-regular.otf`، بعد فحص اسمه الداخلي `Cocon® Next Arabic` ونمطه Regular.

تم تحديث البرنامج ليستخدم ملف OTF في `APP_FONT_FILE`، وتسجيله داخل Windows عبر `AddFontResourceExW`، وضبط خطوط Tk وttk المسماة، وثوابت CustomTkinter، ومسار Pillow للفواتير والعقود. وتمت إضافة ملف OTF نفسه إلى أمر PyInstaller `--add-data` حتى يصل إلى EXE.

تمت مراجعة تعيينات ألوان النصوص وتحويل كل الاستخدامات النصية المتبقية من Rubi/Vino/Crimson إلى الأبيض، مع الحفاظ على ألوان الخلفيات والأزرار والحدود والرسومات، بما فيها أعمدة المخططات.

تم تشغيل TrendCenterApp فعلياً داخل بيئة رسومية، وتحقق Tk من عائلة `CoconÆ Next Arabic` بوزن Bold، وهي صيغة Tk للاسم الداخلي الذي يتضمن `Cocon® Next Arabic`. كما نجحت اختبارات البرنامج: 10/10 دون فشل.

لم يتم تعديل العمليات المحاسبية أو رسوم الفيزا أو الصلاحيات أو التقارير أو أي وظيفة غير مرتبطة بالخط أو لون النص.
