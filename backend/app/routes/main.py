from flask import Blueprint, render_template, jsonify, session
from app.database import check_db_connection
from app.models.transaction import get_user_financial_summary
from app.models.budget import get_user_budgets_with_spending
from app.models.goal import get_user_goals
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
def index():
    user_id = session.get('user_id')
    if user_id:
        summary = get_user_financial_summary(user_id)
        user_budgets = get_user_budgets_with_spending(user_id)
        user_goals = get_user_goals(user_id)
        total_savings = sum(g.get("current_amount", 0.0) for g in user_goals)
        budget_alerts = [b for b in user_budgets if b.get('is_overrun') or b.get('is_warning')]
        return render_template(
            'dashboard/index.html',
            is_guest=False,
            summary=summary,
            budgets=user_budgets,
            goals=user_goals,
            total_savings=total_savings,
            budget_alerts=budget_alerts
        )
    return render_template(
        'dashboard/index.html',
        is_guest=True,
        summary=None,
        budgets=None,
        goals=None,
        total_savings=0.0,
        budget_alerts=[]
    )


@main_bp.route('/health/db')
def db_health():
    connected, message, details = check_db_connection()
    status_code = 200 if connected else 503
    return jsonify(details), status_code
