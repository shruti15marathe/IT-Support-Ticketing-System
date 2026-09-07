from flask import Blueprint,request,jsonify
from database import query
from auth import roles,hash_password
bp=Blueprint('users',__name__,url_prefix='/api/users')
@bp.get('')
@roles('admin')
def list_users(user): return jsonify(query("SELECT id,username,email,role,full_name,phone,department,skills,status,joining_date,created_at FROM users ORDER BY id DESC",fetch=True))
@bp.post('')
@roles('admin')
def create_user(user):
    d=request.get_json() or {}; req=['username','email','password','role','full_name']
    if any(not d.get(x) for x in req): return jsonify({'error':'Required fields missing'}),400
    try:
        uid=query("INSERT INTO users(username,email,password_hash,role,full_name,phone,department,skills,status,joining_date) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(d['username'],d['email'],hash_password(d['password']),d['role'],d['full_name'],d.get('phone'),d.get('department'),d.get('skills'),'active',d.get('joining_date')),commit=True)
        return jsonify({'id':uid}),201
    except Exception as e: return jsonify({'error':str(e)}),400
@bp.put('/<int:uid>')
@roles('admin')
def update_user(user,uid):
    d=request.get_json() or {}; fields=[]; vals=[]
    for key in ['full_name','email','phone','department','skills','status','joining_date']:
        if key in d: fields.append(f'{key}=%s'); vals.append(d[key])
    if d.get('password'): fields.append('password_hash=%s'); vals.append(hash_password(d['password']))
    if not fields: return jsonify({'error':'Nothing to update'}),400
    vals.append(uid); query('UPDATE users SET '+','.join(fields)+' WHERE id=%s',tuple(vals),commit=True); return jsonify({'message':'Updated'})
