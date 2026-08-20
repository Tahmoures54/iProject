from pms_app.extensions import db
from pms_app.models import User, Project

class UserFactory:
    _count = 0
    @classmethod
    def create(cls, **kwargs):
        cls._count += 1
        data = {
            "username": f"user_{cls._count}",
            "email": f"user_{cls._count}@test.com"
        }
        data.update(kwargs)
        user = User(**data)
        if "password" not in kwargs:
            user.set_password("Secret123!")
        db.session.add(user)
        db.session.commit()
        return user
