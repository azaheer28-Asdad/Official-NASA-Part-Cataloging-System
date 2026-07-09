import os
# Force disable the conflicting PIR engine elements and optimization libraries
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

import numpy as np
import cv2
from paddleocr import PaddleOCR
import pygame
import time
import pandas as pd
import csv
import re
import tkinter as tk
import requests


BOX_NUMBER = 0


def buttons(possible_parts, title, button_thick, next_label_length, loc):
    tk.Label(root, text=title).place(relx=0, rely=0+next_label_length, relheight=button_thick/2)
    button = tk.Button(root, text="None", command= lambda: entry.insert(0,"None")).place(relx=0.17, rely=0+next_label_length, relwidth=0.15, relheight=button_thick/2)
    tk.Label(root, text="Edit:").place(relx=0.30, rely=0+next_label_length, relheight=button_thick/2)
    edited = tk.Entry(root, width=50).place(relx=0.35, rely=0+next_label_length, relheight=button_thick/2)
    if edited:
        entry.insert(loc,edited)

    if len(possible_parts) == 1: 
        button = tk.Button(root, text=possible_parts[0], command= lambda: entry.insert(loc,(possible_parts[0]))).place(relx=0.10, rely=0.04+next_label_length, relwidth=0.8, relheight=button_thick)
    elif len(possible_parts) == 2:
        button = tk.Button(root, text=possible_parts[0], command= lambda: entry.insert(loc,(possible_parts[0]))).place(relx=0, rely=0.04+next_label_length, relwidth=0.5, relheight=button_thick)
        button = tk.Button(root, text=possible_parts[1], command= lambda: entry.insert(loc,(possible_parts[1]))).place(relx=0.5, rely=0.04+next_label_length, relwidth=0.5, relheight=button_thick)
        
    elif len(possible_parts) == 3:
        button = tk.Button(root, text=possible_parts[0], command= lambda: entry.insert(loc,(possible_parts[0]))).place(relx=0, rely=0.04+next_label_length, relwidth=0.333, relheight=button_thick)
        button = tk.Button(root, text=possible_parts[1], command= lambda: entry.insert(loc,(possible_parts[1]))).place(relx=0.333, rely=0.04+next_label_length, relwidth=0.333, relheight=button_thick)
        button = tk.Button(root, text=possible_parts[2], command= lambda: entry.insert(loc,(possible_parts[2]))).place(relx=0.666, rely=0.04+next_label_length, relwidth=0.333, relheight=button_thick)



csv_file_name = f"Box {BOX_NUMBER} Contents.csv"

root = tk.Tk()
root.title('NPCS')
root.geometry("800x600")


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

ocr = PaddleOCR(use_textline_orientation=True, lang='en', device="cpu", enable_mkldnn=False)

while True:
    ret, frame = cap.read()

    cv2.imshow("frame", frame)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    key = cv2.waitKey(1)
    
    if key == ord(' '):

        entry = []
        cv2.imwrite("label.jpg", frame)
        cv2.imshow("captured", frame)

        result = ocr.predict("label.jpg")
        result = result[0]['rec_texts']

        print(result)

#===================================================================================================part number
        pattern = re.compile(r"\b[-a-zA-Z0-9]{8,19}[a-zA-Z]\b")

        possible_parts = []
        for text in result:
            # 1. Clean the text: Strip common prefixes like "P/N:", "P/N-", "p/n " 
            # so they don't break our word boundaries.
            clean_text = re.sub(r"(?i)\bp/?n[\s:-]+", "", text)
            
            # 2. Improved Regex:
            # (?=[a-zA-Z0-9-]*[0-9]) -> Forces the word to contain AT LEAST ONE number
            # [-a-zA-Z0-9]{8,19}     -> 8 to 19 characters (letters, numbers, hyphens)
            # [a-zA-Z]               -> Must end in a letter
            pattern = re.compile(r"\b(?=[a-zA-Z0-9-]*[0-9])[-a-zA-Z0-9]{8,19}[a-zA-Z]\b")
            
            matches = pattern.findall(clean_text)
            
            # 3. Final filtering
            for m in matches:
                clean_m = m.upper()
                # Ignore it if it's clearly a Date Code (DC-)
                if not clean_m.startswith("DC-"):
                    possible_parts.append(clean_m)


##############################################################################Possible parts
        title = "Possible Parts"
        button_thick = 0.075
        next_label_length = 0
        loc = 0
        buttons(possible_parts, title, button_thick, next_label_length, loc)


##############################################################################alt part numb
        title = "Alternate Part Number"
        button_thick = 0.075
        next_label_length = 0.2
        loc = 1
        buttons(possible_parts, title, button_thick, next_label_length, loc)
            
        #add edit button, not 'none' for this one

#===================================================================================================DATE CODE
        possible_date_codes = []
        for text in result:
            # Pattern to identify if a line explicitly mentions a date code variant
            prefix_pattern = re.compile(r"(?i)(?:d/c|dc|date\s*code|date|code)")
            
            if prefix_pattern.search(text):
                # 1. Clean the text: Wipe out the matched prefix and any trailing spaces/colons/dashes
                clean_text = re.sub(r"(?i)(?:d/c|dc|date\s*code|date|code)\s*[-:]?\s*", "", text)
                
                # 2. Extract: Grab the first 4 digits and an optional character directly following them
                # Dropping the trailing \b completely handles cases like '9636t2pes' -> '9636T'
                match = re.search(r"\d{4}[a-zA-Z]?", clean_text)
                if match:
                    possible_date_codes.append(match.group().upper())
            else:
                # 3. No prefix found: Only accept it if the entire line is exactly a standalone date code
                # This keeps strings like "ISO 9001-2000" from leaking into your data
                standalone_match = re.match(r"^\s*(\d{4}[a-zA-Z]?)\s*$", text)
                if standalone_match:
                    possible_date_codes.append(standalone_match.group(1).upper())



        title = "Possible Date Codes"
        button_thick = 0.075
        next_label_length = 0.4
        loc = 4
        buttons(possible_date_codes, title, button_thick, next_label_length, loc)   
        
        
#===================================================================================================quantity
        next_label_length = 0.6

        tk.Label(root, text="Quantity:").place(relx=0.30, rely=0+next_label_length, relheight=button_thick/2)
        edited = tk.Entry(root, width=50).place(relx=0.35, rely=0+next_label_length, relheight=button_thick/2)
        if edited:
            entry.insert(5,edited)

#===================================================================================================
        print(entry)

        csv_file_name = f"Box {BOX_NUMBER} Contents.csv"
        with open(csv_file_name, mode='a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(entry)

#-----------------------------------------------------main loop end
        root.mainloop()




    if key == ord('q'):
        header_list = ['Part Number', 'Description', 'Size', 'Date Code', 'Lot Code', 'Quantity', 'Box Number']
        if csv_file_name and os.path.exists(csv_file_name):
            df = pd.read_csv(csv_file_name, header=None)
            df.to_csv(csv_file_name, header=header_list, index=False)
        break
        #change