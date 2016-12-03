#!/user/local/bin python
import time
import wx
import os
import subprocess
import signal
import re
import astropy
from astropy.time import Time
import thread
import threading
import ephem
import matplotlib
import datetime as dati
from datetime import datetime, timedelta
import math
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as dt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
import matplotlib.image as mpimg
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from pytz import timezone
import scipy
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from scipy import linspace, polyval, polyfit, sqrt, stats, randn
from astroplan import Observer, FixedTarget
from astroplan.plots import plot_sky,plot_airmass
import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Galactic, FK4, FK5
#from astroplan.plots.finder import plot_finder_image
from Finder_picker import plot_finder_image
from astroquery.skyview import SkyView
import wcsaxes

from twisted.internet import wxreactor
wxreactor.install()
from twisted.internet import reactor, protocol, defer
from twisted.protocols import basic

global pipe
pipe=None

class Control(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)
        
        #self.parent = parent
        
        self.logBox = wx.TextCtrl(self,size=(600,200), style= wx.TE_READONLY | wx.TE_MULTILINE | wx.VSCROLL)

        #Input individual target, use astropy and a lot of error checking to solve format failures
        self.targetNameLabel = wx.StaticText(self, size=(75,-1))
        self.targetNameLabel.SetLabel('Name: ')
        self.targetNameText = wx.TextCtrl(self,size=(100,-1))

        self.targetRaLabel = wx.StaticText(self, size=(75,-1))
        self.targetRaLabel.SetLabel('RA: ')
        self.targetRaText = wx.TextCtrl(self,size=(100,-1))

        self.targetDecLabel = wx.StaticText(self, size=(75,-1))
        self.targetDecLabel.SetLabel('DEC: ')
        self.targetDecText = wx.TextCtrl(self,size=(100,-1))

        self.targetEpochLabel = wx.StaticText(self, size=(75,-1))
        self.targetEpochLabel.SetLabel('EPOCH: ')
        self.targetEpochText = wx.TextCtrl(self,size=(100,-1))

        self.targetMagLabel = wx.StaticText(self, size=(75,-1))
        self.targetMagLabel.SetLabel('V Mag: ')
        self.targetMagText = wx.TextCtrl(self,size=(100,-1))

        #Current Positions
        self.currentNameLabel = wx.StaticText(self, size=(75,-1))
        self.currentNameLabel.SetLabel('Name:')
        self.currentNamePos = wx.StaticText(self,size=(100,-1))
        self.currentNamePos.SetLabel('Unknown')
        self.currentNamePos.SetForegroundColour((255,0,0))

        self.currentRaLabel = wx.StaticText(self, size=(75,-1))
        self.currentRaLabel.SetLabel('RA: ')
        self.currentRaPos = wx.StaticText(self,size=(100,-1))
        self.currentRaPos.SetLabel('Unknown')
        self.currentRaPos.SetForegroundColour((255,0,0))

        self.currentDecLabel = wx.StaticText(self, size=(75,-1))
        self.currentDecLabel.SetLabel('DEC: ')
        self.currentDecPos = wx.StaticText(self,size=(100,-1))
        self.currentDecPos.SetLabel('Unknown')
        self.currentDecPos.SetForegroundColour((255,0,0))

        self.currentEpochLabel = wx.StaticText(self, size=(75,-1))
        self.currentEpochLabel.SetLabel('EPOCH: ')
        self.currentEpochPos = wx.StaticText(self,size=(75,-1))
        self.currentEpochPos.SetLabel('Unknown')
        self.currentEpochPos.SetForegroundColour((255,0,0))

        self.currentUTCLabel = wx.StaticText(self, size=(75,-1))
        self.currentUTCLabel.SetLabel('UTC: ')
        self.currentUTCPos = wx.StaticText(self,size=(150,-1))
        self.currentUTCPos.SetLabel('Unknown')
        self.currentUTCPos.SetForegroundColour((255,0,0))

        self.currentLSTLabel = wx.StaticText(self, size=(75,-1))
        self.currentLSTLabel.SetLabel('LST: ')
        self.currentLSTPos = wx.StaticText(self,size=(100,-1))
        self.currentLSTPos.SetLabel('Unknown')
        self.currentLSTPos.SetForegroundColour((255,0,0))

        self.currentLocalLabel = wx.StaticText(self, size=(75,-1))
        self.currentLocalLabel.SetLabel('Local: ')
        self.currentLocalPos = wx.StaticText(self,size=(150,-1))
        self.currentLocalPos.SetLabel('Unknown')
        self.currentLocalPos.SetForegroundColour((255,0,0))

        self.currentJDLabel = wx.StaticText(self, size=(75,-1))
        self.currentJDLabel.SetLabel('MJD: ')
        self.currentJDPos = wx.StaticText(self,size=(75,-1))
        self.currentJDPos.SetLabel('Unknown')
        self.currentJDPos.SetForegroundColour((255,0,0))


        self.currentFocusLabel = wx.StaticText(self, size=(75,-1))
        self.currentFocusLabel.SetLabel('Focus: ')
        self.currentFocusPos = wx.StaticText(self,size=(75,-1))
        self.currentFocusPos.SetLabel('Unknown')
        self.currentFocusPos.SetForegroundColour((255,0,0))

        self.currentRATRLabel = wx.StaticText(self, size=(75,-1))
        self.currentRATRLabel.SetLabel('RA TR: ')
        self.currentRATRPos = wx.StaticText(self,size=(75,-1))
        self.currentRATRPos.SetLabel('15.04')
        self.currentRATRPos.SetForegroundColour("black")
        
        self.currentDECTRLabel = wx.StaticText(self, size=(75,-1))
        self.currentDECTRLabel.SetLabel('DEC TR: ')
        self.currentDECTRPos = wx.StaticText(self,size=(75,-1))
        self.currentDECTRPos.SetLabel('Unknown')
        self.currentDECTRPos.SetForegroundColour((255,0,0))


        #Focus Change
        self.focusIncPlusButton = wx.Button(self, -1, 'Increment Positive')
        self.focusIncNegButton = wx.Button(self, -1, 'Increment Negative')
        self.focusAbsText = wx.TextCtrl(self,size=(75,-1))
        self.focusAbsText.SetValue('1500')
        self.focusAbsMove = wx.Button(self,-1,'Move Relative')


        self.slewButton = wx.Button(self, -1, "Slew to Target")
        self.slewButton.Disable()
        self.trackButton = wx.Button(self, -1, "Start Tracking")
        self.trackButton.Disable()

        self.stopButton = wx.Button(self, -1, "HALT MOTION")
        # self.stopButton.Bind(wx.EVT_ENTER_WINDOW, self.onMouseOver)

        #need to reposition these, they're all on top of each other in the
        #top left
        self.jogNButton = wx.Button(self, -1, 'N')
        self.jogSButton = wx.Button(self, -1, 'S')
        self.jogWButton = wx.Button(self, -1, 'W')
        self.jogEButton = wx.Button(self, -1, 'E')
        self.jogIncrement = wx.TextCtrl(self,size=(75,-1))
        self.jogIncrement.SetValue('5.0')
        
        #self.jogNButton.Disable()
        #self.jogSButton.Disable()
        #self.jogWButton.Disable()
        #self.jogEButton.Disable()
        
        #setup sizers
        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.vbox1=wx.BoxSizer(wx.VERTICAL)
        self.vbox2=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        self.gbox=wx.GridSizer(rows=5, cols=2, hgap=5, vgap=5)
        self.gbox2=wx.GridSizer(rows=11, cols=2, hgap=0, vgap=5)
        self.gbox3=wx.GridSizer(rows=2, cols=2, hgap=5, vgap=5)
        
        self.ctlabel = wx.StaticBox(self,label="Current Target")
        self.vbox3 = wx.StaticBoxSizer(self.ctlabel, wx.VERTICAL)
        
        self.TCCstatus=wx.StaticBox(self,label="TCC Status")
        self.vbox4= wx.StaticBoxSizer(self.TCCstatus, wx.VERTICAL)
        
        self.flabel=wx.StaticBox(self,label="Focus")
        self.vbox5= wx.StaticBoxSizer(self.flabel, wx.VERTICAL)
        
        self.jlabel=wx.StaticBox(self,label="Jog Telescope")
        self.vbox6= wx.StaticBoxSizer(self.jlabel, wx.VERTICAL)
        
        self.gbox.Add(self.targetNameLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetNameText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetRaLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetRaText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetDecLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetDecText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetEpochLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetEpochText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetMagLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetMagText, 0, wx.ALIGN_RIGHT)
        
        self.vbox3.Add(self.gbox,0,wx.ALIGN_CENTER)
        self.vbox1.Add(self.vbox3,0,wx.ALIGN_CENTER)


        self.gbox2.Add(self.currentNameLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentNamePos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentRaLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentRaPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentDecLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentDecPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentEpochLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentEpochPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentJDLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentJDPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentUTCLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentUTCPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentLocalLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentLocalPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentLSTLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentLSTPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentFocusLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentFocusPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentRATRLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentRATRPos, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.currentDECTRLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.currentDECTRPos, 0, wx.ALIGN_LEFT)
        
        self.vbox4.Add(self.gbox2,0,wx.ALIGN_CENTER)

        self.gbox3.Add(self.focusIncPlusButton, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusAbsText, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusIncNegButton, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusAbsMove, 0, wx.ALIGN_LEFT)
        
        self.vbox5.Add(self.gbox3,0,wx.ALIGN_CENTER)
        
        self.hbox3.Add(self.jogWButton,0,wx.ALIGN_LEFT)
        self.hbox3.AddSpacer(5)
        #Not conviced this is the best place for increment. Clunky and doesn't allow for labeling. Underneath seems better
        self.hbox3.Add(self.jogIncrement,0,wx.ALIGN_LEFT)
        self.hbox3.AddSpacer(5)
        self.hbox3.Add(self.jogEButton,0,wx.ALIGN_LEFT)
        
        self.vbox6.Add(self.jogNButton,0,wx.ALIGN_CENTER)
        self.vbox6.AddSpacer(5)
        self.vbox6.Add(self.hbox3,0,wx.ALIGN_CENTER)
        self.vbox6.AddSpacer(5)
        self.vbox6.Add(self.jogSButton,0,wx.ALIGN_CENTER)
        
        self.vbox2.Add(self.vbox5,0,wx.ALIGN_CENTER)
        self.vbox2.AddSpacer(5)
        self.vbox2.Add(self.vbox6,0,wx.ALIGN_CENTER)
    

        self.hbox1.Add(self.vbox4, 0, wx.ALIGN_CENTER)
        self.hbox1.AddSpacer(25)
        self.hbox1.Add(self.vbox1, 0, wx.ALIGN_CENTER)
        self.hbox1.AddSpacer(25)
        self.hbox1.Add(self.vbox2, 0, wx.ALIGN_CENTER)

        self.hbox2.Add(self.slewButton, 0, wx.ALIGN_CENTER)
        self.hbox2.AddSpacer(25)
        self.hbox2.Add(self.trackButton, 0, wx.ALIGN_CENTER)

        self.vbox.Add(self.hbox1,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.stopButton,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.logBox,0,wx.ALIGN_CENTER)

        self.SetSizer(self.vbox)

    
