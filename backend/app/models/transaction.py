import csv
import io
from datetime import datetime, date, timezone
from bson import ObjectId
from bson.errors import InvalidId
from app.database import get_db

VALID_TRANSACTION_TYPES = ('income', 'expense')
DEFAULT_CATEGORIES = [
    "Salary",
    "Side Income",
    "Investment",
    "Food & Dining",
    "Housing & Rent",
    "Utilities & Bills",
    "Transit & Fuel",
    "Entertainment",
    "Healthcare",
    "Shopping",
    "Education",
    "Other"
]


def ensure_transaction_indexes():
    db = get_db()
    db.transactions.create_index([("user_id", 1), ("date", -1)])
    db.transactions.create_index([("user_id", 1), ("type", 1)])


def parse_date(date_input):
    if isinstance(date_input, datetime):
        return date_input
    if isinstance(date_input, date):
        return datetime.combine(date_input, datetime.min.time())
    if isinstance(date_input, str) and date_input.strip():
        for fmt in ('%Y-%m-%d', '%d %b %Y', '%Y/%m/%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(date_input.strip(), fmt)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def create_transaction(user_id, title, amount, type_, category, date_input=None, notes=""):
    if not user_id:
        return False, "User identifier is required.", None
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid user identifier.", None

    clean_title = (title or "").strip()
    if not clean_title or len(clean_title) < 2:
        return False, "Transaction title must be at least 2 characters.", None
    if len(clean_title) > 100:
        return False, "Transaction title cannot exceed 100 characters.", None

    try:
        clean_amount = round(float(amount), 2)
        if clean_amount <= 0:
            return False, "Amount must be a positive number greater than 0.", None
    except (ValueError, TypeError):
        return False, "Please provide a valid numerical amount.", None

    clean_type = (type_ or "").strip().lower()
    if clean_type not in VALID_TRANSACTION_TYPES:
        return False, "Transaction type must be either 'income' or 'expense'.", None

    clean_category = (category or "Other").strip()
    txn_date = parse_date(date_input)

    ensure_transaction_indexes()
    db = get_db()

    doc = {
        "user_id": oid,
        "title": clean_title,
        "amount": clean_amount,
        "type": clean_type,
        "category": clean_category,
        "date": txn_date,
        "notes": (notes or "").strip(),
        "created_at": datetime.now(timezone.utc)
    }

    result = db.transactions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return True, "Transaction added successfully.", doc


def get_user_transactions(user_id, type_=None, category=None, limit=None, skip=0):

    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return []

    query = {"user_id": oid}
    if type_ and type_ in VALID_TRANSACTION_TYPES:
        query["type"] = type_
    if category and category.strip():
        query["category"] = category.strip()

    db = get_db()
    cursor = db.transactions.find(query).sort("date", -1).skip(skip)
    if limit and limit > 0:
        cursor = cursor.limit(limit)
    return list(cursor)


def get_transaction_by_id(txn_id, user_id):
    try:
        t_oid = ObjectId(txn_id) if isinstance(txn_id, str) else txn_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return None

    db = get_db()
    return db.transactions.find_one({"_id": t_oid, "user_id": u_oid})


def update_transaction(txn_id, user_id, title=None, amount=None, type_=None, category=None, date_input=None, notes=None):
    txn = get_transaction_by_id(txn_id, user_id)
    if not txn:
        return False, "Transaction not found or access denied."

    update_fields = {}
    if title is not None:
        clean_title = title.strip()
        if len(clean_title) < 2:
            return False, "Title must be at least 2 characters."
        update_fields["title"] = clean_title

    if amount is not None:
        try:
            clean_amt = round(float(amount), 2)
            if clean_amt <= 0:
                return False, "Amount must be greater than 0."
            update_fields["amount"] = clean_amt
        except (ValueError, TypeError):
            return False, "Invalid amount."

    if type_ is not None:
        clean_type = type_.strip().lower()
        if clean_type in VALID_TRANSACTION_TYPES:
            update_fields["type"] = clean_type

    if category is not None:
        update_fields["category"] = category.strip()

    if date_input is not None:
        update_fields["date"] = parse_date(date_input)

    if notes is not None:
        update_fields["notes"] = notes.strip()

    if not update_fields:
        return True, "No changes detected."

    update_fields["updated_at"] = datetime.now(timezone.utc)
    db = get_db()
    db.transactions.update_one(
        {"_id": txn["_id"], "user_id": txn["user_id"]},
        {"$set": update_fields}
    )
    return True, "Transaction updated successfully."


def delete_transaction(txn_id, user_id):
    try:
        t_oid = ObjectId(txn_id) if isinstance(txn_id, str) else txn_id
        u_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return False, "Invalid transaction or user identifier."

    db = get_db()
    result = db.transactions.delete_one({"_id": t_oid, "user_id": u_oid})
    if result.deleted_count > 0:
        return True, "Transaction deleted successfully."
    return False, "Transaction not found or unauthorized."


def get_user_financial_summary(user_id):
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    except InvalidId:
        return _empty_financial_summary()

    db = get_db()
    all_txns = list(db.transactions.find({"user_id": oid}).sort("date", -1))

    if not all_txns:
        return _empty_financial_summary()

    now = datetime.now(timezone.utc)
    current_year = now.year
    current_month = now.month

    total_income = 0.0
    total_expenses = 0.0
    monthly_income = 0.0
    monthly_expenses = 0.0
    category_expenses = {}
    months_keys = []
    month_labels = []
    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        key = f"{y:04d}-{m:02d}"
        months_keys.append(key)
        month_labels.append(datetime(y, m, 1).strftime('%b'))

    monthly_cashflow_data = {k: {"income": 0.0, "expenses": 0.0} for k in months_keys}

    for t in all_txns:
        amt = float(t.get("amount", 0.0))
        t_type = t.get("type", "expense")
        t_date = t.get("date") or t.get("created_at") or now
        if not isinstance(t_date, datetime):
            t_date = parse_date(t_date)

        if t_type == "income":
            total_income += amt
        else:
            total_expenses += amt
          
            cat = t.get("category", "Other")
            category_expenses[cat] = category_expenses.get(cat, 0.0) + amt

      
        if t_date.year == current_year and t_date.month == current_month:
            if t_type == "income":
                monthly_income += amt
            else:
                monthly_expenses += amt

       
        month_key = f"{t_date.year:04d}-{t_date.month:02d}"
        if month_key in monthly_cashflow_data:
            if t_type == "income":
                monthly_cashflow_data[month_key]["income"] += amt
            else:
                monthly_cashflow_data[month_key]["expenses"] += amt

    total_balance = round(total_income - total_expenses, 2)
    monthly_income = round(monthly_income, 2)
    monthly_expenses = round(monthly_expenses, 2)
    total_income = round(total_income, 2)
    total_expenses = round(total_expenses, 2)

   
    cashflow_income = [round(monthly_cashflow_data[k]["income"], 2) for k in months_keys]
    cashflow_expenses = [round(monthly_cashflow_data[k]["expenses"], 2) for k in months_keys]

    
    sorted_cats = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
    category_labels = [c[0] for c in sorted_cats] if sorted_cats else ["No Expenses"]
    category_values = [round(c[1], 2) for c in sorted_cats] if sorted_cats else [0.0]

    category_palette = [
        '#6366f1', '#10b981', '#f59e0b', '#f43f5e', '#0ea5e9',
        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b'
    ]
    category_colors = [category_palette[i % len(category_palette)] for i in range(len(category_labels))]

    return {
        "has_data": True,
        "total_balance": total_balance,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "recent_transactions": all_txns[:5],
        "all_transactions_count": len(all_txns),
        "charts": {
            "cash_flow": {
                "labels": month_labels,
                "income": cashflow_income,
                "expenses": cashflow_expenses
            },
            "categories": {
                "labels": category_labels,
                "data": category_values,
                "colors": category_colors
            }
        }
    }


def _empty_financial_summary():
  
    now = datetime.now(timezone.utc)
    month_labels = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        month_labels.append(datetime(y, m, 1).strftime('%b'))

    return {
        "has_data": False,
        "total_balance": 0.0,
        "total_income": 0.0,
        "total_expenses": 0.0,
        "monthly_income": 0.0,
        "monthly_expenses": 0.0,
        "recent_transactions": [],
        "all_transactions_count": 0,
        "charts": {
            "cash_flow": {
                "labels": month_labels,
                "income": [0.0] * 6,
                "expenses": [0.0] * 6
            },
            "categories": {
                "labels": ["No Expenses Recorded"],
                "data": [0.0],
                "colors": ["#cbd5e1"]
            }
        }
    }


def generate_transactions_csv(user_id, type_=None, category=None):
   
    transactions = get_user_transactions(user_id, type_=type_, category=category)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\r\n')

  
    writer.writerow(["Transaction ID", "Date", "Type", "Title", "Category", "Amount (INR)", "Notes"])

    for txn in transactions:
        t_date = txn.get("date")
        date_str = t_date.strftime("%Y-%m-%d") if isinstance(t_date, datetime) else ""
        t_type = (txn.get("type") or "").capitalize()
        title = txn.get("title", "")
        cat = txn.get("category", "")
        amount = f"{float(txn.get('amount', 0.0)):.2f}"
        notes = txn.get("notes", "")

        writer.writerow([
            str(txn.get("_id", "")),
            date_str,
            t_type,
            title,
            cat,
            amount,
            notes
        ])

    return output.getvalue()
