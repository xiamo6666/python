# encoding: utf-8
import cv2
import redis
import subprocess as sp
import time
import threading as thread
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s-ThreadName: %(threadName)s-pid:%(process)d-%(message)s')
log = logging.getLogger()


class MonitorControl:

    def __init__(self):
        self.process = None
        self.rascal = None
        self.ip = None
        self.rtmp_url = None

    def stop_thread(self):
        """
        停止线程及其子进程
        """
        try:
            monitor_ips.remove(self.ip)
        except Exception:
            print(monitor_ips)

    def stop_process(self):
        log.info("ffmpeg进程结束中")
        while self.process.poll() is None:
            self.process.kill()
        log.info("ffmpeg进程结束完成")

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

        th1 = thread.Thread(target=self.monitor_process)
        th1.start()

    def check_ip(self, ip, rtmp_url):
        """
        验证ip可达；
        创建创建读取rtsp对象
        :param ip:
        :param rtmp_url:
        :return:
        """
        status = sp.call(["ping", "-c", "2", ip])
        self.ip = ip
        self.rtmp_url = rtmp_url
        repeat_count_ = 0
        while status != 0:
            log.info("摄像头{}未激活".format(ip))
            status = sp.call(["ping", "-c", "2", ip])
            if status == 0:
                log.info("摄像头已激活,进入推流模式")
                break
            if repeat_count_ == 3:
                print("超时退出")
                log.info("摄像头:{}未激活,已重试3次".format(ip))
                break
            repeat_count_ += 1
        self.rascal = cv2.VideoCapture('rtsp://admin:admin@{}:554/bs1'.format(ip))
        if self.rascal.isOpened():
            self.start_command()
            try:
                self.push_stream()
            except Exception as e2:
                print(e2)
            try:
                self.stop_process()
            except Exception as e3:
                print(e3)
        self.stop_thread()

    def monitor_process(self):
        log.info("开始进行ffmpeg进程进行监控")
        show_time = time.time()
        while self.process.poll() is None:
            if int(time.time() - show_time) >= 10:
                log.info("ffmpe推流进程正在稳定运行中")
                show_time = time.time()
        log.info("ffmpe推流进程已经正常结束")

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
                if cv2.waitKey(100) & 0xFF == ord('q'): break
                not_ok_count += 1
                if not_ok_count >= 10: break
                continue
            # 清空count数
            not_ok_count = 0
            try:
                self.process.stdin.write(next_frame)
            except Exception as ex:
                log.info("ffmpe进程推流失败，异常信息{}".format(ex))
                if monitor_dict.get(self.ip) is not None:
                    self.stop_process()
                    self.start_command()
            if int(time.time() - times) >= 10:
                log.info("OpenCV取流线程进行稳定运行中")
                times = time.time()
            if monitor_dict.get(self.ip) is None:
                log.info("收到关闭指令，OpenCV线程关闭成功")
                break


def monitor_thread(th1, ip, push_url):
    push_stream = th1
    retry_count = 0
    """
    守护线程 守护5次
    """
    while retry_count < 5:
        time2 = time.time()
        while push_stream.is_alive():
            if int(time.time() - time2) > 120 and retry_count > 0:
                retry_count = 0
                log.info("工作线程持续工作120秒以上，清空连接次数")
        if monitor_dict.get(ip) is None:
            log.info("收到关闭指令，守护进程结束")
            break
        log.info("守护线程保护成功")
        monitor_ips.append(ip)
        monitor_control_retry = MonitorControl()
        thread_retry = thread.Thread(target=monitor_control_retry.check_ip, args=(ip, push_url))
        thread_retry.start()
        monitor_dict[ip] = monitor_control_retry
        push_stream = thread_retry
        retry_count += 1
    if retry_count >= 5:
        log.info("守护线程连续5次守护失败，请检查摄像头是否休眠")
        monitor_ips.remove(ip)


if __name__ == '__main__':
    rc = redis.StrictRedis(host='10.10.11.189', port=6379, password='ebit')
    ps = rc.pubsub()
    monitor_ips = []
    monitor_dict = {}
    ps.subscribe('OpenMonitor')
    for item in ps.listen():
        if item.get('type') == 'message':
            parm_list = item.get('data').decode().strip('"').split('==')
            if parm_list.__len__() == 2:
                if parm_list[0] == 'close':
                    monitor_device = monitor_dict.get(parm_list[1])
                    if monitor_device is not None:
                        del monitor_dict[parm_list[1]]
                        continue
                if not set(monitor_ips).__contains__(parm_list[0]):
                    monitor_ips.append(parm_list[0])
                    monitor_control = MonitorControl()
                    th = thread.Thread(target=monitor_control.check_ip, args=(parm_list[0], parm_list[1]))
                    th.start()
                    monitor_dict[parm_list[0]] = monitor_control
                    # 加入守护线程
                    thread.Thread(target=monitor_thread, args=(th, parm_list[0], parm_list[1])).start()
