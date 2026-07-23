# --- PADDLEX PYINSTALLER FIX ---
try:
    import paddlex.utils.deps


    # Create a safe dummy decorator that lets the real code pass through untouched
    def dummy_decorator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


    paddlex.utils.deps.require_extra = dummy_decorator
    paddlex.utils.deps.require_deps = dummy_decorator
    paddlex.utils.deps.require_packages = dummy_decorator
except ImportError:
    pass
# -------------------------------

import os
import ctypes
import tempfile
import configparser
import sys
import time
import csv
import re
import tkinter as tk
from tkinter import font, messagebox

################################################################################to bundle in the sounds in the .exe
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller --onefile"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Ensure taskbar shows the .ico file in Windows instead of default Python icon
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("npcs.inventory.app.1")
except Exception:
    pass
################################################################################to bundle in the sounds in the .exe



# Force disable the conflicting PIR engine elements and optimization libraries
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

# --- OPENMP DEADLOCK FIX (ADD THESE TWO LINES) ---
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
# -------------------------------------------------

import numpy as np
import cv2
import pandas as pd
import requests
import pygame
from paddleocr import PaddleOCR

# Configuration
MOUSER_API_KEY = os.getenv("MOUSER_API_KEY")

# --- INNO SETUP SAVE LOCATION LOGIC ---
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(exe_dir, 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)

# Reads chosen folder from config.ini, defaults to exe folder if not found
default_docs_dir = os.path.join(os.path.expanduser("~"), "Documents", "NPCS")
save_dir = config.get('Settings', 'SaveDirectory', fallback=default_docs_dir)
os.makedirs(save_dir, exist_ok=True)

# Full path where your CSV will live
csv_file_name = os.path.join(save_dir, "RENAME_Parts.csv")
# --------------------------------------


# Initialize Pygame Mixer for Audio
pygame.init()
pygame.mixer.init()


# --- Helper Functions ---

def good():
    good_sfx = pygame.mixer.Sound(resource_path("good.mp3"))
    good_sfx.set_volume(0.3)
    good_sfx.play()
    time.sleep(1)


def bad():
    bad_sfx = pygame.mixer.Sound(resource_path("bad.mp3"))
    bad_sfx.set_volume(1)
    print("ERROR!!!!!")
    bad_sfx.play()
    time.sleep(0.4)
    bad_sfx.play()
    time.sleep(0.4)
    bad_sfx.play()
    time.sleep(1)


    
def quit_it():
    header_list = ['Box ID', 'Part', 'Alt Part Number', 'Type', 'Desc', 'Package', 'Date', 'Quantity']
    if csv_file_name and os.path.exists(csv_file_name) and os.path.getsize(csv_file_name) > 0:
        try:
            df = pd.read_csv(csv_file_name, header=None, dtype=str, encoding='utf-8')
            df = df.reindex(columns=range(8))
            df.columns = header_list
            df.to_csv(csv_file_name, index=False, encoding='utf-8')
        except pd.errors.EmptyDataError:
            pass
        except PermissionError:
            print("WARNING: Could not apply headers because the file is open in Excel.")

    cap.release()
    cv2.destroyAllWindows()
    sys.exit()


def update_entry(index, text):
    entry[index] = text
    print(f"DEBUG: Saved '{text}' into column {index}!")


# --- MIL-SPEC & NSN Decoder ---

