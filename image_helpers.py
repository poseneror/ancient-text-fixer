from tkinter import filedialog
from PIL import Image, ImageTk
import cv2 as cv
import numpy as np

from skimage.color import rgb2gray
from skimage import data
from skimage.filters import gaussian
from skimage.segmentation import active_contour


def select_image():
    path = filedialog.askopenfilename()
    if len(path) > 0:
        # load the image from disk
        input_image = cv.imdecode(np.fromfile(
            path, dtype=np.uint8), cv.IMREAD_COLOR)
        return input_image


def get_viewable_image(source):
    # OpenCV represents images in BGR order; however PIL represents
    # images in RGB order, so we need to swap the channels
    image = cv.cvtColor(source, cv.COLOR_BGR2RGB)
    # convert the images to PIL format...
    image = Image.fromarray(image)
    # ...and then to ImageTk format
    image = ImageTk.PhotoImage(image)
    return image


def get_viewable_letter_contours_image(source):
    image = cv.cvtColor(source, cv.COLOR_BGRA2RGBA)
    image = Image.fromarray(image)
    image.save('result.png')
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
    dominant = get_dominant_color(source)
    source[np.where(source >= 150)] = dominant
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


def segment_image(source):
    grey = to_grey(source)
    white_letter_edges = get_edges(grey)
    dominant_color = get_dominant_color(grey)
    fixed = cv.addWeighted(grey, 1, white_letter_edges, 1, 1)
    fixed = override_whith_parts_with_color(fixed, dominant_color)
    bg = cv.dilate(fixed, np.ones((5, 5), dtype=np.uint8))
    bg = cv.GaussianBlur(bg, (5, 5), 1)
    # src_no_bg = 255 - cv.absdiff(fixed, bg)
    # src_no_bg = 255 - cv.absdiff(fixed, src_no_bg)
    # maxValue = 255
    # thresh = 240
    # retval, dst = cv.threshold(
    #     fixed, thresh, maxValue, cv.THRESH_BINARY_INV)
    fixed = threshold_image(fixed)
    # fixed = edges
    return fixed


def get_letter_contours(source):
    segmented = segment_image(source)
    contours, hierarchy = cv.findContours(
        segmented, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    blank = np.zeros((source.shape[0], source.shape[1], 4), dtype=np.uint8)
    cv.drawContours(blank, contours, 0, (0, 0, 0, 255), 3)

    return blank, contours[0]


def get_final_letter(letter_contour, image):
    init = np.array(letter_contour.copy()[:, 0],  dtype='float64')
    snake = active_contour(image,
                           init, alpha=0.010, beta=10, gamma=0.0005, w_edge=1, w_line=2, max_iterations=5)
    retval = letter_contour.copy()
    retval[:, 0] = snake
    return retval
