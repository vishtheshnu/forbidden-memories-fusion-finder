from appJar import gui
import pygetwindow as gw
import pyautogui
import cv2 as cv
import numpy as np
import filereader
import os

def getScreenshot():
    app.enableMeter("progress")
    mywin = gw.getWindowsWithTitle(app.getOptionBox("Game Window"))[0]
    mywin.activate()
    img = pyautogui.screenshot(region=(mywin.left, mywin.top, mywin.width, mywin.height))
    #img.save('screenshot.png')
    open_cv_image = cv.cvtColor(np.array(img), cv.COLOR_RGB2BGR)
    app.setMeter("progress", 15)
    #cv.resize(open_cv_image, (320, 240))
    #cv.imshow('screenshot', open_cv_image)
    fusionData = filereader.getFusionsFromImage(open_cv_image)
    resultText = ""
    for result in fusionData.keys():
        resultText += result+":\n"
        for chain in fusionData[result]:
            resultText += "\t"+str(chain)
            resultText += "\n"
    print(resultText)
    app.clearTextArea("fusions")
    app.setTextArea("fusions", resultText)
    app.disableMeter("progress")

def loadRom():
    app.enableMeter("progress")
    filereader.loadData(app.getOptionBox("RomFolder"), app)
    app.setButtonState("GET FUSIONS", "normal")
    app.disableMeter("progress")

#filereader.loadData()

app = gui("Forbidden Memories Fusion Finder", "700x500")
# add & configure widgets - widgets get a name, to help referencing them later
#app.addLabel("title", "Fusion Finder")

row = app.getRow()
app.addLabelOptionBox("RomFolder", [x[0] for x in os.walk('data') if x[0] != 'data'], row, 0)
app.addButton("LOAD DATA", loadRom, row, 1)

app.addMeter("progress", app.getRow(), 0, 3, 0)
app.setMeterFill("progress", "blue")
app.disableMeter("progress")

appTitles = gw.getAllTitles()
#[t if len(t) < 50 else t[:50] for t in gw.getAllTitles()]
app.addLabelOptionBox("Game Window", appTitles)#[str(i)+'. '+gw.getAllTitles()[i] for i in range(len(gw.getAllTitles()))])
app.addButton("GET FUSIONS", getScreenshot, "p", 1)
app.setButtonState("GET FUSIONS", "disabled")
app.addScrolledTextArea("fusions", "n", 0, 3, 3)
#app.setScrolledTextAreaWidth("fusions", 720)

# start the GUI
app.go()