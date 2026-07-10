import os

from setuptools._distutils import command

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
import sys


BOX_NUMBER = 0

pygame.init()
pygame.mixer.init()
def good():
    good_sfx = pygame.mixer.Sound("good.mp3")
    good_sfx.set_volume(0.3)
    good_sfx.play()
    time.sleep(1)

def bad():
    bad_sfx = pygame.mixer.Sound("bad.mp3")
    bad_sfx.set_volume(1)
    print("ERROR!!!!!")
    bad_sfx.play()
    time.sleep(0.4)
    bad_sfx.play()
    time.sleep(0.4)
    bad_sfx.play()
    time.sleep(1)


def quit_it():
    header_list = ['Part Number', 'Description', 'Size', 'Date Code', 'Quantity', 'Box Number']
    if csv_file_name and os.path.exists(csv_file_name) and os.path.getsize(csv_file_name) > 0:
        try:
            df = pd.read_csv(csv_file_name, header=None)
            df = df.reindex(columns=range(6))
            df.columns = header_list
            df.to_csv(csv_file_name, index=False)
        except pd.errors.EmptyDataError:
            pass  # Failsafe just in case

    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

def update_entry(index, text):
    entry.pop(index)
    entry.insert(index, text)
    print(f"DEBUG: Saved '{text}' into column {index}!") # This lets you see it working live!


def save_and_quit(current_entry):
    # 1. Save the current part we are looking at
    with open(csv_file_name, mode='a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(current_entry)
        good()

    # 2. Run your normal quit function to format headers and close!
    quit_it()


def buttons(possible_parts, title, button_thick, next_label_length, loc):
    tk.Label(root, text=title).place(relx=0, rely=0 + next_label_length, relheight=button_thick / 2)

    # "None" Button Layout - Streamlined!
    btn_none = tk.Button(root, text="None", bg="white",
                         command=lambda: [update_entry(loc, "None"), btn_none.config(bg="lightblue")])
    btn_none.place(relx=0.17, rely=0 + next_label_length, relwidth=0.15, relheight=button_thick / 2)

    tk.Label(root, text="Edit:").place(relx=0.30, rely=0 + next_label_length, relheight=button_thick / 2)

    # Text box (Stays normal since it uses Return key binding)
    edite = tk.Entry(root, width=50)
    edite.place(relx=0.35, rely=0 + next_label_length, relheight=button_thick / 2)
    edite.bind('<Return>', lambda event, e=edite, l=loc: update_entry(l, e.get()))

    if len(possible_parts) == 1:
        tk.Label(root, text=f"Found: {possible_parts[0]}").place(relx=0.10, rely=0.04 + next_label_length)
        update_entry(loc, possible_parts[0])

    elif len(possible_parts) == 2:
        btn1 = tk.Button(root, text=possible_parts[0], bg="white",
                         command=lambda: [update_entry(loc, possible_parts[0]), btn1.config(bg="lightblue")])
        btn1.place(relx=0, rely=0.04 + next_label_length, relwidth=0.5, relheight=button_thick)

        btn2 = tk.Button(root, text=possible_parts[1], bg="white",
                         command=lambda: [update_entry(loc, possible_parts[1]), btn2.config(bg="lightblue")])
        btn2.place(relx=0.5, rely=0.04 + next_label_length, relwidth=0.5, relheight=button_thick)

    elif len(possible_parts) == 3:
        btn1 = tk.Button(root, text=possible_parts[0], bg="white",
                         command=lambda: [update_entry(loc, possible_parts[0]), btn1.config(bg="lightblue")])
        btn1.place(relx=0, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)

        btn2 = tk.Button(root, text=possible_parts[1], bg="white",
                         command=lambda: [update_entry(loc, possible_parts[1]), btn2.config(bg="lightblue")])
        btn2.place(relx=0.333, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)

        btn3 = tk.Button(root, text=possible_parts[2], bg="white",
                         command=lambda: [update_entry(loc, possible_parts[2]), btn3.config(bg="lightblue")])
        btn3.place(relx=0.666, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)

csv_file_name = f"Box {BOX_NUMBER} Contents.csv"

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
        root = tk.Tk()
        root.title('NPCS')
        root.geometry("800x600")

        entry = ["", "", "", "", "", ""]
        cv2.imwrite("label.jpg", frame)

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
        if len(possible_parts) > 1:
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
        loc = 3
        buttons(possible_date_codes, title, button_thick, next_label_length, loc)   
        
        
#===================================================================================================quantity
        #===================================================================================================QUANTITY
        possible_quantities = []
        for text in result:
            # 1. Look for prefixes like QTY, QTY:, Quantity, etc.
            prefix_pattern = re.compile(r"(?i)(?:qty|quantity|q)\s*[-:]?\s*")

            if prefix_pattern.search(text):
                # Wipe the prefix out
                clean_text = prefix_pattern.sub("", text)
                # Find exactly 1 to 5 digits with word boundaries
                match = re.search(r"\b\d{1,5}\b", clean_text)
                if match:
                    possible_quantities.append(match.group())
            else:
                # 2. No prefix? Accept the line if it is ONLY a 1 to 5 digit number
                standalone_match = re.match(r"^\s*(\d{1,5})\s*$", text)
                if standalone_match:
                    possible_quantities.append(standalone_match.group(1))

        title = "Possible Quantities"
        button_thick = 0.075
        next_label_length = 0.6
        loc = 4
        # Pass in possible_quantities!
        buttons(possible_quantities, title, button_thick, next_label_length, loc)
    #===================================================================================================
        print(entry)

        Etch = tk.Button(root, text="Etch into Sheet", command=lambda: (root.destroy(), good()))
        Etch.place(relx=0.65, rely=0.88, relwidth=0.333, relheight=button_thick * 1.3)
        tk.Button(root, text="Save and Quit", command=lambda: save_and_quit(entry)).place(relx=0.02, rely=0.88, relwidth=0.333, relheight=button_thick * 1.3)

#-----------------------------------------------------main loop end                                                            relheight=button_thick * 1.3)
        root.mainloop()


        csv_file_name = f"Box {BOX_NUMBER} Contents.csv"
        with open(csv_file_name, mode='a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(entry)




    if key == ord('q'):
        quit_it()