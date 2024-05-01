from fastapi import FastAPI, Request, HTTPException, Depends, Form, status, responses
from fastapi.templating import Jinja2Templates
import models
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from database import engine, sessionlocal
from sqlalchemy.orm import Session
from sqlalchemy import func
import hashlib
from datetime import datetime
from datetime import timedelta
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from forms import AddEmployeForm, AddInternForm, PatchEmployeForm, DeleteEmployeForm


templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="36300cc0806f4828e5556813eb865837")


app.mount("/static", StaticFiles(directory="static"), name="static")


def form_data_parser(
    name: str = Form(...),
    email: str = Form(...),
    telephone: int = Form(...),
    password: str = Form(...),
    position: str = Form(...),
    naissance: str = Form(...),
    start_day: str = Form(...),
    salary: int = Form(...),
):
    return {
        "name": name,
        "email": email,
        "telephone": telephone,
        "password": password,
        "position": position,
        "naissance": naissance,
        "start_day": start_day,
        "salary": salary,
    }


def form_data_parser_stagaire(
    name: str = Form(...),
    ecole: str = Form(...),
    email: str = Form(...),
    telephone: int = Form(...),
    naissance: str = Form(...),
    start_day: str = Form(...),
    encadrant_id: int = Form(...),
):
    return {
        "name": name,
        "ecole": ecole,
        "email": email,
        "telephone": telephone,
        "naissance": naissance,
        "start_day": start_day,
        "encadrant_id": encadrant_id,
    }


def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


def form_data_parser_login(
    email: str = Form(...),
    password: str = Form(...),
):
    return {
        "email": email,
        "password": password,
    }


@app.get("/loginn")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/loginn")
async def login(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    employe = (
        db.query(models.Employe)
        .filter(func.lower(models.Employe.email) == func.lower(email))
        .first()
    )
    if employe and verify_password(password, employe.password):
        request.session["user_id"] = employe.id
        employe.is_authenticated = True
        db.commit()
        print(f"User ID in session: {request.session['user_id']}")
        print(f"Is admin: {employe.admin}")
        if employe.admin:
            print("Redirecting to /dashboard")
            return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        else:
            print("Redirecting to /dashemp")
            return RedirectResponse("/dashemp", status_code=status.HTTP_303_SEE_OTHER)
    print(f"User not authenticated or passwords do not match.")
    print(f"User ID: {employe.id if employe else 'None'}")
    print(f"Admin status: {employe.admin if employe else 'None'}")
    print(
        f"User in session: {request.session['user_id'] if 'user_id' in request.session else 'None'}"
    )
    error_message = "Email ou mot de passe incorrect"
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error_message}
    )


@app.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id:
        employe = db.query(models.Employe).filter(models.Employe.id == user_id).first()
        if employe:
            employe.is_authenticated = False
            db.commit()
    request.session.pop("user_id", None)
    return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    nb_people = get_nb_people(db)
    nb_stagaire = get_nb_stagaire(db)
    nb_requests = get_nb_requests(db)
    nb_requests_pending = get_nb_requests_pending(db)
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "nb_people": nb_people,
            "nb_stagaire": nb_stagaire,
            "nb_requests": nb_requests,
            "nb_requests_pending": nb_requests_pending,
            "employe": employe,
        },
    )


@app.get("/dashemp")
async def dashemp(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "dashemp.html", {"request": request, "employe": employe}
    )


@app.get("/sendrequest")
async def sendrequest(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "sendrequest.html", {"request": request, "employe": employe}
    )


def form_data_parser_request(
    id_emp: int = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    selectchoix: str = Form(...),
    startdate: str = Form(...),
    enddate: str = Form(...),
):
    return {
        "id_emp": id_emp,
        "name": name,
        "password": password,
        "selectchoix": selectchoix,
        "startdate": startdate,
        "enddate": enddate,
    }


def create_request(request_data: dict, db: Session = Depends(get_db)):
    id_employe = request_data["id_emp"]
    employe = db.query(models.Employe).filter(models.Employe.id == id_employe).first()

    if not employe:
        print(f"Employe not found for id: {id_employe}")
        raise HTTPException(status_code=404, detail="Employe not found")

    name_from_form = request_data["name"]
    if name_from_form != employe.name:
        print("ID and name are not identical")
        raise HTTPException(status_code=400, detail="ID and name are not identical")

    pass_from_form = request_data["password"]
    hashed_password_from_form = hashlib.sha256(pass_from_form.encode()).hexdigest()

    print(f"Hashed Password from Form: {hashed_password_from_form}")
    print(f"Password from Employe Table: {employe.password}")

    if hashed_password_from_form != employe.password:
        print("Password verification failed")
        raise HTTPException(status_code=400, detail="Invalid password")

    request_data["password"] = hashed_password_from_form
    request_emp = models.Demand(**request_data)

    try:
        db.add(request_emp)
        db.commit()
        db.refresh(request_emp)
        return request_emp
    except Exception as e:
        print(f"Error during database operation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/sendrequest")
