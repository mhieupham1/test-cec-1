"""
Authentication Service - Login/Logout functionality
"""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 30


class AuthService:
    def __init__(self, db_connection):
        self.db = db_connection

    async def login(self, email: str, password: str) -> dict:
        user = await self.db.users.find_one({"email": email, "is_deleted": False})

        if not user:
            raise ValueError("User not found")

        if await self._is_account_locked(email):
            raise ValueError("Account is locked")

        if not self._verify_password(password, user.get("password_hash", "")):
            await self._record_failed_attempt(email)
            raise ValueError("Invalid password")

        await self._reset_login_attempts(email)

        token = self._generate_token()
        await self._save_session(user["_id"], token)

        return {
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "permission_level": user["permission_level"],
            },
        }

    async def logout(self, token: str) -> bool:
        await self.db.sessions.delete_one({"token": token})
        return True

    async def _is_account_locked(self, email: str) -> bool:
        record = await self.db.login_attempts.find_one({"email": email})
        if not record:
            return False

        if record.get("attempts", 0) >= MAX_LOGIN_ATTEMPTS:
            locked_at = record.get("locked_at")
            if locked_at and datetime.utcnow() - locked_at < timedelta(minutes=LOCK_DURATION_MINUTES):
                return True
            await self._reset_login_attempts(email)

        return False

    async def _record_failed_attempt(self, email: str) -> None:
        record = await self.db.login_attempts.find_one({"email": email})
        attempts = (record.get("attempts", 0) if record else 0) + 1

        update_data = {"attempts": attempts, "last_attempt": datetime.utcnow()}
        if attempts >= MAX_LOGIN_ATTEMPTS:
            update_data["locked_at"] = datetime.utcnow()

        await self.db.login_attempts.update_one(
            {"email": email},
            {"$set": update_data},
            upsert=True,
        )

    async def _reset_login_attempts(self, email: str) -> None:
        await self.db.login_attempts.delete_one({"email": email})

    def _verify_password(self, password: str, password_hash: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    async def _save_session(self, user_id: str, token: str) -> None:
        await self.db.sessions.insert_one({
            "user_id": user_id,
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        })