class Target(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)

        #setup the test and retrieval button for getting target list
        self.fileLabel=wx.StaticText(self, size=(125,-1))
        self.fileLabel.SetLabel('Target List Path: ')
        self.fileText=wx.TextCtrl(self,size=(400,-1))


        #show list of targets with selection button.  When the target is highlighted the selection button will input the data into the Control window.
        self.targetList=wx.ListCtrl(self,size=(525,200), style=wx.LC_REPORT | wx.VSCROLL)
        self.targetList.InsertColumn(0,'Target Name',width=125)
        self.targetList.InsertColumn(1,'RA',width=100)
        self.targetList.InsertColumn(2,'DEC',width=100)
        self.targetList.InsertColumn(3,'EPOCH',width=62.5)
        self.targetList.InsertColumn(5,'V Mag',width=62.5)
        self.targetList.InsertColumn(6,'Airmass',width=75)
        

        #Input individual target, use astropy and a lot of error checking to solve format failures
        self.nameLabel=wx.StaticText(self, size=(50,-1))
        self.nameLabel.SetLabel('Name: ')
        self.nameText=wx.TextCtrl(self,size=(100,-1))

        self.raLabel=wx.StaticText(self, size=(50,-1))
        self.raLabel.SetLabel('RA: ')
        self.raText=wx.TextCtrl(self,size=(100,-1))

        self.decLabel=wx.StaticText(self, size=(50,-1))
        self.decLabel.SetLabel('DEC: ')
        self.decText=wx.TextCtrl(self,size=(100,-1))

        self.epochLabel=wx.StaticText(self, size=(75,-1))
        self.epochLabel.SetLabel('EPOCH: ')
        self.epochText=wx.TextCtrl(self,size=(100,-1))

        self.magLabel=wx.StaticText(self, size=(75,-1))
        self.magLabel.SetLabel('V Mag: ')
        self.magText=wx.TextCtrl(self,size=(100,-1))
        
        #Buttons
        self.listButton = wx.Button(self, -1, "Retrieve List")
        self.selectButton = wx.Button(self, -1, "Select as Current Target")
        self.enterButton = wx.Button(self, -1, "Add Item to List")
        self.removeButton=wx.Button(self,-1,"Remove Item from List")
        self.exportButton=wx.Button(self,-1,"Export List")
        self.plot_button=wx.Button(self,-1,'Plot Target')
        self.airmass_button=wx.Button(self,-1,"Airmass Curve")
        
        self.listButton.Disable()
        self.selectButton.Disable()
        self.enterButton.Disable()
        self.removeButton.Disable()
        self.exportButton.Disable()
        self.plot_button.Disable()
        self.airmass_button.Disable()

        #setup sizers
        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        self.gbox=wx.GridSizer(rows=5, cols=2, hgap=5, vgap=5)

        self.hbox1.Add(self.fileLabel,0,wx.ALIGN_CENTER)
        self.hbox1.Add(self.fileText,0, wx.ALIGN_CENTER)
        self.hbox1.Add(self.listButton,0, wx.ALIGN_CENTER)


        self.gbox.Add(self.nameLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.nameText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.raLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.raText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.decLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.decText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.epochLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.epochText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.magLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.magText, 0, wx.ALIGN_RIGHT)

        self.hbox2.Add(self.targetList,0, wx.ALIGN_CENTER)
        self.hbox2.Add(self.gbox,0,wx.ALIGN_CENTER)

        self.hbox3.Add(self.selectButton,0, wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(25)
        self.hbox3.Add(self.enterButton,0, wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(25)
        self.hbox3.Add(self.removeButton,0, wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(25)
        self.hbox3.Add(self.exportButton,0, wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(25)
        self.hbox3.Add(self.plot_button,0,wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(25)
        self.hbox3.Add(self.airmass_button,0,wx.ALIGN_CENTER)

        self.vbox.Add(self.hbox1,0, wx.ALIGN_CENTER,5)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox2,0, wx.ALIGN_CENTER,5)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox3,0, wx.ALIGN_CENTER,5)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

        debug==True
        self.dir=os.getcwd()
			
class ScienceFocus(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)
        None
'''
        self.currentFocusLabel = wx.StaticText(self, size=(75,-1))
        self.currentFocusLabel.SetLabel('Focus: ')
        self.currentFocusPos = wx.StaticText(self,size=(75,-1))
        self.currentFocusPos.SetLabel('Unknown')
        self.currentFocusPos.SetForegroundColour((255,0,0))

#Focus Change
        self.focusIncPlusButton = wx.Button(self, -1, 'Increment Positive')
        self.focusIncNegButton = wx.Button(self, -1, 'Increment Negative')
        self.focusAbsText = wx.TextCtrl(self,size=(75,-1))
        self.focusAbsText.SetLabel('1500')
        self.focusAbsMove = wx.Button(self,-1,'Move Absolute')


        self.slewButton = wx.Button(self, -1, "Slew to Target")
        #self.slewButton.Disable()
        self.trackButton = wx.Button(self, -1, "Start Tracking")
        #self.trackButton.Disable()
'''
class Guider(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)

        #self.guiderTZLabel=wx.StaticText(self, size=(75,-1))
        #self.guiderTZLabel.SetLabel('Time Zone: ')
        #time_options=['Pacific','UTC']
        #self.guiderTZCombo=wx.ComboBox(self,size=(50,-1), choices=time_options, style=wx.CB_READONLY)

        #self.header=wx.StaticText(self,-1,"Guider Performance")
        #Add current offset and timing information only.
        self.dpi = 100
        self.fig = Figure((7.0,4.5), dpi=self.dpi)
        self.canvas = FigCanvas(self,-1, self.fig)

        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title('Guider Performance', size='small')
        self.ax1.set_ylabel('Offset (arcmin)', size='x-small')

        self.ax1.plot([1,2,3], label="Seeing")
        self.ax1.plot([3,2,1], label="Line 2")
        self.ax1.legend(bbox_to_anchor=(0,1.02,1.,.102),loc=3,ncol=2,mode="expand",borderaxespad=0.)

        for xlabel_i in self.ax1.get_xticklabels():
            xlabel_i.set_fontsize(8)
        for ylabel_i in self.ax1.get_yticklabels():
            ylabel_i.set_fontsize(8)

        self.ax2= self.fig.add_subplot(212)
        self.ax2.set_xlabel('Time (PT)', size='x-small')
        self.ax2.set_ylabel('fwhm (arcsec)', size='x-small')
        for xlabel_i in self.ax2.get_xticklabels():
            xlabel_i.set_fontsize(8)
        for ylabel_i in self.ax2.get_yticklabels():
            ylabel_i.set_fontsize(8)

        self.toolbar = NavigationToolbar(self.canvas)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        #self.hbox=wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox.Add(self.guiderTZLabel,0)
        #self.hbox.Add(self.guiderTZCombo,0)
        #self.vbox.Add(self.hbox,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.canvas, 0, wx.ALIGN_CENTER)
        self.vbox.Add(self.toolbar,0, wx.ALIGN_CENTER)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

class GuiderControl(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)

        # add visual representation of stepper and periscope position
        # show computation for decovultion of position
        # image display w/ vector offset arrows
        # need to define guider directory and filename structure

        self.Buffer = None
        self.center=[200,275]
        self.dc = None
        self.rotAng=0
        
        self.fig_r = Figure((4,4))
        self.canvas_r = FigCanvas(self,-1, self.fig_r)
        self.ax_r = self.fig_r.add_subplot(111)
        self.ax_r.set_axis_off()
        #self.cir = matplotlib.patches.Circle( (156,160), radius=125, fill=False, color='steelblue',linewidth=2.5)
        #self.line= matplotlib.patches.Rectangle( (156,160), height=-125, width=2, fill=True, color='k')
        
        #self.ax_r.add_patch(self.cir)
        #self.ax_r.add_patch(self.line)
        
        self.fig_r.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        
        
        self.fig_l = Figure((4,4))
        self.canvas_l = FigCanvas(self,-1, self.fig_l)
        self.ax_l = self.fig_l.add_subplot(111)
        self.ax_l.set_axis_off()
        self.cir = matplotlib.patches.Circle( (150,150), radius=125, fill=False, color='steelblue',linewidth=2.5)
	self.cir1 = matplotlib.patches.Circle( (150,150), radius=126, fill=False, color='k',linewidth=1.0)
        self.line= matplotlib.patches.Rectangle( (150,150), height=125, width=2, fill=True, color='k')
        
        
        self.ax_l.add_patch(self.cir)
	self.ax_l.add_patch(self.cir1)
        self.ax_l.add_patch(self.line)
        
        self.fig_l.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        
        self.finderLabel=wx.StaticText(self, size=(100,-1))
        self.finderLabel.SetLabel('Radius (arcmin): ')
        self.finderText=wx.TextCtrl(self,size=(100,-1))
        self.finderText.SetValue('18.0')
        
        self.finderButton=wx.Button(self,-1,"Load Finder Chart",size=(125,-1))
        #self.finderButton.Bind(wx.EVT_BUTTON,self.load_finder_chart)
        
        self.findStarsButton = wx.Button(self, -1, "Auto Find Guide Stars",size=(150,-1))
        self.startGuidingButton = wx.Button(self, -1, "Start Guiding",size=(150,-1))

        self.guiderTimeLabel=wx.StaticText(self, size=(100,-1))
        self.guiderTimeLabel.SetLabel('Exposure: ')
        self.guiderTimeText=wx.TextCtrl(self,size=(100,-1))
        self.guiderTimeText.SetValue('10.0')

        self.guiderExposureButton = wx.Button(self, -1, 'Guider Exposure',size=(125,-1))

        self.guiderRotLabel=wx.StaticText(self, size=(100,-1))
        self.guiderRotLabel.SetLabel('Rot. Angle: ')
        self.guiderRotText=wx.TextCtrl(self,size=(100,-1))
        self.guiderRotText.SetValue('0.0')
        self.guiderRotButton = wx.Button(self, -1, 'Set Guider Rotation',size=(125,-1))
        #self.Bind(wx.EVT_BUTTON, self.on_Rot, self.guiderRotButton)
        
        self.jogNButton = wx.Button(self, -1, 'N',size=(75,-1))
        self.jogSButton = wx.Button(self, -1, 'S',size=(75,-1))
        self.jogWButton = wx.Button(self, -1, 'W',size=(75,-1))
        self.jogEButton = wx.Button(self, -1, 'E',size=(75,-1))
        
        self.focusIncPlusButton = wx.Button(self, -1, 'Increment Positive')
        self.focusIncNegButton = wx.Button(self, -1, 'Increment Negative')
        self.focusAbsText = wx.TextCtrl(self,size=(75,-1))
        self.focusAbsText.SetValue('1500')
        self.focusAbsMove = wx.Button(self,-1,'Move Relative')

        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.hbox=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        self.gbox=wx.GridSizer(rows=3, cols=3, hgap=0, vgap=5)
        self.gbox3=wx.GridSizer(rows=2, cols=2, hgap=5, vgap=5)
        self.ghbox=wx.BoxSizer(wx.HORIZONTAL)
        
        self.clabel=wx.StaticBox(self,label="Guider Controls")
        self.vboxc= wx.StaticBoxSizer(self.clabel, wx.VERTICAL)
        
        self.flabel=wx.StaticBox(self,label="Focus Guider")
        self.vboxf= wx.StaticBoxSizer(self.flabel, wx.VERTICAL)
        
        self.jlabel=wx.StaticBox(self,label="Jog Guider Field")
        self.vboxj= wx.StaticBoxSizer(self.jlabel, wx.VERTICAL)
        
        self.gbox3.Add(self.focusIncPlusButton, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusAbsText, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusIncNegButton, 0, wx.ALIGN_LEFT)
        self.gbox3.Add(self.focusAbsMove, 0, wx.ALIGN_LEFT)
        
        self.vboxf.Add(self.gbox3,0,wx.ALIGN_CENTER)
        
        self.hbox3.Add(self.jogWButton,0,wx.ALIGN_LEFT)
        self.hbox3.AddSpacer(5)
        self.hbox3.Add(self.jogEButton,0,wx.ALIGN_LEFT)
        
        self.vboxj.Add(self.jogNButton,0,wx.ALIGN_CENTER)
        self.vboxj.AddSpacer(5)
        self.vboxj.Add(self.hbox3,0,wx.ALIGN_CENTER)
        self.vboxj.AddSpacer(5)
        self.vboxj.Add(self.jogSButton,0,wx.ALIGN_CENTER)
        
        self.gbox.Add(self.guiderTimeLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.guiderTimeText, 0, wx.ALIGN_LEFT)
        self.gbox.Add(self.guiderExposureButton,0,wx.ALIGN_LEFT)
        self.gbox.Add(self.guiderRotLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.guiderRotText, 0, wx.ALIGN_LEFT)
        self.gbox.Add(self.guiderRotButton,0,wx.ALIGN_LEFT)
        self.gbox.Add(self.finderLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.finderText, 0, wx.ALIGN_LEFT)
        self.gbox.Add(self.finderButton,0,wx.ALIGN_LEFT)
        
        #self.hbox.AddSpacer(50)
        self.hbox.Add(self.findStarsButton, 0, wx.ALIGN_LEFT)
        self.hbox.AddSpacer(15)
        self.hbox.Add(self.startGuidingButton, 0, wx.ALIGN_RIGHT)
        
        self.vboxc.Add(self.gbox,0,wx.ALIGN_CENTER)
        self.vboxc.AddSpacer(10)
        self.vboxc.Add(self.hbox,0,wx.ALIGN_CENTER)
        
        self.ghbox.AddSpacer(20)
        self.ghbox.Add(self.vboxc,0,wx.ALIGN_LEFT)
        self.ghbox.AddSpacer(20)
        self.ghbox.Add(self.vboxj,0,wx.ALIGN_LEFT)
        self.ghbox.AddSpacer(20)
        self.ghbox.Add(self.vboxf,0,wx.ALIGN_LEFT)
        
        self.hbox2.Add(self.canvas_l,0,wx.ALIGN_RIGHT)
        self.hbox2.AddSpacer(90)
        self.hbox2.Add(self.canvas_r,0,wx.ALIGN_RIGHT)

        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.ghbox,0,wx.ALIGN_LEFT)


        self.SetSizer(self.vbox)

class GuiderFocus(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)
        None


#Ernest        
class Spectrograph(wx.Panel):
    def __init__(self,parent,debug,night):
        wx.Panel.__init__(self,parent)
        None



class Initialization(wx.Panel):
    def __init__(self,parent, debug, night):
        wx.Panel.__init__(self,parent)

        # add line to separate the different sections

        self.atZenithButton = wx.Button(self, -1, "Load Zenith Coordinates")
        self.atZenithButton.Disable()
        

        #Set current telescope position
        self.targetNameLabel=wx.StaticText(self, size=(75,-1))
        self.targetNameLabel.SetLabel('Name: ')
        self.targetNameText=wx.TextCtrl(self,size=(100,-1))

        self.targetRaLabel=wx.StaticText(self, size=(75,-1))
        self.targetRaLabel.SetLabel('RA: ')
        self.targetRaText=wx.TextCtrl(self,size=(100,-1))

        self.targetDecLabel=wx.StaticText(self, size=(75,-1))
        self.targetDecLabel.SetLabel('DEC: ')
        self.targetDecText=wx.TextCtrl(self,size=(100,-1))

        self.targetEpochLabel=wx.StaticText(self, size=(75,-1))
        self.targetEpochLabel.SetLabel('EPOCH: ')
        self.targetEpochText=wx.TextCtrl(self,size=(100,-1))
        self.targetEpochText.SetLabel('2000')

        #Precessed Coordinates
        self.precessNameText=wx.StaticText(self,size=(100,-1))
        self.precessNameText.SetLabel('None')
        self.precessRaText=wx.StaticText(self,size=(100,-1))
        self.precessRaText.SetLabel('None')
        self.precessDecText=wx.StaticText(self,size=(100,-1))
        self.precessDecText.SetLabel('None')
        self.precessEpochText=wx.StaticText(self,size=(100,-1))
        self.precessEpochText.SetLabel('None')

        # this should autofill from tcc.conf
        self.trackingRateRALabel=wx.StaticText(self, size=(100,-1))
        self.trackingRateRALabel.SetLabel('RA Tracking Rate: ')
        self.trackingRateRAText=wx.TextCtrl(self,size=(100,-1))
        self.rateRAButton = wx.Button(self, -1, "Set RA Tracking Rate")

        self.trackingRateDECLabel=wx.StaticText(self, size=(100,-1))
        self.trackingRateDECLabel.SetLabel('DEC Tracking Rate: ')
        self.trackingRateDECText=wx.TextCtrl(self,size=(100,-1))
        self.rateDECButton = wx.Button(self, -1, "Set DEC Tracking Rate")

        #allows for change in maximum guider offsets, should be set by tcc.conf as an initial value
        self.maxdRALabel=wx.StaticText(self, size=(75,-1))
        self.maxdRALabel.SetLabel('Max dRA: ')
        self.maxdRAText=wx.TextCtrl(self,size=(100,-1))
        self.dRAButton = wx.Button(self, -1, "Set Maximum dRA")

        self.maxdDECLabel=wx.StaticText(self, size=(75,-1))
        self.maxdDECLabel.SetLabel('Max dDEC: ')
        self.maxdDECText=wx.TextCtrl(self,size=(100,-1))
        self.dDECButton = wx.Button(self, -1, "Set Maximum dDEC")


        self.syncButton = wx.Button(self, -1, "Set Telescope Position")
        self.initButton = wx.Button(self, -1, "Initialize Telescope Systems")
        self.parkButton= wx.Button(self, -1, "Park Telescope")
        self.coverposButton=wx.Button(self,-1,"Slew to Cover Position")
        self.onTargetButton=wx.Button(self,-1,"On Target")
        
        self.parkButton.Disable()
        self.coverposButton.Disable()
        self.onTargetButton.Disable()

        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.gbox=wx.GridSizer(rows=4, cols=3, hgap=5, vgap=5)
        self.gbox2=wx.GridSizer(rows=5, cols=3, hgap=5, vgap=5)

        self.gbox.Add(self.targetNameLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetNameText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.precessNameText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetRaLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetRaText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.precessRaText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetDecLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetDecText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.precessDecText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetEpochLabel, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.targetEpochText, 0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.precessEpochText, 0, wx.ALIGN_RIGHT)

        self.gbox2.Add(self.trackingRateRALabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.trackingRateRAText, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.rateRAButton, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.trackingRateDECLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.trackingRateDECText, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.rateDECButton,0,wx.ALIGN_LEFT)
        self.gbox2.Add(self.maxdRALabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.maxdRAText, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.dRAButton, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.maxdDECLabel, 0, wx.ALIGN_RIGHT)
        self.gbox2.Add(self.maxdDECText, 0, wx.ALIGN_LEFT)
        self.gbox2.Add(self.dDECButton, 0, wx.ALIGN_LEFT)

        self.hbox1.Add(self.atZenithButton,0,wx.ALIGN_CENTER)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.initButton,0,wx.ALIGN_CENTER)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.syncButton, 0, wx.ALIGN_RIGHT)
        
        self.vbox.AddSpacer(10)
        self.hbox2.Add(self.coverposButton,0,wx.ALIGN_CENTER)
        self.hbox2.AddSpacer(10)
        self.hbox2.Add(self.onTargetButton,0,wx.ALIGN_CENTER)
        self.hbox2.AddSpacer(10)
        self.hbox2.Add(self.parkButton,0,wx.ALIGN_CENTER)
		
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox1,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.gbox,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.gbox2,0,wx.ALIGN_CENTER)

        self.SetSizer(self.vbox)


