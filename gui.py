import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from tkinter import Tk, Button, Label, Frame, Canvas, NW, Scrollbar, BOTTOM, RIGHT, X, Y, HORIZONTAL, VERTICAL, BOTH, LEFT, BOTTOM, RIGHT, LEFT, ALL, CURRENT, ACTIVE, NORMAL
from PIL import Image, ImageTk
import sys
from image_helpers import get_final_letter, select_image, get_viewable_image, get_viewable_letter_contours_image, generate_output_from_canvas, segment_image, get_letter_contours


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.source_image = None
        self.selected_letter_to_add = None

        # GUI setup
        self.pack()
        self.create_widgets()

        # Controls
        self.bind_keyboard_events()
        if '-d' in sys.argv:
            self.debug = True
        else:
            self.debug = False

        if self.debug:
            print('DEBUG MODE IS ON')
            cv.namedWindow("DEBUG", cv.WINDOW_AUTOSIZE)
            cv.namedWindow("DEBUG_2", cv.WINDOW_AUTOSIZE)
            source_image = cv.imread('resources/test_text.tif')
            charactar_image = cv.imread('resources/beit-test.tif')
            self.set_source_image(source_image)
            char, cont = get_letter_contours(charactar_image)
            self.add_selectable_letter_image(char, cont)

            # cv.imshow("DEBUG", self.modified_source_image)

    def create_widgets(self):
        self.input_select = Button(
            self, text="Select an letter image", command=self.pick_selectable_letter_image)
        self.input_select.pack(side="left")

        self.input_select = Button(
            self, text="Select source image", command=self.pick_source_image)
        self.input_select.pack(side="right")

        self.setup_input_image_canvas()
        self.setup_letter_selection_frame()

        self.input_select = Button(
            self, text="OUTPUT", command=self.generate_output)
        self.input_select.pack(side="bottom")

    def bind_keyboard_events(self):
        # Delete or Backspace key pressed
        self.master.bind_all(
            "<BackSpace>", self.delete_selected_letter)
        self.master.bind_all("<Delete>", self.delete_selected_letter)
        self.master.bind_all(
            "<Left>", lambda event: self.move_selected_letter('left'))
        self.master.bind_all(
            "<Right>", lambda event: self.move_selected_letter('right'))
        self.master.bind_all(
            "<Up>", lambda event: self.move_selected_letter('up'))
        self.master.bind_all(
            "<Down>", lambda event: self.move_selected_letter('down'))
        # scale
        # scale(self, xscale, yscale, xoffset, yoffset)

    def pick_source_image(self):
        selected = select_image()
        if selected is None:
            return
        self.set_source_image(selected)

    def pick_selectable_letter_image(self):
        selected = select_image()
        if selected is None:
            return
        char, cont = get_letter_contours(selected)
        self.add_selectable_letter_image(char, cont)

    def set_source_image(self, source):
        self.source_image = source
        self.modified_source_image = self.modify_image(source.copy())

        # update the image panels
        image = get_viewable_image(self.source_image)

        # Clear current canvas display
        self.output_image_view.delete(ALL)

        # garbage collector, please don't collect me
        self.output_image_view.tkimage = image
        self.output_image_view.letters = {}
        self.output_image_view.letters_source = {}

        # Insert the image to the canvas
        self.output_image_view.create_image(
            0, 0, image=image, anchor=NW)

        # Scroll Size Setup
        height, width = self.source_image.shape[:2]
        self.output_image_view.configure(scrollregion=(
            0, 0, width, height))

    def add_selectable_letter_image(self, source, contours):
        resized = cv.resize(source, (100, 100), interpolation=cv.INTER_AREA)
        image = get_viewable_letter_contours_image(source)

        cv.imshow("DEBUG", source)
        self.letter_selection_frame.letters.append(image)

        image_instance = Label(self.letter_selection_frame,
                               image=image, background='grey')
        image_instance.pack(side='top', fill='x')

        # Selection binding
        image_instance.bind(
            "<Button-1>", lambda event: self.select_letter_image(image_instance, source, contours))

    def add_letter_image(self, source, top_left):
        # update the image panels
        image = get_viewable_letter_contours_image(source)
        top, left = top_left
        # Insert the image to the canvas
        instance = self.output_image_view.create_image(
            left, top, image=image, anchor=NW, tags='letter')

        # garbage collector, please don't collect me
        self.output_image_view.letters[instance] = image
        self.output_image_view.letters_source[instance] = source

    def unselect_letter_image(self):
        self.selected_letter_to_add = None
        for letter_image in self.letter_selection_frame.winfo_children():
            letter_image.configure(background='grey')
        self.reset_cursor()

    def select_letter_image(self, image_instance, source, contours):
        if self.selected_letter_to_add is None or not np.array_equal(self.selected_letter_to_add[0], source):
            self.unselect_letter_image()
            self.selected_letter_to_add = (source, contours)
            image_instance.configure(background='red')
        else:
            self.unselect_letter_image()

    def get_bounds(self, coords, image):
        x, y = coords
        height, width = image.shape[:2]
        height += 20
        width += 20
        top = int(max(y - (height / 2), 0))
        bottom = int(min(y + (height / 2), self.source_image.shape[0]))
        left = int(max(x - (width / 2), 0))
        right = int(min(x + (width / 2), self.source_image.shape[1]))
        return left, top, right, bottom

    def left_click_callback(self, event):
        # validation
        if(self.source_image is None):
            return

        x = int(self.output_image_view.canvasx(event.x))
        y = int(self.output_image_view.canvasy(event.y))
        if(self.selected_letter_to_add is None):
            # Select a piece from the canvas
            clicked_letter = self.output_image_view.find_withtag(CURRENT)
            if 'letter' in self.output_image_view.gettags(clicked_letter):
                self.output_image_view.selected_letter = clicked_letter
            else:
                # clear selection
                self.output_image_view.selected_letter = None
        else:
            # Add letter to canvas
            self.place_letter(self.get_bounds(
                (x, y), self.selected_letter_to_add[0]))

            # Clear selected letter to add
            self.selected_letter_to_add = None

    def delete_selected_letter(self, event):
        if(not self.output_image_view.selected_letter is None):
            self.output_image_view.delete(
                self.output_image_view.selected_letter)
            self.output_image_view.selected_letter = None

    def move_selected_letter(self, direction):
        speed = 1
        if direction == 'left':
            dx, dy = (-speed, 0)
        if direction == 'right':
            dx, dy = (speed, 0)
        if direction == 'up':
            dx, dy = (0, -speed)
        if direction == 'down':
            dx, dy = (0, speed)
        if(not self.output_image_view.selected_letter is None):
            self.output_image_view.move(
                self.output_image_view.selected_letter, dx, dy)

    def on_mousewheel_callback(self, event):
        self.output_image_view.yview_scroll(-1 * (event.delta // 120), "units")

    def reset_cursor(self):
        if(self.output_image_view.corsur_image is not None):
            self.output_image_view.delete(
                self.output_image_view.corsur_image)
            self.output_image_view.delete(
                self.output_image_view.corsur_bounds)
        self.output_image_view.corsur = None
        self.output_image_view.corsur_image = None
        self.output_image_view.corsur_bounds = None

    def draw_cursor(self, event):
        if self.selected_letter_to_add is None or self.source_image is None:
            return

        x, y = event.x, event.y
        height, width = self.selected_letter_to_add[0].shape[:2]
        center_y = y - (height / 2)
        center_x = x - (width / 2)
        if self.debug:
            self.debug_display(self.get_bounds(
                (x, y), self.selected_letter_to_add[0]))
        if self.output_image_view.corsur is None:
            image = get_viewable_letter_contours_image(
                self.selected_letter_to_add[0])
            self.output_image_view.corsur_image = image
            self.output_image_view.corsur = self.output_image_view.create_image(
                center_x, center_y, image=image, anchor=NW, tags='corsur')
            left, top, right, bottom = self.get_bounds(
                (x, y), self.selected_letter_to_add[0])
            self.output_image_view.corsur_bounds = self.output_image_view.create_rectangle(
                left, top, right, bottom)
        else:
            self.output_image_view.coords(
                self.output_image_view.corsur, center_x, center_y)
            left, top, right, bottom = self.get_bounds(
                (x, y), self.selected_letter_to_add[0])
            self.output_image_view.coords(
                self.output_image_view.corsur_bounds, left, top, right, bottom)

    def setup_input_image_canvas(self):
        self.source_image_frame = Frame(
            width=650, height=650, background='white')
        self.source_image_frame.pack(expand=True, fill=BOTH, side="right")
        self.output_image_view = Canvas(self.source_image_frame, width=650, height=650,
                                        cursor='dot')

        # Scrollbar
        self.input_scroll_x = Scrollbar(
            self.source_image_frame, orient=HORIZONTAL)
        self.input_scroll_x.pack(side=BOTTOM, fill=X)
        self.input_scroll_x.config(command=self.output_image_view.xview)

        self.input_scroll_y = Scrollbar(
            self.source_image_frame, orient=VERTICAL)
        self.input_scroll_y.pack(side=RIGHT, fill=Y)
        self.input_scroll_y.config(command=self.output_image_view.yview)

        self.output_image_view.config(
            yscrollcommand=self.input_scroll_y.set, xscrollcommand=self.input_scroll_x.set)

        self.output_image_view.pack(
            expand=True, fill=BOTH, side=LEFT, padx=10, pady=10)

        # Selected letter
        self.output_image_view.selected_letter = None

        # Mouse Scroll
        self.output_image_view.bind(
            "<MouseWheel>", self.on_mousewheel_callback)

        # Mouse Cursor
        self.output_image_view.corsur = None
        self.output_image_view.corsur_image = None
        self.output_image_view.corsur_bounds = None
        self.output_image_view.bind('<Motion>', self.draw_cursor)

        # Left Mouse Click
        self.output_image_view.bind("<Button-1>", self.left_click_callback)

        # Right Mouse Click
        # self.output_image_view.bind('<Button-3>', self.delete_clicked_letter)

    def setup_letter_selection_frame(self):
        self.letter_selection_frame = Frame(
            width=100, height=650, background='grey')
        self.letter_selection_frame.pack(side="left", fill="y")
        self.letter_selection_frame.letters = []
        self.letter_selection_frame.selected_letter = None

    def modify_image(self, source):
        # source = cv.cvtColor(source, cv.COLOR_BGR2GRAY)
        # source = override_with_dominant_color(source)
        source = segment_image(source)
        return source

    def debug_display(self, bounds):
        left, top, right, bottom = bounds
        search_bounds = self.modified_source_image[
            top:bottom, left:right]
        mask = self.selected_letter_to_add[1]
        result = get_final_letter(mask, search_bounds)
        blank = np.zeros(
            (search_bounds.shape[0], search_bounds.shape[1], 4), dtype=np.uint8)
        cv.drawContours(blank, [result], 0, (0, 0, 255, 255), 3)
        cv.imshow("DEBUG", blank)
        # cv.imshow("DEBUG_2", mask)

    def place_letter(self, bounds):
        # Search only in the given bounds
        left, top, right, bottom = bounds
        search_bounds = self.modified_source_image[top:bottom, left:right]
        # grey_search_bounds = cv.cvtColor(search_bounds, cv.COLOR_BGR2GRAY)

        # B&W is faster and takes less memory space
        # grey_letter = cv.cvtColor(
        #     self.selected_letter_to_add, cv.COLOR_BGR2GRAY)
        w, h = self.selected_letter_to_add[0].shape[:2]

        # Apply template Matching, max_loc holds the best matching point top_left corner
        res = cv.matchTemplate(
            search_bounds, self.selected_letter_to_add[0], cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        # fix to full image bounds (absolute position on image)
        top_left = (top + max_loc[1], left + max_loc[0])

        self.add_letter_image(self.selected_letter_to_add[0], top_left)
        self.unselect_letter_image()

    def generate_output(self):
        if self.source_image is None:
            return
        output = self.source_image

        # Put all the letters on the source image
        letters = self.output_image_view.find_withtag('letter')
        for letter in letters:
            coords = self.output_image_view.coords(letter)
            top_left = [int(coords[0]), int(coords[1])]
            letter_source = self.output_image_view.letters_source[letter]
            output[top_left[1]:(top_left[1] + letter_source.shape[0]),
                   top_left[0]:(top_left[0] + letter_source.shape[1])] = letter_source

        if self.debug:
            cv.imshow("DEBUG", output)
        cv.imwrite('output.tif', output)


root = Tk()
app = Application(master=root)
app.mainloop()
