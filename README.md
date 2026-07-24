# NASA PART CATALOGING SYSTEM (NPCS)
This is an open-source application created by a high school NASA intern, used to eliminate the need to manually input part numbers and various other words from a part label into a spreadsheet. This tool is intendid to automate catalogging so people can focus on building circuts rather than spend hours looking for the parts. 
The program uses OpenCV to scan and process the part label, PaddleOCR to extract the text, some built-in logic plus Mouser's free API to extract information from the part number, and Tkinter to display everything. 
The program was intendid to be used as fast as possible and to put the user ease-of-use first. 
Please don't mind the outdated GUI --my bad. 
This is supposed to be a Windows only application, but if needed on Linux, you must run from the terminal. If needed on a Mac, the graphics may not work, but can probably be run from an IDE / terminal (using the NPCS.py file instead). 

## How to Install
### The General Gist:
**NO LIBRARIES NEED TO BE INSTALLED** -- Just use the windows .EXE file. Easy!
* Get a free API key from Mouser Electronics. (Has a limit of 1000 free scans per day)
* Save that key and title it exactly "MOUSER_API_KEY" (no quotes) as an env variable through the terminal
* Download the NPCS_setup.exe file and procede with instalation, pleas be patient as things do load even without progress bars.
* Application should launch on its own just be patient, it may take as long as a minute or two (with no loading screen). 

## How to Install, Specifics:
* [Click on this link](https://www.mouser.com/en/api-search/) and follow the instructions there and copy your API key.
* This is is highly secretive and take the necessary precautions to keep it safe.
  * Press the Windows Key and type ```CMD``` and then hit enter. Use this following command to save it as an env variable.
```
setx MOUSER_API_KEY "YOURAPIKEYGOESHEREINSIDETHEQUOTES"
```
Here is another example using a fake made-up API key (make sure you include the quotes):
```
setx MOUSER_API_KEY "ogaeoruegpoiuhp845hpgq9peiurbggfdfak"
```
* Close the terminal, Go back to GitHub, and download the NPCS_setup.exe file from the releases tab on the right side.
#### **Warning**
 * I do not own an expensive windows developer license so you will have to trust the file either in you browser, or in File Explorer before you are able to run it.
### How To Trust the File For Different Browsers:
* ### Google Chrome:
  * Chrome will not flag the file, but windows will. Go to File Explorer right after the file finishes the download, and right-click on the file → select properties → under the security section at the bottom, check the box that says "unblock" → apply → ok → double click the file to launch it and wait. After installation, it will auto launch, just give it 1 - 2 minutes, and it will be ready to go. (First time launch takes a bit longer) 

* ### Microsoft Edge:
  * Edge will flag the file. It will say that you don't often install files from here or somehting like that. Hover over the file with the error (you just downloaded) → keep → clcik the down arrow next to the delete button → select Keep Anyway → click the file in the broswer once to launch or alternatively double click the file in File Explorer and wait. After installation, it will auto launch, just give it 1 - 2 minutes, and it will be ready to go. (First time launch takes a bit longer)
 
* ### Mozilla Firefox:
  * Same as Chrome.

## How to Use the Software:
* This is the fun part.
* After the live camera feed comes up, click the actual feed and then bring up the label up to the camera.
* Press the Space Bar to take a photo, and give it a couple of seconds to process.
* Now you should see the GUI, and you want to click on the button with the correct part number, unless it was clear enogh that the software found it, and will auto-upload the one that it found unless you click the "Edit" text box.
* After clicking "edit" if needed, press the Enter / Return key to register what you wrote, if you didnt that's okay, it will auto pull whatever is in the text box.
* You can also click "none", and if will not fill that box of the spreadsheet.
* Fianlly, you can click the "Etch into Sheet" button to make a new entry, or you could click the "Save and quit" button to make an entry and kill the process gracefully.
* Alternatively, if you forget to press "save and quit" then you could also jsut close the camera window, and it will serve the same function.
* You will hear a nice sound if there are no errors (may not play in the lastest release, but windows makes its own sound so its okay).
* You will see a pop-up come up for sorting purposes. The way we are sorting them here at NASA, is by type and by package. Please note package data is not available for a lot of the scans, you could use an LLM at the end to fix that by uploading you .csv file.
* After quitting, you can find the .csv file under the new folder you created in the instaltion process, under the Documents tab.
* Double-click the .csv to open it, and if you have Excel or another spreadsheet program, it will promt you to format, click "NO", this will not remove the leading zeros. Also if your spreadsheet program has a different pop-up that comes up (like in LibreOffice Calc) make sure you click "seperate by comma", and not by spaces.
* Please rename the spreadsheet before running the program again, otherwise all of you next scans will write to that file. 

## Warnings:
* If you do not rename the spreadsheet, then your next entries will be appended to that spreadsheet. Unfortunately, there will be another set of headers added to the sheet, but nothing will be deleted.
* Unfortunately, the API and the system part number decoder will not catch everything, and depending on where your parts are coming from, the level of success may vary (but only by a little bit, the algorith is pretty fool-proof, so that even if the part isn't in Mouser's inventory, it will try to decode the part number itself). I had to use a free API to make this more avilable to people, but paid-for ones like "Silicon Expert" are aggregators and will likely know every part.
* You can try using a different API, but I'm not sure the format of how those may retrieve data, so they proabaly won't work.



#### AI Transperancy:
Google's Gemini was used to debug and write small portions of the code. 
