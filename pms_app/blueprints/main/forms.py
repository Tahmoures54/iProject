# Path: pms_app/blueprints/main/forms.py
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class SettingsForm(FlaskForm):
    document_types = TextAreaField("انواع اسناد", validators=[Optional(), Length(max=5000)])
    disciplines = TextAreaField("رشته‌ها", validators=[Optional(), Length(max=5000)])
    companies = TextAreaField("شرکت‌ها", validators=[Optional(), Length(max=5000)])
    task_statuses = TextAreaField("وضعیت‌های آیتم/وظیفه", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("ذخیره تنظیمات")


class PremiumActivateForm(FlaskForm):
    name = StringField("نام یا شرکت", validators=[DataRequired(), Length(max=200)])
    key = StringField("کلید اشتراک", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("فعال‌سازی اشتراک")