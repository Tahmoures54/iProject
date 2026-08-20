# Path: pms_app/utils/template_filters.py
"""Jinja template filters – including Jalali date formatting."""
from __future__ import annotations

from flask import Flask

from pms_app.utils.jalali import (
    format_jalali,
    format_jalali_month,
    format_jalali_month_name,
)


def register_template_filters(app: Flask) -> None:
    @app.template_filter("jalali")
    def jalali_filter(value, fmt="%Y/%m/%d"):
        """{{ some_date|jalali }} → 1403/06/29"""
        return format_jalali(value, fmt=fmt)

    @app.template_filter("jalali_long")
    def jalali_long_filter(value):
        """{{ some_date|jalali_long }} → ۲۹ شهریور ۱۴۰۳"""
        return format_jalali(value, with_month_name=True)

    @app.template_filter("jalali_month")
    def jalali_month_filter(value):
        """{{ some_date|jalali_month }} → 1403/06"""
        return format_jalali_month(value)

    @app.template_filter("jalali_month_name")
    def jalali_month_name_filter(value):
        return format_jalali_month_name(value)
