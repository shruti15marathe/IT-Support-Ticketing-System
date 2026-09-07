from pathlib import Path
from uuid import uuid4
from flask import current_app
from werkzeug.utils import secure_filename
from database import query

def allowed_file(name):
    return '.' in name and name.rsplit('.',1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_upload(file):
    if not file or not file.filename: return None
    if not allowed_file(file.filename): raise ValueError('Unsupported file type')
    folder=Path(current_app.config['UPLOAD_FOLDER']); folder.mkdir(parents=True,exist_ok=True)
    ext=file.filename.rsplit('.',1)[1].lower(); stored=f'{uuid4().hex}.{ext}'
    path=folder/stored; file.save(path)
    return {'original_name':secure_filename(file.filename),'stored_name':stored,'file_path':str(path),'mime_type':file.mimetype,'file_size':path.stat().st_size}

def add_history(ticket_id,user_id,action,old_value=None,new_value=None,details=None):
    query("INSERT INTO ticket_history(ticket_id,user_id,action,old_value,new_value,details) VALUES(%s,%s,%s,%s,%s,%s)",(ticket_id,user_id,action,old_value,new_value,details),commit=True)

def notify(user_id,ticket_id,title,message):
    query("INSERT INTO notifications(user_id,ticket_id,title,message) VALUES(%s,%s,%s,%s)",(user_id,ticket_id,title,message),commit=True)

def notify_role(role,ticket_id,title,message,exclude_id=None):
    sql="SELECT id FROM users WHERE role=%s AND status='active'"; rows=query(sql,(role,),fetch=True)
    for r in rows:
        if exclude_id and r['id']==exclude_id: continue
        notify(r['id'],ticket_id,title,message)
