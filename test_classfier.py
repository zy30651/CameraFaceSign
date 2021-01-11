# -*- coding: utf-8 -*-
# 无效
#
import datetime
import face_recognition
import cv2
from os import listdir
# source = '/Users/zy/Desktop/Git/CameraFaceSign/face_video/3333.mp4'
# cam = cv2.VideoCapture(source)
# filepath = './face_photos'
# filename_list = listdir(filepath)
# known_face_names = []
# known_face_encodings = []
# a = 0
# print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# for filename in filename_list:  # 依次读入列表中的内容
#     a += 1
#     if filename.endswith('png'):  # 后缀名'jpg'匹对
#         known_face_names.append(filename[:-4])  # 把文件名字的后四位.jpg去掉获取人名
#         file_str = filepath + '/' + filename
#         a_images = face_recognition.load_image_file(file_str)
#         print(a_images.shape)
#         a_face_encoding = face_recognition.face_encodings(a_images)[0]
#         print(a_face_encoding.shape)
#         known_face_encodings.append(a_face_encoding)
# print(known_face_names, a)
#
# face_locations = []
# face_encodings = []
# face_names = []
# process_this_frame = True

print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
cap = cv2.VideoCapture(
    r'/Users/zy/Desktop/Git/CameraFaceSign/face_video/3333.mp4'
)
classfier = cv2.CascadeClassifier(
    r'/Users/zy/Desktop/Git/CameraFaceSign/haarcascade_frontalface_default.xml'
)
color = (0, 255, 0)
while cap.isOpened():
    ok, frame = cap.read()  # 读取一帧数据
   #如果读取失败，直接break
    if not ok:
        break
    # 读取成功后，将当前帧转换成灰度图像
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 人脸检测，使用detectMultiScale函数进行
    faceRects = classfier.detectMultiScale(
        grey,
        scaleFactor=1.25,
        minNeighbors=3,
        minSize=(35, 35) #设置最小检测范围，即是目标小于该值就无视
        # maxSize=(200,200)#设置最大检测范围
    )
    if len(faceRects) > 0:  # 当检测到多张脸时
        for faceRect in faceRects:  # 单独框出每一张人脸
            x, y, w, h = faceRect
            cv2.rectangle(frame, (x , y), (x + w, y + h), color, 2)

    # 显示图像
    cv2.imshow("Face Detection", frame)
    c = cv2.waitKey(5)		#数值越小播放越流畅，不可为浮点数
    if c & 0xFF == ord('q'):
        break
# 释放摄像头并销毁所有窗口
cap.release()
cv2.destroyAllWindows()
