import cv2
import numpy as np
import imageio
from scipy.signal import savgol_filter
from skimage.morphology import skeletonize
from .gui_helpers.do_calculations import sortContours, contourEdge

def process_aponeurosis_mask(mask_path: str):
    """
    Processes a single aponeurosis mask to create an ROI mask.

    Args:
        mask_path (str): Path to the aponeurosis mask.

    Returns:
        np.ndarray: The ROI mask.
    """
    APO_LENGTH_TRESH = 600
    MIN_WIDTH = 60

    try:
        mask = imageio.imread(mask_path)
    except FileNotFoundError as e:
        print(f"Error reading file: {e}")
        return None

    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
    thresh = thresh.astype("uint8")

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    contours_re = [c for c in contours if len(c) > APO_LENGTH_TRESH]
    if len(contours_re) < 1:
        return None

    contours, _ = sortContours(contours_re)
    if contours is None:
        return None

    contours_re2 = []
    for contour in contours:
        pts = list(contour)
        ptsT = sorted(pts, key=lambda k: [k[0][0], k[0][1]])
        allx = [p[0, 0] for p in ptsT]
        ally = [p[0, 1] for p in ptsT]
        app = np.array(list(zip(allx, ally)))
        contours_re2.append(app)

    maskT = np.zeros(thresh.shape, np.uint8)
    for cnt in contours_re2:
        cv2.drawContours(maskT, [cnt], 0, 255, -1)

    xs1 = [c[0][0] for c in contours_re2]
    xs2 = [c[-1][0] for c in contours_re2]
    ys1 = [c[0][1] for c in contours_re2]
    ys2 = [c[-1][1] for c in contours_re2]

    for i in range(len(contours_re2) - 1):
        if xs1[i + 1] > xs2[i]:
            y1, y2 = ys2[i], ys1[i + 1]
            if y1 - 10 <= y2 <= y1 + 10:
                m = np.vstack((contours_re2[i], contours_re2[i + 1]))
                cv2.drawContours(maskT, [m], 0, 255, -1)

    maskT[maskT > 0] = 1
    skeleton = skeletonize(maskT).astype(np.uint8)
    kernel = np.ones((3, 7), np.uint8)
    dilate = cv2.dilate(skeleton, kernel, iterations=15)
    erode = cv2.erode(dilate, kernel, iterations=10)

    contoursE, _ = cv2.findContours(erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contoursE = [c for c in contoursE if len(c) > APO_LENGTH_TRESH]

    if len(contoursE) < 2:
        return None

    contoursE, _ = sortContours(contoursE)
    if contoursE is None:
        return None

    upp_x, upp_y = contourEdge("B", contoursE[0])

    if contoursE[1][0, 0, 1] > contoursE[0][0, 0, 1] + MIN_WIDTH:
        low_x, low_y = contourEdge("T", contoursE[1])
    else:
        if len(contoursE) > 2:
            low_x, low_y = contourEdge("T", contoursE[2])
        else:
            return None

    if len(upp_x) == 0 or len(low_x) == 0:
        return None

    upp_y_new = savgol_filter(upp_y, min(len(upp_y)-1 if len(upp_y) % 2 == 0 else len(upp_y), 81), 2)
    low_y_new = savgol_filter(low_y, min(len(low_y)-1 if len(low_y) % 2 == 0 else len(low_y), 81), 2)

    ex_mask = np.zeros(thresh.shape, np.uint8)
    f_upp = np.poly1d(np.polyfit(upp_x, upp_y_new, 2))
    f_low = np.poly1d(np.polyfit(low_x, low_y_new, 2))

    start_x = int(max(np.min(upp_x), np.min(low_x)))
    end_x = int(min(np.max(upp_x), np.max(low_x)))

    for x in range(start_x, end_x):
        ymin = int(np.floor(f_upp(x)))
        ymax = int(np.ceil(f_low(x)))
        ymin = max(0, ymin)
        ymax = min(ex_mask.shape[0], ymax)
        ex_mask[ymin:ymax, x] = 255

    return ex_mask
