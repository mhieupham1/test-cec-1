"""
User Management Service
"""
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: str
    name: str
    email: str
    permission_level: str
    department: Optional[str] = None
    is_deleted: bool = False
    created_at: datetime = None
    updated_at: datetime = None


class UserService:
    def __init__(self, db_connection):
        self.db = db_connection

    async def get_users(self, page: int = 1, page_size: int = 20, search: str = None, sort_by: str = "created_at", filter_permission: str = None) -> dict:
        query = {"is_deleted": False}

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]

        if filter_permission:
            query["permission_level"] = filter_permission

        skip = (page - 1) * page_size
        total = await self.db.users.count_documents(query)
        users = await self.db.users.find(query).sort(sort_by, -1).skip(skip).limit(page_size).to_list(length=page_size)

        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def create_user(self, name: str, email: str, permission_level: str, department: str = None) -> User:
        existing = await self.db.users.find_one({"email": email, "is_deleted": False})
        if existing:
            raise ValueError(f"User with email {email} already exists")

        user_data = {
            "name": name,
            "email": email,
            "permission_level": permission_level,
            "department": department,
            "is_deleted": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.db.users.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        logger.info(f"Created user: {email}")
        return User(**user_data)

    async def update_user(self, user_id: str, name: str = None, permission_level: str = None, department: str = None) -> User:
        update_data = {"updated_at": datetime.utcnow()}

        if name:
            update_data["name"] = name
        if permission_level:
            update_data["permission_level"] = permission_level
        if department is not None:
            update_data["department"] = department

        result = await self.db.users.find_one_and_update(
            {"_id": user_id, "is_deleted": False},
            {"$set": update_data},
            return_document=True,
        )

        if not result:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Updated user: {user_id}")
        return result

    async def delete_user(self, user_id: str) -> bool:
        result = await self.db.users.find_one_and_update(
            {"_id": user_id, "is_deleted": False},
            {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}},
        )

        if not result:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Deleted user: {user_id}")
        return True
