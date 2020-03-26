import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import tkinter as tk
import PIL.Image
import PIL.ImageTk
import tkFileDialog


def select_image():
	# grab a reference to the image panels
	global input_image, letter_images
	path = tkFileDialog.askopenfilename()

    if len(path) > 0:
		# load the image from disk, convert it to grayscale, and detect
		# edges in it
		image = cv.imread(path)
		gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
		edged = cv.Canny(gray, 50, 100)
		# OpenCV represents images in BGR order; however PIL represents
		# images in RGB order, so we need to swap the channels
		image = cv.cvtColor(image, cv2.COLOR_BGR2RGB)
		# convert the images to PIL format...
		image = Image.fromarray(image)
		edged = Image.fromarray(edged)
		# ...and then to ImageTk format
		image = ImageTk.PhotoImage(image)
		edged = ImageTk.PhotoImage(edged)

        
original_piece = cv.imread('resources/beit.tif')
piece = cv.imread('resources/beit.tif', 0)
# piece_gray = cv.cvtColor(piece, cv.COLOR_BGR2GRAY)
# ret, piece_thresh = cv.threshold(
#     piece_gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)

# load template image
original = cv.imread('resources/text2.tif')
template = cv.imread('resources/text2.tif', 0)

# get the dominant color and paint all white parts with it
pixels = np.float32(template.reshape(-1, 1))
n_colors = 5
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 200, .1)
flags = cv.KMEANS_RANDOM_CENTERS
_, labels, palette = cv.kmeans(pixels, n_colors, None, criteria, 10, flags)
_, counts = np.unique(labels, return_counts=True)
dominant = palette[np.argmax(counts)]
template[np.where(template >= 150)] = dominant

# SEGMENTATION
# # ret, temp_thresh = cv.threshold(
# #     template, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)


def find_letter(bounds, letterImage):
    search_bounds = template[bounds[1]:bounds[3],
                             bounds[0]:bounds[2]]
    w, h = letterImage.shape[::-1]
    method = cv.TM_CCOEFF_NORMED
    # Apply template Matching
    res = cv.matchTemplate(search_bounds, letterImage, method)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc

    # fix to full image bounds
    top_left = (bounds[0] + top_left[0], bounds[1] + top_left[1])
    bottom_right = (bounds[0] + top_left[0] + w, bounds[1] + top_left[1] + h)
    original[top_left[1]:top_left[1] + original_piece.shape[0],
             top_left[0]:top_left[0] + original_piece.shape[1]] = original_piece
    cv.rectangle(original, top_left,
                 (top_left[0] + original_piece.shape[1], top_left[1] + original_piece.shape[0]), 255, 2)
    cv.imshow("image", original)


# letter size
height = 100
width = 100


def place_letter(event, x, y, flags, param):
    # Left Mouse Click
    if event == cv.EVENT_LBUTTONDOWN:
        coord = (x, y)
        box = [max(coord[0] - height, 0), max(coord[1] - width, 0),
               min(coord[0] + height, template.shape[0]), min(coord[1] + width, template.shape[1])]
        print(box)
        find_letter(box, piece)