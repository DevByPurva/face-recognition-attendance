import cv2
import face_recognition
import pickle
import os
import mysql.connector
from datetime import datetime

# Database connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'python_project'
}

# Connect to the database
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    # Importing student images
    folderPath = 'Images'
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
        print(f"Created directory: {folderPath}")
    
    pathList = os.listdir(folderPath)
    print(f"Found {len(pathList)} images in {folderPath}")
    
    imgList = []
    studentIds = []
    
    for path in pathList:
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = cv2.imread(os.path.join(folderPath, path))
            if img is not None:
                imgList.append(img)
                student_id = os.path.splitext(path)[0]
                studentIds.append(student_id)
                
                # Check if the student exists in the database
                cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
                
                if not student:
                    # If student does not exist, add a basic record
                    print(f"Adding new student record for ID: {student_id}")
                    cursor.execute("""
                    INSERT INTO students 
                    (student_id, name, image_path, total_attendance, last_attendance_time) 
                    VALUES (%s, %s, %s, %s, %s)
                    """, (student_id, f"Student {student_id}", f"Images/{path}", 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    connection.commit()
                else:
                    # Update the image path if needed
                    cursor.execute("""
                    UPDATE students SET image_path = %s WHERE student_id = %s
                    """, (f"Images/{path}", student_id))
                    connection.commit()
            else:
                print(f"Warning: Could not read image {path}")
    
    def findEncodings(imagesList):
        encodeList = []
        for img in imagesList:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            try:
                encode = face_recognition.face_encodings(img)[0]
                encodeList.append(encode)
            except IndexError:
                print(f"No face found in one of the images. Skipping...")
                encodeList.append(None)  # Append None for failed encodings
        return encodeList
    
    print("Encoding Started...")
    encodeListKnown = findEncodings(imgList)
    
    # Filter out None values (failed encodings)
    valid_encodings = []
    valid_ids = []
    for i, encoding in enumerate(encodeListKnown):
        if encoding is not None:
            valid_encodings.append(encoding)
            valid_ids.append(studentIds[i])
        else:
            print(f"Warning: Encoding failed for student ID {studentIds[i]}")
    
    encodeListKnownWithIds = [valid_encodings, valid_ids]
    print("Encoding Complete")
    
    # Save encodings to file
    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("File Saved")

except mysql.connector.Error as err:
    print(f"Database Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection closed")