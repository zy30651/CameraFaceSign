import time
import cv2
import queue
import time
import threading
q = queue.Queue()

url = "rtsp://admin:ADTVKL@192.168.8.216:554/h264/ch1/main/av_stream"
cap = cv2.VideoCapture(url)
# cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc1 = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc1, 10.0, ((int(cap.get(3)),int(cap.get(4)))))
start_time = time.time()
time_set = 300  # 计时设定时间
while(cap.isOpened()):
    t1 = time.time() - start_time  # 计时时间间隔
    print(int(t1))
    ret, frame = cap.read()

    if ret is True:
        # write the flipped frame
        out.write(frame)

        cv2.imshow('frame', frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')) | (t1 > time_set):
            break
    else:
        break

# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()

