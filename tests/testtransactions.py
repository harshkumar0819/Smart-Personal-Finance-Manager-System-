
from app import create_app
from app.models.user import create_user
from app.models.transaction import create_transaction, get_transaction_by_id, get_user_financial_summary

def run_tests():
    app = create_app()
    client = app.test_client()

    print("=========================================================================")
    print(" FinWise Stage 3B -- Transaction Editing & User Isolation Test Suite     ")
    print("=========================================================================")

    dummy_id = "507f1f77bcf86cd799439011"
    res_guest_get = client.get(f'/transactions/{dummy_id}/edit')
    assert res_guest_get.status_code == 302, f"Expected 302 redirect, got {res_guest_get.status_code}"
    assert '/auth/login' in res_guest_get.headers.get('Location', '')

    res_guest_post = client.post(f'/transactions/{dummy_id}/edit', data={'title': 'Hacked Title'})
    assert res_guest_post.status_code == 302
    assert '/auth/login' in res_guest_post.headers.get('Location', '')
    print("[PASS] Test 1: Guest access to /transactions/<id>/edit strictly blocked and redirected to login")

    from app.database import get_db
    db = get_db()
    db.users.delete_many({"email": {"$in": ["alice_edit_test@example.com", "bob_edit_test@example.com"]}})

    u1_email = "alice_edit_test@example.com"
    u1_pass = "AliceSecure123!"
    u1_name = "Alice EditUser"
    ok1, _, user1_doc = create_user(u1_name, u1_email, u1_pass)
    assert ok1, "Failed to create user Alice"
    u1_id = user1_doc["_id"]
    db.transactions.delete_many({"user_id": u1_id})

    u2_email = "bob_edit_test@example.com"
    u2_pass = "BobSecure123!"
    u2_name = "Bob TamperUser"
    ok2, _, user2_doc = create_user(u2_name, u2_email, u2_pass)
    assert ok2, "Failed to create user Bob"
    u2_id = user2_doc["_id"]
    db.transactions.delete_many({"user_id": u2_id})

    _, _, inc_doc = create_transaction(u1_id, "Alice Original Salary", 50000.0, "income", "Salary")
    _, _, exp_doc = create_transaction(u1_id, "Alice Original Groceries", 4000.0, "expense", "Food & Dining")
    inc_id = str(inc_doc["_id"])
    exp_id = str(exp_doc["_id"])

    client.post('/auth/login', data={'email': u1_email, 'password': u1_pass})

    res_get_inc = client.get(f'/transactions/{inc_id}/edit')
    assert res_get_inc.status_code == 200
    json_inc = res_get_inc.get_json()
    assert json_inc["success"] is True
    assert json_inc["transaction"]["title"] == "Alice Original Salary"
    assert json_inc["transaction"]["amount"] == 50000.0

    res_post_inc = client.post(f'/transactions/{inc_id}/edit', data={
        'title': 'Alice Promoted Salary',
        'amount': '65000.00',
        'category': 'Salary',
        'type': 'income',
        'notes': 'Promoted to Senior Lead',
        'redirect_to': 'income'
    })
    assert res_post_inc.status_code == 302
    assert '/income' in res_post_inc.headers.get('Location', '')

    updated_inc = get_transaction_by_id(inc_id, u1_id)
    assert updated_inc["title"] == "Alice Promoted Salary"
    assert updated_inc["amount"] == 65000.0
    assert updated_inc["notes"] == "Promoted to Senior Lead"
    print("[PASS] Test 2: Authenticated user can view details and update an Income record")

    res_post_exp = client.post(f'/transactions/{exp_id}/edit', data={
        'title': 'Alice Wholesale Groceries',
        'amount': '5500.00',
        'category': 'Food & Dining',
        'type': 'expense',
        'notes': 'Bulk grocery purchase',
        'redirect_to': 'expenses'
    })
    assert res_post_exp.status_code == 302
    assert '/expenses' in res_post_exp.headers.get('Location', '')

    updated_exp = get_transaction_by_id(exp_id, u1_id)
    assert updated_exp["title"] == "Alice Wholesale Groceries"
    assert updated_exp["amount"] == 5500.0

    summary_alice = get_user_financial_summary(u1_id)
    assert summary_alice["total_income"] == 65000.0
    assert summary_alice["total_expenses"] == 5500.0
    assert summary_alice["total_balance"] == 59500.0
    print("[PASS] Test 3: Authenticated user can edit Expense record; dashboard totals dynamically recalculate")

    client.get('/auth/logout')
    client.post('/auth/login', data={'email': u2_email, 'password': u2_pass})

    res_bob_tamper_get = client.get(f'/transactions/{inc_id}/edit')
    assert res_bob_tamper_get.status_code == 404, f"Security Breach! Bob got status {res_bob_tamper_get.status_code}"

    res_bob_tamper_post = client.post(f'/transactions/{inc_id}/edit', data={
        'title': 'Bob Tampered Salary',
        'amount': '1.00',
        'type': 'income'
    })
    
    unaltered_alice_txn = get_transaction_by_id(inc_id, u1_id)
    assert unaltered_alice_txn["title"] == "Alice Promoted Salary"
    assert unaltered_alice_txn["amount"] == 65000.0
    print("[PASS] Test 4: Multi-user data isolation verified: User B strictly prevented from reading or updating User A's records")

    client.get('/auth/logout')
    client.post('/auth/login', data={'email': u1_email, 'password': u1_pass})

    res_invalid_amt = client.post(f'/transactions/{inc_id}/edit', data={
        'title': 'Negative Income Test',
        'amount': '-500'
    })
    check_txn = get_transaction_by_id(inc_id, u1_id)
    assert check_txn["amount"] == 65000.0

    res_invalid_title = client.post(f'/transactions/{inc_id}/edit', data={
        'title': 'X',
        'amount': '1000'
    })
    check_txn2 = get_transaction_by_id(inc_id, u1_id)
    assert check_txn2["title"] == "Alice Promoted Salary"
    print("[PASS] Test 5: Input validation rules strictly enforce positive amounts and valid titles on update")

    res_income_page = client.get('/income')
    assert res_income_page.status_code == 200
    income_html = res_income_page.get_data(as_text=True)
    assert 'id="edit-income-modal"' in income_html, "Edit Income modal missing from /income"
    assert 'openEditModal' in income_html, "openEditModal function missing from /income"
    assert 'Edit record' in income_html, "Edit record button missing from /income"
    print("[PASS] Test 6: /income renders Edit buttons and working modal dialog")

    res_expenses_page = client.get('/expenses')
    assert res_expenses_page.status_code == 200
    expenses_html = res_expenses_page.get_data(as_text=True)
    assert 'id="edit-expense-modal"' in expenses_html, "Edit Expense modal missing from /expenses"
    assert 'openEditExpenseModal' in expenses_html, "openEditExpenseModal function missing from /expenses"
    assert 'Edit record' in expenses_html, "Edit record button missing from /expenses"
    print("[PASS] Test 7: /expenses renders Edit buttons and working modal dialog")

    print("=========================================================================")
    print(" ALL 7 TRANSACTION EDITING & UI MODAL TESTS PASSED!                      ")
    print("=========================================================================")

if __name__ == '__main__':
    run_tests()
