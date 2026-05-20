"""
Application entry point
"""
from fastapi import FastAPI
from src.auth_service import AuthService
from src.user_service import UserService
from src.dashboard_service import DashboardService

app = FastAPI(title="User Management API", version="1.0.0")


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/v1/users")
async def get_users(page: int = 1, page_size: int = 20, search: str = None):
    pass


@app.post("/api/v1/users")
async def create_user(name: str, email: str, permission_level: str):
    pass


@app.put("/api/v1/users/{user_id}")
async def update_user(user_id: str, name: str = None, permission_level: str = None):
    pass


@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: str):
    pass


@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    pass


@app.post("/api/v1/auth/logout")
async def logout(token: str):
    pass


@app.get("/api/v1/dashboard")
async def get_dashboard(user_id: str):
    pass
