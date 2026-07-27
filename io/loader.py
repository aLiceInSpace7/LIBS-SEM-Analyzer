from skimage import io
import numpy as np
from qtpy.QtWidgets import QMessageBox
from gui.msg import show_msg

def load_and_add_image(viewer):
    from qtpy.QtWidgets import QFileDialog
    path, _ = QFileDialog.getOpenFileName(None, "Select SEM/TEM Image", "", 
                                        "Images (*.tif *.tiff *.png *.jpg *.jpeg)")
    if not path:
        return
    
    try:
        # Load raw image with skimage
        img = io.imread(path, as_gray=True)
        raw_img = img
        if len(raw_img.shape) == 3:
            raw_img = np.mean(raw_img, axis=2).astype(np.float32)
        else:
            raw_img = raw_img.astype(np.float32)

        # Use SimpliPyTEM for image processing
        processed = None
        try:
            from SimpliPyTEM.Micrograph_class import Micrograph
            micro_raw = Micrograph(path)
            micro_gaussian = micro_raw.gaussian_filter()
            micro_gaussian.plot_histogram()
            micro_8bit = micro_gaussian.convert_to_8bit()
            micro = micro_8bit
            micro.write_image('output.png')
            micro_raw.write_image('raw.png')
            print("SimpliPyTEM processing succeeded")
            processed = io.imread('output.png', as_gray=True)
        except Exception as e:
            print(f"[DEBUG] SimpliPyTEM failed, using fallback: {e}")
            processed = raw_img.copy()

        # Preserve shapes layers
        roi_data = line_data = scan_data = None
        for layer in viewer.layers:
            if layer.name == 'ROIs':
                roi_data = list(layer.data)
            elif layer.name == 'Profile Line':
                line_data = list(layer.data)
            elif layer.name == 'Scan Line':
                scan_data = list(layer.data)

        # Remove old image layers
        for layer in list(viewer.layers):
            if layer._type_string == 'image':
                viewer.layers.remove(layer.name)

        # Add layers and reorder
        viewer.add_image(raw_img, name="Raw SEM", colormap='gray', visible=True)
        viewer.add_image(processed, name="Processed", colormap='gray', visible=True)
        viewer.layers.move(viewer.layers.index('Raw SEM'), 0)
        viewer.layers.move(viewer.layers.index('Processed'), 1)

        # Restore shapes if any
        if roi_data: viewer.layers['ROIs'].data = roi_data
        if line_data: viewer.layers['Profile Line'].data = line_data
        if scan_data: viewer.layers['Scan Line'].data = scan_data

        show_msg("Success", 
                 "Image loaded successfully", 
                 f"File: {path.split('/')[-1]}", 
                 QMessageBox.Icon.Information)

    except Exception as e:
        show_msg("Error", 
                 "Failed to load image", 
                 str(e), 
                 QMessageBox.Icon.Information)
        print(f"[DEBUG] Critical Error: {e}")
