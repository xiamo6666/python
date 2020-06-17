import ast
import time
import threading as thread
from ws4py.client.threadedclient import WebSocketClient
import pymysql
import re


class CG_Client(WebSocketClient):

    def opened(self):
        req = '["{\\"_event\\":\\"bulk-subscribe\\",\\"tzID\\":28,\\"message\\":\\"pid-2124:%%pid-4:%%cmt-6-5-1\\"}"] '
        self.send(req)

    def closed(self, code, reason=None):
        # print("Closed down", code, reason)
        print("Closed down")

    def received_message(self, resp):
        resps = str(resp)
        if resps.__len__() != 46 and resps.__len__() > 100:
            msg = re.findall('(?<=::)\{?.*\d\}', resps.replace('\\', '').replace('"', "'"))[0]
            lists = ast.literal_eval(str(msg))
            # cursor = comm.cursor()
            type_name = '美/欧'
            last_numeric = lists.get('last_numeric')
            if lists.get('pid') == '4':
                last_numeric = float(last_numeric)
                type_name = '美/瑞'
            print(lists)
            # cursor.executemany(
            #     'insert into test1(`time`,`numeric`,`type`,`type_name`) values(%s,%s,%s,%s);',
            #     [(datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()) + " " + lists.get('time'),
            #                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=8),
            #       last_numeric,
            #       lists.get('pid'),
            #       type_name)])
            # comm.commit()

    def test(self):
        print(thread.current_thread().getName())
        time1 = time.time()
        while True:
            time2 = time.time()
            if 10 < (time2 - time1):
                try:
                    self.send('["{\\"_event\\":\\"heartbeat\\",\\"data\\":\\"h\\"}"]')
                except BaseException:
                    self.send('["{\\"_event\\":\\"heartbeat\\",\\"data\\":\\"h\\"}"]')
                time1 = time2
                time.sleep(5)


if __name__ == '__main__':
    ws = None

    comm = pymysql.connect(host='10.10.11.189', port=3338, user='root', password='123456', db='test2')
    count = 0
    while True:
        try:
            ws = CG_Client('wss://stream198.forexpros.com/echo/095/98pc6s0i/websocket')
            print("Start contenting...")
            ws.connect()
            ws.test()
            ws.run_forever()
        except KeyboardInterrupt:
            ws.close()
            break
        except Exception as e:
            count += 1
            print(e, "Try again %s times..." % count)
            continue
