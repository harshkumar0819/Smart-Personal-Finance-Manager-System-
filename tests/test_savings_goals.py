"""
FinWise — Savings Goals Automated Test Suite
Validates:
1. Guest protection: Unauthenticated requests to /goals redirect to login.
2. Goal Creation: Users can create goals with target amounts, starting funds, and deadlines.
3. Progress Calculations: Accurate percentage and remaining balance math.
4. Deposit / Update: Adding funds increases current amount and updates status to Achieved when target reached.
5. Goal Deletion: Users can delete their own goals.
6. Multi-User Isolation: User Bob cannot view, deposit to, or delete User Alice's savings goals.
"""

from bson import ObjectId
from app import create_app
from app.database import get_db
from app.models.user import create_user
from app.models.goal import create_goal, get_user_goals, deposit_to_goal, update_goal, delete_goal


def cleanup_test_data():
    db = get_db()
    db.users.delete_many({"email": {"$regex": "@goals\\.finwise\\.com$"}})
    db.goals.delete_many({"notes": {"$regex": "^TEST_GOAL_"}})


def run_goals_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    cleanup_test_data()
    db = get_db()

    print("=========================================================================")
    print(" FinWise -- Savings Goals Feature Test Suite                              ")
    print("=========================================================================")

    # -------------------------------------------------------------------------
    # Test 1: Guest Protection
    # -------------------------------------------------------------------------
    res_guest = client.get('/goals', follow_redirects=False)
    assert res_guest.status_code == 302, f"Expected 302 redirect for guest, got {res_guest.status_code}"
    assert '/auth/login' in res_guest.headers['Location']
    print("[PASS] Test 1: Guest access to /goals is blocked and redirected to login")

    # -------------------------------------------------------------------------
    # Test 2: User Creation & Goal Creation via HTTP POST
    # -------------------------------------------------------------------------
    u_alice_email = "alice@goals.finwise.com"
    u_alice_pass = "AliceSecurePass123!"
    ok_a, _, alice_user = create_user("Alice Goals", u_alice_email, u_alice_pass)
    assert ok_a, "Failed to create test user Alice"
    alice_id = alice_user["_id"]

    with client:
        # Log in as Alice
        client.post('/auth/login', data={'email': u_alice_email, 'password': u_alice_pass})

        # Create goal via form POST
        res_add = client.post('/goals/add', data={
            'title': 'Emergency Fund',
            'target_amount': '50000.00',
            'current_amount': '10000.00',
            'target_date': '2026-12-31',
            'notes': 'TEST_GOAL_EMERGENCY'
        }, follow_redirects=True)
        assert res_add.status_code == 200
        add_text = res_add.get_data(as_text=True)
        assert "Emergency Fund" in add_text
        assert "50,000.00" in add_text
        assert "10,000.00" in add_text
        print("[PASS] Test 2: User can create a savings goal via form submission")

        # -------------------------------------------------------------------------
        # Test 3: Progress Calculation & Status Display
        # -------------------------------------------------------------------------
        alice_goals = get_user_goals(alice_id)
        assert len(alice_goals) == 1
        g1 = alice_goals[0]
        # Target = 50000, current = 10000 -> 20.0%, remaining = 40000, in progress
        assert g1["target_amount"] == 50000.0
        assert g1["current_amount"] == 10000.0
        assert g1["percentage"] == 20.0
        assert g1["remaining"] == 40000.0
        assert g1["is_achieved"] is False
        assert "In Progress" in g1["status_label"]
        print("[PASS] Test 3: Goal progress (20.0%) and remaining balance (Rs. 40,000.00) calculated accurately")

        # -------------------------------------------------------------------------
        # Test 4: Deposit to Goal & Milestone Completion (Achieved)
        # -------------------------------------------------------------------------
        goal_id = g1["_id"]

        # Deposit 15,000 -> total 25,000 (50%)
        res_dep1 = client.post(f'/goals/{goal_id}/deposit', data={'amount': '15000.00'}, follow_redirects=True)
        assert res_dep1.status_code == 200
        alice_goals_after_dep1 = get_user_goals(alice_id)
        assert alice_goals_after_dep1[0]["current_amount"] == 25000.0
        assert alice_goals_after_dep1[0]["percentage"] == 50.0
        assert alice_goals_after_dep1[0]["remaining"] == 25000.0

        # Deposit 30,000 -> total 55,000 (>= 50,000 target -> Achieved!)
        res_dep2 = client.post(f'/goals/{goal_id}/deposit', data={'amount': '30000.00'}, follow_redirects=True)
        assert res_dep2.status_code == 200
        alice_goals_after_dep2 = get_user_goals(alice_id)
        g_completed = alice_goals_after_dep2[0]
        assert g_completed["current_amount"] == 55000.0
        assert g_completed["remaining"] == 0.0
        assert g_completed["is_achieved"] is True
        assert "Achieved" in g_completed["status_label"]
        # Bar percentage capped at 100 for clean UI
        assert g_completed["bar_percentage"] == 100.0

        # Also verify direct update of goal properties (title, target, notes)
        res_update = client.post(f'/goals/{goal_id}/update', data={
            'title': 'Emergency & Rainy Day Fund',
            'target_amount': '60000.00',
            'notes': 'Updated emergency target'
        }, follow_redirects=True)
        assert res_update.status_code == 200
        alice_updated_goals = get_user_goals(alice_id)
        g_updated = alice_updated_goals[0]
        assert g_updated["title"] == "Emergency & Rainy Day Fund"
        assert g_updated["target_amount"] == 60000.0
        assert g_updated["notes"] == "Updated emergency target"
        # 55000 / 60000 = 91.7%, not achieved yet
        assert g_updated["percentage"] == 91.7
        assert g_updated["is_achieved"] is False
        assert g_updated["remaining"] == 5000.0
        print("[PASS] Test 4: Goal updates verified (deposits increase balance to 'Achieved', and direct property updates recalculate targets)")

        # -------------------------------------------------------------------------
        # Test 5: Goal Deletion
        # -------------------------------------------------------------------------
        # Create a second goal to delete
        ok2, _, g2_doc = create_goal(alice_id, "Temporary Vacation", 15000.0, notes="TEST_GOAL_VACATION")
        assert ok2
        g2_id = str(g2_doc["_id"])

        res_del = client.post(f'/goals/{g2_id}/delete', follow_redirects=True)
        assert res_del.status_code == 200
        alice_remaining_goals = get_user_goals(alice_id)
        assert len(alice_remaining_goals) == 1
        assert alice_remaining_goals[0]["title"] == "Emergency & Rainy Day Fund"
        print("[PASS] Test 5: User can delete their own savings goals")

    # -------------------------------------------------------------------------
    # Test 6: Multi-User Isolation (Anti-Tampering & Cross-User Security)
    # -------------------------------------------------------------------------
    u_bob_email = "bob@goals.finwise.com"
    u_bob_pass = "BobSecurePass456!"
    ok_b, _, bob_user = create_user("Bob Goals", u_bob_email, u_bob_pass)
    assert ok_b
    bob_id = bob_user["_id"]

    # Bob creates his own goal
    ok_b_goal, _, bob_goal = create_goal(bob_id, "Bob Laptop Fund", 80000.0, notes="TEST_GOAL_BOB")
    assert ok_b_goal
    bob_goal_id = str(bob_goal["_id"])

    # 6a. Bob should only see his goal, zero of Alice's goals
    bob_goals_list = get_user_goals(bob_id)
    assert len(bob_goals_list) == 1
    assert bob_goals_list[0]["title"] == "Bob Laptop Fund"
    bob_titles = [g["title"] for g in bob_goals_list]
    assert "Emergency Fund" not in bob_titles, "SECURITY BREACH: Bob can see Alice's savings goal!"
    assert "Emergency & Rainy Day Fund" not in bob_titles, "SECURITY BREACH: Bob can see Alice's updated goal!"

    # 6b. Alice tries to deposit into Bob's goal -> must fail
    tamper_dep, msg_dep = deposit_to_goal(bob_goal_id, alice_id, 5000.0)
    assert tamper_dep is False, "SECURITY BREACH: Alice was able to deposit to Bob's goal!"
    assert "unauthorized" in msg_dep.lower() or "not found" in msg_dep.lower()

    # 6c. Alice tries to update Bob's goal -> must fail
    tamper_up, msg_up, _ = update_goal(bob_goal_id, alice_id, title="Tampered Title")
    assert tamper_up is False, "SECURITY BREACH: Alice was able to update Bob's goal!"
    assert "unauthorized" in msg_up.lower() or "not found" in msg_up.lower()

    # 6d. Alice tries to delete Bob's goal -> must fail
    tamper_del, msg_del = delete_goal(bob_goal_id, alice_id)
    assert tamper_del is False, "SECURITY BREACH: Alice was able to delete Bob's goal!"
    assert "denied" in msg_del.lower() or "not found" in msg_del.lower()

    # Verify Bob's goal is still completely intact in database
    bob_verify = db.goals.find_one({"_id": ObjectId(bob_goal_id), "user_id": bob_id})
    assert bob_verify is not None, "Bob's goal was deleted during cross-user attack!"
    assert bob_verify["current_amount"] == 0.0, "Bob's balance was modified by unauthorized deposit!"
    print("[PASS] Test 6: Multi-user isolation verified: cross-user reading, deposits, and deletion strictly blocked")

    cleanup_test_data()
    print("=========================================================================")
    print(" ALL 6 SAVINGS GOALS TESTS PASSED!                                      ")
    print("=========================================================================")


if __name__ == '__main__':
    run_goals_tests()
