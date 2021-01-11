# -*- coding: utf-8 -*-
# 摄像头头像识别
import datetime
import queue

import face_recognition
import cv2
from os import listdir

# 摄像头的rtsp地址 小屋、大屋
# source = "rtsp://admin:ADTVKL@192.168.8.216:554/h264/ch1/main/av_stream"
# source = "rtsp://admin:LEWMHE@192.168.8.212:554/h264/ch1/main/av_stream"
# source = "rtsp://admin:CLSMKY@192.168.8.214:554/h264/ch1/main/av_stream"
source = '/Users/zy/Desktop/Git/CameraFaceSign/face_video/3333.mp4'
# 本机摄像头
# cam = cv2.VideoCapture(0)
cam = cv2.VideoCapture(source)
print('cam is open %s' % cam.isOpened())
# 已知人脸图片文件夹 注意 如果会员图片后缀不是jpg 需要进行修改
filepath = './face_photos'
filename_list = listdir(filepath)
known_face_names = []
known_face_encodings = []
a = 0
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
for filename in filename_list:  # 依次读入列表中的内容
    a += 1
    if filename.endswith('png'):  # 后缀名'jpg'匹对
        known_face_names.append(filename[:-4])  # 把文件名字的后四位.jpg去掉获取人名
        file_str = filepath + '/' + filename
        a_images = face_recognition.load_image_file(file_str)
        print(a_images.shape)
        a_face_encoding = face_recognition.face_encodings(a_images)[0]
        print(a_face_encoding.shape)
        known_face_encodings.append(a_face_encoding)
print(known_face_names, a)

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
while cam.isOpened():
    # 读取摄像头画面
    ret, frame = cam.read()
    if not ret:
        # 等同于 if ret is not none
        break

    # 改变摄像头图像的大小，图像小，所做的计算就少
    # small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    # opencv的图像是BGR格式的，而我们需要是的RGB格式的，因此需要进行一个转换。
    # rgb_small_frame = frame[:, :, ::-1]

    classfier = cv2.CascadeClassifier(
        r'./haarcascade_frontalface_default.xml'
    )
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faceRects = classfier.detectMultiScale(
        grey,
        scaleFactor=1.25,
        minNeighbors=3,
        minSize=(35, 35) #设置最小检测范围，即是目标小于该值就无视
        # maxSize=(200,200)#设置最大检测范围
    )

    # Only process every other frame of video to save time
    if process_this_frame:
        # 根据encoding来判断是不是同一个人，是就输出true，不是为flase
        face_locations = face_recognition.face_locations(rgb_small_frame)
        print("face_locations %s" % face_locations)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_names = []
        for face_encoding in face_encodings:
            # 默认为unknown
            print(face_encoding.shape)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.46)
            # 阈值太低容易造成无法成功识别人脸，太高容易造成人脸识别混淆 默认阈值tolerance为0.6

            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)
        print(face_names)

    process_this_frame = not process_this_frame

    # 将捕捉到的人脸显示出来
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        # 由于我们检测到的帧被缩放到1/4大小，所以要缩小面位置
        # 矩形框
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # 引入ft2中的字体
        # 加上标签
        cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

        # frame = ft.draw_text(frame,(left + 6, bottom - 6), name, 1.0, (255, 255, 255))
        # def draw_text(self, image, pos, text, text_size, text_color)
    # Display

    cv2.imshow('monitor', frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cam.release()
cv2.destroyAllWindows()
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# 根据本地视频，进行人脸识别
'''
def check_face_sign(path):
    print('Task for %s' % path)
    cam = cv2.VideoCapture(path)

    while (cam.isOpened()):
        # 读取摄像头画面
        ret, frame = cam.read()
        print(ret)
        if not ret:
            # 等同于 if ret is not none
            print('%s %s 视频读取不到' % (path))
            break

        # 改变摄像头图像的大小，图像小，所做的计算就少
        small_frame = cv2.resize(frame, (0, 0), fx=0.33, fy=0.33)

        # opencv的图像是BGR格式的，而我们需要是的RGB格式的，因此需要进行一个转换。
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # 根据encoding来判断是不是同一个人，是就输出true，不是为flase
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            # 此处可能识别多张脸
            for face_encoding in face_encodings:
                # 默认为unknown, match人脸

                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.48)
                # 阈值太低容易造成无法成功识别人脸，太高容易造成人脸识别混淆 默认阈值tolerance为0.6
                # print(matches)
                name = "Unknown"

                # if match[0]:
                #     name = "michong"
                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                face_names.append(name)
            print(face_names)

        process_this_frame = not process_this_frame

        # 将捕捉到的人脸显示出来
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            # 由于我们检测到的帧被缩放到1/4大小，所以要缩小面位置
            top *= 3
            right *= 3
            bottom *= 3
            left *= 3

            # 矩形框
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # 引入ft2中的字体
            # 加上标签
            cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

            # frame = ft.draw_text(frame,(left + 6, bottom - 6), name, 1.0, (255, 255, 255))
            # def draw_text(self, image, pos, text, text_size, text_color)
        # Display

        cv2.imshow('monitor', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
'''

