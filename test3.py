# 2：系统根据上课时间、下课时间，前后几分钟，操作摄像头拍照
# 	2.1每小时拉取服务器今天所上课程；
# 	2.2根据课程找到班级所在摄像头；
# 	2.3设置定时任务，在上课10分钟内，多次调用摄像头人脸识别
# 	2.4人脸识别成功后，
# 		打印识别人员名单，识别人员数量，
# 		发送签到命令到服务器，给识别成功人员登记考勤
# 		手机小程序，推送签到成功给手机端(顾问、老师、家长)
import datetime

import pytz
import requests
import json
import cv2
import face_recognition
import time
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED
# 鉴于人脸识别需要大量计算，此处使用多进程
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
scheduler = BlockingScheduler()


def get_beijing_time():
    hea = {'User-Agent': 'Mozilla/5.0'}
    url = r'http://time1909.beijing-time.org/time.asp'
    r = requests.get(url=url, headers=hea)
    if r.status_code == 200:
        result = r.text
        data = result.split(";")
        year = data[1][len("nyear") + 3: len(data[1])]
        month = data[2][len("nmonth") + 3: len(data[2])]
        day = data[3][len("nday") + 3: len(data[3])]
        time_str = "%s-%s-%s" % (year, month, day)
        l_time = time.strptime(time_str, "%Y-%m-%d")
        time_stamp = int(time.mktime(l_time)) * 1000
        print('当前时间为：%s, 时间戳为;%s'% (time_str, time_stamp))
        return time_stamp


class Student:
    def __init__(self, name, face):
        self.name = name
        self.face = face

    def stu_desc(self):
        print(self.name)


class Cam:
    def __init__(self, cam_name, ip, username, password, port=554):
        self.cam_name = cam_name
        self.ip = ip
        self.username = username
        self.password = password

    def cam_desc(self):
        print("cam_name: %s, cam_ip: %s, username: %s, username:%s", self.cam_name, self.ip, self.username, self.password)


class Product:
    def __init__(self, pro_id, name, start_time, end_time, cams=None):
        self.name = name
        self.pro_id = pro_id
        self.startTime = start_time
        self.endTime = end_time
        self.cams = cams

    def pro_desc(self):
        print("pro_id: %s, name: %s, time: %s-%s" % (self.pro_id, self.name, self.startTime, self.endTime))
        # for cam in self.cams:
        #     cam.cam_desc()


# requests
base_url = 'https://ssl.renee-arts.com/sps'
# 日历模块 - 指定日期课程列表
product_url = '/api/v1/schedule/getByProductBaseIdAndStartEnd'
# 班级学员列表 - 查询班级学员信息，包含人脸数据
# product_students_url = '/api/v1/student/listByProductBaseId'
product_students_url = '/api/v1/student/listByProductBaseIdToteacher'

array_products = []
# 定时任务
task_list = []


def get_course_for_day():
    cur_time = get_beijing_time()
    data = {
        'orgId': '7210',
        "customer_id": 'YIJIE_2017_FAKE',
        "startTime": '1607097751000',
        'endTime': '1607097751000',
        # "startTime": cur_time,
        # 'endTime': cur_time
    }
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0',
               'authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1YWM3NTI2MGU1ZGZiMGU0NzlkNzM1MGMiLC'
                                'JhdWQiOiJqYWN5LmxpdUByZW5lZS1hcnRzLmNvbSJ9.uVUBft-xbe8TL2Wev2JRa_r5mJHIVr4I5REXJdJa_VM'}
    r = requests.get(base_url + product_url, params=data, headers=headers)
    products = json.loads(r.content)
    for pro in products:
        # 序列号课程id、名称、开课时间、下课时间，用于添加计划任务
        base_product = Product(pro['curriculumId'], pro['curriculumId'], pro['startTime'], pro['endTime'])
        base_product.pro_desc()
        # 获取班级学生数据
        get_course_students(base_product.pro_id)
        # 获取当前课程的摄像头
        # get_course_cams(base_product.pro_id)
        # 当天第二次以后再查询，需筛选重复后，再添加；但是避免添加已过期任务

        # 转换时间格式
        start_time = datetime.datetime.fromisoformat(base_product.startTime)
        end_time = datetime.datetime.fromisoformat(base_product.endTime)
        # 给每个摄像头添加计划任务；
        # 任务1：每个摄像头开始上课前1分钟开始启动，再次执行：20分钟后
        # 任务2：每个摄像头下课前5分钟启动弄个
        cams = ['1', '2']
        for cam in cams:
            cam = Cam('摄像头1', '192.168.1.1', 'admin', '111111')
            scheduler.add_job(
                check_face_sign,
                trigger='date',
                run_date=start_time - datetime.timedelta(seconds=1 * 60),
                next_run_time=start_time + datetime.timedelta(seconds=20 * 60),
                args=[cam.ip, cam.username, cam.password, pro['curriculumId']]
            )
            scheduler.add_job(
                check_face_sign,
                trigger='date',
                run_date=end_time - datetime.timedelta(seconds=5 * 60),
                args=[cam.ip, cam.username, cam.password, pro['curriculumId']]
            )
            scheduler.print_jobs()
            print('_'*20)


