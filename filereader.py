import numpy as np
from PIL import Image
from io import BytesIO
import cv2 as cv

game = None
mrg = None
cards = None
app = None
nonFusers = None

charList = ['']*256
gstarNames = ['None', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Pluto', 'Neptune', 'Mercury', 'Sun', 'Moon', 'Venus']

def loadData(dataFolder, myapp):
    global app
    app = myapp
    global game
    game = np.fromfile(dataFolder+'\SLUS_014.11', dtype=np.dtype('uint8'))
    global mrg
    mrg = np.fromfile(dataFolder+'\WA_MRG.MRG', dtype=np.dtype('uint8'))
    print('Opened files')
    if app != None:
        app.setMeter("progress", 10)
    
    with open('chartable.tbl') as chars:
        line = chars.readline()
        while line:
            index = int(line.split('=')[0], 16)
            charList[index] = line.split('=')[1][:-1]
            line = chars.readline()
    print('Parsed chartable')
    if app != None:
        app.setMeter("progress", 15)

    global cards
    cards = getCardData()
    print('Loaded basic card data')
    if app != None:
        app.setMeter("progress", 30)

    if app != None:
        getCardImageData()
    print('Loaded card thumbnails')
    if app != None:
        app.setMeter("progress", 100)

#Full work flow
def getFusionsFromImage(image):
    print('getting fusions...')
    #Get cards in hand from image
    matched = getCardsInImage(image)
    print('got cards in hand')

    #Get available fusion chains
    fusionList = []
    for card in range(len(matched)):
        newlist = matched[:]
        newlist.pop(card)
        fusionList.append(getFusionChain(matched[card], newlist, [matched[card]]))
    if app != None:
        app.setMeter("progress", 97)

    #Evaluate fusion chains and sort to get possible results in order of attack, then # of cards required
    fusions = []
    for l1 in fusionList:
        for chain in l1:
            fusions.append((evaluateFusion(chain), chain))
    fusions.sort(key = lambda x : cards[x[0]].attack - len(x[1]))

    print('obtained fusions from cards')
    if app != None:
        app.setMeter("progress", 99)

    #Format fusion chains and results into presentable format
    fusionDict = {}
    for fusion in fusions:
        if fusion[0] in fusionDict:
            if fusion[1] not in fusionDict[fusion[0]]:
                fusionDict[fusion[0]].append(fusion[1])
        else:
            fusionDict[fusion[0]] = [fusion[1]]
    
    nameDict = {}
    for result in fusionDict:
        nameDict[cards[result].getTitle()] = [ [cards[i].name for i in chain] for chain in fusionDict[result]]
    #Display and return results
    print(nameDict)
    if app != None:
        app.setMeter("progress", 100)
    return nameDict

def getChar(bt):
    if bt >= len(charList):
        print('byte out of bounds!', bt)
    return charList[bt]

def readName(addr):
    name = ""
    bts = ""
    for i in range(100):
        bt = game[addr+i]
        bts += str(bt)+" "
        if bt == 254:
            name += "\r\n"
        elif bt == 255:
            break
        else:
            name += getChar(bt)
        
    return (name, bts)

def getCardData():
    cards = []

    #Basic numerical card attributes
    addr = 0x1C4A44
    for i in range(722):
        cards.append(Card())
        #Get 32 bits (4 bytes) of data and unpack for card info
        cardData = int.from_bytes(game[addr:addr+4], byteorder='little', signed=False)
        addr += 4
        cards[i].card_id = i+1
        cards[i].attack = (cardData & 0x1FF) * 10
        cards[i].defense = (cardData >> 9 & 0x1FF) * 10
        cards[i].guardian_star_1 = cardData >> 18 & 0xF
        cards[i].guardian_star_2 = cardData >> 22 & 0xF
        cards[i].card_type = cardData >> 26 & 0x1F

    #Level and Attribute
    addr = 0x1C5B33
    for i in range(722):
        cards[i].level = game[addr] & 0xF
        cards[i].attribute = game[addr] >> 4 & 0xF
        addr += 1

    #Name
    addr = 0x1C6002
    for i in range(722):
        num = int.from_bytes(game[addr+i*2:addr+i*2+2], byteorder='little', signed=False)
        name, bts = readName(0x1C6800 + num - 0x6000)
        cards[i].name = name
    
    #Description
    for i in range(722):
        offset = int.from_bytes(game[0x1B0A02+i*2 : 0x1B0A02+i*2 + 2], byteorder='little', signed=False)
        descAddr = 0x1B11F4 + (offset - 0x9F4)
        name, bts = readName(descAddr)
        cards[i].description = name

    '''
    #Card Images
    addr = 0x169000
    imgSize = 102*96
    clutSize = 256*2
    for i in range(1):
        pixelStart = addr + i*14336
        pixels = mrg[pixelStart : pixelStart+imgSize]
        clut = mrg[pixelStart+imgSize : pixelStart+imgSize+clutSize]

        data = []
        for pixel in pixels:
            color = int.from_bytes(clut[pixel*2: pixel*2+2], byteorder='little', signed=False)
            red = color & 31
            green = (color >> 5) & 31
            blue = (color >> 10) & 31
            alpha = color >> 15
            
            data.append(np.uint8(red*8))
            data.append(np.uint8(green*8))
            data.append(np.uint8(blue*8))
            data.append(np.uint8(255))

        data = np.array(data, 'uint8')
        cards[i].image = data
        image = Image.frombytes('RGBA', (102,96), data, 'raw')
        #image.show()
    '''
    
    
    #Fusions

    addr = 0xB87800
    fuseDat = mrg[addr:addr+0x10000]
    for i in range(722):
        position = i*2 + 2
        fusionIndex = 0
        num = int.from_bytes(fuseDat[position : position+2], byteorder='little', signed=False)
        position = num & 0xFFFF

        if position != 0:
            fusionAmt = fuseDat[position]
            position += 1
            if fusionAmt == 0:
                fusionAmt = 511 - fuseDat[position]
                position += 1
            
            num2 = fusionAmt
            cards[i].fusionAmt = num2

            while num2 > 0:
                num3 = fuseDat[position]
                num4 = fuseDat[position+1]
                num5 = fuseDat[position+2]
                num6 = fuseDat[position+3]
                num7 = fuseDat[position+4]
                position += 5

                num9 = (num3 & 3) << 8 | num4#int.from_bytes([(num3 & 3), num4], byteorder='little', signed=False)
                num11 = (num3 >> 2 & 3) << 8 | num5#int.from_bytes([(num3 >> 2 & 3), num5], byteorder='little', signed=False)
                num13 = (num3 >> 4 & 3) << 8 | num6#int.from_bytes([(num3 >> 4 & 3), num6], byteorder='little', signed=False)
                num15 = (num3 >> 6 & 3) << 8 | num7#int.from_bytes([(num3 >> 6 & 3), num7], byteorder='little', signed=False)

                cards[i].fusions.append({})
                cards[i].fusions[-1]['card1'] = i #Current card's index
                cards[i].fusions[-1]['card2'] = num9-1
                cards[i].fusionMaterials.append(num9-1)
                cards[i].fusions[-1]['result'] = num11-1
                cards[i].fusionResults.append(num11-1)
                
                num2 -= 1
                if num2 <= 0: continue

                cards[i].fusions.append({})
                cards[i].fusions[-1]['card1'] = i #Current card's index
                cards[i].fusions[-1]['card2'] = num13-1
                cards[i].fusionMaterials.append(num13-1)
                cards[i].fusions[-1]['result'] = num15-1
                cards[i].fusionResults.append(num15-1)

                num2 -= 1
        
    return cards

def getCardImageData():
    #Card Thumbnails
    addr = 0x16BAE0
    imgSize = 40*32
    clutSize = 256*2
    for i in range(722):
        if i % 100 == 0 and app != None:
            print('loading thumbnail ',i)
            app.setMeter("progress", 30+i/10)
        pixelStart = addr + i*14336
        pixels = mrg[pixelStart : pixelStart+imgSize]
        clut = mrg[pixelStart+imgSize : pixelStart+imgSize+clutSize]

        data = []
        for pixel in pixels:
            color = int.from_bytes(clut[pixel*2: pixel*2+2], byteorder='little', signed=False)
            red = color & 31
            green = (color >> 5) & 31
            blue = (color >> 10) & 31
            alpha = color >> 15
            
            data.append(np.uint8(red*8))
            data.append(np.uint8(green*8))
            data.append(np.uint8(blue*8))
            data.append(np.uint8(255))

        '''
        imgdata = np.ndarray((4, 40, 32))
        for col in range(len(data)):
            x = col%3
            y = int(col/3)%40
            z = int(col/120)%32
            imgdata[x][y][z] = data[col]
        '''

        data = np.array(data, 'uint8')
        image = Image.frombytes('RGBA', (40,32), data, 'raw')
        imgdata = cv.cvtColor(np.array(image), cv.COLOR_BGR2GRAY)
        cards[i].thumbnail = imgdata
    print('finished loading card thumbnails')


def getCardsInImage(img_rgb):
    matchedCards = []
    img_rgb = cv.resize(img_rgb, (320, 240), interpolation = cv.INTER_AREA)
    img_gray = cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)
    w, h = cards[0].thumbnail.shape[::-1]
    if app != None:
        app.setMeter("progress", 30)
    for card in cards:
        res = cv.matchTemplate(img_gray, card.thumbnail, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.8)
        if card.card_id % 100 == 0 and app != None: 
            print('checked card ', card.card_id)
            app.setMeter("progress", 25+card.card_id/10)
        points = []
        for pt in zip(*loc[::-1]):
            inList = False
            for point in points:
                if (point[0] - 10 < pt[0] and point[0] + 10 > pt[0]) and (point[1] - 10 < pt[1] and point[1] + 10 > pt[1]):
                    inList = True
                    break
            if not inList:
                points.append(pt)
                matchedCards.append(card.card_id-1)
                print('Found card: ', card.name, ' at point: ', pt)
    print('finished searching for images')
    return matchedCards


