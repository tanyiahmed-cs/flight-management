# flight-management
The program (flight_management.py) is a command-line interface written in Python using the built-in sqlite3 module. On startup, initialise_database() executes the three CREATE TABLE statements and, only when the tables are empty, loads 12 destinations, 12 pilots and 15 flights of sample data so that every feature can be tested. The code checks whether Destinations is empty before inserting sample rows into all three tables.

The user is then presented with a menu. Each menu option calls a dedicated Python function that: (1) collects and validates input (e.g. checking that a typed FlightID exists), (2) executes the corresponding parameterised SQL statement through a cursor, and (3) commits the transaction and reports the result, including the number of rows affected. Connections are opened per operation and always closed in a finally block.

Display queries join Flights to Destinations and Pilots so that users always see names rather than IDs, and use LEFT JOIN where a relationship is optional (unassigned pilots) or where a summary must include zero-count groups.
