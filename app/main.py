from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .database import engine
from sqlmodel import SQLModel
from .routers import expense, group, invitation, user

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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})
