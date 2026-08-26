import os
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from psycopg2.extras import RealDictCursor

from database import (
    get_connection,
    fetch_one,
    fetch_all
)

from ml.predict import (
    predict_priority,
    get_department
)


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "change-this-secret-key"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# =========================================================
# FILE UPLOAD CONFIGURATION
# =========================================================

ROOT = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


def save_image(file_object, folder):
    """
    Save an uploaded image and return its relative path.
    """

    name = secure_filename(
        file_object.filename or ""
    )

    if not name:
        raise ValueError(
            "Please select an image."
        )

    if (
        "." not in name
        or
        name.rsplit(".", 1)[1].lower()
        not in ALLOWED_EXTENSIONS
    ):
        raise ValueError(
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        )

    target_folder = os.path.join(
        ROOT,
        folder
    )

    os.makedirs(
        target_folder,
        exist_ok=True
    )

    extension = name.rsplit(
        ".",
        1
    )[1].lower()

    new_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    full_path = os.path.join(
        target_folder,
        new_filename
    )

    file_object.save(
        full_path
    )

    return (
        f"{folder}/{new_filename}"
    )


# =========================================================
# COMPLAINT OPTIONS
# =========================================================

OPTIONS = {

    "Waste Management": [
        "Garbage not collected",
        "Garbage bin overflowing",
        "Waste dumped on roadside",
        "Waste collection vehicle not visiting",
        "Door-to-door collection problem",
        "Other waste collection problem"
    ],

    "Road": [
        "Large pothole",
        "Damaged road",
        "Broken road surface",
        "Multiple potholes",
        "Road repair required",
        "Other road problem"
    ],

    "Water Supply": [
        "No water supply",
        "Water supply interrupted",
        "Pipeline leakage",
        "Low water pressure",
        "Irregular water supply",
        "Other water supply problem"
    ],

    "Street Lighting": [
        "Street light not working",
        "Broken light pole",
        "Several street lights not working",
        "Street light flickering",
        "Dark street area",
        "Other street lighting problem"
    ],

    "Drainage and Sewerage": [
        "Drain blocked",
        "Sewage overflowing",
        "Drainage line blocked",
        "Dirty water from drain",
        "Sewer overflowing",
        "Drain cleaning required"
    ],

    "Other Municipal Issue": [
        "Public cleanliness problem",
        "Public facility problem",
        "Other municipal complaint"
    ]
}


# =========================================================
# AUTHENTICATION DECORATORS
# =========================================================

