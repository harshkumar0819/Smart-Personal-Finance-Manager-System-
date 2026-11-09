from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from app.utils.auth import login_required
from app.models.transaction import (
    create_transaction,
    get_user_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction,
    get_user_financial_summary,
    generate_transactions_csv,
    DEFAULT_CATEGORIES
)
from app.models.budget import (
    set_user_budget,
    get_user_budgets_with_spending,
    delete_user_budget
)
from app.models.goal import (
    create_goal,
    get_user_goals,
    deposit_to_goal,
    update_goal,
    delete_goal
)

finance_bp = Blueprint('finance', __name__)
@finance_bp.route('/income')
@login_required
def income():
    user_id = session.get('user_id')
    income_records = get_user_transactions(user_id, type_='income')
    summary = get_user_financial_summary(user_id)

    income_categories = ["Salary", "Side Income", "Investment", "Freelance", "Bonus", "Rental", "Other"]

    return render_template(
        'finance/income.html',
        transactions=income_records,
        summary=summary,
        categories=income_categories
    )
@finance_bp.route('/expenses')
@login_required
def expenses():
    user_id = session.get('user_id')
    selected_category = request.args.get('category', '').strip()
    expense_records = get_user_transactions(user_id, type_='expense', category=selected_category if selected_category else None)
    summary = get_user_financial_summary(user_id)

    expense_categories = [
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

    return render_template(
        'finance/expenses.html',
        transactions=expense_records,
        summary=summary,
        categories=expense_categories,
        selected_category=selected_category
    )
@finance_bp.route('/budgets')
@login_required
def budgets():
    user_id = session.get('user_id')
    user_budgets = get_user_budgets_with_spending(user_id)
    summary = get_user_financial_summary(user_id)

    budget_categories = [
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

    return render_template(
        'finance/budgets.html',
        budgets=user_budgets,
        summary=summary,
        categories=budget_categories
    )
@finance_bp.route('/analytics')
@login_required
def analytics():
    user_id = session.get('user_id')
    summary = get_user_financial_summary(user_id)
    user_budgets = get_user_budgets_with_spending(user_id)

    return render_template(
        'finance/analytics.html',
        summary=summary,
        budgets=user_budgets
    )
@finance_bp.route('/transactions/add', methods=['POST'])
@login_required
def add_transaction():
    user_id = session.get('user_id')
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
    type_ = request.form.get('type', 'expense').strip().lower()
    category = request.form.get('category', 'Other').strip()
    date_str = request.form.get('date', '').strip()
    notes = request.form.get('notes', '').strip()

    success, message, doc = create_transaction(
        user_id=user_id,
        title=title,
        amount=amount,
        type_=type_,
        category=category,
        date_input=date_str,
        notes=notes
    )

    if success:
        flash(f"{type_.capitalize()} '{title}' of ₹{float(amount):,.2f} recorded successfully.", "success")
    else:
        flash(message, "danger")

    redirect_target = request.form.get('redirect_to')
    if redirect_target in ('income', 'expenses', 'budgets', 'analytics'):
        return redirect(url_for(f'finance.{redirect_target}'))
    return redirect(url_for('main.index'))


@finance_bp.route('/transactions/<txn_id>/delete', methods=['POST'])
@login_required
def delete_txn(txn_id):
    user_id = session.get('user_id')
    success, message = delete_transaction(txn_id, user_id)
    if success:
        flash("Transaction deleted successfully.", "success")
    else:
        flash(message, "danger")

    redirect_target = request.form.get('redirect_to')
    if redirect_target in ('income', 'expenses', 'budgets', 'analytics'):
        return redirect(url_for(f'finance.{redirect_target}'))
    return redirect(url_for('main.index'))


@finance_bp.route('/transactions/<txn_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(txn_id):
    user_id = session.get('user_id')

    if request.method == 'GET':
        txn = get_transaction_by_id(txn_id, user_id)
        if not txn:
            return {"success": False, "message": "Transaction not found or access denied."}, 404
        return {
            "success": True,
            "transaction": {
                "id": str(txn["_id"]),
                "title": txn.get("title", ""),
                "amount": txn.get("amount", 0.0),
                "type": txn.get("type", "expense"),
                "category": txn.get("category", "Other"),
                "date": txn.get("date").strftime('%Y-%m-%d') if txn.get("date") else "",
                "notes": txn.get("notes", "")
            }
        }

    title = request.form.get('title')
    amount = request.form.get('amount')
    type_ = request.form.get('type')
    category = request.form.get('category')
    date_str = request.form.get('date')
    notes = request.form.get('notes')

    success, message = update_transaction(
        txn_id=txn_id,
        user_id=user_id,
        title=title,
        amount=amount,
        type_=type_,
        category=category,
        date_input=date_str,
        notes=notes
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    redirect_target = request.form.get('redirect_to')
    if redirect_target in ('income', 'expenses', 'budgets', 'analytics'):
        return redirect(url_for(f'finance.{redirect_target}'))
    return redirect(url_for('main.index'))
@finance_bp.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    user_id = session.get('user_id')
    category = request.form.get('category', '').strip()
    monthly_limit = request.form.get('monthly_limit', '').strip()

    success, message = set_user_budget(user_id, category, monthly_limit)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.budgets'))


@finance_bp.route('/budgets/<budget_id>/delete', methods=['POST'])
@login_required
def delete_budget(budget_id):
    user_id = session.get('user_id')
    success, message = delete_user_budget(budget_id, user_id)
    if success:
        flash("Budget target deleted successfully.", "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.budgets'))
@finance_bp.route('/goals')
@login_required
def goals():
    user_id = session.get('user_id')
    user_goals = get_user_goals(user_id)
    summary = get_user_financial_summary(user_id)

    total_target = sum(g["target_amount"] for g in user_goals)
    total_saved = sum(g["current_amount"] for g in user_goals)
    achieved_count = sum(1 for g in user_goals if g["is_achieved"])

    return render_template(
        'finance/goals.html',
        goals=user_goals,
        summary=summary,
        total_target=total_target,
        total_saved=total_saved,
        achieved_count=achieved_count
    )


@finance_bp.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    user_id = session.get('user_id')
    title = request.form.get('title', '').strip()
    target_amount = request.form.get('target_amount', '').strip()
    current_amount = request.form.get('current_amount', '0').strip()
    target_date = request.form.get('target_date', '').strip()
    notes = request.form.get('notes', '').strip()

    success, message, _ = create_goal(
        user_id=user_id,
        title=title,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        notes=notes
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.goals'))


@finance_bp.route('/goals/<goal_id>/deposit', methods=['POST'])
@login_required
def deposit_goal(goal_id):
    user_id = session.get('user_id')
    amount = request.form.get('amount', '').strip()

    success, message = deposit_to_goal(goal_id, user_id, amount)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.goals'))


@finance_bp.route('/goals/<goal_id>/update', methods=['POST'])
@login_required
def update_goal_action(goal_id):
    user_id = session.get('user_id')
    title = request.form.get('title')
    target_amount = request.form.get('target_amount')
    current_amount = request.form.get('current_amount')
    target_date = request.form.get('target_date')
    notes = request.form.get('notes')

    success, message, _ = update_goal(
        goal_id=goal_id,
        user_id=user_id,
        title=title,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        notes=notes
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.goals'))


@finance_bp.route('/goals/<goal_id>/delete', methods=['POST'])
@login_required
def delete_goal_action(goal_id):
    user_id = session.get('user_id')
    success, message = delete_goal(goal_id, user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('finance.goals'))
@finance_bp.route('/transactions/export/csv')
@login_required
def export_transactions_csv():
    from datetime import datetime, timezone

    user_id = session.get('user_id')
    txn_type = request.args.get('type', '').strip().lower()
    if txn_type not in ('income', 'expense'):
        txn_type = None

    category = request.args.get('category', '').strip()
    if not category:
        category = None

    csv_data = generate_transactions_csv(user_id, type_=txn_type, category=category)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if txn_type and category:
        filename = f"finwise_{txn_type}_{category.lower().replace(' ', '_')}_{timestamp}.csv"
    elif txn_type:
        filename = f"finwise_{txn_type}_{timestamp}.csv"
    elif category:
        filename = f"finwise_{category.lower().replace(' ', '_')}_{timestamp}.csv"
    else:
        filename = f"finwise_all_transactions_{timestamp}.csv"

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )
