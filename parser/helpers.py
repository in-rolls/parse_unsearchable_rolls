import cv2
import numpy as np
import pdf2image

def pdf_to_img(pdf_file_path, output_images_path,dpi=200,page=None) :

    PDF_PATH = pdf_file_path
    DPI = dpi
    OUTPUT_FOLDER = output_images_path
    FIRST_PAGE = page
    LAST_PAGE = page
    FORMAT = 'jpg'
    THREAD_COUNT = 1
    USERPWD = None
    USE_CROPBOX = False
    STRICT = False

    # def rename_filename(output_image_path,idx):
    #     path, filename = os.path.split(output_image_path)
    #     os.rename(output_image_path,path+"/"+str(idx)+".jpg")

    # def delete_existing_images():
    #     images = os.listdir(output_images_path)
    #     for image in images:
    #         os.remove(output_images_path+"/"+image)



    def pdftopil():

        pil_images = pdf2image.convert_from_path(PDF_PATH,
                                                 dpi=DPI,
                                                 #output_folder=OUTPUT_FOLDER,
                                                 first_page=FIRST_PAGE,
                                                 last_page=LAST_PAGE,
                                                 fmt=FORMAT,
                                                 thread_count=THREAD_COUNT,
                                                 userpw=USERPWD,
                                                 use_cropbox=USE_CROPBOX,
                                                 strict=STRICT)

        # for idx,image in enumerate(pil_images,1):
        #     rename_filename(image.filename,idx)

        return pil_images

    pil_images = pdftopil()

    return pil_images

def get_boxes(pil_image):
    #im1 = cv2.imread(file, 0)
    #im = cv2.imread(file)
    #im = np.zeros((6000,4500,3), dtype=np.uint8)

    im = np.array(pil_image) 

    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ret,thresh_value = cv2.threshold(im,180,255,cv2.THRESH_BINARY_INV)

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
            #print(x,y,w,h)
            #im = cv2.rectangle(im,(x,y),(x+w,y+h),(0,0,255),1)

            crop_img = im[y:y+h, x:x+w]
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

