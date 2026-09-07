from flask import Blueprint,jsonify
from auth import login_required
from database import query
bp=Blueprint('notifications',__name__,url_prefix='/api/notifications')
@bp.get('')
@login_required
def all_notifications(user): return jsonify(query('SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 100',(user['id'],),fetch=True))
@bp.get('/unread-count')
@login_required
def unread(user): return jsonify({'count':query('SELECT COUNT(*) n FROM notifications WHERE user_id=%s AND is_read=0',(user['id'],),fetch=True)[0]['n']})
@bp.patch('/<int:nid>/read')
@login_required
def read(user,nid): query('UPDATE notifications SET is_read=1 WHERE id=%s AND user_id=%s',(nid,user['id']),commit=True); return jsonify({'message':'Marked read'})
@bp.post('/read-all')
@login_required
def read_all(user): query('UPDATE notifications SET is_read=1 WHERE user_id=%s',(user['id'],),commit=True); return jsonify({'message':'All marked read'})
