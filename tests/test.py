import cv2
import numpy as np

def get_borders(im1):
    #im1 = cv2.imread(file, 0)
    #im = cv2.imread(file)
    im = np.zeros((6000,4500,3), dtype=np.uint8)

    ret,thresh_value = cv2.threshold(im1,180,255,cv2.THRESH_BINARY_INV)

    kernel = np.ones((5,5),np.uint8)
    dilated_value = cv2.dilate(thresh_value,kernel,iterations = 1)

    contours, hierarchy = cv2.findContours(dilated_value,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    cordinates = [] 
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        cordinates.append((x,y,w,h))
        #bounding the images
        if h > 400 and h < 1000:
            print(x,y,w,h)
            im = cv2.rectangle(im,(x,y),(x+w,y+h),(0,0,255),1)

    #cv2.imshow('d', im)
    #k = cv2.waitKey(0)
    cv2.imwrite("detected.jpg", im) 
    
    return 

file =  r'10.jpg'
im1 = cv2.imread(file, 0)
get_borders(im1)
#breakpoint()