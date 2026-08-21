# Path: pms_app/blueprints/daily_reports/forms.py
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    TextAreaField,
    HiddenField,
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError


class DailyReportForm(FlaskForm):
    """فرم ثبت / ویرایش گزارش روزانه."""

    report_date = DateField(
        "تاریخ گزارش",
        validators=[DataRequired(message="تاریخ گزارش الزامی است.")],
        default=date.today,
    )

    weather = SelectField(
        "وضعیت هوا",
        choices=[
            ("", "— انتخاب کنید —"),
            ("sunny", "آفتابی"),
            ("partly_cloudy", "نیمه‌ابری"),
            ("cloudy", "ابری"),
            ("rainy", "بارانی"),
            ("stormy", "طوفانی"),
            ("snowy", "برفی"),
            ("foggy", "مه"),
            ("windy", "باد شدید"),
            ("other", "سایر"),
        ],
        validators=[Optional()],
    )
    temperature_min = DecimalField("حداقل دما (°C)", places=1, validators=[Optional()])
    temperature_max = DecimalField("حداکثر دما (°C)", places=1, validators=[Optional()])

    manpower_total = IntegerField(
        "تعداد کل نیروی انسانی",
        validators=[Optional(), NumberRange(min=0, max=10000)],
        default=0,
    )
    manpower_details_raw = TextAreaField(
        "جزئیات نیروی انسانی (هر خط: نقش | تعداد)",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "کارگر ساده | ۱۲\nجوشکار | ۴\nراننده | ۲"},
    )

    equipment_details_raw = TextAreaField(
        "ماشین‌آلات و تجهیزات (هر خط: نام | تعداد | ساعت کار)",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 3, "placeholder": "بیل مکانیکی | ۱ | ۸\nکمپرسی | ۳ | ۶"},
    )

    work_performed = TextAreaField(
        "شرح کارهای انجام‌شده",
        validators=[Optional(), Length(max=10000)],
        render_kw={"rows": 5, "placeholder": "فعالیت‌های اصلی امروز را شرح دهید..."},
    )

    # پیشرفت پیشنهادی روی آیتم‌ها (JSON ساده به صورت متن)
    progress_updates_raw = TextAreaField(
        "به‌روزرسانی پیشرفت آیتم‌ها (اختیاری)\nهر خط: شناسه آیتم | درصد پیشرفت | مقدار انجام‌شده | یادداشت",
        validators=[Optional(), Length(max=5000)],
        render_kw={
            "rows": 4,
            "placeholder": "۱۲ | ۶۵ | ۱۲۰ | بتن‌ریزی فونداسیون\n۱۵ | ۳۰ | ۰ | نصب اسکلت",
        },
    )

    issues_delays = TextAreaField(
        "مشکلات، تأخیرات و موانع",
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 3},
    )

    hse_incidents = TextAreaField(
        "حوادث ایمنی (HSE)",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 2},
    )
    hse_observations = TextAreaField(
        "مشاهدات و نکات ایمنی",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 2},
    )
    near_miss_count = IntegerField(
        "تعداد Near Miss",
        validators=[Optional(), NumberRange(min=0, max=1000)],
        default=0,
    )

    visitors_meetings = TextAreaField(
        "بازدیدکنندگان / جلسات",
        validators=[Optional(), Length(max=2000)],
        render_kw={"rows": 2},
    )

    notes = TextAreaField(
        "یادداشت کلی",
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 2},
    )

    # برای submit vs save draft
    action = HiddenField(default="save")

    def validate_report_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("تاریخ گزارش نمی‌تواند در آینده باشد.")


class ReviewForm(FlaskForm):
    """فرم تأیید / رد / درخواست اصلاح."""

    action = SelectField(
        "تصمیم",
        choices=[
            ("approve", "تأیید نهایی"),
            ("request_revision", "درخواست اصلاح"),
            ("reject", "رد گزارش"),
        ],
        validators=[DataRequired()],
    )
    comment = TextAreaField(
        "توضیحات / دلیل",
        validators=[Optional(), Length(max=3000)],
        render_kw={"rows": 4, "placeholder": "در صورت رد یا درخواست اصلاح، توضیح الزامی است."},
    )
    apply_progress = SelectField(
        "اعمال پیشرفت روی آیتم‌ها پس از تأیید؟",
        choices=[("yes", "بله – پیشرفت به‌روز شود"), ("no", "خیر – فقط تأیید گزارش")],
        default="yes",
    )
