"""Ui dialog.

file: ui_dialog.py

Notes:
    works in new wb scheme

Author: Carlo Dormeletti
Copyright: 2023
Licence: LGPL
"""

__ver__ = "20230724"

import os  # noqa
import sys  # noqa


from datetime import datetime  # noqa
from math import pi, sin, cos # noqa

import FreeCAD
import FreeCADGui
from FreeCAD import Placement, Rotation, Vector # noqa
import Part # noqa


# Utilize PySide2 "newer" imports, no need to be compatible with PyQt4 anymore.
from PySide2 import QtGui, QtCore, QtWidgets  # noqa
from PySide2.QtWidgets import (  # noqa
    QCheckBox, QComboBox, QColorDialog, QDesktopWidget, QDoubleSpinBox,
    QGroupBox, QFrame, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton,
    QSpinBox, QTabWidget, QTextEdit, QHBoxLayout, QGridLayout, QVBoxLayout)

from PySide2.QtCore import Slot, QObject, Qt  # noqa

from functools import partial  # noqa


# Set dbg_test to True during tests if not an error during main_dia creation
# prevent the run of the new istance forcing to restart FC everytime
# dbg_test = True
dbg_test = False

dbg_ui = 1  # integer > 0 if you want some debug

# Macros #
MSG = FreeCAD.Console.PrintMessage

mw = FreeCADGui.getMainWindow()

# Interface font sizes
sz_ch_ap = 14
sz_ch_tx = 16

# Color Names for fields
cc_names = ["Red", "Green", "Blue"]

# Validated field colors
fld_clr_bad = '#FFB6C1'
fld_clr_blu = '#000000'
fld_clr_dsp = '#FFFFE0'
fld_clr_good = '#FAFAD2'
fld_clr_gre = '#000000'
fld_clr_red = '#000000'

md_fld_v1min = 0.0
md_fld_v1max = 1.0e12
md_fld_v2min = -1.0e12
md_fld_v2max = 1.0e12

md_fld_sfmt = {'std': "-03.3g", 'dbl': "-03.3g", 'int': "-d"}

style_ap = f"font-size: {sz_ch_ap}px"
style_bl = f"{style_ap}; color: {fld_clr_blu}"
style_ds = f"{style_ap}; background-color: {fld_clr_dsp}"
style_gl = f"{style_ap}; color: {fld_clr_gre}"
style_rl = f"{style_ap}; color: {fld_clr_red}"
style_tx = f"font-size: {sz_ch_tx}px"
# hold colors for colorname labels
style_cf = (style_rl, style_gl, style_bl)

precision = 3

un_len = 'mm'
units_len = ("mm")

# --- copied from miki

def getMainWindow():
    """Return the main window."""
    toplevel = QtGui.qApp.topLevelWidgets()

    for i in toplevel:
        if i.metaObject().className() == "Gui::MainWindow":
            return i

    raise Exception("No main window found")


def getComboView(mw):
    """Return Combo View widget."""
    dw = mw.findChildren(QtGui.QDockWidget)

    for i in dw:
        if str(i.objectName()) == "Combo View":
            return i.findChild(QtGui.QTabWidget)

        elif str(i.objectName()) == "Python Console":
            return i.findChild(QtGui.QTabWidget)

    raise Exception("No tab widget found")


def ComboViewShowWidget(widget, tabMode=False):
    """Create a tab widget inside the combo view."""
    #
    if tabMode is False:
        widget.show()
        return widget

    mw = getMainWindow()
    tab = getComboView(mw)
    c = tab.count()

    # clear the combo  window
    for i in range(c - 1, 1, -1):
        tab.removeTab(i)

    # start the requested tab
    tab.addTab(widget, widget.tabname)
    tab.setCurrentIndex(2)

    widget.tab = tab
    return widget

# -----------------


def ui_create_chb(f_name, d_txt, c_ttp, c_state):
    """Create a CheckBox."""
    chb = QCheckBox()
    chb.setChecked(c_state)
    chb.setStyleSheet(style_ap)
    chb.setText(d_txt)
    chb.setToolTip(c_ttp)
    chb.setObjectName(f_name)

    return chb


