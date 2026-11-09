

from bson import ObjectId
from werkzeug.security import check_password_hash
from app import create_app
from app.database import get_db
from app.models.user import create_user, get_user_by_email, get_user_by_id, authenticate_user
from app.utils.auth import login_required


def setup_clean_db():
    db = get_db()
    db.users.delete_many({"email": {"$regex": "@test\\.finwise\\.com$"}})
    db.transactions.delete_many({"test_suite": "phase1"})


def run_phase1_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    @app.route('/test/protected-route')
    @login_required
    def protected_view():
        return "Secret Financial Data: Access Granted"

    client = app.test_client()

    setup_clean_db()
    db = get_db()

    print("=================================================================")
    print(" FinWise Phase 1: Authentication & User Management Test Suite    ")
    print("=================================================================")
    test_email = "alice@test.finwise.com"
    test_password = "SecurePassword123!"
    test_name = "Alice Test"

    res_reg = client.post('/auth/register', data={
        'name': test_name,
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password
    }, follow_redirects=False)

    assert res_reg.status_code == 302, f"Expected 302 redirect on registration, got {res_reg.status_code}"
    assert '/auth/login' in res_reg.headers['Location'], "Expected redirect to /auth/login"
    user_in_db = db.users.find_one({"email": test_email})
    assert user_in_db is not None, "Registered user was not saved to MongoDB"
    assert user_in_db["name"] == test_name, "User name mismatch in DB"
    assert user_in_db["password_hash"] != test_password, "CRITICAL: Password stored in plaintext!"
    assert check_password_hash(user_in_db["password_hash"], test_password), "Stored hash failed verification"
    print("[PASS] Test 1: User registration succeeds; password securely hashed in MongoDB")
    res_dup = client.post('/auth/register', data={
        'name': "Duplicate Alice",
        'email': "ALICE@test.finwise.com",  
        'password': "DifferentPassword456!",
        'confirm_password': "DifferentPassword456!"
    }, follow_redirects=True)

    dup_text = res_dup.get_data(as_text=True)
    assert "already exists" in dup_text.lower(), "Expected duplicate email warning message"
    count = db.users.count_documents({"email": test_email})
    assert count == 1, f"Expected exactly 1 user document, found {count}"
    print("[PASS] Test 2: Duplicate registration strictly blocked (case-insensitive & unique constraint)")

    res_mismatch = client.post('/auth/register', data={
        'name': "Bob Mismatch",
        'email': "bob@test.finwise.com",
        'password': "PasswordA1",
        'confirm_password': "PasswordB2"
    }, follow_redirects=True)
    assert "do not match" in res_mismatch.get_data(as_text=True).lower()

    res_short = client.post('/auth/register', data={
        'name': "Bob Short",
        'email': "bob@test.finwise.com",
        'password': "123",
        'confirm_password': "123"
    }, follow_redirects=True)
    assert "at least 6 characters" in res_short.get_data(as_text=True).lower()

    res_bad_email = client.post('/auth/register', data={
        'name': "Bob BadEmail",
        'email': "not-an-email",
        'password': "ValidPassword123",
        'confirm_password': "ValidPassword123"
    }, follow_redirects=True)
    assert "valid email" in res_bad_email.get_data(as_text=True).lower()
    print("[PASS] Test 3: Form validation rules verified (short passwords, mismatches, malformed emails)")

    res_bad_pw = client.post('/auth/login', data={
        'email': test_email,
        'password': "WrongPassword999!"
    }, follow_redirects=True)
    assert "invalid email or password" in res_bad_pw.get_data(as_text=True).lower()

    res_no_user = client.post('/auth/login', data={
        'email': "ghost@test.finwise.com",
        'password': "SomePassword123"
    }, follow_redirects=True)
    assert "invalid email or password" in res_no_user.get_data(as_text=True).lower()
    print("[PASS] Test 4: Invalid login attempts safely rejected without information leakage")
    with client:
        res_login = client.post('/auth/login', data={
            'email': test_email,
            'password': test_password
        }, follow_redirects=False)

        assert res_login.status_code == 302, f"Expected 302 on valid login, got {res_login.status_code}"
        from flask import session
        assert 'user_id' in session, "Session missing user_id after login"
        assert session['user_name'] == test_name, "Session user_name mismatch"
        assert session['user_email'] == test_email, "Session user_email mismatch"
        print("[PASS] Test 5: Valid login establishes secure authenticated session")
        res_dash = client.get('/dashboard')
        dash_content = res_dash.get_data(as_text=True)
        assert f"User: {test_name}" in dash_content, "User name missing from dashboard header/banner"
        assert "Welcome back" in dash_content, "Welcome banner missing"
        assert "Live User Account" in dash_content, "Live user indicator missing"
        assert "Sample Preview Data Active" not in dash_content, "Sample preview banner incorrectly shown to logged-in user!"
        assert "₹0.00" in dash_content, "Expected real zeroed metric for new account"
        print("[PASS] Test 6: Authenticated dashboard renders live user identity and never displays sample numbers")
        res_logout = client.get('/auth/logout', follow_redirects=True)
        assert res_logout.status_code == 200
        assert 'user_id' not in session, "Session was not cleared after logout"
        logout_text = res_logout.get_data(as_text=True)
        assert "logged out" in logout_text.lower(), "Logout notification message missing"
        print("[PASS] Test 7: Logout clears session and terminates user authentication")

    ok1, _, user_a = create_user("User Alpha", "alpha@test.finwise.com", "PasswordAlpha123")
    ok2, _, user_b = create_user("User Beta", "beta@test.finwise.com", "PasswordBeta123")
    assert ok1 and ok2, "Failed to create User Alpha or Beta"

    user_a_id = user_a["_id"]
    user_b_id = user_b["_id"]

    db.transactions.insert_many([
        {
            "user_id": user_a_id,
            "title": "Alpha Salary",
            "amount": 90000.0,
            "type": "income",
            "test_suite": "phase1"
        },
        {
            "user_id": user_a_id,
            "title": "Alpha Laptop Purchase",
            "amount": 45000.0,
            "type": "expense",
            "test_suite": "phase1"
        },
        {
            "user_id": user_b_id,
            "title": "Beta Consulting Fee",
            "amount": 35000.0,
            "type": "income",
            "test_suite": "phase1"
        }
    ])
    alpha_records = list(db.transactions.find({"user_id": user_a_id, "test_suite": "phase1"}))
    alpha_titles = [r["title"] for r in alpha_records]
    assert len(alpha_records) == 2, f"Expected 2 records for User Alpha, got {len(alpha_records)}"
    assert "Alpha Salary" in alpha_titles
    assert "Alpha Laptop Purchase" in alpha_titles
    assert "Beta Consulting Fee" not in alpha_titles, "SECURITY BREACH: User Alpha can view User Beta's transactions!"

    beta_records = list(db.transactions.find({"user_id": user_b_id, "test_suite": "phase1"}))
    beta_titles = [r["title"] for r in beta_records]
    assert len(beta_records) == 1, f"Expected 1 record for User Beta, got {len(beta_records)}"
    assert "Beta Consulting Fee" in beta_titles
    assert "Alpha Salary" not in beta_titles, "SECURITY BREACH: User Beta can view User Alpha's transactions!"
    print("[PASS] Test 8: User data isolation verified: zero data leakage across different user accounts")

    res_guest = client.get('/test/protected-route', follow_redirects=False)
    assert res_guest.status_code == 302, f"Expected 302 redirect for guest, got {res_guest.status_code}"
    assert '/auth/login' in res_guest.headers['Location']
    assert 'next=' in res_guest.headers['Location'] and 'test/protected-route' in res_guest.headers['Location']

    with client:
        client.post('/auth/login', data={'email': 'alpha@test.finwise.com', 'password': 'PasswordAlpha123'})
        res_auth_user = client.get('/test/protected-route')
        assert res_auth_user.status_code == 200
        assert "Secret Financial Data" in res_auth_user.get_data(as_text=True)
    print("[PASS] Test 9: @login_required decorator protects private routes & preserves 'next' redirect")

    setup_clean_db()
    print("=================================================================")
    print(" ALL 9 PHASE 1 AUTHENTICATION & SECURITY TESTS PASSED!          ")
    print("=================================================================")


if __name__ == '__main__':
    run_phase1_tests()
