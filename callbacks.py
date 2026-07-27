import numpy as np
from skimage.draw import line
import matplotlib.pyplot as plt
from analysis.fft import analyze_fft
from gui.msg import show_msg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from qtpy.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QLabel, QSlider
from qtpy.QtCore import Qt
from scipy import fftpack


def plot_fft_graph(viewer):
    """Graph the 2D-FFT power spectrum of the processed image."""
    processed = viewer.layers['Processed'].data
    
    fft_img = fftpack.fft2(processed) # Compute the 2D-FFT
    fft_shift = fftpack.fftshift(fft_img) # Move the 0 frequency to centre
    power_spectrum = np.abs(fft_shift)**2 # Calculate power/intensity
    power_spectrum = np.log1p(power_spectrum) # Log scaling to improve graph appearance

    with plt.style.context('dark_background'):
        fig, ax = plt.subplots()
        ax.imshow(power_spectrum, cmap='inferno')
        ax.set_title("2D-FFT Power Spectrum")
        plt.show()

    return


def run_roi_analysis(viewer, scale_spin, results_label):
    try:
        shapes = viewer.layers['ROIs']
    
        if len(shapes.data) == 0:
            show_msg("Warning", 
                    "Please draw a polygon on ROIs layer first",
                    None,
                    QMessageBox.Icon.Warning)
            return
        
        shape = shapes.data[-1]
        min_y, min_x = np.floor(shape.min(axis=0)).astype(int)
        max_y, max_x = np.ceil(shape.max(axis=0)).astype(int)
        roi_width = max_x - min_x
        roi_height = max_y - min_y
        roi_area = roi_width * roi_height
        
        processed = viewer.layers['Processed'].data
        roi_img = processed[min_y:max_y, min_x:max_x]
        
        period, orient = analyze_fft(roi_img, scale_nm_per_px=scale_spin.value())
        
        text = f"""<b>ROI Analysis</b><br>
        Period: <b>{period:.1f} nm</b><br>
        Orientation: <b>{orient:.1f}°</b><br>"""
        results_label.setText(text)
        
        detailed_text = f"""
                        ANALYSIS RESULTS
                        =====================
                        
                        Period:          {period:.2f} nm
                        Orientation:     {orient:.2f}°
                        
                        ROI:
                        • Width:         {roi_width} pixels
                        • Height:        {roi_height} pixels
                        • Area:          {roi_area:,} pixels²
                        • Scale used:    {scale_spin.value()} nm/pixel
                        """

        show_msg( "Analysis Results",
                 detailed_text,
                 None,
                QMessageBox.Icon.Information)

    except Exception as e:
        show_msg("Analysis Error", 
                 "Failed to analyze ROI",
                 str(e),
                 QMessageBox.Icon.Critical)
        print(f"Error in ROI analysis: {e}")


def run_1d_profile(viewer):
    try:
        lines = viewer.layers['Profile Line']
        
        if len(lines.data) == 0:
            show_msg("Warning", 
                    "Please draw a line on the 'Profile Line' layer first",
                    None,
                    QMessageBox.Icon.Warning)
            return
        
        line_coords = lines.data[-1]
        r0, c0 = int(line_coords[0][0]), int(line_coords[0][1])
        r1, c1 = int(line_coords[1][0]), int(line_coords[1][1])
        
        rr, cc = line(r0, c0, r1, c1)
        profile = viewer.layers['Processed'].data[rr, cc]
        
        # Plot
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(profile, 'r-', linewidth=2)
        ax.set_title("1D Intensity Profile")
        ax.set_xlabel("Position along line (px)")
        ax.set_ylabel("Intensity (a.u.)")
        ax.grid(True)
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        show_msg("Analysis Error", 
                 "Failed to analyze line profile",
                 str(e),
                 QMessageBox.Icon.Critical)
        print(f"Error in 1D profile: {e}")