def ui_create_cbo(f_name, c_items):
    """Create a ComboBox."""
    cbo = QComboBox()
    cbo.addItems(c_items)
    cbo.InsertPolicy(QComboBox.NoInsert)
    cbo.setObjectName(f_name)

    return cbo


def ui_create_ifld(
        wid, f_id, f_name, f_unit, min_val, max_val, pre_val, ed_fld_p, e_ttp):
    """Create and input field."""
    f_align = Qt.AlignRight | Qt.AlignVCenter

    # edit field
    ed_fld = QLineEdit()
    ed_fld.setStyleSheet(
        "background-color: " + fld_clr_good)
    ed_fld.setAlignment(f_align)

    if f_id == "ifi":
        ed_fld_v = QtGui.QIntValidator()
        ed_fld_v.setRange(int(min_val), int(max_val))

    elif f_id == "ifd":
        ed_fld_v = QtGui.QDoubleValidator()
        ed_fld_v.setRange(float(min_val), float(max_val), int(ed_fld_p))

    ed_fld.setValidator(ed_fld_v)
    ed_fld.insert(f"{pre_val}")

    ed_fld.setObjectName(f_name)
    ed_fld.setToolTip(e_ttp)

    return ed_fld


def ui_create_lbl(
        wid, f_id, f_desc, f_name, l_ttp, row, col, create=True, role='lb'):
    """Create label for interface."""
    label = QLabel()
    label.setWordWrap(False)
    label.setStyleSheet(style_ap)
    label.setText(f_desc)
    label.setObjectName(f_name)

    if f_id in ("cbo", "mds"):
        # attach tooltip to label
        label.setToolTip(l_ttp)

    if role == 'ds':
        label.setStyleSheet("background-color: " + fld_clr_dsp)

    if create:
        wid.addWidget(label, row, col)
        return label
    else:
        return label


# Field definition for create_ui

# ("txt_ptname", ("pt", "Name", "Object", 1, False), "Object Name")

# ("btn_gsl", ("an", "Get Selection", "", "", "a", 0, 0))

# ("ifd_ptwi", ("pt", "Patch Width", "len", 0.0, 30.0, 2.0, 0.0)

# ("cbo_len", ("up", "Length", units_len), "Units length"),


def create_hui(parent, start_row, start_col, if_fields):
    """Create Ui from a definition tuple."""
    # must remain here to make globals() works
    if dbg_ui > 0:
        print(f'chui - pc: {parent.children()}')
        print(f'chui - if: {if_fields}')

    row = start_row
    col = start_col

    for field in if_fields:
        if dbg_ui > 0:
            print(f"-- CR: {field}")

        f_name = field[0]
        f_id = f_name[:3]
        f_desc = field[1][1]
        f_ref = f_name[4:]

        if dbg_ui > 0:
            print(f'-- f_ref: {f_ref}')

        wid = parent.findChild(QObject, field[1][0])

        if f_id not in ("mcb", "mlb", "btn", "chb"):
            lbl = ui_create_lbl(
                wid, f_id, f_desc, f"l_{f_name}", field[2], row, col)

            parent.ids[f_ref] = lbl
            col += 1

        if f_id == "chb":
            chb = ui_create_chb(f_name, f_desc, field[2], field[1][2])
            wid.addWidget(chb, row, col)

            parent.ids[f_ref] = chb

            col += 1

        elif f_id == "cbo":
            cbo = ui_create_cbo(f_name, field[1][2])
            wid.addWidget(cbo, row, col)

            parent.ids[f_ref] = cbo

            col += 1


    if f_id != "btn":
        # col += 1
        pass
    else:
        # buttons are positioned using field values
        pass

    return row


