# -- coding: UTF-8 --
import wx
import cv2
import numpy as np
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from utils.excel_exporter import ExcelExporter
from utils.image_utils import ImageHandler
from utils.plot_handler import PlotHandler
from utils.rectangle_handler import RectangleHandler
from .panels.image_panel import ImagePanel
from .panels.plot_panel import PlotPanel
from .dialogs.settings_dialog import SettingsDialog

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Gray Scale Analyzer', size=(1200, 800))
        
        # Initialize variables
        self.rect_color = (0, 255, 0)  # BGR format, green
        self.MAX_POINTS = 3000
        self.MIN_RECT_WIDTH = 20
        self.MIN_RECT_HEIGHT = 20
        self.line_color = "#0000ff"
        self.line_width = 0.5
        self.circle_radius = 5
        self.highlight_color = (0, 255, 0)
        self.rect_thickness = 2
        self.plot_type = "scatter"  # Default plot type
        
        # Initialize handlers
        self.image_handler = ImageHandler()
        self.plot_handler = PlotHandler()
        self.rect_handler = RectangleHandler()
        
        # Create UI
        self.init_ui()
        
        # Create status bar
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("Ready")
        
        # Show the frame
        self.Centre()
        self.Show()

    def init_ui(self):
        """Initialize the user interface"""
        # Create main panel and sizer
        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create horizontal splitter for image and plots
        splitter = wx.SplitterWindow(self.panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        
        # Left side - Image panel
        self.image_panel = ImagePanel(splitter, self)
        
        # Right side - Plot panel
        self.plot_panel = PlotPanel(splitter, self)
        
        # Set up splitter
        splitter.SplitVertically(self.image_panel, self.plot_panel)
        splitter.SetSashGravity(0.6)  # 60% for image, 40% for plots
        splitter.SetMinimumPaneSize(300)
        
        self.main_sizer.Add(splitter, 1, wx.EXPAND)
        self.panel.SetSizer(self.main_sizer)
        
        # Bind events
        self.Bind(wx.EVT_SIZE, self.on_size)
        
        # Set up accelerator table for keyboard shortcuts
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN),
            (wx.ACCEL_CTRL, ord('S'), wx.ID_SAVE),
            (wx.ACCEL_CTRL, ord('E'), wx.ID_ANY),  # Export
            (wx.ACCEL_CTRL, ord('Q'), wx.ID_EXIT),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, wx.ID_DELETE),  # Delete selected rectangle
        ])
        self.SetAcceleratorTable(accel_tbl)

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        open_item = file_menu.Append(wx.ID_OPEN, '&Open Image\tCtrl+O', 'Open an image file')
        save_item = file_menu.Append(wx.ID_SAVE, '&Save Results\tCtrl+S', 'Save analysis results')
        file_menu.AppendSeparator()
        export_item = file_menu.Append(wx.ID_ANY, '&Export to Excel\tCtrl+E', 'Export data to Excel')
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, 'E&xit\tCtrl+Q', 'Exit the application')
        
        # Settings menu
        settings_menu = wx.Menu()
        points_item = settings_menu.Append(wx.ID_ANY, '&Max Points', 'Set maximum points')
        rect_size_item = settings_menu.Append(wx.ID_ANY, '&Min Rectangle Size', 'Set minimum rectangle size')
        settings_all_item = settings_menu.Append(wx.ID_ANY, '&All Settings', 'Open settings dialog')
        
        # View menu
        view_menu = wx.Menu()
        self.splitter_item = view_menu.AppendCheckItem(wx.ID_ANY, '&Adjustable Panels', 'Toggle adjustable panels')
        self.splitter_item.Check(True)
        
        menubar.Append(file_menu, '&File')
        menubar.Append(settings_menu, '&Settings')
        menubar.Append(view_menu, '&View')
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_open, open_item)
        self.Bind(wx.EVT_MENU, self.on_save, save_item)
        self.Bind(wx.EVT_MENU, self.on_export, export_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_set_points, points_item)
        self.Bind(wx.EVT_MENU, self.on_set_rect_size, rect_size_item)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_all_item)

    def create_toolbar(self):
        """Create the toolbar"""
        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add buttons
        open_btn = wx.Button(self.panel, label='Open Image')
        save_btn = wx.Button(self.panel, label='Save Results')
        export_btn = wx.Button(self.panel, label='Export to Excel')
        settings_btn = wx.Button(self.panel, label='Settings')
        
        open_btn.Bind(wx.EVT_BUTTON, self.on_open)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        settings_btn.Bind(wx.EVT_BUTTON, self.on_settings)
        
        self.toolbar.Add(open_btn, 0, wx.ALL, 5)
        self.toolbar.Add(save_btn, 0, wx.ALL, 5)
        self.toolbar.Add(export_btn, 0, wx.ALL, 5)
        self.toolbar.Add(settings_btn, 0, wx.ALL, 5)
        
        # Add status text
        self.status_text = wx.StaticText(self.panel, label=f"Max Points: {self.MAX_POINTS}")
        self.toolbar.Add(self.status_text, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        self.main_sizer.Add(self.toolbar, 0, wx.EXPAND)

    def on_size(self, event):
        """Handle window resize events"""
        event.Skip()
        if hasattr(self, 'image_panel'):
            self.image_panel.on_size()

    def on_open(self, event):
        """Handle open image"""
        with wx.FileDialog(self, "Choose an image", wildcard="Image files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg",
                         style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
        try:
            self.image_panel.load_image(pathname)
            self.plot_panel.clear_all_plots()
            self.statusbar.SetStatusText(f"Loaded: {pathname}")
        except Exception as e:
            wx.MessageBox(f'Error loading image: {str(e)}', 'Error',
                        wx.OK | wx.ICON_ERROR)
            self.statusbar.SetStatusText("Error loading image")

    def on_save(self, event):
        """Handle save results"""
        if not hasattr(self.image_panel, 'original_img') or self.image_panel.original_img is None:
            wx.MessageBox('No image loaded', 'Error', wx.OK | wx.ICON_ERROR)
            return
            
        with wx.FileDialog(self, "Save results", wildcard="PNG files (*.png)|*.png",
                         style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
            try:
                self.image_panel.save_results(pathname)
                wx.MessageBox('Results saved successfully', 'Success', wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f'Error saving results: {str(e)}', 'Error',
                            wx.OK | wx.ICON_ERROR)

    def on_export(self, event):
        """Export analysis results to Excel"""
        if not hasattr(self.image_panel, 'rectangles') or not self.image_panel.rectangles:
            wx.MessageBox('No regions selected for export', 'Error', wx.OK | wx.ICON_ERROR)
            return
            
        with wx.FileDialog(self, "Export to Excel", wildcard="Excel files (*.xlsx)|*.xlsx",
                         style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            pathname = fileDialog.GetPath()
            try:
                self.image_panel.export_to_excel(pathname)
                wx.MessageBox('Data exported successfully', 'Success', wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f'Error exporting data: {str(e)}', 'Error',
                            wx.OK | wx.ICON_ERROR)

    def on_exit(self, event):
        """Handle exit"""
        self.Close()

    def on_set_points(self, event):
        """Handle set max points"""
        dlg = wx.NumberEntryDialog(self, 'Enter maximum points (0 for actual points):', 
                                  'Max Points', 'Set Maximum Points', 
                                  self.MAX_POINTS, 0, 100000)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAX_POINTS = dlg.GetValue()
            self.status_text.SetLabel(f"Max Points: {'Actual' if self.MAX_POINTS == 0 else self.MAX_POINTS}")
        dlg.Destroy()

    def on_set_rect_size(self, event):
        """Handle set minimum rectangle size"""
        dlg = wx.MultiChoiceDialog(self, 'Set minimum rectangle size:', 'Rectangle Size',
                                  [f'Width: {self.MIN_RECT_WIDTH}', f'Height: {self.MIN_RECT_HEIGHT}'])
        
        # Use a simpler dialog
        width_dlg = wx.NumberEntryDialog(self, 'Enter minimum width:', 
                                        'Width', 'Minimum Rectangle Width', 
                                        self.MIN_RECT_WIDTH, 1, 1000)
        if width_dlg.ShowModal() == wx.ID_OK:
            self.MIN_RECT_WIDTH = width_dlg.GetValue()
            
        height_dlg = wx.NumberEntryDialog(self, 'Enter minimum height:', 
                                         'Height', 'Minimum Rectangle Height', 
                                         self.MIN_RECT_HEIGHT, 1, 1000)
        if height_dlg.ShowModal() == wx.ID_OK:
            self.MIN_RECT_HEIGHT = height_dlg.GetValue()
            
        width_dlg.Destroy()
        height_dlg.Destroy()

    def on_settings(self, event):
        """Handle settings button"""
        dlg = SettingsDialog(self, self.MAX_POINTS, self.MIN_RECT_WIDTH, 
                           self.MIN_RECT_HEIGHT, self.rect_color, self.plot_type)
        if dlg.ShowModal() == wx.ID_OK:
            settings = dlg.get_settings()
            self.MAX_POINTS = settings['max_points']
            self.MIN_RECT_WIDTH = settings['min_width']
            self.MIN_RECT_HEIGHT = settings['min_height']
            self.rect_color = settings['color']
            old_plot_type = self.plot_type
            self.plot_type = settings['plot_type']
            
            # Update status
            self.status_text.SetLabel(f"Max Points: {'Actual' if self.MAX_POINTS == 0 else self.MAX_POINTS}")
            
            # Update image panel
            if hasattr(self, 'image_panel'):
                self.image_panel.rect_color = self.rect_color
                self.image_panel.MIN_RECT_WIDTH = self.MIN_RECT_WIDTH
                self.image_panel.MIN_RECT_HEIGHT = self.MIN_RECT_HEIGHT
                self.image_panel.Refresh()
                
            # Refresh all plots if plot type changed
            if old_plot_type != self.plot_type and hasattr(self, 'plot_panel'):
                self.plot_panel.refresh_all_plots(self.plot_type)
                
        dlg.Destroy()

    def update_plot(self, region_data, rect_index):
        """Update plot for a specific rectangle"""
        max_points = region_data.get('max_points', self.MAX_POINTS)
        self.plot_panel.update_plot(region_data, rect_index, max_points)

    def select_plot_tab(self, rect_index):
        """Select the plot tab for a specific rectangle"""
        self.plot_panel.select_plot_tab(rect_index)

    def highlight_rectangle(self, rect_index):
        """Highlight a specific rectangle when its tab is selected"""
        self.image_panel.highlight_rectangle(rect_index)

    def remove_plot(self, rect_index):
        """Remove plot for a specific rectangle"""
        self.plot_panel.remove_plot(rect_index)
