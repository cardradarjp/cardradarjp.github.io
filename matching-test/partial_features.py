"""Multi-view perceptual signatures for partially occluded card art."""
import cv2,numpy as np
# Normalized regions: visible top, central artwork, and upper-central overlap.
REGIONS=((.12,.12,.88,.39),(.12,.23,.88,.51),(.12,.12,.88,.56))
def features(img):
    h,w=img.shape[:2]
    bits=[];hist=[]
    for x1,y1,x2,y2 in REGIONS:
        crop=img[int(h*y1):int(h*y2),int(w*x1):int(w*x2)]
        gray=cv2.resize(cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY),(32,32),interpolation=cv2.INTER_AREA).astype(np.float32)
        dct=cv2.dct(gray)[:8,:8]
        bits.append((dct[1:,:]>np.median(dct[1:,:])).ravel())
        hsv=cv2.cvtColor(crop,cv2.COLOR_BGR2HSV)
        hh=cv2.calcHist([hsv],[0,1],None,[16,8],[0,180,0,256])
        cv2.normalize(hh,hh)
        hist.append(hh.ravel())
    return np.stack(bits),np.stack(hist)
