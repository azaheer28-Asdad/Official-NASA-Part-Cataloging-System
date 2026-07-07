import numpy as np
import cv2
import os
from paddleocr import PaddleOCR
import pygame
import time
import pandas as pd
import csv
import re


BOX_NUMBER = 1

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

ocr = PaddleOCR(use_textline_orientation=True, lang='en', device="gpu:0")

while True:
    ret, frame = cap.read()

    cv2.imshow("frame", frame)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    key = cv2.waitKey(1)
    
    if key == ord(' '):
        cv2.imwrite("label.jpg", frame)
        cv2.imshow("captured", frame)

        result = ocr.predict("label.jpg")
        result = result[0]['rec_texts']

        print(result)

        pattern = re.compile(r"\b[A-Z0-9]{8,19}[A-Z]\b")

        possible_parts = [word for word in result if pattern.match(word)]

        print(possible_parts)



    if key == ord('q'):
        break

    '''ends with capital letter, could be 9 to 20 digits, and no spaces'''