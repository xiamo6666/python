import asyncio
import base64
import multiprocessing as mp
import websockets
import time
import cv2
import threading as thread
from wsgiref.simple_server import make_server
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from itertools import chain

server_client = []

queue = mp.Queue(maxsize=2)


async def run(websocket, path):
    while True:
        try:
            recv_str = await websocket.recv()
            print(recv_str)
            server_client.append(websocket)
        except Exception as e:
            server_client.remove(websocket)
            print(e)
            break


def read():
    retval = cv2.VideoCapture('rtsp://admin:admin@192.168.201.12:554/bs1')
    if retval.isOpened():
        while retval.isOpened():
            ok, image = retval.read()
            if ok:
                try:
                    asyncio.new_event_loop().run_until_complete(
                        send(str(base64.b64encode(cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 40])[1]),
                                 'utf-8'))
                    )
                except Exception as e:
                    print(e)


async def send(msg):
    [await ws.send(msg) for ws in list(server_client)]


#
# def write():
#     loop = asyncio.new_event_loop()
#     while True:
#         if len(server_client) > 0:
#             if queue.full():


if __name__ == '__main__':
    thread.Thread(target=read).start()
    # thread.Thread(target=write).start()
    start_server = websockets.serve(run, '10.10.11.2', 9001)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