def imageDataToCV(data, w, h):
    image = Image.frombytes('RGBA', (w,h), data, 'raw')
    imgdata = cv.cvtColor(np.array(image), cv.COLOR_BGR2GRAY)
    return imgdata

def getFusionsList(hand, fusionList=[]):
    for i in range(len(hand)):
        myhand = hand[:]
        myhand.pop(i)
        card = hand[i]

        for j in range(len(myhand)):
            if myhand[j] in cards[card].fusionMaterials:
                result = cards[card].fusionResults[cards[card].fusionMaterials.index(myhand[j])]
                fusionList.append((card, myhand[j], result))
                newhand = myhand[:]
                newhand.pop(j)
                newhand.append(result)
                getFusionsList(cards, newhand, fusionList)

def getFusionChain(mycard, hand, fusionChain=[]):
    if len(hand) == 0 or (len(cards[mycard].fusionResults) == 0):
        return [fusionChain]
    #print(mycard, len(cards), [i for i in hand])
    #print(mycard, cards[mycard].name,': ' ,[cards[i].name for i in hand])
    fusions = []
    #fusionChain.append(mycard)
    isFusion = False
    for j in range(len(hand)):
         if hand[j] in cards[mycard].fusionMaterials or mycard in cards[hand[j]].fusionMaterials:
            isFusion = True
            if mycard in cards[hand[j]].fusionMaterials:
                result = cards[hand[j]].fusionResults[cards[hand[j]].fusionMaterials.index(mycard)]
            else:
                result = cards[mycard].fusionResults[cards[mycard].fusionMaterials.index(hand[j])]
            
            newhand = hand[:]
            newhand.pop(j)
            
            newchain = fusionChain[:]
            newchain.append(hand[j])

            fusions += getFusionChain(result, newhand, newchain)
    fusions.append(fusionChain)
    return fusions

