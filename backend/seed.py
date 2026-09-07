from app import app
from database import query
from auth import hash_password

def add_user(username,email,password,role,name,phone=None,department=None,skills=None):
    exists=query('SELECT id FROM users WHERE username=%s OR email=%s',(username,email),fetch=True)
    if exists:return exists[0]['id']
    return query("INSERT INTO users(username,email,password_hash,role,full_name,phone,department,skills,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'active')",(username,email,hash_password(password),role,name,phone,department,skills),commit=True)
with app.app_context():
    admin=add_user('admin','admin@example.com','Admin@123','admin','System Administrator','9999999999','IT','Administration')
    tech=add_user('technician','tech@example.com','Tech@123','technician','Demo Technician','9999999998','Support','Hardware, Network')
    cust_user=add_user('customer','customer@example.com','Customer@123','customer','Demo Customer','9999999997',None,None)
    rows=query('SELECT id FROM customers WHERE user_id=%s',(cust_user,),fetch=True)
    if not rows: query("INSERT INTO customers(user_id,company_name,contact_person,email,phone,address,status) VALUES(%s,'Demo Company','Demo Customer','customer@example.com','9999999997','Mumbai, India','active')",(cust_user,),commit=True)
    cats=query('SELECT COUNT(*) n FROM categories',fetch=True)[0]['n']
    if not cats:
        for n in ['Hardware','Software','Network','Printer','Email','Server','Security','Internet','Other']:query('INSERT INTO categories(name) VALUES(%s)',(n,),commit=True)
    print('Seed complete. admin@example.com / Admin@123, tech@example.com / Tech@123, customer@example.com / Customer@123')