def decode_milspec_expanded(part_number):
    pn = str(part_number).strip().upper()

    # --- New Feature: National Stock Number (NSN) Decoder ---
    if re.match(r"^\d{4}-\d{2}-", pn):
        fsc = pn[:4]
        fsc_map = {
            "5905": ("resistor", "National Stock Number (NSN) Resistor"),
            "5910": ("capacitor", "National Stock Number (NSN) Capacitor"),
            "5920": ("fuse", "National Stock Number (NSN) Fuse / Protection"),
            "5935": ("connector", "National Stock Number (NSN) Connector"),
            "5945": ("relay", "National Stock Number (NSN) Relay"),
            "5961": ("semiconductor", "National Stock Number (NSN) Diode / Transistor"),
            "5962": ("IC", "National Stock Number (NSN) Microcircuit / IC")
        }
        cat, desc = fsc_map.get(fsc, ("other", "National Stock Number (NSN) Component"))
        return {
            "Category": cat,
            "Description": desc,
            "Package Size": "N/A",
            "Packaging": "Military Poly Bag"
        }

    # --- Existing MIL-SPEC Decoders ---
    if pn.startswith("M55342") or pn.startswith("D55342"):
        res_sizes = {
            '11': '0402', '12': '0603', '06': '0805', '05': '0805',
            '07': '1206', '08': '2010', '09': '2512', '10': '1010', '01': '0502'
        }
        size_code = pn[7:9] if len(pn) >= 9 else "Unknown"
        package_size = res_sizes.get(size_code, f"Code {size_code}")
        value_code = pn[10:14] if len(pn) >= 14 else ""

        res_str = value_code
        mil_res_letters = {
            'A': (1, "0.1%"), 'B': (1000, "0.1%"), 'C': (1000000, "0.1%"),
            'D': (1, "1.0%"), 'E': (1000, "1.0%"), 'F': (1000000, "1.0%"),
            'G': (1, "2.0%"), 'H': (1000, "2.0%"), 'T': (1000000, "2.0%"),
            'J': (1, "5.0%"), 'K': (1000, "5.0%"), 'L': (1000000, "5.0%"),
            'M': (1, "10.0%"), 'N': (1000, "10.0%"), 'P': (1000000, "10.0%")
        }

        found_letter = None
        for char in value_code:
            if char.isalpha():
                found_letter = char
                break

        if found_letter in mil_res_letters:
            mult, tol = mil_res_letters[found_letter]
            idx = value_code.find(found_letter)
            before = value_code[:idx]
            after = value_code[idx + 1:]
            try:
                sig_str = before + "." + (after if after else "0")
                val = float(sig_str) * mult
                if val >= 1000000:
                    res_str = f"{val / 1000000:g} MOhms ({tol})"
                elif val >= 1000:
                    res_str = f"{val / 1000:g} kOhms ({tol})"
                else:
                    res_str = f"{val:g} Ohms ({tol})"
            except ValueError:
                pass

        packaging = "Bulk / Bag"
        if pn.endswith("TR") or "T/R" in pn:
            packaging = "Tape & Reel"
        elif pn.endswith("W") or pn.endswith("WA"):
            packaging = "Waffle Pack"
        elif pn.endswith("BS"):
            packaging = "Bulk / Bag"

        return {
            "Category": "resistor",
            "Description": "MIL-SPEC SMD Film Resistor",
            "Value": res_str,
            "Package Size": package_size,
            "Packaging": packaging
        }

    elif pn.startswith("CDR"):
        cap_sizes = {
            '31': '0805', '32': '1206', '33': '1210', '34': '1812', '35': '1825',
            '01': '0805', '02': '1805', '03': '1808', '04': '1812'
        }
        size_code = pn[3:5] if len(pn) >= 5 else "Unknown"
        package_size = cap_sizes.get(size_code, f"Code {size_code}")
        packaging = "Tape & Reel" if pn.endswith("TR") else "Bulk / Bag"

        return {
            "Category": "capacitor",
            "Description": "MIL-SPEC Ceramic Chip Capacitor",
            "Package Size": package_size,
            "Packaging": packaging
        }

    elif pn.startswith("JAN"):
        category = "semiconductor"
        if "1N" in pn:
            category = "diode"
        elif "2N" in pn:
            category = "transistor"
        packaging = "Tape & Reel" if pn.endswith("TR") else "Standard/Bag"
        return {"Category": category, "Description": "MIL-SPEC Discrete Semiconductor", "Package Size": "Varies",
                "Packaging": packaging}

    elif pn.startswith("5962") or pn.startswith("M38510"):
        return {"Category": "IC", "Description": "MIL-SPEC Microcircuit", "Package Size": "Varies",
                "Packaging": "Tube / Tray"}

    elif pn.startswith("D38999") or pn.startswith("MS274") or pn.startswith("M83513"):
        return {"Category": "connector", "Description": "MIL-SPEC Aerospace Connector", "Package Size": "N/A",
                "Packaging": "Bulk / Individual"}

    elif pn.startswith("M39010") or pn.startswith("MS750"):
        packaging = "Tape & Reel" if pn.endswith("TR") else "Bulk / Bag"
        return {"Category": "inductor", "Description": "MIL-SPEC RF Inductor", "Package Size": "Varies",
                "Packaging": packaging}

    elif pn.startswith("311P"):
        return {"Category": "space component", "Description": "NASA GSFC Procured Component", "Package Size": "N/A",
                "Packaging": "Standard"}

    elif pn.startswith("UT54") or pn.startswith("UT63"):
        return {"Category": "IC", "Description": "Aerospace Rad-Hard IC", "Package Size": "Varies",
                "Packaging": "Standard"}

    elif pn.startswith("M54") or pn.startswith("M38"):
        return {"Category": "IC", "Description": "Military-Grade Logic IC", "Package Size": "Varies",
                "Packaging": "Tube / Tray"}

    elif pn.startswith("SN74") or pn.startswith("74HC") or pn.startswith("74LS") or pn.startswith("CD40"):
        return {"Category": "IC", "Description": "Commercial Logic IC", "Package Size": "Varies (SOIC/DIP)",
                "Packaging": "Tube / Reel"}

    elif re.match(r"^\d{2}HS\d{2}", pn):
        return {"Category": "capacitor", "Description": "High-Voltage Radial Ceramic Capacitor",
                "Package Size": "Radial", "Packaging": "Bulk / Bag"}

    elif pn.startswith("LT1") or pn.startswith("LT3") or pn.startswith("LTC"):
        return {"Category": "IC / Op-Amp", "Description": "Linear Technology Precision IC",
                "Package Size": "Varies (SOIC/DIP)", "Packaging": "Tube / Reel"}

    elif pn.startswith("TSW-") or pn.startswith("SSW-") or pn.startswith("FTSH-"):
        return {"Category": "connector", "Description": "Samtec Board-to-Board Connector", "Package Size": "N/A",
                "Packaging": "Bulk / Tube"}

    elif pn.startswith("GUS-"):
        return {"Category": "resistor", "Description": "SMD Resistor Network", "Package Size": "QSOP/SSOP",
                "Packaging": "Tube / Reel"}

    return None


