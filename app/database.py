from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def has_unlimited_access(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    if user.get("is_unlimited"):
        return True
    until = user.get("subscription_until")
    if not until:
        return False
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    return until > utcnow()


class Database:
    def __init__(self, uri: str, name: str):
        self.uri = uri
        self.name = name
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self) -> None:
        self.client = AsyncIOMotorClient(self.uri)
        self.db = self.client[self.name]
        await self.client.admin.command("ping")

        await self.db.users.create_index([("telegram_id", ASCENDING)], unique=True)
        await self.db.attempts.create_index(
            [("telegram_id", ASCENDING), ("created_at", DESCENDING)]
        )
        await self.db.attempts.create_index([("topic", ASCENDING)])
        await self.db.reminders.create_index(
            [("enabled", ASCENDING), ("timezone", ASCENDING), ("reminder_time", ASCENDING)]
        )

    async def close(self) -> None:
        if self.client:
            self.client.close()

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        return await self.db.users.find_one({"telegram_id": telegram_id})

    async def upsert_user(self, telegram_id: int, **data: Any) -> None:
        data["updated_at"] = utcnow()
        await self.db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": data, "$setOnInsert": {"created_at": utcnow()}},
            upsert=True,
        )

    async def save_attempt(self, data: dict[str, Any]) -> None:
        data.setdefault("created_at", utcnow())
        await self.db.attempts.insert_one(data)

    async def count_attempts(self, telegram_id: int) -> int:
        return await self.db.attempts.count_documents({"telegram_id": telegram_id})

    async def grant_extra_attempts(self, telegram_id: int, count: int) -> None:
        await self.db.users.update_one(
            {"telegram_id": telegram_id},
            {
                "$inc": {"extra_attempts": count},
                "$set": {"updated_at": utcnow()},
                "$setOnInsert": {"created_at": utcnow()},
            },
            upsert=True,
        )

    async def consume_extra_attempt(self, telegram_id: int) -> bool:
        result = await self.db.users.find_one_and_update(
            {"telegram_id": telegram_id, "extra_attempts": {"$gt": 0}},
            {"$inc": {"extra_attempts": -1}, "$set": {"updated_at": utcnow()}},
        )
        return result is not None

    async def extend_subscription(self, telegram_id: int, days: int) -> None:
        user = await self.get_user(telegram_id)
        now = utcnow()
        current_until = user.get("subscription_until") if user else None
        if current_until and current_until.tzinfo is None:
            current_until = current_until.replace(tzinfo=timezone.utc)
        base = current_until if current_until and current_until > now else now
        await self.upsert_user(telegram_id, subscription_until=base + timedelta(days=days))

    async def get_stats(self, telegram_id: int) -> dict[str, Any]:
        user = await self.get_user(telegram_id)
        total = await self.db.attempts.count_documents({"telegram_id": telegram_id})

        pipeline = [
            {"$match": {"telegram_id": telegram_id}},
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$overall_score"},
                "best_score": {"$max": "$overall_score"},
            }},
        ]
        score_data = await self.db.attempts.aggregate(pipeline).to_list(1)

        topics = await self.db.attempts.distinct("topic", {"telegram_id": telegram_id})
        last = await self.db.attempts.find_one(
            {"telegram_id": telegram_id},
            sort=[("created_at", DESCENDING)],
        )

        return {
            "user": user,
            "attempts": total,
            "topics": topics,
            "avg_score": score_data[0]["avg_score"] if score_data else None,
            "best_score": score_data[0]["best_score"] if score_data else None,
            "last_topic": last.get("topic") if last else None,
        }

    async def get_due_reminder_users(self, timezone_name: str, reminder_time: str):
        cursor = self.db.users.find({
            "reminder_enabled": True,
            "timezone": timezone_name,
            "reminder_time": reminder_time,
        })
        return await cursor.to_list(None)
