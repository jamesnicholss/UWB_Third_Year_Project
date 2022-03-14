# James Nichols 6527678 (UWB Project University of Surrey)

import pygame  # 2D Graphics Engine
from pygame.locals import *
import redis  # Database
import paho.mqtt.client as mqtt  # Controls IoT Devices

pygame.init()
clock = pygame.time.Clock()
# Sets Application Title and Icon
pygame.display.set_caption("Precise Realtime Indoor Localisation using Ultra-Wideband Technology")  # Sets Window Title
programIcon = pygame.image.load(r"C:\\Users\James\Documents\Uni\3rd Year\Sem2\YEAR 3 PROJECT\UWB_Project\Images\UWB.png")
pygame.display.set_icon(programIcon)  # Sets Window Icon
# Application Fonts
font = pygame.font.Font(None, 24)
fontLarge = pygame.font.Font(None, 32)
fontTitle = pygame.font.Font(None, 45)

# Redis Database Set-Up
r = redis.Redis(host='192.168.1.8', port=6379, db=0)
# MQTT Set-Up
mqttBroker = "192.168.1.8"
client = mqtt.Client("UWB_Application")
client.connect(mqttBroker, 1883, keepalive=600)

class TextBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.colour = pygame.Color(140,180,200)
        self.text = text
        self.active = False
        self.textSurface = fontLarge.render(text, True, self.colour)
    def tbEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):  # If the user clicks on an textbox
                self.active = True
                self.colour = pygame.Color(0,155,230)  # Active Colour
            else:
                self.active = False
                self.colour = pygame.Color(140,180,200)  # Inactive Colour
        if event.type == pygame.KEYDOWN:
            if self.active:
                # When a backspace is pressed remove the last characture
                if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
                elif len(self.text)<20: self.text += event.unicode  # Limits to 15 charactures
                self.textSurface = fontLarge.render(self.text, True, self.colour)  # Re-render the text
    def tbDraw(self, screen):
        screen.blit(self.textSurface, (self.rect.x+5, self.rect.y+5))  # Blit the text
        pygame.draw.rect(screen, self.colour, self.rect, 2)  # Blit the rect 
    def tbUpdate(self):  # Resize the box if the text is too long.
        width = max(190, self.textSurface.get_width()+10)
        self.rect.w = width

# Allows Text to be written to the Screen
def draw_text(text, font, colour, screen, x, y):
    textobj = font.render(text, 1, colour)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    screen.blit(textobj, textrect)

def mainScreen():
    # Main Screens Variables
    tagSizee = 10  # Pixel size of the tag
    node = 2  # Default anchor for calculating distance of the tag
    click = 0  # Click has been detected each frame
    selected = 0  # State of MQTTArea button
    waitClick = 0  # Records the number of clicks for MQTTArea
    hideMQTTArea = 0  # Show/Hide MQTTArea
    stateMQTT = 0  # State of MQTT value
    # Restores MQTTArea position
    mqttAreaXm = int(r.get('mqttAreaX'))
    mqttAreaYm = int(r.get('mqttAreaY'))
    mqttAreaXm2 = int(r.get('mqttAreaX2'))
    mqttAreaYm2 = int(r.get('mqttAreaY2'))
    screenInitialise = 1  # Used to initialise the screen
    
    # Testing Variables
    x = 250  # Start x position of tag
    y = 250  # Start y position of tag
    vel = 5  # Velocity of tag for arrow keys
    manual = 1  # Testing
    # While loop that represent each frame of the screen
    while True:
        if screenInitialise>=1: # Called once when the screen starts and every time the screen size changes
            width = int(r.get('width'))  # Calls the width of the tag area from DB
            height = int(r.get('height'))  # Calls the length of the tag area from DB
            if (1400/width)>(600/height): scaleFactor = 600/height  # Checks which distance is screen limited first
            else: scaleFactor = 1400/width
            borderSize=150  # Area around the tagArea
            width = int(width*scaleFactor+(borderSize*2))  # Calculate actual size of the screen
            height = int(height*scaleFactor+(borderSize*2))
            screen = pygame.display.set_mode((width, height))  # Creates a screen object
            # Used to simplify the program
            tagArea = borderSize - (tagSizee/2)
            tagAreaLength = width-(2*tagArea)
            tagAreaWidth = height-(2*tagArea)
            # Loads and transforms the background image
            roomOverlay = pygame.image.load(r'C:\Users\James\Documents\Uni\3rd Year\Sem2\YEAR 3 PROJECT\UWB_Project\Images\overlay.png')
            roomOverlay = pygame.transform.scale(roomOverlay, (int(tagAreaLength),int(tagAreaWidth)))  # Fits background image to tagArea
            # MQTT Info Update
            roomName = r.get('roomName').decode()
            MQTT_Topic = r.get('MQTT_Topic').decode()
            MQTT_Message = r.get('MQTT_Message').decode()
            MQTT_Message2 = r.get('MQTT_Message2').decode()
            if screenInitialise==2:  # Hides MQTTArea if the screen changes size
                hideMQTTArea = 1
            screenInitialise = 0  # Ensures only performs once
        
        if manual==0:
            # Redis DB holding most recent tag location
            tagInput = r.get('pos')  # Retrieves location data stored in Redis DB named 'pos'
            tagInput = tagInput.replace('"'.encode(), ''.encode())  # Removes '"'
            tagInput = (tagInput.decode().split(","))  # Splits DB entry by ','
            x = int((int(tagInput[1]) * scaleFactor) + tagArea)  # Indexes to extract location data &
            y = int((int(tagInput[3]) * scaleFactor) + tagArea)  # converts cm to pixels
            y = height - y
        else:
            # Manual tag sprite control for testing
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                x -= vel
            if keys[pygame.K_RIGHT]:
                x += vel
            if keys[pygame.K_UP]:
                y -= vel
            if keys[pygame.K_DOWN]:
                y += vel

        screen.fill((255,255,255))  # Creates white background colour
        draw_text(roomName, fontTitle, (0, 0, 0), screen, 60, 40)  # Draws screen title
        screen.blit(roomOverlay, (tagArea, tagArea)) # Adds floor plan image to the screen
        tagBoxArea = pygame.Rect(tagArea, tagArea, tagAreaLength, tagAreaWidth)
        mx, my = pygame.mouse.get_pos()  # Gets mouse position
        
        # Calculates Users Position (Converts pixel count to meters)
        if node == 1:  # Top Left Anchor
            tagX = round((((x - tagArea) / scaleFactor) / 100),2)  
            tagY = round((((y - tagArea) / scaleFactor) / 100),2)
        elif node == 2:  # Bottom Left Anchor
            tagX = round((((x - tagArea) / scaleFactor) / 100),2)
            tagY = round((((height - borderSize - (tagSizee/2) - y) / scaleFactor) / 100),2)
        elif node == 3:  # Top Right Anchor
            tagX = round((((width - borderSize - (tagSizee/2) - x) / scaleFactor) / 100),2)  
            tagY = round((((y - tagArea) / scaleFactor) / 100),2)
        elif node == 4:  # Bottom Right Anchor
            tagX = round((((width - borderSize - (tagSizee/2) - x) / scaleFactor) / 100),2)  
            tagY = round((((height - borderSize - (tagSizee/2) - y) / scaleFactor) / 100),2)
        distenceOfTag=('Position ( '+str(tagX) +'m, '+str(tagY)+'m )')  # Formulates the text for distance of the tag
        draw_text(str(distenceOfTag), fontLarge, (0, 0, 0), screen, ((width/2)-120), height-75)  # Displays position of tag
        
        # Options Button
        inactiveColour=(169,169,169)
        activeColour=(200,200,200)
        buttonX = width-200
        buttonY = height-80
        optionButton = pygame.Rect(buttonX, buttonY, 150, 40)  # Option button size and position
        if optionButton.collidepoint(mx, my):  # Button changes colour when mouse is hovering over
            colourChoise=activeColour
            if click:  # If Options Button is moused over and clicked open the options screen
                screenInitialise=optionScreen()  # Takes value returned from optionscreen
        else: colourChoise=inactiveColour
        pygame.draw.rect(screen, colourChoise, optionButton, border_radius=10)  # Draws Option Button
        draw_text('Options Menu', font, (0,0,0), screen, buttonX+20, buttonY+12)  # Draws Option Button Text

        # MQTT Button
        selectedColour=(255,0,0)
        buttonY = 40  # Used x from option button
        optionButton = pygame.Rect(buttonX, buttonY, 150, 40)  # MQTT button size and position
        if optionButton.collidepoint(mx, my):
            if selected==0: colourChoise=activeColour  # If MQTT Button is moused over &
            if click:  # clicked the program will record the users next click position
                waitClick=1
                selected=1
        elif selected==0: colourChoise=inactiveColour
        elif selected==1: colourChoise=selectedColour
        pygame.draw.rect(screen, colourChoise, optionButton, border_radius=10)  # Draws MQTT Button
        draw_text('Activation Area', font, (0,0,0), screen, buttonX+14, buttonY+12)  # Draws MQTT Button Text

        # User drawable MQTTArea 
        if waitClick==2:  # Waiting for the second click for MQTTArea
            if tagBoxArea.collidepoint(mx, my):  # Only draw MQTTArea inside the tag area
                if click:  # Second Click
                    if (mqttAreaXm-mx>20) or (mqttAreaXm-mx<-20): # Prevents double clicks
                        mqttAreaXm2=mx  # Sets second corner of the MQTTArea rectangle to the current mouse coordinates
                        mqttAreaYm2=my
                        r.set('mqttAreaX', mqttAreaXm)  # Stores new MQTTArea coordinates to database
                        r.set('mqttAreaY', mqttAreaYm)
                        r.set('mqttAreaX2', mqttAreaXm2)
                        r.set('mqttAreaY2', mqttAreaYm2)
                        waitClick=0  # Program is no longer waiting for a click
                        selected=0  # Changes button colour back to unselected
                        hideMQTTArea=0  # When a new MQTTArea is drawn, unhide MQTTArea
            # Uses first MQTT click coordinates and current mouse coordinates
            MQTTArea = pygame.Rect(mqttAreaXm,mqttAreaYm,mx-mqttAreaXm,my-mqttAreaYm)
            pygame.draw.rect(screen, (0,0,0), MQTTArea, width=2, border_radius=5)  # Draws temporary area that follows mouse cursor
        else:
            if hideMQTTArea==0:
                MQTTArea = pygame.Rect(mqttAreaXm, mqttAreaYm, mqttAreaXm2-mqttAreaXm, mqttAreaYm2-mqttAreaYm)  # Draws Final MQTTArea outline
                pygame.draw.rect(screen, (0,0,0), MQTTArea, width=2, border_radius=5)
                # Initialises transparent MQTTArea layer
                t1=abs(mqttAreaXm2-mqttAreaXm)
                t2=abs(mqttAreaYm2-mqttAreaYm)
                areaTL = pygame.Surface((t1,t2))  # Size of translucent MQTTArea
                areaTL.set_alpha(128)  # Set to 50% transparent
                areaTL.fill((255,0,0))  # Sets the surface to red
            if waitClick==1:  # If the MQTT button has been pressed
                if tagBoxArea.collidepoint(mx, my):  # If the current mouse position is inside the UWB area
                    if click:  # If the user clicks it stores the current mouse position
                        mqttAreaXm=mx
                        mqttAreaYm=my
                        waitClick=2  # Increment wait click for the second mouse click
        
        # MQTT Control
        if waitClick!=2:  # Checks the box has been drawn
            if mqttAreaXm2-mqttAreaXm>1:  # Depending on how the user drew the box
                if mqttAreaYm2-mqttAreaYm>1:
                    if (x>mqttAreaXm)and(y>mqttAreaYm)and(x<mqttAreaXm2-tagSizee)and(y<mqttAreaYm2-tagSizee):insideArea=1
                    else: insideArea=0  # Draw Top Left to Bottom Right
                    if hideMQTTArea == 0: screen.blit(areaTL, (mqttAreaXm,mqttAreaYm))  # Overlays transparent MQTTArea to screen
                else:
                    if (x>mqttAreaXm)and(y<mqttAreaYm-tagSizee)and(x<mqttAreaXm2-tagSizee)and(y>mqttAreaYm2):insideArea=1
                    else: insideArea=0  # Draw Bottom Left to Top Right
                    if hideMQTTArea == 0: screen.blit(areaTL, (mqttAreaXm,mqttAreaYm2))
            else:
                if mqttAreaYm2-mqttAreaYm<1:
                    if (x<mqttAreaXm-tagSizee)and(y<mqttAreaYm-tagSizee)and(x>mqttAreaXm2)and(y>mqttAreaYm2):insideArea=1
                    else: insideArea=0  # Draw Bottom Right to Top Left
                    if hideMQTTArea == 0: screen.blit(areaTL, (mqttAreaXm2,mqttAreaYm2))
                else:
                    if (x<mqttAreaXm-tagSizee)and(y>mqttAreaYm)and(x>mqttAreaXm2)and(y<mqttAreaYm2-tagSizee):insideArea=1
                    else: insideArea=0  # Draw Top Right to Bottom Left
                    if hideMQTTArea == 0: screen.blit(areaTL, (mqttAreaXm2,mqttAreaYm))
            if ((stateMQTT == 0) and (insideArea == 1)):
                stateMQTT = 1
                client.publish(MQTT_Topic, MQTT_Message)
            if ((stateMQTT == 1) and (insideArea == 0)):
                stateMQTT = 0
                client.publish(MQTT_Topic, MQTT_Message2)
        
        # Interactive Anchors
        activeColour = (255,0,0)
        inactiveColour = (0,0,255)
        anchor1 = pygame.Rect(tagArea-20, tagArea-20, 40, 40)  # Interactable area for anchors
        anchor2 = pygame.Rect(tagArea-20, height-tagArea-20, 40, 40)
        anchor3 = pygame.Rect(width-tagArea-20, tagArea-20, 40, 40)
        anchor4 = pygame.Rect(width-tagArea-20, height-tagArea-20, 40, 40)
        if anchor1.collidepoint(mx, my):  # If a user hovers mouse above anchor1
            anchorColour1 = activeColour  # Changes the colour to the active colour
            if click: node = 1 # If a user left clicks the interacted anchor then its selected
        else: anchorColour1 = inactiveColour  # If a user isn't interacting with anchor1 the colour is set to default
        if anchor2.collidepoint(mx, my):
            anchorColour2 = activeColour
            if click: node = 2
        else: anchorColour2 = inactiveColour
        if anchor3.collidepoint(mx, my):
            anchorColour3 = activeColour
            if click: node = 3
        else: anchorColour3 = inactiveColour
        if anchor4.collidepoint(mx, my):
            anchorColour4 = activeColour
            if click: node = 4
        else: anchorColour4 = inactiveColour
        
        # Draws Anchors and Tag to the screen
        pygame.draw.circle(screen, anchorColour1, (tagArea,tagArea), 20)
        pygame.draw.circle(screen, anchorColour2, (tagArea,height-tagArea), 20)
        pygame.draw.circle(screen, anchorColour3, (width-tagArea,tagArea), 20)
        pygame.draw.circle(screen, anchorColour4, (width-tagArea,height-tagArea), 20)
        pygame.draw.rect(screen, (255,0,0), (x, y, tagSizee, tagSizee), border_radius=2)  # Draws the tag that moved round the screen
        
        # Event Handling
        click = False
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit()  # Quits if the window is closed
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if selected >= 1: # Pressing Escape Key during the drawing of a new MQTTArea allows for cancelation
                        waitClick=0
                        selected=0
                        mqttAreaXm = int(r.get('mqttAreaX')) #Reverts back to first click coordinates
                        mqttAreaYm = int(r.get('mqttAreaY'))
                    else: pygame.quit()  # Quits if the escape key is pressed
                elif event.key == K_f:
                    roomOverlay = pygame.transform.flip(roomOverlay, True, False)  # Flips image along y axis if 'F' key is pressed
                elif event.key == K_v:
                    roomOverlay = pygame.transform.flip(roomOverlay, False, True)  # Flips image along x axis if 'V' key is pressed
                elif event.key == K_h:
                    hideMQTTArea ^= 1  # Bit flips every time 'H' key is pressed to hide MQTTArea
            if event.type == MOUSEBUTTONDOWN:  # Checks if a user presses the left click button this frame
                if event.button == 1:
                    click = True
        pygame.display.update()  # Updates the applications display
        clock.tick(45)  # Limits the screens update rate to 60 times per-second

def optionScreen():
    # Calculates screen size
    heightO = int(r.get('height'))
    widthO = int(r.get('width'))
    if (1400/widthO)>(600/heightO): scaleFactor = 600/heightO
    else: scaleFactor = 1400/widthO
    borderSize=150  # Border Size
    width = int(widthO * scaleFactor + (borderSize*2))
    height = int(heightO * scaleFactor + (borderSize*2))
    screen = pygame.display.set_mode((width, height))  # Creates a screen object
    
    # Database Values
    roomName = r.get('roomName').decode()
    MQTT_Topic = r.get('MQTT_Topic').decode()
    MQTT_Message = r.get('MQTT_Message').decode()
    MQTT_Message2 = r.get('MQTT_Message2').decode()
    
    # Centres Contents of the Input Screen
    offset_X=(width/2)-400
    offset_Y=(height/2)-120
    # Text input boxes size and positions
    roomWidthBox = TextBox(offset_X+160, offset_Y+72, 140, 32)
    roomHeightBox = TextBox(offset_X+160, offset_Y+120, 140, 32)
    roomNameBox = TextBox(offset_X+160, offset_Y+168, 140, 32)
    MQTT_TopicBox = TextBox(offset_X+500, offset_Y+72, 140, 32)
    MQTT_MessageBox = TextBox(offset_X+500, offset_Y+120, 140, 32)
    MQTT_MessageBox2 = TextBox(offset_X+500, offset_Y+168, 140, 32)
    inputBoxes = [roomWidthBox, roomHeightBox, roomNameBox, MQTT_TopicBox, MQTT_MessageBox, MQTT_MessageBox2]
    
    
    click = False
    running = True
    while running:  # While loop that represent each frame of the screen
        # Draws Backgrounds
        screen.fill((255,255,255))  # Creates a white background
        backgroundColour = pygame.Rect(offset_X, offset_Y-20, 800, 330)
        pygame.draw.rect(screen, (240,240,240), backgroundColour, border_radius=10)  #Filled Box
        pygame.draw.rect(screen, (0,0,0), backgroundColour, width=1, border_radius=10)  #Border
        
        #Draws Screen Elements
        draw_text('Options Menu', fontTitle, (0, 0, 0), screen, 60, 40)
        draw_text('Input Room Size (cm):', fontLarge, (0,0,0), screen, offset_X+80, offset_Y+20)
        draw_text('Width:', font, (0,0,0), screen, offset_X+101, offset_Y+80)
        draw_text('Height:', font, (0,0,0), screen, offset_X+93, offset_Y+128)
        draw_text('Room Name:', font, (0,0,0), screen, offset_X+53, offset_Y+176)
        draw_text('MQTT IoT Device Settings:', fontLarge, (0,0,0), screen, offset_X+400, offset_Y+20)
        draw_text('Topic: ', font, (0,0,0), screen, offset_X+444, offset_Y+80)
        draw_text('Activate MSG:', font, (0,0,0), screen, offset_X+380, offset_Y+128)
        draw_text('Deactivate MSG:', font, (0,0,0), screen, offset_X+365, offset_Y+176)
        
        # Overlays current values over text boxes
        if (roomWidthBox.active == False) and (roomWidthBox.text == ""):
            draw_text(str(widthO), fontLarge, (169,169,169), screen, offset_X+165, offset_Y+77)
        if (roomHeightBox.active == False) and (roomHeightBox.text == ""):
            draw_text(str(heightO), fontLarge, (169,169,169), screen, offset_X+165, offset_Y+125)
        if (roomNameBox.active == False) and (roomNameBox.text == ""):
            draw_text(str(roomName), fontLarge, (169,169,169), screen, offset_X+165, offset_Y+173)
        if (MQTT_TopicBox.active == False) and (MQTT_TopicBox.text == ""):
            draw_text(str(MQTT_Topic), fontLarge, (169,169,169), screen, offset_X+505, offset_Y+77)
        if (MQTT_MessageBox.active == False) and (MQTT_MessageBox.text == ""):
            draw_text(str(MQTT_Message), fontLarge, (169,169,169), screen, offset_X+505, offset_Y+125)
        if (MQTT_MessageBox2.active == False) and (MQTT_MessageBox2.text == ""):
            draw_text(str(MQTT_Message2), fontLarge, (169, 169, 169), screen, offset_X+505, offset_Y+173)
        
        # Check if width & height text boxes contain integers
        try :
            check = int(roomWidthBox.text)
            check = int(roomHeightBox.text)
            errorCheck = 0
        except ValueError:
            errorCheck = 1
        
        # Update Size Button
        inactiveColour = (169,169,169)  # Default button colour
        activeColourT = (0,255,0)  # Colour when contents are accepted
        activeColourF = (255,0,0)  # Colour when contents are not accepted
        mx, my = pygame.mouse.get_pos()  # Gets mouse position
        buttonX = offset_X+160
        buttonY = offset_Y+230
        sizeButton = pygame.Rect(buttonX, buttonY, 140, 40)  # Input button size and position
        
        if sizeButton.collidepoint((mx, my)):
            # If text boxes contain integers of values between 1m and 10m
            if ((errorCheck == 0) and (int(roomWidthBox.text)<=1000 and int(roomWidthBox.text)>=100) and 
                (int(roomHeightBox.text)<=1000 and int(roomHeightBox.text)>=100) and (roomNameBox.text!="")):
                colourChoise = activeColourT  # Colour of button if contents are correct and moused over
                if click == True:
                    if (int(roomWidthBox.text) > int(roomHeightBox.text)):  # Makes the larger number the width
                        r.set('width', roomWidthBox.text)
                        r.set('height', roomHeightBox.text)
                    else:
                        r.set('width', roomHeightBox.text)
                        r.set('height', roomWidthBox.text)
                    r.set('roomName', roomNameBox.text)
                    return(2)  # Returns a value of 2 to mainScreen
            else: colourChoise = activeColourF  # Colour of button if contents are incorrect and moused over
        else: colourChoise = inactiveColour  # Colour of button when not interacted with by user
        pygame.draw.rect(screen, colourChoise, sizeButton, border_radius=5)  # Adds button to screen
        draw_text('Update Size', font, (0,0,0), screen, buttonX+22, buttonY+12)  # Adds text over button
        
        # MQTT Settings Button
        buttonX = offset_X+500
        MQTTButton = pygame.Rect(buttonX, buttonY, 140, 40)  # Option button size and position
        
        if MQTTButton.collidepoint(mx, my):  # Button becomes active when interacting with
            if not (MQTT_TopicBox.text=="" or MQTT_MessageBox.text=="" or MQTT_MessageBox2.text==""):
                colourChoise=activeColourT
                if click == True:
                    r.set('MQTT_Topic', MQTT_TopicBox.text)  # Saves contents to DB
                    r.set('MQTT_Message', MQTT_MessageBox.text)
                    r.set('MQTT_Message2', MQTT_MessageBox2.text)
                    return(1)  # Returns a value of 1 to mainScreen
            else: colourChoise = activeColourF
        else: colourChoise = inactiveColour
        
        pygame.draw.rect(screen, colourChoise, MQTTButton, border_radius=5)  # Draws Option Button
        draw_text('Update MQTT', font, (0,0,0), screen, buttonX+16, buttonY+12)  # Draws Option Button Text
        
        # Event Handling
        click = False
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:  # Press the escape key returns back to the mainScreen
                    running = False
                    return(0)  # Returns a value of 0 to mainScreen
            if event.type == MOUSEBUTTONDOWN:  # Checks if a user presses the left click button this frame
                if event.button == 1:
                    click = True
            for currentBox in inputBoxes: currentBox.tbEvent(event)
        for currentBox in inputBoxes:
            currentBox.tbUpdate()  # Updates the text boxes
            currentBox.tbDraw(screen)   # Adds the text boxes to the screen
        pygame.display.update()  # Updates the applications display
        clock.tick(30)  # Limits the screens update rate to 30 times per-second

mainScreen()