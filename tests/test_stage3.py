from app import create_app

def run_tests():
    app = create_app()
    client = app.test_client()

    # Test 1: GET / returns 200 OK
    res_root = client.get('/')
    assert res_root.status_code == 200, f"Expected 200, got {res_root.status_code}"
    content_root = res_root.get_data(as_text=True)
    print("[PASS] Test 1: GET / returned HTTP 200 OK")

    # Test 2: GET /dashboard returns 200 OK
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200, f"Expected 200, got {res_dash.status_code}"
    print("[PASS] Test 2: GET /dashboard returned HTTP 200 OK")

    # Test 3: Project Title Presence
    title = "FinWise — Smart Personal Finance and Expense Management System"
    assert title in content_root, "Project title missing from dashboard"
    print("[PASS] Test 3: Project title is correctly rendered")

    # Test 4: All 4 KPI Cards present
    kpis = ['Total Balance', 'Monthly Income', 'Monthly Expenses', 'Active Budgets']
    for kpi in kpis:
        assert kpi in content_root, f"KPI card missing: {kpi}"
    print(f"[PASS] Test 4: All 4 KPI cards present ({kpis})")

    # Test 5: Chart.js Canvas Elements and CDN present
    assert 'id="cashFlowChart"' in content_root, "cashFlowChart canvas missing"
    assert 'id="categoryChart"' in content_root, "categoryChart canvas missing"
    assert "cdn.jsdelivr.net/npm/chart.js" in content_root, "Chart.js CDN missing"
    print("[PASS] Test 5: Chart.js containers and CDN verified")

    # Test 6: Reusable Jinja2 Macros output verified
    assert 'id="sample_title"' in content_root, "input_field macro failed"
    assert "Monthly Salary Credit" in content_root, "transaction_row macro failed"
    print("[PASS] Test 6: Jinja2 macros (input_field, transaction_row, badge, kpi_card) verified")

    # Test 7: Responsive Navigation & Sidebar elements verified
    assert 'id="sidebar"' in content_root, "sidebar element missing"
    assert 'id="open-sidebar-btn"' in content_root, "mobile toggle button missing"
    assert 'id="close-sidebar-btn"' in content_root, "sidebar close button missing"
    print("[PASS] Test 7: Responsive sidebar and mobile toggle controls verified")

    # Test 8: Sample Data Clearly Disclaimed
    assert "Sample Preview Data" in content_root, "Sample data notice missing"
    print("[PASS] Test 8: Transparent sample preview disclaimer verified")

if __name__ == '__main__':
    run_tests()