async def requests(
    request: Request,
    request_data: dict = Depends(form_data_parser_request),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    create_request(request_data, db)
    db.commit()
    return templates.TemplateResponse(
        "sendrequest.html", {"request": request, "employe": employe}
    )


@app.get("/viewrequest")
async def viewrequest(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "requestsemp.html", {"request": request, "employe": employe}
    )


def form_data_parser_view_request(
    id_emp: int = Form(...),
    password: str = Form(...),
):
    return {
        "id_emp": id_emp,
        "password": password,
    }


@app.post("/viewrequest")
async def viewrequest(
    request: Request,
    request_result: dict = Depends(form_data_parser_view_request),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)

    id_employe = request_result["id_emp"]
    password_from_form = request_result["password"]
    error_message = []
    employe = db.query(models.Employe).filter(models.Employe.id == id_employe).first()
    if (
        not employe
        or employe.password != hashlib.sha256(password_from_form.encode()).hexdigest()
    ):
        # raise HTTPException(status_code=400, detail="Invalid ID or password")
        error_message.append("ID ou PASSWORD NON VALIDE !")

        return templates.TemplateResponse(
            "requestsemp.html",
            {
                "request": request,
                "error_message": error_message,
                "employe": employe,
            },
        )

    demande = db.query(models.Demand).filter(models.Demand.id_emp == id_employe).first()
    if not demande:
        # raise HTTPException(status_code=404, detail="No request found for this ID")
        error_message.append("No request found for this ID")

        return templates.TemplateResponse(
            "requestsemp.html",
            {
                "request": request,
                "error_message": error_message,
                "employe": employe,
            },
        )

    redirect_url = f"/result/{id_employe}"
    return RedirectResponse(url=redirect_url)


@app.post("/result/{id_employe}")
async def view_result(request: Request, id_employe: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == False)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    result = db.query(models.Demand).filter(models.Demand.id_emp == id_employe).all()
    return templates.TemplateResponse(
        "resultrequest.html", {"request": request, "result": result, "employe": employe}
    )


@app.get("/ajoutstagaire")
async def ajoutstagaire(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "ajoutstagaire.html", {"request": request, "employe": employe}
    )


def get_last_stagiaire_id(db: Session):
    return db.query(models.Stagaire).order_by(models.Stagaire.id.desc()).first().id


def create_stagaire(stagaire_data: dict, db: Session = Depends(get_db)):
    stagaire = models.Stagaire(**stagaire_data)
    db.add(stagaire)
    db.commit()
    db.refresh(stagaire)
    return stagaire


@app.post("/ajoutstagaire")
async def ajout_stagaire(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    stagaire_form = AddInternForm(request)
    await stagaire_form.load_data()
    success_messages = []
    if await stagaire_form.is_valid():
        await stagaire_form.exists_in_database(db)
        if not stagaire_form.errors:
            stagaire_data = {
                "name": stagaire_form.name,
                "ecole": stagaire_form.ecole,
                "email": stagaire_form.email,
                "telephone": stagaire_form.telephone,
                "naissance": stagaire_form.naissance,
                "start_day": stagaire_form.start_day,
                "end_day": stagaire_form.end_day,
                "encadrant_id": stagaire_form.encadrant_id,
            }
            create_stagaire(stagaire_data, db)
            last_stagiaire_id = get_last_stagiaire_id(db)
            encadrant_id = stagaire_data["encadrant_id"]
            encadrant = (
                db.query(models.Employe)
                .filter(models.Employe.id == encadrant_id)
                .first()
            )
            if not encadrant:
                raise HTTPException(status_code=404, detail="Encadrant not found")
            encadrant.stagiaire_id = last_stagiaire_id

            db.commit()
            success_messages.append("The stagaire has been added successfully")
            return templates.TemplateResponse(
                "ajoutstagaire.html",
                {
                    "request": request,
                    "employe": employe,
                    "success_messages": success_messages,
                },
            )
    errors = stagaire_form.errors
    return templates.TemplateResponse(
        "ajoutstagaire.html", {"request": request, "employe": employe, "errors": errors}
    )


@app.get("/updatestagaire")
async def updatestagaire(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "updatestagaire.html", {"request": request, "employe": employe}
    )


@app.post("/updatestagaire")
async def updateemploye(
    request: Request,
    id: int = Form(...),
    email: str = Form(None),
    telephone: int = Form(None),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    existing_stagaire = (
        db.query(models.Stagaire).filter(models.Stagaire.id == id).first()
    )
    if not existing_stagaire:
        raise HTTPException(status_code=404, detail="Stagaire not found")
    if email is not None:
        existing_stagaire.email = email
    if telephone is not None:
        existing_stagaire.telephone = telephone
    db.commit()
    db.refresh(existing_stagaire)

    return templates.TemplateResponse(
        "updatestagaire.html",
        {"request": request, "employe": employe},
    )


@app.get("/ajoutemploye")
async def ajoutemploye(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "ajoutemploye.html", {"request": request, "employe": employe}
    )


def create_employe(employe_data: dict, db: Session = Depends(get_db)):
    employe_data.setdefault("stagiaire_id", None)
    password = employe_data.get("password")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    employe_data["password"] = hashed_password
    employe = models.Employe(**employe_data)
    db.add(employe)
    db.commit()
    db.refresh(employe)
    return employe


@app.post("/ajoutemploye")
async def ajout_employe(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    employe_form = AddEmployeForm(request)
    await employe_form.load_data()
    success_messages = []
    if await employe_form.is_valid():
        await employe_form.exists_in_database(db)
        if not employe_form.errors:
            employe_data = {
                "name": employe_form.name,
                "telephone": employe_form.telephone,
                "email": employe_form.email,
                "password": employe_form.password,
                "position": employe_form.position,
                "naissance": employe_form.naissance,
                "start_day": employe_form.start_day,
                "salary": employe_form.salary,
            }

            create_employe(employe_data, db)
            success_messages.append("The employee has been added successfully!")
            return templates.TemplateResponse(
                "ajoutemploye.html",
                {
                    "request": request,
                    "success_messages": success_messages,
                    "employe": employe,
                },
            )

    errors = employe_form.errors
    return templates.TemplateResponse(
        "ajoutemploye.html",
        {"request": request, "errors": errors, "employe": employe},
    )


@app.get("/supemploye")
async def supemploye(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "supemploye.html", {"request": request, "employe": employe}
    )


def delete_person(person_id: int, db):

    existing_person = (
        db.query(models.Employe).filter(models.Employe.id == person_id).first()
    )
    if not existing_person:
        raise HTTPException(status_code=406, detail="Person not available")

    db.delete(existing_person)
    db.commit()
    return existing_person


@app.post("/supemploye")
async def supemploye(
    request: Request, form: DeleteEmployeForm = Depends(), db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    await form.load_data()
    if not await form.is_valid():
        return templates.TemplateResponse(
            "supemploye.html",
            {
                "request": request,
                "employe": employe,
                "error_messages": form.error_messages,
            },
        )

    person_id = form.id
    existing_person = (
        db.query(models.Employe).filter(models.Employe.id == person_id).first()
    )
    if not existing_person:
        error = "ID does not exist"
        return templates.TemplateResponse(
            "supemploye.html",
            {"request": request, "employe": employe, "error": error},
        )
    print(f"Received request to delete person with ID: {form.id}")

    db.delete(existing_person)
    db.commit()
    success_message = "Person deleted successfully."
    return templates.TemplateResponse(
        "supemploye.html",
        {"request": request, "employe": employe, "success_message": success_message},
    )


@app.get("/updateemploye")
async def updateemploye(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "updateemploye.html", {"request": request, "employe": employe}
    )


@app.post("/updateemploye")
async def updateemploye(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    employe_form = PatchEmployeForm(request)
    await employe_form.load_data()
    error_messages = []

    if not await employe_form.is_valid():
        error_messages = employe_form.error_messages
        return templates.TemplateResponse(
            "updateemploye.html",
            {"request": request, "employe": employe, "error_messages": error_messages},
        )

    existing_employe = (
        db.query(models.Employe).filter(models.Employe.id == employe_form.id).first()
    )
    if employe_form.telephone and employe_form.telephone != existing_employe.telephone:
        existing_telephone = (
            db.query(models.Employe)
            .filter(models.Employe.telephone == employe_form.telephone)
            .first()
        )
        if existing_telephone:
            error_messages.append(
                "Ce numéro de téléphone existe déjà dans la base de données"
            )

    if employe_form.email and employe_form.email != existing_employe.email:
        existing_email = (
            db.query(models.Employe)
            .filter(models.Employe.email == employe_form.email)
            .first()
        )
        if existing_email:
            error_messages.append("Cet e-mail existe déjà dans la base de données")
    if employe_form.email:
        try:
            str(employe_form.email)
        except ValueError:
            error_messages.append("L'email doit être une chaine")
        else:
            existing_employe.email = employe_form.email

    if employe_form.telephone:
        try:
            int(employe_form.telephone)
        except ValueError:
            error_messages.append("Le numéro de téléphone doit être un nombre")
        else:
            existing_employe.telephone = employe_form.telephone

    if employe_form.position:
        try:
            str(employe_form.position)
        except ValueError:
            error_messages.append("Le position doit être une chaine")
        else:
            existing_employe.position = employe_form.position

    if employe_form.salary:
        try:
            int(employe_form.salary)
        except ValueError:
            error_messages.append("Le salaire doit être un nombre")
        else:
            existing_employe.salary = employe_form.salary

    db.commit()
    db.refresh(existing_employe)
    success_messages = []
    success_messages.append("Employé modifié avec success.")
    return templates.TemplateResponse(
        "updateemploye.html",
        {
            "request": request,
            "employe": employe,
            "error_messages": error_messages,
            "success_messages": success_messages,
        },
    )


@app.get("/supstagaire")
async def supstagaire(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "supstagaire.html",
        {"request": request, "employe": employe},
    )


def delete_stagaire(person_id: int, sessionLocal):
    with sessionLocal as db:
        existing_person = (
            db.query(models.Stagaire).filter(models.Stagaire.id == person_id).first()
        )
        if not existing_person:
            raise HTTPException(status_code=406, detail="Person not available")

        encadrant = (
            db.query(models.Employe)
            .filter(models.Employe.stagiaire_id == person_id)
            .first()
        )

        if encadrant:
            encadrant.stagiaire_id = None

        db.delete(existing_person)
        db.commit()
        return existing_person


@app.post("/supstagaire")
async def supstagaire(
    request: Request, person_id: int = Form(...), db: Session = Depends(get_db)
):

    delete_stagaire(person_id, db)
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    return templates.TemplateResponse(
        "supstagaire.html",
        {"request": request, "employe": employe},
    )


def get_people_data(db: Session):
    return db.query(models.Employe).all()


@app.get("/workers")
async def workers(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    people_data = get_people_data(db)
    return templates.TemplateResponse(
        "tables.html",
        {"request": request, "people_data": people_data, "employe": employe},
    )


def get_stagiare_data(db: Session):
    return db.query(models.Stagaire).all()


@app.get("/stagaire")
async def stagaire(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    stagaire_data = get_stagiare_data(db)
    return templates.TemplateResponse(
        "stagaire.html",
        {"request": request, "stagaire_data": stagaire_data, "employe": employe},
    )


def get_requests_data(db: Session):
    return db.query(models.Demand).all()


@app.get("/requests")
async def requests(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    employe = (
        db.query(models.Employe)
        .filter(models.Employe.id == user_id, models.Employe.admin == True)
        .first()
    )
    if not employe or not employe.is_authenticated:
        return RedirectResponse("/loginn", status_code=status.HTTP_303_SEE_OTHER)
    requests_data = get_requests_data(db)
    return templates.TemplateResponse(
        "requests.html",
        {"request": request, "requests_data": requests_data, "employe": employe},
    )


@app.post("/accept/{request_id}")
async def accept_request(
    request: Request, request_id: int, db: Session = Depends(get_db)
):
    request_obj = db.query(models.Demand).filter(models.Demand.id == request_id).first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Demand not found")

    if request_obj.statut == "pending":
        request_obj.statut = "approved"
        db.commit()

    return RedirectResponse(
        url="/requests",
        status_code=303,
    )


@app.post("/decline/{request_id}")
async def decline_request(
    request: Request, request_id: int, db: Session = Depends(get_db)
):
    request_obj = db.query(models.Demand).filter(models.Demand.id == request_id).first()

    if not request_obj:
        raise HTTPException(status_code=404, detail="Demand not found")

    if request_obj.statut == "pending":
        request_obj.statut = "declined"
        db.commit()

    return RedirectResponse(
        url="/requests",
        status_code=303,
    )


def verify_password(plain_password, hashed_password):
    hashed_input_password = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed_input_password == hashed_password


def get_nb_people(db: Session):
    return db.query(models.Employe).count()


def get_nb_stagaire(db: Session):
    return db.query(models.Stagaire).count()


def get_nb_requests(db: Session):
    return db.query(models.Demand).count()


def get_nb_requests_pending(db: Session):
    return (
        db.query(func.count(models.Demand.id))
        .filter(models.Demand.statut == "pending")
        .scalar()
    )
