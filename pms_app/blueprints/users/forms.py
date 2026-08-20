# Path: pms_app/blueprints/users/forms.py
from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from pms_app.models.user import User


class DeleteForm(FlaskForm):
    """فرم ساده برای حذف (فقط CSRF + submit)."""
    submit = SubmitField("حذف")


class InviteForm(FlaskForm):
    """فرم دعوت کاربر با ایمیل."""
    email = StringField(
        "ایمیل",
        validators=[
            DataRequired(message="ایمیل الزامی است."),
            Email(message="یک ایمیل معتبر وارد کنید."),
            Length(max=120),
        ],
    )
    submit = SubmitField("ارسال دعوت")


class UserForm(FlaskForm):
    """
    فرم ایجاد/ویرایش کاربر
    """
    full_name = StringField("نام و نام خانوادگی", validators=[Optional(), Length(max=120)])
    company_name = StringField("نام شرکت", validators=[Optional(), Length(max=120)])
    phone = StringField("شماره موبایل", validators=[Optional(), Length(max=32)])
    email = StringField(
        "ایمیل",
        validators=[
            DataRequired(message="ایمیل الزامی است."),
            Email(message="یک ایمیل معتبر وارد کنید."),
            Length(max=120),
        ],
    )
    is_active = BooleanField("حساب فعال باشد", default=True)

    password = PasswordField("رمز عبور", validators=[Optional(), Length(min=6, max=128)])
    password2 = PasswordField("تکرار رمز عبور", validators=[Optional()])

    # roles: choices را باید در route بگذارید (id, title)
    roles = SelectMultipleField("نقش‌ها", coerce=int, validators=[Optional()], choices=[])

    # متادیتای اختیاری برای پیمانکار (اگر backend پشتیبانی کند)
    contractor_company = StringField("شرکت پیمانکاری", validators=[Optional(), Length(max=120)])

    submit = SubmitField("ذخیره تغییرات")

    def __init__(self, user_id: int | None = None, *args, **kwargs):
        """
        routes.py شما موقع ویرایش، فرم را اینطور می‌سازد: UserForm(obj=user)
        و user_id پاس نمی‌دهد؛ پس اینجا اگر obj وجود داشت، id را از obj می‌گیریم
        تا validate_email روی خودِ همان کاربر گیر ندهد.
        """
        obj = kwargs.get("obj", None)
        super().__init__(*args, **kwargs)

        if user_id is not None:
            self._user_id = int(user_id)
        else:
            self._user_id = int(getattr(obj, "id", 0)) or None if obj is not None else None

    def validate_email(self, field):
        raw = (field.data or "").strip()
        email = raw.lower()
        if not email:
            raise ValidationError("ایمیل الزامی است.")

        q = User.query.filter(User.email.ilike(email))
        if self._user_id:
            q = q.filter(User.id != self._user_id)
        if q.first():
            raise ValidationError("این ایمیل قبلاً توسط کاربر دیگری استفاده شده است.")

        field.data = email

    def validate_phone(self, field):
        raw = (field.data or "").strip()
        if not raw:
            return

        if not re.fullmatch(r"[0-9۰-۹+\-\s()]+", raw):
            raise ValidationError("شماره موبایل فقط می‌تواند شامل اعداد، +، -، فاصله و پرانتز باشد.")

        trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        normalized = raw.translate(trans)

        digits = re.sub(r"\D", "", normalized)
        if len(digits) < 10:
            raise ValidationError("شماره موبایل باید حداقل ۱۰ رقم داشته باشد.")

        field.data = normalized

    def validate_password2(self, field):
        pw = (self.password.data or "")
        repeat = (field.data or "")

        if pw:
            if not repeat:
                raise ValidationError("لطفاً رمز عبور را تکرار کنید.")
            if pw != repeat:
                raise ValidationError("رمز عبور و تکرار آن یکسان نیستند.")