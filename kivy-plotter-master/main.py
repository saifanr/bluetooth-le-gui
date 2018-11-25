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
import matplotlib.pyplot as plt

Builder.load_string("""
<MainView>:
    plot: plot
    orientation: 'horizontal'
    BoxLayout:
        width: root.width * 4/5
        height: root.height
        center_x: root.width * 2/5
        center_y: root.height * 1/2
        orientation: 'vertical'
        spacing: 10
        padding: 10
        Plot:
            id: plot
            size_hint: None, None
            pos_hint: {'center_x': 0.5, 'center_y': 0}
            size_hint: (1, .9)
            viewport: [0,0,30,30]
            tick_distance_x: 2
            tick_distance_y: 2
        BoxLayout:
            size_hint: None, None
            pos_hint: {'center_x': 0.5, 'center_y': 0}
            size_hint: (1, .1)
            orientation: 'horizontal'
            spacing: 10
            Button:
                text: "Scan"
                on_release: Recycle.Populate()
                on_release: root.scan(self.state)

            Button:
                text: "Connect"
                on_release: Recycle.Populate()
                on_release: root.connect(self.state)

            Button:
                text: "Disconnect"
                on_release: Recycle.Populate()
                on_release: root.disconnect(self.state)

            Button:
                text: "Request Data"
                on_release: root.RequestData(self.state)

            ToggleButton:
                text: "Plot I-V Curve"
                on_release: root.PlotIV(self.state)
    RV:
        width: root.width * 1/5
        height: root.height
        center_x: root.width * 0.9
        center_y: root.height * 1/2
        viewclass: 'SelectableLabel'
        id: Recycle
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
WRITE_CHAR = "ffe1"
READ_CHAR = "ffe4"
AllDevices = ["Device 1","Device 2"]
device = -1
SelectedDevice = -1
isConnected = False
AskForData = "AD"

def get_data_from_csv(csvfile, has_header=True):
    with open(csvfile, 'r') as inf:
        reader = csv.reader(inf)
        for idx, line in enumerate(reader):
            if idx == 0 and has_header: continue
            yield (float(line[0]), float(line[1]))


class MainView(Widget):
    plot = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainView, self).__init__(**kwargs)
        self.series_controller = SeriesController(self.plot)

    def scan(self,state):
        global AllDevices
        global device
        AllDevices = []
        try:
            device = 0
            self.devices = scanble(timeout=3)
            for device in self.devices:
                if(device['name']  != "(unknown)"):
                    AllDevices.append((device['name'],device['addr']))
        except:
            AllDevices = ['No Devices Found :( ']
            device = -1


    def connect(self,state):
        global device
        if(device != -1):
            device
            device = BLEDevice(SelectedDevice)
            global AllDevices
            global isConnected
            AllDevices = ['Connected!!']
            isConnected = True

        else:
			global AllDevices
			AllDevices = ['No Devices to Connect']

    def disconnect(self,state):
        global isConnected
        global device
        isConnected = False
        global AllDevices
        AllDevices = []
        device = -1

    def PlotIV(self, state):
        if state == 'down':
            try:
                self.series_controller.enable('Plot I-V Curve')
            except KeyError:
                xy_data = [t for t in get_data_from_csv('sample_data_1.csv')]
                self.series_controller.add_data('Plot I-V Curve', xy_data, marker='plus')
                self.series_controller.enable('Plot I-V Curve')
        else:
            self.series_controller.disable('Plot I-V Curve')
        self.series_controller.fit_to_all_series()

    def RequestData(self, state):
        global device
        if(isConnected is True):
            try:
                device.writecmd(device.getvaluehandle(WRITE_CHAR), AskForData)
                while(data != End):
                    data = device.notify()
                    print(data)
            except:
                print("Something went wrong, try Again")


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


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in AllDevices]

    def Populate(self):
        self.data = [{'text': str(x)} for x in AllDevices]
        print(self.data )

class PlotDemo(App):
    def build(self):
        return MainView()



class TestApp(App):
    def build(self):
        return RV()

if __name__ == '__main__':
    PlotDemo().run()