class NightLog(wx.ScrolledWindow):
    def __init__(self,parent, debug, night):
        self.parent = parent
        wx.ScrolledWindow.__init__(self, parent, -1, style=wx.TAB_TRAVERSAL)
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        self.SetScrollRate(fontsz.x, fontsz.y)
        self.EnableScrolling(True,True)

        self.nltitle=wx.StaticText(self,-1, "Manastash Ridge Observatory Night Log")
        font = wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.nltitle.SetFont(font)
        self.labelastr=wx.StaticText(self, -1, "Astronomer(s)")
        self.labelobs=wx.StaticText(self, -1, "Observer(s)")
        self.labelinst=wx.StaticText(self, -1, "Instrument")
        self.labelstart=wx.StaticText(self, -1, "Start Time")
        self.labelend=wx.StaticText(self, -1, "End Time")
        self.usastr=wx.TextCtrl(self,size=(50,-1))
        self.usobs=wx.TextCtrl(self, size=(50,-1))
        self.usinst=wx.TextCtrl(self,size=(50,-1))
        self.usstart=wx.TextCtrl(self,size=(50,-1))
        self.usend=wx.TextCtrl(self,size=(50,-1))

        #First box components for observer and astronomer identification

        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.labelastr,0,wx.ALIGN_RIGHT)
        self.hbox1.AddSpacer(5)
        self.hbox1.Add(self.usastr,1,wx.ALIGN_LEFT|wx.EXPAND)
        self.hbox1.AddSpacer(10)

        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.labelobs,0,wx.ALIGN_RIGHT)
        self.hbox2.AddSpacer(21)
        self.hbox2.Add(self.usobs,1,wx.ALIGN_LEFT|wx.EXPAND)
        self.hbox2.AddSpacer(10)

        self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.labelinst,0,wx.ALIGN_RIGHT)
        self.hbox3.AddSpacer(23)
        self.hbox3.Add(self.usinst,1,wx.ALIGN_LEFT|wx.EXPAND)
        self.hbox3.AddSpacer(10)

        self.hbox4=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox4.Add(self.labelstart,0,wx.ALIGN_RIGHT)
        self.hbox4.AddSpacer(27)
        self.hbox4.Add(self.usstart,1,wx.ALIGN_LEFT|wx.EXPAND)
        self.hbox4.AddSpacer(10)

        self.hbox5=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox5.Add(self.labelend,0,wx.ALIGN_RIGHT)
        self.hbox5.AddSpacer(31)
        self.hbox5.Add(self.usend,1,wx.ALIGN_LEFT|wx.EXPAND)
        self.hbox5.AddSpacer(10)


        #Activity Log
        self.actheader=wx.StaticText(self,label="ACTIVITY LOG")
        self.actlog=wx.TextCtrl(self, size=(600,100),style= wx.TE_MULTILINE)

        #Failure Log
        self.failheader=wx.StaticText(self,label="FAILURE LOG")
        #self.failinfo=wx.StaticText(self,label="Time                                                                          Description                                                                                    ")
        self.faillog=wx.TextCtrl(self, size=(600,50),style= wx.TE_MULTILINE)

        #Focus Log
        self.focheader=wx.StaticText(self,label="FOCUS LOG")
        #self.focinfo=wx.StaticText(self,label='Time               Instrument               Focus                 Az      El      Temp    Strc    Prim     Sec     Air     filt     FWHM')
        #self.foclog=wx.TextCtrl(self, size=(600,100),style= wx.TE_MULTILINE)
        self.foclog=wx.ListCtrl(self,size=(600,100), style=wx.LC_REPORT| wx.VSCROLL | wx.LC_VRULES)
        self.foclog.InsertColumn(0,'Time',width=50)
        self.foclog.InsertColumn(1,'Instrument',width=75)
        self.foclog.InsertColumn(2,'Focus',width=75)
        self.foclog.InsertColumn(3,'Az',width=50)
        self.foclog.InsertColumn(5,'El',width=50)
        self.foclog.InsertColumn(6,'Temp',width=50)
        self.foclog.InsertColumn(7,'Strc',width=50)
        self.foclog.InsertColumn(8,'Prim',width=50)
        self.foclog.InsertColumn(9,'Sec',width=50)
        self.foclog.InsertColumn(10,'Air',width=50)
        self.foclog.InsertColumn(11,'filt',width=50)
        self.foclog.InsertColumn(12,'FWHM',width=50)

        self.focusButton=wx.Button(self,label="Number of Focus Lines")
        self.focusNum=wx.TextCtrl(self,size=(30,-1))
        self.focusNum.AppendText('1')

        self.hbox6=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox6.Add(self.focusButton,0,wx.ALIGN_CENTER)
        self.hbox6.AddSpacer(5)
        self.hbox6.Add(self.focusNum,0,wx.ALIGN_CENTER)

        #Save as and Submit buttons
        self.saveButton=wx.Button(self,label="Save As")

        self.submitButton=wx.Button(self,label="Submit")

        self.hbox7=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox7.Add(self.saveButton,0,wx.ALIGN_CENTER)
        self.hbox7.AddSpacer(25)
        self.hbox7.Add(self.submitButton,0,wx.ALIGN_CENTER)


        #Vertical box organization
        self.vbox=wx.BoxSizer(wx.VERTICAL)

        self.vbox.Add(self.nltitle, 0, wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox1,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.hbox3,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.hbox4,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.hbox5,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.actheader,0,wx.ALIGN_CENTER)
        self.vbox.Add(self.actlog,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.failheader, 0, wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.faillog,0, wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.focheader,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.foclog,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(5)
        self.vbox.Add(self.hbox6,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(25)
        self.vbox.Add(self.hbox7,0,wx.ALIGN_CENTER)


        self.SetSizer(self.vbox)
        self.Show()

class TCC(wx.Frame):
    title='Manastash Ridge Observatory Telescope Control Computer'
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title,size=(900,600))
        
        #Tracking on boot is false
	self.guider_rot=False
        self.calculate=True
        self.precession=True
        self.tracking=False
        self.slewing=False
        self.night=True
        self.initState=False
        self.export_active=False
        self.dict={'lat':None, 'lon':None,'elevation':None, 'lastRA':None, 'lastDEC':None,'lastGuiderRot':None,'lastFocusPos':None,'maxdRA':None,'maxdDEC':None, 'trackingRate':None }
        self.list_count=0
        self.active_threads={}
        self.thread_to_close=-1
        #Stores current time zone for whole GUI
        self.current_timezone="PST"
        self.mro=ephem.Observer()
        self.mrolat=46.9528*u.deg
        
        self.MRO = Observer(longitude = -120.7278 *u.deg,
                latitude = 46.9528*u.deg,
                elevation = 1198*u.m,
                name = "Manastash Ridge Observatory"
                )
        debug=True
        

        self.dir=os.getcwd()
        
        #setup notebook
        p=wx.Panel(self)
        nb=wx.Notebook(p)
        controlPage=Control(nb, debug, self.night)
        targetPage=Target(nb, debug, self.night)
        #scienceFocusPage=ScienceFocus(nb, debug, self.night)
        guiderPage=Guider(nb, debug, self.night)
        guiderControlPage=GuiderControl(nb,debug,self.night)
        spectroPage=Spectrograph(nb,debug,self.night)
        #guiderFocusPage=GuiderFocus(nb,debug,self.night)
        initPage=Initialization(nb, debug, self.night)
        logPage=NightLog(nb, debug, self.night)

        nb.AddPage(controlPage,"Telescope Control")
        self.control=nb.GetPage(0)
        '''
        nb.AddPage(scienceFocusPage, "Science Focus")
        self.scienceFocus=nb.GetPage(1)
        '''
        nb.AddPage(targetPage,"Target List")
        self.target=nb.GetPage(1)
        
        nb.AddPage(guiderControlPage,"Guider Control")
        self.guiderControl=nb.GetPage(2)
        '''
        nb.AddPage(guiderFocusPage, "Guider Focus")
        self.guiderFocus=nb.GetPage(4)
        '''
        nb.AddPage(guiderPage,"Guider Performance Monitor")
        self.guider=nb.GetPage(3)
        
        nb.AddPage(spectroPage,"Spectrograph")
        self.guider=nb.GetPage(4)

        nb.AddPage(initPage,"Initialization Parameters")
        self.init=nb.GetPage(5)

        nb.AddPage(logPage,"Night Log")
        self.nl=nb.GetPage(6)
        
        #Control Tab Bindings
        self.Bind(wx.EVT_BUTTON, self.startSlew, self.control.slewButton)
        self.Bind(wx.EVT_BUTTON,self.toggletracksend,self.control.trackButton)
        self.Bind(wx.EVT_BUTTON,self.haltmotion,self.control.stopButton)
        self.Bind(wx.EVT_BUTTON,self.Noffset,self.control.jogNButton)
        self.Bind(wx.EVT_BUTTON,self.Soffset,self.control.jogSButton)
        self.Bind(wx.EVT_BUTTON,self.Eoffset,self.control.jogEButton)
        self.Bind(wx.EVT_BUTTON,self.Woffset,self.control.jogWButton)
        self.Bind(wx.EVT_BUTTON,self.focusIncPlus,self.control.focusIncPlusButton)
        self.Bind(wx.EVT_BUTTON,self.focusIncNeg,self.control.focusIncNegButton)
        self.Bind(wx.EVT_BUTTON,self.setfocus,self.control.focusAbsMove)
        
        #Target Tab Bindings
        self.Bind(wx.EVT_BUTTON, self.set_target, self.target.selectButton)
        self.Bind(wx.EVT_BUTTON, self.addToList, self.target.enterButton)
        self.Bind(wx.EVT_BUTTON, self.readToList, self.target.listButton)
        self.Bind(wx.EVT_BUTTON, self.removeFromList,self.target.removeButton)
        self.Bind(wx.EVT_BUTTON, self.ExportOpen,self.target.exportButton)
        self.Bind(wx.EVT_BUTTON, self.target_plot, self.target.plot_button)
        self.Bind(wx.EVT_BUTTON, self.airmass_plot, self.target.airmass_button)
        
        #Guider Control Tab Bindings
        self.Bind(wx.EVT_BUTTON, self.LoadFinder, self.guiderControl.finderButton)
        self.Bind(wx.EVT_BUTTON,self.on_Rot,self.guiderControl.guiderRotButton)
        
        # Init Tab Bindings
        self.Bind(wx.EVT_BUTTON,self.setTelescopeZenith ,self.init.atZenithButton)
        self.Bind(wx.EVT_BUTTON, self.setTelescopePosition, self.init.syncButton)
        self.Bind(wx.EVT_BUTTON, self.onInit, self.init.initButton)
        self.Bind(wx.EVT_BUTTON, self.setRATrackingRate,self.init.rateRAButton)
        self.Bind(wx.EVT_BUTTON, self.setDECTrackingRate,self.init.rateDECButton)
        self.Bind(wx.EVT_BUTTON, self.coverpos, self.init.coverposButton)
        self.Bind(wx.EVT_BUTTON, self.parkscope, self.init.parkButton)
        self.Bind(wx.EVT_BUTTON, self.pointing, self.init.onTargetButton)
        
        self.createMenu()

        self.sb = self.CreateStatusBar(5)

        sizer=wx.BoxSizer()
        sizer.Add(nb,1, wx.EXPAND|wx.ALL)
        p.SetSizer(sizer)
        p.Layout()

        self.readConfig()
        """Target testing parameters """
        self.target.nameText.SetValue('M31')
        self.target.raText.SetValue('00h42m44.330s')
        self.target.decText.SetValue('+41d16m07.50s')
        self.target.epochText.SetValue('J2000')
        self.target.magText.SetValue('3.43')

        #png image appears to cause an RGB conversion failure.  Either use jpg or convert with PIL
        img_default=os.path.join(self.dir,'gimg','gcam_56901_859.jpg')
        img=mpimg.imread(img_default)
        #img = wx.Image(img_default, wx.BITMAP_TYPE_ANY)
        #self.guiderControl.imageCtrl.SetBitmap(wx.BitmapFromImage(img))
        self.guiderControl.ax_r.imshow(img, picker=False)
        self.guiderControl.canvas_l.mpl_connect('pick_event', self.on_pick)

    def createMenu(self):
        '''
        Generates the menu bar for the WX application.
        
         Args: 
                self: points function towards WX application
         Returns:
                None
        '''
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
    
        tool_file = wx.Menu()
        m_night = tool_file.Append(-1, 'Night\tCtrl-N','Night Mode')
        
        tz_choice = wx.Menu()
        tz_choice.Append(1110, "Pacific", "Set Time Zone", kind=wx.ITEM_RADIO)
        tz_choice.Append(1111, "Mountain", "Set Time Zone", kind=wx.ITEM_RADIO)
        tz_choice.Check(id=1110, check=True)
        tool_file.AppendMenu(1112,'Time Zone',tz_choice)
        
        precess = wx.Menu()
        precess.Append(1120, "On", "Set Precession", kind=wx.ITEM_RADIO)
        precess.Append(1121, "Off", "Set Precession", kind=wx.ITEM_RADIO)
        precess.Check(id=1120, check=True)
        tool_file.AppendMenu(1122,'Precession',precess)
        
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        self.Bind(wx.EVT_MENU, self.on_night, m_night)
        self.Bind(wx.EVT_MENU, self.on_Pacific, id=1110)
        self.Bind(wx.EVT_MENU, self.on_Mountain, id=1111)
        self.Bind(wx.EVT_MENU, self.pre_on, id=1120)
        self.Bind(wx.EVT_MENU, self.pre_off, id=1121)

        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(tool_file, "&Tools")

        self.SetMenuBar(self.menubar)

   
    def on_exit(self, event):
        """
        Exit in a graceful way so that the telescope information can be saved and used at a later time.
        
         Args:
                self: points function towards WX application
                event: handler to allow function to be tethered to a wx widget
                
         Returns:
                None
         
        """
        dlg = wx.MessageDialog(self,
                               "Exit the TCC?",
                               "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            if(self.protocol is not None):
                #d= self.protocol.sendCommand("shutdown")
                #d.addCallback(self.quit)
                self.quit()
    def quit(self):
        self.Destroy()
        os.killpg(os.getpgid(pipe.pid),signal.SIGTERM)
        reactor.callFromThread(reactor.stop)
            #add save coordinates
            #self.Destroy()

    def on_night(self,event):
        """
        Event handle for the night mode option in the menu. Aesthetic change to make the GUI background color redder.
        
         Args:
                self: points function towards WX application
                event: handler to allow function to be tethered to a wx widget
         Returns:
                None
        
        """
        if self.night:
            self.SetBackgroundColour((176,23,23))
            self.night=False
        else:
            self.night=True
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
            self.SetBackgroundColour(color)
        return
    def on_Pacific(self,event):
        """
        Event handle for the pacific time zone option. Changes time to the current pacific time representation.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget.
                
         Returns:
                None
        """
        self.current_timezone="PST"
        self.sb.SetStatusText('Timezone: PST',4)
        return
    def on_Mountain(self,event):
        """
        Event handle for the Mountain time zone option. Changes time to the current Mountain time representation.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget.
                
         Returns:
                None
        """
        self.current_timezone="MST"
        self.sb.SetStatusText('Timezone: MST',4)
        return
    def pre_on(self,event):
        """
        Turns precession on for the entire GUI. Note that this is on by default when the GUI is initialized.
            Args:
                    self: points function towards WX application.
                    event: handler to allow function to be tethered to a wx widget.
                
            Returns:
                    self.precession: Sets self.precession = True
        """
        self.precession=True
        self.log("Precession enabled")
        return
        
    def pre_off(self,event):
        """
        Turns precession off for the entire GUI.
            Args:
                    self: points function towards WX application.
                    event: handler to allow function to be tethered to a wx widget.
                
            Returns:
                    self.precession: Sets self.precession = True
        """
        self.precession=False
        self.log("Precession disabled")
        return
        
    def log(self, input):
        """
        Take input from the any system and log both on screen and to a file.
        Necessary to define command structure for easy expansion.
        
         Args:
                self: points function towards WX application.
                input (string): The desired message to be logged.
                
         Returns:
                None
        
        """
        today=time.strftime('%Y%m%d.log')
        current_time_log=time.strftime('%Y%m%dT%H%M%S')
        current_time=time.strftime('%Y%m%d  %H:%M:%S')
        f_out=open(self.dir+today,'a')
        f_out.write(current_time_log+','+str(input)+'\n')
        f_out.close()
        self.control.logBox.AppendText(str(current_time)+':  '+str(input)+'\n')
        return


    def readConfig(self):
        """
        Get the basic telescope information if it is available.  It would be nice if the dictionary was defined external to the program.
        
         Args:
                self: points function towards WX application.
                
         Returns:
                None
        """
        self.log('==== Initializing Parameters ====')
        self.log('Reading in config file ....')
        f_in=open('tcc.conf','r')
        for line in f_in:
            l=line.split()
            self.dict[l[0]]=l[1]
        f_in.close()
        for d in self.dict:
            self.log([d,self.dict[d]])
        t = self.timeCalc()
        self.log('Configuration parameters read')
        self.sb.SetStatusText('Tracking: False',0)
        self.sb.SetStatusText('Slewing: False',1)
        self.sb.SetStatusText('Guiding: False',2)
        self.sb.SetStatusText('Init Telescope to Enable Slew / Track',3)
        self.sb.SetStatusText('Timezone: UTC',4)
        self.init.targetDecText.SetValue(str(self.dict['lat']))
        self.init.targetEpochText.SetValue(str( '%.3f') % t['epoch'])
        self.init.trackingRateRAText.SetValue(str(self.dict['trackingRate']))
        self.init.maxdRAText.SetValue(str(self.dict['maxdRA']))
        self.init.maxdDECText.SetValue(str(self.dict['maxdDEC']))
        return
        
    def Noffset(self,event):
        """
        Jog Command; apply a coordinate offset in the North direction.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "N" button in the telescope control tab.
                
         Returns:
                None
        """
        if self.tracking==True:
        	self.protocol.sendCommand("offset N "+str(self.control.jogIncrement.GetValue())+"True "+str(self.control.currentRATRPos.GetLabel()))
	if self.tracking==False:
		self.protocol.sendCommand("offset N "+str(self.control.jogIncrement.GetValue()))
        return
    		
    def Woffset(self,event):
        """
        Jog Command; apply a coordinate offset in the West direction.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "W" button in the telescope control tab.
                
         Returns:
                None
        """
        if self.tracking==True:
        	self.protocol.sendCommand("offset W "+str(self.control.jogIncrement.GetValue())+"True "+str(self.control.currentRATRPos.GetLabel()))
	if self.tracking==False:
		self.protocol.sendCommand("offset W "+str(self.control.jogIncrement.GetValue()))
        return
    def Eoffset(self,event):
        """
        Jog Command; apply a coordinate offset in the East direction.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget.Tethered to the "E" button in the telescope control tab.
                
         Returns:
                None
        """
        if self.tracking==True:
        	self.protocol.sendCommand("offset E "+str(self.control.jogIncrement.GetValue())+"True "+str(self.control.currentRATRPos.GetLabel()))
	if self.tracking==False:
		self.protocol.sendCommand("offset E "+str(self.control.jogIncrement.GetValue()))
        return
    def Soffset(self,event):
        """
        Jog Command; apply a coordinate offset in the South direction.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget.Tethered to the "S" button in the telescope control tab.
                
         Returns:
                None
        """
        if self.tracking==True:
        	self.protocol.sendCommand("offset S "+str(self.control.jogIncrement.GetValue())+"True "+str(self.control.currentRATRPos.GetLabel()))
	if self.tracking==False:
		self.protocol.sendCommand("offset S "+str(self.control.jogIncrement.GetValue()))
        return
        
    def focusIncPlus(self,event):
        """
        Focus Increment; apply a positive focus increment of 1500.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget.Tethered to the "Increment Positive" button in the telescope control tab.
                
         Returns:
                None
        """
        val=self.control.focusAbsText.GetValue()
        val=float(val)+1500.0
        val=int(val)
        self.control.focusAbsText.SetValue(str(val))
        return
    def focusIncNeg(self,event):
        """
        Focus Increment; apply a negative focus increment of 1500.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Increment Negative" button in the telescope control tab.
                
         Returns:
                None
        """
        val=self.control.focusAbsText.GetValue()
        val=float(val)-1500.0
        val=int(val)
        self.control.focusAbsText.SetValue(str(val))
        return
        
    def setfocus(self,event):
        """
        Focus Command; set current TCC focus to the value entered in the WX textctrl box.
        Overwrites current TCC focus value and sends value to drivers.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Move Absolute" button in the telescope control tab.
                
         Returns:
                None
        """
        inc=self.control.focusAbsText.GetValue()
        curFocus=self.control.currentFocusPos.GetLabel()
        if curFocus=='Unknown':
        	curFocus=0.0
        newfocus=float(curFocus)+float(inc)
        self.control.currentFocusPos.SetLabel(str(newfocus))
        self.control.currentFocusPos.SetForegroundColour('black')
        self.protocol.sendCommand(str("focus")+' '+str(inc))
        return
        
    def haltmotion(self,event):
        '''
        Halt Telescope motion, emergency button, use stop slew during slewing if possible.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "HALT MOTION" button in the telescope control tab.
                
         Returns:
                None
         
        '''
        self.protocol.sendCommand("halt")
        return
        
    
    def toggletracksend(self,evt):
        '''
        Passes a command to the telescope to toggle tracking.
        
         Args:
                self: points function towards WX application.
                evt: handler to allow function to be tethered to a wx widget. Tethered to the "Start Tracking" button in the telescope control tab.
                
         Returns:
                None
        '''
        RATR=self.control.currentRATRPos.GetLabel()
        DECTR=self.control.currentDECTRPos.GetLabel()
        print RATR, DECTR
        if str(RATR)=='Unknown':
        	dlg = wx.MessageDialog(self,"Please input a valid RA tracking rate. Range is between -10.0 and 25.0. Use 1.0 if unsure.", "Error", wx.OK|wx.ICON_ERROR)
        	dlg.ShowModal()
        	dlg.Destroy()
        	return
        if self.tracking==False:
            self.control.trackButton.SetLabel('Stop Tracking')
            self.sb.SetStatusText('Tracking: True',0)
            self.protocol.sendCommand("track on "+str(RATR)+' '+str(DECTR))
        if self.tracking==True:
            self.control.trackButton.SetLabel('Start Tracking')
            self.sb.SetStatusText('Tracking: False',0)
            self.protocol.sendCommand("track off")
        self.tracking= not self.tracking    
        return
    
       
    def inputcoordSorter(self,ra,dec,epoch):
        '''
        Take in any valid RA/DEC format and read it into an Astropy SkyCoord object. Format of RA must be consistent with format of DEC. Supports galactic coordinates as well, to
        input galactic coordinates, set the ra argument to be l=00h00m00s and the dec argument to be b=+00h00m00s. These will be put into a galactic skycoord frame which will then
        be transformed into an fk5 skycoord object.
        
        Args:
                self: points function towards WX application.
                ra (string): Right Ascension of object. Valid forms are decimal degrees, hh:mm:ss , hh mm ss ,XXhXXmXXs and l=XXhXXmXXs
                dec (string): Declination of object. Valid forms are decimal degrees, hh:mm:ss, hh mm ss, XXdXXmXXs and b=XXdXXmXXs
                epoch (string): The epoch that the RA/DEC are specific to (usually J2000).
                
         Returns:
                None
        '''
        
        self.validity=False
        self.galactic_coords=False
        
        #first check to see if galactic coordinates
        if str(ra)[0:2]== 'l=' or str(ra)[0:2] == 'L=':
            self.galactic_coords=True
            self.galcoordinates = SkyCoord("galactic", l=str(ra)[2:], b=str(dec)[2:])
            self.coordinates=self.galcoordinates.transform_to('fk5')
            self.validity=True
            return self.coordinates
                
        deg_input=True
        
        try:
            val=float(ra)
        except ValueError:
            deg_input=False
        
        if deg_input==True:
            self.coordinates=SkyCoord(ra=float(ra)*u.degree,dec=float(dec)*u.degree,frame='icrs',equinox=str(epoch))
            self.validity=True
            return self.coordinates
        elif str(ra)[2]== 'h' and str(ra)[5]== 'm':
            self.coordinates=SkyCoord(ra,dec,frame='icrs',equinox=str(epoch))
            self.validity=True
            return self.coordinates
        elif str(ra)[2]== ' ' and str(ra)[5]== ' ':
            self.coordinates=SkyCoord(str(ra)+' '+str(dec), unit=(u.hourangle,u.deg),equinox=str(epoch))
            self.validity=True
            return self.coordinates
        elif str(ra)[2]== ':' and str(ra)[5]== ':':
            self.coordinates=SkyCoord(str(ra)+' '+str(dec), unit=(u.hourangle,u.deg),equinox=str(epoch))
            self.validity=True
            return self.coordinates
        elif self.validity==False:
            dlg = wx.MessageDialog(self,
                           "Not a valid RA or DEC format. Please input an RA and DEC in any of the following forms: decimal degrees, 00h00m00s, 00:00:00, 00 00 00. If attempting to input galactic coordinates\n please enter in form l=00h00m00s and b=+00d00m00s in RA and DEC fields.",
                           "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
            return
        '''
        else:
            self.validity=False
            dlg = wx.MessageDialog(self,
                               "Not a transformable input epoch. Coordinate types supported are J2000 and J1950. Leave epoch blank to assume J2000.",
                               "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
            return
        '''
    def coordprecess(self,coords,epoch_now,epoch):
        '''
        coordprecess() generates an astropy skycoord object with RA/DEC precessed to the current epoch.
        Precession is calculated using astronomical precession approximations centered on J2000. Note that
        while this function allows flexibility in coordinate epoch, it may fail at arbitrary coordinate epochs.
        It is recommended that when using an epoch that is not J2000, that the user transform to J2000 first.
    
            Args:
                      coords(astropy.skycoord): astropy.skycoord object containing the unprecessed coordinates.
                      epoch_now(string): The epoch of the date the user desires precession to. Usually the current epoch.
                      epoch(string): The epoch of the coordinates. J2000 is recommended.
            Returns:
                     self.coordinates(astropy.skycoord): astropy.skycoord object containing the new precessed coordinates.
    
        '''
    
        ra_in=coords.ra.deg
        dec_in=coords.dec.deg
        ep_in=float(epoch[1:])
        ep_now_in=float(epoch_now)
        print ra_in, dec_in, ep_in, ep_now_in
    
        T=(ep_now_in - ep_in)/100.0
        M=1.2812323*T+0.0003879*(T**2)+0.0000101*(T**3)
        N=0.5567530*T-0.0001185*(T**2)-0.0000116*(T**3)
        #print T, M, N
    
        d_ra= M + N*np.cos(ra_in* np.pi / 180.)*np.tan(dec_in* np.pi / 180.)
        d_dec=N*np.cos(ra_in* np.pi / 180.)
        #print d_ra, d_dec
    
        self.ra_out=ra_in+d_ra
        self.dec_out=dec_in+d_dec
        print self.ra_out,self.dec_out
    
        self.coordinates=SkyCoord(ra=float(self.ra_out)*u.degree,dec=float(self.dec_out)*u.degree,frame='icrs',equinox=str(epoch_now))
        return self.coordinates, self.ra_out, self.dec_out
    
    def startSlew(self,event):
        '''
        Slew Command from coordinates in control tab, also acts as a toggle. If telescope is slewing, this will stop current slewing. Stop slewing command acts as the ideal
        method for stopping the telescope. Halt Motion is the alternative intended for emergencies only. Before sending a slew command, startslew() checks the altitude of the
        target. If the altitude is below the altitude set in the configuration file, it will only return an error.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Slew to Target" button in the telescope control tab.
                
        Returns:
                None
                
        Information needed by Server: RA (Degrees), DEC (Degrees), 
        '''
        name=self.control.targetNameText.GetValue()
        input_ra=self.control.targetRaText.GetValue()
        input_dec=self.control.targetDecText.GetValue()
        input_epoch=self.control.targetEpochText.GetValue()
        current_epoch=self.control.currentEpochPos.GetLabel()
        
        
        
        if self.slewing==False:
            
            self.MRO_loc=EarthLocation(lat=46.9528*u.deg, lon=-120.7278*u.deg, height=1198*u.m)
            self.inputcoordSorter(input_ra,input_dec,input_epoch)
            self.obstarget=FixedTarget(name=name,coord=self.coordinates)
            
            if self.precession==True:
                self.coordprecess(self.coordinates,current_epoch,input_epoch)
                
            self.target_altaz = self.coordinates.transform_to(AltAz(obstime=Time.now(),location=self.MRO_loc))

            self.alt=str("{0.alt:.2}".format(self.target_altaz))
            self.split_alt=self.alt.split(' ')
            self.slew_altitude=self.split_alt[0]
            
            ''' Debug code
            self.decimalcoords=self.coordinates.to_string('decimal')
            
            
            self.log([input_ra,input_dec,current_epoch])
            self.protocol.sendCommand("slew"+' '+str(self.decimalcoords))
            self.control.slewButton.SetLabel('Stop Slew')
            self.sb.SetStatusText('Slewing: True',1)
            self.control.currentNamePos.SetLabel(name)
            self.control.currentNamePos.SetForegroundColour((0,0,0))
            '''
            if float(self.slew_altitude) > float(self.horizonlimit):

                self.decimalcoords=self.coordinates.to_string('decimal')
            
            	self.LST=str(self.control.currentLSTPos.GetLabel())
            	self.LST=self.LST.split(':')
            	self.LST=float(self.LST[0])+float(self.LST[1])/60.+float(self.LST[2])/3600.
                self.log([input_ra,input_dec,current_epoch])
                command="slew"+' '+str(self.decimalcoords)+' '+str(self.LST)
                self.protocol.sendCommand(command)
                thread.start_new_thread(self.velwatch,())
                #d.addCallback(self.vcback)
                self.control.slewButton.SetLabel('Stop Slew')
                self.sb.SetStatusText('Slewing: True',1)
                self.control.currentNamePos.SetLabel(name)
                self.control.currentNamePos.SetForegroundColour((0,0,0))
                self.control.currentRaPos.SetLabel(input_ra)
            	self.control.currentRaPos.SetForegroundColour((0,0,0))
            	self.control.currentDecPos.SetLabel(input_dec)
            	self.control.currentDecPos.SetForegroundColour((0,0,0))
                self.slewing= not self.slewing
                
                return
                         
            elif float(self.slew_altitude) < float(self.horizonlimit):
                dlg = wx.MessageDialog(self,
                               "Target is below current minimum altitude, cannot slew.",
                               "Error", wx.OK|wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.log("Error: Attempted slew altitude below 20 degrees.")
                return
                
        elif self.slewing==True:
            self.protocol.sendCommand("stop")
            self.control.slewButton.SetLabel('Start Slew')
            self.sb.SetStatusText('Slewing: False',1)
            
            self.slewing= not self.slewing
            
        return
    def velwatch(self):
    	time.sleep(0.5)
    	while self.slewing==True:
    		d=self.protocol.sendCommand("velmeasure")
    		d.addCallback(self.velmeasure)
    		time.sleep(0.5)
    		
    def velmeasure(self,msg):
    	print repr(msg)
    	msg=int(msg)
    	if msg==1:
    		self.slewing=False
    		wx.CallAfter(self.slewbutton_toggle)
    	if msg==0:
    		self.slewing=True
    		
    		
    def checkslew(self):
    	while True:
    		if self.slewing==False:
    			wx.CallAfter(self.slewbuttons_on,True,self.tracking)
    		if self.slewing==True:
    			wx.CallAfter(self.slewbuttons_on,False,self.tracking)
    		time.sleep(2.0)
    def slewbuttons_on(self,bool,track):
    	if track==False:
    		self.control.jogNButton.Enable(bool)
    		self.control.jogSButton.Enable(bool)
    		self.control.jogWButton.Enable(bool)
    		self.control.jogEButton.Enable(bool)
    	if track==True:
    		self.control.jogNButton.Enable(False)
    		self.control.jogSButton.Enable(False)
    		self.control.jogWButton.Enable(False)
    		self.control.jogEButton.Enable(False)
    	self.control.trackButton.Enable(bool)
    	self.init.parkButton.Enable(bool)
    	self.init.coverposButton.Enable(bool)
    	
    def slewbutton_toggle(self):
    	self.control.slewButton.SetLabel('Start Slew')
    	self.sb.SetStatusText('Slewing: False',1)
    	
    def getstatus(self):
    	time.sleep(5.0)
    	while True:
    		self.LST=str(self.control.currentLSTPos.GetLabel())
    		self.epoch=str(self.control.currentEpochPos.GetLabel())
    		self.UTC=str(self.control.currentUTCPos.GetLabel())
    		self.UTC=self.UTC.split(" ")
    		self.UTCdate=self.UTC[0].split("/")
    		self.UTCdate=self.UTCdate[0]+self.UTCdate[1]+self.UTCdate[2]
    		self.UTC=self.UTCdate+"T"+self.UTC[1]
    		self.sfile="logs/"+self.UTCdate+".txt"
    		self.LST=self.LST.split(':')
    		self.LST=float(self.LST[0])+float(self.LST[1])/60.+float(self.LST[2])/3600.
    		self.protocol.sendCommand("status "+str(self.UTC)+" "+str(self.epoch)+" "+str(self.LST)+" "+self.sfile)
    		time.sleep(15.0)
    		
    	 	
    	
    def set_target(self, event):
        """
        Take a selected item from the list and set it as the current target. Load it into the control tab and load it's coordinates into the guider control tab for finder charts
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Select as Current Target" button in the target list tab.
                
        Returns:
                None
        """
        sel_item=self.target.targetList.GetFocusedItem()
        
        name=str(self.target.targetList.GetItem(sel_item,col=0).GetText())
        input_ra=str(self.target.targetList.GetItem(sel_item,col=1).GetText())
        input_dec=str(self.target.targetList.GetItem(sel_item,col=2).GetText())
        input_epoch=str(self.target.targetList.GetItem(sel_item,col=3).GetText())
        mag = str(self.target.targetList.GetItem(sel_item,4).GetText())

        #self.coordinates=SkyCoord(ra,dec,frame='icrs')
        #self.guiderControl.current_target=FixedTarget(name=None,coord=self.coordinates)
        #self.image.current_target=FixedTarget(name=None,coord=self.coordinates)
        #self.load_finder_chart()

        #print name, ra, dec, epoch
        self.control.targetNameText.SetValue(name)
        self.control.targetRaText.SetValue(input_ra)
        self.control.targetDecText.SetValue(input_dec)
        self.control.targetEpochText.SetValue(input_epoch)
        self.control.targetMagText.SetValue(mag)
        
        self.log("Current target is '"+name+"'")
        
        return
        
        
    def LoadFinder(self,event):
        """
        Use Astroplan's plot_finder_image function to plot the finder image of the current target. Current location of finder chart is an axes object on the guider control tab.
        
        Args:
                self: points function towards WX application.
                
        Returns:
                None
        """
        name=self.control.targetNameText.GetValue()
        ra=self.control.targetRaText.GetValue()
        dec=self.control.targetDecText.GetValue()
        epoch=self.control.targetEpochText.GetValue()
        
        self.inputcoordSorter(ra,dec,epoch)
        self.finder_object=FixedTarget(name=None,coord=self.coordinates)
        plot_finder_image(self.finder_object, fov_radius=float(self.guiderControl.finderText.GetValue())*u.arcmin,ax=self.guiderControl.ax_l,reticle=False, log=False)
        return
        #self.image.fig.savefig("testfinder.png")
        #image_file = 'testfinder.png'
        
    def on_pick(self,event):
        artist = event.artist
        if isinstance(artist, AxesImage):
            im = artist
            A = im.get_array()
            center_x=A.shape[0]/2.0
            center_y=A.shape[1]/2.0
            mouseevent = event.mouseevent
            self.x = mouseevent.xdata
            self.y = mouseevent.ydata
            #print('onpick4 image', self.x,self.y, center_x, center_y)
            dx=self.x-center_x
            dy=self.y-center_y
            rho = np.sqrt(dx**2 + dy**2)
            phi = np.arctan2(dy, dx)
            phi_or=(phi*180./np.pi)-90
            print A.shape,rho,phi_or
	    if self.guider_rot==False:	
            	thread.start_new_thread(self.Rotate,(phi_or,))
            
    def on_Rot(self,event):
        #move = float(self.guiderRotText.GetValue()) - self.rotAng
        try:
            val=float(self.guiderControl.guiderRotText.GetValue())
        except ValueError:
            dlg = wx.MessageDialog(self,
                           "Input Error: Please input a valid number.",
                           "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
            return
	if val>0:
		while val>=360.0:
			val-=360.0
	if val<0:
		while val<=-360.0:
			val+=360.0

	if self.guider_rot==False:
        	thread.start_new_thread(self.Rotate,(-1*val,))
	   
    def Rotate(self,Rot_angle):
	self.guider_rot=True
        current_pos=self.guiderControl.rotAng
        if float(Rot_angle)-float(current_pos)>=0:
            inc=0.5
        else:
            inc=-0.5
        sweep_range=np.arange(current_pos, float(Rot_angle)+1, inc)
        for angle in sweep_range:
            wx.CallAfter(self.guiderControl.line.remove,)
            self.guiderControl.line = matplotlib.patches.Rectangle((150,150), height=125, width=2, fill=True, color='k',angle=float(angle))
            wx.CallAfter(self.guiderControl.ax_l.add_patch,self.guiderControl.line);
            wx.CallAfter(self.guiderControl.canvas_l.draw,)
            self.guiderControl.rotAng=float(angle)
            time.sleep(0.025)
	self.guider_rot=False
        return
    
    def addToList(self,event):
        """
        Add a manual text item from the target panel to the list control. Requires valid inputs for coordinate sorter. This includes valid formats for RA and DEC which are consistent with one another.
        Epoch should be inputted as J2000 or J1950. addToList runs a dynamic airmass calculation as per these inputs.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Add Item to List" button in the target list tab.
                
        Returns:
                None
        
        """
        t_name = self.target.nameText.GetValue()
        input_ra = self.target.raText.GetValue()
        input_dec = self.target.decText.GetValue()
        epoch = self.target.epochText.GetValue()
        mag  = self.target.magText.GetValue()
        epoch_now = self.control.currentEpochPos.GetLabel()
        
        self.inputcoordSorter(input_ra,input_dec,epoch)
        
        if self.galactic_coords==True:
            input_ra=self.coordinates.ra.degree
            input_dec=self.coordinates.dec.degree
        
        if self.precession==True:
            self.coordprecess(self.coordinates,epoch_now,epoch)
            
        self.obstarget=FixedTarget(name=t_name,coord=self.coordinates)
        #airmass= self.MRO.altaz(Time.now(),self.obstarget).secz
       
        
        #add transformation, the epoch should be current
        if self.validity==True:
            
            self.target.targetList.InsertStringItem(self.list_count,str(t_name))
            self.target.targetList.SetStringItem(self.list_count,1,str(input_ra))
            self.target.targetList.SetStringItem(self.list_count,2,str(input_dec))
            self.target.targetList.SetStringItem(self.list_count,3,str(epoch))
            self.target.targetList.SetStringItem(self.list_count,4,str(mag))
            #self.target.targetList.SetStringItem(0,5,str(airmass))
            #thread.start_new_thread(self.dyn_airmass,(self.obstarget,self.MRO,self.list_count,))
            t = threading.Thread(target=self.dyn_airmass, args=(self.obstarget,self.MRO,self.list_count,), name="airmass_"+str(self.list_count))
            t.daemon = True
            t.start()
            self.active_threads["airmass_"+str(self.list_count)] = t
            self.list_count+=1
        return
        
    def readToList(self,event):
        """
        Read in a target list file to the ctrl list.
        Format is: name;ra;dec;epoch
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Retrieve List" button in the target list tab.
                
        Returns:
                None
        
        """
        try:
            f_in=open(self.target.fileText.GetValue())
        except IOError:
            dlg = wx.MessageDialog(self,
                           "Path Error: File not Found.",
                           "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
            return
        #f_in=open(self.target.fileText.GetValue())
        for line in f_in:
            l = line.split(';')
            print l
            t_name = l[0]
            input_ra = l[1]
            input_dec = l[2]
            epoch = l[3]
            mag=l[4][0:-1]
            epoch_now = self.control.currentEpochPos.GetLabel()
            
            self.inputcoordSorter(input_ra,input_dec,epoch)
        
            if self.galactic_coords==True:
                input_ra=self.coordinates.ra.degree
                input_dec=self.coordinates.dec.degree
        
            if self.precession==True:
                self.coordprecess(self.coordinates,epoch_now,epoch)
            
            self.obstarget=FixedTarget(name=t_name,coord=self.coordinates)
       
            if self.validity==True:
            
                self.target.targetList.InsertStringItem(self.list_count,str(t_name))
                self.target.targetList.SetStringItem(self.list_count,1,str(input_ra))
                self.target.targetList.SetStringItem(self.list_count,2,str(input_dec))
                self.target.targetList.SetStringItem(self.list_count,3,str(epoch))
                self.target.targetList.SetStringItem(self.list_count,4,str(mag))
                #self.target.targetList.SetStringItem(0,5,str(airmass))
                #thread.start_new_thread(self.dyn_airmass,(self.obstarget,self.MRO,self.list_count,))
                t = threading.Thread(target=self.dyn_airmass, args=(self.obstarget,self.MRO,self.list_count,), name="airmass_"+str(self.list_count))
                t.daemon = True
                t.start()
                self.active_threads["airmass_"+str(self.list_count)] = t
                self.list_count+=1

        f_in.close()
        return
            
    def removeFromList(self,event):
        """
        Remove selected item from list. Operates by clearing list and then regenerating surviving entries.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Retrieve List" button in the target list tab.
                
        Returns:
                None
        
        """
        del_item=self.target.targetList.GetFocusedItem()
        self.calculate=False        
        for key in self.active_threads:
            self.active_threads[key].join()
            
        self.object_list=[]
        self.listrange=np.arange(0,self.target.targetList.GetItemCount())
        for row in self.listrange:
            if row!=del_item:
                name=self.target.targetList.GetItem(itemId=row, col=0).GetText()
                ra=self.target.targetList.GetItem(itemId=row, col=1).GetText()
                dec=self.target.targetList.GetItem(itemId=row, col=2).GetText()
                epoch=self.target.targetList.GetItem(itemId=row, col=3).GetText()
                vmag=self.target.targetList.GetItem(itemId=row, col=4).GetText()
            
                objectdata=str(name)+';'+str(ra)+';'+str(dec)+';'+str(epoch)+';'+str(vmag)
                self.object_list.append(objectdata)
            
        self.target.targetList.DeleteAllItems()
        self.active_threads={} 
        self.list_count=0
        self.calculate=True
        
        for entry in self.object_list:
            l=entry.split(';')
            t_name = l[0]
            input_ra = l[1]
            input_dec = l[2]
            epoch = l[3]
            mag=l[4]
            epoch_now = self.control.currentEpochPos.GetLabel()
                
            self.inputcoordSorter(input_ra,input_dec,epoch)
                
            if self.precession==True:
                self.coordprecess(self.coordinates,epoch_now,epoch)
            
            self.obstarget=FixedTarget(name=t_name,coord=self.coordinates)
            self.target.targetList.InsertStringItem(self.list_count,str(t_name))
            self.target.targetList.SetStringItem(self.list_count,1,str(input_ra))
            self.target.targetList.SetStringItem(self.list_count,2,str(input_dec))
            self.target.targetList.SetStringItem(self.list_count,3,str(epoch))
            self.target.targetList.SetStringItem(self.list_count,4,str(mag))
            t = threading.Thread(target=self.dyn_airmass, args=(self.obstarget,self.MRO,self.list_count,), name="airmass_"+str(self.list_count))
            t.daemon = True
            t.start()
            self.active_threads["airmass_"+str(self.list_count)] = t
            self.list_count+=1
    
    def FinderOpen(self,event):
        
        name=self.control.targetNameText.GetValue()
        ra=self.control.targetRaText.GetValue()
        dec=self.control.targetDecText.GetValue()
        epoch=self.control.targetEpochText.GetValue()
        
        self.window=FinderImageWindow(self, Finder_name=name)
        self.window.Show()
        
        self.inputcoordSorter(ra,dec,epoch)
        self.window.finder_object=FixedTarget(name=None,coord=self.coordinates)
        
        self.window.LoadFinder()

    
    def ExportOpen(self,event):  
        """
        Launch Export Window. Pull in current target list to window.
        
         Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Retrieve List" button in the target list tab.
                
        Returns:
                Export Window.
        """
        self.window=TargetExportWindow(self)
        self.window.Show()
        
        self.window.list=[]
        
        self.listrange=np.arange(0,self.target.targetList.GetItemCount())

        for row in self.listrange:
            name=self.target.targetList.GetItem(itemId=row, col=0).GetText()
            ra=self.target.targetList.GetItem(itemId=row, col=1).GetText()
            dec=self.target.targetList.GetItem(itemId=row, col=2).GetText()
            epoch=self.target.targetList.GetItem(itemId=row, col=3).GetText()
            vmag=self.target.targetList.GetItem(itemId=row, col=4).GetText()
            
            objectdata=str(name)+';'+str(ra)+';'+str(dec)+';'+str(epoch)+';'+str(vmag)
            self.window.list.append(objectdata)
            
        
        self.export_active=True
        
    
        
    def dyn_airmass(self,tgt,obs,count):
        """
        Continuously calculates the airmass using observer information and target information. Airmass is calculated using the secz function in astropy. 
        Dynamically updates in the target list and allows a quick read of the airmass for any given target.
        
        Args:
                tgt (FixedTarget): Astroplan FixedTarget object for the target, details target name and RA/DEC coordinates.
                obs (astroplan.Observer): Astroplan Observer object for observer location, details longitude, latitude and elevation of observer.
                count (integer): list counter that tracks the position of the target in the wx listctrl object, used to append airmass to correct row.
                
        Returns:
                a (float): airmass at current time.
        
        """
        while self.calculate==True:
            a= obs.altaz(Time.now(),tgt).secz
            if a > 8 or a < 0:
                a="N/A"
            wx.CallAfter(self.target.targetList.SetStringItem,count,5,str(a))
            #self.target.targetList.SetStringItem(count,5,str(a))
            time.sleep(1)
            
    
    def target_plot(self,event):
        '''
        Plot the selected targets position over the next 8 hours utilizing astroplan's plot_sky() method. This method plot with respect to target selected in
        the target list tab and not the GUI-set current target. Individual points are plotted with 1 hour cadence. Red point indicates current position 
        to specify direction of target trajectory. Note: Using this while a currentplot is being displayed will overwrite the current plot, this 
        overplotting has complications between radial and cartesian plots and will produce strange results. Exit the working plot before sending a new plot command.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Plot Target" button in the target list tab.
                
        Returns:
                Radial plot of target altitude and azimuth in new window or current plotting window (overplotting not advised).
        
        '''
        sel_item=self.target.targetList.GetFocusedItem()
        input_ra=self.target.targetList.GetItem(sel_item,col=1).GetText()
        input_dec=self.target.targetList.GetItem(sel_item,col=2).GetText()
        input_epoch=self.target.targetList.GetItem(sel_item,col=3).GetText()
        
        current_epoch=self.control.currentEpochPos.GetLabel()
        
        self.inputcoordSorter(input_ra,input_dec,input_epoch)
        
        if self.precession==True:
            self.coordprecess(self.coordinates,current_epoch,input_epoch) 
            
        self.targetobject=FixedTarget(name=self.target.targetList.GetItem(sel_item,0).GetText(),coord=self.coordinates)
        self.Obstime=Time.now()
        self.plot_times = self.Obstime + np.linspace(0, 8, 8)*u.hour
        self.target_style={'color':'Black'}
        self.initial_style={'color':'r'}
        
        plot_sky(self.targetobject, self.MRO, self.plot_times,style_kwargs=self.target_style)
        plt.legend(shadow=True, loc=2)
        plot_sky(self.targetobject, self.MRO, self.Obstime,style_kwargs=self.initial_style)
        plt.show()
        
    def airmass_plot(self,event):
        '''
        Plot the selected targets airmass curve over the next 10 hours utilizing astroplan's plot_airmass() method. This method plot with respect to target selected in
        the target list tab and not the GUI-set current target. Airmass warning limits at 2 and 2.5 are given as yellow and red lines respectively. Note: Using this while a current
        plot is being displayed will overwrite the current plot, this overplotting has complications between radial and cartesian plots and will produce strange results. Exit the working plot
        before sending a new plot command.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Airmass Curve" button in the target list tab.
                
        Returns:
                Airmass curve of target in new window or current plotting window (overplotting not advised).
        
        '''
        sel_item=self.target.targetList.GetFocusedItem()
        input_ra=self.target.targetList.GetItem(sel_item,col=1).GetText()
        input_dec=self.target.targetList.GetItem(sel_item,col=2).GetText()
        input_epoch=self.target.targetList.GetItem(sel_item,col=3).GetText()
        current_epoch=self.control.currentEpochPos.GetLabel()
        
        self.inputcoordSorter(input_ra,input_dec,input_epoch)
        
        if self.precession==True:
            self.coordprecess(self.coordinates,current_epoch,input_epoch) 
            
        self.targetobject=FixedTarget(name=self.target.targetList.GetItem(sel_item,0).GetText(),coord=self.coordinates)
        
        self.Obstime=Time.now()
        self.plot_times = self.Obstime + np.linspace(0, 10, 24)*u.hour
        self.target_style={'color':'Black'}
        self.airmass=plot_airmass(self.targetobject, self.MRO, self.plot_times,style_kwargs=self.target_style)
        plt.axhline(y=2,linestyle='--',color='orange')
        plt.axhline(y=2.5,linestyle='--',color='r')
        plt.legend(shadow=True, loc=1)
        plt.show()
            
    def setTelescopeZenith(self, event):
        """
        This is the basic pointing protocol for the telescope.  A bubble level is used to set the telescope to a known position. When the telescope is at Zenith the RA is the current LST, the 
        DEC is the Latitude of the telescope, and the Epoch is the current date transformed to the current epoch. setTelescopeZenith() produces these parameters and writes them to the
        initialization text boxes. Pushing these to the telescope is then accomplished by Set Telescope Position.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Load Zenith Coordinates" button in the initialization tab.
                
        Returns:
                None
        """
        name='Zenith'
        ra=self.control.currentLSTPos.GetLabel() #set to current LST
        dec='+46:57:10.08' #set to LAT
        epoch=self.control.currentEpochPos.GetLabel()#define as current epoch
        
        self.init.targetNameText.SetValue(name)
        self.init.targetRaText.SetValue(ra)
        self.init.targetDecText.SetValue(dec)
        self.init.targetEpochText.SetValue(epoch)
        
        return
        
            
            
    def setTelescopePosition(self,event):
        """
        Sends contents of the name, RA, DEC and EPOCH text boxes in the initialization tab to the control tab. Overwrites current control tab values in the status column with the sent values.
        Used to sync TCC values with physical position of telescope.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Set Telescope Position" button in the initialization tab.
                
        Returns:
                None
        """
        target_name=self.init.targetNameText.GetValue()
        target_ra=self.init.targetRaText.GetValue()
        target_dec=self.init.targetDecText.GetValue()
        target_epoch=self.init.targetEpochText.GetValue()
        
        if target_name=='':
            self.control.currentNamePos.SetLabel('Unknown')
            self.control.currentNamePos.SetForegroundColour((255,0,0))
        else:
            self.control.currentNamePos.SetLabel(str(target_name))
            self.control.currentNamePos.SetForegroundColour('black')   
        
        self.control.currentRaPos.SetLabel(str(target_ra))
        self.control.currentRaPos.SetForegroundColour('black')
        self.control.currentDecPos.SetLabel(str(target_dec))
        self.control.currentDecPos.SetForegroundColour('black')
        
        self.log('Syncing TCC position to'+' '+str(target_ra)+' '+str(target_dec))
        if target_name=="Zenith":
        	self.protocol.sendCommand("zenith")
        return
    def parkscope(self,event):
    	if self.slewing==False:
    		self.protocol.sendCommand("park")
    		
    def coverpos(self,event):
    	if self.slewing==False:
    		self.protocol.sendCommand("coverpos")
    		
    def pointing(self,event):
    	self.targetRA=str(self.control.currentRaPos.GetValue())
    	self.targetRA=self.targetRA.split(':')
    	self.targetRA=float(self.targetRA[0])+float(self.targetRA[1])/60.+float(self.targetRA[2])/3600.
    	self.targetRA=self.targetRA*15.0 #Degrees
    	self.targetDEC=str(self.control.currentDecPos.GetValue())
    	self.targetDEC=self.targetDEC.split(':')
    	self.targetDEC=float(self.targetDEC[0])+float(self.targetDEC[1])/60.+float(self.targetDEC[2])/3600.
    	self.LST=str(self.control.currentLSTPos.GetValue())
    	self.LST=self.LST.split(':')
    	self.LST=float(self.LST[0])+float(self.LST[1])/60.+float(self.LST[2])/3600.
    	self.protocol.sendCommand("point "+self.targetRA+ " "+self.targetDec+" "+self.LST)
    		
    def setRATrackingRate(self,event):
        """
        Sets telescope RA tracking rate to the value specified in the RA tracking rate text box in the initialization tab.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Set RA Tracking Rate" button in the initialization tab.
                
        Returns:
                None
        """
        RArate=self.init.trackingRateRAText.GetValue()
        
        valid_input=True
        
        try:
            val=float(RArate)
        except ValueError:
            valid_input=False
        
        if valid_input==True:
            self.control.currentRATRPos.SetLabel(RArate)
            self.control.currentRATRPos.SetForegroundColour('black')
        else:
            dlg = wx.MessageDialog(self,
                               "Please input an integer or float number.",
                               "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
        return
        
    def setDECTrackingRate(self,event):
        """
        Sets telescope DEC tracking rate to the value specified in the RA tracking rate text box in the initialization tab.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Set DEC Tracking Rate" button in the initialization tab.
                
        Returns:
                None
        """
        DECrate=self.init.trackingRateDECText.GetValue()
        
        valid_input=True
        
        try:
            val=float(DECrate)
        except ValueError:
            valid_input=False
        
        if valid_input==True:
            self.control.currentDECTRPos.SetLabel(DECrate)
            self.control.currentDECTRPos.SetForegroundColour('black')
        else:
            dlg = wx.MessageDialog(self,
                               "Please input an integer or float number.",
                               "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy() 
        return
        
    def onInit(self,event):
        """
        Initialize telescope systems according to values set in the TCC config file. Enables buttons throughout the GUI that depend on initialized systems to function.
        
        Args:
                self: points function towards WX application.
                event: handler to allow function to be tethered to a wx widget. Tethered to the "Initialize Telescope Systems" button in the initialization tab.
                
        Returns:
                None
        """
        if self.initState==False:
            self.mro.lon=self.dict['lon']
            self.mro.lat=self.dict['lat']
            self.horizonlimit=self.dict['horizonLimit']
        
        
            self.control.slewButton.Enable()
            self.control.trackButton.Enable()
            self.init.atZenithButton.Enable()
        
            self.target.listButton.Enable()
            self.target.selectButton.Enable()
            self.target.enterButton.Enable()
            self.target.removeButton.Enable()
            self.target.exportButton.Enable()
            self.target.plot_button.Enable()
            self.target.airmass_button.Enable()
            self.init.parkButton.Enable()
            self.init.coverposButton.Enable()
            self.init.onTargetButton.Enable()
        
            thread.start_new_thread(self.timer,())
            thread.start_new_thread(self.checkslew,())
            print "Slew Checking On"
            thread.start_new_thread(self.getstatus,())
            self.initState=True
        if self.initState==True:
            self.control.currentJDPos.SetForegroundColour('black')
            self.control.currentLSTPos.SetForegroundColour('black')
            self.control.currentUTCPos.SetForegroundColour('black')
            self.control.currentLocalPos.SetForegroundColour('black')
            self.control.currentEpochPos.SetForegroundColour('black')
            self.sb.SetStatusText('ERROR: Telescope Not Responding',3)

    def timer(self):
        """
        Dynamically updates Julian Date, LST, UTC, Local Time and current Epoch in the telescope control tab.
        
        Args:
                self: points function towards WX application.
                
        Returns:
                None
        """
        while True:
            t = self.timeCalc()
            wx.CallAfter(self.control.currentJDPos.SetLabel,( '%.2f' % t['mjd']))
            wx.CallAfter(self.control.currentLSTPos.SetLabel,(str(t['lst'])))
            wx.CallAfter(self.control.currentUTCPos.SetLabel,(str(t['utc'])))
            wx.CallAfter(self.control.currentLocalPos.SetLabel,(str(t['local'])))
            wx.CallAfter(self.control.currentEpochPos.SetLabel,('%.3f' % t['epoch']))
            time.sleep(1)

    def timeCalc(self):
        """
       Calculates current time values for Julian Date, Epoch, Local Time and LST.
        
        Args:
                self: points function towards WX application.
                
        Returns:
                None
        """
        t = Time(Time.now())

        jdt=t.jd
        mjdt = t.mjd
        epoch = 1900.0 + ((float(jdt)-2415020.31352)/365.242198781)
        
        if self.current_timezone=="PST":
            local = time.strftime('%Y/%m/%d %H:%M:%S')
        if self.current_timezone=="MST":
            MST = datetime.now() + timedelta(hours=1)
            local=MST.strftime("%Y/%m/%d %H:%M:%S")
            #MST_rounded=MST.split('.')[0]
            #local=MST_rounded.replace("-","/")
        self.mro.date=dati.datetime.utcnow()
        lst = self.mro.sidereal_time()
        return {'mjd':mjdt,'utc':self.mro.date,'local':local,'epoch':epoch, 'lst':lst}

    def getFocus(self,event):
        num=self.focusNum.GetValue()
        files=os.popen('tail -%s /Users/%s/nfocus.txt' % (num, os.getenv('USER')), 'r')
        for l in files:
            self.focusLog.AppendText(l)
            
'''
Additional Frames called during GUI operation
'''

class TargetExportWindow(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self, parent, -1, "Export to Target List File", size=(300,200))
        
        self.parent=parent
        self.defaultdirectory='targetlists'
        
        self.panel=Export(self)
        
        self.panel.pathText.SetValue(self.defaultdirectory)
        
        self.Bind(wx.EVT_BUTTON, self.onExport, self.panel.ExButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, self.panel.CancelButton)
        
    def onExport(self,event):
        f = open(str(self.panel.pathText.GetValue()+'/'+self.panel.filenameText.GetValue()), 'w')
        for item in self.list:
            f.write(str(item)+'\n')
        f.close()
        self.Close()
        
    def onCancel(self, event):
        self.Close()

class Export(wx.Panel): 
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        
        self.parent=parent
        
        self.pathLabel = wx.StaticText(self, size=(75,-1))
        self.pathLabel.SetLabel('Output Path: ')
        self.pathText = wx.TextCtrl(self,size=(-1,-1))
        
        self.filenameLabel = wx.StaticText(self, size=(75,-1))
        self.filenameLabel.SetLabel('File Name: ')
        self.filenameText = wx.TextCtrl(self,size=(-1,-1))
        
        self.ExButton=wx.Button(self,-1,"Export")
        self.CancelButton=wx.Button(self,-1,"Cancel")
        
        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        
        self.hbox1.AddSpacer(15)
        self.hbox1.Add(self.pathLabel,0,wx.ALIGN_LEFT)
        self.hbox1.Add(self.pathText,1,wx.ALIGN_LEFT)
        self.hbox1.AddSpacer(15)
        
        self.hbox2.AddSpacer(15)
        self.hbox2.Add(self.filenameLabel,0,wx.ALIGN_LEFT)
        self.hbox2.Add(self.filenameText,1,wx.ALIGN_LEFT)
        self.hbox2.AddSpacer(15)
        
        self.hbox3.Add(self.CancelButton,0,wx.ALIGN_CENTER)
        self.hbox3.AddSpacer(20)
        self.hbox3.Add(self.ExButton,1,wx.ALIGN_CENTER)
        
        self.vbox.AddSpacer(15)
        self.vbox.Add(self.hbox1,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(15)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_LEFT|wx.EXPAND)
        self.vbox.AddSpacer(15)
        self.vbox.Add(self.hbox3,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(15)
        
        self.SetSizer(self.vbox)
        
        
'''
Twisted Python
'''
class DataForwardingProtocol(basic.LineReceiver):

    def __init__(self):
        self.output = None
        self._deferreds = {}

    def dataReceived(self, data):
        gui = self.factory.gui
        gui.protocol = self
        gui.control.protocol= self
        print "data recieved from server" ,data

        if gui:
            val = gui.control.logBox.GetValue()
            self.timestamp()
            gui.control.logBox.SetValue(val+stamp+data+'\n')
            gui.control.logBox.SetInsertionPointEnd()
            sep_data= data.split(" ")
            if sep_data[0] in self._deferreds:
                self._deferreds.pop(sep_data[0]).callback(sep_data[1])

    def sendCommand(self, data):
        self.transport.write(data)
        d=self._deferreds[data.split(" ")[0]]=defer.Deferred()
        return d
    
    def connectionMade(self):
        gui=self.factory.gui
        gui.protocol=self
        self.output = self.factory.gui.control.logBox
    def timestamp(self):
    	t=datetime.now()
    	if len(str(t.month))==1:
    		month='0'+str(t.month)
    	else:
    		month=str(t.month)
    	if len(str(t.day))==1:
    		day='0'+str(t.day)
    	else:
    		day=str(t.day)
    	if len(str(t.hour))==1:
    		hour='0'+str(t.hour)
    	else:
    		hour=str(t.hour)
    	if len(str(t.minute))==1:
    		minute='0'+str(t.minute)
    	else:
    		minute=str(t.minute)
    	if len(str(t.second))==1:
    		second='0'+str(t.second)
    	else:
    		second=str(t.second)
    	global stamp
    	stamp=str(t.year)+str(month)+str(day)+'  '+str(hour)+':'+str(minute)+':'+str(second)+': '
    	return stamp
    	
    	

class TCCClient(protocol.ClientFactory):

    def __init__(self, gui):
        self.gui = gui
        self.protocol = DataForwardingProtocol

    def clientConnectionLost(self, transport, reason):
        reactor.stop()

    def clientConnectionFailed(self, transport, reason):
        reactor.stop()

if __name__=="__main__":
	try:
  		app = wx.App(False)
  		app.frame = TCC()
  		app.frame.Show()
  		reactor.registerWxApp(app)
  		#pipe= subprocess.Popen("./parsercode/test",shell=True, preexec_fn=os.setsid)
  		#thread.start_new_thread(os.system,("./parsercode/test",))
  		time.sleep(3)
  		reactor.connectTCP('localhost',5501,TCCClient(app.frame))
  		reactor.run()
  		app.MainLoop()
	except KeyboardInterrupt:
		os.killpg(os.getpgid(pipe.pid),signal.SIGTERM)
		sys.exit(0)
