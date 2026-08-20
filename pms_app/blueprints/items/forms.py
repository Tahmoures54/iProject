# Path: pms_app/blueprints/items/forms.py

from __future__ import annotations
import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from pms_app.models.user import User  # برای populate responsible_owner_id در route

_FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

def _normalize_number(value: str) -> str:
    v = (value or "").strip().translate(_FA_TO_EN)
    v = v.replace(",", "").replace("٬", "")
    return v

class ItemForm(FlaskForm):
    # فیلدهای پایه
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    pms_item_number = StringField("PMS Item Number", validators=[Optional(), Length(max=80)])
    zone = StringField("Zone", validators=[Optional(), Length(max=120)])
    phase = StringField("Phase", validators=[Optional(), Length(max=80)])
    area = StringField("Area", validators=[Optional(), Length(max=120)])
    discipline = StringField("Discipline", validators=[Optional(), Length(max=80)])
    work_package = StringField("Work Package", validators=[Optional(), Length(max=120)])
    wbs_code = StringField("WBS Code", validators=[Optional(), Length(max=80)])
    boq_item_code = StringField("BOQ Item Code", validators=[Optional(), Length(max=80)])
    activity_id = StringField("Activity ID", validators=[Optional(), Length(max=80)])
    equipment_number = StringField("Equipment Number", validators=[Optional(), Length(max=80)])
    unit_of_measure = StringField("Unit of Measure", validators=[Optional(), Length(max=30)])
    tag_number = StringField("Tag Number", validators=[Optional(), Length(max=80)])
    currency = StringField("Currency", validators=[Optional(), Length(max=10)])
    cost_center = StringField("Cost Center", validators=[Optional(), Length(max=80)])

    # فیلدهای مالی
    original_amount = DecimalField("Original Amount", validators=[Optional()])
    adjusted_amount = DecimalField("Adjusted Amount", validators=[Optional()])
    weight_factor = DecimalField("Weight Factor", validators=[Optional()])
    planned_quantity = DecimalField("Planned Quantity", validators=[Optional()])
    actual_progress_percentage = DecimalField(
        "Actual Progress Percentage",
        validators=[Optional(), NumberRange(min=0, max=100)],
    )

    # وضعیت و اولویت
    status = SelectField(
        "Status",
        choices=[
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("blocked", "Blocked"),
            ("done", "Done"),
            ("closed", "Closed"),
        ],
        validators=[DataRequired()],
        default="open",
    )
    priority = SelectField(
        "Priority",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        validators=[DataRequired()],
        default="medium",
    )

    is_common = BooleanField("Is Common", default=False)
    workfront = StringField("Workfront", validators=[Optional(), Length(max=120)])
    risk_level = SelectField(
        "Risk Level",
        choices=[
            ("", "-"),
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        validators=[Optional()],
    )
    quality_metrics = TextAreaField("Quality Metrics", validators=[Optional()])
    acceptance_criteria = TextAreaField("Acceptance Criteria", validators=[Optional()])
    stakeholder_id = IntegerField("Stakeholder ID", validators=[Optional()])

    baseline_start_date = DateField("Baseline Start Date", validators=[Optional()], format="%Y-%m-%d")
    baseline_end_date = DateField("Baseline End Date", validators=[Optional()], format="%Y-%m-%d")
    actual_start_date = DateField("Actual Start Date", validators=[Optional()], format="%Y-%m-%d")
    actual_end_date = DateField("Actual End Date", validators=[Optional()], format="%Y-%m-%d")

    remarks = TextAreaField("Remarks", validators=[Optional()])

    # فیلدهای WBS با نام جدید LevelX_...
    Level1_project_no = StringField("Level1_project_no", validators=[Optional(), Length(max=50)])
    Level2_sub_project = StringField("Level2_sub_project", validators=[Optional(), Length(max=50)])
    Level3_phase = StringField("Level3_phase", validators=[Optional(), Length(max=50)])
    Level4_discipline = StringField("Level4_discipline", validators=[Optional(), Length(max=50)])
    Level5_area_zone = StringField("Level5_area_zone", validators=[Optional(), Length(max=50)])
    Level6_site_location = StringField("Level6_site_location", validators=[Optional(), Length(max=50)])
    Level7_equipment_tag = StringField("Level7_equipment_tag", validators=[Optional(), Length(max=50)])
    Level8_work_package = StringField("Level8_work_package", validators=[Optional(), Length(max=50)])
    Level9_activity_name = StringField("Level9_activity_name", validators=[Optional(), Length(max=200)])

    # فیلدهای دیگر جدید
    responsible_owner_id = SelectField(
        "Responsible Owner",
        coerce=int,
        validators=[Optional()],
    )
    is_milestone = BooleanField("Is Milestone", default=False)
    approval_status = SelectField(
        "Approval Status",
        choices=[("", "-"), ("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        validators=[Optional()],
    )
    approval_date = DateField("Approval Date", validators=[Optional()], format="%Y-%m-%d")
    revision_number = IntegerField("Revision Number", validators=[Optional(), NumberRange(min=0)])
    estimated_duration = DecimalField("Estimated Duration (days)", validators=[Optional(), NumberRange(min=0)])
    predecessors = StringField("Predecessors (comma-separated IDs)", validators=[Optional()])
    successors = StringField("Successors (comma-separated IDs)", validators=[Optional()])
    actual_quantity = DecimalField("Actual Quantity", validators=[Optional()])
    actual_cost = DecimalField("Actual Cost", validators=[Optional()])
    cost_category = SelectField(
        "Cost Category",
        choices=[("", "-"), ("labor", "Labor"), ("material", "Material"), ("equipment", "Equipment"), ("indirect", "Indirect")],
        validators=[Optional()],
    )
    funding_source = StringField("Funding Source", validators=[Optional(), Length(max=100)])
    resource_assignment = TextAreaField("Resource Assignment (comma-separated)", validators=[Optional()])

    submit = SubmitField("Save")

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        if formdata is not None:
            mutable = formdata.to_dict(flat=False) if hasattr(formdata, "to_dict") else None
            if isinstance(mutable, dict):
                for key in (
                    "original_amount", "adjusted_amount", "weight_factor",
                    "planned_quantity", "actual_progress_percentage",
                    "estimated_duration", "actual_quantity", "actual_cost",
                ):
                    if key in mutable and mutable[key]:
                        mutable[key] = [_normalize_number(mutable[key][0])]
                from werkzeug.datastructures import MultiDict
                formdata = MultiDict(mutable)
        super().process(formdata=formdata, obj=obj, data=data, **kwargs)


class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")


class ImportExcelForm(FlaskForm):
    file = FileField(
        "Excel File",
        validators=[
            FileRequired(message="No file selected."),
            FileAllowed(["xlsx", "xls"], message="Only Excel files allowed."),
        ],
    )
    submit = SubmitField("Upload")