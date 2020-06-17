# encoding: utf-8
import cv2
import numpy as np
import matplotlib.pyplot as plt
import cv2

if __name__ == '__main__':
    # f = '/Volumes/Data/kkk/DJI_0688.JPG'
    # fd = open(f, 'rb')
    # d = str(fd.read())
    # xmp_start = d.find('<x:xmpmeta')
    # xmp_end = d.find('</x:xmpmeta')
    # xmp_str = d[xmp_start:xmp_end + 12]
    # print(xmp_str)
    # img = cv2.imread("/Volumes/Data/kkk/2.jpg")
    img = np.random.randint(255, size=[3, 3])
    # retval, dst = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
    # dst = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 5)
    # cv2.imshow("test", img//96*96)
    # x, y, z = img.shape
    # for i in range(50000):
    #     x1 = np.random.randint(0, x)
    #     y1 = np.random.randint(0, y)
    #     img[x1, y1, :] = 255
    # img = cv2.imwrite("/Volumes/Data/kkk/2.jpg", img)
    # dist = cv2.medianBlur(img, 3)

    # dist = cv2.medianBlur(img, 3)
    # cv2.imshow("test", dist)
    # cv2.waitKey(0)
    # print(img)
    y = np.arange(5).repeat(5).reshape(5, -1)
    x = np.tile(np.arange(5), (5, 1))
    y = np.round(y / 2).astype(np.int)
    # x = np.round(x / 1.5).astype(np.int)
    # print(img)
    # print(img[y, x].astype(np.uint8))
    # print(x)
    print(y)
