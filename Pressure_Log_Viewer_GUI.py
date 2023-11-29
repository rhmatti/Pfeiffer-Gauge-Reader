import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.animation as animation
import numpy as np
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import threading
import time
import os
import sys

#Enables multi-threading so that function will not freeze main GUI
def multiThreading(function):
    t1=threading.Thread(target=function)
    t1.setDaemon(True)      #This is so the thread will terminate when the main program is terminated
    t1.start()

def startProgram(root=None):
    instance = Pressure_Plotter()
    instance.makeGui(root)


#Defines location of the Desktop as well as font and text size for use in the software
desktop = os.path.expanduser("~\Desktop")
font1 = ('Helvetica', 18)
font2 = ('Helvetica', 16)
font3 = ('Helvetica', 14)
font4 = ('Helvetica', 12)
textSize = 20

colors = [[0.368417,0.506779,0.709798],[0.880722,0.611041,0.142051],[0.560181,0.691569,0.194885],\
          [0.922526,0.385626,0.209179],[0.528488,0.470624,0.701351],[0.772079,0.431554,0.102387]]

class Pressure_Plotter:
    def __init__(self):
        #Defines global variables
        self.canvas = None
        self.fig = None
        self.ax = None
        self.toolbar = None
        self.update = False
        self.first = True
        
        self.work_dir = None
        self.header = None
        self.times = np.full(int(1e4), time.time() ,dtype="datetime64[us]")
        self.pressures = np.zeros(int(1e4))
        self.filename = None

        #Loads the variables V and R from the variables file, and creates the file if none exists
        try:
            f = open('variables', 'r')
            variables = f.readlines()
            f.close()
            self.points = int(variables[0].split('=')[1])
            self.update = float(variables[1].split('=')[1])
            self.work_dir = str(variables[2].split('=')[1])
        except:
            self.points = 1e4
            self.update = False
            self.work_dir = desktop
            f = open("variables",'w')
            f.write(f'points={self.points}\nupdate={self.update}\n')
            f.write(f'work_dir={self.work_dir}')
            f.close()

    #Used to import a pressure log file into the software
    def askopenfile(self):
        try:
            newfile = filedialog.askopenfilename(initialdir = self.work_dir,title = "Select file",filetypes = (("all files","*.*"),("all files","*.*")))
        except:
            newfile = filedialog.askopenfilename(initialdir = desktop,title = "Select file",filetypes = (("all files","*.*"),("all files","*.*")))
        if newfile == '':
            return
        self.filename = newfile
        folders = newfile.split('/')
        self.work_dir = ''
        for i in range(0,len(folders)-1):
            self.work_dir = f'{self.work_dir}{folders[i]}/'

        self.updateSettings(self.points, self.update)

        self.read_log()

    def read_log(self, filename = None):
        if filename != None:
            self.filename = filename
        inputFile = open(self.filename, "r")
        start_line = 0
        header = False

        i = 0
        for line in inputFile:
            if not header:
                i = i + 1
                if 'Time\tPressure (Torr)' in line:
                    header = True
                    start_line = i
                    break

        inputFile.close()

        data = np.genfromtxt(self.filename, delimiter='\t', skip_header=start_line)
        if header == True:
            self.times = data[:,0]
            self.pressures = data[:,1]
        else:
            self.times = data[:,0]
            self.pressures = data[:,1]

        if len(self.times) > self.points:
            print(self.points)
            self.times = self.times[-self.points:]
            self.pressures = self.pressures[-self.points:]
        self.first = True

    def update_values(self):
        while True:
            if self.update == True and self.filename != None:
                with open(self.filename, 'rb') as f:
                    try:  # catch OSError in case of a one line file 
                        f.seek(-2, os.SEEK_END)
                        while f.read(1) != b'\n':
                            f.seek(-2, os.SEEK_CUR)
                    except OSError:
                        f.seek(0)
                    last_line = f.readline().decode().split('\t')

                last_time = float(last_line[0])
                last_pressure = float(last_line[1].strip('\r\n'))

                if self.times[-1] < last_time:
                    self.times = np.roll(self.times,-1)
                    self.times[-1] = last_time
                    self.pressures = np.roll(self.pressures,-1)
                    self.pressures[-1] = last_pressure

                    self.avgs = self.moving_average(self.pressures)

            time.sleep(1)
        
    
    def animate_fig(self, _):
        if self.update or self.first:
            self.first = False
            self.ax.clear()

            #self.ax.plot(self.times, self.pressures, label='Raw Value')
            self.ax.plot(self.times, self.pressures, color = colors[0], linestyle = '-', linewidth = 2)
            self.ax.set_xlim(np.amin(self.times), np.amax(self.times))
            #self.ax.plot(self.times, self.avgs, label='Moving Average')

            #self.ax.legend()

            self.ax.set_ylabel('Pressure (Torr)')
            self.ax.set_xlabel('Epoch Time (s)')
            self.ax.get_yaxis().set_major_formatter("{x:.2e}")
            self.ax.set_yscale('log')
            self.ax.set_title(f'Current Pressure - {self.pressure[-1]} Torr')
    
    def moving_average(self, array):
        n = 15
        ret = np.cumsum(array, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        for i in range(min(n, len(ret))):
            ret[i] = n * array[0]
        return ret / n

    def quitProgram(self):
        print('quit')
        self.root.quit()
        self.root.destroy()

        #Opens Settings Window, which allows the user to change the persistent global variables V and R
    def Settings(self):
        t = Toplevel(self.root)
        t.geometry('400x300')
        t.wm_title("Settings")
        t.configure(bg='grey95')
        L0 = Label(t, text = 'Settings', font = font3)
        L0.place(relx=0.5, rely=0.15, anchor = CENTER)
        L1 = Label(t, text = ' # of Points:', font = font2)
        L1.place(relx=0.4, rely=0.3, anchor = E)
        E1 = Entry(t, font = font2, width = 10)
        E1.insert(0,str(self.points))
        E1.place(relx=0.4, rely=0.3, anchor = W)

        update = IntVar(value=int(self.update))
        check1 = Checkbutton(t, text="Live Update", variable=update, onvalue = 1, offvalue = 0, bg='white', font = font4)
        check1.place(relx=0.4, rely=0.5, anchor=CENTER)
            
        b1 = Button(t, text = 'Update', relief = 'raised', background='lightblue', activebackground='blue', font = font1, width = 10, height = 1,\
                    command = lambda: [self.updateSettings(int(E1.get()),update.get()),t.destroy()])
        b1.place(relx=0.75, rely=0.8, anchor = CENTER)

        b2 = Button(t, text = 'Reset', relief = 'raised', background='pink', activebackground='red', font = font1, width = 10, height = 1, command = lambda: [self.updateSettings(1e4,1),t.destroy()])
        b2.place(relx=0.25, rely=0.8, anchor = CENTER)

    #Updates the persistent global variables V and R, as well as store which elements the user has selected for calibration
    def updateSettings(self, E1, E2):
        self.points = E1
        self.update = E2
        f = open("variables",'w')
        f.write(f'points={self.points}\nupdate={self.update}\n')
        f.write(f'work_dir={self.work_dir}')
        f.close()
        if self.filename != None:
            self.read_log()

    #This is the GUI for the software
    def makeGui(self, root=None):
        global first
        if root == None:
            self.root = Tk()
        else:
            self.root = root
        menu = Menu(self.root)
        self.root.config(menu=menu)

        self.root.title("Pfeiffer Gauge Pressure Logger")
        self.root.geometry("1200x768")
        self.root.configure(bg='white')
        self.root.protocol("WM_DELETE_WINDOW", self.quitProgram)

        #Creates intro message
        introMessage ='Import a data file to begin'
        introMessageVar = Message(self.root, text = introMessage, font = font2, width = 600)
        introMessageVar.config(bg='white', fg='grey')
        introMessageVar.place(relx = 0.5, rely = 0.5, anchor = CENTER)
        introMessageVar.bind('<Button-1>', lambda  eff: self.askopenfile())

        #Creates File menu
        filemenu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Import", command=lambda: self.askopenfile(), accelerator="Ctrl+I")
        filemenu.add_command(label='Settings', command=lambda: self.Settings())
        filemenu.add_separator()
        filemenu.add_command(label='New Window', command=lambda: startProgram(Toplevel(self.root)))
        filemenu.add_command(label='Exit', command=lambda: self.quitProgram())


        #Binds keyboard shortcuts to functions
        self.root.bind_all("<Control-i>", lambda eff: self.askopenfile())

        #Allows another program to open spectrum analyzer and provide an input file to be read
        if len(sys.argv) > 1 and first:
            print('Program started remotely by another program')
            self.getData(sys.argv[1])
            first = False

        
        ''''
        self.fig, self.ax = plt.subplots(figsize = (16,9))
        self.ax.tick_params(which='both', direction='in')
        plt.rcParams.update({'font.size': textSize})
        # creating the Tkinter canvas containing the Matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()

        # creating the toolbar and placing it
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=BOTTOM, fill=X)
        '''
        
        #Creates a Plot of the Magnet Power Supply Current
        self.fig = Figure(figsize=(16,9))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=BOTTOM, fill=X)

        #Setting the default save directory for matplotlib toolbar
        plt.rcParams["savefig.directory"] = self.work_dir

        # placing the canvas on the Tkinter window
        self.canvas.get_tk_widget().pack(side="top",fill='both',expand=True)
        
        self.ani = animation.FuncAnimation(self.fig, self.animate_fig, interval = 1000)

        multiThreading(self.update_values)
        self.root.mainloop()

startProgram()