# --- API and Data Integration ---

def search_mouser(part_number):
    url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={MOUSER_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "SearchByPartRequest": {
            "mouserPartNumber": part_number,
            "partSearchOptions": "BeginsWith"
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        return [f"API Error: connection failed", "N/A", "N/A", "other"]

    description, package_size, value, part_type = "N/A", "N/A", "N/A", "other"

    if response.status_code == 200:
        data = response.json()
        search_results = data.get("SearchResults") or {}

        if search_results.get("NumberOfResult", 0) == 0:
            return ["Part Not Found", "N/A", "N/A", "other"]

        product = search_results["Parts"][0]
        description = product.get("Description", "N/A")
        category_lower = product.get("Category", "").lower()
        desc_lower = description.lower()

        for attr in product.get("ProductAttributes", []):
            attr_name = attr.get("AttributeName")
            attr_value = attr.get("AttributeValue")

            if attr_name == "Package / Case":
                package_size = attr_value
            elif attr_name in ["Resistance", "Capacitance", "Inductance"]:
                value = attr_value

        if package_size == "N/A":
            size_match = re.search(r'\b(0402|0603|0805|0705|1206|1210|2010|2512)\b', description)
            if size_match:
                package_size = size_match.group(1)

        if value == "N/A":
            value_match = re.search(r'\b(\d+(?:\.\d+)?\s*(?:K|M|Ohm|Ohms|R))\b', description, re.IGNORECASE)
            if value_match:
                value = value_match.group(1)

        if "resistor" in category_lower or "resistor" in desc_lower or "ohm" in value.lower():
            part_type = "resistor"
        elif "capacitor" in category_lower or "capacitor" in desc_lower:
            part_type = "capacitor"
        elif "op amp" in desc_lower or "operational amplifier" in category_lower or "operational amplifier" in desc_lower:
            part_type = "op amp"
        elif "diode" in category_lower or "diode" in desc_lower:
            part_type = "diode"
        elif "inductor" in category_lower or "inductor" in desc_lower:
            part_type = "inductors"
        elif "jumper" in desc_lower or "header" in desc_lower or "pins" in desc_lower:
            part_type = "jumper pins"
        elif "integrated circuit" in category_lower or "ic" in category_lower:
            part_type = "IC"

        return [description, package_size, value, part_type]

    return [f"API Error {response.status_code}", "N/A", "N/A", "other"]


def populate_mouser_data(current_entry):
    part_number = current_entry[1]
    alt_part_number = current_entry[2]

    def try_lookup(pn):
        if not pn or pn == "None" or pn == "":
            return None

        mil_data = decode_milspec_expanded(pn)
        if mil_data:
            print(f"DEBUG: Decoded '{pn}' via MIL-SPEC/NSN Decoder!")
            return [
                f"{mil_data['Description']} ({mil_data['Packaging']})",
                mil_data["Package Size"],
                mil_data.get("Value", "N/A"),
                mil_data["Category"]
            ]

        print(f"DEBUG: Checking '{pn}' via Mouser API...")
        mouser_data = search_mouser(pn)
        if mouser_data[0] != "Part Not Found" and not str(mouser_data[0]).startswith("API Error"):
            return mouser_data

        return None

    print("DEBUG: Beginning lookup sequence...")
    final_data = try_lookup(part_number)

    if not final_data:
        print("DEBUG: Primary part failed. Trying Alternate Part Number...")
        final_data = try_lookup(alt_part_number)

    if final_data:
        current_entry[3] = final_data[3]
        if final_data[2] != "N/A":
            current_entry[4] = f"{final_data[0]} (Value: {final_data[2]})"
        else:
            current_entry[4] = final_data[0]
        current_entry[5] = final_data[1]
        print("DEBUG: Successfully mapped data to sheet row!")
    else:
        current_entry[3] = "other"
        current_entry[4] = "Part Not Found"
        current_entry[5] = "N/A"
        print("DEBUG: Both primary and alternate part lookups failed.")


def save_and_quit(current_entry):
    populate_mouser_data(current_entry)
    current_entry[0] = f"{current_entry[3].upper()}, {current_entry[5]}"
    try:
        with open(csv_file_name, mode='a', newline='', encoding='utf-8') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(current_entry)
            good()
        quit_it()
    except PermissionError:
        print(f"ERROR: Cannot save. Please close {csv_file_name} in Excel!")
        bad()
        messagebox.showerror("Save Error",
                             f"Permission Denied!\n\nPlease close '{csv_file_name}' in Excel and try again.")


# --- GUI Buttons ---

def buttons(possible_parts, title, button_thick, next_label_length, loc, auto_fill=True):
    tk.Label(root, text=title, font=word_font).place(relx=0, rely=0 + next_label_length, relheight=button_thick / 2)

    btn_none = tk.Button(root, text="None", bg="white", font=word_font,
                         command=lambda: [update_entry(loc, "None"), btn_none.config(bg="lightblue")])
    btn_none.place(relx=0.17, rely=0 + next_label_length, relwidth=0.15, relheight=button_thick / 2)

    tk.Label(root, text="Edit:", font=word_font).place(relx=0.30, rely=0 + next_label_length,
                                                       relheight=button_thick / 2)

    edite = tk.Entry(root, width=50)
    text_boxes.append((edite, loc))
    edite.place(relx=0.35, rely=0 + next_label_length, relheight=button_thick / 2)
    edite.bind('<Return>', lambda event, e=edite, l=loc: update_entry(l, e.get()))

    edite.bind('<Button-1>',
               lambda event, e=edite, p=possible_parts: e.insert(0, p[0]) if len(p) > 0 and e.get() == "" else None)
    edite.bind('<Return>', lambda event, e=edite, l=loc: [update_entry(l, e.get()), e.config(bg="#D4EDDA")])

    display_parts = possible_parts[:3]

    if len(display_parts) == 1:
        if auto_fill:
            tk.Label(root, text=f"Found: {display_parts[0]}", font=found_font).place(relx=0.10,
                                                                                     rely=0.04 + next_label_length)
            update_entry(loc, display_parts[0])
        else:
            btn1 = tk.Button(root, text=display_parts[0], bg="white", font=word_font,
                             command=lambda: [update_entry(loc, display_parts[0]), btn1.config(bg="lightblue")])
            btn1.place(relx=0, rely=0.04 + next_label_length, relwidth=0.5, relheight=button_thick)

    elif len(display_parts) == 2:
        btn1 = tk.Button(root, text=display_parts[0], bg="white", font=word_font,
                         command=lambda: [update_entry(loc, display_parts[0]), btn1.config(bg="lightblue")])
        btn1.place(relx=0, rely=0.04 + next_label_length, relwidth=0.5, relheight=button_thick)

        btn2 = tk.Button(root, text=display_parts[1], bg="white", font=word_font,
                         command=lambda: [update_entry(loc, display_parts[1]), btn2.config(bg="lightblue")])
        btn2.place(relx=0.5, rely=0.04 + next_label_length, relwidth=0.5, relheight=button_thick)

    elif len(display_parts) == 3:
        btn1 = tk.Button(root, text=display_parts[0], bg="white", font=word_font,
                         command=lambda: [update_entry(loc, display_parts[0]), btn1.config(bg="lightblue")])
        btn1.place(relx=0, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)

        btn2 = tk.Button(root, text=display_parts[1], bg="white", font=word_font,
                         command=lambda: [update_entry(loc, display_parts[1]), btn2.config(bg="lightblue")])
        btn2.place(relx=0.333, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)

        btn3 = tk.Button(root, text=display_parts[2], bg="white", font=word_font,
                         command=lambda: [update_entry(loc, display_parts[2]), btn3.config(bg="lightblue")])
        btn3.place(relx=0.666, rely=0.04 + next_label_length, relwidth=0.333, relheight=button_thick)


# --- Main Application Loop ---

if __name__ == "__main__":



    import multiprocessing
    multiprocessing.freeze_support()


    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

    # Force use_angle_cls instead of textline orientation to bypass PP-LCNet
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_textline_orientation=False,
        lang='en',
        device="cpu",
        enable_mkldnn=False
    )

    while True:
        ret, frame = cap.read()
        cv2.imshow("frame", frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        key = cv2.waitKey(1) & 0xFF

        if cv2.getWindowProperty("frame", cv2.WND_PROP_VISIBLE) < 1:
            quit_it()

        if key == 32 or key == ord(' '):
            root = tk.Tk()
            root.title('NPCS')
            root.geometry("800x600")

            bg_color = "lightgray"
            root.configure(bg=bg_color)
            found_font = font.Font(family="Helvetica", size=11, weight="bold")
            meta_font = font.Font(family="Helvetica", size=17, weight="bold")
            word_font = font.Font(family="Helvetica", size=10, weight="bold")

            entry = ["", "", "", "", "", "", "", ""]
            text_boxes = []

            temp_img_path = os.path.join(tempfile.gettempdir(), "npcs_label.jpg")
            cv2.imwrite(temp_img_path, frame)
            result = ocr.predict(temp_img_path)
            result = result[0]['rec_texts']

            print(result)

            possible_parts = []
            for text in result:
                clean_text = re.sub(r"(?i)\bp/?n[\s:-]+", "", text)
                pattern = re.compile(r"\b(?=[A-Za-z0-9-]*[0-9])[-A-Za-z0-9]{6,25}\b")
                matches = pattern.findall(clean_text)

                for m in matches:
                    clean_m = m.upper()
                    if not clean_m.startswith("DC-") and clean_m not in possible_parts:
                        possible_parts.append(clean_m)

            buttons(possible_parts, "Possible Parts", 0.075, 0, 1, auto_fill=True)
            buttons(possible_parts, "Alt Part Number", 0.075, 0.2, 2, auto_fill=False)

            # Date Codes Logic
            possible_date_codes = []
            for text in result:
                prefix_pattern = re.compile(r"(?i)(?:d/c|dc|date\s*code|date|code)")
                if prefix_pattern.search(text):
                    clean_text = re.sub(r"(?i)(?:d/c|dc|date\s*code|date|code)\s*[-:]?\s*", "", text)
                    match = re.search(r"\d{4}[a-zA-Z]?", clean_text)
                    if match:
                        possible_date_codes.append(match.group().upper())
                else:
                    standalone_match = re.match(r"^\s*(\d{4}[a-zA-Z]?)\s*$", text)
                    if standalone_match:
                        possible_date_codes.append(standalone_match.group(1).upper())

            buttons(possible_date_codes, "Possible Date Codes", 0.075, 0.4, 6)

            # Quantities Logic
            possible_quantities = []
            for text in result:
                prefix_pattern = re.compile(r"(?i)(?:qty|quantity|q)\s*[-:]?\s*")
                if prefix_pattern.search(text):
                    clean_text = prefix_pattern.sub("", text)
                    match = re.search(r"\b\d{1,5}\b", clean_text)
                    if match:
                        possible_quantities.append(match.group())
                else:
                    standalone_match = re.match(r"^\s*(\d{1,5})\s*$", text)
                    if standalone_match:
                        possible_quantities.append(standalone_match.group(1))

            buttons(possible_quantities, "Possible Quantities", 0.075, 0.6, 7)


            print("Initial blank entry layout:", entry)

            Etch = tk.Button(root, text="Etch into Sheet",
                             command=lambda: (
                                 [update_entry(loc, box.get()) for box, loc in text_boxes if box.get() != ""],
                                 root.destroy(), good()), font=meta_font)
            Etch.place(relx=0.65, rely=0.88, relwidth=0.333, relheight=0.075 * 1.3)

            tk.Button(root, text="Save and Quit",
                      command=lambda: ([update_entry(loc, box.get()) for box, loc in text_boxes if box.get() != ""],
                                       save_and_quit(entry)), font=meta_font).place(relx=0.02, rely=0.88,
                                                                                    relwidth=0.333,
                                                                                    relheight=0.075 * 1.3)

            for widget in root.winfo_children():
                widget.configure(bg=bg_color)

            root.mainloop()

            populate_mouser_data(entry)
            entry[0] = f"{entry[3].upper()}, {entry[5]}"

            messagebox.showinfo("Sorting Instructions", f"Place in:\nType: {entry[3].upper()}\nPackage: {entry[5]}")

            try:
                with open(csv_file_name, mode='a', newline='', encoding='utf-8') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow(entry)
            except PermissionError:
                print(f"ERROR: File lock encountered. Could not auto-save row to {csv_file_name}.")
                bad()
                messagebox.showerror("Save Error",
                                     f"Could not auto-save row!\nPlease close '{csv_file_name}' in Excel before parsing the next item.")