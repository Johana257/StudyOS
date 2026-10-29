
import csv
import os
import getpass
import mysql.connector
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt


class StudyOS:
    def __init__(self):
        self.subjects = []
        self.assignments = []
        self.sessions = []
        self.host = "localhost"
        self.username = "root"
        self.password = ""

        self.setup_database()
        self.load_data()

    # -------- DATABASE SETUP AND DATA STORAGE --------
    
    def setup_database(self):
        print("StudyOS MySQL setup")
        print("Make sure your MySQL Server is installed and running.")

        host = input("MySQL host [localhost]: ").strip()
        if host == "":
            host = "localhost"

        username = input("MySQL username [root]: ").strip()
        if username == "":
            username = "root"

        password = getpass.getpass("MySQL password (input hidden): ")

        self.host = host
        self.username = username
        self.password = password

        con = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password
        )

        cur = con.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS studyos")
        con.commit()
        cur.close()
        con.close()

        print("Connected to MySQL. Database 'studyos' is ready.\n")

    def connect_database(self):
        con = mysql.connector.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database="studyos"
        )
        return con

    @contextmanager
    def database_session(self):
        connection = self.connect_database()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def load_data(self):
        with self.database_session() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    name VARCHAR(100) PRIMARY KEY
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    subject VARCHAR(100) NOT NULL,
                    due_date VARCHAR(10),
                    completed VARCHAR(10) NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_date VARCHAR(10) NOT NULL,
                    subject VARCHAR(100) NOT NULL,
                    hours DECIMAL(6, 2) NOT NULL,
                    notes TEXT
                )
            """)

            # Import CSV records only if the new database tables are empty.
            cursor.execute("SELECT COUNT(*) FROM subjects")
            subject_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM assignments")
            assignment_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]

            if subject_count == 0 and assignment_count == 0 and session_count == 0:
                self.import_csv_data(cursor)

            cursor.execute("SELECT name FROM subjects ORDER BY name")
            self.subjects = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT id, title, subject, due_date, completed FROM assignments ORDER BY id"
            )
            rows = cursor.fetchall()
            self.assignments = []
            for row in rows:
                self.assignments.append({
                    "id": str(row[0]),
                    "title": row[1],
                    "subject": row[2],
                    "due_date": row[3] or "",
                    "completed": row[4]
                })

            cursor.execute(
                "SELECT session_date, subject, hours, notes FROM sessions ORDER BY id"
            )
            rows = cursor.fetchall()
            self.sessions = []
            for row in rows:
                self.sessions.append({
                    "date": row[0],
                    "subject": row[1],
                    "hours": str(row[2]),
                    "notes": row[3] or ""
                })

    def import_csv_data(self, cursor):
        if os.path.exists("subjects.csv"):
            with open("subjects.csv", "r", newline="") as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if len(row) > 0 and row[0].strip() != "":
                        cursor.execute(
                            "INSERT IGNORE INTO subjects (name) VALUES (%s)",
                            (row[0],)
                        )

        if os.path.exists("assignments.csv"):
            with open("assignments.csv", "r", newline="") as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if len(row) >= 5:
                        cursor.execute("""
                            INSERT IGNORE INTO assignments
                            (id, title, subject, due_date, completed)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (int(row[0]), row[1], row[2], row[3], row[4]))

        if os.path.exists("sessions.csv"):
            with open("sessions.csv", "r", newline="") as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if len(row) >= 4:
                        cursor.execute("""
                            INSERT INTO sessions (session_date, subject, hours, notes)
                            VALUES (%s, %s, %s, %s)
                        """, (row[0], row[1], float(row[2]), row[3]))

    def save_subjects(self):
        with self.database_session() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM subjects")
            for subject in self.subjects:
                cursor.execute(
                    "INSERT INTO subjects (name) VALUES (%s)",
                    (subject,)
                )

    def save_assignments(self):
        with self.database_session() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM assignments")
            for assignment in self.assignments:
                cursor.execute("""
                    INSERT INTO assignments (id, title, subject, due_date, completed)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    int(assignment["id"]),
                    assignment["title"],
                    assignment["subject"],
                    assignment["due_date"],
                    assignment["completed"]
                ))

    def save_sessions(self):
        with self.database_session() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM sessions")
            for session in self.sessions:
                cursor.execute("""
                    INSERT INTO sessions (session_date, subject, hours, notes)
                    VALUES (%s, %s, %s, %s)
                """, (
                    session["date"],
                    session["subject"],
                    float(session["hours"]),
                    session["notes"]
                ))

    # -------- SUBJECTS --------

    def view_subjects(self):
        print("\n--- MY SUBJECTS ---")

        if len(self.subjects) == 0:
            print("No subjects added yet.")
        else:
            for subject in self.subjects:
                print("- " + subject)

    def add_subject(self):
        print("\n--- ADD A SUBJECT ---")
        subject = input("Enter subject name: ").strip()

        if subject == "":
            print("Subject name cannot be empty.")
        elif subject.lower() in [
            existing.lower() for existing in self.subjects
        ]:
            print("This subject already exists.")
        else:
            self.subjects.append(subject)
            self.save_subjects()
            print("Subject added successfully!")

    # -------- CHOOSE A SUBJECT --------

    def choose_subject(self):

        if len(self.subjects) == 0:
            print("Please add a subject first.")
            return None

        print("\nAvailable subjects:")

        for i in range(len(self.subjects)):
            print(str(i + 1) + ". " + self.subjects[i])

        choice = input("Choose a subject number: ").strip()

        if not choice.isdigit():
            print("Please enter a number.")
            return None

        choice = int(choice)

        if choice < 1 or choice > len(self.subjects):
            print("Invalid subject number.")
            return None

        return self.subjects[choice - 1]

    # -------- ADD ASSIGNMENT --------

    def add_assignment(self):
        print("\n--- ADD AN ASSIGNMENT ---")

        subject = self.choose_subject()

        if subject is None:
            return

        title = input("Assignment title: ").strip()

        if title == "":
            print("Assignment title cannot be empty.")
            return

        due_date = input(
            "Due date (YYYY-MM-DD, or press Enter to skip): "
        ).strip()

        if due_date != "":
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                print("Invalid date. Please use YYYY-MM-DD.")
                return

        next_id = 1

        for assignment in self.assignments:
            if int(assignment["id"]) >= next_id:
                next_id = int(assignment["id"]) + 1

        assignment = {
            "id": str(next_id),
            "title": title,
            "subject": subject,
            "due_date": due_date,
            "completed": "No"
        }

        self.assignments.append(assignment)
        self.save_assignments()

        print("Assignment added successfully!")

    # -------- VIEW ASSIGNMENTS --------

    def view_assignments(self):
        print("\n--- MY ASSIGNMENTS ---")

        if len(self.assignments) == 0:
            print("No assignments found.")
            return

        today = date.today().isoformat()

        for assignment in self.assignments:
            print("\nID:", assignment["id"])
            print("Title:", assignment["title"])
            print("Subject:", assignment["subject"])

            if assignment["due_date"] == "":
                print("Due date: Not set")
            else:
                print("Due date:", assignment["due_date"])

            if assignment["completed"] == "Yes":
                print("Status: Completed")
            elif (
                assignment["due_date"] != ""
                and assignment["due_date"] < today
            ):
                print("Status: OVERDUE")
            else:
                print("Status: Pending")

    # -------- FILTER ASSIGNMENTS --------

    def filter_assignments(self):
        print("\n--- FILTER ASSIGNMENTS ---")
        print("1. Pending assignments")
        print("2. Completed assignments")
        print("3. Overdue assignments")

        choice = input("Choose a filter: ").strip()
        today = date.today().isoformat()
        found = False

        for assignment in self.assignments:
            is_completed = assignment["completed"] == "Yes"
            is_overdue = (
                assignment["due_date"] != ""
                and assignment["due_date"] < today
                and not is_completed
            )

            if choice == "1" and not is_completed and not is_overdue:
                matches = True
            elif choice == "2" and is_completed:
                matches = True
            elif choice == "3" and is_overdue:
                matches = True
            else:
                matches = False

            if matches:
                found = True
                print("\nID:", assignment["id"])
                print("Title:", assignment["title"])
                print("Subject:", assignment["subject"])
                print("Due date:", assignment["due_date"] or "Not set")

        if choice not in ["1", "2", "3"]:
            print("Invalid filter choice.")
        elif not found:
            print("No assignments found for this filter.")

    # -------- COMPLETE ASSIGNMENT --------

    def complete_assignment(self):
        print("\n--- COMPLETE AN ASSIGNMENT ---")

        self.view_assignments()

        if len(self.assignments) == 0:
            return

        assignment_id = input(
            "\nEnter the assignment ID to complete: "
        ).strip()

        if not assignment_id.isdigit():
            print("Please enter a valid ID.")
            return

        for assignment in self.assignments:
            if assignment["id"] == assignment_id:
                if assignment["completed"] == "Yes":
                    print("This assignment is already completed.")
                else:
                    assignment["completed"] = "Yes"
                    self.save_assignments()
                    print("Assignment completed!")
                return

        print("Assignment ID not found.")

    # -------- LOG STUDY SESSION --------

    def log_session(self):
        print("\n--- LOG A STUDY SESSION ---")

        subject = self.choose_subject()

        if subject is None:
            return

        hours_input = input("Hours studied: ").strip()

        if not hours_input.replace(".", "", 1).isdigit():
            print("Please enter a valid number of hours.")
            return

        hours = float(hours_input)

        if hours <= 0 or hours > 24:
            print("Hours must be greater than 0 and at most 24.")
            return

        session_date = input(
            "Date (YYYY-MM-DD, or press Enter for today): "
        ).strip()

        if session_date == "":
            session_date = date.today().isoformat()
        else:
            try:
                datetime.strptime(session_date, "%Y-%m-%d")
            except ValueError:
                print("Invalid date. Please use YYYY-MM-DD.")
                return

        notes = input("Notes (optional): ").strip()

        session = {
            "date": session_date,
            "subject": subject,
            "hours": str(hours),
            "notes": notes
        }

        self.sessions.append(session)
        self.save_sessions()

        print("Study session saved successfully!")

    # -------- VIEW STUDY HISTORY --------

    def view_sessions(self):
        print("\n--- STUDY SESSION HISTORY ---")

        if len(self.sessions) == 0:
            print("No study sessions recorded.")
            return

        for session in self.sessions:
            print("\nDate:", session["date"])
            print("Subject:", session["subject"])
            print("Hours:", session["hours"])
            print("Notes:", session["notes"])

    # -------- STATISTICS --------

    def view_statistics(self):
        print("\n--- STUDY STATISTICS ---")

        total_hours = 0

        for session in self.sessions:
            total_hours += float(session["hours"])

        completed = 0

        for assignment in self.assignments:
            if assignment["completed"] == "Yes":
                completed += 1

        pending = len(self.assignments) - completed

        print("Total subjects:", len(self.subjects))
        print("Study sessions:", len(self.sessions))
        print("Total study hours:", round(total_hours, 2))
        print("Completed assignments:", completed)
        print("Pending assignments:", pending)

        today_hours = 0

        for session in self.sessions:
            if session["date"] == date.today().isoformat():
                today_hours += float(session["hours"])

        print("Hours studied today:", round(today_hours, 2))

        print("\nStudy hours by subject:")

        for subject in self.subjects:
            subject_hours = 0

            for session in self.sessions:
                if session["subject"] == subject:
                    subject_hours += float(session["hours"])

            print(subject + ":", round(subject_hours, 2), "hours")

    # -------- LAST SEVEN DAYS ANALYTICS --------

    def view_weekly_analytics(self):
        print("\n--- LAST SEVEN DAYS OF STUDY ---")

        today = date.today()
        first_day = today - timedelta(days=6)
        daily_totals = {}

        for day_number in range(7):
            current_day = first_day + timedelta(days=day_number)
            daily_totals[current_day.isoformat()] = 0

        for session in self.sessions:
            if session["date"] in daily_totals:
                daily_totals[session["date"]] += float(session["hours"])

        weekly_total = 0
        for day in daily_totals:
            hours = daily_totals[day]
            weekly_total += hours
            print(day, "-", round(hours, 2), "hours")

        print("Total hours in the last seven days:", round(weekly_total, 2))

        if weekly_total == 0:
            print("Log some study sessions to see a weekly chart.")
            return

        dates = list(daily_totals.keys())
        hours = list(daily_totals.values())

        plt.figure(figsize=(8, 4))
        plt.bar(dates, hours, color="#8A5AAA", width=0.6)
        plt.title("Study Hours in the Last Seven Days")
        plt.xlabel("Date")
        plt.ylabel("Hours Studied")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.show()

    # -------- MATPLOTLIB CHART --------

    def show_chart(self):
        print("\n--- STUDY HOURS CHART ---")

        if len(self.sessions) == 0:
            print("Log a study session first to create a chart.")
            return

        subject_names = []
        subject_hours = []

        for subject in self.subjects:
            total = 0

            for session in self.sessions:
                if session["subject"] == subject:
                    total += float(session["hours"])

            subject_names.append(subject)
            subject_hours.append(total)

        plt.figure(figsize=(8, 5))
        bars = plt.bar(
            subject_names,
            subject_hours,
            color="#8A5AAA",
            width=0.55
        )
        plt.title("Study Hours by Subject")
        plt.xlabel("Subjects")
        plt.ylabel("Hours Studied")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.show()


    # -------- DELETE SUBJECT --------

    def delete_subject(self):
        print("\n--- DELETE A SUBJECT ---")

        if len(self.subjects) == 0:
            print("No subjects to delete.")
            return

        for i in range(len(self.subjects)):
            print(str(i + 1) + ". " + self.subjects[i])

        choice = input("Choose a subject number: ").strip()

        if not choice.isdigit():
            print("Please enter a number.")
            return

        choice = int(choice)

        if choice < 1 or choice > len(self.subjects):
            print("Invalid subject number.")
            return

        subject = self.subjects[choice - 1]

        confirm = input(
            "Delete " + subject + " and its related records? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Deletion cancelled.")
            return

        self.subjects.remove(subject)

        remaining_assignments = []
        for assignment in self.assignments:
            if assignment["subject"] != subject:
                remaining_assignments.append(assignment)
        self.assignments = remaining_assignments

        remaining_sessions = []
        for session in self.sessions:
            if session["subject"] != subject:
                remaining_sessions.append(session)
        self.sessions = remaining_sessions

        self.save_subjects()
        self.save_assignments()
        self.save_sessions()

        print("Subject and related records deleted.")

    # -------- DELETE ASSIGNMENT --------

    def delete_assignment(self):
        print("\n--- DELETE AN ASSIGNMENT ---")

        if len(self.assignments) == 0:
            print("No assignments to delete.")
            return

        self.view_assignments()
        choice = input("Enter assignment ID to delete: ").strip()

        if not choice.isdigit():
            print("Please enter a valid ID.")
            return

        for i in range(len(self.assignments)):
            if self.assignments[i]["id"] == choice:
                confirm = input(
                    "Are you sure you want to delete this assignment? (yes/no): "
                ).strip().lower()

                if confirm == "yes":
                    self.assignments.pop(i)
                    self.save_assignments()
                    print("Assignment deleted.")
                else:
                    print("Deletion cancelled.")
                return

        print("Assignment ID not found.")

    # -------- DELETE STUDY SESSION --------

    def delete_session(self):
        print("\n--- DELETE A STUDY SESSION ---")

        if len(self.sessions) == 0:
            print("No study sessions to delete.")
            return

        for i in range(len(self.sessions)):
            session = self.sessions[i]
            print(
                str(i + 1) + ". "
                + session["date"] + " | "
                + session["subject"] + " | "
                + session["hours"] + " hours"
            )

        choice = input("Choose a session number to delete: ").strip()

        if not choice.isdigit():
            print("Please enter a number.")
            return

        choice = int(choice)

        if choice < 1 or choice > len(self.sessions):
            print("Invalid session number.")
            return

        confirm = input(
            "Are you sure you want to delete this session? (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Deletion cancelled.")
            return

        self.sessions.pop(choice - 1)
        self.save_sessions()
        print("Study session deleted.")

    # -------- MAIN MENU --------

    def run(self):
        while True:
            print("\n" + "=" * 38)
            print("               STUDYOS")
            print("     Student Productivity Tracker")
            print("=" * 38)

            print("1. View subjects")
            print("2. Add a subject")
            print("3. Add an assignment")
            print("4. View assignments")
            print("5. Complete an assignment")
            print("6. Log a study session")
            print("7. View study session history")
            print("8. View statistics")
            print("9. View study hours chart")
            print("10. View weekly study analytics")
            print("11. Filter assignments")
            print("12. Delete a subject")
            print("13. Delete an assignment")
            print("14. Delete a study session")
            print("15. Exit")

            choice = input("\nEnter your choice: ").strip()

            if choice == "1":
                self.view_subjects()
            elif choice == "2":
                self.add_subject()
            elif choice == "3":
                self.add_assignment()
            elif choice == "4":
                self.view_assignments()
            elif choice == "5":
                self.complete_assignment()
            elif choice == "6":
                self.log_session()
            elif choice == "7":
                self.view_sessions()
            elif choice == "8":
                self.view_statistics()
            elif choice == "9":
                self.show_chart()
            elif choice == "10":
                self.view_weekly_analytics()
            elif choice == "11":
                self.filter_assignments()
            elif choice == "12":
                self.delete_subject()
            elif choice == "13":
                self.delete_assignment()
            elif choice == "14":
                self.delete_session()
            elif choice == "15":
                print("Thank you for using StudyOS!")
                break
            else:
                print("Invalid choice. Please try again.")


app = StudyOS()
app.run()