def create_vui(parent, start_row, if_fields):
    """Create Ui from a definition tuple."""
    # must remain here to make globals() works
    if dbg_ui > 0:
        print(parent.children())
        print(if_fields)

    row = start_row

    for field in if_fields:
        if dbg_ui > 0:
            print(f"CR: {field}")

        f_name = field[0]
        f_id = f_name[:3]
        f_desc = field[1][1]

        wid = parent.findChild(QObject, field[1][0])

        if dbg_ui > 0:
            print(f"Widget = {wid}")
            print(f"Name = {wid.objectName()}")

        if f_id not in ("mcb", "mlb", "btn", "chb"):
            ui_create_lbl(
                wid, f_id, f_desc, f"l_{f_name}", field[2], row, 0)

        if f_id in ("ifi", "ifd"):
            min_val, max_val = get_limits(field[1][3], field[1][4])
            if len(field[1]) == 7:
                fld_p = field[1][6]
            else:
                fld_p = precision

            ed_fld = ui_create_ifld(
                wid, f_id, f_name, field[1][2],
                min_val, max_val, field[1][5], fld_p, field[2],
                row, 0)

            wid.addWidget(ed_fld, row, col)

            # measure unit
            f_unit = get_unit(unit)
            ed_unit = ui_create_lbl(
                wid, "", f_unit, f"m_{f_name}", "", row, col + 2)

            # range
            ed_range = ui_create_lbl(
                wid, "", f"{min_val} - {max_val}", f"r_{f_name}", "", row, col + 1)

        elif f_id == "chb":
            chb = ui_create_chb(f_name, field[2], field[1][2])
            wid.addWidget(chb, row, 1)

        elif f_id == "txt":
            itxt = QLineEdit()
            itxt.setText(field[1][2])
            itxt.setReadOnly(field[1][4])

            itxt.setStyleSheet(style_ds)
            itxt.setToolTip(field[2])
            itxt.setObjectName(f_name)

            wid.addWidget(itxt, row, 1, 1, field[1][3])

        elif f_id == "dsf":
            d_val = field[1][2]
            d_type = field[1][4]
            ca_tp = field[1][7]  # 0: left 1: right

            f_width = 0

            if d_type in ("fl", "sc"):
                f_align = Qt.AlignRight | Qt.AlignVCenter
                f_width = field[1][5]

                if d_type == "sc":
                    d_val = sc_format(d_val)

            elif d_type == "vl":
                f_align = Qt.AlignRight | Qt.AlignVCenter
            else:
                f_align = Qt.AlignLeft | Qt.AlignVCenter

            txtf = ui_create_lbl(
                wid, f_id, d_val, f_name, field[2],
                0, 0, False, 'ds')
            txtf.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
            txtf.setAlignment(f_align)

            if f_width != 0:
                txtf.setFixedWidth(f_width)

            if ca_tp == 0:
                cell_align = Qt.AlignLeft
            else:
                cell_align = Qt.AlignRight

            wid.addWidget(txtf, row, 1, 1, 1, cell_align)

        elif f_id == "dmf":
            dm_val = field[1][2]
            dm_num = field[1][3]
            d_type = field[1][4]
            ca_tp = field[1][7]  # 0: left 1: right

            for mf_idx in range(0, dm_num):
                f_width = 0

                if d_type in ("fl", "sc"):
                    f_align = Qt.AlignRight | Qt.AlignVCenter
                    f_width = field[1][5]
                    if d_type == "sc":
                        d_val = sc_format(dm_val[mf_idx])

                elif d_type == "vl":
                    f_align = Qt.AlignRight | Qt.AlignVCenter
                else:
                    f_align = Qt.AlignLeft | Qt.AlignVCenter

                txtf = ui_create_lbl(
                    wid, f_id, d_val, f"{f_name}_{mf_idx}", field[2],
                    0, 0, False, 'ds')

                txtf.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
                txtf.setAlignment(f_align)

                if f_width != 0:
                    txtf.setFixedWidth(f_width)

                if ca_tp == 0:
                    cell_align = Qt.AlignLeft
                else:
                    cell_align = Qt.AlignRight

                wid.addWidget(txtf, row, 1 + mf_idx, 1, 1, cell_align)

        elif f_id == "cbo":
            cbo = ui_create_cbo(f_name, field[1][2])
            wid.addWidget(cbo, row, 1)

            parent.ids[f_ref] = cbo

        elif f_id == "mcb":
            mcb = QtWidgets.QButtonGroup(parent)
            mcb.setExclusive(True)
            mcb.setObjectName(f_name)

            b_lay = QHBoxLayout()

            for idx, mfld in enumerate(field[1][2]):
                mf_name = f"{f_name}_{idx}"
                chb = QCheckBox(field[1][2][idx])
                chb.setObjectName(mf_name)
                chb.setChecked(field[1][3][idx])
                chb.setStyleSheet(style_ap)

                mcb.addButton(chb)
                mcb.setId(chb, idx)
                b_lay.addWidget(chb)

            wid.addLayout(b_lay, row, 0, 1, 3)

        elif f_id == "mlb":
            for cnt, x in enumerate(field[1][1]):
                # print(f"mlb: {cnt} > {x}")
                sf_lbl = ui_create_lbl(
                    wid, f_id, x, f"l_{f_name}_{cnt}", "", 0, 0, False)

                wid.addWidget(sf_lbl, row, cnt + 1, 1, 1, Qt.AlignCenter)

        elif f_id == "mds":
            print("mds")
            min_val, max_val = get_limits(field[1][5], field[1][6])
            pre_val = float(field[1][7])
            d_typ = field[1][4]
            f_align = Qt.AlignRight | Qt.AlignVCenter

            for cnt in range(0, field[1][3]):
                ifld_name = f"{f_name}_{cnt}"
                ed_fld = QLineEdit()
                ed_fld.setStyleSheet(
                    "background-color: " + fld_clr_good)
                ed_fld.setAlignment(f_align)
                ed_fld.setObjectName(ifld_name)

                if d_typ == "dbl":
                    ed_fld_v = QtGui.QDoubleValidator()
                    ed_fld_v.setRange(min_val, max_val, field[1][8])
                else:
                    d_typ = "int"
                    ed_fld_v = QtGui.QIntValidator()
                    ed_fld_v.setRange(min_val, max_val)

                tv_min = f"{min_val:{md_fld_sfmt[d_typ]}}"
                tv_max = f"{max_val:{md_fld_sfmt[d_typ]}}"

                ed_fld.setValidator(ed_fld_v)
                ed_fld.insert(f"{pre_val:{md_fld_sfmt[d_typ]}}")
                ed_fld.textChanged.connect(
                    partial(onLEV_ch, parent, ifld_name))
                # set tooltip
                desc_str = f"Min value = {tv_min} \nMax value = {tv_max}"
                ed_fld.setToolTip(desc_str)

                wid.addWidget(ed_fld, row, cnt + 1)

        elif f_id == "col":
            # color
            cnt = QFrame()
            cnt.setObjectName("color_show")
            cnt_lay = QGridLayout()

            cnt_lay.addWidget(
                ColorFrame(field[1][2], f"{f_name}_cfm"), 0, 2, 3, 1)

            for c_idx, mat_cc in enumerate(field[1][2]):
                ed_val = int(mat_cc)  # must be integer
                c_lab = QLabel()
                c_lab.setText(cc_names[c_idx])
                c_lab.setStyleSheet(style_cf[c_idx])
                c_lab.setFixedWidth(50)

                c_val = QLabel()
                c_val.setText(str(ed_val))
                c_val.setStyleSheet(style_ds)
                c_val.setFixedWidth(fl_lr1 * 2)  # roughly 50px
                cnt_lay.addWidget(c_lab, c_idx, 0)
                cnt_lay.addWidget(c_val, c_idx, 1)

            cnt_lay.addWidget(
                ColorFrame(field[1][2], f"{f_name}_cfm"), 0, 2, 3, 1)

            cnt.setLayout(cnt_lay)

            # wid.addLayout(cnt_lay, row, 1, 1, 1)
            wid.addWidget(cnt, row, 1, 1, field[1][3])

        elif f_id == "cpk":
            # color picker
            csb_wid, cnt = ui_create_color_picker(
                f_name, field[1][2], field[2])
            wid.addWidget(cnt, row, 1, 1, field[1][3])

            # Apply actions here after widgets are created
            for c_sb in csb_wid:
                c_sb.valueChanged.connect(partial(set_co_frm, f_name))

        elif f_id == "btn":
            # print("button detected")
            b_pos = field[1][4]
            b_row = field[1][5]
            b_col = field[1][6]

            Btn_cif = QPushButton(field[1][1])

            if field[1][2] != "":
                Btn_cif.clicked.connect(
                    getattr(globals()[field[1][2]], field[1][3]))

            Btn_cif.setAutoDefault(False)

            if b_pos == "a":
                pass
            elif b_pos == "p":
                # use the parent row pos
                b_row = row
                # row is not advanced automatically due to final
                # condition
                row += 1

            wid.addWidget(Btn_cif, b_row, b_col)

        wid.setRowMinimumHeight(row, 25)
        wid.setRowStretch(row, 1)

        if f_id != "btn":
            row += 1
        else:
            # buttons are positioned using field values
            pass

    return row


