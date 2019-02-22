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
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
from matplotlib.figure import Figure
from numpy import arange, sin, pi
from kivy.app import App
from kivy.uix.textinput import TextInput
import numpy as np
from matplotlib.mlab import griddata
from kivy.garden.matplotlib.backend_kivy import FigureCanvas, NavigationToolbar2Kivy

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from matplotlib.transforms import Bbox
from kivy.uix.button import Button
from kivy.graphics import Color, Line, Rectangle

import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

from enum import Enum
import threading
import time

class SMState(Enum):
    notConnected = 1
    connected = 2
    waitingForData = 3

class ButtonState(Enum):
    connect = 1
    disconnect = 2
    scan = 3

# als have is connected and device, how do i use those with the enum above
# should i squash them?

fig, ax = plt.subplots()

X = []
Y = []

plt.scatter(X,Y)

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
            Button:
                text: 'Save'
                on_release: root.saveToFile(self.state)

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


class MainView(Widget):
    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        self._smState = SMState.notConnected
        self._button = ButtonState.scan
        self._freshData = False
        self._stopWaiting = threading.Event()
        self._child = None
        self.rv.data = [{'text': str(x)} for x in AllDevices]

    def Populate(self):
        self.rv.data = [{'text': str(x)} for x in AllDevices]
        print(self.rv.data )

    def promptDialog(self, state):
        modal = ModalView(title="Continue?", size_hint=(0.5, 0.3))
        label = Label(text="Currently waiting for Data. Do you want to disconnect?", size_hint=(1,.7))
        btn_ok = Button(text="Yes", on_press=self.promptDialogYes, on_release=modal.dismiss)
        btn_no = Button(text="No", on_release=modal.dismiss)

        outerbox = BoxLayout(orientation='vertical')
        box = BoxLayout(spacing=10, size_hint=(1,.3), padding=[10,10,10,10]);
        box.add_widget(btn_ok)
        box.add_widget(btn_no)
        outerbox.add_widget(label)
        outerbox.add_widget(box)

        modal.add_widget(outerbox)
        modal.open()

    def promptDialogYes(self, state):
        self._stopWaiting.set()
        if (self._child):
            self._child.join()
        self._promptDialogResult = True

    def scan(self, state):
        if (self._smState == SMState.waitingForData):
            print "DEBUG: in scan: waitingfordata"
            self._button = ButtonState.scan
            self.promptDialog(state)
            return
        else:
            self.do_scan(state)

    def do_scan(self, state):
        global AllDevices
        global device
        AllDevices = []

        
        device = 0
        self.devices = scanble(timeout=2)
        try:
            for device in self.devices:
                if(device['name']  != "(unknown)"):
                    AllDevices.append((device['name'], device['addr']))
            if (len(AllDevices) == 0):
                AllDevices = ['No Device Found']
        except:
            AllDevices = ['No Device Found']
            device = -1
        
    def connect(self,state):
        if (self._smState == SMState.waitingForData):
            self._button = ButtonState.connect
            self.promptDialog(state)
            return
        else:
            self.do_connect(state)
        
    def do_connect(self, state):
        global device
        global AllDevices
        global isConnected

        if(device != -1 and isConnected is False):
            try:
                device = BLEDevice(SelectedDevice)
                print "DEBUG ..device initialized"
                AllDevices = ['Connected']
                isConnected = True
                self._smState = SMState.connected
            except:
                print "DEBUG: in exception block for connect"
                AllDevices = ['Not able to connect']
        elif (isConnected is True):
            self.promptWithCustomString(state, 'Already Connected to {0}'.format(device['name']))
        else:
            AllDevices = ['No Devices to Connect']


    def disconnect(self,state):
        if (self._smState == SMState.waitingForData):
            self._button = ButtonState.disconnect
            self.promptDialog(state)
            return
        else:
            self.do_disconnect(state)
        
    def do_disconnect(self, state):
        global isConnected
        global device
        isConnected = False
        global AllDevices
        AllDevices = []
        device = -1
        self._smState = SMState.notConnected

    def saveToFile(self, state):
        if (not self._freshData):
            self.promptWithCustomString(state, "No fresh data to save")
            return

        self._stopWaiting.set()
        self._child.join()
        filename = "{0}.csv".format("PlotDemo")
        with open(filename, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows([('Voltage', 'Current')] + \
                [(self.newV[i], self.newI[i]) for i in range(len(self.newV))])

        csvFile.close()
        self.promptWithCustomString(state, "File saved in PlotDemo.csv")

    def promptWithCustomString(self, state, message):
        modal = ModalView(title="Message", size_hint=(0.5, 0.3))
        label = Label(text=message, size_hint=(1,.7))
        btn_ok = Button(text="Okay", on_press=modal.dismiss)

        outerbox = BoxLayout(orientation='vertical')
        box = BoxLayout(spacing=10, size_hint=(1,.3), padding=[10,10,10,10]);
        box.add_widget(btn_ok)
        outerbox.add_widget(label)
        outerbox.add_widget(box)

        modal.add_widget(outerbox)
        modal.open()

    def PlotIV(self, state):
        if (not self._freshData):
            self.promptWithCustomString(state, "No fresh data to plot")
            return
        self.plotReadyData(state)

    def plotReadyData(self, state):
        plt.cla()
        X = np.random.randint(50, size=50)
        Y = np.random.randint(50, size=50)
        V = []
        I = []
        status = 'V'
        val = ""
        flag = True
        corrupt = False

        for i in range(1, len(plotData)):
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
        self.newV = []
        self.newI = []
        tolerance = 0.2
        for i in range(1,len(V)):
                self.newV.append(V[i])
                self.newI.append(I[i])

        plt.scatter(self.newV, self.newI)

        ax.set_ylabel('Current (I)', fontsize=20)
        ax.set_title('I-V Curve', fontsize=30)
        ax.set_xlabel('Voltage (V)', fontsize=20)
        ax.tick_params(axis='both', which='major', labelsize=20)

        canvas.draw()

    def RequestData(self, state):
        global device
        global plotData
        global AllDevices

        print "DEBUG: in RequestData"
        if (self._smState == SMState.connected):
            self._stopWaiting.set()

            if (self._child):
                self._child.join()
            print "DEBUG: About to start test on thread"
            AllDevices = ["Requested Data"]
            self._smState = SMState.waitingForData
            print "DEBUG: changed state to waiting for data"
            self._child = threading.Thread(target=self.processRequest, args=(state,))
            self._stopWaiting.clear()
            self._child.start()

        elif (self._smState == SMState.notConnected):
            self.promptWithCustomString(state, "Please Connect to a device before requesting data")

        else:
            self.promptWithCustomString(state, "Already Waiting for Data")

    def processRequest(self, state):
        global device
        global plotData
        global AllDevices

        start_time = time.time();

        if(isConnected is True):
            plotData = ""
            AllDevices = ["Requested Data"]
            device.writecmd(device.getvaluehandle(WRITE_CHAR), "T".encode('hex'))

            while(True):
                data = device.notify()
                if (self._stopWaiting.isSet() or (time.time() - start_time > 145)):
                    print "DEBUG: stopped waiting"
                    self._freshData = False
                    self._smState = SMState.connected
                    AllDevices = ['Timed Out']
                    plotData = []
                    break

                if(data is not None):
                    plotData = plotData + data
                    print(data)
                    if data[-1] == 'E':
                        self._freshData = True
                        self._smState = SMState.connected;
                        print "DEBUG: got all data"
                        break

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
        save = Button(text="Save", height=100, size_hint_y=None)
        save.bind(on_release=mv.saveToFile)
        Plot = Button(text="Plot I-V", height=100, size_hint_y=None)
        Plot.bind(on_release = mv.PlotIV)

        button.add_widget(scan)
        button.add_widget(connect)
        button.add_widget(disconnect)
        button.add_widget(reqdata)
        button.add_widget(Plot)
        button.add_widget(save)
        root.add_widget(fl)

        return root


if __name__ == '__main__':
    PlotDemo().run()
