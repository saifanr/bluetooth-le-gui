from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior


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

X = np.arange(-508, 510, 203.2)
Y = np.arange(-508, 510, 203.2)
X, Y = np.meshgrid(X, Y)

Z = np.random.rand(6, 6)

plt.contourf(X, Y, Z, 100, zdir='z', offset=1.0, cmap=cm.hot)
plt.colorbar()

ax.set_ylabel('Y [mm]')
ax.set_title('NAILS surface')
ax.set_xlabel('X [mm]')

canvas = fig.canvas



def callback(instance):

    global fig, ax
    # fig, ax = plt.subplots()

    X = np.arange(-508, 510, 203.2)
    Y = np.arange(-508, 510, 203.2)
    X, Y = np.meshgrid(X, Y)

    Z = 1000*np.random.rand(6, 6)
    plt.clf()
    plt.contourf(X, Y, Z, 100, zdir='z', offset=1.0, cmap=cm.hot)
    plt.colorbar()

    # ax.set_ylabel('Y [mm]')
    # ax.set_title('NAILS surface')
    # ax.set_xlabel('X [mm]')

    # canvas = fig.canvas
    canvas.draw()


class MatplotlibTest(App):
    title = 'Matplotlib Test'

    def build(self):
        root = BoxLayout(orientation = "horizontal")
        fl0 = RV(viewclass= 'SelectableLabel', size_hint=(0.2, 1))

        select = SelectableRecycleBoxLayout( default_size_hint= (1, 1), orientation="vertical")

        fl = BoxLayout(orientation="vertical", size_hint=(0.8, 1))
        fl1 = BoxLayout(orientation="vertical", size_hint=(1, .9))
        fl2 = BoxLayout(orientation="horizontal", size_hint=(1, .1))
        scan = Button(text="Scan", height=100, size_hint_y=None)
        connect = Button(text="Connect", height=100, size_hint_y=None)
        disconnect = Button(text="disconnect", height=100, size_hint_y=None)
        reqdata = Button(text="Request Data", height=100, size_hint_y=None)
        Plot = Button(text="Plot I-V", height=100, size_hint_y=None)

        scan.bind(on_press=callback)

        fl0.add_widget(select)
        fl1.add_widget(canvas)
        fl2.add_widget(scan)
        fl2.add_widget(connect)
        fl2.add_widget(disconnect)
        fl2.add_widget(reqdata)
        fl2.add_widget(Plot)
        fl.add_widget(fl1)
        fl.add_widget(fl2)

        root.add_widget(fl)
        root.add_widget(fl0)
        return root



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
                #print(rv.data[index]['text'][1:-1].split(',')[1])
            except:
                print("not a valid device")

        else:
            print("selection removed for {0}".format(rv.data[index]))

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(10)]

    def Populate(self):
        self.data = [{'text': str(x)} for x in range(10)]
        print(self.data )

if __name__ == '__main__':
    MatplotlibTest().run()
