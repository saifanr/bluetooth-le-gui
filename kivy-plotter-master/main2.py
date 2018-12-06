from kivy.app import App
from plot import Plot, SeriesController
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
import csv
import sys, time
from bledevice import scanble, BLEDevice
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.button import Button

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
from matplotlib.figure import Figure
from numpy import arange, sin, pi
from kivy.app import App

import numpy as np
from matplotlib.mlab import griddata
from kivy.garden.matplotlib.backend_kivy import FigureCanvas,\
                                                NavigationToolbar2Kivy

# from backend_kivy import FigureCanvasKivy as FigureCanvas

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from matplotlib.transforms import Bbox
from kivy.uix.button import Button
from kivy.graphics import Color, Line, Rectangle

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

# fig, ax = plt.subplots()
fig, ax = plt.subplots()

#X = np.arange(-508, 510, 203.2, 444, 1111)
#Y = np.arange(-508, 510, 203.2, 444, 123)
#X, Y = np.meshgrid(X, Y)


X = []
Y = []

#plt.contourf(X, Y, Z, 100, zdir='z', offset=1.0, cmap=cm.hot)

plt.scatter(X,Y)
#plt.colorbar()

ax.set_ylabel('Current (I)', fontsize=20)
ax.set_title('I-V Curve', fontsize=30)
ax.set_xlabel('Voltage (V)', fontsize=20)
ax.tick_params(axis='both', which='major', labelsize=20)

canvas = fig.canvas



Builder.load_string("""
<MainView>:
    #plot: plot
    orientation: 'horizontal'
    rv: rv
    BoxLayout:
        width: root.width
        height: root.height
        center_x: root.width * 4.47
        center_y: root.height / 2
        orientation: 'vertical'
        spacing: 10
        padding: 10
        BoxLayout:
            size_hint: None, None
            pos_hint: {'center_x': 0, 'center_y': 0}
            size_hint: (1, .4)
            orientation: 'vertical'
            spacing: 10
            Button:
                text: 'Scan'
                on_press: root.scan(self.state)
                on_release: root.Populate()
            Button:
                text: 'Connect'
                on_press: root.connect(self.state)
                on_release: root.Populate()
            Button:
                text: 'Disconnect'
                on_press: root.disconnect(self.state)
                on_release: root.Populate()
            Button:
                text: 'Request Data'
                on_release: root.RequestData(self.state)
            Button:
                text: 'Plot I-V'
                on_release: root.PlotIV(self.state)

        RecycleView:
            pos_hint: {'center_x': 0, 'center_y': 0}
            size_hint: (1, 0.6)
            spacing: 10
            viewclass: 'SelectableLabel'
            id: rv
            SelectableRecycleBoxLayout:
                default_size: None, dp(80)
                default_size_hint: 1, 1
                size_hint_y: 1
                size_hint_x: 1
                height: self.minimum_height
                orientation: "vertical"



<SelectableLabel>:
    # Draw a background to indicate selection
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    """)
def isfloat(val):
    try:
        float(val)
        return True
    except ValueError:
        return False



WRITE_CHAR = "ffe1"
READ_CHAR = "ffe4"
AllDevices = []
device = -1
SelectedDevice = -1
isConnected = False
AskForData = "T"
END = 'E'
plotData = ""

def get_data_from_csv(csvfile, has_header=True):
    with open(csvfile, 'r') as inf:
        reader = csv.reader(inf)
        for idx, line in enumerate(reader):
            if idx == 0 and has_header: continue
            yield (float(line[0]), float(line[1]))



