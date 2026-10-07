# Trend Center Jordan — V209 Attached OTF Font

تم استبدال ملف الخط السابق بملف المستخدم المرفق حرفياً:

`cocon-next-arabic-regular.otf`

تم فحص الاسم الداخلي للملف، وهو `Cocon® Next Arabic` بنمط Regular. تم تحديث `APP_FONT_FILE`، ومسار تسجيل الخط في Windows، وخيارات الخط المسماة في Tk وttk، وثوابت CustomTkinter، ومسار Pillow للفواتير والعقود.

تم تشغيل `TrendCenterApp` فعلياً داخل بيئة رسومية والتحقق من أن `TkDefaultFont` و`TkTextFont` و`TkMenuFont` و`TkHeadingFont` تعيد عائلة Cocon بوزن Bold المطبق على الواجهة، بينما يستخدم Pillow ملف OTF المرفق للفواتير والعقود.

لم يتم تعديل العمليات المحاسبية أو رسوم الفيزا أو الصلاحيات أو التقارير أو أي وظيفة أخرى.

النتائج: `py_compile` ناجح، AST ناجح، و10/10 اختبارات ناجحة.
