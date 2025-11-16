from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated
from .database import engine
from sqlmodel import SQLModel
from .routers import expense, group, invitation, user, payment
from .models import User
from .auth import get_current_user_optional
from .crud import *
from .database import *


#Add startup event handler 
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(expense.router)
app.include_router(group.router)
app.include_router(invitation.router)
app.include_router(user.router)
app.include_router(payment.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

UserOptional = Annotated[User | None, Depends(get_current_user_optional)]

# --- HTML-RENDERING ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: UserOptional):
    return templates.TemplateResponse(
        "pages/index.html", 
        {"request": request, "user": user} 
    )

@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request, user: UserOptional):
    return templates.TemplateResponse(
        "pages/login.html", 
        {"request": request, "user": user} 
    )

@app.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request, user: UserOptional):
    return templates.TemplateResponse(
        "pages/register.html", 
        {"request": request, "user": user} 
    )


#----------GROUP--------------
@app.get("/groups", response_class=HTMLResponse)
async def groups_page(request: Request, user: UserOptional,  db: SessionDep):
    groups = get_groups_for_user(db, user.id) if user else []

    return templates.TemplateResponse("pages/groups.html", {
        "request": request,
        "groups": groups,
        "active_page": "groups"
    })

@app.get("/groups/{group_id}",response_class=HTMLResponse)
async def get_group_detail(request: Request, user: UserOptional, group_id: int, db: SessionDep):
    return templates.TemplateResponse("pages/group_details.html",
        {"request": request, "user": user, "group_id": group_id})
      
## Expense
@app.get("/groups/{group_id}/expenses", response_class=HTMLResponse)
async def read_root(request: Request, user: UserOptional, group_id:int):
    return templates.TemplateResponse(
        "pages/expense.html", 
        {"request": request, "user": user, "group_id":group_id} 
    )

@app.get("/expenses/{expense_id}", response_class=HTMLResponse)
async def read_root(request: Request, user: UserOptional, expense_id:int):
    return templates.TemplateResponse(
        "pages/expense_form.html", 
        {"request": request, "user": user, "expense_id":expense_id} 
    )