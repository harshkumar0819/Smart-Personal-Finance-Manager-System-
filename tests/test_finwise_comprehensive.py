
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from flask import session
from werkzeug.security import check_password_hash

from app import create_app
from app.database import get_db, check_db_connection
from app.models.user import create_user
from app.models.transaction import (
    create_transaction,
    get_transaction_by_id,
    delete_transaction,
    get_user_financial_summary,
)
from app.models.budget import (
    set_user_budget,
    delete_user_budget,
    get_user_budgets_with_spending,
)


USER_EMAILS = (
    "alice@comp.finwise.com",
    "bob@comp.finwise.com",
)


def cleanup_test_database():
    db = get_db()

    user_ids = [
        user["_id"]
        for user in db.users.find(
            {"email": {"$in": list(USER_EMAILS)}},
            {"_id": 1},
        )
    ]

    if user_ids:
        db.transactions.delete_many({"user_id": {"$in": user_ids}})
        db.budgets.delete_many({"user_id": {"$in": user_ids}})
        db.users.delete_many({"_id": {"$in": user_ids}})


def run_comprehensive_tests():
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    client = app.test_client()

    with app.app_context():
        db = get_db()

        try:
            cleanup_test_database()

            print("Starting FinWise verification")

            response = client.get("/")
            assert response.status_code == 200

            page = response.get_data(as_text=True)

            assert (
                "Guest Demo Mode" in page
                or "Sample Preview Data" in page
            )
            assert "Log In" in page
            assert "Create Account" in page or "Register" in page

            private_pages = (
                "/income",
                "/expenses",
                "/budgets",
                "/analytics",
            )

            for path in private_pages:
                response = client.get(
                    path,
                    follow_redirects=False,
                )

                assert response.status_code == 302
                assert "/auth/login" in response.headers.get(
                    "Location",
                    "",
                )

            print("Guest access and protected pages: passed")

            alice_email = USER_EMAILS[0]
            alice_password = "AliceSecurePass123!"
            alice_name = "Alice Comprehensive"

            response = client.post(
                "/auth/register",
                data={
                    "name": alice_name,
                    "email": alice_email,
                    "password": alice_password,
                    "confirm_password": alice_password,
                },
                follow_redirects=False,
            )

            assert response.status_code == 302

            alice_doc = db.users.find_one(
                {"email": alice_email}
            )

            assert alice_doc is not None
            assert alice_doc["password_hash"] != alice_password
            assert check_password_hash(
                alice_doc["password_hash"],
                alice_password,
            )

            response = client.post(
                "/auth/login",
                data={
                    "email": alice_email,
                    "password": alice_password,
                },
                follow_redirects=False,
            )

            assert response.status_code == 302

            with client:
                client.post(
                    "/auth/login",
                    data={
                        "email": alice_email,
                        "password": alice_password,
                    },
                )

                assert session.get("user_id") == str(
                    alice_doc["_id"]
                )

                response = client.get(
                    "/auth/logout",
                    follow_redirects=False,
                )

                assert response.status_code == 302
                assert "user_id" not in session

            print("Registration, password hashing, login and logout: passed")

            with client:
                client.post(
                    "/auth/login",
                    data={
                        "email": alice_email,
                        "password": alice_password,
                    },
                )

                pages = (
                    ("/income", "Income Tracking"),
                    ("/expenses", "Expenses Log"),
                    ("/budgets", "Monthly Budgets"),
                    (
                        "/analytics",
                        "Analytics & Financial Reports",
                    ),
                )

                for path, expected_text in pages:
                    response = client.get(path)

                    assert response.status_code == 200
                    assert expected_text in response.get_data(
                        as_text=True
                    )

            print("Main navigation pages: passed")

            connected, message, details = check_db_connection()

            assert connected is True, (
                f"Database connection failed: {message}"
            )
            assert details.get("status") == "connected"
            assert details.get("read_write") == "verified"

            response = client.get("/health/db")

            assert response.status_code == 200

            health_data = response.get_json()

            assert health_data["status"] == "connected"
            assert health_data["read_write"] == "verified"

            health_text = str(health_data).lower()

            assert "password" not in health_text
            assert "mongodb+srv://" not in health_text

            print("Database connection and health endpoint: passed")

            alice_id = alice_doc["_id"]

            empty_summary = get_user_financial_summary(alice_id)

            assert empty_summary["total_balance"] == 0.0
            assert empty_summary["total_income"] == 0.0
            assert empty_summary["total_expenses"] == 0.0
            assert empty_summary["recent_transactions"] == []

            with client:
                client.post(
                    "/auth/login",
                    data={
                        "email": alice_email,
                        "password": alice_password,
                    },
                )

                response = client.get("/dashboard")
                dashboard = response.get_data(as_text=True)

                assert response.status_code == 200
                assert "₹0.00" in dashboard
                assert "No transactions recorded yet" in dashboard
                assert "Sample Preview Data Active" not in dashboard

            transactions = (
                create_transaction(
                    alice_id,
                    "Monthly Salary",
                    60000.0,
                    "income",
                    "Salary",
                    notes="TEST_COMP_INC1",
                ),
                create_transaction(
                    alice_id,
                    "Freelance Work",
                    15000.0,
                    "income",
                    "Side Income",
                    notes="TEST_COMP_INC2",
                ),
                create_transaction(
                    alice_id,
                    "Apartment Rent",
                    20000.0,
                    "expense",
                    "Housing & Rent",
                    notes="TEST_COMP_EXP1",
                ),
                create_transaction(
                    alice_id,
                    "Supermarket",
                    5000.0,
                    "expense",
                    "Food & Dining",
                    notes="TEST_COMP_EXP2",
                ),
            )

            assert all(result[0] for result in transactions)

            salary_transaction = transactions[0][2]

            summary = get_user_financial_summary(alice_id)

            assert summary["total_income"] == 75000.0
            assert summary["total_expenses"] == 25000.0
            assert summary["total_balance"] == 50000.0
            assert summary["monthly_income"] == 75000.0
            assert summary["monthly_expenses"] == 25000.0
            assert len(summary["recent_transactions"]) == 4

            set_user_budget(
                alice_id,
                "Food & Dining",
                10000.0,
            )

            budgets = get_user_budgets_with_spending(alice_id)

            assert len(budgets) == 1
            assert budgets[0]["spent"] == 5000.0
            assert budgets[0]["percentage"] == 50.0
            assert budgets[0]["remaining"] == 5000.0
            assert budgets[0]["status"] == "On Track"

            with client:
                client.post(
                    "/auth/login",
                    data={
                        "email": alice_email,
                        "password": alice_password,
                    },
                )

                response = client.get("/dashboard")
                dashboard = response.get_data(as_text=True)

                assert response.status_code == 200
                assert "50,000.00" in dashboard
                assert "75,000.00" in dashboard
                assert "25,000.00" in dashboard
                assert "Monthly Salary" in dashboard
                assert "Apartment Rent" in dashboard

            print("Dashboard and budget calculations: passed")

            bob_email = USER_EMAILS[1]
            bob_password = "BobSecurePass456!"

            created, message, bob_doc = create_user(
                "Bob Comprehensive",
                bob_email,
                bob_password,
            )

            assert created, (
                f"Could not create second test user: {message}"
            )

            bob_id = bob_doc["_id"]

            create_transaction(
                bob_id,
                "Bob Consulting",
                30000.0,
                "income",
                "Side Income",
                notes="TEST_COMP_BOB1",
            )

            create_transaction(
                bob_id,
                "Bob New Phone",
                12000.0,
                "expense",
                "Shopping",
                notes="TEST_COMP_BOB2",
            )

            set_user_budget(
                bob_id,
                "Shopping",
                15000.0,
            )

            bob_summary = get_user_financial_summary(bob_id)

            assert bob_summary["total_balance"] == 18000.0
            assert bob_summary["total_income"] == 30000.0
            assert bob_summary["total_expenses"] == 12000.0

            bob_titles = [
                item["title"]
                for item in bob_summary["recent_transactions"]
            ]

            assert "Monthly Salary" not in bob_titles
            assert "Apartment Rent" not in bob_titles

            alice_summary = get_user_financial_summary(alice_id)

            alice_titles = [
                item["title"]
                for item in alice_summary["recent_transactions"]
            ]

            assert "Bob Consulting" not in alice_titles
            assert "Bob New Phone" not in alice_titles

            salary_id = salary_transaction["_id"]

            deleted, message = delete_transaction(
                salary_id,
                bob_id,
            )

            assert deleted is False

            assert get_transaction_by_id(
                salary_id,
                alice_id,
            ) is not None

            bob_budget = db.budgets.find_one(
                {
                    "user_id": bob_id,
                    "category": "Shopping",
                }
            )

            assert bob_budget is not None

            deleted, message = delete_user_budget(
                bob_budget["_id"],
                alice_id,
            )

            assert deleted is False

            print("Multi-user data isolation: passed")

            gitignore_path = PROJECT_ROOT / ".gitignore"

            assert gitignore_path.exists()

            gitignore_text = gitignore_path.read_text(
                encoding="utf-8"
            )

            assert ".env" in gitignore_text.splitlines()

            print("Environment file protection: passed")
            print("All FinWise verification checks completed")

        finally:
            cleanup_test_database()


if __name__ == "__main__":
    run_comprehensive_tests()
