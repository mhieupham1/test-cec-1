"""
Dashboard Service
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300


class DashboardService:
    def __init__(self, db_connection, cache=None):
        self.db = db_connection
        self.cache = cache

    async def get_dashboard_data(self, user_id: str) -> dict:
        if self.cache:
            cached = await self.cache.get(f"dashboard:{user_id}")
            if cached:
                return cached

        user = await self.db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError("User not found")

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        today_activities = await self.db.activities.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today},
        })

        weekly_report = await self._get_weekly_report(user_id, week_ago)
        recent_projects = await self._get_recent_projects(user_id)
        notifications = await self._get_unread_notifications(user_id)

        data = {
            "user": {
                "name": user["name"],
                "avatar": user.get("avatar_url"),
            },
            "today_activities": today_activities,
            "weekly_report": weekly_report,
            "recent_projects": recent_projects,
            "unread_notifications": notifications,
        }

        if self.cache:
            await self.cache.set(f"dashboard:{user_id}", data, ttl=CACHE_TTL_SECONDS)

        return data

    async def _get_weekly_report(self, user_id: str, since: datetime) -> dict:
        pipeline = [
            {"$match": {"user_id": user_id, "created_at": {"$gte": since}}},
            {"$group": {"_id": {"$dayOfWeek": "$created_at"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        results = await self.db.activities.aggregate(pipeline).to_list(length=7)
        return {"daily_counts": results}

    async def _get_recent_projects(self, user_id: str, limit: int = 5) -> list:
        projects = await self.db.projects.find(
            {"members": user_id, "is_deleted": False}
        ).sort("updated_at", -1).limit(limit).to_list(length=limit)
        return projects

    async def _get_unread_notifications(self, user_id: str) -> int:
        return await self.db.notifications.count_documents({
            "user_id": user_id,
            "is_read": False,
        })
