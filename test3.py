import datetime
import requests
import json
import cv2
import face_recognition
import time, os.path
import xlwings as xw
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
scheduler = BlockingScheduler()
videos_path = '/Users/zy/Desktop/Git/CameraFaceSign/face_video/'


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
    # 学生姓名和学生脸部特征; 目前没有的话读取的是id
    def __init__(self, name, face):
        self.name = name
        self.face = face

    def stu_desc(self):
        print(self.name)


class Cam:
    def __init__(self, cam_name, ip, username, password):
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
        "startTime": '1609827018000',
        'endTime': '1609827018000',
        # "startTime": cur_time,
        # 'endTime': cur_time
    }
    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0',
               'authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1YWM3NTI2MGU1ZGZiMGU0NzlkNzM1MGMiLC'
                                'JhdWQiOiJqYWN5LmxpdUByZW5lZS1hcnRzLmNvbSJ9.uVUBft-xbe8TL2Wev2JRa_r5mJHIVr4I5REXJdJa_VM'}
    r = requests.get(base_url + product_url, params=data, headers=headers)
    products = json.loads(r.content)
    print('len(products):%s' % (len(products)))

    app = xw.App(visible=False, add_book=True)
    for pro in products:
        # 序列号课程id、名称、开课时间、下课时间，用于添加计划任务
        base_product = Product(pro['curriculumId'], pro['curriculumId'], pro['startTime'], pro['endTime'])
        base_product.pro_desc()
        # 获取班级学生数据
        dict_student_name, dict_student_face = get_course_students(base_product.pro_id)
        # 获取当前课程的摄像头
        # cams = get_course_cams(base_product.pro_id)
        cams = [
            # {'cam_name': '摄像头1', "ip": '192.168.8.212', "username": 'admin', 'password': 'LEWMHE'},
                # {'cam_name': '摄像头2', "ip": '192.168.8.216', "username": 'admin', 'password': 'ADTVKL'},
                {'cam_name': '摄像头3', "ip": '192.168.8.214', "username": 'admin', 'password': 'CLSMKY'}]
        # 当天第二次以后再查询，需筛选重复后，再添加；但是避免添加已过期任务

        # 转换时间格式
        start_time = datetime.datetime.fromisoformat(base_product.startTime)
        end_time = datetime.datetime.fromisoformat(base_product.endTime)

        wb = create_xlsx(app, base_product.name, base_product.pro_id, base_product.startTime, dict_student_name)
        # 给每个摄像头添加计划任务；
        # 任务1：每个摄像头开始上课前1分钟开始启动，再次执行：20分钟后
        # 任务2：每个摄像头下课前5分钟启动弄个
        for cam in cams:
            cam_real = Cam(cam['cam_name'], cam['ip'], cam['username'], cam['password'])
            scheduler.add_job(
                save_cam_video,
                trigger='date',
                run_date=start_time + datetime.timedelta(seconds=2720 * 60),
                args=[cam_real.ip, cam_real.cam_name, cam_real.username, cam_real.password,
                      base_product.pro_id, base_product.pro_id]
            )
            # scheduler.add_job(
            #     save_cam_video,
            #     trigger='date',
            #     run_date=start_time + datetime.timedelta(seconds=30 * 60),
            #     args=[cam_real.ip, cam_real.cam_name, cam_real.username, cam_real.password,
            #           base_product.pro_id, base_product.pro_id]
            # )
            # scheduler.add_job(
            #     save_cam_video,
            #     trigger='date',
            #     run_date=end_time - datetime.timedelta(seconds=5 * 60),
            #     args=[cam_real.ip, cam_real.cam_name, cam_real.username, cam_real.password,
            #           base_product.pro_id, base_product.pro_id]
            # )
            scheduler.print_jobs()
            print('_'*40)

            # 添加检测人脸任务,录制视频结束5分钟后
            # 录制完视频，根据录制视频人脸识别
            # 录制视频的path
            # print('添加人脸识别任务' + '-' * 30)
            # scheduler.add_job(
            #     check_face,
            #     trigger='date',
            #     run_date=start_time + datetime.timedelta(seconds=2700 * 60),
            #     args=[base_product.pro_id, cam_real.cam_name, dict_student_face, dict_student_name]
            # )
            # scheduler.add_job(
            #     check_face,
            #     trigger='date',
            #     run_date=start_time + datetime.timedelta(seconds=35 * 60),
            #     args=[base_product.pro_id, cam_real.cam_name, dict_student_name, dict_student_face]
            # )
            # scheduler.add_job(
            #     check_face,
            #     trigger='date',
            #     run_date=end_time - datetime.timedelta(seconds=5 * 60),
            #     args=[base_product.pro_id, cam_real.cam_name, dict_student_name, dict_student_face]
            # )
            scheduler.print_jobs()
            print('-'*40)

        # break 是临时测试录制视频使用，只录制一个课程的视频；
        wb.close()
        app.quit()
        break

        # 202101051715_5f520b4c23c5b0e45041cb1c_摄像头1

        # 202101051710_5f520b4c23c5b0e45041cb1c_摄像头1
        # 202101051710_5f520b4c23c5b0e45041cb1c_摄像头2


# 目前把每个录好的视频保存完成
#     1：展示文件列表所有视频mp4文件
#     2：视频人脸识别
#         怎么把视频文件和某个班级关联；
#         视频文件名称：班级id+上课时间
#         此外：保存视频的时候最好每天记录1个Excel：
#             当天时间.excel：班级名称、班级ID、上课时间、班级学生[]
#     3：识别后发送请求
#     4.1：发送成功删除视频
#     4.2：如果不删除，移动视频到另外一个目录；
def check_face(base_product_id, cam_name, dict_student_face, dict_student_name):
    """
    根据传入的视频、学生人脸信息、学生名称检测人脸
    """
    # path = '%s%s_%s_%s.mp4' % (videos_path, (datetime.datetime.now()-datetime.timedelta(seconds=2 * 60)).strftime("%Y%m%d%H%M"),
    #                            base_product_id, cam_name)
    path = '%s%s_%s_%s.mp4' % (videos_path, "202101061430", "5f520b4c23c5b0e45041cb1c", cam_name)
    print('人脸识别任务：time: %s Task for %s ' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), path))

    cam = cv2.VideoCapture(path)

    time_count = 0
    while cam.isOpened():
        # 读取摄像头画面
        ret, frame = cam.read()
        if not ret:
            # 等同于 if ret is not none
            print('%s 视频读取不到' % path)
            break

        # 改变摄像头图像的大小，图像小，所做的计算就少
        small_frame = cv2.resize(frame, (0, 0), fx=0.33, fy=0.33)
        # opencv的图像是BGR格式的，而我们需要是的RGB格式的，因此需要进行一个转换。
        rgb_small_frame = small_frame[:, :, ::-1]
        if True:
            # 根据encoding来判断是不是同一个人，是就输出true，不是为flase
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            # 此处可能识别多张脸

            # !!!打印下：是否检测到人脸。然后在看是否是否正确
            # ufunc 'subtract' did not contain a loop with signature matching types
            # (dtype('<U32'), dtype('<U32')) -> dtype('<U32')
            for face_encoding in face_encodings:
                # 默认为unknown, match人脸
                # 此处是已经检测出来的人脸，需要多数组比对

                matches = face_recognition.compare_faces(dict_student_face, face_encoding, tolerance=0.48)
                # 阈值太低容易造成无法成功识别人脸，太高容易造成人脸识别混淆 默认阈值tolerance为0.6
                name = "Unknown"
                if True in matches:
                    first_match_index = matches.index(True)
                    name = dict_student_name[first_match_index]

                face_names.append(name)
            # 检测出来所有比对上的人脸
            time_count = time_count + 1
            print('time----face_names: %s', (time_count, face_names))


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
    print('学员考勤名单')

    dict_students = []
    dict_students_face = []
    # 测试数据
    dict_students.append('张扬')
    dict_students_face.append([-0.15581109 ,0.05472353 ,0.07025001 ,-0.03478277 ,-0.1225464  ,-0.067148
 ,-0.04389102 ,-0.1788922  ,0.12924638 ,-0.13846681 ,0.19092084 ,-0.08122106
 ,-0.17738664 ,-0.07762139 ,-0.04714717 ,0.15356822 ,-0.11676171 ,-0.17608058
 ,-0.04891798 ,-0.00277308 ,0.08459656 ,-0.02672651 ,0.02233794 ,0.02675597
 ,-0.12284711 ,-0.32423082 ,-0.06693836 ,-0.03330912 ,0.0370509  ,-0.00095372
 ,-0.037985   ,0.08953559 ,-0.24225864 ,-0.06567553 ,0.00651651 ,0.07766151
 ,0.0249553  ,-0.04690952 ,0.16115598 ,-0.03531392 ,-0.2754212  ,-0.00158843
 ,0.048085   ,0.2217226  ,0.1728704  ,0.03510183 ,0.03582369 ,-0.14219961
 ,0.13848777 ,-0.15398261 ,0.00651219 ,0.13421679 ,0.03736773 ,-0.00163173
 ,0.00824203 ,-0.15828934 ,0.03566626 ,0.09645136 ,-0.10309847 ,0.03537229
 ,0.10742516 ,-0.05479398 ,-0.03489756 ,-0.12615083 ,0.22970793 ,0.03928682
 ,-0.10161316 ,-0.152999   ,0.14209804 ,-0.11457364 ,-0.04976563 ,0.04947362
 ,-0.17679501 ,-0.16622965 ,-0.32321617 ,-0.01142678 ,0.39683309 ,0.09516249
 ,-0.18623924 ,0.08498649 ,-0.03429099 ,0.0539407  ,0.13747117 ,0.1810905
 ,-0.00931429 ,0.06738873 ,-0.070461   ,-0.02259749 ,0.23196349 ,-0.02541499
 ,-0.04351148 ,0.21511103 ,0.00179936 ,0.04083151 ,0.01450604 ,0.00452439
 ,-0.08403969 ,0.00656004 ,-0.15078424 ,-0.01985493 ,0.02659354 ,-0.00236686
 ,0.00856806 ,0.13737226 ,-0.14282063 ,0.12214312 ,-0.02238862 ,0.09799347
 ,0.00912961 ,-0.0087376  ,-0.05622048 ,-0.06681822 ,0.05815097 ,-0.18055841
 ,0.16614303 ,0.15774544 ,0.07016143 ,0.11707322 ,0.14276291 ,0.07293998
 ,0.01899813 ,0.08238558 ,-0.1801544  ,-0.03088881 ,0.11364438 ,-0.07084202
 ,0.0956964  ,0.0301157 ])

    # for stu in students:
    #     # 打印目前查到的课程，添加计划任务stu['schoolStudent']
    #     base_stu = Student(stu['schoolStudent']['studentName'], stu['schoolStudent']['id'])
    #     # 打印目前查到的课程，添加计划任务
    #     print('学生姓名：%s 学生Face：%s' % (base_stu.name, base_stu.face))
    #     # 当前记录所有学生的脸部数据； 用于启动班级人脸考勤后的人脸对比；
    #     # known_face_encodings.append(base_stu.face)
    #     # known_face_names.append(base_stu.name)
    #     dict_students.append(base_stu.name)
    # print('-' * 20)
    print(dict_students, dict_students_face)
    return dict_students, dict_students_face


def save_cam_video(ip, cam_name, username, password, pro_name, base_product_id):
    print('保存视频任务：Task for %s time: %s' % (cam_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    url = 'rtsp://%s:%s@%s:554/h264/ch1/main/av_stream' % (username, password, ip)
    # url = "rtsp://admin:ADTVKL@192.168.8.216:554/h264/ch1/main/av_stream"
    cap = cv2.VideoCapture(url)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    width = int(cap.get(3))
    height = int(cap.get(4))
    path = '%s%s_%s_%s.mp4' % (videos_path, datetime.datetime.now().strftime("%Y%m%d%H%M"),
                               base_product_id, cam_name)
    print(path)
    out = cv2.VideoWriter(path, fourcc, 10.0, (width, height))
    start_time = time.time()
    time_set = 90
    while cap.isOpened():
        t1 = time.time() - start_time
        ret, frame = cap.read()
        if ret is True:
            out.write(frame)
            if (cv2.waitKey(1) & 0xFF == ord('q')) | (t1 > time_set):
                break
        else:
            print('%s %s 摄像头读取不到' % (pro_name, ip))
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()


# 保存视频的时候最好每天记录1个Excel：
# 当天时间.excel：班级名称、班级ID、上课时间、班级学生[]
# 每天新增一个excel，第一次是新增，第二次是追加。
def create_xlsx(app, classname, class_id, start_time, stus):
    now_time = datetime.datetime.now().strftime("%Y-%m-%d ")
    path = ('%s.xlsx' % now_time)

    if os.path.isfile(path):
        wb = app.books.open(path)
        sht = wb.sheets['Sheet1']  # 实例化工作表
        row = 'a%s' % (sht.used_range.shape[0] + 1)
        str_students = ''

        for stu in stus:
            str_students = str_students + str(stu)
        sht.range(row).value = [classname, class_id, start_time, str_students]
    else:
        wb = app.books.add()
        sht = wb.sheets['Sheet1']  # 实例化工作表
        sht.range('a1').value = [classname, class_id, start_time, stus]

    wb.save(path)  # 保存
    return wb


def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')


# 启动任务监听，监听成功、失败-真实启动，每日早上7点半执行get_course_for_day
# scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
# scheduler.add_job(
#     get_course_for_day,
#     trigger='cron',
#     minute=30,
#     hour=7
# )
# scheduler.print_jobs()
# scheduler.start()

# 临时启动 执行一次 之后启动定时任务
get_course_for_day()
# scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
# scheduler.print_jobs()
scheduler.start()

