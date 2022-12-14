# 参考
# https://google.github.io/mediapipe/solutions/pose

import math

import cv2
import mediapipe as mp
from playsound import playsound

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
# model load
mp_pose = mp.solutions.pose

# For static images:
IMAGE_FILES = []
BG_COLOR = (192, 192, 192) # gray
with mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=True,
    min_detection_confidence=0.5) as pose:
  for idx, file in enumerate(IMAGE_FILES):
    image = cv2.imread(file)
    image_height, image_width, _ = image.shape
    # Convert the BGR image to RGB before processing.
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if not results.pose_landmarks:
      continue
    print(
        f'Nose coordinates: ('
        f'{results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width}, '
        f'{results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height})'
    )

    annotated_image = image.copy()
    # Draw segmentation on the image.
    # To improve segmentation around boundaries, consider applying a joint
    # bilateral filter to "results.segmentation_mask" with "image".
    condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
    bg_image = np.zeros(image.shape, dtype=np.uint8)
    bg_image[:] = BG_COLOR
    annotated_image = np.where(condition, annotated_image, bg_image)
    # Draw pose landmarks on the image.
    mp_drawing.draw_landmarks(
        annotated_image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    cv2.imwrite('/tmp/annotated_image' + str(idx) + '.png', annotated_image)
    # Plot pose world landmarks.
    mp_drawing.plot_landmarks(
        results.pose_world_landmarks, mp_pose.POSE_CONNECTIONS)

# For webcam input:
# cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture(1)
cap = cv2.VideoCapture("sample_video\pushup_sample.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
# 3秒間に1度だけカウントするように定義する。
max_inference = fps * 3

push_up_cnt = 0
frame = 0
# 画像保存用
count = 0
with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:
  while cap.isOpened():
    frame +=1
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      # If loading a video, use 'break' instead of 'continue'.
      continue

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    # 判定する基準の設定
    if results.pose_landmarks:
      for idx, landmark in enumerate(results.pose_landmarks.landmark):
        if idx == 12: # 11:  # 左肩
            left_shoulder = landmark
        if idx == 20: # 19:  # 左手
            left_index = landmark
            # 2点間の距離を求める
            distance = math.sqrt((left_shoulder.x - left_index.x)**2 + (left_shoulder.y - left_index.y)**2)
            # print(distance)

            # countをn秒に1回にしたい。
            if frame > max_inference:
              if distance < 0.15:
                push_up_cnt += 1
                if push_up_cnt % 3 ==0:
                  playsound("sound\sample_sound.mp3")
                # frame数の初期化
                frame = 0
                print('push up success', f'cnt : {push_up_cnt}')



    # Draw the pose annotation on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    # Flip the image horizontally for a selfie-view display.
    # cv2.imshow('pushup_count', cv2.flip(image, 1))
    cv2.putText(image,
            text='pushup count : ' + str(push_up_cnt),
            org=(10, 40),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=1.0,
            color=(0, 255, 0),
            thickness=3,
            lineType=cv2.LINE_4)
    cv2.imshow('pushup_count', image)
    # 画像保存
    # cv2.imwrite(f"./result/{str(count).zfill(3)}_frame.jpg", image)
    # count += 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
cap.release()
cv2.destroyAllWindows()