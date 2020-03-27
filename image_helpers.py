from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from matplotlib import path

from skimage.color import rgb2gray, gray2rgb
from skimage.io import imread, show, imshow
from skimage.filters import gaussian
from skimage.segmentation import active_contour
from skimage.feature import canny
from skimage.measure import find_contours
from skimage.transform import resize
from skimage.draw import polygon
class ContouredImage:
  def __init__(self, original, contours):
    self.original = original
    self.contours = contours

def get_image_from_file(file_name):
    return imread(file_name)

def select_image_file():
    path = filedialog.askopenfilename()
    if len(path) > 0:
        # load the image from disk
        input_image = imread(path)
        return input_image

def get_viewable_image(source):
    image = Image.fromarray(source)
    image = ImageTk.PhotoImage(image)
    return image

def generate_output_from_canvas(canvas, fileName):
    # save postscipt image
    canvas.postscript(file=fileName + '.eps')
    # use PIL to convert to PNG
    img = Image.open(fileName + '.eps')
    img.save(fileName + '.png', 'png')

def get_dominant_color(source):
    pixels = np.float32(source.reshape(-1, 1))
    n_colors = 1
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 200, .1)
    flags = cv.KMEANS_RANDOM_CENTERS
    _, labels, palette = cv.kmeans(pixels, n_colors, None, criteria, 5, flags)
    _, counts = np.unique(labels, return_counts=True)
    dominant = palette[np.argmax(counts)]
    return dominant


def override_whith_parts_with_color(source, color):
    source[np.where(source >= 150)] = color
    return source


def threshold_image(source, thresh=100):
    ret, temp_thresh = cv.threshold(
        source, thresh, 255, cv.THRESH_BINARY_INV)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 8))
    morph_img = cv.morphologyEx(temp_thresh, cv.MORPH_CLOSE, kernel)
    return morph_img


def to_grey(source):
    return cv.cvtColor(source, cv.COLOR_BGR2GRAY)


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)
    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv.Canny(image, lower, upper)
    # return the edged image
    return edged


def get_edges(source):
    scale = 1
    delta = 0
    ddepth = cv.CV_16S

    size = 5
    blurred = cv.GaussianBlur(source, (3, 3), 0)
    # kernel = np.ones((size, size), np.float32)/(size**2)
    # blurred = source.copy()
    # blurred = cv.filter2D(blurred, -1, kernel)

    # grad_x = cv.Sobel(blurred, ddepth, 1, 0, ksize=3, scale=scale,
    #                   delta=delta, borderType=cv.BORDER_DEFAULT)
    # grad_y = cv.Sobel(blurred, ddepth, 0, 1, ksize=3, scale=scale,
    #                   delta=delta, borderType=cv.BORDER_DEFAULT)

    # abs_grad_x = cv.convertScaleAbs(grad_x)
    # abs_grad_y = cv.convertScaleAbs(grad_y)

    # grad = cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    edges = auto_canny(blurred)

    edges = cv.GaussianBlur(edges, (5, 5), 0)
    edges = cv.GaussianBlur(edges, (3, 3), 0)

    return edges

def toolbar_sized(source, width=100, height=100):
    resized = source.copy()
    resize(resized, (width, height), order=1, mode='reflect', cval=0, clip=True,
           preserve_range=False, anti_aliasing=True, anti_aliasing_sigma=None)
    return resized

def segment_image(source):
    grey = rgb2gray(source)
    # white_letter_edges = canny(grey, sigma=1)
    # fixed = white_letter_edges
    return grey

def get_letter_contours(source):
    grey = rgb2gray(source)
    contours = find_contours(grey, 0.3)
    # larget contour
    letter_contour = sorted(contours, key=lambda x: len(x))[-1]
    letter_image = np.zeros((source.shape[0], source.shape[1], 4), dtype=np.uint8)
    letter_image = drawContours(letter_image, letter_contour, [255, 0, 0, 255])
    # debug_draw(letter_image)
    return ContouredImage(letter_image, letter_contour)


def get_snakes(letter_contour, image):
    init = letter_contour.copy()
    snake = active_contour(image, init, alpha=0.010, beta=10, gamma=0.0005, w_edge=1, w_line=-1, max_iterations=10, coordinates='rc')
    # debug_draw(image, letter_contour)
    blank = np.zeros(
        (image.shape[0], image.shape[1], 4), dtype=np.uint8)
    # blank = drawContours(blank, snake, color)

    rr, cc = polygon(snake[:, 0], snake[:, 1], blank.shape)
    color = [255, 0, 0, 255]
    blank[rr, cc] = color
    return ContouredImage(blank, snake)

def debug_draw(img, contours):
    fig, ax = plt.subplots()
    ax.imshow(img, cmap=plt.cm.gray)
    ax.plot(contours[:, 1], contours[:, 0], linewidth=2)
    ax.axis('image')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.show()

def drawContours(img, contours, color):
    img = gray2rgb(img)
    contours = contours.astype(int)
    img[contours[:, 0], contours[:, 1]] = color
    return img