def create_scanner(viewer):
    if 'Processed' not in [layer.name for layer in viewer.layers]:
        show_msg("Warning",
                 "Please load an image first",
                 None,
                 QMessageBox.Icon.Warning)
        return
    
    processed = viewer.layers['Processed'].data
    height, width = processed.shape
    
    # Determine plot scale
    g_min = processed.min()
    g_max = processed.max()
    y_padding = (g_max - g_min) * 0.05

    # Make scan layer
    if 'Scan Line' not in viewer.layers:
        scan_layer = viewer.add_shapes(name='Scan Line', shape_type='line', edge_color='red', edge_width=2, opacity=0.7, visible=True)
    else:
        scan_layer = viewer.layers['Scan Line']
        scan_layer.visible = True
        scan_layer.opacity = 0.85
        scan_layer.edge_width = 3.5
    try:
        idx = viewer.layers.index('Scan Line')
        viewer.layers.move(idx, -1)
    except: pass

    # Make scan widget
    scanner_widget = QWidget()
    layout = QVBoxLayout(scanner_widget)
    layout.addWidget(QLabel("<b>Intensity Profile Scanner</b>"))

    # Angle control
    layout.addWidget(QLabel("Angle (°):"))
    angle_slider = QSlider(Qt.Horizontal)
    angle_slider.setRange(0, 180)
    angle_slider.setValue(0)
    layout.addWidget(angle_slider)
    angle_label = QLabel("0°")
    layout.addWidget(angle_label)
    
    # Position control (perp to angle)
    layout.addWidget(QLabel("Position:"))
    pos_slider = QSlider(Qt.Horizontal)
    pos_slider.setRange(0, 100)  # %
    pos_slider.setValue(50)
    layout.addWidget(pos_slider)
    pos_label = QLabel("Center")
    layout.addWidget(pos_label)
    
    # Plot
    fig, ax = plt.subplots(figsize=(7, 4))
    canvas = FigureCanvas(fig)
    line_plot, = ax.plot([], [], 'b-', linewidth=1)
    ax.set_title("Intensity Profile")
    ax.set_xlabel("Position along scan line (pixels)")
    ax.set_ylabel("Intensity")
    ax.grid(True)
    ax.set_ylim(g_min - y_padding, g_max + y_padding)
    layout.addWidget(canvas)

    #  Update the scanner line
    def update_scan(ang, pos):
        if 'Processed' not in viewer.layers:
            return
        
        img = viewer.layers['Processed'].data
        h, w = img.shape

        centre_x, centre_y = w/2, h/2
        length = max(h, w) * 1.2
        rad = np.radians(ang)

        dx = length/2 * np.cos(rad)
        dy = length/2 * np.sin(rad)

        perp_rad = rad + np.pi/2
        offset = (pos - 50) / 50 * min(h, w) * 0.4
        cx = centre_x + offset * np.cos(perp_rad)
        cy = centre_y + offset * np.sin(perp_rad)

        x1, y1 = cx - dx, cy - dy
        x2, y2 = cx + dx, cy + dy

        scan_layer.data = [[(y1, x1), (y2, x2)]]

        r0, c0 = int(y1), int(x1)
        r1, c1 = int(y2), int(x2)
        rr, cc = line(r0, c0, r1, c1)
        rr = np.clip(rr, 0, h-1)
        cc = np.clip(cc, 0, w-1)
        profile = img[rr, cc]

        line_plot.set_data(range(len(profile)), profile)
        ax.relim()
        ax.autoscale_view()
        canvas.draw_idle()

        angle_label.setText(f"{ang}°")
        pos_label.setText(f"{pos}%")
    
    # Connect slider to the scan line
    def on_change(value):
        update_scan(angle_slider.value(), pos_slider.value())
    angle_slider.valueChanged.connect(on_change)
    pos_slider.valueChanged.connect(on_change)
    
    # Initial update
    update_scan(0, 50)
    
    # Add scanner to napari
    viewer.window.add_dock_widget(scanner_widget, area='left', name="Intensity Profile Scanner", tabify=True)
    
    return scanner_widget

