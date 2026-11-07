"""
Budget Model & Analytics Module for FinWise
Handles per-user monthly budgets, category thresholds, and real-time consumption tracking.
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database import get_db


def set_user_budget(user_id, category, monthly_limit):
    """
    Sets or updates a monthly budget threshold for a specific category.
    Strictly isolated per user.
    """
    try:
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid user identifier."

    clean_category = (category or "").strip()
    if not clean_category:
        return False, "Budget category is required."

    try:
        clean_limit = round(float(monthly_limit), 2)
        if clean_limit <= 0:
            return False, "Budget limit must be greater than 0."
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric budget limit."

    db = get_db()
    db.budgets.update_one(
        {"user_id": u_oid, "category": clean_category},
        {
            "$set": {
                "monthly_limit": clean_limit,
                "updated_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    return True, f"Budget for '{clean_category}' set to ₹{clean_limit:,.2f}."


def get_user_budgets_with_spending(user_id):
    """
    Retrieves all budgets for the authenticated user and computes
    actual current-month expense consumption per category.
    """
    try:
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return []

    db = get_db()
    user_budgets = list(db.budgets.find({"user_id": u_oid}).sort("category", 1))

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month

    # Aggregate current month's expenses by category for this user
    month_start = datetime(current_year, current_month, 1)
    # Next month start
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1
    month_end = datetime(next_year, next_month, 1)

    pipeline = [
        {
            "$match": {
                "user_id": u_oid,
                "type": "expense",
                "date": {"$gte": month_start, "$lt": month_end}
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total_spent": {"$sum": "$amount"}
            }
        }
    ]

    spent_by_category = {}
    for entry in db.transactions.aggregate(pipeline):
        spent_by_category[entry["_id"]] = round(float(entry["total_spent"]), 2)

    results = []
    for b in user_budgets:
        cat = b.get("category")
        limit = float(b.get("monthly_limit", 0.0))
        spent = spent_by_category.get(cat, 0.0)
        percentage = round((spent / limit) * 100, 1) if limit > 0 else 0.0
        remaining = max(0.0, round(limit - spent, 2))

        if percentage >= 100:
            status = "Exceeded"
            status_color = "rose"
            bar_color = "bg-rose-500"
        elif percentage >= 85:
            status = "Warning"
            status_color = "amber"
            bar_color = "bg-amber-500"
        else:
            status = "On Track"
            status_color = "emerald"
            bar_color = "bg-emerald-500"

        results.append({
            "_id": str(b["_id"]),
            "category": cat,
            "monthly_limit": limit,
            "spent": spent,
            "remaining": remaining,
            "percentage": percentage,
            "bar_percentage": min(100.0, percentage),
            "status": status,
            "status_color": status_color,
            "bar_color": bar_color
        })

    return results


def delete_user_budget(budget_id, user_id):
    """
    Deletes a user budget strictly verifying ownership.
    """
    try:
        b_oid = ObjectId(budget_id) if isinstance(budget_id, str) else budget_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid budget or user identifier."

    db = get_db()
    result = db.budgets.delete_one({"_id": b_oid, "user_id": u_oid})
    if result.deleted_count > 0:
        return True, "Budget deleted successfully."
    return False, "Budget not found or access denied."
