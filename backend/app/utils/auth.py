"""
Authentication Helpers & Decorators for FinWise
"""

from functools import wraps
from urllib.parse import urlparse, urljoin
from flask import session, flash, redirect, url_for, request


def is_safe_url(target):
    """
    Ensures that a redirect target URL is internal to the application to prevent open redirects.
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def login_required(f):
    """
    Decorator protecting routes that require an authenticated user session.
    Redirects unauthenticated visitors to the login view with an informative message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this feature.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function
