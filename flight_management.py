"""
Flight Management Database Application
======================================
CM500292 - Databases Coursework

A command-line interface (CLI) that connects to a SQLite database and
allows airline staff to manage FLIGHTS, PILOTS and DESTINATIONS.

The schema (three related tables) is created automatically on first run
and is pre-populated with sample data (12 destinations, 12 pilots,
15 flights) so the application can be demonstrated immediately.
"""

import sqlite3

DB_NAME = "flight_management.db"

# ---------------------------------------------------------------------------
# 1. SCHEMA - SQL statements that create the three tables
# ---------------------------------------------------------------------------
# A flight MUST belong to exactly one destination (DestinationID is a
# mandatory foreign key). A flight MAY have one pilot assigned (PilotID
# is optional - NULL means "pilot not assigned yet").

SQL_CREATE_DESTINATIONS = (
    "CREATE TABLE IF NOT EXISTS Destinations ("
    "DestinationID INTEGER PRIMARY KEY AUTOINCREMENT, "
    "City TEXT NOT NULL, "
    "Country TEXT NOT NULL, "
    "AirportCode TEXT NOT NULL UNIQUE)"
)

SQL_CREATE_PILOTS = (
    "CREATE TABLE IF NOT EXISTS Pilots ("
    "PilotID INTEGER PRIMARY KEY AUTOINCREMENT, "
    "FirstName TEXT NOT NULL, "
    "LastName TEXT NOT NULL, "
    "LicenseNumber TEXT NOT NULL UNIQUE, "
    "HoursFlown INTEGER NOT NULL DEFAULT 0)"
)

SQL_CREATE_FLIGHTS = (
    "CREATE TABLE IF NOT EXISTS Flights ("
    "FlightID INTEGER PRIMARY KEY AUTOINCREMENT, "
    "FlightNumber TEXT NOT NULL, "
    "Origin TEXT NOT NULL, "
    "DestinationID INTEGER NOT NULL, "
    "DepartureDateTime TEXT NOT NULL, "
    "ArrivalDateTime TEXT, "
    "Status TEXT NOT NULL DEFAULT 'Scheduled', "
    "PilotID INTEGER, "
    "FOREIGN KEY (DestinationID) REFERENCES Destinations(DestinationID), "
    "FOREIGN KEY (PilotID) REFERENCES Pilots(PilotID))"
)

SCHEMA_STATEMENTS = [
    SQL_CREATE_DESTINATIONS,
    SQL_CREATE_PILOTS,
    SQL_CREATE_FLIGHTS,
]

# ---------------------------------------------------------------------------
# 2. INSERT statements (parameterised with ? placeholders to avoid SQL
#    injection and syntax errors with user input)
# ---------------------------------------------------------------------------

SQL_INSERT_DESTINATION = (
    "INSERT INTO Destinations (City, Country, AirportCode) VALUES (?, ?, ?)"
)
SQL_INSERT_PILOT = (
    "INSERT INTO Pilots (FirstName, LastName, LicenseNumber, HoursFlown) "
    "VALUES (?, ?, ?, ?)"
)
SQL_INSERT_FLIGHT = (
    "INSERT INTO Flights (FlightNumber, Origin, DestinationID, "
    "DepartureDateTime, ArrivalDateTime, Status, PilotID) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)"
)

# ---------------------------------------------------------------------------
# 3. SELECT queries
# ---------------------------------------------------------------------------

# "Base" query used whenever flight details are displayed: joins Flights to
# Destinations (so the city/airport is shown instead of a bare ID) and
# LEFT JOINs Pilots (a flight may have no pilot yet, so LEFT not INNER).
SQL_FLIGHT_DETAILS = (
    "SELECT f.FlightID, f.FlightNumber, f.Origin, "
    "d.City || ' (' || d.AirportCode || ')' AS Destination, "
    "f.DepartureDateTime, f.ArrivalDateTime, f.Status, "
    "p.FirstName || ' ' || p.LastName AS Pilot "
    "FROM Flights f "
    "JOIN Destinations d ON f.DestinationID = d.DestinationID "
    "LEFT JOIN Pilots p ON f.PilotID = p.PilotID"
)

