# -- coding: UTF-8 --
import wx
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotPanel(wx.Panel):
    def __init__(self, parent, main_frame):
        super().__init__(parent)
        
        self.main_frame = main_frame
        self.plot_data = {}  # Store plot data by rectangle index
        
        # Create notebook for multiple plots with scrollable tabs
        self.notebook = wx.Notebook(parent=self, style=wx.NB_MULTILINE)
        
        # Add default "No plots" page
        self.no_plots_panel = wx.Panel(self.notebook)
        no_plots_sizer = wx.BoxSizer(wx.VERTICAL)
        no_plots_text = wx.StaticText(self.no_plots_panel, label="Select a region to show plot")
        no_plots_sizer.Add(no_plots_text, 1, wx.ALIGN_CENTER)
        self.no_plots_panel.SetSizer(no_plots_sizer)
        self.notebook.AddPage(self.no_plots_panel, "Plots")
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Bind tab selection event
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)

    def on_tab_changed(self, event):
        """Handle tab selection change"""
        selection = event.GetSelection()
        
        # Skip the first tab (No plots)
        if selection == 0:
            return
            
        # Find the rectangle index for this tab
        page = self.notebook.GetPage(selection)
        for rect_index, plot_data in self.plot_data.items():
            if plot_data['panel'] == page:
                # Notify main frame to highlight the rectangle
                self.main_frame.highlight_rectangle(rect_index)
                break
        
        event.Skip()

    def has_plot(self, rect_index):
        """Check if a plot exists for the given rectangle index"""
        return rect_index in self.plot_data

    def update_plot(self, region_data, rect_index, max_points):
        """Update or create plot for a specific rectangle"""
        # If plot already exists, update it
        if rect_index in self.plot_data:
            self.update_existing_plot(region_data, rect_index, max_points)
        else:
            self.create_new_plot(region_data, rect_index, max_points)

    def create_new_plot(self, region_data, rect_index, max_points):
        """Create a new plot for the rectangle"""
        # Create new panel and figure
        panel = wx.Panel(self.notebook)
        figure = Figure(figsize=(6, 4))
        canvas = FigureCanvas(panel, -1, figure)
        
        # Create sizer for the panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(canvas, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        
        # Store plot data
        self.plot_data[rect_index] = {
            'panel': panel,
            'figure': figure,
            'canvas': canvas,
            'ax': None
        }
        
        # Add to notebook
        rect_name = region_data.get('name', f"Region {rect_index + 1}")
        page_title = rect_name
        self.notebook.AddPage(panel, page_title)
        
        # Generate the plot
        self.generate_histogram(region_data, rect_index, max_points)
        
        # Select the new tab
        page_count = self.notebook.GetPageCount()
        self.notebook.SetSelection(page_count - 1)
        
        # Bind tab selection event
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)

    def update_existing_plot(self, region_data, rect_index, max_points):
        """Update an existing plot"""
        if rect_index in self.plot_data:
            # Clear the figure and regenerate
            figure = self.plot_data[rect_index]['figure']
            figure.clear()
            self.plot_data[rect_index]['ax'] = None
            
            # Generate new plot
            self.generate_histogram(region_data, rect_index, max_points)

    def generate_histogram(self, region_data, rect_index, max_points):
        """Generate scatter plot for the region data showing pixel index vs grayscale value"""
        if rect_index not in self.plot_data:
            return
            
        figure = self.plot_data[rect_index]['figure']
        canvas = self.plot_data[rect_index]['canvas']
        
        # Create subplot
        ax = figure.add_subplot(111)
        self.plot_data[rect_index]['ax'] = ax
        
        # Get data
        region = region_data['region']
        coords = region_data['coordinates']
        x, y, w, h = coords
        
        # Calculate total pixels
        total_pixels = w * h
        
        # Show progress dialog for large datasets
        progress_dialog = None
        if max_points == 0 and total_pixels > 50000:  # Show progress for large datasets
            progress_dialog = wx.ProgressDialog(
                "Generating Plot",
                "Processing pixel data...",
                maximum=100,
                parent=self.GetTopLevelParent(),
                style=wx.PD_AUTO_HIDE | wx.PD_APP_MODAL
            )
            progress_dialog.Pulse()
            wx.GetApp().Yield()
        
        # Create pixel data with indices
        pixels = []
        for row in range(h):
            for col in range(w):
                grayscale_value = region[row, col]
                pixels.append(grayscale_value)
            
            # Update progress for large datasets
            if progress_dialog and row % max(1, h // 20) == 0:  # Update every 5%
                progress = int((row / h) * 50)  # First 50% for data collection
                progress_dialog.Update(progress, f"Processing pixel data... {progress}%")
                wx.GetApp().Yield()
        
        # Apply max points limit if specified
        if max_points > 0 and len(pixels) > max_points:
            if progress_dialog:
                progress_dialog.Update(60, "Sampling data points...")
                wx.GetApp().Yield()
            # Sample pixels uniformly
            indices = np.linspace(0, len(pixels) - 1, max_points, dtype=int)
            pixels = [pixels[i] for i in indices]
        
        # Update progress
        if progress_dialog:
            progress_dialog.Update(80, "Generating plot...")
            wx.GetApp().Yield()
        
        # Create index array
        pixel_indices = np.arange(1, len(pixels) + 1)
        
        # Calculate statistics
        mean_value = region_data['mean']
        std_dev = region_data['std_dev']
        median_value = region_data['median']
        min_value = region_data['min']
        max_value = region_data['max']
        area = region_data['area']
        rect_name = region_data.get('name', f"Region {rect_index + 1}")
        
        # Create plot based on plot type
        plot_type = self.main_frame.plot_type if hasattr(self.main_frame, 'plot_type') else 'scatter'
        
        if plot_type == 'line':
            # Create line plot
            ax.plot(pixel_indices, pixels, linewidth=0.5, color='blue', alpha=0.7)
        else:
            # Create scatter plot (default)
            ax.scatter(pixel_indices, pixels, alpha=0.6, s=1, c='blue')
        
        # Add horizontal lines for statistics
        ax.axhline(mean_value, color='r', linestyle='dashed', linewidth=2, label=f'Mean: {mean_value:.1f}')
        ax.axhline(median_value, color='g', linestyle='dashed', linewidth=2, label=f'Median: {median_value:.1f}')
        
        # Add labels and title
        ax.set_xlabel('Pixel Index (Left-to-Right, Top-to-Bottom)')
        ax.set_ylabel('Grayscale Value (0-255)')
        title = (f'{rect_name} - Pixel Values\n'
                f'Area: {area} pixels, Points: {len(pixels)}\n'
                f'Mean: {mean_value:.1f}, Std: {std_dev:.1f}, Range: {min_value}-{max_value}')
        ax.set_title(title, fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        
        # Set axis limits
        ax.set_ylim(0, 255)
        if len(pixel_indices) > 0:
            ax.set_xlim(1, len(pixel_indices))
        
        # Update progress
        if progress_dialog:
            progress_dialog.Update(95, "Finalizing plot...")
            wx.GetApp().Yield()
        
        # Adjust layout
        figure.tight_layout()
        
        # Refresh canvas
        canvas.draw()
        
        # Close progress dialog
        if progress_dialog:
            progress_dialog.Update(100, "Complete!")
            wx.GetApp().Yield()
            progress_dialog.Destroy()

    def remove_plot(self, rect_index):
        """Remove plot for a specific rectangle"""
        if rect_index in self.plot_data:
            # Find the page index in notebook
            panel = self.plot_data[rect_index]['panel']
            for i in range(self.notebook.GetPageCount()):
                if self.notebook.GetPage(i) == panel:
                    self.notebook.DeletePage(i)
                    break
            
            # Clean up
            try:
                panel.Destroy()
            except:
                pass
            
            # Remove from plot data
            del self.plot_data[rect_index]

    def refresh_all_plots(self, plot_type):
        """Refresh all plots with new plot type"""
        for rect_index in list(self.plot_data.keys()):
            # Get region data from image panel
            if hasattr(self.main_frame, 'image_panel') and self.main_frame.image_panel:
                # Re-analyze the rectangle to refresh the plot
                self.main_frame.image_panel.analyze_rectangle(rect_index)

    def reindex_plots(self, deleted_index):
        """Reindex plots after a rectangle is deleted"""
        # Create new plot data with updated indices
        new_plot_data = {}
        
        # Get all current indices and sort them
        indices = sorted(self.plot_data.keys())
        
        for old_index in indices:
            if old_index < deleted_index:
                # Keep the same index
                new_index = old_index
            else:
                # Shift index down by 1
                new_index = old_index - 1
            
            # Move data to new index
            new_plot_data[new_index] = self.plot_data[old_index]
            
            # Update tab title
            panel = self.plot_data[old_index]['panel']
            for i in range(self.notebook.GetPageCount()):
                if self.notebook.GetPage(i) == panel:
                    self.notebook.SetPageText(i, f"Region {new_index + 1}")
                    break
        
        # Update plot data
        self.plot_data = new_plot_data

    def select_plot_tab(self, rect_index):
        """Select the tab for the given rectangle index"""
        if rect_index in self.plot_data:
            panel = self.plot_data[rect_index]['panel']
            for i in range(self.notebook.GetPageCount()):
                if self.notebook.GetPage(i) == panel:
                    self.notebook.SetSelection(i)
                    break

    def update_tab_title(self, rect_index, new_name):
        """Update the tab title for a specific rectangle"""
        if rect_index in self.plot_data:
            panel = self.plot_data[rect_index]['panel']
            for i in range(self.notebook.GetPageCount()):
                if self.notebook.GetPage(i) == panel:
                    self.notebook.SetPageText(i, new_name)
                    break

    def clear_all_plots(self):
        """Clear all plots"""
        # Remove all pages except the first one
        while self.notebook.GetPageCount() > 1:
            self.notebook.DeletePage(1)
        
        # Clean up plot data
        for rect_index in list(self.plot_data.keys()):
            try:
                self.plot_data[rect_index]['panel'].Destroy()
            except:
                pass
        
        self.plot_data = {}
        
        # Select the "No plots" page
        self.notebook.SetSelection(0)
