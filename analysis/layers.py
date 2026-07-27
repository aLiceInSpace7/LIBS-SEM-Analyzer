def setup_layers(viewer):

    roi_layer = viewer.add_shapes(name='ROIs', shape_type='polygon', edge_color='yellow', edge_width=3, opacity=0.8, visible=True)
    
    line_layer = viewer.add_shapes(name='Profile Line', shape_type='line', edge_color='cyan', edge_width=2, opacity=0.9, visible=True)