# 存储学生姓名
known_face_names = []
# 存储人脸数据
known_face_encodings = []


def get_course_cams(product_id):
    pass


def get_course_students(product_id):
    data = {
        'productBaseId': product_id,
        "customer_id": 'YIJIE_2017_FAKE',
    }
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0',
               'authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1YWM3NTI2MGU1ZGZiMGU0NzlkNzM1MGMiLC'
                                'JhdWQiOiJqYWN5LmxpdUByZW5lZS1hcnRzLmNvbSJ9.uVUBft-xbe8TL2Wev2JRa_r5mJHIVr4I5REXJdJa_VM'}
    r = requests.get(base_url + product_students_url, params=data, headers=headers)
    students = json.loads(r.content)
    print(students)
    for stu in students:
        # 打印目前查到的课程，添加计划任务stu['schoolStudent']
        base_stu = Student(stu['schoolStudent']['studentName'], stu['schoolStudent']['id'])
        # 打印目前查到的课程，添加计划任务
        print('学员考勤名单')
        print('学生姓名：%s 学生Face：%s' % (base_stu.name, base_stu.face))
        print('-'*20)
        # 当前记录所有学生的脸部数据； 用于启动班级人脸考勤后的人脸对比；
        known_face_encodings.append(base_stu.face)
        known_face_names.append(base_stu.name)


face_locations = []
face_encodings = []
face_names = []
process_this_frame = True


# 启动摄像头，录像并做人脸识别，成功后考勤登记
def check_face_sign(ip, username, password, pro_name):

    print('Task for %s' % pro_name)
    source = "×××××"  # 摄像头的rtsp地址
    # cam = cv2.VideoCapture(source)
    # 本机摄像头
    cam = cv2.VideoCapture(0)

    while (cam.isOpened()):
        # 读取摄像头画面
        ret, frame = cam.read()
        print(ret)
        if not ret:
            # 等同于 if ret is not none
            print('%s %s 摄像头读取不到' % (pro_name, ip))
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


from os import listdir


def test():
    starttime = time.time()
    print('starttime: %s' % starttime)
    # 摄像头的rtsp地址
    source = "rtsp://[username]:[password]@[100.29.111.29]:[554]/[h264]/[ch1]/[main]/av_stream"

    # 本机摄像头
    cam = cv2.VideoCapture(0);
    # cam = cv2.VideoCapture(source)

    # 已知人脸图片文件夹 注意 如果会员图片后缀不是jpg 需要进行修改
    filepath = './face_photos'
    filename_list = listdir(filepath)
    known_face_names = []
    known_face_encodings = []
    a = 0

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

    while (cam.isOpened()):
        # 读取摄像头画面
        ret, frame = cam.read()
        if not ret:
            # 等同于 if ret is not none
            break

        # 改变摄像头图像的大小，图像小，所做的计算就少
        small_frame = cv2.resize(frame, (0, 0), fx=0.33, fy=0.33)

        # opencv的图像是BGR格式的，而我们需要是的RGB格式的，因此需要进行一个转换。
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if process_this_frame:
            # 根据encoding来判断是不是同一个人，是就输出true，不是为flase
            face_locations = face_recognition.face_locations(rgb_small_frame)
            print(face_locations)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # 默认为unknown
                print(face_encoding.shape)
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
        endtime = time.time()
        print('endTime: %s' % endtime)
        if endtime - starttime > 1*10:
            cam.release()
            cv2.destroyAllWindows()

        cv2.imshow('monitor', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break


def aps_test(x):
    print('_'*10)
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), x)


def test2():
    starttime = time.time()
    file_name = str(starttime)+'.txt'
    print('file_name: %s' % file_name)
    f = open(file_name, 'w')
    f.close()


def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')

# 启动任务监听，监听成功、失败
# scheduler = BlockingScheduler()
# scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
# scheduler.add_job(
#     get_course_for_day,
#     trigger='cron',
#     minute=30,
#     hour=7
# )
# scheduler.print_jobs()
# scheduler.start()

# 临时启动
# get_course_for_day()


# scheduler = BlockingScheduler()
# scheduler.configure(executors=executors, job_defaults=job_defaults)
# scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
# scheduler.add_job(
#     func=test2,
#     trigger='interval',
#     minutes=1
# )
# scheduler.print_jobs()
# scheduler.start()


