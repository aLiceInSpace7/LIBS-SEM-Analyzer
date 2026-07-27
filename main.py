import napari
from gui.widgets import create_main_control_panel
from analysis.layers import setup_layers
from gui.msg import show_msg
from qtpy.QtWidgets import QMessageBox


def main():
    viewer = napari.Viewer()
    viewer.title = "SEM Analyzer"
    
    # Setup
    setup_layers(viewer)
    control_widget = create_main_control_panel(viewer)
    viewer.window.add_dock_widget(control_widget, area='right', name="Controls")
    
    show_msg("SEM Analyzer", 
             "SEM Analyzer started successfully",
             "Click 'Load New Image' to begin.",
             QMessageBox.Icon.Information)
    
    # Launch napari
    napari.run()


if __name__ == "__main__":
    main()