from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, current_app
from database import query

def hash_password(p): return generate_password_hash(p)
def verify_password(h,p): return check_password_hash(h,p)

def create_token(user):
    now=datetime.now(timezone.utc)
    return jwt.encode({'sub':user['id'],'role':user['role'],'exp':now+timedelta(hours=12),'iat':now}, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def current_user():
    token=request.cookies.get('access_token') or request.headers.get('Authorization','').replace('Bearer ','',1)
    if not token: return None
    try:
        data=jwt.decode(token,current_app.config['JWT_SECRET_KEY'],algorithms=['HS256'])
        rows=query("SELECT * FROM users WHERE id=%s AND status='active'",(data['sub'],),fetch=True)
        return rows[0] if rows else None
    except jwt.PyJWTError: return None

def login_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        user=current_user()
        if not user: return jsonify({'error':'Authentication required'}),401
        return fn(*a, user=user, **kw)
    return wrapper

def roles(*allowed):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            user=current_user()
            if not user: return jsonify({'error':'Authentication required'}),401
            if user['role'] not in allowed: return jsonify({'error':'Forbidden'}),403
            return fn(*a,user=user,**kw)
        return wrapper
    return deco
