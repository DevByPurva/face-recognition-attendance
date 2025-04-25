import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import mysql.connector
from datetime import datetime

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'python_project'
}

# Initialize webcam
cap = cv2.VideoCapture(0)  # Try 0 first, if not working change to 1
cap.set(3, 640)  # Width
cap.set(4, 480)  # Height

# Load background image
imgBackground = cv2.imread('Resources/background.png')
if imgBackground is None:
    print("Warning: Background image not found. Using plain background.")
    imgBackground = np.zeros((900, 1300, 3), dtype=np.uint8)
    imgBackground[:] = (255, 255, 255)  # White background

# Load mode images
folderModePath = 'Resources/Modes'
if not os.path.exists(folderModePath):
    os.makedirs(folderModePath)
    print(f"Created directory: {folderModePath}")
    print("Please add mode images to the Modes folder")

modePathList = os.listdir(folderModePath) if os.path.exists(folderModePath) else []
imgModeList = []

if modePathList:
    for path in modePathList:
        img = cv2.imread(os.path.join(folderModePath, path))
        if img is not None:
            imgModeList.append(img)
        else:
            print(f"Warning: Could not read mode image {path}")

# If no mode images found, create placeholder images
if not imgModeList:
    print("No mode images found. Creating placeholder mode images.")
    # Create 4 placeholder mode images
    for i in range(4):
        img = np.zeros((633, 414, 3), dtype=np.uint8)
        img[:] = (220, 220, 220)  # Light gray background
        cv2.putText(img, f"Mode {i}", (150, 300), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
        imgModeList.append(img)

# Load the encoding file
print("Loading Encode File ...")
try:
    file = open('EncodeFile.p', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encode File Loaded")
except (FileNotFoundError, EOFError):
    print("Encode file not found or empty. Please run encode_generator.py first.")
    encodeListKnown, studentIds = [], []

modeType = 0
counter = 0
id = -1
imgStudent = []

# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    print("MySQL Connection Successful")

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame from camera. Check camera index.")
            break

        # Resize image for faster face recognition
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        # Detect faces in current frame
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        # Place webcam feed and active mode image on background
        # Adjust these values according to your background image
        try:
            imgBackground[162:162 + 480, 55:55 + 640] = img
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        except:
            print("Error overlaying images. Check dimensions.")

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                if encodeListKnown:  # Only compare if we have encodings
                    matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                    faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                    matchIndex = np.argmin(faceDis)

                    if matches[matchIndex]:
                        # Known face detected
                        y1, x2, y2, x1 = faceLoc
                        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                        bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                        imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                        id = studentIds[matchIndex]
                        
                        if counter == 0:
                            cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                            cv2.imshow("Face Attendance", imgBackground)
                            cv2.waitKey(1)
                            counter = 1
                            modeType = 1

            if counter != 0:
                if counter == 1:
                    # Get student data from database
                    cursor.execute("SELECT * FROM students WHERE student_id = %s", (id,))
                    studentInfo = cursor.fetchone()
                    print(studentInfo)

                    if studentInfo:
                        # Load student image
                        student_img_path = studentInfo['image_path']
                        if os.path.exists(student_img_path):
                            imgStudent = cv2.imread(student_img_path)
                        else:
                            print(f"Student image not found: {student_img_path}")
                            imgStudent = np.zeros((216, 216, 3), dtype=np.uint8)
                            imgStudent[:] = (200, 200, 200)  # Gray placeholder
                            
                        # Check attendance time
                        last_attendance = studentInfo['last_attendance_time']
                        if isinstance(last_attendance, str):
                            datetimeObject = datetime.strptime(last_attendance, "%Y-%m-%d %H:%M:%S")
                        else:
                            datetimeObject = last_attendance
                            
                        secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                        print(f"Seconds since last attendance: {secondsElapsed}")
                        
                        # Update attendance if more than 30 seconds have passed
                        if secondsElapsed > 30:
                            new_attendance = studentInfo['total_attendance'] + 1
                            cursor.execute("""
                            UPDATE students 
                            SET total_attendance = %s, last_attendance_time = %s 
                            WHERE student_id = %s
                            """, (new_attendance, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id))
                            connection.commit()
                            
                            # Update local copy of student info
                            studentInfo['total_attendance'] = new_attendance
                            studentInfo['last_attendance_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            modeType = 3
                            counter = 0
                            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
                    else:
                        print(f"Student ID {id} not found in database")
                        counter = 0
                        modeType = 0

                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2

                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10 and studentInfo:
                        # Display student information on the UI
                        cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['major'] or "Unknown"), (1006, 550),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(id), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['standing'] or "Unknown"), (910, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['year'] or "Unknown"), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['starting_year'] or "Unknown"), (1125, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        # Center student name
                        name = studentInfo['name']
                        (w, h), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, name, (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        # Display student image
                        if imgStudent is not None and len(imgStudent) > 0:
                            try:
                                imgStudent = cv2.resize(imgStudent, (216, 216))
                                imgBackground[175:175 + 216, 909:909 + 216] = imgStudent
                            except:
                                print("Error displaying student image")

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = None
                        imgStudent = []
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            modeType = 0
            counter = 0

        cv2.imshow("Face Attendance", imgBackground)
        
        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except mysql.connector.Error as err:
    print(f"Database Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed")
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()