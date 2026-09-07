from flask import Blueprint,request,jsonify
from database import query
from auth import login_required,roles
bp=Blueprint('categories',__name__,url_prefix='/api/categories')
@bp.get('')
@login_required
def list_categories(user): return jsonify(query("SELECT c.*,COUNT(t.id) ticket_count FROM categories c LEFT JOIN tickets t ON t.category_id=c.id GROUP BY c.id ORDER BY c.name",fetch=True))
@bp.post('')
@roles('admin')
def create(user):
    d=request.get_json() or {}; name=d.get('name','').strip()
    if not name:return jsonify({'error':'Name is required'}),400
    try: cid=query('INSERT INTO categories(name,description) VALUES(%s,%s)',(name,d.get('description')),commit=True); return jsonify({'id':cid}),201
    except Exception as e:return jsonify({'error':str(e)}),400
@bp.put('/<int:cid>')
@roles('admin')
def edit(user,cid):
    d=request.get_json() or {}; query('UPDATE categories SET name=%s,description=%s,status=%s WHERE id=%s',(d.get('name'),d.get('description'),d.get('status','active'),cid),commit=True); return jsonify({'message':'Updated'})
