from flask import Blueprint,request,jsonify
from auth import login_required,hash_password,verify_password
from database import query
bp=Blueprint('profile',__name__,url_prefix='/api/profile')
@bp.get('')
@login_required
def get_profile(user): return jsonify({k:user.get(k) for k in ['id','username','email','full_name','phone','department','skills','role','status']})
@bp.put('')
@login_required
def update(user):
    d=request.get_json() or {}; fields=[];vals=[]
    for k in ['full_name','email','phone']:
        if k in d:fields.append(k+'=%s');vals.append(d[k])
    if fields:vals.append(user['id']);query('UPDATE users SET '+','.join(fields)+' WHERE id=%s',tuple(vals),commit=True)
    if d.get('current_password') or d.get('new_password'):
        if not d.get('current_password') or not d.get('new_password') or not verify_password(user['password_hash'],d['current_password']):return jsonify({'error':'Current password is incorrect'}),400
        query('UPDATE users SET password_hash=%s WHERE id=%s',(hash_password(d['new_password']),user['id']),commit=True)
    return jsonify({'message':'Profile updated'})