class MainView(Widget):
    #plot = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        self.rv.data = [{'text': str(x)} for x in AllDevices]
        #self.series_controller = SeriesController(self.plot)

    def Populate(self):
        self.rv.data = [{'text': str(x)} for x in AllDevices]
        print(self.rv.data )


    def scan(self,state):
        global AllDevices
        global device
        AllDevices = []

        try:
            device = 0
            self.devices = scanble(timeout=2)
            for device in self.devices:
                if(device['name']  != "(unknown)"):
                    AllDevices.append((device['name'],device['addr']))
        except:
            AllDevices = ['No Devices Found :( ']
            device = -1


    def connect(self,state):
        global device
        global AllDevices
        global isConnected
        if(device != -1 and isConnected is False):
            try:
                device = BLEDevice(SelectedDevice)
                AllDevices = ['Connected!!']
                isConnected = True
            except:
                AllDevices = ['Not able to connect!']
        elif(isConnected is True):
            AllDevices = ['Connected!!']
        else:

            AllDevices = ['No Devices to Connect']


    def disconnect(self,state):
        global isConnected
        global device
        isConnected = False
        global AllDevices
        AllDevices = []
        device = -1

    def PlotIV(self, state):

        plt.cla()
        X = np.random.randint(50, size=50)
        Y = np.random.randint(50, size=50)
        V = []
        I = []
        status = 'V'
        val = ""
        flag = True
        corrupt = False

        for i in range(1,len(plotData)):
            if(plotData[i] == 'V' or plotData[i] == 'I'):
                if (plotData[i] == status):
                    if(status == 'V'):
                        pass
                    else:
                        if(isfloat(val)):
                            flag = False
                            status = 'I'
                            if(len(I) < len(V)):
                                I.append(float(val))
                        else:
                            corrupt = True
                            if(len(V) > len((I))):
                                V.pop()
                else:
                    corrupt = False
                    if(plotData[i] == 'V'):
                        if(isfloat(val)):
                            if(flag is False):
                                flag = True
                                status = 'V'
                            else:
                                status = 'V'
                                if(corrupt ):
                                    corrupt = False
                                else:
                                    I.append(float(val))
                        else:
                            if(len(V) > len((I))):
                                V.pop()
                            status = 'V'
                    else:
                        if(isfloat(val)):
                            status = 'I'
                            V.append(float(val))
                            #corrupt = False
                        else:
                            corrupt = True
                            status = 'I'
                val = ""
            elif(plotData[i] == 'E'):
                if(isfloat(val) and len(I) < len(V)):
                    I.append(float(val))
            else:
                val = val + plotData[i]

        R = V[0] / I[0]
        newV = []
        newI = []
        tolerance = 0.2
        for i in range(1,len(V)):
            if abs(I[i] - V[i] / R) < tolerance:
                newV.append(V[i])
                newI.append(I[i])

        plt.scatter(newV, newI)
        ax.set_ylabel('Current (I)', fontsize=20)
        ax.set_title('I-V Curve', fontsize=30)
        ax.set_xlabel('Voltage (V)', fontsize=20)
        ax.tick_params(axis='both', which='major', labelsize=20)


        canvas.draw()

    def RequestData(self, state):
        global device
        global plotData
        if(isConnected is True):
            #try:
                plotData = ""
                device.writecmd(device.getvaluehandle(WRITE_CHAR), "T".encode('hex'))
                #try:
                while(True):
                    data = device.notify()
                    if(data is not None):
                        plotData = plotData + data
                        print(data)
                        if data[-1] == 'E':
                            break
                #except:
                 #   print("Incorrect Data")
            #except:
                #print("Something went wrong, try Again")


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''

class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected and not isConnected:
            print("selection changed to {0}".format(rv.data[index]))
            global SelectedDevice
            try:
                SelectedDevice = rv.data[index]['text'][1:-1].split(',')[1]
                print(rv.data[index]['text'][1:-1].split(',')[1])
            except:
                print("not a valid device")

        else:
            print("selection removed for {0}".format(rv.data[index]))



import inspect


class PlotDemo(App):
    def build(self):
        mv = MainView()

        root = BoxLayout(orientation="vertical")
        fl = BoxLayout(orientation="horizontal", size_hint=(1, 0.9))
        fl1 = BoxLayout(orientation="horizontal", size_hint=(3.5, 1))
        fl1.add_widget(canvas)
        fl.add_widget(fl1)
        fl.add_widget(MainView())

        button = BoxLayout(orientation="horizontal", size_hint=(1, .1))
        scan = Button(text="Scan", height=100, size_hint_y=None)

        scan.bind(on_release = mv.scan)


        connect = Button(text="Connect", height=100, size_hint_y=None)
        connect.bind(on_release = mv.connect)
        disconnect = Button(text="disconnect", height=100, size_hint_y=None)
        disconnect.bind(on_release = mv.disconnect)
        reqdata = Button(text="Request Data", height=100, size_hint_y=None)
        reqdata.bind(on_release = mv.RequestData)
        Plot = Button(text="Plot I-V", height=100, size_hint_y=None)
        Plot.bind(on_release = mv.PlotIV)

        button.add_widget(scan)
        button.add_widget(connect)
        button.add_widget(disconnect)
        button.add_widget(reqdata)
        button.add_widget(Plot)
        root.add_widget(fl)
        #root.add_widget(button)

        return root



if __name__ == '__main__':
    PlotDemo().run()