# def create_scanner(viewer):
#     if 'Processed' not in [layer.name for layer in viewer.layers]:
#         show_msg("Warning",
#                  "Please load an image first",
#                  None,
#                  QMessageBox.Icon.Warning)
#         return
    
#     processed = viewer.layers['Processed'].data
#     height, width = processed.shape
    
#     # Determine plot scale
#     g_min = processed.min()
#     g_max = processed.max()
#     y_padding = (g_max - g_min) * 0.05

#     # Create scanner widget
#     scanner_widget = QWidget()
#     layout = QVBoxLayout(scanner_widget)
    
#     layout.addWidget(QLabel("<b>Intensity Profile Scanner</b>"))

#     # Angle control
#     layout.addWidget(QLabel("Angle (°):"))
#     angle_slider = QSlider(Qt.Horizontal)
#     angle_slider.setRange(0, 180)
#     angle_slider.setValue(0)
#     layout.addWidget(angle_slider)
#     angle_label = QLabel("0°")
#     layout.addWidget(angle_label)
    
#     # Position control (perpendicular to angle)
#     layout.addWidget(QLabel("Position:"))
#     pos_slider = QSlider(Qt.Horizontal)
#     pos_slider.setRange(0, 100) # Percent
#     pos_slider.setValue(50)
#     layout.addWidget(pos_slider)
#     pos_label = QLabel("Center")
#     layout.addWidget(pos_label)
    
#     # Live plot (we'll keep one figure open)
#     fig, ax = plt.subplots(figsize=(7, 4))
#     canvas = FigureCanvas(fig)
#     line_plot, = ax.plot([], [], 'r-', linewidth=2)
#     ax.set_title("Intensity Profile")
#     ax.set_xlabel("Position along scan line (pixels)")
#     ax.set_ylabel("Intensity")
#     ax.grid(True)
#     ax.set_ylim(g_min - y_padding, g_max + y_padding)
#     layout.addWidget(canvas)
        
#     if 'Scan Line' not in viewer.layers:
#         scan_layer = viewer.add_shapes(name='Scan Line', shape_type='line', edge_color='red', edge_width=2, opacity=0.7)
#     else:
#         scan_layer = viewer.layers['Scan Line']

#     def update_scan(ang, pos):
#         if 'Processed' not in viewer.layers:
#             return
        
#         img = viewer.layers['Processed'].data
#         h, w = img.shape

#         centre_x, centre_y = w/2, h/2
#         length = max(h, w) * 1.2
#         rad = np.radians(ang)

#         dx = length/2 * np.cos(rad)
#         dy = length/2 * np.sin(rad)

#         perp_rad = rad + np.pi/2
#         offset = (pos - 50) / 50 * min(h, w) * 0.4
#         cx = centre_x + offset * np.cos(perp_rad)
#         cy = centre_y + offset * np.sin(perp_rad)

#         x1, y1 = cx - dx, cy - dy
#         x2, y2 = cx + dx, cy + dy

#         scan_layer.data = [[(y1, x1), (y2, x2)]]

#         r0, c0 = int(y1), int(x1)
#         r1, c1 = int(y2), int(x2)
#         rr, cc = line(r0, c0, r1, c1)
#         rr = np.clip(rr, 0, h-1)
#         cc = np.clip(cc, 0, w-1)
#         profile = img[rr, cc]

#         line_plot.set_data(range(len(profile)), profile)
#         ax.relim()
#         ax.autoscale_view()
#         canvas.draw_idle()

#         angle_label.setText(f"{ang}°")
#         pos_label.setText(f"{pos}%")

    
#     # Connect slider
#     def on_change(value):
#         update_scan(angle_slider.value(), pos_slider.value())
    
#     angle_slider.valueChanged.connect(on_change)
#     pos_slider.valueChanged.connect(on_change)
    
#     # Initial update
#     update_scan(0, 50)
    
#     # Add scanner to napari
#     viewer.window.add_dock_widget(scanner_widget, area='bottom', name="Intensity Profile Scanner")
    
#     return scanner_widget

