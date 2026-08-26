\connect citizen_grievance;

DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS grievance_photos CASCADE;
DROP TABLE IF EXISTS grievance_assignments CASCADE;
DROP TABLE IF EXISTS grievance_followups CASCADE;
DROP TABLE IF EXISTS grievances CASCADE;
DROP TABLE IF EXISTS workers CASCADE;
DROP TABLE IF EXISTS officers CASCADE;
DROP TABLE IF EXISTS citizens CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

CREATE TABLE departments (department_id SERIAL PRIMARY KEY, department_name VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE citizens (citizen_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, mobile VARCHAR(20) NOT NULL, email VARCHAR(150) UNIQUE NOT NULL, address TEXT, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE officers (officer_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) UNIQUE NOT NULL, password_hash TEXT NOT NULL, department_id INT REFERENCES departments(department_id), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE workers (worker_id SERIAL PRIMARY KEY, emp_id VARCHAR(30) UNIQUE NOT NULL, name VARCHAR(100) NOT NULL, mobile VARCHAR(20), email VARCHAR(150), password_hash TEXT NOT NULL, department_id INT REFERENCES departments(department_id), availability_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE' CHECK (availability_status IN ('AVAILABLE','BUSY')), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE grievances (grievance_id SERIAL PRIMARY KEY, grievance_code VARCHAR(30) UNIQUE NOT NULL, citizen_id INT NOT NULL REFERENCES citizens(citizen_id), category VARCHAR(100) NOT NULL, complaint_type VARCHAR(150) NOT NULL, complaint_details TEXT, priority VARCHAR(30) NOT NULL, department_id INT REFERENCES departments(department_id), status VARCHAR(40) NOT NULL DEFAULT 'Submitted', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE grievance_assignments (assignment_id SERIAL PRIMARY KEY, grievance_id INT NOT NULL REFERENCES grievances(grievance_id) ON DELETE CASCADE, worker_id INT NOT NULL REFERENCES workers(worker_id), officer_id INT NOT NULL REFERENCES officers(officer_id), assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, started_at TIMESTAMP, completed_at TIMESTAMP, status VARCHAR(40) NOT NULL DEFAULT 'ASSIGNED');
CREATE TABLE grievance_photos (photo_id SERIAL PRIMARY KEY, grievance_id INT NOT NULL REFERENCES grievances(grievance_id) ON DELETE CASCADE, citizen_id INT REFERENCES citizens(citizen_id), worker_id INT REFERENCES workers(worker_id), photo_type VARCHAR(30) NOT NULL, photo_path TEXT NOT NULL, verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING', officer_remarks TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, verified_at TIMESTAMP);
CREATE TABLE grievance_followups (followup_id SERIAL PRIMARY KEY, grievance_id INT NOT NULL REFERENCES grievances(grievance_id) ON DELETE CASCADE, officer_id INT REFERENCES officers(officer_id), worker_id INT REFERENCES workers(worker_id), status VARCHAR(40) NOT NULL, remarks TEXT, followup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE notifications (notification_id SERIAL PRIMARY KEY, citizen_id INT NOT NULL REFERENCES citizens(citizen_id) ON DELETE CASCADE, grievance_id INT NOT NULL REFERENCES grievances(grievance_id) ON DELETE CASCADE, message TEXT NOT NULL, is_read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
INSERT INTO departments (department_name) VALUES ('Waste Management'),('Public Works'),('Water Supply'),('Street Lighting'),('Drainage and Sewerage'),('General Administration');