def get_limits(min_val, max_val):
    """Return float limits from string definitions."""
    if min_val == "v1min":
        rmin = md_fld_v1min
    elif min_val == "v2min":
        rmin = md_fld_v2min
    else:
        rmin = 0.0

    if max_val == "v1max":
        rmax = md_fld_v1max
    elif max_val == "v2max":
        rmax = md_fld_v2max
    else:
        rmax = 1e+16

    return rmin, rmax


def get_unit(unit_t):
    """Get units from defined variables."""
    if unit_t == "len":
        f_unit = un_len
    else:
        f_unit = ""

    return f_unit


def sc_format(f_val, fmt_t='std'):
    """Return a floating number as scientific notation if needed."""
    return f"{f_val:{md_fld_sfmt[fmt_t]}}"


def ui_create_color_picker(f_name, color, ttp):
    """Create color picker for interface."""
    cnt = QFrame()
    cnt.setObjectName(f"{f_name}_frm")
    cf_name = f"{f_name}_cfm"
    cnt_lay = QGridLayout()

    cnt_lay.addWidget(
        ColorFrame(color, cf_name), 0, 2, 3, 1)

    spcn = ("r", "g", "b")
    csb_wid = []

    for c_idx, mat_cc in enumerate(color):
        c_lab = QLabel()
        c_lab.setText(cc_names[c_idx])
        c_lab.setStyleSheet(style_ap)
        c_lab.setFixedWidth(50)

        ed_fld = QSpinBox()
        ed_fld.setStyleSheet(style_ap)
        ed_fld.setFixedWidth(50)

        csb_name = f"{f_name}_cl_{spcn[c_idx]}"
        ed_fld.setObjectName(csb_name)
        ed_fld.setRange(0, 255)
        ed_fld.setSingleStep(1)
        ed_fld.setValue(color[c_idx])
        ed_fld.setToolTip(ttp)

        cnt_lay.addWidget(c_lab, c_idx, 0)
        cnt_lay.addWidget(ed_fld, c_idx, 1)
        csb_wid.append(ed_fld)

    cnt.setLayout(cnt_lay)

    return csb_wid, cnt



