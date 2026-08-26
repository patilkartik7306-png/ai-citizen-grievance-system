# AI-Based Citizen Grievance Lodging & Tracking System — Final Updated Version

Includes the requested complete workflow:

Citizen:
- Register/login
- Select complaint category first
- Only complaint types for that category appear
- Upload complaint photo
- Add additional details
- Submit grievance
- AI predicts priority only
- Complaint/category/department saved in PostgreSQL
- Track worker/status/follow-up history
- See worker completion photo
- Receive final resolution notification

Officer:
- Department login
- View department grievances and citizen photo
- See only AVAILABLE workers from same department
- Assign worker using EMP_ID
- Worker becomes BUSY while work is assigned
- Review worker completion photo
- APPROVE & RESOLVE or REWORK REQUIRED
- Worker becomes AVAILABLE only after final approval
- Rejecting work keeps the worker BUSY for rework

Worker:
- Login using EMP_ID
- See assigned work
- START WORK -> IN PROGRESS
- Upload completion photo and remarks
- Submit for officer verification
- Rework if officer rejects

Setup:
1. CREATE DATABASE citizen_grievance;
2. \c citizen_grievance
3. Run sql/tables.sql
4. Set DB_PASSWORD in config.py
5. python -m venv venv
6. Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
7. venv\Scripts\Activate.ps1
8. pip install -r requirements.txt
9. python test_db.py
10. python seed_data.py
11. python ml\train_model.py
12. python app.py
13. Open http://127.0.0.1:5000

Demo officers:
water@example.com / officer123
waste@example.com / officer123
road@example.com / officer123
lighting@example.com / officer123
drainage@example.com / officer123

Demo workers:
EMP001 / worker123
EMP002 / worker123
EMP003 / worker123
EMP004 / worker123
EMP005 / worker123
EMP006 / worker123
EMP007 / worker123
EMP008 / worker123

Images: JPG/JPEG/PNG/WEBP, max 5 MB.
