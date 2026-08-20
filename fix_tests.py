# fix_tests.py
from pathlib import Path

files = [
    Path("tests/test_auth.py"),
    Path("tests/test_models.py"),
    Path("tests/test_projects.py"),
]

for f in files:
    if f.exists():
        content = f.read_text(encoding="utf-8")
        # اصلاح ایمپورت اشتباه
        content = content.replace(
            "from pms_app.models.user import Role, User",
            "from pms_app.models import Role, User",
        )
        content = content.replace(
            "from pms_app.models.user import User, Role",
            "from pms_app.models import Role, User",
        )
        f.write_text(content, encoding="utf-8")
        print(f"✅ Fixed: {f}")