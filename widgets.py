from qtpy.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel, QDoubleSpinBox
from fileio.loader import load_and_add_image
from gui.callbacks import run_roi_analysis, run_1d_profile, create_scanner, plot_fft_graph


def create_main_control_panel(viewer):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Load image button
    load_btn = QPushButton("Load New Image")
    load_btn.clicked.connect(lambda: load_and_add_image(viewer))
    layout.addWidget(load_btn)
    
    layout.addWidget(QLabel("<hr>"))
    
    # Scale settings widget
    layout.addWidget(QLabel("<b>Scale Settings</b>"))
    scale_spin = QDoubleSpinBox()
    scale_spin.setRange(0.1, 100.0)
    scale_spin.setValue(10.87)
    scale_spin.setSuffix(" nm/pixel")
    layout.addWidget(scale_spin)
    
    layout.addWidget(QLabel("<hr>"))
    layout.addWidget(QLabel("<b>Analysis Tools</b>"))
    
    # 2D-FFT graph button
    btn_fft = QPushButton("Show 2D-FFT Graph")
    btn_fft.clicked.connect(lambda: plot_fft_graph(viewer))
    layout.addWidget(btn_fft)

    # ROI analysis button
    btn_roi = QPushButton("Analyze Polygon ROI")
    btn_roi.clicked.connect(lambda: run_roi_analysis(viewer, scale_spin, results_label))
    layout.addWidget(btn_roi)
    
    # 1D profile button
    btn_profile = QPushButton("1D Intensity Profile")
    btn_profile.clicked.connect(lambda: run_1d_profile(viewer))
    layout.addWidget(btn_profile)

    # Intensity profile scanner button
    btn_scanner = QPushButton("Intensity Profile Scanner")
    btn_scanner.clicked.connect(lambda: create_scanner(viewer))
    layout.addWidget(btn_scanner)
    
    layout.addWidget(QLabel("<hr>"))
    
    # Global results label (shared)
    layout.addWidget(QLabel("<b>Results</b>"))
    global results_label
    results_label = QLabel("No analysis performed yet.")
    results_label.setWordWrap(True)
    layout.addWidget(results_label)
    
    return widget