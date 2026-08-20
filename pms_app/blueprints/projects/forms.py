# Path: pms_app/blueprints/projects/forms.py
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    PasswordField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    ValidationError,
    EqualTo,
)

from pms_app.models.project import Project

INDUSTRY_CHOICES = [
    ("", "-- انتخاب حوزه پروژه --"),
    ("construction", "عمرانی و زیرساخت — کلی"),
    ("civil_building", "ساختمان و معماری"),
    ("civil_road_bridge_tunnel", "راه، پل و تونل"),
    ("civil_rail_metro", "راه‌آهن و مترو"),
    ("civil_water_wastewater", "آب و فاضلاب"),
    ("civil_dam_hydraulic", "سد و هیدرولیک"),
    ("civil_port_marine", "بنادر و ساحلی"),
    ("civil_pipeline_transmission", "خطوط انتقال"),
    ("oil_gas", "نفت و گاز — کلی"),
    ("petrochemical", "پتروشیمی"),
    ("epc_power_energy", "نیروگاه و انرژی"),
    ("epc_factory_production_line", "کارخانه و خط تولید"),
    ("it_software_product", "نرم‌افزار و محصول IT"),
    ("it_erp_crm", "پیاده‌سازی ERP/CRM"),
    ("org_pmo", "استقرار PMO"),
    ("other", "سایر"),
]

CURRENCY_CHOICES = [
    ("", "-- انتخاب ارز --"),
    ("IRR", "ریال ایران (IRR)"),
    ("USD", "دلار آمریکا (USD)"),
    ("EUR", "یورو (EUR)"),
    ("AED", "درهم امارات (AED)"),
    ("TRY", "لیر ترکیه (TRY)"),
    ("CNY", "یوان چین (CNY)"),
]

STATUS_CHOICES = [
    ("", "-- انتخاب وضعیت --"),
    ("proposed", "پیشنهادی"),
    ("feasibility", "امکان‌سنجی"),
    ("planning", "برنامه‌ریزی"),
    ("approval_pending", "در انتظار تأیید"),
    ("tender", "در مناقصه"),
    ("contracting", "در حال عقد قرارداد"),
    ("active", "در حال اجرا"),
    ("monitoring_control", "پایش و کنترل"),
    ("on_hold", "متوقف موقت"),
    ("suspended", "تعلیق"),
    ("canceled", "لغو شده"),
    ("completed", "پایان یافته"),
    ("delivered", "تحویل شده"),
    ("closed", "بسته شده"),
    ("warranty", "در دوره گارانتی"),
]

PROJECT_ROLE_CHOICES = [
    ("member", "عضو"),
    ("manager", "مدیر"),
    ("admin", "ادمین"),
]


class ProjectForm(FlaskForm):
    project_code = StringField(
        "کد پروژه",
        validators=[
            DataRequired(message="کد پروژه الزامی است."),
            Length(max=50, message="حداکثر ۵۰ کاراکتر."),
        ],
    )
    project_name = StringField(
        "نام پروژه",
        validators=[
            DataRequired(message="نام پروژه الزامی است."),
            Length(max=200, message="حداکثر ۲۰۰ کاراکتر."),
        ],
    )
    industry = SelectField(
        "حوزه / نوع پروژه",
        choices=INDUSTRY_CHOICES,
        validators=[Optional()],
        default="",
    )
    client_name = StringField(
        "کارفرما / صاحب پروژه",
        validators=[Optional(), Length(max=200)],
    )
    location = StringField(
        "موقعیت جغرافیایی",
        validators=[Optional(), Length(max=200)],
    )
    base_currency = SelectField(
        "ارز پایه",
        choices=CURRENCY_CHOICES,
        validators=[DataRequired(message="ارز پایه را انتخاب کنید.")],
        default="IRR",
    )
    start_date = DateField(
        "تاریخ شروع",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    finish_date = DateField(
        "تاریخ پایان",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    status = SelectField(
        "وضعیت پروژه",
        choices=STATUS_CHOICES,
        validators=[DataRequired(message="وضعیت پروژه الزامی است.")],
        default="proposed",
    )
    remarks = TextAreaField(
        "توضیحات / یادداشت‌ها",
        validators=[Optional(), Length(max=2000)],
    )
    submit = SubmitField("ذخیره پروژه")

    def __init__(self, project_id: int | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project_id = project_id

    def validate_project_code(self, field):
        code = (field.data or "").strip()
        if not code:
            return
        q = Project.query.filter_by(project_code=code)
        if self._project_id:
            q = q.filter(Project.id != self._project_id)
        if q.first():
            raise ValidationError("این کد پروژه قبلاً ثبت شده است. کد دیگری انتخاب کنید.")

    def validate_finish_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.")


class InviteToProjectForm(FlaskForm):
    full_name = StringField(
        "نام و نام خانوادگی",
        validators=[Optional(), Length(max=100, message="حداکثر ۱۰۰ کاراکتر.")],
    )
    email = StringField(
        "ایمیل کاربر",
        validators=[
            DataRequired(message="ایمیل الزامی است."),
            Email(message="لطفاً یک ایمیل معتبر وارد کنید."),
        ],
    )

    # added password fields
    password = PasswordField(
        "رمز عبور",
        validators=[
            DataRequired(message="رمز عبور الزامی است."),
            Length(min=6, message="رمز عبور باید حداقل ۶ کاراکتر باشد."),
        ],
    )
    password2 = PasswordField(
        "تکرار رمز عبور",
        validators=[
            DataRequired(message="تکرار رمز عبور الزامی است."),
            EqualTo("password", message="رمزها مطابقت ندارند."),
        ],
    )

    role = SelectField(
        "نقش در پروژه",
        choices=PROJECT_ROLE_CHOICES,
        default="member",
        validators=[DataRequired(message="نقش را انتخاب کنید.")],
    )
    invite_message = TextAreaField(
        "پیام دعوت",
        validators=[Optional(), Length(max=500)],
    )
    submit = SubmitField("ارسال دعوت‌نامه")

    def validate_email(self, field):
        """
        Normalize email. You can extend this validator to check:
        - if the email already belongs to an existing user,
        - if the user is already a member of this project (if project_id passed to form),
        - or to block certain domains.
        """
        email = (field.data or "").strip().lower()
        if not email:
            raise ValidationError("ایمیل الزامی است.")
        # simple normalization; further checks (DB) can be added here if needed
        field.data = email