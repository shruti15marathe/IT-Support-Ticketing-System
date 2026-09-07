# Installation

1. Install MySQL 8+ and Python 3.11+ (or a supported Python version for the pinned dependencies).
2. Create/import the schema:
   `mysql -u root -p < database/schema.sql`
3. Enter `backend`.
4. Copy `.env.example` to `.env` and set the MySQL password and secrets.
5. Create a virtual environment and install dependencies:
   `python -m venv venv`
   Windows: `venv\\Scripts\\activate`
   Linux/macOS: `source venv/bin/activate`
   `pip install -r requirements.txt`
6. Run sample data: `python seed.py`
7. Start: `python app.py`
8. Open `http://127.0.0.1:5000`

Demo accounts:
- Admin: admin@example.com / Admin@123
- Technician: tech@example.com / Tech@123
- Customer: customer@example.com / Customer@123

For production, set secure random secrets, `secure=True` on the JWT cookie behind HTTPS, and deploy with Gunicorn + Nginx as described by the SRS.
