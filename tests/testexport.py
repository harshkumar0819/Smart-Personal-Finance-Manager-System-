

import csv
import io
from app import create_app
from app.database import get_db
from app.models.user import create_user
from app.models.transaction import create_transaction


def cleanup_test_data():
    db = get_db()
    db.users.delete_many({"email": {"$regex": "@csvexport\\.finwise\\.com$"}})
    db.transactions.delete_many({"notes": {"$regex": "^TEST_CSV_"}})


def run_csv_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    cleanup_test_data()

    print("=========================================================================")
    print(" FinWise -- Transaction CSV Export Feature Test Suite                     ")
    print("=========================================================================")

    res_guest = client.get('/transactions/export/csv', follow_redirects=False)
    assert res_guest.status_code == 302, f"Expected 302 redirect for guest, got {res_guest.status_code}"
    assert '/auth/login' in res_guest.headers['Location']
    print("[PASS] Test 1: Guest access to /transactions/export/csv is blocked and redirected to login")

    u_alice_email = "alice@csvexport.finwise.com"
    u_alice_pass = "AliceSecurePass123!"
    ok_a, _, alice_user = create_user("Alice Export", u_alice_email, u_alice_pass)
    assert ok_a, "Failed to create test user Alice"
    alice_id = alice_user["_id"]

    create_transaction(alice_id, "Monthly Salary Credit", 75000.0, "income", "Salary", "2026-10-01", "TEST_CSV_ALICE_SALARY")
    create_transaction(alice_id, "Freelance Web Project", 25000.0, "income", "Side Income", "2026-10-15", "TEST_CSV_ALICE_FREELANCE")
    create_transaction(alice_id, "Supermarket Groceries", 4500.0, "expense", "Food & Dining", "2026-10-20", "TEST_CSV_ALICE_GROCERY")

    with client:
        client.post('/auth/login', data={'email': u_alice_email, 'password': u_alice_pass})

        res_all = client.get('/transactions/export/csv')
        assert res_all.status_code == 200
        assert "text/csv" in res_all.headers.get("Content-Type", "")
        assert "attachment; filename=" in res_all.headers.get("Content-Disposition", "")
        
        csv_text = res_all.get_data(as_text=True)
        reader = list(csv.reader(io.StringIO(csv_text)))
        
        header = reader[0]
        assert header == ["Transaction ID", "Date", "Type", "Title", "Category", "Amount (INR)", "Notes"]
        
        assert len(reader) == 4
        titles = [row[3] for row in reader[1:]]
        assert "Monthly Salary Credit" in titles
        assert "Freelance Web Project" in titles
        assert "Supermarket Groceries" in titles
        print("[PASS] Test 2: Authenticated user can export complete transactions as RFC 4180 CSV")

        res_inc = client.get('/transactions/export/csv?type=income')
        assert res_inc.status_code == 200
        reader_inc = list(csv.reader(io.StringIO(res_inc.get_data(as_text=True))))
        assert len(reader_inc) == 3  
        for row in reader_inc[1:]:
            assert row[2] == "Income"
        assert "Supermarket Groceries" not in [r[3] for r in reader_inc]

        res_exp = client.get('/transactions/export/csv?type=expense')
        assert res_exp.status_code == 200
        reader_exp = list(csv.reader(io.StringIO(res_exp.get_data(as_text=True))))
        assert len(reader_exp) == 2  
        assert reader_exp[1][2] == "Expense"
        assert reader_exp[1][3] == "Supermarket Groceries"
        print("[PASS] Test 3: Filtered exports by type (?type=income, ?type=expense) work accurately")

        res_cat = client.get('/transactions/export/csv?category=Salary')
        assert res_cat.status_code == 200
        reader_cat = list(csv.reader(io.StringIO(res_cat.get_data(as_text=True))))
        assert len(reader_cat) == 2  
        assert reader_cat[1][4] == "Salary"
        assert reader_cat[1][3] == "Monthly Salary Credit"
        print("[PASS] Test 4: Category-filtered export (?category=Salary) outputs exact matching records")

    u_bob_email = "bob@csvexport.finwise.com"
    u_bob_pass = "BobSecurePass456!"
    ok_b, _, bob_user = create_user("Bob Export", u_bob_email, u_bob_pass)
    assert ok_b
    bob_id = bob_user["_id"]

    create_transaction(bob_id, "Bob Gaming Laptop EMI", 8500.0, "expense", "Shopping", "2026-10-22", "TEST_CSV_BOB_LAPTOP")

    client_bob = app.test_client()
    with client_bob:
        client_bob.post('/auth/login', data={'email': u_bob_email, 'password': u_bob_pass})
        res_bob = client_bob.get('/transactions/export/csv')
        assert res_bob.status_code == 200
        reader_bob = list(csv.reader(io.StringIO(res_bob.get_data(as_text=True))))
        
        assert len(reader_bob) == 2
        assert reader_bob[1][3] == "Bob Gaming Laptop EMI"
        bob_csv_content = res_bob.get_data(as_text=True)
        assert "Monthly Salary Credit" not in bob_csv_content, "SECURITY LEAK: Bob export contains Alice's salary!"
        assert "Freelance Web Project" not in bob_csv_content, "SECURITY LEAK: Bob export contains Alice's freelance!"
        assert "Supermarket Groceries" not in bob_csv_content, "SECURITY LEAK: Bob export contains Alice's grocery!"
        print("[PASS] Test 5: Multi-user isolation verified: zero cross-user transaction leakage in CSV exports")

    cleanup_test_data()
    print("=========================================================================")
    print(" ALL 5 CSV EXPORT TESTS PASSED!                                         ")
    print("=========================================================================")


if __name__ == '__main__':
    run_csv_tests()
