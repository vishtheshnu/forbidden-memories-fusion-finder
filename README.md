# forbidden-memories-fusion-finder
Python tool to find fusions in yugioh Forbidden Memories


Demo: https://youtu.be/Xc5Zvx_A-bY

Setup Instructions:

1. Download all of the files in the repository onto your computer
2. Create a new folder in the location you downloaded the app named "data". Inside of that folder, create a new subfolder for each mod you want the Fusion Finder to work with.
3. Mount the FM ROM's .bin file and extract the "SLUS_014.11" and "WA_MRG.MRG" files, and put them both inside one of the subfolders you created in the previous step.
4. Open the command line to the folder you downloaded the files into
5. Type "pip install -r requirements.txt" and hit enter
  5a. Optionally create a virtual environment and activate it first if you're an advanced user
6. Type "python app.py" and hit enter
7. The app should now open up. In it, select the subfolder from the top drop-down menu whose fusion data you want to load and then press the "LOAD DATA" button next to it.
  7a. If the "LOAD DATA" button doesn't appear, stretch the app window to the left or right since the window might not be large enough to show it.
8. Select the emulator window for the game from the lower drop-down menu
9. When you want the app to get fusions from your current hand, have the emulator window not overlap with the app, and then press the "GET FUSIONS" button

On subsequent uses, start from step 6
