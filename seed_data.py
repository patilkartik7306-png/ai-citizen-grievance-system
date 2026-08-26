from werkzeug.security import generate_password_hash
from database import get_connection

def seed():
    c = get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT department_id,department_name FROM departments")
            d = {r[1]: r[0] for r in cur.fetchall()}
            officers = [
                ("Admin Officer","officer1@example.com","officer123","General Administration"),
                ("Waste Officer","waste@example.com","officer123","Waste Management"),
                ("Road Officer","road@example.com","officer123","Public Works"),
                ("Water Officer","water@example.com","officer123","Water Supply"),
                ("Lighting Officer","lighting@example.com","officer123","Street Lighting"),
                ("Drainage Officer","drainage@example.com","officer123","Drainage and Sewerage")]
            for name,email,pw,dept in officers:
                cur.execute("INSERT INTO officers(name,email,password_hash,department_id) VALUES(%s,%s,%s,%s) ON CONFLICT(email) DO NOTHING",(name,email,generate_password_hash(pw),d[dept]))
            workers = [
                ("EMP001","Rahul Patil","9876500001","rahul.worker@example.com","worker123","Waste Management"),
                ("EMP002","Amit Jadhav","9876500002","amit.worker@example.com","worker123","Waste Management"),
                ("EMP003","Suresh More","9876500003","suresh.worker@example.com","worker123","Public Works"),
                ("EMP004","Vijay Shinde","9876500004","vijay.worker@example.com","worker123","Public Works"),
                ("EMP005","Nikhil Patil","9876500005","nikhil.worker@example.com","worker123","Water Supply"),
                ("EMP006","Prasad Jagtap","9876500006","prasad.worker@example.com","worker123","Water Supply"),
                ("EMP007","Akash More","9876500007","akash.worker@example.com","worker123","Street Lighting"),
                ("EMP008","Rohit Kale","9876500008","rohit.worker@example.com","worker123","Drainage and Sewerage")]
            for emp,name,mobile,email,pw,dept in workers:
                cur.execute("INSERT INTO workers(emp_id,name,mobile,email,password_hash,department_id) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(emp_id) DO NOTHING",(emp,name,mobile,email,generate_password_hash(pw),d[dept]))
        c.commit(); print('Officers and workers seeded successfully.')
    finally: c.close()
if __name__ == '__main__': seed()
