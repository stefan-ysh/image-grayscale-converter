# -- coding: UTF-8 --
import wx

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, max_points, min_width, min_height, rect_color, plot_type="scatter"):
        super().__init__(parent, title="Settings", size=(400, 600))

        self.max_points = max_points
        self.min_width = min_width
        self.min_height = min_height
        self.rect_color = rect_color
        self.plot_type = plot_type
        
        self.init_ui()
        self.Center()  # Center the dialog
        
    def init_ui(self):
        """Initialize the user interface"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Max Points setting
        points_box = wx.StaticBox(panel, label="Maximum Points")
        points_sizer = wx.StaticBoxSizer(points_box, wx.VERTICAL)
        
        points_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        points_label = wx.StaticText(panel, label="Max Points:")
        self.points_ctrl = wx.SpinCtrl(panel, value=str(self.max_points), 
                                      min=0, max=100000)
        self.actual_points_cb = wx.CheckBox(panel, label="Use actual points (0)")
        
        if self.max_points == 0:
            self.actual_points_cb.SetValue(True)
            self.points_ctrl.Enable(False)
        
        points_h_sizer.Add(points_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        points_h_sizer.Add(self.points_ctrl, 1, wx.ALL, 5)
        points_sizer.Add(points_h_sizer, 0, wx.EXPAND)
        points_sizer.Add(self.actual_points_cb, 0, wx.ALL, 5)
        
        # Rectangle size settings
        rect_box = wx.StaticBox(panel, label="Minimum Rectangle Size")
        rect_sizer = wx.StaticBoxSizer(rect_box, wx.VERTICAL)
        
        width_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        width_label = wx.StaticText(panel, label="Min Width:")
        self.width_ctrl = wx.SpinCtrl(panel, value=str(self.min_width), 
                                     min=1, max=1000)
        width_h_sizer.Add(width_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        width_h_sizer.Add(self.width_ctrl, 1, wx.ALL, 5)
        
        height_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        height_label = wx.StaticText(panel, label="Min Height:")
        self.height_ctrl = wx.SpinCtrl(panel, value=str(self.min_height), 
                                      min=1, max=1000)
        height_h_sizer.Add(height_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        height_h_sizer.Add(self.height_ctrl, 1, wx.ALL, 5)
        
        rect_sizer.Add(width_h_sizer, 0, wx.EXPAND)
        rect_sizer.Add(height_h_sizer, 0, wx.EXPAND)
        
        # Plot Type setting
        plot_box = wx.StaticBox(panel, label="Plot Type")
        plot_sizer = wx.StaticBoxSizer(plot_box, wx.VERTICAL)
        
        self.plot_type_choice = wx.Choice(panel, choices=["Scatter Plot", "Line Plot"])
        if self.plot_type == "line":
            self.plot_type_choice.SetSelection(1)
        else:
            self.plot_type_choice.SetSelection(0)
        
        plot_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plot_label = wx.StaticText(panel, label="Type:")
        plot_h_sizer.Add(plot_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        plot_h_sizer.Add(self.plot_type_choice, 1, wx.ALL, 5)
        plot_sizer.Add(plot_h_sizer, 0, wx.EXPAND)
        
        # Color setting
        color_box = wx.StaticBox(panel, label="Rectangle Color")
        color_sizer = wx.StaticBoxSizer(color_box, wx.VERTICAL)
        
        color_h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        color_label = wx.StaticText(panel, label="Color:")
        self.color_btn = wx.Button(panel, label="Choose Color")
        self.color_preview = wx.Panel(panel, size=(50, 25))
        self.color_preview.SetBackgroundColour(wx.Colour(self.rect_color[2], 
                                                        self.rect_color[1], 
                                                        self.rect_color[0]))
        
        color_h_sizer.Add(color_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        color_h_sizer.Add(self.color_btn, 0, wx.ALL, 5)
        color_h_sizer.Add(self.color_preview, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        color_sizer.Add(color_h_sizer, 0, wx.EXPAND)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_btn, 0, wx.ALL, 5)
        button_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        # Main layout
        main_sizer.Add(points_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(rect_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(plot_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(color_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Make the dialog fit its contents
        # self.Fit()
        
        # Bind events
        self.actual_points_cb.Bind(wx.EVT_CHECKBOX, self.on_actual_points)
        self.color_btn.Bind(wx.EVT_BUTTON, self.on_choose_color)
        
    def on_actual_points(self, event):
        """Handle actual points checkbox"""
        if self.actual_points_cb.GetValue():
            self.points_ctrl.Enable(False)
            self.points_ctrl.SetValue(0)
        else:
            self.points_ctrl.Enable(True)
            if self.points_ctrl.GetValue() == 0:
                self.points_ctrl.SetValue(3000)
    
    def on_choose_color(self, event):
        """Handle color button"""
        data = wx.ColourData()
        data.SetChooseFull(True)
        data.SetColour(wx.Colour(self.rect_color[2], self.rect_color[1], self.rect_color[0]))
        
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            color = dlg.GetColourData().GetColour()
            self.rect_color = (color.Blue(), color.Green(), color.Red())
            self.color_preview.SetBackgroundColour(color)
            self.color_preview.Refresh()
        
        dlg.Destroy()
    
    def get_settings(self):
        """Get the current settings"""
        plot_type = "scatter" if self.plot_type_choice.GetSelection() == 0 else "line"
        return {
            'max_points': self.points_ctrl.GetValue() if not self.actual_points_cb.GetValue() else 0,
            'min_width': self.width_ctrl.GetValue(),
            'min_height': self.height_ctrl.GetValue(),
            'color': self.rect_color,
            'plot_type': plot_type
        }
