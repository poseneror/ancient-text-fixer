import numpy as np
from matplotlib import pyplot as plt
from tkinter import Tk, Button, Label, Frame, Canvas, NW, Scrollbar, BOTTOM, RIGHT, X, Y, HORIZONTAL, VERTICAL, BOTH, LEFT, BOTTOM, RIGHT, LEFT, ALL, CURRENT, ACTIVE, NORMAL
from PIL import Image, ImageTk
import sys
from image_helpers import debug_draw, get_image_from_file, select_image_file, get_viewable_image, toolbar_sized, get_snakes, generate_output_from_canvas, segment_image, get_letter_contours


class SegmentedImage:
  def __init__(self, original, segmented):
    self.original = original
    self.segmented = segmented

class ContouredImage:
  def __init__(self, original, contours):
    self.original = original
    self.contours = contours

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.source_image = None
        self.selected_letter = None
        self.selected_letter_snake = None

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
            source_image = get_image_from_file('resources/test_text.tif')
            charactar_image = get_image_from_file('resources/beit-test.tif')
            self.set_source_image(source_image)
            contoured_image = get_letter_contours(charactar_image)
            self.add_selectable_letter_image(contoured_image)

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
        selected = select_image_file()
        if selected is None:
            return
        self.set_source_image(selected)

    def pick_selectable_letter_image(self):
        selected = select_image_file()
        if selected is None:
            return
        contoured_image = get_letter_contours(selected)
        self.add_selectable_letter_image(contoured_image)

    def set_source_image(self, source):
        self.source_image = SegmentedImage(
            source, segment_image(source))

        # update the image panels
        image = get_viewable_image(self.source_image.original)

        # Clear current canvas display
        self.output_image_view.delete(ALL)

        # garbage collector, please don't collect me
        self.output_image_view.tkimage = image
        self.output_image_view.letters = {}
        # self.output_image_view.letters_source = {}

        # Insert the image to the canvas
        self.output_image_view.create_image(
            0, 0, image=image, anchor=NW)

        # Scroll Size Setup
        height, width = self.source_image.original.shape[:2]
        self.output_image_view.configure(scrollregion=(
            0, 0, width, height))

    def add_selectable_letter_image(self, contoured_image):
        resized = toolbar_sized(contoured_image.original)
        resized = get_viewable_image(resized)

        self.letter_selection_frame.letters.append(resized)

        image_instance = Label(self.letter_selection_frame,
                               image=resized, background='grey')
        image_instance.pack(side='top', fill='x')

        # Selection binding
        image_instance.bind(
            "<Button-1>", lambda event: self.select_letter_image(image_instance, contoured_image))

    def add_letter_image(self, source, top_left):
        # update the image panels
        image = get_viewable_image(source)
        left, top = top_left
        # Insert the image to the canvas
        instance = self.output_image_view.create_image(
            left, top, image=image, anchor=NW, tags='letter')

        # garbage collector, please don't collect me
        self.output_image_view.letters[instance] = image
        # self.output_image_view.letters_source[instance] = source

    def unselect_letter(self):
        self.selected_letter = None
        self.selected_letter_snake = None
        for letter_image in self.letter_selection_frame.winfo_children():
            letter_image.configure(background='grey')
        self.reset_cursor()

    def select_letter_image(self, image_instance, contoured_image):
        if self.selected_letter is None or not np.array_equal(self.selected_letter.original, contoured_image.original):
            self.unselect_letter()
            self.selected_letter = contoured_image
            image_instance.configure(background='white')
        else:
            self.unselect_letter()

    def get_bounds(self, coords, image):
        x, y = coords
        height, width = image.shape[:2]
        height += 0
        width += 0
        top = int(max(y - (height / 2), 0))
        bottom = int(min(y + (height / 2), self.source_image.original.shape[0]))
        left = int(max(x - (width / 2), 0))
        right = int(min(x + (width / 2), self.source_image.original.shape[1]))
        return left, top, right, bottom

    def left_click_callback(self, event):
        # validation
        if(self.source_image is None):
            return

        x = int(self.output_image_view.canvasx(event.x))
        y = int(self.output_image_view.canvasy(event.y))
        if(self.selected_letter is None):
            # Select a piece from the canvas
            clicked_letter = self.output_image_view.find_withtag(CURRENT)
            if 'letter' in self.output_image_view.gettags(clicked_letter):
                self.output_image_view.selected_letter = clicked_letter
            else:
                # clear selection
                self.output_image_view.selected_letter = None
        else:
            # Add letter to canvas
            self.place_letter()

            # Clear selected letter to add
            self.unselect_letter()

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

    def draw_snaked_letter(self, event):
        if self.selected_letter is None or self.source_image is None:
            return

        x, y = event.x, event.y
        height, width = self.selected_letter.original.shape[:2]
        center_y = y - (height / 2)
        center_x = x - (width / 2)

        bounds = self.get_bounds(
            (x, y), self.selected_letter.original)
        left, top, right, bottom = bounds

        # Update snake image
        search_bounds = self.source_image.segmented[
            top:bottom, left:right]
        mask = self.selected_letter.contours
        snake = get_snakes(mask, search_bounds)
        corsur_image = get_viewable_image(
            snake.original)
        self.output_image_view.corsur_image = corsur_image
        self.selected_letter_snake = snake

        if self.output_image_view.corsur is None:
            self.output_image_view.corsur = self.output_image_view.create_image(
                center_x, center_y, image=corsur_image, anchor=NW, tags='corsur')
            self.output_image_view.corsur_bounds = self.output_image_view.create_rectangle(
                *bounds)
        else:
            # Update corsur image and bounds position
            self.output_image_view.coords(
                self.output_image_view.corsur, center_x, center_y)
            self.output_image_view.coords(
                self.output_image_view.corsur_bounds, *bounds)
            # Update corsur image 
            self.output_image_view.itemconfig(
                self.output_image_view.corsur, image=corsur_image)

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
        self.output_image_view.bind('<Motion>', self.draw_snaked_letter)

        # Left Mouse Click
        self.output_image_view.bind("<Button-1>", self.left_click_callback)

        # Right Mouse Click
        # self.output_image_view.bind('<Button-3>', self.delete_clicked_letter)

    def setup_letter_selection_frame(self):
        self.letter_selection_frame = Frame(
            width=100, height=650, background='grey')
        self.letter_selection_frame.pack(side="left", fill="y")
        self.letter_selection_frame.letters = []

    def place_letter(self):
        if self.selected_letter_snake is not None:
            snakes_image = self.selected_letter_snake
            # debug_draw(snakes_image.original, snakes_image.contours)
            coords = self.output_image_view.coords(self.output_image_view.corsur)
            self.add_letter_image(snakes_image.original, coords)

    def generate_output(self):
        if self.source_image is None:
            return
        output = self.source_image.original

        # Put all the letters on the source image
        letters = self.output_image_view.find_withtag('letter')
        for letter in letters:
            coords = self.output_image_view.coords(letter)
            top_left = [int(coords[0]), int(coords[1])]
            # letter_source = self.output_image_view.letters_source[letter]
            # output[top_left[1]:(top_left[1] + letter_source.shape[0]),
            #        top_left[0]:(top_left[0] + letter_source.shape[1])] = letter_source


root = Tk()
app = Application(master=root)
app.mainloop()
