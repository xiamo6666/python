import cv2
import numpy as np

if __name__ == '__main__':
    img = cv2.imread('/Volumes/Data/kkk/1.jpeg', 0)
    cv2.imwrite('/Volumes/Data/kkk/2.jpeg',img)