def evaluateFusion(fusionChain):
    card = fusionChain[0]
    fusionChain = fusionChain[1:]
    while len(fusionChain) > 0:
        card2 = fusionChain[0]
        fusionChain.pop(0)
        if card in cards[card2].fusionMaterials: result = cards[card2].fusionResults[cards[card2].fusionMaterials.index(card)]
        else: result = cards[card].fusionResults[cards[card].fusionMaterials.index(card2)]
        card = result
    return card
        
def printChain(fusionChain, result):
    for card in chain:
        print(cards[card].name, end=" + ")
    print(' = ', cards[result].name)


def findMaterials(result):
    for card in cards:
        if result in card.fusionResults:
            return (card.card_id, card.fusionMaterials[card.fusionResults.index(result)])
    return None

def findAllMaterials(result):
    chain = [[result]]
    while not all(v is None for v in chain[-1]):
        materials = [findMaterials(card) for card in chain[-1]]
        chain.append(materials)
    return chain

def findBestFusion():
    '''
    products = set()
    for card in cards:
        for result in card.fusionResults:
            products.add(result)
    print(products)
    global nonFusers
    nonFusers = []
    for card in cards:
        if card.card_id-1 not in products:
            nonFusers.append(card.card_id-1)
    print(nonFusers)
    '''
    nonFusers = [i for i in range(722)]
    #Get available fusion chains
    fusionList = []
    for card in range(len(nonFusers)):
        newlist = nonFusers[:]
        newlist.pop(card)
        fusionList.append(getFusionChain(nonFusers[card], newlist, [nonFusers[card]]))
    if app != None:
        app.setMeter("progress", 97)

    #Evaluate fusion chains and sort to get possible results in order of attack, then # of cards required
    fusions = []
    for l1 in fusionList:
        for chain in l1:
            fusions.append((evaluateFusion(chain), chain))
    fusions.sort(key = lambda x : cards[x[0]].attack - len(x[1]))

    print('obtained fusions from cards')
    if app != None:
        app.setMeter("progress", 99)

    #Format fusion chains and results into presentable format
    fusionDict = {}
    for fusion in fusions:
        if fusion[0] in fusionDict:
            if fusion[1] not in fusionDict[fusion[0]]:
                fusionDict[fusion[0]].append(fusion[1])
        else:
            fusionDict[fusion[0]] = [fusion[1]]
    
    nameDict = {}
    for result in fusionDict:
        nameDict[cards[result].getTitle()] = [ [cards[i].name for i in chain] for chain in fusionDict[result]]
    #Return results
    if app != None:
        app.setMeter("progress", 100)
    return nameDict
    

class Card:

    def __init__(self):
        self.card_id = 0
        self.name = ""
        self.attack = 0
        self.defense = 0
        self.guardian_star_1 = 0
        self.guardian_star_2 = 0
        self.card_type = 0

        self.level = 0
        self.attribute = 0
        self.description = ""

        self.image = None
        self.thumbnail = None

        self.fusionAmt = 0 #number of fusions
        self.fusions = []
        self.fusionMaterials = []
        self.fusionResults = []

    def __str__(self):
        return str(self.card_id)+": "+self.name+" ("+str(self.card_type)+")\nA/D: "+str(self.attack)+" | "+str(self.defense)+"\n"+str(self.description)
    
    def getTitle(self):
        return self.name+' ('+str(self.attack)+' | '+str(self.defense)+')\t'+gstarNames[self.guardian_star_1]+' | '+gstarNames[self.guardian_star_2]

if __name__ == '__main__':
    loadData('data\\reimagined', None)
    fusionData = findBestFusion()
    resultText = ""
    for result in fusionData.keys():
        resultText += result+":\n"
        for chain in fusionData[result]:
            resultText += "\t"+str(chain)
            resultText += "\n"
    print(resultText)

'''
if __name__ == '__main__':
    cardList = getCardData()
    #getCardImageData(cardList)
    for fusion in cardList[1].fusions:
        print(cardList[fusion['card1']-1].name, ' + ', cardList[fusion['card2']].name, ' = ', cardList[fusion['result']].name)
    #matched = getCardsInImage(cardList, cv.imread('ygofmhand.jpg'))
    matched = [199, 199, 74, 59, 457]
    for card in matched:
        print(cardList[card].name)
    fusionList = []
    for card in range(len(matched)):
        newlist = matched[:]
        newlist.pop(card)
        fusionList.append(getFusionChain(cardList, matched[card], newlist, [matched[card]]))
    #getFusionsList(cardList, matched, fusionList)
    
    fusions = []
    for l1 in fusionList:
        for chain in l1:
            fusions.append((evaluateFusion(cardList, chain), chain))
    
    fusions.sort(key = lambda x : cardList[x[0]].attack - len(x[1]))
    
    print(fusions)
    print([cardList[fusion[0]].name for fusion in fusions])

    getCardImageData(cardList)
    getFusionsFromImage(cardList, cv.imread('ygofmhand.jpg'))
'''