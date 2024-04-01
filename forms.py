from typing import Optional, List
from fastapi import Request
from sqlalchemy.orm import Session
from models import Employe


class AddEmployeForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.name: Optional[str] = None
        self.telephone: Optional[int] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.position: Optional[str] = None
        self.naissance: Optional[str] = None
        self.start_day: Optional[str] = None
        self.salary: Optional[int] = None

    async def load_data(self):
        form = await self.request.form()
        self.name = form.get("name")
        self.telephone = form.get("telephone")
        self.email = form.get("email")
        self.password = form.get("password")
        self.position = form.get("position")
        self.naissance = form.get("naissance")
        self.start_day = form.get("start_day")
        self.salary = form.get("salary")

    async def exists_in_database(self, db: Session):
        if (
            self.telephone
            and db.query(Employe).filter(Employe.telephone == self.telephone).first()
        ):
            self.errors.append(
                "Ce numéro de téléphone existe déjà dans la base de données"
            )

        if self.email and db.query(Employe).filter(Employe.email == self.email).first():
            self.errors.append("Cet e-mail existe déjà dans la base de données")

    async def is_valid(self):
        if not self.name or not len(self.name) > 5:
            self.errors.append("Name is required")
        if not self.telephone or not len(self.telephone) == 8:
            self.errors.append("Phone number is required")
        if (
            not self.email
            or not (self.email.__contains__("@"))
            or not (self.email.endswith(".com"))
        ):
            self.errors.append("Email is required")
        if not self.password or not len(self.password) > 6:
            self.errors.append("Password is required")
        if not self.position:
            self.errors.append("Position is required")
        if not self.naissance:
            self.errors.append("Birthday date is required")
        if not self.start_day:
            self.errors.append("Start date is required")
        if not self.salary:
            self.errors.append("Salary is required")
        if not self.errors:
            return True
        return False


class PatchEmployeForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.error_messages: List[str] = []
        self.id: Optional[int] = None
        self.email: Optional[str] = None
        self.telephone: Optional[int] = None
        self.position: Optional[str] = None
        self.salary: Optional[int] = None

    async def load_data(self):
        form = await self.request.form()
        self.id = form.get("id")
        self.email = form.get("email")
        self.telephone = form.get("telephone")
        self.position = form.get("position")
        self.salary = form.get("salary")

    async def is_valid(self):
        if not self.id:
            self.error_messages.append("ID is required")
        if (
            self.id
            and not self.email
            and not self.telephone
            and not self.position
            and not self.salary
        ):
            self.error_messages.append("You must edit one field at least")
        if not self.error_messages:
            return True
        return False


class DeleteEmployeForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.error_messages: List[str] = []
        self.id: Optional[int] = None

    async def load_data(self):
        form = await self.request.form()
        self.id = form.get("id")

    async def is_valid(self):
        if not self.id:
            self.error_messages.append("ID is required")
        if not self.error_messages:
            return True
        return False


class AddInternForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.name: Optional[str] = None
        self.ecole: Optional[str] = None
        self.email: Optional[str] = None
        self.telephone: Optional[int] = None
        self.naissance: Optional[str] = None
        self.start_day: Optional[str] = None
        self.end_day: Optional[str] = None
        self.encadrant_id: Optional[int] = None

    async def load_data(self):
        form = await self.request.form()
        self.name = form.get("name")
        self.ecole = form.get("ecole")
        self.email = form.get("email")
        self.telephone = form.get("telephone")
        self.naissance = form.get("naissance")
        self.start_day = form.get("start_day")
        self.end_day = form.get("end_day")
        self.encadrant_id = form.get("encadrant_id")

    async def exists_in_database(self, db: Session):
        if (
            self.telephone
            and db.query(Employe).filter(Employe.telephone == self.telephone).first()
        ):
            self.errors.append(
                "Ce numéro de téléphone existe déjà dans la base de données"
            )

        if self.email and db.query(Employe).filter(Employe.email == self.email).first():
            self.errors.append("Cet e-mail existe déjà dans la base de données")

    async def is_valid(self):
        if not self.name or not len(self.name) > 5:
            self.errors.append("Name is required")
        if not self.ecole or not len(self.ecole) > 5:
            self.errors.append("School is required")

        if (
            not self.email
            or not (self.email.__contains__("@"))
            or not (self.email.endswith(".com"))
        ):
            self.errors.append("Email is required")
        if not self.telephone or not len(self.telephone) == 8:
            self.errors.append("Phone number is required")
        if not self.naissance:
            self.errors.append("Birthday date is required")
        if not self.start_day:
            self.errors.append("Start date is required")
        if not self.end_day:
            self.errors.append("End date is required")
        if not self.encadrant_id:
            self.errors.append("Encadrant ID is required")
        if not self.errors:
            return True
        return False


class PatchInternForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.error_messages: List[str] = []
        self.id: Optional[int] = None
        self.email: Optional[str] = None
        self.telephone: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.id = form.get("id")
        self.email = form.get("email")
        self.telephone = form.get("telephone")

    async def is_valid(self):
        if not self.id:
            self.error_messages.append("ID is required")
        if not self.error_messages:
            return True
        return False
