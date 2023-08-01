"""Nurbs WB - Next Generation

Filename:
    pyob.py

Inspired from microelly work on freecad-nurbswb


Portions of code from microelly (c) 2016 - 2019.

Versions:
    v 0.1 - 2023 onekk

Licence:
    GNU Lesser General Public License (LGPL)

"""


import FreeCAD
import FreeCADGui

import PySide

import Part
import numpy as np


class NurbsFPO:
    """Basic definition."""

    def __init__(self, obj):
        """Docstring missing."""
        print(f"Initialising NurbsFPO {obj.Name}")
        obj.Proxy = self
        self.Object = obj
        obj.addProperty("App::PropertyBool", "_noExecute", "~aux")
        obj.addProperty("App::PropertyBool", "_debug", "~aux")
        obj.addProperty("App::PropertyBool", "_showaux", "~aux")

    def attach(self, vobj):
        """Docstring missing."""
        print("attached")
        self.Object = vobj.Object

    def claimChildren(self):
        """Docstring missing."""
        return self.Object.Group

    def __getstate__(self):
        """Docstring missing."""
        return None

    def __setstate__(self, state):
        """Docstring missing."""
        return None

    def showprops(self, obj, prop):
        """Docstring missing."""
        if prop.startswith("_show"):
            mode = 0 if getattr(obj, prop) else 2

            for pn in obj.PropertiesList:
                if (
                    obj.getGroupOfProperty(pn).replace(" ", "") == prop[5:]
                    and pn != prop
                ):
                    obj.setEditorMode(pn, mode)

                if (
                    obj.getGroupOfProperty(pn).startswith("~")
                    and obj.getGroupOfProperty(pn).replace(" ", "")[1:] == prop[5:]
                    and pn != prop
                ):
                    obj.setEditorMode(pn, mode)

    def myOnChanged(self, fp, prop):
        """Docstring missing."""
        pass

    def onChanged(self, fp, prop):
        """Docstring missing."""
        try:
            a = fp._noExecute
        except:
            return

        if not fp._noExecute:
            self.myOnChanged(fp, prop)

    def onBeforeChange(self, fp, prop):
        """Docstring missing."""
        pass

    def onDocumentRestored(self, fp):
        """Docstring missing."""
        print("Docu restored")

        for pn in fp.PropertiesList:
            if pn.startswith("_show"):
                self.onChanged(fp, pn)

        self.restored = True

    def myExecute(self, fp):
        """Docstring missing."""
        pass

    def execute(self, fp):
        """Docstring missing."""
        try:
            a = fp._noExecute
        except:
            return

        if not fp._noExecute:
            self.myExecute(fp)

    def run(self):
        """Docstring missing."""
        print("run test")


class VP_NurbsFPO:
    """Basic definition."""

    def __init__(self, obj, icon=None):
        """Docstring missing."""
        print(f"Initialising VP_NurbsFPO {obj}")
        obj.Proxy = self
        self.Object = obj.Object
        self.ViewObject = obj
        self.icon = icon
        if icon is None:
            icon = "../icons/BB.svg"
        if icon.startswith("/"):
            ic = self.icon
        else:
            ic = FreeCAD.ConfigGet("UserAppData") + "/Mod/" + icon

        obj.addProperty("App::PropertyString", "icon").icon = ic

    #   def onDelete(self, obj, subelements):
    #       return False

    def __getstate__(self):
        """Docstring missing."""
        return None

    def __setstate__(self, state):
        """Docstring missing."""
        return None

    def attach(self, vobj):
        """Docstring missing."""
        self.ViewObject = vobj
        self.Object = vobj.Object

    def getIcon(self):
        """Docstring missing."""
        return self.Object.ViewObject.icon

    def claimChildren(self):
        """Docstring missing."""
        s = self.Object
        rc = []
        for prop in s.PropertiesList:
            if s.getTypeIdOfProperty(prop) in ["App::PropertyLink"]:
                v = s.getPropertyByName(prop)
                if v is not None:
                    rc += [v]
            elif s.getTypeIdOfProperty(prop) in ["App::PropertyLinkList"]:
                v = s.getPropertyByName(prop)
                if len(v) != 0:
                    rc += v
        return rc

    def recompute(self):
        """Docstring missing."""
        obj = self.Object
        print(("Recompute ", obj.Label))
        obj.Proxy.myOnChanged(obj, "_recompute_")

    def setupContextMenu(self, obj, menu):
        """Docstring missing."""
        #       self.createDialog()

        action = menu.addAction("Recompute ...")
        action.triggered.connect(self.recompute)

    def setEdit(self, vobj, mode=0):
        """Docstring missing."""
        # self.createDialog()
        print("huhu")
        try:
            self.edit()
            # print "ha 2"
        except:
            pass

        # FreeCAD.ActiveDocument.recompute()
        # print "hah"
        # print vobj
        # FreeCAD.v=vobj
        return True

    def run_later(self):
        """Docstring missing."""
        self.ViewObject.show()

    # seems to superseed first definition
    '''
    def setEdit(self, vobj, mode=0):
        """Docstring missing."""
        # self.createDialog()
        PySide.QtCore.QTimer.singleShot(100, self.run_later)
        raise Exception("Exception-Hack to start Editor")
        # return False
        # return True
    '''

# proxies for python objects


def _Sketch(FeaturePython):
    """Docstring missing."""

    def __init__(self, obj):
        """Docstring missing."""
        print("_SKetch init")
        NurbsFPO.__init__(self, obj)
        obj.Proxy = self
        self.Type = self.__class__.__name__
        self.obj2 = obj
        print(f"_Sketch Label: {obj.Label}")


def _Sheet(NurbsFPO):
    """Docstring missing."""

    def __init__(self, obj):
        """Docstring missing."""
        NurbsFPO.__init__(self, obj)


def Sketch(name="MySketch"):
    """Create a SketchObjectPython."""
    #
    obj = FreeCAD.ActiveDocument.addObject("Sketcher::SketchObjectPython", name)
    obj.addProperty(
        "App::PropertyBool",
        "off",
        "Base",
    )
    _Sketch(obj)
    VP_NurbsFPO(obj.ViewObject, "../icons/sketchdriver.svg")
    return obj


def Spreadsheet(name="MySketch"):
    """Create a Spreadsheet."""
    obj = FreeCAD.ActiveDocument.addObject("Spreadsheet::Sheet", name)
    obj.addProperty(
        "App::PropertyBool",
        "off",
        "Base",
    )
    _Sheet(obj)
    return obj
