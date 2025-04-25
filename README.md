Face Recognition Attendance System
A cool Python project that uses your webcam to recognize faces and track student attendance in a MySQL database.
What it does

Spots faces in real-time through your webcam
Automatically logs attendance when it recognizes someone
Shows a nice UI with student info when someone is recognized
Stores everything in a MySQL database
Prevents students from marking attendance multiple times in a row (30-second cooldown)

What you'll need

Python 3.6+
MySQL Server
A webcam

Setup

Install these Python packages:
pip install mysql-connector-python opencv-python face-recognition cvzone numpy

Set up your folders like this:
your_project_folder/
├── Images/                  # Put student photos here (named like 123456.png)
├── Resources/
│   ├── background.png       # Background for the UI
│   └── Modes/               # Different UI state images
├── database_setup.py
├── encode_generator.py
└── face_attendance.py

Make sure MySQL is running with username "root" and password "root"

If your MySQL login is different, just update the db_config in the Python files



How to use it
Important: Run these in order!

First, set up the database:
python database_setup.py

Process the student images:
python encode_generator.py

Start the attendance system:
python face_attendance.py


How it works
The system uses three scripts:

database_setup.py: Creates your MySQL database and adds some sample students
encode_generator.py: Takes the photos in your Images folder and creates "face encodings" (digital face fingerprints)
face_attendance.py: The main program that:

Opens your webcam
Looks for faces
Checks if they match any students
Updates attendance in the database
Shows all the info on screen



Fixing common problems

MySQL errors: Check if MySQL is running and your username/password are correct
"Table doesn't exist" error: You probably skipped running database_setup.py first
Camera not working: Try changing cv2.VideoCapture(0) to cv2.VideoCapture(1) in the code
Missing files: The program will create placeholders for missing images, but it works best with proper images# face-recognition-attendance
