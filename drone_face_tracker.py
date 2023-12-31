import cv2
from djitellopy import tello
import numpy as np
import time

drone = tello.Tello()
drone.connect()
drone.streamon()

fb_range = [20000, 22000]#sesuaikan dengan resolusi wajah yang dinginkan
pid = [0.3 , 0.1 , 0]#up_coming progress

p_error = [0,0]

cam_w = 640
cam_h = 480


def motion_movement(drone, feature, width, height, pid, prev_error):#parameter asli(drone, feature, camera weight, pid, previous error)

    area = feature[1]
    x, y = feature[0]

    x_error = x - (width // 2)
    y_error = y - (height // 2)

    fb_speed = 0
    yaw_speed = 0
    ud_speed = 0
    yaw_speed = pid[0]*x_error + pid[1]*(x_error - prev_error[0])
    yaw_speed = int(np.clip(yaw_speed,-100,100))

    ud_speed = pid[0]*y_error + pid[1]*(y_error - prev_error[1])
    ud_speed = int(np.clip(ud_speed, -100,100))
    if area != 0:
        #drone.send_rc_control(0, fb_speed, -ud_speed, yaw_speed)
        drone.send_rc_control(0, 0, 0, yaw_speed)
    # else:
    #     drone.send_rc_control(0,0,0,0)

    return [x_error, y_error]


def face_finder(img):
    face_cascade = cv2.CascadeClassifier("trained_file/haarcascade_frontalface_default.xml")
    #ubah jadi gray background
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #labelling x,y,w,h tiap wajah
    faces = face_cascade.detectMultiScale(img_gray, 1.3, 4)
    face_list = list()
    face_area = list()
    for x,y,w,h in faces:
        cv2.rectangle(img,(x,y), (x+w, y+h), (255, 0, 0), 5)
        #calculating center of faces and its area
        center_x = x + (w // 2)
        center_y = y + (h // 2)
        area = w * h
        cv2.circle(img, (center_x, center_y),5,(0,0,255), cv2.FILLED)
        face_list.append([center_x, center_y])
        face_area.append(area)
    
    if len(face_list) != 0:
        #if there is multiple faces, take the closest one
        face_index = face_area.index(max(face_area))
        return img, [face_list[face_index], face_area[face_index]]
    else:
        return img, [[0,0], 0]
        
def face_tracker():
    global p_error
    #capture = cv2.VideoCapture(0)
    
    while True:
        #ret, img = capture.read()
        img = drone.get_frame_read().frame
        img = cv2.resize(img, (cam_w, cam_h))
        img, feature = face_finder(img)
        p_error = motion_movement(drone,feature, cam_w,cam_h, pid, p_error)
        print("Center : ", feature[0], "Area : ", feature[1])
        cv2.imshow("Output", img)
        cv2.putText(img, f"Area: {feature[1]}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            drone.land()
            break
    #capture.release()
    cv2.destroyAllWindows()
    return

if __name__ == '__main__':
    batt = drone.get_battery()
    print("Battery percentage: ", batt)
    print("If u want to start press 's' on your keyboard :")
    while True:
        if input() == 's':
            break
    # start = time.time()
    # end = time.time()

    # while end - start < 5:
    #     end = time.time()

    drone.takeoff()
   
    print('Start tracking? (press y): ')
    while True:
        if input() == 'y':
            face_tracker()
            break
    