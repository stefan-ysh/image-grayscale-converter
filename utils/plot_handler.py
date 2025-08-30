import matplotlib
matplotlib.use('WXAgg')  # This line should be before importing pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import numpy as np
import wx


class PlotHandler:
    @staticmethod
    def create_plot_panel(parent, region_data=None, title="Grayscale Distribution"):
        """Create a new plot panel with the specified data
        Args:
            parent: wx.Panel to add the plot to
            region_data: Optional numpy array of pixel values
            title: Title for the plot
        Returns:
            wx.Panel containing the plot
        """
        # Create matplotlib figure and canvas
        panel = wx.Panel(parent)
        figure = Figure(figsize=(6, 4), dpi=100)
        canvas = FigureCanvas(panel, -1, figure)
        
        # Add canvas to panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        
        # Create the plot
        ax = figure.add_subplot(111)
        
        if region_data is None:
            # Show placeholder text
            ax.text(0.5, 0.5, 'Select a region to show plot',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            # Plot histogram data
            points = min(len(region_data.ravel()), 3000)  # Limit points for performance
            indices = np.linspace(0, len(region_data.ravel())-1, points, dtype=int)
            data = region_data.ravel()[indices]
            ax.hist(data, bins=256, range=(0, 256), density=True)
            ax.set_xlabel('Gray Level')
            ax.set_ylabel('Frequency')
            ax.set_title(f'{title} ({points} points)')
        
        # Layout and finish
        figure.tight_layout()
        canvas.draw()
        panel.figure = figure
        panel.canvas = canvas
        return panel

    @staticmethod
    def update_plot(panel, region_data=None, title="Grayscale Distribution"):
        """Update an existing plot with new data
        Args:
            panel: wx.Panel containing the plot
            region_data: Optional numpy array of pixel values
            title: Title for the plot
        """
        if not hasattr(panel, 'figure') or not hasattr(panel, 'canvas'):
            return
            
        figure = panel.figure
        canvas = panel.canvas
        figure.clear()
        
        ax = figure.add_subplot(111)
        if region_data is None:
            # Show placeholder text
            ax.text(0.5, 0.5, 'Select a region to show plot',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            # Plot histogram data
            points = min(len(region_data.ravel()), 3000)  # Limit points for performance
            indices = np.linspace(0, len(region_data.ravel())-1, points, dtype=int)
            data = region_data.ravel()[indices]
            ax.hist(data, bins=256, range=(0, 256), density=True)
            ax.set_xlabel('Gray Level')
            ax.set_ylabel('Frequency')
            ax.set_title(f'{title} ({points} points)')
        
        figure.tight_layout()
        canvas.draw()
