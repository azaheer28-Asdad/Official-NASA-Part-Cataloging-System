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


csv_file_name = f"Box {BOX_NUMBER} Contents.csv"


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

        print("Possible Parts:" ,possible_parts)
        option = input("select:_")

        if option == "00":
            entry.insert(0,"None")
        elif option == "000":
            change = input("Enter Custom Val:_")
            entry.insert(0,change)
        else:
            entry.insert(0,possible_parts[int(option)])

#--------------------------------------spacing compensation
        entry.insert(1, "None")
        entry.insert(2, "None")
#--------------------------------------spacing compensation

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

        print("Possible Date Codes:",possible_date_codes)
        option = input("select:_")
        
        if option == "00":
            entry.insert(3,"None")
        elif option == "000":
            change = input("Enter Custom Val:_")
            entry.insert(3,change)
        else:
            entry.insert(3,possible_date_codes[int(option)])
#===================================================================================================LOT CODE
        possible_lot_codes = []
        for text in result:
            # Pattern to identify if a line explicitly mentions LOC: or LOT#
            prefix_pattern = re.compile(r"(?i)\b(?:loc|lot)\s*[:#]")
            
            if prefix_pattern.search(text):
                # 1. Clean the text: Wipe out the prefix (LOC:, LOT #, etc.) and any spaces after it
                clean_text = re.sub(r"(?i)\b(?:loc|lot)\s*[:#]\s*", "", text)
                
                # 2. Extract: Grab the continuous sequence of letters, numbers, dashes, or underscores
                match = re.search(r"[a-zA-Z0-9_-]+", clean_text)
                if match:
                    possible_lot_codes.append(match.group().upper())
            else:
                # 3. No prefix found: General Regex Filter
                # (?<![a-zA-Z0-9_-])           -> Custom boundary to ensure we don't grab partial strings
                # (?=[a-zA-Z0-9_-]*[0-9])      -> Requires AT LEAST one number (ignores pure dictionary words)
                # [a-zA-Z0-9_-]{4,25}          -> Matches 4 to 25 characters (letters, numbers, -, _)
                # (?![a-zA-Z0-9_-])            -> Custom closing boundary
                fallback_pattern = re.compile(r"(?<![a-zA-Z0-9_-])(?=[a-zA-Z0-9_-]*[0-9])[a-zA-Z0-9_-]{4,25}(?![a-zA-Z0-9_-])")
                matches = fallback_pattern.findall(text)
                
                for m in matches:
                    possible_lot_codes.append(m.upper())

        # Optional: Remove duplicates from the list to keep your terminal output clean
        possible_lot_codes = list(set(possible_lot_codes))
        
        print("Possible Lot Codes:", possible_lot_codes)
        option = input("select:_")

        if option == "00":
            entry.insert(4,"None")
        elif option == "000":
            change = input("Enter Custom Val:_")
            entry.insert(4,change)
        else:
            entry.insert(4,possible_lot_codes[int(option)])
#===================================================================================================quantity
        quant = int(input("Enter Quantity:_"))
        entry.insert(5, quant)
#===================================================================================================Box Number
        entry.insert(6, BOX_NUMBER)
#===================================================================================================
        print(entry)

        csv_file_name = f"Box {BOX_NUMBER} Contents.csv"
        with open(csv_file_name, mode='a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(entry)




    if key == ord('q'):
        header_list = ['Part Number', 'Description', 'Size', 'Date Code', 'Lot Code', 'Quantity', 'Box Number']
        if csv_file_name and os.path.exists(csv_file_name):
            df = pd.read_csv(csv_file_name, header=None)
            df.to_csv(csv_file_name, header=header_list, index=False)
        break