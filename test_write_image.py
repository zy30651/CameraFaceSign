import time
import cv2
url = "rtsp://admin:ADTVKL@192.168.8.216:554/h264/ch1/main/av_stream"


# img = cv.imread('test.jpg',0)  # 灰度模式读取图片
# cv.imshow('image',img)  # 显示图片，窗口名称为'image'
# k = cv.waitKey(0)  # 无限等待一个键击，将此键击存在k变量中
# if k == 27:         # 27代表esc，可以查看ascii码表
#     cv.destroyAllWindows()  # 退出窗口
# elif k == ord('s'): # 等待s键，ord函数可以将字符串转换为ascii码
#     cv.imwrite('test.png',img)  # 写入图片
#     cv.destroyAllWindows()  # 关闭窗口


def Receive():
    print("start Reveive")
    cap = cv2.VideoCapture(url)
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            for index in range(100):
                cv2.imshow('frame', frame)
                cv2.imwrite('%d.jpg' % index, frame)
                print('%d.jpg' % index)
                time.sleep(1)
                ret, frame = cap.read()
                index += 1
                if (cv2.waitKey(5) & 0xFF) == ord('q'):
                    break


Receive()
cv2.release()
cv2.destroyAllWindows()