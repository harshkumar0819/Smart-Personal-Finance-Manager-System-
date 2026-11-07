"""
Authentication Routes for FinWise
Handles registration, login, logout, and session lifecycle.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import (
    validate_registration_input,
    create_user,
    authenticate_user
)
from app.utils.auth import is_safe_url

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration View.
    GET: Displays registration form.
    POST: Validates inputs, creates user with hashed password, redirects to login.
    """
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate form inputs
        is_valid, error_message = validate_registration_input(name, email, password, confirm_password)
        if not is_valid:
            flash(error_message, "danger")
            return render_template('auth/register.html', name=name, email=email)

        # Create user in MongoDB
        success, message, new_user = create_user(name, email, password)
        if not success:
            flash(message, "danger")
            return render_template('auth/register.html', name=name, email=email)

        flash("Registration successful! You can now log in to your account.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login View.
    GET: Displays login form.
    POST: Authenticates credentials, initializes user session, redirects to dashboard or next url.
    """
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    next_url = request.args.get('next', '')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('auth/login.html', email=email, next=next_url)

        is_auth, message, user = authenticate_user(email, password)
        if not is_auth:
            flash(message, "danger")
            return render_template('auth/login.html', email=email, next=next_url)

        # Prevent session fixation by resetting the session
        session.clear()
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        flash(f"Welcome back, {user['name']}!", "success")

        # Validate redirect target against open redirect attacks
        if next_url and is_safe_url(next_url):
            return redirect(next_url)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', next=next_url)


@auth_bp.route('/logout')
def logout():
    """
    Clears the active session and logs out the user.
    """
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('auth.login'))
