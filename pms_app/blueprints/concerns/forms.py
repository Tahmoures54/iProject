# Path: pms_app/blueprints/concerns/forms.py
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    StringField,
    TextAreaField,
    BooleanField,
    IntegerField,
)
from wtforms.validators import DataRequired, Optional, Length


class ConcernForm(FlaskForm):
    title = StringField(
        "عنوان کانسرن",
        validators=[DataRequired(message="عنوان الزامی است."), Length(max=250)],
    )
    description = TextAreaField(
        "شرح دغدغه / کانسرن",
        validators=[Optional(), Length(max=10000)],
        render_kw={"rows": 5, "placeholder": "جزئیات مشکل، تأثیر، و زمینه را بنویسید..."},
    )

    project_id = SelectField("پروژه (اختیاری)", coerce=int, validators=[Optional()])

    category = SelectField(
        "دسته‌بندی",
        choices=[
            ("technical", "فنی / اجرایی"),
            ("schedule", "زمان‌بندی"),
            ("cost", "هزینه / مالی"),
            ("safety", "ایمنی (HSE)"),
            ("quality", "کیفیت"),
            ("resource", "منابع انسانی / تجهیزات"),
            ("contractual", "قراردادی"),
            ("organizational", "سازمانی / فرآیندی"),
            ("other", "سایر"),
        ],
        default="other",
    )

    priority = SelectField(
        "اولویت",
        choices=[
            ("low", "کم"),
            ("medium", "متوسط"),
            ("high", "بالا"),
            ("critical", "بحرانی"),
        ],
        default="medium",
    )

    visibility = SelectField(
        "سطح دسترسی مشاهده",
        choices=[
            ("private", "خصوصی — فقط من، مسئول و ادمین"),
            ("project", "اعضای پروژه"),
            ("managers_only", "فقط مدیران"),
            ("company", "کل شرکت"),
        ],
        default="project",
        description="چه کسانی این کانسرن را ببینند؟",
    )

    assignee_id = SelectField("مسئول رسیدگی", coerce=int, validators=[Optional()])
    due_date = DateField("مهلت رسیدگی", validators=[Optional()])
    tags_raw = StringField(
        "تگ‌ها (با کاما جدا کنید)",
        validators=[Optional(), Length(max=300)],
        render_kw={"placeholder": "تأخیر, بتن, ایمنی"},
    )


class ConcernCommentForm(FlaskForm):
    body = TextAreaField(
        "نظر",
        validators=[DataRequired(message="متن نظر الزامی است."), Length(max=5000)],
        render_kw={"rows": 3},
    )
    is_internal = BooleanField("نظر داخلی (فقط مدیران)", default=False)


class ConcernStatusForm(FlaskForm):
    action = SelectField(
        "عملیات",
        choices=[
            ("acknowledge", "دریافت / تأیید مشاهده"),
            ("start_progress", "شروع رسیدگی"),
            ("resolve", "حل‌شده"),
            ("close", "بستن"),
            ("escalate", "ارجاع به سطح بالاتر"),
            ("reopen", "بازگشایی"),
        ],
        validators=[DataRequired()],
    )
    note = TextAreaField(
        "یادداشت / راه‌حل",
        validators=[Optional(), Length(max=5000)],
        render_kw={"rows": 3},
    )
    assignee_id = SelectField("تغییر مسئول (اختیاری)", coerce=int, validators=[Optional()])
