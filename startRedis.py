# encoding: utf-8
import redis
import threading as thread
import cv2
from skimage.measure import compare_ssim
from fdfs_client.client import Fdfs_client, get_tracker_conf
import time
from RTSCapture import RTSCapture
import logging
import subprocess as sp

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s-ThreadName: %(threadName)s-pid:%(process)d-%(message)s')
log = logging.getLogger()


class Photograph:
    def __init__(self, ip, plan_id, number, rcs):
        self.ip = ip
        self.plan_id = plan_id
        self.number = number
        self.redis = rcs

    def redisControl(self, frame):
        test = Fdfs_client(get_tracker_conf('./client.conf'))
        real, buff = cv2.imencode('.jpg', frame)
        ret_upload = test.upload_appender_by_buffer(buff.tobytes(), 'jpg')
        self.redis.hset("PresetPosition", '"{}:{}"'.format(self.plan_id, self.number),
                        '"{}"'.format(ret_upload.get("Remote file_id").decode()))
        log.info("采集编号:[{}]-采集过程id:[{}]-拍照成功".format(self.plan_id, self.number))

    def check_ip(self):
        status = sp.call(["ping", "-c", "2", self.ip])
        repeat_count_ = 0
        while status != 0:
            log.info("摄像头{}未激活".format(self.ip))
            status = sp.call(["ping", "-c", "2", self.ip])
            if status == 0:
                break
            if repeat_count_ == 10:
                log.info("摄像头:{}未激活,已重试10次".format(self.ip))
                break
            repeat_count_ += 1
        if status == 0:
            log.info("摄像头激活进入拍照模式")
            self.control()
        else:
            log.info("摄像头未激活")

    def control(self):
        rascal = RTSCapture.create('rtsp://admin:admin@{}:554/bs1'.format(self.ip))
        rascal.start_read()  # 启动子线程并改变 read_latest_frame 的指向
        start_time = time.time()

        last_frame = None
        frame = None
        num_count = 0
        while rascal.isStarted():
            ok, next_frame = rascal.read_latest_frame()  # read_latest_frame() 替代 read()
            if not ok:
                if cv2.waitKey(100) & 0xFF == ord('q'): break
                continue

            # 帧处理代码写这里
            end_time = time.time()
            if 2 <= int(end_time - start_time):
                if last_frame is not None and frame is not None:
                    one_score, diff = compare_ssim(cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY),
                                                   cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                                   full=True)
                    tow_score, diff = compare_ssim(cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY),
                                                   cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY),
                                                   full=True)
                    print(one_score)
                    print(tow_score)
                    if one_score > 0.90 and tow_score < 0.85:
                        self.redisControl(next_frame)
                        break
                    """
                    如果超过循环多次没有匹配就截图
                    """
                    if num_count == 20:
                        self.redisControl(next_frame)
                        break
                start_time = end_time
                last_frame = frame
                frame = next_frame
                num_count += 1
                print(num_count)
            cv2.waitKey(1)
        rascal.stop_read()
        rascal.release()
        self.redis.publish('onlineMonitorMsg', '{}:{}'.format(self.plan_id, self.number))


if __name__ == '__main__':
    rc = redis.StrictRedis(host='10.10.11.104', port=6379, password='ebit')

    ps = rc.pubsub()
    ps.subscribe('onlineMonitor')
    for item in ps.listen():
        if item.get('type') == 'message':
            parm_list = item.get('data').decode().strip('"').split(':')
            if parm_list.__len__() == 3:
                photograph = Photograph(parm_list[0], parm_list[1], parm_list[2], rc)
                tr = thread.Thread(target=photograph.check_ip)
                tr.start()