def citizen_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "citizen_id" not in session:
            return redirect(
                url_for("citizen_login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def officer_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "officer_id" not in session:
            return redirect(
                url_for("officer_login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def worker_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "worker_id" not in session:
            return redirect(
                url_for("worker_login")
            )

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# UPLOADED IMAGES
# =========================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploads(filename):

    return send_from_directory(
        ROOT,
        filename
    )


# =========================================================
# CITIZEN REGISTRATION
# =========================================================

@app.route(
    "/citizen/register",
    methods=["GET", "POST"]
)
def citizen_register():

    if request.method == "POST":

        name = request.form[
            "name"
        ].strip()

        mobile = request.form[
            "mobile"
        ].strip()

        email = request.form[
            "email"
        ].strip().lower()

        address = request.form[
            "address"
        ].strip()

        password = request.form[
            "password"
        ]


        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for("citizen_register")
            )


        connection = get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO citizens
                    (
                        name,
                        mobile,
                        email,
                        address,
                        password_hash
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        name,
                        mobile,
                        email,
                        address,
                        generate_password_hash(
                            password
                        )
                    )
                )

            connection.commit()

        except Exception:

            connection.rollback()

            flash(
                "Email may already be registered.",
                "error"
            )

            connection.close()

            return redirect(
                url_for(
                    "citizen_register"
                )
            )

        finally:

            try:
                connection.close()
            except Exception:
                pass


        flash(
            "Registration successful.",
            "success"
        )

        return redirect(
            url_for("citizen_login")
        )


    return render_template(
        "citizen/register.html"
    )


# =========================================================
# CITIZEN LOGIN
# =========================================================

@app.route(
    "/citizen/login",
    methods=["GET", "POST"]
)
def citizen_login():

    if request.method == "POST":

        email = request.form[
            "email"
        ].strip().lower()

        password = request.form[
            "password"
        ]


        citizen = fetch_one(
            """
            SELECT *
            FROM citizens
            WHERE email = %s
            """,
            (
                email,
            )
        )


        if (
            citizen
            and
            check_password_hash(
                citizen["password_hash"],
                password
            )
        ):

            session.clear()

            session["citizen_id"] = (
                citizen["citizen_id"]
            )

            session["citizen_name"] = (
                citizen["name"]
            )

            return redirect(
                url_for(
                    "citizen_dashboard"
                )
            )


        flash(
            "Invalid email or password.",
            "error"
        )


    return render_template(
        "citizen/login.html"
    )


# =========================================================
# CITIZEN LOGOUT
# =========================================================

@app.route(
    "/citizen/logout"
)
def citizen_logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# CITIZEN DASHBOARD
# =========================================================

@app.route(
    "/citizen/dashboard"
)
@citizen_required
def citizen_dashboard():

    grievances = fetch_all(
        """
        SELECT
            g.*,
            d.department_name

        FROM grievances g

        LEFT JOIN departments d
            ON g.department_id =
               d.department_id

        WHERE
            g.citizen_id = %s

        ORDER BY
            g.created_at DESC
        """,
        (
            session["citizen_id"],
        )
    )


    notifications = fetch_all(
        """
        SELECT *
        FROM notifications

        WHERE
            citizen_id = %s

        ORDER BY
            created_at DESC

        LIMIT 20
        """,
        (
            session["citizen_id"],
        )
    )


    return render_template(
        "citizen/dashboard.html",
        grievances=grievances,
        notifications=notifications
    )


# =========================================================
# LODGE CITIZEN GRIEVANCE
# =========================================================

@app.route(
    "/citizen/lodge",
    methods=["GET", "POST"]
)
@citizen_required
def lodge():

    if request.method == "POST":

        category = request.form[
            "category"
        ]

        complaint_type = request.form[
            "complaint_type"
        ]

        complaint_details = request.form[
            "complaint_details"
        ].strip()

        complaint_photo = request.files.get(
            "complaint_photo"
        )


        # -------------------------------------
        # Validate category
        # -------------------------------------

        if category not in OPTIONS:

            flash(
                "Invalid category selection.",
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # Validate complaint type
        # -------------------------------------

        if (
            complaint_type
            not in OPTIONS[category]
        ):

            flash(
                "Invalid complaint type for the selected category.",
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # Complaint photo required
        # -------------------------------------

        if (
            not complaint_photo
            or
            not complaint_photo.filename
        ):

            flash(
                "Complaint photo is required.",
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # Save complaint photo
        # -------------------------------------

        try:

            complaint_photo_path = save_image(
                complaint_photo,
                "complaints"
            )

        except ValueError as error:

            flash(
                str(error),
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # AI Priority Prediction
        # -------------------------------------

        try:

            priority = predict_priority(
                complaint_type
                + " "
                + complaint_details
            )

        except Exception:

            flash(
                "AI model is not trained. Run: python ml\\train_model.py",
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # Get department
        # -------------------------------------

        department_name = get_department(
            category
        )


        department = fetch_one(
            """
            SELECT
                department_id

            FROM departments

            WHERE
                department_name = %s
            """,
            (
                department_name,
            )
        )


        if not department:

            flash(
                "Department not found.",
                "error"
            )

            return redirect(
                url_for("lodge")
            )


        # -------------------------------------
        # Save grievance
        # -------------------------------------

        connection = get_connection()

        try:

            with connection.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                # Initial insert
                cursor.execute(
                    """
                    INSERT INTO grievances
                    (
                        grievance_code,
                        citizen_id,
                        category,
                        complaint_type,
                        complaint_details,
                        priority,
                        department_id,
                        status
                    )
                    VALUES
                    (
                        'TEMP',
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'Submitted'
                    )

                    RETURNING *
                    """,
                    (
                        session["citizen_id"],
                        category,
                        complaint_type,
                        complaint_details,
                        priority,
                        department[
                            "department_id"
                        ]
                    )
                )


                grievance = cursor.fetchone()


                grievance_id = (
                    grievance["grievance_id"]
                )


                grievance_code = (
                    f"GRV-{grievance_id:06d}"
                )


                # Update grievance code
                cursor.execute(
                    """
                    UPDATE grievances

                    SET
                        grievance_code = %s

                    WHERE
                        grievance_id = %s

                    RETURNING *
                    """,
                    (
                        grievance_code,
                        grievance_id
                    )
                )


                grievance = cursor.fetchone()


                # Save citizen photo
                cursor.execute(
                    """
                    INSERT INTO grievance_photos
                    (
                        grievance_id,
                        citizen_id,
                        worker_id,
                        photo_type,
                        photo_path
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        NULL,
                        'CITIZEN_COMPLAINT',
                        %s
                    )
                    """,
                    (
                        grievance_id,
                        session["citizen_id"],
                        complaint_photo_path
                    )
                )


                # Initial follow-up
                cursor.execute(
                    """
                    INSERT INTO grievance_followups
                    (
                        grievance_id,
                        officer_id,
                        worker_id,
                        status,
                        remarks
                    )

                    VALUES
                    (
                        %s,
                        NULL,
                        NULL,
                        'Submitted',
                        %s
                    )
                    """,
                    (
                        grievance_id,
                        (
                            "Complaint submitted. "
                            "Category selected by citizen "
                            "and priority predicted by AI."
                        )
                    )
                )


            # COMMIT grievance + photo + followup
            connection.commit()


        except Exception:

            connection.rollback()

            raise

        finally:

            connection.close()


        return render_template(
            "citizen/success.html",
            grievance=grievance,
            department=department_name
        )


    return render_template(
        "citizen/lodge.html",
        options=OPTIONS
    )


# =========================================================
# CITIZEN GRIEVANCE DETAILS
# =========================================================

@app.route(
    "/citizen/grievance/<int:gid>"
)
@citizen_required
def citizen_grievance(gid):

    grievance = fetch_one(
        """
        SELECT
            g.*,
            d.department_name

        FROM grievances g

        LEFT JOIN departments d
            ON g.department_id =
               d.department_id

        WHERE
            g.grievance_id = %s

            AND

            g.citizen_id = %s
        """,
        (
            gid,
            session["citizen_id"]
        )
    )


    if not grievance:

        flash(
            "Grievance not found.",
            "error"
        )

        return redirect(
            url_for(
                "citizen_dashboard"
            )
        )


    followups = fetch_all(
        """
        SELECT
            f.*,
            o.name AS officer_name,
            w.name AS worker_name,
            w.emp_id

        FROM grievance_followups f

        LEFT JOIN officers o
            ON f.officer_id =
               o.officer_id

        LEFT JOIN workers w
            ON f.worker_id =
               w.worker_id

        WHERE
            f.grievance_id = %s

        ORDER BY
            f.followup_date
        """,
        (
            gid,
        )
    )


    photos = fetch_all(
        """
        SELECT *
        FROM grievance_photos

        WHERE
            grievance_id = %s

        ORDER BY
            uploaded_at
        """,
        (
            gid,
        )
    )


    return render_template(
        "citizen/detail.html",
        g=grievance,
        followups=followups,
        photos=photos
    )


# =========================================================
# OFFICER LOGIN
# =========================================================

@app.route(
    "/officer/login",
    methods=["GET", "POST"]
)
def officer_login():

    if request.method == "POST":

        email = request.form[
            "email"
        ].strip().lower()

        password = request.form[
            "password"
        ]


        officer = fetch_one(
            """
            SELECT
                o.*,
                d.department_name

            FROM officers o

            LEFT JOIN departments d
                ON o.department_id =
                   d.department_id

            WHERE
                o.email = %s
            """,
            (
                email,
            )
        )


        if (
            officer
            and
            check_password_hash(
                officer["password_hash"],
                password
            )
        ):

            session.clear()

            session["officer_id"] = (
                officer["officer_id"]
            )

            session["officer_name"] = (
                officer["name"]
            )

            session["department_id"] = (
                officer["department_id"]
            )

            session["department_name"] = (
                officer["department_name"]
            )


            return redirect(
                url_for(
                    "officer_dashboard"
                )
            )


        flash(
            "Invalid email or password.",
            "error"
        )


    return render_template(
        "officer/login.html"
    )


# =========================================================
# OFFICER LOGOUT
# =========================================================

@app.route(
    "/officer/logout"
)
def officer_logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# OFFICER DASHBOARD
# =========================================================

@app.route(
    "/officer/dashboard"
)
@officer_required
def officer_dashboard():

    grievances = fetch_all(
        """
        SELECT
            g.*,
            c.name AS citizen_name,
            d.department_name

        FROM grievances g

        JOIN citizens c
            ON g.citizen_id =
               c.citizen_id

        LEFT JOIN departments d
            ON g.department_id =
               d.department_id

        WHERE
            g.department_id = %s

        ORDER BY
            g.updated_at DESC
        """,
        (
            session["department_id"],
        )
    )


    available_workers = fetch_all(
        """
        SELECT
            worker_id,
            emp_id,
            name,
            mobile

        FROM workers

        WHERE
            department_id = %s

            AND

            availability_status = 'AVAILABLE'

        ORDER BY
            emp_id
        """,
        (
            session["department_id"],
        )
    )


    busy_workers = fetch_all(
        """
        SELECT
            w.emp_id,
            w.name,
            g.grievance_code,
            ga.status

        FROM workers w

        JOIN grievance_assignments ga
            ON w.worker_id =
               ga.worker_id

        JOIN grievances g
            ON ga.grievance_id =
               g.grievance_id

        WHERE
            w.department_id = %s

            AND

            w.availability_status = 'BUSY'

        ORDER BY
            w.emp_id
        """,
        (
            session["department_id"],
        )
    )


    return render_template(
        "officer/dashboard.html",
        grievances=grievances,
        available=available_workers,
        busy=busy_workers
    )


# =========================================================
# OFFICER COMPLAINT DETAILS
# =========================================================

@app.route(
    "/officer/complaint/<int:gid>"
)
@officer_required
def officer_detail(gid):

    grievance = fetch_one(
        """
        SELECT
            g.*,
            c.name AS citizen_name,
            c.mobile,
            c.email,
            c.address,
            d.department_name

        FROM grievances g

        JOIN citizens c
            ON g.citizen_id =
               c.citizen_id

        LEFT JOIN departments d
            ON g.department_id =
               d.department_id

        WHERE
            g.grievance_id = %s
        """,
        (
            gid,
        )
    )


    if not grievance:

        flash(
            "Grievance not found.",
            "error"
        )

        return redirect(
            url_for(
                "officer_dashboard"
            )
        )


    assignment = fetch_one(
        """
        SELECT
            ga.*,
            w.emp_id,
            w.name AS worker_name

        FROM grievance_assignments ga

        JOIN workers w
            ON ga.worker_id =
               w.worker_id

        WHERE
            ga.grievance_id = %s

        ORDER BY
            ga.assignment_id DESC

        LIMIT 1
        """,
        (
            gid,
        )
    )


    available_workers = fetch_all(
        """
        SELECT
            worker_id,
            emp_id,
            name,
            mobile

        FROM workers

        WHERE
            department_id = %s

            AND

            availability_status = 'AVAILABLE'

        ORDER BY
            emp_id
        """,
        (
            grievance[
                "department_id"
            ],
        )
    )


    photos = fetch_all(
        """
        SELECT
            gp.*,
            w.emp_id,
            w.name AS worker_name

        FROM grievance_photos gp

        LEFT JOIN workers w
            ON gp.worker_id =
               w.worker_id

        WHERE
            gp.grievance_id = %s

        ORDER BY
            gp.uploaded_at
        """,
        (
            gid,
        )
    )


    followups = fetch_all(
        """
        SELECT
            f.*,
            o.name AS officer_name,
            w.emp_id,
            w.name AS worker_name

        FROM grievance_followups f

        LEFT JOIN officers o
            ON f.officer_id =
               o.officer_id

        LEFT JOIN workers w
            ON f.worker_id =
               w.worker_id

        WHERE
            f.grievance_id = %s

        ORDER BY
            f.followup_date
        """,
        (
            gid,
        )
    )


    return render_template(
        "officer/detail.html",
        g=grievance,
        a=assignment,
        workers=available_workers,
        photos=photos,
        followups=followups
    )


# =========================================================
# OFFICER ASSIGN WORKER
# =========================================================

@app.route(
    "/officer/assign/<int:gid>",
    methods=["POST"]
)
@officer_required
def assign(gid):

    worker_id = request.form.get(
        "worker_id",
        type=int
    )


    if not worker_id:

        flash(
            "Please select a worker.",
            "error"
        )

        return redirect(
            url_for(
                "officer_detail",
                gid=gid
            )
        )


    connection = get_connection()

    try:

        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            # Lock worker record
            cursor.execute(
                """
                SELECT
                    worker_id,
                    department_id,
                    availability_status

                FROM workers

                WHERE
                    worker_id = %s

                FOR UPDATE
                """,
                (
                    worker_id,
                )
            )

            worker = cursor.fetchone()


            # Lock grievance record
            cursor.execute(
                """
                SELECT
                    grievance_id,
                    department_id,
                    status

                FROM grievances

                WHERE
                    grievance_id = %s

                FOR UPDATE
                """,
                (
                    gid,
                )
            )

            grievance = cursor.fetchone()


            if not worker:

                connection.rollback()

                flash(
                    "Worker not found.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_detail",
                        gid=gid
                    )
                )


            if not grievance:

                connection.rollback()

                flash(
                    "Grievance not found.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_dashboard"
                    )
                )


            if (
                worker[
                    "availability_status"
                ] != "AVAILABLE"
            ):

                connection.rollback()

                flash(
                    "This worker is already assigned to another work.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_detail",
                        gid=gid
                    )
                )


            if (
                worker[
                    "department_id"
                ]
                !=
                session[
                    "department_id"
                ]
            ):

                connection.rollback()

                flash(
                    "Worker belongs to another department.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_detail",
                        gid=gid
                    )
                )


            if (
                grievance[
                    "department_id"
                ]
                !=
                session[
                    "department_id"
                ]
            ):

                connection.rollback()

                flash(
                    "This complaint belongs to another department.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_dashboard"
                    )
                )


            if grievance[
                "status"
            ] not in (
                "Submitted",
                "Rework Required"
            ):

                connection.rollback()

                flash(
                    "This grievance is not ready for worker assignment.",
                    "error"
                )

                return redirect(
                    url_for(
                        "officer_detail",
                        gid=gid
                    )
                )


            # Assign worker
            cursor.execute(
                """
                INSERT INTO grievance_assignments
                (
                    grievance_id,
                    worker_id,
                    officer_id,
                    status
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'ASSIGNED'
                )
                """,
                (
                    gid,
                    worker_id,
                    session["officer_id"]
                )
            )


            # Worker becomes busy
            cursor.execute(
                """
                UPDATE workers

                SET
                    availability_status = 'BUSY'

                WHERE
                    worker_id = %s
                """,
                (
                    worker_id,
                )
            )


            # Complaint assigned
            cursor.execute(
                """
                UPDATE grievances

                SET
                    status = 'Assigned',
                    updated_at = CURRENT_TIMESTAMP

                WHERE
                    grievance_id = %s
                """,
                (
                    gid,
                )
            )


            # Follow-up
            cursor.execute(
                """
                INSERT INTO grievance_followups
                (
                    grievance_id,
                    officer_id,
                    worker_id,
                    status,
                    remarks
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'Assigned',
                    %s
                )
                """,
                (
                    gid,
                    session["officer_id"],
                    worker_id,
                    "Work assigned to field worker."
                )
            )


        connection.commit()


    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


    flash(
        "Worker assigned successfully.",
        "success"
    )


    return redirect(
        url_for(
            "officer_detail",
            gid=gid
        )
    )


# =========================================================
# OFFICER VERIFY WORK
# =========================================================

@app.route(
    "/officer/verify/<int:gid>",
    methods=["POST"]
)
@officer_required
def verify(gid):

    # --------------------------------------
    # Read action and remarks
    # --------------------------------------

    action = request.form.get(
        "action",
        ""
    ).strip()


    remarks = request.form.get(
        "remarks",
        ""
    ).strip()


    # --------------------------------------
    # Validate action
    # --------------------------------------

    if action not in (
        "approve",
        "reject"
    ):

        flash(
            "Invalid verification action.",
            "error"
        )

        return redirect(
            url_for(
                "officer_detail",
                gid=gid
            )
        )


    # --------------------------------------
    # Rework requires remarks
    # Approval does NOT require remarks.
    # --------------------------------------

    if (
        action == "reject"
        and
        not remarks
    ):

        flash(
            "Please enter verification remarks before requesting rework.",
            "error"
        )

        return redirect(
            url_for(
                "officer_detail",
                gid=gid
            )
        )


    # --------------------------------------
    # Get latest assignment
    # --------------------------------------

    assignment = fetch_one(
        """
        SELECT
            *

        FROM grievance_assignments

        WHERE
            grievance_id = %s

        ORDER BY
            assignment_id DESC

        LIMIT 1
        """,
        (
            gid,
        )
    )


    # --------------------------------------
    # Get latest completion photo
    # --------------------------------------

    photo = fetch_one(
        """
        SELECT
            *

        FROM grievance_photos

        WHERE
            grievance_id = %s

            AND

            photo_type =
                'WORK_COMPLETION'

        ORDER BY
            uploaded_at DESC

        LIMIT 1
        """,
        (
            gid,
        )
    )


    if not assignment:

        flash(
            "No worker assignment found.",
            "error"
        )

        return redirect(
            url_for(
                "officer_detail",
                gid=gid
            )
        )


    if not photo:

        flash(
            "No worker completion photo found.",
            "error"
        )

        return redirect(
            url_for(
                "officer_detail",
                gid=gid
            )
        )


    # --------------------------------------
    # Database transaction
    # --------------------------------------

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            # ==================================
            # APPROVE
            # ==================================

            if action == "approve":

                # 1. Approve photo
                cursor.execute(
                    """
                    UPDATE grievance_photos

                    SET
                        verification_status = 'APPROVED',
                        officer_remarks = %s,
                        verified_at = CURRENT_TIMESTAMP

                    WHERE
                        photo_id = %s
                    """,
                    (
                        remarks
                        or
                        "Completion photo approved.",

                        photo[
                            "photo_id"
                        ]
                    )
                )


                # 2. Assignment verified
                cursor.execute(
                    """
                    UPDATE grievance_assignments

                    SET
                        status = 'VERIFIED',
                        completed_at = CURRENT_TIMESTAMP

                    WHERE
                        assignment_id = %s
                    """,
                    (
                        assignment[
                            "assignment_id"
                        ],
                    )
                )


                # 3. WORKER BECOMES AVAILABLE
                cursor.execute(
                    """
                    UPDATE workers

                    SET
                        availability_status = 'AVAILABLE'

                    WHERE
                        worker_id = %s
                    """,
                    (
                        assignment[
                            "worker_id"
                        ],
                    )
                )


                # 4. Grievance resolved
                cursor.execute(
                    """
                    UPDATE grievances

                    SET
                        status = 'Resolved',
                        updated_at = CURRENT_TIMESTAMP

                    WHERE
                        grievance_id = %s
                    """,
                    (
                        gid,
                    )
                )


                # 5. Follow-up
                cursor.execute(
                    """
                    INSERT INTO grievance_followups
                    (
                        grievance_id,
                        officer_id,
                        worker_id,
                        status,
                        remarks
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        'Resolved',
                        %s
                    )
                    """,
                    (
                        gid,
                        session[
                            "officer_id"
                        ],
                        assignment[
                            "worker_id"
                        ],
                        (
                            remarks
                            or
                            "Completion photo verified. Complaint resolved."
                        )
                    )
                )


                # 6. Citizen notification
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (
                        citizen_id,
                        grievance_id,
                        message
                    )

                    SELECT
                        citizen_id,
                        grievance_id,
                        %s

                    FROM grievances

                    WHERE
                        grievance_id = %s
                    """,
                    (
                        (
                            "Your grievance has been resolved "
                            "and verified by the department officer."
                        ),
                        gid
                    )
                )


                success_message = (
                    "Photo approved. Complaint resolved successfully. "
                    "Worker is now AVAILABLE."
                )


            # ==================================
            # REJECT / REWORK
            # ==================================

            else:

                # 1. Reject photo
                cursor.execute(
                    """
                    UPDATE grievance_photos

                    SET
                        verification_status = 'REJECTED',
                        officer_remarks = %s,
                        verified_at = CURRENT_TIMESTAMP

                    WHERE
                        photo_id = %s
                    """,
                    (
                        remarks,
                        photo[
                            "photo_id"
                        ]
                    )
                )


                # 2. Assignment requires rework
                cursor.execute(
                    """
                    UPDATE grievance_assignments

                    SET
                        status = 'REWORK REQUIRED'

                    WHERE
                        assignment_id = %s
                    """,
                    (
                        assignment[
                            "assignment_id"
                        ],
                    )
                )


                # 3. Complaint requires rework
                cursor.execute(
                    """
                    UPDATE grievances

                    SET
                        status = 'Rework Required',
                        updated_at = CURRENT_TIMESTAMP

                    WHERE
                        grievance_id = %s
                    """,
                    (
                        gid,
                    )
                )


                # 4. Worker stays BUSY
                # We intentionally DO NOT change
                # availability_status here.


                # 5. Follow-up
                cursor.execute(
                    """
                    INSERT INTO grievance_followups
                    (
                        grievance_id,
                        officer_id,
                        worker_id,
                        status,
                        remarks
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        'Rework Required',
                        %s
                    )
                    """,
                    (
                        gid,
                        session[
                            "officer_id"
                        ],
                        assignment[
                            "worker_id"
                        ],
                        remarks
                    )
                )


                # 6. Citizen notification
                cursor.execute(
                    """
                    INSERT INTO notifications
                    (
                        citizen_id,
                        grievance_id,
                        message
                    )

                    SELECT
                        citizen_id,
                        grievance_id,
                        %s

                    FROM grievances

                    WHERE
                        grievance_id = %s
                    """,
                    (
                        (
                            "The field work requires "
                            "additional action before final resolution."
                        ),
                        gid
                    )
                )


                success_message = (
                    "Work rejected. Worker remains BUSY for rework."
                )


            # ==================================
            # THIS COMMIT APPLIES TO BOTH CASES
            # ==================================

            connection.commit()


    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


    flash(
        success_message,
        "success" if action == "approve" else "error"
    )


    return redirect(
        url_for(
            "officer_detail",
            gid=gid
        )
    )


# =========================================================
# WORKER LOGIN
# =========================================================

@app.route(
    "/worker/login",
    methods=["GET", "POST"]
)
def worker_login():

    if request.method == "POST":

        emp_id = request.form[
            "emp_id"
        ].strip().upper()

        password = request.form[
            "password"
        ]


        worker = fetch_one(
            """
            SELECT
                w.*,
                d.department_name

            FROM workers w

            LEFT JOIN departments d
                ON w.department_id =
                   d.department_id

            WHERE
                w.emp_id = %s
            """,
            (
                emp_id,
            )
        )


        if (
            worker

            and

            check_password_hash(
                worker["password_hash"],
                password
            )
        ):

            session.clear()

            session["worker_id"] = (
                worker["worker_id"]
            )

            session["worker_emp_id"] = (
                worker["emp_id"]
            )

            session["worker_name"] = (
                worker["name"]
            )

            session[
                "worker_department_id"
            ] = worker[
                "department_id"
            ]

            session[
                "worker_department_name"
            ] = worker[
                "department_name"
            ]


            return redirect(
                url_for(
                    "worker_dashboard"
                )
            )


        flash(
            "Invalid Employee ID or Password.",
            "error"
        )


    return render_template(
        "worker/login.html"
    )


# =========================================================
# WORKER LOGOUT
# =========================================================

@app.route(
    "/worker/logout"
)
def worker_logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# WORKER DASHBOARD
# =========================================================

@app.route(
    "/worker/dashboard"
)
@worker_required
def worker_dashboard():

    assignments = fetch_all(
        """
        SELECT
            ga.*,

            g.grievance_code,
            g.category,
            g.complaint_type,
            g.complaint_details,
            g.priority,
            g.status AS grievance_status,

            c.name AS citizen_name,
            c.mobile,
            c.address

        FROM grievance_assignments ga

        JOIN grievances g
            ON ga.grievance_id =
               g.grievance_id

        JOIN citizens c
            ON g.citizen_id =
               c.citizen_id

        WHERE
            ga.worker_id = %s

        ORDER BY
            ga.assigned_at DESC
        """,
        (
            session[
                "worker_id"
            ],
        )
    )


    worker = fetch_one(
        """
        SELECT
            availability_status

        FROM workers

        WHERE
            worker_id = %s
        """,
        (
            session[
                "worker_id"
            ],
        )
    )


    return render_template(
        "worker/dashboard.html",
        assignments=assignments,
        availability=worker[
            "availability_status"
        ]
    )


# =========================================================
# WORKER START WORK
# =========================================================

@app.route(
    "/worker/start/<int:aid>",
    methods=["POST"]
)
@worker_required
def worker_start(aid):

    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    assignment_id,
                    grievance_id,
                    status

                FROM grievance_assignments

                WHERE
                    assignment_id = %s

                    AND

                    worker_id = %s

                FOR UPDATE
                """,
                (
                    aid,
                    session[
                        "worker_id"
                    ]
                )
            )


            assignment = cursor.fetchone()


            if not assignment:

                connection.rollback()

                flash(
                    "Assignment not found.",
                    "error"
                )

                return redirect(
                    url_for(
                        "worker_dashboard"
                    )
                )


            if assignment[
                2
            ] not in (
                "ASSIGNED",
                "REWORK REQUIRED"
            ):

                connection.rollback()

                flash(
                    "Assignment cannot be started.",
                    "error"
                )

                return redirect(
                    url_for(
                        "worker_dashboard"
                    )
                )


            # Start / restart work
            cursor.execute(
                """
                UPDATE grievance_assignments

                SET
                    status = 'IN PROGRESS',

                    started_at =
                        COALESCE(
                            started_at,
                            CURRENT_TIMESTAMP
                        )

                WHERE
                    assignment_id = %s
                """,
                (
                    aid,
                )
            )


            cursor.execute(
                """
                UPDATE grievances

                SET
                    status = 'In Progress',

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE
                    grievance_id = %s
                """,
                (
                    assignment[
                        1
                    ],
                )
            )


            cursor.execute(
                """
                INSERT INTO grievance_followups
                (
                    grievance_id,
                    worker_id,
                    status,
                    remarks
                )

                VALUES
                (
                    %s,
                    %s,
                    'In Progress',
                    %s
                )
                """,
                (
                    assignment[
                        1
                    ],

                    session[
                        "worker_id"
                    ],

                    "Worker started work at the assigned location."
                )
            )


        connection.commit()


    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


    flash(
        "Work marked as In Progress.",
        "success"
    )


    return redirect(
        url_for(
            "worker_dashboard"
        )
    )


# =========================================================
# WORKER COMPLETE WORK
# =========================================================

@app.route(
    "/worker/complete/<int:aid>",
    methods=["POST"]
)
@worker_required
def worker_complete(aid):

    completion_photo = request.files.get(
        "completion_photo"
    )

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()


    if (
        not completion_photo
        or
        not completion_photo.filename
    ):

        flash(
            "Completion photo is required.",
            "error"
        )

        return redirect(
            url_for(
                "worker_dashboard"
            )
        )


    try:

        completion_photo_path = save_image(
            completion_photo,
            "worker_completion"
        )

    except ValueError as error:

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for(
                "worker_dashboard"
            )
        )


    connection = get_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    assignment_id,
                    grievance_id,
                    status

                FROM grievance_assignments

                WHERE
                    assignment_id = %s

                    AND

                    worker_id = %s

                FOR UPDATE
                """,
                (
                    aid,
                    session[
                        "worker_id"
                    ]
                )
            )


            assignment = cursor.fetchone()


            if not assignment:

                connection.rollback()

                flash(
                    "Assignment not found.",
                    "error"
                )

                return redirect(
                    url_for(
                        "worker_dashboard"
                    )
                )


            if assignment[
                2
            ] != "IN PROGRESS":

                connection.rollback()

                flash(
                    "Work is not currently in progress.",
                    "error"
                )

                return redirect(
                    url_for(
                        "worker_dashboard"
                    )
                )


            # Save completion photo
            cursor.execute(
                """
                INSERT INTO grievance_photos
                (
                    grievance_id,
                    citizen_id,
                    worker_id,
                    photo_type,
                    photo_path
                )

                VALUES
                (
                    %s,
                    NULL,
                    %s,
                    'WORK_COMPLETION',
                    %s
                )
                """,
                (
                    assignment[
                        1
                    ],

                    session[
                        "worker_id"
                    ],

                    completion_photo_path
                )
            )


            # Assignment waiting verification
            cursor.execute(
                """
                UPDATE grievance_assignments

                SET
                    status =
                        'WAITING FOR VERIFICATION',

                    completed_at =
                        CURRENT_TIMESTAMP

                WHERE
                    assignment_id = %s
                """,
                (
                    aid,
                )
            )


            # Complaint waiting verification
            cursor.execute(
                """
                UPDATE grievances

                SET
                    status =
                        'Waiting for Verification',

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE
                    grievance_id = %s
                """,
                (
                    assignment[
                        1
                    ],
                )
            )


            # Follow-up
            cursor.execute(
                """
                INSERT INTO grievance_followups
                (
                    grievance_id,
                    worker_id,
                    status,
                    remarks
                )

                VALUES
                (
                    %s,
                    %s,
                    'Waiting for Verification',
                    %s
                )
                """,
                (
                    assignment[
                        1
                    ],

                    session[
                        "worker_id"
                    ],

                    (
                        remarks
                        or
                        "Worker completed the work and uploaded completion photo."
                    )
                )
            )


        connection.commit()


    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


    flash(
        "Completion submitted for officer verification.",
        "success"
    )


    return redirect(
        url_for(
            "worker_dashboard"
        )
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    try:

        row = fetch_one(
            """
            SELECT
                current_database()
                AS database_name,

                NOW()
                AS server_time
            """
        )


        return {
            "status": "ok",
            "database": row[
                "database_name"
            ],
            "server_time": str(
                row[
                    "server_time"
                ]
            )
        }


    except Exception as error:

        return {
            "status": "database_error",
            "error": str(error)
        }, 500


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )