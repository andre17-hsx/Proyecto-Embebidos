
import ipywidgets as widgets
import mysql.connector
import cv2
import imutils
import numpy as np
import pytesseract
import matplotlib.pyplot as plt
from PIL import Image
import RPi.GPIO as GPIO


from time import sleep

GPIO.setmode(GPIO.BCM)
led1= 12
led2= 6
GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)

servo = 17
GPIO.setup(servo, GPIO.OUT)
p = GPIO.PWM(servo, 50) # GPIO 17 for PWM with 50Hz
p.start(7.5) # Initialization

uploader = widgets.FileUpload()
display(uploader)

uploader.value
uploaded_file = uploader.value[0]
with open("./saved-output.jpg", "wb") as fp:
    fp.write(uploaded_file.content)

widgets.Image(value=uploaded_file.content.tobytes())

#TEXT DTECTION 
img = cv2.imread('./saved-output.jpg',cv2.IMREAD_COLOR)

img = cv2.resize(img, (620,480) )

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert to grey scale
gray = cv2.bilateralFilter(gray, 11, 17, 17) #Blur to reduce noise
edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

# find contours in the edged image, keep only the largest
# ones, and initialize our screen contour
cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
screenCnt = None

# loop over our contours
for c in cnts:
 # approximate the contour
 peri = cv2.arcLength(c, True)
 approx = cv2.approxPolyDP(c, 0.018 * peri, True)
 
 # if our approximated contour has four points, then
 # we can assume that we have found our screen
 if len(approx) == 4:
  screenCnt = approx
  break

 

if screenCnt is None:
 detected = 0
 print ("No contour detected")
else:
 detected = 1

if detected == 1:
 cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

# Masking the part other than the number plate
mask = np.zeros(gray.shape,np.uint8)
new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
new_image = cv2.bitwise_and(img,img,mask=mask)

# Now crop
(x, y) = np.where(mask == 255)
(topx, topy) = (np.min(x), np.min(y))
(bottomx, bottomy) = (np.max(x), np.max(y))
Cropped = gray[topx:bottomx+1, topy:bottomy+1]

#Read the number plate
text = pytesseract.image_to_string(Cropped, config='-l eng --oem 1 --psm 12')
print("La placa detectada es:",text)

#cv2.imshow('image',img)
#cv2.imshow('Cropped',Cropped)

#print(img)
#print(Cropped)

#cv2.waitKey(0)
#cv2.destroyAllWindows()

plt.imshow(img)
plt.title('Imagen')
plt.show

plt.imshow(Cropped)
plt.title('Placa detectada')
plt.show

#Listado de todas las tablas de una base de datos de MySQL.
conexion1=mysql.connector.connect(host="localhost", 
                                  user="admin", 
                                  passwd="1234", 
                                  database="vehiculos")

cursor1=conexion1.cursor()
cursor1.execute("select placa from app_autos_vehiculo")

linea = text.rstrip()
resultado = False
for fila in cursor1:
    if linea == fila[0]:
        resultado = True
conexion1.close() 

if resultado:
    print("La placa " + linea + " se encuentra registrada en el sistema")
    GPIO.output(led1,True)
    p.ChangeDutyCycle(2.5)
    sleep(3)
    GPIO.output(led1,False)
    p.ChangeDutyCycle(7.5)
else:
    print("La placa " + linea + " no se encuentra registrada en el sistema")
    GPIO.output(led2,True)
    sleep(3)
    GPIO.output(led2,False)

p.ChangeDutyCycle(0)
GPIO.cleanup()