def onLEV_ch(parent, ifld_name, value):
    """Change edit color if field is not valid."""
    wid = parent.findChild(QLineEdit, ifld_name)

    if wid.hasAcceptableInput():
        wid.setStyleSheet("background-color: " + fld_clr_good)
    else:
        wid.setStyleSheet("background-color: " + fld_clr_bad)


class ColorFrame(QFrame):
    """Create a Frame of specified color."""

    def __init__(self, color, obj_name, parent=None):
        """Initialize thing."""
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        r, g, b = color
        # print(r, g, b)
        self._bgcolor = QtGui.QColor(r, g, b)
        # print(self._bgcolor.isValid())
        self.setObjectName(obj_name)
        self.resize(50, 50)

    def set_color(self, color):
        """Set color for the frame."""
        r, g, b = color
        self._bgcolor = QtGui.QColor(r, g, b)
        self.repaint()

    def paintEvent(self, event):
        """Subclass PaintEvent."""
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), self._bgcolor)
        super().paintEvent(event)


class main_dialog(QtWidgets.QDialog):
    """Create Main dialog."""

    def __init__(self, parent=mw, conf_dict=None):
        """Init class."""
        # Using the Tool flag will keep widget on top of parent while
        # not locking operation
        super().__init__(parent, Qt.Tool)
        # So widget object is deleted when closed
        # not just hidden (memory friendly)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # So font is propagated from parent to self
        # (needed for windowed widgets)
        self.setAttribute(Qt.WA_WindowPropagation, True)
        self.setObjectName("MainDia")

        if conf_dict is not None:
            self.codi = conf_dict
        else:
            self.codi = {}

        self.ids = {}
        self.app = None

        self.initUI()


    def initUI(self):
        """Specifically handles the UI initialization."""
        # set window dimensions
        sc_wid = QDesktopWidget().screenGeometry().width()
        sc_hei = QDesktopWidget().screenGeometry().height()
        # get dimensions for available space on screen
        av_wid = QDesktopWidget().availableGeometry().width()
        av_hei = QDesktopWidget().availableGeometry().height()
        self.w_wid = av_wid * 0.33
        self.w_hei = av_hei * 0.60
        x_loc = (sc_wid - self.w_wid) * 0.5
        y_loc = (sc_hei - self.w_hei) * 0.5

        # define window        xLoc,yLoc,xDim,yDim
        self.setGeometry(x_loc, y_loc, self.w_wid, self.w_hei)

        self.setWindowTitle(self.codi['title'])

        self.lay = QVBoxLayout(self)

        if self.codi['ui_type'] == 'tabs':
            self.tabw = QTabWidget(self)

            for tab_o in self.codi['tabs']:
                tab = QtWidgets.QWidget()
                tab.setObjectName('t_' + tab_o[1])
                lay = QGridLayout(tab)
                lay.setObjectName(tab_o[1])
                self.tabw.addTab(tab, tab_o[0])

            # Text field for the Log windows
            self.log_win = QTextEdit()
            self.log_win.setStyleSheet(style_tx)
            self.log_win.setReadOnly(True)
            self.log_win.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            # print(self.tabw.children())

            wid = self.tabw.findChild(QObject, "lg")
            wid.addWidget(self.log_win, 0, 0)

            self.lay.addWidget(self.tabw)

        # OK/Cancel Buttons
        # Buttons are defined explicitly to permit the check if "OK"
        # is clicked with mouse to avoid strange interface behaviour

        button_box = QtWidgets.QDialogButtonBox(Qt.Horizontal)

        self.dia_ok_btn = button_box.addButton(QtWidgets.QDialogButtonBox.Ok)

        button_box.addButton(QtWidgets.QDialogButtonBox.Cancel)

        self.lay.addWidget(button_box)

        self.setLayout(self.lay)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)



    def accept(self):
        """Subclass subclasses the one of QDialog."""
        # Prevent the close action if the OK Button is not pressed
        # using mouse click
        if not self.dia_ok_btn.underMouse():
            return

        # Possible action when closing should be put here

        super().accept()

    def reject(self):
        """Subclass the one of QDialog."""
        MSG('Good bye\n')
        super().accept()

    def hideEvent(self, event):
        """Subclass the one of QDialog."""
        super().hideEvent(event)

    def closeEvent(self, event):
        """Redefine action of the closing cross."""
        # Ignore event if cross is clicked
        event.ignore()


    def populateUI(self):
        """Populate UI."""
        # Define most of the real interface here
        # This flag will prevent to run methods when buttons are created.
        ie_flg = False

        last_row = 0

        for field in self.codi['if_def']:
            print(f'PopulateUI: {field}')

            if field[0][:2] == 'hr':
                # Horizontal layout
                ret_row = create_hui(self, last_row, 0, field[1])
                last_row = ret_row + 1

        # Set the initialize end flag to permit the work of buttons
        ie_flg = True

    # Actions for Buttons

    # Comboboxes Actions

# ---  Actions



def nurbs_dialog(app, layout):
    """Create nurbs dialog."""
    #
    dialog = main_dialog(app, layout)
    dialog.show()

    return dialog


if __name__ == "__main__":
    # This will be called when file is "executed"
    # but not if imported as module
    main_dia = nurbs_dialog(None, None)
    main_dia.show()
