"""
Savings Goals Model & Data Access Module for FinWise
Handles per-user financial target setting, progress tracking, deposits, and status calculations.
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database import get_db
from app.models.transaction import parse_date


def ensure_goal_indexes():
    """
    Ensures index on user_id for high-performance isolated queries.
    """
    db = get_db()
    db.goals.create_index([("user_id", 1), ("created_at", -1)])


def create_goal(user_id, title, target_amount, current_amount=0.0, target_date=None, notes=""):
    """
    Creates a new savings goal bound to the authenticated user.
    Returns:
        tuple: (bool: success, str: message, dict or None: goal_doc)
    """
    try:
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid user identifier.", None

    clean_title = (title or "").strip()
    if not clean_title or len(clean_title) < 2:
        return False, "Goal title must be at least 2 characters.", None
    if len(clean_title) > 80:
        return False, "Goal title cannot exceed 80 characters.", None

    try:
        clean_target = round(float(target_amount), 2)
        if clean_target <= 0:
            return False, "Target amount must be greater than 0.", None
    except (ValueError, TypeError):
        return False, "Please enter a valid target amount.", None

    try:
        clean_current = round(float(current_amount or 0.0), 2)
        if clean_current < 0:
            return False, "Initial saved amount cannot be negative.", None
    except (ValueError, TypeError):
        clean_current = 0.0

    parsed_target_date = parse_date(target_date) if target_date else None
    status = "achieved" if clean_current >= clean_target else "in_progress"

    ensure_goal_indexes()
    db = get_db()

    goal_doc = {
        "user_id": u_oid,
        "title": clean_title,
        "target_amount": clean_target,
        "current_amount": clean_current,
        "target_date": parsed_target_date,
        "notes": (notes or "").strip(),
        "status": status,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    result = db.goals.insert_one(goal_doc)
    goal_doc["_id"] = result.inserted_id
    return True, f"Savings goal '{clean_title}' created successfully.", goal_doc


def get_user_goals(user_id):
    """
    Retrieves all savings goals for the user and calculates:
    - Percentage achieved (capped at 100% for progress bar display)
    - Remaining balance to reach goal
    - Display status badge ('Achieved' vs 'In Progress')
    """
    try:
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return []

    db = get_db()
    raw_goals = list(db.goals.find({"user_id": u_oid}).sort("created_at", -1))

    processed_goals = []
    for g in raw_goals:
        target = float(g.get("target_amount", 0.0))
        current = float(g.get("current_amount", 0.0))
        pct = round((current / target) * 100, 1) if target > 0 else 0.0
        remaining = max(0.0, round(target - current, 2))
        is_achieved = current >= target

        t_date = g.get("target_date")
        date_str = t_date.strftime("%d %b %Y") if isinstance(t_date, datetime) else "No target date"

        processed_goals.append({
            "_id": str(g["_id"]),
            "title": g.get("title", ""),
            "target_amount": target,
            "current_amount": current,
            "target_date_str": date_str,
            "notes": g.get("notes", ""),
            "percentage": pct,
            "bar_percentage": min(100.0, pct),
            "remaining": remaining,
            "is_achieved": is_achieved,
            "status_label": "Achieved 🎉" if is_achieved else "In Progress",
            "status_color": "emerald" if is_achieved else "indigo"
        })

    return processed_goals


def deposit_to_goal(goal_id, user_id, amount):
    """
    Adds savings to an existing goal, updating its balance and status.
    Strictly verifies ownership to prevent cross-user tampering.
    """
    try:
        g_oid = ObjectId(goal_id) if isinstance(goal_id, str) else goal_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid goal or user identifier."

    try:
        deposit_amt = round(float(amount), 2)
        if deposit_amt <= 0:
            return False, "Deposit amount must be greater than 0."
    except (ValueError, TypeError):
        return False, "Please provide a valid deposit amount."

    db = get_db()
    goal = db.goals.find_one({"_id": g_oid, "user_id": u_oid})
    if not goal:
        return False, "Goal not found or unauthorized."

    new_total = round(float(goal.get("current_amount", 0.0)) + deposit_amt, 2)
    target = float(goal.get("target_amount", 0.0))
    new_status = "achieved" if new_total >= target else "in_progress"

    db.goals.update_one(
        {"_id": g_oid, "user_id": u_oid},
        {
            "$set": {
                "current_amount": new_total,
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    msg = f"Deposited ₹{deposit_amt:,.2f}! Total saved is now ₹{new_total:,.2f}."
    if new_status == "achieved" and goal.get("status") != "achieved":
        msg = f"🎉 Congratulations! Goal '{goal.get('title')}' has been achieved!"

    return True, msg


def update_goal(goal_id, user_id, title=None, target_amount=None, current_amount=None, target_date=None, notes=None):
    """
    Updates an existing savings goal's properties, strictly verifying user ownership.
    Recalculates status if amounts change.
    """
    try:
        g_oid = ObjectId(goal_id) if isinstance(goal_id, str) else goal_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid goal or user identifier.", None

    db = get_db()
    existing = db.goals.find_one({"_id": g_oid, "user_id": u_oid})
    if not existing:
        return False, "Goal not found or unauthorized.", None

    updates = {}
    if title is not None:
        clean_title = (title or "").strip()
        if len(clean_title) < 2 or len(clean_title) > 80:
            return False, "Goal title must be between 2 and 80 characters.", None
        updates["title"] = clean_title

    if target_amount is not None:
        try:
            clean_target = round(float(target_amount), 2)
            if clean_target <= 0:
                return False, "Target amount must be greater than 0.", None
            updates["target_amount"] = clean_target
        except (ValueError, TypeError):
            return False, "Invalid target amount.", None

    if current_amount is not None:
        try:
            clean_curr = round(float(current_amount), 2)
            if clean_curr < 0:
                return False, "Current amount cannot be negative.", None
            updates["current_amount"] = clean_curr
        except (ValueError, TypeError):
            return False, "Invalid current amount.", None

    if target_date is not None:
        updates["target_date"] = parse_date(target_date) if target_date else None

    if notes is not None:
        updates["notes"] = (notes or "").strip()

    final_target = updates.get("target_amount", existing.get("target_amount", 0.0))
    final_curr = updates.get("current_amount", existing.get("current_amount", 0.0))
    updates["status"] = "achieved" if final_curr >= final_target else "in_progress"
    updates["updated_at"] = datetime.now(timezone.utc)

    db.goals.update_one({"_id": g_oid, "user_id": u_oid}, {"$set": updates})
    updated_doc = db.goals.find_one({"_id": g_oid, "user_id": u_oid})
    return True, "Savings goal updated successfully.", updated_doc


def delete_goal(goal_id, user_id):
    """
    Deletes a savings goal strictly verifying user ownership.
    """
    try:
        g_oid = ObjectId(goal_id) if isinstance(goal_id, str) else goal_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid goal or user identifier."

    db = get_db()
    result = db.goals.delete_one({"_id": g_oid, "user_id": u_oid})
    if result.deleted_count > 0:
        return True, "Savings goal deleted successfully."
    return False, "Goal not found or access denied."
