from flask import Flask, render_template, request, redirect
from config import get_db_connection
from datetime import datetime
print("REDIRECT IMPORT TEST")

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM users
        WHERE username=%s AND password=%s
        """,
        (username, password)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return redirect("/dashboard")
    else:
        return """
        <h2>❌ Invalid Username or Password</h2>
        <a href="/">Try Again</a>
        """

# Dashboard
@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM slots")
    total_slots = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM slots WHERE status='Available'")
    available_slots = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM slots WHERE status='Occupied'")
    occupied_slots = cursor.fetchone()[0]

    # Get currently parked cars
    cursor.execute("""
        SELECT car_number, owner_name, slot, entry_time
        FROM parking
        WHERE status='Parked'
    """)
    cars = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        cars=cars
    )


# Car Entry
@app.route("/car_entry", methods=["GET", "POST"])
def car_entry():

    if request.method == "POST":

        car_number = request.form["car_number"].strip().upper()
        owner_name = request.form["owner_name"]
        slot = request.form["slot"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing parked car
        cursor.execute("""
            SELECT id FROM parking
            WHERE car_number=%s AND status='Parked'
        """, (car_number,))

        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()

            return """
            <h2>❌ Car already parked!</h2>
            <a href="/car_entry">Back</a>
            """


        # Insert car
        cursor.execute("""
            INSERT INTO parking
            (car_number, owner_name, slot, entry_time, status)
            VALUES (%s,%s,%s,NOW(),'Parked')
        """,
        (car_number, owner_name, slot))


        # Update slot
        cursor.execute("""
            UPDATE slots
            SET status='Occupied'
            WHERE slot_number=%s
        """,(slot,))


        conn.commit()

        cursor.close()
        conn.close()


        return """
        <h2>✅ Car Parked Successfully</h2>
        <a href="/dashboard">Dashboard</a>
        """


    return render_template("car_entry.html")


#view car route
@app.route("/view_cars")
def view_cars():

    search = request.args.get("search")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute("""
            SELECT *
            FROM parking
            WHERE status='Parked'
            AND car_number LIKE %s
        """, ("%" + search + "%",))
    else:
        cursor.execute("""
            SELECT *
            FROM parking
            WHERE status='Parked'
        """)

    cars = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("view_cars.html", cars=cars)


# Car Exit
@app.route("/car_exit", methods=["GET","POST"])
def car_exit():

    if request.method=="POST":

        car_number=request.form["car_number"].strip().upper()

        conn=get_db_connection()
        cursor=conn.cursor(buffered=True)


        cursor.execute("""
            SELECT owner_name, slot, entry_time
            FROM parking
            WHERE TRIM(UPPER(car_number))=%s
            AND status='Parked'
        """,(car_number,))


        car=cursor.fetchone()


        if not car:

            cursor.close()
            conn.close()

            return """
            <h2>❌ Car Not Found</h2>
            <a href="/car_exit">Back</a>
            """


        owner_name=car[0]
        slot=car[1]
        entry_time=car[2]


        # Calculate amount
        cursor.execute("""
            SELECT GREATEST(1,TIMESTAMPDIFF(HOUR,%s,NOW()))*50
        """,(entry_time,))

        amount=cursor.fetchone()[0]


        exit_time=datetime.now()


        # History
        cursor.execute("""
            INSERT INTO parking_history
            (car_number,owner_name,slot,entry_time,exit_time,amount)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            car_number,
            owner_name,
            slot,
            entry_time,
            exit_time,
            amount
        ))


        # Remove parked car
        cursor.execute("""
            DELETE FROM parking
            WHERE car_number=%s
        """,(car_number,))


        # Free slot
        cursor.execute("""
            UPDATE slots
            SET status='Available'
            WHERE slot_number=%s
        """,(slot,))


        conn.commit()


        cursor.close()
        conn.close()


        return render_template(
            "receipt.html",
            car_number=car_number,
            owner_name=owner_name,
            slot=slot,
            entry_time=entry_time,
            exit_time=exit_time,
            amount=amount
        )


    return render_template("car_exit.html")



# Slots page
@app.route("/slots")
def slots():

    conn=get_db_connection()
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM slots")

    slots=cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "slots.html",
        slots=slots
    )



# History
@app.route("/history", methods=["GET","POST"])
def history():

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        search = request.form["search"].strip().upper()

        cursor.execute("""
            SELECT *
            FROM parking_history
            WHERE TRIM(UPPER(car_number)) = %s
            ORDER BY exit_time DESC
                """,
             (search,))

    else:

        cursor.execute("""
            SELECT *
            FROM parking_history
            ORDER BY exit_time DESC
        """)


    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        history=history
    )

@app.route("/logout")
def logout():
    return render_template("login.html")



if __name__=="__main__":
    app.run(debug=True)