SQL_SELECT_ALL_FLIGHTS = SQL_FLIGHT_DETAILS + " ORDER BY f.DepartureDateTime"

# Flight retrieval by multiple criteria (destination / status / date)
SQL_SEARCH_BY_DESTINATION = SQL_FLIGHT_DETAILS + " WHERE d.City = ?"
SQL_SEARCH_BY_STATUS = SQL_FLIGHT_DETAILS + " WHERE f.Status = ?"
SQL_SEARCH_BY_DATE = (
    SQL_FLIGHT_DETAILS + " WHERE date(f.DepartureDateTime) = ?"
)

SQL_SELECT_ALL_DESTINATIONS = (
    "SELECT * FROM Destinations ORDER BY City"
)
SQL_SEARCH_DESTINATION_BY_CITY = (
    "SELECT * FROM Destinations WHERE City = ?"
)

SQL_SELECT_ALL_PILOTS = (
    "SELECT PilotID, FirstName || ' ' || LastName AS Name, "
    "LicenseNumber, HoursFlown FROM Pilots ORDER BY LastName"
)

# Pilot schedule: all flights assigned to one pilot, with destination names
SQL_PILOT_SCHEDULE = (
    "SELECT f.FlightNumber, f.Origin, d.City AS Destination, "
    "f.DepartureDateTime, f.Status "
    "FROM Flights f "
    "JOIN Destinations d ON f.DestinationID = d.DestinationID "
    "WHERE f.PilotID = ? "
    "ORDER BY f.DepartureDateTime"
)

# Aggregation queries
SQL_COUNT_FLIGHTS_PER_DESTINATION = (
    "SELECT d.City, d.Country, COUNT(f.FlightID) AS NumberOfFlights "
    "FROM Destinations d "
    "LEFT JOIN Flights f ON f.DestinationID = d.DestinationID "
    "GROUP BY d.DestinationID "
    "ORDER BY NumberOfFlights DESC"
)
SQL_COUNT_FLIGHTS_PER_PILOT = (
    "SELECT p.FirstName || ' ' || p.LastName AS Pilot, "
    "COUNT(f.FlightID) AS NumberOfFlights "
    "FROM Pilots p "
    "LEFT JOIN Flights f ON f.PilotID = p.PilotID "
    "GROUP BY p.PilotID "
    "ORDER BY NumberOfFlights DESC"
)

# ---------------------------------------------------------------------------
# 4. UPDATE / DELETE statements
# ---------------------------------------------------------------------------

SQL_UPDATE_FLIGHT_STATUS = (
    "UPDATE Flights SET Status = ? WHERE FlightID = ?"
)
SQL_UPDATE_DEPARTURE = (
    "UPDATE Flights SET DepartureDateTime = ? WHERE FlightID = ?"
)
SQL_UPDATE_ARRIVAL = (
    "UPDATE Flights SET ArrivalDateTime = ? WHERE FlightID = ?"
)
SQL_ASSIGN_PILOT = (
    "UPDATE Flights SET PilotID = ? WHERE FlightID = ?"
)
SQL_UPDATE_DESTINATION = (
    "UPDATE Destinations SET City = ?, Country = ?, AirportCode = ? "
    "WHERE DestinationID = ?"
)

SQL_FIND_FLIGHT = "SELECT COUNT(*) FROM Flights WHERE FlightID = ?"
SQL_FIND_PILOT = "SELECT COUNT(*) FROM Pilots WHERE PilotID = ?"

# ---------------------------------------------------------------------------
# 5. SAMPLE DATA - used to populate the tables for testing/demonstration
# ---------------------------------------------------------------------------

