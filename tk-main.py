from tkinter import *
import math
from PIL import Image, ImageTk

class car_detection_gui(object):

    def __init__(self):
        self.window = Tk()
        # set gui title and window size
        self.window.title('Chernger')
        #self.window.geometry('{}x{}'.format(1800, 1080))
        self.window.wm_attributes('-fullscreen','true')
        # set background image
        self.bg_image = ImageTk.PhotoImage(Image.open('background.jpg'))
        self.background = Label(self.window, image=self.bg_image, width = 1920, height=1080)
        self.background.grid(row = 0, column = 0)

        #separate frame 
        first_textbox = Frame(self.background, width=1900, height=1000)
        first_textbox.grid(column=1, row=1)
        
        # second_textbox = Label(self.background, width=80, height=100, bg='blue')
        # second_textbox.grid(column=2, row=1)
        # third_textbox = Label(self.background, width=100, height=20, bg='red')
        # third_textbox.grid(column=3, row=1, columnspan=20)        
        # labelWidth = Label(self.background,
        #                     text = "Width Ratio")
        # labelWidth.grid(column=0, row=0,, sticky=W+N)

        # labelHeight = Label(self.background,
        #                     text = "Height Ratio")
        # labelHeight.grid(column=0, row=1, ipadx=5, pady=5, sticky=W+S)

        # entryWidth = Entry(self.background, width=20)
        # entryHeight = Entry(self.background, width=20)

        # entryWidth.grid(column=1, row=0, padx=10, pady=5, sticky=N)
        # entryHeight.grid(column=1, row=1, padx=10, pady=5, sticky=S)

        # Button(self.background, text = 'left button', padx = 10, pady = 10).grid(column=0, row=0, sticky='NW')
        # Button(self.background, text = 'middle button').grid(column=1, row=0, sticky='NW')
        # Button(self.background, text = 'right button').grid(column=2, row=0, sticky='NW')

        self.window.mainloop()

    def show_window(self):
        self.window.mainloop()

def main():
    gui = car_detection_gui()
    gui.show_window()

if __name__ == '__main__':
    main()
