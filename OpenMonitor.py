# encoding: utf-8
import cv2
import redis
import subprocess as sp
import time
import threading as thread
import logging
import multiprocessing as mp

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s----%(message)s')
log = logging.getLogger()
monitor_guard_thread = {}
monitor_dict = {}


class MonitorControl:

    def __init__(self, ip, rtmp_url):
        self.process = None
        self.rascal = None
        self.monitor_dict_s = None
        self.monitor_ips_s = None
        self.ip = ip
        self.rtmp_url = rtmp_url

    def stop_process(self):
        if self.process is not None:
            while self.process.poll() is None:
                self.process.kill()

    def start_command(self):
        """
        ffmpeg 启动命令和创建子进程
        :param args:
        :return:
        """

        fps = int(self.rascal.get(cv2.CAP_PROP_FPS))
        width = int(self.rascal.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.rascal.get(cv2.CAP_PROP_FRAME_HEIGHT))
        command = ['/Users/xiamo/Documents/ffmpeg',
                   '-y',
                   '-f', 'rawvideo',
                   '-vcodec', 'rawvideo',
                   '-pix_fmt', 'bgr24',
                   '-s', "{}x{}".format(width, height),
                   '-r', str(fps),
                   '-i', '-',
                   '-c:v', 'libx264',
                   '-pix_fmt', 'yuv420p',
                   '-preset', 'ultrafast',
                   '-f', 'flv',
                   self.rtmp_url]

        self.process = sp.Popen(command, stdin=sp.PIPE, stderr=sp.STDOUT, stdout=open("process.out", "w"), bufsize=-1,
                                shell=False)

    def check_ip(self):
        """
        验证ip可达；
        创建创建读取rtsp对象
        :param ip:
        :param rtmp_url:
        :return:
        """
        status = sp.call(["ping", "-c", "5", self.ip])
        repeat_count_ = 1
        while status != 0:
            log.error("摄像头{}未激活".format(self.ip))
            status = sp.call(["ping", "-c", "5", self.ip])
            if status == 1:
                log.info("摄像头ip:{}激活成功,进入推流模式".format(self.ip))
                break
            if repeat_count_ == 3:
                print("超时退出")
                log.error("摄像头ip:{}未激活,进程已停止".format(self.ip))
                rc.srem('monitor_ips', self.ip)
                return
            repeat_count_ += 1
        self.rascal = cv2.VideoCapture('rtsp://admin:admin@{}:554/bs1'.format(self.ip))
        if self.rascal.isOpened():
            self.start_command()
            try:
                self.push_stream()
            except Exception as e2:
                print(e2)
        self.stop_process()
        rc.srem('monitor_ips', self.ip)

    def push_stream(self):
        """
        读流推流
        :return:
        """
        times = time.time()
        not_ok_count = 0
        while self.rascal.isOpened():
            ok, next_frame = self.rascal.read()  # read_latest_frame() 替代 read()
            if not ok:
                not_ok_count += 1
                if not_ok_count >= 10: break
                continue
            # 清空count数
            not_ok_count = 0
            try:
                self.process.stdin.write(next_frame)
            except Exception as ex:
                log.info("ffmpe进程推流失败，异常信息{}".format(ex))
                self.stop_process()
                break
            if int(time.time() - times) >= 10:
                log.info(self.ip + ":摄像头稳定运行中")
                times = time.time()
            if not rc.sismember('monitor_ips', self.ip):
                log.info(self.ip + ":直播结束")
                break


def monitor_thread():
    """
    守护线程
    """
    while True:
        time.sleep(0.1)
        if monitor_dict is not None and len(monitor_dict) > 0:
            for ips in list(monitor_dict):
                if not rc.sismember('monitor_ips', ips):
                    if monitor_dict[ips] is not None:
                        if monitor_guard_thread.__contains__(ips) and monitor_guard_thread[ips] == 3:
                            log.info('摄像头ip:{}守护线程保护3次完成、已经停止守护'.format(ips))
                            del monitor_guard_thread[ips]
                            try:
                                del monitor_dict[ips]
                            except Exception:
                                pass
                        else:
                            mp.Process(target=monitor_dict[ips].check_ip).start()
                            rc.sadd('monitor_ips', ips)
                            if not monitor_guard_thread.__contains__(ips):
                                monitor_guard_thread[ips] = 1
                            log.info('摄像头ip:%s守护线程保护第:%d成功' % (ips, monitor_guard_thread[ips]))
                            monitor_guard_thread[ips] += 1


if __name__ == '__main__':
    rc = redis.StrictRedis(host='127.0.0.1', port=6379, password='ebit')
    # 每次启动删除清空redis
    rc.delete('monitor_ips')
    # 启动一个守护线程
    ps = rc.pubsub()
    thread.Thread(target=monitor_thread).start()
    ps.subscribe('OpenMonitor')
    for item in ps.listen():
        if item.get('type') == 'message':
            parm_list = item.get('data').decode().strip('"').split('==')
            if parm_list.__len__() == 2:
                if parm_list[0] == 'close':
                    if monitor_dict is not None and len(monitor_dict) > 0:
                        try:
                            del monitor_dict[parm_list[1]]
                        except Exception as ex1:
                            pass
                        rc.srem("monitor_ips", parm_list[1])
                        log.info("{}:收到关闭指令".format(parm_list[1]))
                    continue
                if not rc.sismember("monitor_ips", parm_list[0]):
                    rc.sadd("monitor_ips", parm_list[0])
                    log.info('{}:收到打开指令'.format(parm_list[0]))
                    monitor_control = MonitorControl(parm_list[0], parm_list[1])
                    monitor_dict[parm_list[0]] = monitor_control
                    mp.Process(target=monitor_control.check_ip).start()