SAMPLE_DESTINATIONS = [
    ("London", "United Kingdom", "LHR"),
    ("Paris", "France", "CDG"),
    ("New York", "United States", "JFK"),
    ("Tokyo", "Japan", "HND"),
    ("Dubai", "United Arab Emirates", "DXB"),
    ("Sydney", "Australia", "SYD"),
    ("Frankfurt", "Germany", "FRA"),
    ("Madrid", "Spain", "MAD"),
    ("Rome", "Italy", "FCO"),
    ("Amsterdam", "Netherlands", "AMS"),
    ("Singapore", "Singapore", "SIN"),
    ("Hong Kong", "Hong Kong", "HKG"),
]

SAMPLE_PILOTS = [
    ("James", "Carter", "ATPL-1001", 8200),
    ("Elena", "Rodriguez", "ATPL-1002", 6400),
    ("Wei", "Chen", "ATPL-1003", 9100),
    ("Fatima", "Al-Sayed", "ATPL-1004", 5300),
    ("Oliver", "Nash", "ATPL-1005", 7600),
    ("Ingrid", "Larsen", "ATPL-1006", 4800),
    ("Marco", "Rossi", "ATPL-1007", 11200),
    ("Aisha", "Bello", "ATPL-1008", 3700),
    ("Liam", "OConnor", "ATPL-1009", 6900),
    ("Yuki", "Tanaka", "ATPL-1010", 8400),
    ("Sofia", "Petrova", "ATPL-1011", 5500),
    ("Daniel", "Klein", "ATPL-1012", 7100),
]

# (FlightNumber, Origin, DestinationID, Departure, Arrival, Status, PilotID)
SAMPLE_FLIGHTS = [
    ("BA249", "London Heathrow", 3, "2026-10-14 08:30", "2026-10-14 11:45", "Departed", 1),
    ("AF1081", "Paris Charles de Gaulle", 1, "2026-10-14 09:15", "2026-10-14 09:55", "Arrived", 2),
    ("JL4012", "Tokyo Haneda", 11, "2026-10-14 10:00", "2026-10-14 16:40", "Boarding", 10),
    ("EK029", "Dubai International", 1, "2026-10-14 11:20", "2026-10-14 15:35", "Scheduled", 4),
    ("QF2210", "Sydney Kingsford Smith", 6, "2026-10-14 13:05", "2026-10-14 15:50", "Delayed", 6),
    ("LH911", "Frankfurt am Main", 8, "2026-10-14 14:40", "2026-10-14 17:05", "Scheduled", 12),
    ("IB3177", "Madrid Barajas", 7, "2026-10-15 07:25", "2026-10-15 09:50", "Scheduled", None),
    ("AZ202", "Rome Fiumicino", 10, "2026-10-15 08:10", "2026-10-15 10:30", "Scheduled", 7),
    ("KL1009", "Amsterdam Schiphol", 1, "2026-10-15 09:45", "2026-10-15 09:50", "Scheduled", None),
    ("SQ317", "London Heathrow", 11, "2026-10-15 11:00", "2026-10-16 07:25", "Scheduled", 3),
    ("CX251", "Hong Kong International", 1, "2026-10-15 12:30", "2026-10-15 18:05", "Scheduled", None),
    ("BA117", "London Heathrow", 3, "2026-10-15 15:20", "2026-10-15 18:30", "Scheduled", 5),
    ("AF7623", "Paris Charles de Gaulle", 9, "2026-10-16 06:50", "2026-10-16 08:55", "Scheduled", 2),
    ("EK030", "London Heathrow", 5, "2026-10-16 09:35", "2026-10-16 20:10", "Scheduled", 4),
    ("LH1340", "Frankfurt am Main", 2, "2026-10-16 10:15", "2026-10-16 11:40", "Cancelled", None),
]


# ---------------------------------------------------------------------------
# Database connection and initialisation
# ---------------------------------------------------------------------------

def get_connection():
    """Open (or create) the SQLite database and return the connection."""
    return sqlite3.connect(DB_NAME)


