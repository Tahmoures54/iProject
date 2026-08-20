# Path: pms_app/blueprints/contracts/forms.py
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class ContractForm(FlaskForm):
    contract_number = StringField("شماره قرارداد", validators=[DataRequired(), Length(max=80)])
    contract_title = StringField("عنوان قرارداد", validators=[DataRequired(), Length(max=200)])
    contractor_name = StringField("پیمانکار", validators=[Optional(), Length(max=200)])

    contract_type = SelectField(
        "نوع قرارداد",
        choices=[
            ("EPC", "EPC"),
            ("EPCM", "EPCM"),
            ("Construction", "Construction"),
            ("Service", "Service"),
            ("Supply", "Supply"),
            ("UnitRate", "Unit Rate"),
        ],
        validators=[DataRequired()],
    )

    pricing_model = SelectField(
        "مدل قیمت‌گذاری",
        choices=[
            ("lumpsum", "Lump Sum"),
            ("unit_rate", "Unit Rate"),
            ("reimbursable", "Reimbursable"),
        ],
        validators=[DataRequired()],
    )

    currency = StringField("ارز", validators=[DataRequired(), Length(max=10)])
    original_contract_value = DecimalField("ارزش اولیه قرارداد", validators=[Optional()])
    revised_contract_value = DecimalField("ارزش اصلاح‌شده قرارداد", validators=[Optional()])

    start_date = DateField("شروع", validators=[Optional()])
    finish_date = DateField("پایان", validators=[Optional()])

    status = SelectField(
        "وضعیت",
        choices=[
            ("active", "فعال"),
            ("on_hold", "متوقف"),
            ("closed", "بسته"),
        ],
        validators=[DataRequired()],
    )

    remarks = TextAreaField("توضیحات", validators=[Optional()])
    submit = SubmitField("ذخیره")