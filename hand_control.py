import cv2
import mediapipe as mp
import numpy as np
from djitellopy import tello



drone = tello.Tello()
drone.connect()

pid = [0.3 , 0.2 , 0.4]
p_error = 0
cam_w = 640
cam_h = 480


def hand_follow(hand_bounding_area, center_point, prev_error):
    area = hand_bounding_area
    x= center_point
    x_error = x - (640 // 2)
    fb_speed = 0
    yaw_speed = pid[0]*x_error + pid[1]*(x_error - prev_error)
    yaw_speed = int(np.clip(yaw_speed,-100,100))

    if area != 0:
         drone.send_rc_control(0, 0, 0, -yaw_speed)
    return x_error


def hand_gesture(hand_point_list, bounding_area, bounding_center):
    global p_error
    thumbs_open = True
    index_open = True
    middle_open = True
    ring_open = True
    pinky_open = True

    # Check if all required landmarks are present
    required_landmarks = [3, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    if all(landmark in hand_point_list for landmark in required_landmarks):
        if hand_point_list[4][0] > hand_point_list[3][0]:
            thumbs_open = False
        if hand_point_list[8][1] > hand_point_list[6][1]:
            index_open = False
        if hand_point_list[12][1] > hand_point_list[10][1]:
            middle_open = False
        if hand_point_list[16][1] > hand_point_list[14][1]:
            ring_open = False
        if hand_point_list[20][1] > hand_point_list[18][1]:
            pinky_open = False

    # Print the status of each finger
    print(f"Thumbs open: {thumbs_open}")
    print(f"Index open: {index_open}")
    print(f"Middle open: {middle_open}")
    print(f"Ring open: {ring_open}")
    print(f"Pinky open: {pinky_open}")

    ##tinggal kesepakatan mau gerak gimana
    if (index_open and middle_open) and (not thumbs_open and not ring_open and not pinky_open):
        drone.flip_forward()
        print("flip forward")
    elif thumbs_open and index_open and middle_open and ring_open and pinky_open:
        p_error = hand_follow(bounding_area, bounding_center, p_error)
        print("follow my hand")
    elif thumbs_open and not( index_open or middle_open or ring_open or pinky_open ):
        drone.move_right(10)
        print("move right 10 cm")
    elif  pinky_open and not( index_open or middle_open or ring_open or thumbs_open):
        drone.move_left(10)
        print("move left 10 cm")
    elif not(thumbs_open or index_open or middle_open or ring_open or pinky_open):
        drone.land()
        print("landing")

    else:
        print("do nothing")
    return [thumbs_open, index_open, middle_open, ring_open, pinky_open]


def cam_stream():
    #cam = cv2.VideoCapture(0)
    mpHands = mp.solutions.hands
    hands = mpHands.Hands()
    mpDraw = mp.solutions.drawing_utils
    bounding_area = 0
    bounding_center = 0
    
    while True:
        #success , img = cam.read()
        img = drone.get_frame_read().frame
        img = cv2.flip(img, 1)
        imageRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imageRGB)
        hand_point = dict()
        if results.multi_hand_landmarks:
            hand_detected = True
            for idx, handLms in enumerate(results.multi_hand_landmarks): # working with each hand
                
                # Check if this is the right hand
                if results.multi_handedness[idx].classification[0].label == 'Right':
                    landmarks_list = []
                    for id, lm in enumerate(handLms.landmark):
                        h, w, c = img.shape
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        hand_point[id]=[cx, cy]
                        landmarks_list.append([cx, cy])  
                        # store the coordinates in the dictionary
                    mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
                    landmarks_array = np.array(landmarks_list, dtype=np.int32)
                    x, y, w, h = cv2.boundingRect(landmarks_array)
                    bounding_area = w * h
                    bounding_center = x + w // 2
                    # Draw the bounding rectangle on the image
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    print("Center : ", bounding_center, "Area : ", bounding_area)
                    
        else:
            hand_detected = False

        if hand_detected:
            gesture_result = hand_gesture(hand_point, bounding_area, bounding_center)
        cv2.imshow("Output", img)
        
        cv2.waitKey(1)
if __name__ == "__main__":
    
    drone.streamon()
    batt = drone.get_battery()
    print("Battery percentage: ", batt)
    print("If u want to start press 's' on your keyboard :")
    while True:
        if input() == 's':
            break
    
    drone.takeoff()
    print('Start tracking? (press y): ')
    while True:
        if input() == 'y':
            cam_stream()
            break