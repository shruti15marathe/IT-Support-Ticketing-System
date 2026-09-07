from flask import Blueprint,request,jsonify,make_response,redirect
from database import query
from auth import hash_password,verify_password,create_token
bp=Blueprint('auth',__name__,url_prefix='/api/auth')
@bp.post('/login')
def login():
    data=request.get_json(silent=True) or request.form
    identity=(data.get('identity') or data.get('email') or data.get('username') or '').strip(); password=data.get('password','')
    rows=query("SELECT * FROM users WHERE (email=%s OR username=%s) AND status='active'",(identity,identity),fetch=True)
    if not rows or not verify_password(rows[0]['password_hash'],password): return jsonify({'error':'Invalid credentials'}),401
    token=create_token(rows[0]); resp=jsonify({'message':'Login successful','token':token,'user':{k:rows[0][k] for k in ('id','username','email','role','full_name')}})
    resp.set_cookie('access_token',token,httponly=True,samesite='Lax',secure=False,max_age=43200)
    return resp
@bp.post('/logout')
def logout():
    resp=jsonify({'message':'Logged out'}); resp.delete_cookie('access_token'); return resp
@bp.get('/me')
def me():
    from auth import current_user
    u=current_user()
    return jsonify({'user':({k:u[k] for k in ('id','username','email','role','full_name','phone','department','skills')} if u else None)})
