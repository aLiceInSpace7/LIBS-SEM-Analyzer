from qtpy.QtWidgets import QMessageBox

def show_msg(title, txt, info_txt=None, icon=None):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(txt)
    msg.setInformativeText(info_txt)
    msg.setIcon(icon)
    msg.exec()
