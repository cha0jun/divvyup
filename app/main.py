from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated
from database import engine
from sqlmodel import SQLModel
from routers import expense, group, invitation, user
from models import User
from auth import get_current_user_optional

#Add startup event handler 
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(expense.router)
app.include_router(group.router)
app.include_router(invitation.router)
app.include_router(user.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

UserOptional = Annotated[User | None, Depends(get_current_user_optional)]

# --- HTML-RENDERING ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: UserOptional):
    return templates.TemplateResponse(
        "pages/index.html", 
        {"request": request, "user": user} 
    )

@app.get("/expenses", response_class=HTMLResponse)
async def read_root(request: Request, user: UserOptional): 
    return templates.TemplateResponse(
        "pages/expense.html", 
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