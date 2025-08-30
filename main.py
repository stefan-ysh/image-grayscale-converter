# -- coding: UTF-8 --
import os
import sys
import wx
import cv2
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from PIL import Image
from utils.excel_exporter import ExcelExporter
from utils.image_utils import ImageHandler
from utils.plot_handler import PlotHandler
from utils.rectangle_handler import RectangleHandler
from ui.main_frame import MainFrame

def main():
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()

if __name__ == '__main__':
    main()
