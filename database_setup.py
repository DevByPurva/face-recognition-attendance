import mysql.connector

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'python_project'
}

# Connect to MySQL server
try:
    # Connect without specifying database first to create it if it doesn't exist
    connection = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password']
    )
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
    cursor.execute(f"USE {db_config['database']}")
    
    # Create students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        major VARCHAR(100),
        starting_year INT,
        total_attendance INT DEFAULT 0,
        standing VARCHAR(5),
        year INT,
        last_attendance_time DATETIME,
        image_path VARCHAR(255)
    )
    """)
    
    # Sample data
    sample_data = [
        ("123456", "Purva Battawar", "Computer Science", 2023, 7, "G", 2, "2025-04-24 00:54:34", "Images/123456.png"),
        ("321654", "Murtaza Hassan", "Robotics", 2017, 7, "G", 4, "2025-02-24 00:54:34", "Images/321654.png"),
        ("852741", "Emly Blunt", "Economics", 2021, 12, "B", 1, "2025-04-24 00:54:34", "Images/852741.png"),
        ("963852", "Elon Musk", "Physics", 2020, 7, "G", 2, "2025-04-23 00:54:34", "Images/963852.png")
    ]
    
    # Check if data already exists to avoid duplicates
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.executemany("""
        INSERT INTO students 
        (student_id, name, major, starting_year, total_attendance, standing, year, last_attendance_time, image_path) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, sample_data)
        connection.commit()
        print("Sample data inserted successfully")
    else:
        print("Database already contains data")
    
    print("Database setup completed successfully")

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed")