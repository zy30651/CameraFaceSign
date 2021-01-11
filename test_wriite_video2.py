import cv2
import time

# cams = [{'cam_name': '摄像头1', "ip": '192.168.8.212', "username": 'admin', 'password': 'LEWMHE'},
        # {'cam_name': '摄像头2', "ip": '192.168.8.216', "username": 'admin', 'password': 'ADTVKL'}]
# url = "rtsp://admin:ADTVKL@192.168.8.216:554"
      # "# /h264/ch1/main/av_stream"
url = "rtsp://admin:CLSMKY@192.168.8.214:554"
      # "/h264/ch1/main/av_stream"
# rstp://admin:LEWMHE@192.168.8.212:554/h264/ch1/main/av_stream
# rstp://admin:ADTVKL@192.168.8.216:554/h264/ch1/main/av_stream
cap = cv2.VideoCapture(url)

# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
width = int(cap.get(3))
height = int(cap.get(4))
# out = cv2.VideoWriter('output.mp4', fourcc, 10.0, (width, height))
start_time = time.time()
time_set = 200
while(cap.isOpened()):
    t1 = time.time() - start_time
    ret, frame = cap.read()
    if ret is True:
        # out.write(frame)
        cv2.imshow('monitor', frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')) | (t1 > time_set):
            break
    else:
        break

cap.release()
# out.release()
cv2.destroyAllWindows()

