import cv2
import numpy as np
import pytesseract

def get_boxes(im1):
    #im1 = cv2.imread(file, 0)
    #im = cv2.imread(file)
    im = np.zeros((6000,4500,3), dtype=np.uint8)

    ret,thresh_value = cv2.threshold(im1,180,255,cv2.THRESH_BINARY_INV)

    kernel = np.ones((5,5),np.uint8)
    dilated_value = cv2.dilate(thresh_value,kernel,iterations = 1)

    contours, hierarchy = cv2.findContours(dilated_value,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    cropped = []
    cordinates = [] 
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        cordinates.append((x,y,w,h))
        #bounding the images
        if h > 400 and h < 1000:
            print(x,y,w,h)
            im = cv2.rectangle(im,(x,y),(x+w,y+h),(0,0,255),1)

            crop_img = im1[y:y+h, x:x+w]
            cropped.append(crop_img)
            # cv2.imshow("cropped", crop_img)
            # cv2.waitKey(100)
            #cv2.imwrite("crop_example.jpg", crop_img) 
        
        #cv2.imwrite("detected.jpg", im) 
    
    return cropped


if __name__ == "__main__":
    file =  r'10.jpg'
    im1 = cv2.imread(file, 0)
    cropped = get_boxes(im1)
    breakpoint()

