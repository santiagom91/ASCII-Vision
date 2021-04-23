# Alex Eidt
# Copyright 2021

from ctypes import *
from tkinter import *
from tkinter.ttk import Style
import imageio
import os
import numpy as np
from numpy.ctypeslib import ndpointer
from PIL import Image, ImageTk

# Bindings for functions from process_image.c.
lib = CDLL(os.path.join(os.getcwd(), 'process_image.so'), RTLD_GLOBAL)
lib.process_stream.argtypes = [ndpointer(c_uint8), ndpointer(c_uint8), c_int, c_int, c_int, c_int, c_bool]
lib.process_stream.restype = None
lib.ascii.argtypes = [ndpointer(c_uint8), c_int]
lib.ascii.restype = None
lib.apply.argtypes = [ndpointer(c_uint8), ndpointer(c_uint8), c_int, c_int, c_int]
lib.apply.restype = None

# Mirror image stream along vertical axis.
MIRROR = True
# Video Stream to use. Put filename here if using video file.
STREAM = '<video0>'
# Background color of the ASCII stream.
BACKGROUND_COLOR = 'white'
# Font color used in the ASCII stream. Make sure there's some contrast between the two.
FONT_COLOR = 'black'


def get_dims(w, h, factor):
    """
    Finds the optimal resizing factor for the webcam stream based on the screen dimensions.
    """
    root = Tk()
    # Get screen size
    height = root.winfo_screenheight() / factor
    width = root.winfo_screenwidth() / factor
    root.destroy()
    scale = None
    max_resolution = 1 << 16
    for i in range(2, 20):
        if not (w % i or h % i):
            max_ = abs(height - h / i) + abs(width - w / i)
            if max_ < max_resolution:
                max_resolution = max_
                scale = i
    return scale


def main():
    # All ASCII characters used in the images sorted by pixel density.
    chars = f""" `.,|^'\/~!_-;:)("><¬?*+7j1ilJyc&vt0$VruoI=wzCnY32LTxs4Zkm5hg6qfU9paOS#£eX8D%bdRPGFK@AMQNWHEB"""
    char_mapper = np.vectorize(lambda x: chars[x])
    toggle_enabled = lambda enabled, panel: [w.config(state=enabled) for w in panel.winfo_children()]

    def stream(scale):
        try:
            image = video.get_next_data()
        except Exception:
            video.close()
            return
        h, w, c = image.shape
        # Define options based on radio button selections.
        color_mode, ascii_mode, filter_mode = color.get() == 2, is_ascii.get() == 1, has_filter.get() > 0
        # If color mode is on, disable ASCII and Filter radio buttons.
        if color_mode:
            toggle_enabled(DISABLED, ascii_panel), toggle_enabled(DISABLED, filter_panel)
        else:
            toggle_enabled(NORMAL, ascii_panel), toggle_enabled(NORMAL, filter_panel)
        # ASCII image is larger than regular, so multiply scaling factor by 2 if ASCII mode is on.
        size = scale << 1 if ascii_mode else scale
        dims = w * h * c // (size * size) if color_mode else w * h // (size * size)

        output = np.empty(dims, dtype=np.uint8)
        # Process incoming frames by resizing them and mirroring them if specified.
        lib.process_stream(image.ravel().astype(np.uint8), output, w * c, h, size, color.get(), MIRROR)
        h //= size
        w //= size
        # If the user selected a filter to apply, apply it to the current frame.
        if filter_mode:
            # Applying 3x3 kernel to a (w, h) image will result in a (w - 2, h - 2) image.
            convolved = np.empty((h - 2) * (w - 2), dtype=np.uint8)
            lib.apply(output, convolved, w, h, has_filter.get())
            output = convolved
            del convolved
            h -= 2
            w -= 2
        # If there is a filter applied or ASCII mode is on, prevent the user from turning on color mode.
        if filter_mode or ascii_mode:
            radio_buttons['Color'].config(state=DISABLED)
        else:
            radio_buttons['Color'].config(state=NORMAL)          
        # If the color is grayscaled, leave out the color channels
        shape = (h, w, c) if color_mode else (h, w)
        # If ASCII mode is on convert frame to ascii and display, otherwise display video stream.
        if ascii_mode:
            lib.ascii(output, w * h)
            image_label.pack_forget()
            ascii_label.pack()
            # Update label with new ASCII image.
            ascii_label.config(
                text='\n'.join([''.join(x) for x in char_mapper(output).reshape((h, w))])
            )
            ascii_label.after(delay, lambda: stream(scale))
        else:
            ascii_label.pack_forget()
            image_label.pack()
            frame_image = Image.fromarray(output.reshape(shape))
            frame_image = ImageTk.PhotoImage(frame_image)
            image_label.config(image=frame_image)
            image_label.image = frame_image
            image_label.after(delay, lambda: stream(scale))

    root = Tk()
    root.title('ASCII Streamer')
    f1 = Frame()
    image_label = Label(f1, borderwidth=5, relief='solid')
    ascii_label = Label(f1, font=('courier', 2), fg=FONT_COLOR, bg=BACKGROUND_COLOR, borderwidth=5, relief='solid')
    f1.pack(side=LEFT, expand=YES, padx=10)
    root.protocol("WM_DELETE_WINDOW", lambda: (video.close(), root.destroy()))
    # Variables that store state of radio buttons.
    color, has_filter, is_ascii = IntVar(root, 2), IntVar(root, 0), IntVar(root, 0)

    Style(root).configure("TRadiobutton", font=("arial", 10, "bold"))
    # Map Radio Button labels and their IDs.
    colors = dict(enumerate(['Grayscale - Weighted RGB', 'Grayscale - Three Way Max', 'Color']))
    filters = dict(enumerate(['None', 'Outline', 'Sharpen', 'Emboss', 'Sobel']))
    ascii_ = dict(enumerate(['No ASCII', 'ASCII']))
    # Create panel on the right side with radio buttons and labels.
    buttons = Frame(root)
    color_panel = Frame(buttons, borderwidth=10)
    Label(color_panel, text="Color", font=('Arial', 15, 'bold')).pack()
    filter_panel = Frame(buttons, borderwidth=10)
    Label(filter_panel, text="Filters", font=('Arial', 15, 'bold')).pack()
    ascii_panel = Frame(buttons, borderwidth=10)
    Label(ascii_panel, text="ASCII", font=('Arial', 15, 'bold')).pack()
    # Add radio buttons to their respective buttons panel.
    radio_buttons = {}
    for button, panel, option in zip(
        [colors, filters, ascii_],
        [color_panel, filter_panel, ascii_panel],
        [color, has_filter, is_ascii]
    ):
        for value, text in button.items():
            radio_buttons[text] = Radiobutton(panel, text=text, variable=option, value=value)
            radio_buttons[text].pack(side=TOP, ipady=5, anchor=W)
    # Add all button panels to main panel on the right side.
    buttons.pack(side=RIGHT, padx=(10, 50))
    ascii_panel.pack(side=TOP)
    color_panel.pack()
    filter_panel.pack(side=BOTTOM)
    # Get image stream from webcam or other source and begin streaming.
    video = imageio.get_reader(STREAM)
    meta_data = video.get_meta_data()
    # To change the framerate of the stream, change the "delay" value below.
    delay = int(meta_data['fps'])
    h, w, _ = video.get_next_data().shape
    scale = get_dims(w, h, 2)
    if scale is None:
        raise ValueError('Could not find rescaling factor for video/webcam stream.')
    stream(scale)
    root.mainloop()


if __name__ == '__main__':
    main()