def initialise_database():
    """Create the three tables and populate them with sample data.
    Sample data is only inserted once - on the very first run."""
    conn = get_connection()
    cur = conn.cursor()
    for statement in SCHEMA_STATEMENTS:
        cur.execute(statement)

    cur.execute("SELECT COUNT(*) FROM Destinations")
    if cur.fetchone()[0] == 0:  # tables are empty -> insert sample data
        cur.executemany(SQL_INSERT_DESTINATION, SAMPLE_DESTINATIONS)
        cur.executemany(SQL_INSERT_PILOT, SAMPLE_PILOTS)
        cur.executemany(SQL_INSERT_FLIGHT, SAMPLE_FLIGHTS)
        print("Database created and populated with sample data.")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def ask_int(prompt):
    """Keep asking until the user enters a whole number."""
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("  Please enter a whole number.")


def ask_non_empty(prompt):
    """Keep asking until the user enters a non-empty string."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("  This field cannot be empty.")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_flights(rows):
    """Print a set of flight rows returned by a SELECT query."""
    if not rows:
        print("  No matching flights found.")
        return
    header = ("ID", "Flight", "Origin", "Destination", "Departs", "Arrives", "Status", "Pilot")
    print("  " + "{:<4}{:<9}{:<26}{:<20}{:<17}{:<17}{:<11}{}".format(*header))
    print("  " + "-" * 118)
    for row in rows:
        print("  " + "{:<4}{:<9}{:<26}{:<20}{:<17}{:<17}{:<11}{}".format(*[str(c) if c else "-" for c in row]))


def print_destinations(rows):
    if not rows:
        print("  No matching destinations found.")
        return
    print("  {:<15}{:<22}{:<25}{}".format("DestinationID", "City", "Country", "Airport Code"))
    print("  " + "-" * 80)
    for row in rows:
        print("  {:<15}{:<22}{:<25}{}".format(*[str(c) for c in row]))


def print_pilots(rows):
    if not rows:
        print("  No pilots found.")
        return
    print("  {:<8}{:<24}{:<16}{}".format("PilotID", "Name", "License No.", "Hours Flown"))
    print("  " + "-" * 60)
    for row in rows:
        print("  {:<8}{:<24}{:<16}{}".format(*[str(c) for c in row]))


def record_exists(cur, sql, record_id):
    """Return True if a record with the given primary key exists."""
    cur.execute(sql, (record_id,))
    return cur.fetchone()[0] > 0


# ---------------------------------------------------------------------------
# Menu option 1: Add a new flight
# ---------------------------------------------------------------------------

def add_flight(conn):
    print("\n--- Add a New Flight ---")
    cur = conn.cursor()

    # Show the destinations so the user can pick a valid DestinationID
    cur.execute(SQL_SELECT_ALL_DESTINATIONS)
    print_destinations(cur.fetchall())
    while True:
        dest_id = ask_int("Enter DestinationID for this flight: ")
        if record_exists(cur, "SELECT COUNT(*) FROM Destinations WHERE DestinationID = ?", dest_id):
            break
        print("  No destination with that ID. Try again.")

    flight_number = ask_non_empty("Enter Flight Number (e.g. BA249): ")
    origin = ask_non_empty("Enter Origin airport: ")
    departure = ask_non_empty("Enter departure date/time (YYYY-MM-DD HH:MM): ")
    arrival = input("Enter arrival date/time (YYYY-MM-DD HH:MM, optional): ").strip() or None
    status = input("Enter status (default Scheduled): ").strip() or "Scheduled"

    cur.execute(SQL_INSERT_FLIGHT,
                (flight_number, origin, dest_id, departure, arrival, status, None))
    conn.commit()
    print("Inserted data successfully - flight {} added.".format(flight_number))


# ---------------------------------------------------------------------------
# Menu option 2: View flights (all, or by destination / status / date)
# ---------------------------------------------------------------------------

def view_flights_menu(conn):
    print("\n--- View Flights ---")
    print(" 1. View all flights")
    print(" 2. Search by destination city")
    print(" 3. Search by status")
    print(" 4. Search by departure date")
    sub = input("Enter your choice: ").strip()
    cur = conn.cursor()

    if sub == "1":
        cur.execute(SQL_SELECT_ALL_FLIGHTS)
        print_flights(cur.fetchall())
    elif sub == "2":
        city = ask_non_empty("Enter destination city: ")
        cur.execute(SQL_SEARCH_BY_DESTINATION, (city,))
        print_flights(cur.fetchall())
    elif sub == "3":
        status = ask_non_empty("Enter status (e.g. Scheduled, Delayed, Cancelled): ")
        cur.execute(SQL_SEARCH_BY_STATUS, (status,))
        print_flights(cur.fetchall())
    elif sub == "4":
        date = ask_non_empty("Enter departure date (YYYY-MM-DD): ")
        cur.execute(SQL_SEARCH_BY_DATE, (date,))
        print_flights(cur.fetchall())
    else:
        print("  Invalid choice.")


# ---------------------------------------------------------------------------
# Menu option 3: Update flight information (schedule / status)
# ---------------------------------------------------------------------------

def update_flight(conn):
    print("\n--- Update Flight Information ---")
    cur = conn.cursor()
    flight_id = ask_int("Enter the FlightID of the flight to update: ")

    if not record_exists(cur, SQL_FIND_FLIGHT, flight_id):
        print("  Cannot find this record in the database.")
        return

    print("  1. Change status")
    print("  2. Change departure date/time")
    print("  3. Change arrival date/time")
    sub = input("Enter your choice: ").strip()

    if sub == "1":
        value = ask_non_empty("Enter new status: ")
        cur.execute(SQL_UPDATE_FLIGHT_STATUS, (value, flight_id))
    elif sub == "2":
        value = ask_non_empty("Enter new departure date/time (YYYY-MM-DD HH:MM): ")
        cur.execute(SQL_UPDATE_DEPARTURE, (value, flight_id))
    elif sub == "3":
        value = ask_non_empty("Enter new arrival date/time (YYYY-MM-DD HH:MM): ")
        cur.execute(SQL_UPDATE_ARRIVAL, (value, flight_id))
    else:
        print("  Invalid choice.")
        return

    conn.commit()
    if cur.rowcount != 0:
        print(str(cur.rowcount) + " row(s) affected.")
    else:
        print("  Cannot find this record in the database.")


# ---------------------------------------------------------------------------
# Menu option 4: Assign a pilot to a flight
# ---------------------------------------------------------------------------

def assign_pilot(conn):
    print("\n--- Assign Pilot to Flight ---")
    cur = conn.cursor()

    flight_id = ask_int("Enter the FlightID to assign a pilot to: ")
    if not record_exists(cur, SQL_FIND_FLIGHT, flight_id):
        print("  Cannot find this record in the database.")
        return

    cur.execute(SQL_SELECT_ALL_PILOTS)
    print_pilots(cur.fetchall())
    pilot_id = ask_int("Enter the PilotID to assign: ")
    if not record_exists(cur, SQL_FIND_PILOT, pilot_id):
        print("  No pilot with that ID.")
        return

    cur.execute(SQL_ASSIGN_PILOT, (pilot_id, flight_id))
    conn.commit()
    if cur.rowcount != 0:
        print("Pilot {} assigned to flight {}.".format(pilot_id, flight_id))
    else:
        print("  Cannot find this record in the database.")


# ---------------------------------------------------------------------------
# Menu option 5: View a pilot's schedule
# ---------------------------------------------------------------------------

def view_pilot_schedule(conn):
    print("\n--- View Pilot Schedule ---")
    cur = conn.cursor()
    cur.execute(SQL_SELECT_ALL_PILOTS)
    print_pilots(cur.fetchall())

    pilot_id = ask_int("Enter the PilotID to view the schedule for: ")
    if not record_exists(cur, SQL_FIND_PILOT, pilot_id):
        print("  No pilot with that ID.")
        return

    cur.execute(SQL_PILOT_SCHEDULE, (pilot_id,))
    rows = cur.fetchall()
    if not rows:
        print("  This pilot has no flights assigned.")
        return
    print("  {:<9}{:<26}{:<18}{:<17}{}".format("Flight", "Origin", "Destination", "Departs", "Status"))
    print("  " + "-" * 90)
    for row in rows:
        print("  {:<9}{:<26}{:<18}{:<17}{}".format(*[str(c) for c in row]))


# ---------------------------------------------------------------------------
# Menu option 6: View / update destination information
# ---------------------------------------------------------------------------

def destinations_menu(conn):
    print("\n--- Destination Management ---")
    print(" 1. View all destinations")
    print(" 2. Search destination by city")
    print(" 3. Add a new destination")
    print(" 4. Update a destination")
    sub = input("Enter your choice: ").strip()
    cur = conn.cursor()

    if sub == "1":
        cur.execute(SQL_SELECT_ALL_DESTINATIONS)
        print_destinations(cur.fetchall())
    elif sub == "2":
        city = ask_non_empty("Enter city: ")
        cur.execute(SQL_SEARCH_DESTINATION_BY_CITY, (city,))
        print_destinations(cur.fetchall())
    elif sub == "3":
        city = ask_non_empty("Enter city: ")
        country = ask_non_empty("Enter country: ")
        code = ask_non_empty("Enter airport code (e.g. LHR): ")
        cur.execute(SQL_INSERT_DESTINATION, (city, country, code))
        conn.commit()
        print("Destination added successfully.")
    elif sub == "4":
        cur.execute(SQL_SELECT_ALL_DESTINATIONS)
        print_destinations(cur.fetchall())
        dest_id = ask_int("Enter the DestinationID to update: ")
        if not record_exists(cur,
                             "SELECT COUNT(*) FROM Destinations WHERE DestinationID = ?",
                             dest_id):
            print("  Cannot find this record in the database.")
            return
        city = ask_non_empty("Enter new city: ")
        country = ask_non_empty("Enter new country: ")
        code = ask_non_empty("Enter new airport code: ")
        cur.execute(SQL_UPDATE_DESTINATION, (city, country, code, dest_id))
        conn.commit()
        if cur.rowcount != 0:
            print(str(cur.rowcount) + " row(s) affected.")
        else:
            print("  Cannot find this record in the database.")
    else:
        print("  Invalid choice.")


# ---------------------------------------------------------------------------
# Menu option 7: Summary reports (aggregations)
# ---------------------------------------------------------------------------

def summary_reports(conn):
    print("\n--- Summary Reports ---")
    cur = conn.cursor()

    print("\n  Number of flights to each destination:")
    cur.execute(SQL_COUNT_FLIGHTS_PER_DESTINATION)
    print("  {:<22}{:<25}{}".format("City", "Country", "Number of Flights"))
    print("  " + "-" * 60)
    for row in cur.fetchall():
        print("  {:<22}{:<25}{}".format(*[str(c) for c in row]))

    print("\n  Number of flights assigned to each pilot:")
    cur.execute(SQL_COUNT_FLIGHTS_PER_PILOT)
    print("  {:<24}{}".format("Pilot", "Number of Flights"))
    print("  " + "-" * 40)
    for row in cur.fetchall():
        print("  {:<24}{}".format(*[str(c) for c in row]))


# ---------------------------------------------------------------------------
# Main menu loop
# ---------------------------------------------------------------------------

MENU = """
 Menu:
**********
 1. Add a new flight
 2. View flights (all / by criteria)
 3. Update flight information
 4. Assign pilot to flight
 5. View pilot schedule
 6. View / update destination information
 7. Summary reports
 0. Exit
"""


def main():
    initialise_database()
    while True:
        print(MENU)
        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        conn = get_connection()
        try:
            if choice == "1":
                add_flight(conn)
            elif choice == "2":
                view_flights_menu(conn)
            elif choice == "3":
                update_flight(conn)
            elif choice == "4":
                assign_pilot(conn)
            elif choice == "5":
                view_pilot_schedule(conn)
            elif choice == "6":
                destinations_menu(conn)
            elif choice == "7":
                summary_reports(conn)
            else:
                print("Invalid choice.")
        except sqlite3.Error as e:
            print("Database error:", e)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
