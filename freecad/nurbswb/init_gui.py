"""Nurbs WB - Next Generation

Filename:
    init_gui.py

Inspired from microelly work on freecad-nurbswb


Portions of code from microelly (c) 2016 - 2019.

Versions:
    v 0.1 - 2023 onekk

Licence:
    GNU Lesser General Public License (LGPL)

"""

__title__ = "FreeCAD Nurbs-NG"

__vers__ = "0.1"


import os
import sys
import re

import importlib

import FreeCAD
import FreeCADGui

import freecad.nurbswb


fc_msg = FreeCAD.Console.PrintMessage
fc_wrn = FreeCAD.Console.PrintWarning
fc_err = FreeCAD.Console.PrintError

ICONPATH = os.path.join(os.path.dirname(__file__), "resources", "icons")

# print(f"ICONPATH: {ICONPATH}")

# from workfeature macro
global get_SelectedObjects


def get_SelectedObjects(info=0, printError=True):
    """Return selected objects as Selection.

    (Number_of_Points, Number_of_Edges, Number_of_Planes,
      Selected_Points, Selected_Edges, Selected_Planes)
    """

    def storeShapeType(Object, Selected_Points, Selected_Edges, Selected_Planes):
        if Object.ShapeType == "Vertex":
            Selected_Points.append(Object)
            return True
        if Object.ShapeType == "Edge":
            Selected_Edges.append(Object)
            return True
        if Object.ShapeType == "Face":
            Selected_Planes.append(Object)
            return True
        return False

    m_actDoc = FreeCAD.ActiveDocument

    if m_actDoc.Name:
        # Return a list of SelectionObjects for a given document name.
        # "getSelectionEx" Used for selecting subobjects
        m_selEx = FreeCADGui.Selection.getSelectionEx(m_actDoc.Name)

        m_num = len(m_selEx)
        if info != 0:
            fc_msg(f"m_selEx : {str(m_selEx)}")
            fc_msg(f"m_num   : {str(m_num)}")

        if m_num >= 1:
            Selected_Points = []
            Selected_Edges = []
            Selected_Planes = []
            Selected_Objects = []
            for Sel_i_Object in m_selEx:
                if info != 0:
                    fc_msg(f"Processing : {str(Sel_i_Object.ObjectName)}")

                if Sel_i_Object.HasSubObjects:

                    for Object in Sel_i_Object.SubObjects:

                        if info != 0:
                            fc_msg(f"SubObject : {str(Object)}")

                        if hasattr(Object, 'ShapeType'):
                            storeShapeType(Object, Selected_Points, Selected_Edges, Selected_Planes)
                        if hasattr(Object, 'Shape'):
                            Selected_Objects.append(Object)
                else:
                    if info != 0:
                        fc_msg(f"Object : {str(Sel_i_Object)}")

                    if hasattr(Sel_i_Object, 'Object'):

                        if hasattr(Sel_i_Object.Object, 'ShapeType'):
                            storeShapeType(Sel_i_Object.Object, Selected_Points, Selected_Edges, Selected_Planes)
                        if hasattr(Sel_i_Object.Object, 'Shape'):
                            if hasattr(Sel_i_Object.Object.Shape, 'ShapeType'):
                                if not storeShapeType(Sel_i_Object.Object.Shape, Selected_Points, Selected_Edges, Selected_Planes):
                                    Selected_Objects.append(Sel_i_Object.Object)

            Number_of_Points = len(Selected_Points)
            Number_of_Edges = len(Selected_Edges)
            Number_of_Planes = len(Selected_Planes)
            Selection = (Number_of_Points, Number_of_Edges, Number_of_Planes,
                         Selected_Points, Selected_Edges, Selected_Planes,
                         Selected_Objects)

            if info != 0:
                fc_msg(f"Number_of_Points, Number_of_Edges, Number_of_Planes, \
                       Selected_Points, Selected_Edges, Selected_Planes,\
                       Selected_Objects = {str(Selection)}")
            return Selection
        else:
            if info != 0:
                fc_msg("No Object selected !")

            if printError:
                fc_err("Select at least one object !")
            return None
    else:
        fc_err("No active document !")

    return

# fast command adder template

global _Command2


class _Command2():
    """Create Command V2."""

    def __init__(self, lib=None, name=None, icon=None, command=None,
                 modul='freecad.nurbswb', tooltip='No Tooltip'):
        """Initialize class."""
        debug = False
        dbg_lev = 0

        if debug and dbg_lev > 0:
            print("--- Command2 ---")
            print(f"Cmd Name: {name}")
            print(f"Cmd Lib: {lib}")
            print(f"Cmd Cmd: {command}")
            print(f"Cmd Icon: {icon}")
            print(f"Cmd Modul: {modul}")
            print(f"Cmd Ttip: {tooltip}")

        if debug and dbg_lev == 0:
            print(f"Cmd2 Icon: {icon}")

        if lib is None:
            lmod = modul
        else:
            lmod = modul + '.' + lib

        if command is None:
            command = lmod + ".run()"
        else:
            command = lmod + "." + command

        self.lmod = lmod
        self.command = command
        self.modul = modul

        if icon is not None:
            self.icon = f"{ICONPATH}/{icon}"
        else:
            self.icon = None

        if name is None:
            name = command

        self.name = name
        self.tooltip = tooltip

        if debug and dbg_lev == 0:
            print(f"Cmd2 self.icon: {self.icon}")

    def GetResources(self):
        """Docstring missing."""
        if self.icon is not None:
            return {'Pixmap': self.icon,
                    'MenuText': self.name,
                    'ToolTip': self.tooltip,
                    'CmdType': "ForEdit"
                    # bleibt aktiv, wenn sketch editor oder andere tasktab an ist
                    }
        else:
            return {
                'MenuText': self.name,
                'ToolTip': self.name,
                'CmdType': "ForEdit"
                # bleibt aktiv, wenn sketch editor oder andere tasktab an ist
            }

    def IsActive(self):
        """Docstring missing."""
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        """Docstring missing."""
        ta = True

        if ta:
            FreeCAD.ActiveDocument.openTransaction(self.name)

        if self.command != '':
            if self.modul != '':
                modul = self.modul
            else:
                modul = self.name

            # dbg info
            print(f"modul: {modul}")

            FreeCADGui.doCommand("from importlib import reload")
            FreeCADGui.doCommand("import re")
            FreeCADGui.doCommand("import " + modul)
            FreeCADGui.doCommand("import " + self.lmod)
            FreeCADGui.doCommand("reload(" + self.lmod + ")")
            docstring = 'print()\nprint(' + re.sub(r'\(.*\)', '.__doc__)', self.command)
            FreeCADGui.doCommand(docstring)
            FreeCADGui.doCommand(self.command)

        if ta:
            FreeCAD.ActiveDocument.commitTransaction()

        if FreeCAD.ActiveDocument is not None:
            FreeCAD.ActiveDocument.recompute()


global _Command


class _Command():
    """Docstring missing."""

    def __init__(self, lib=None, name=None,
                 icon="nurbs.svg",
                 command=None, modul='freecad.nurbswb'):
        """Docstring missing."""
        debug = False
        dbg_lev = 0

        if debug and dbg_lev > 0:
            print("--- Command ---")
            print(f"Cmd Name: {name}")
            print(f"Cmd Lib: {lib}")
            print(f"Cmd Cmd: {command}")
            print(f"Cmd Icon: {icon}")
            print(f"Cmd Modul: {modul}")

        if lib is None:
            lmod = modul

        else:
            lmod = f"{modul}.{lib}"

        if command is None:
            command = f"{lmod}.run()"

        else:
            command = f"{lmod}.{command}"

        self.lmod = lmod
        self.command = command
        self.modul = modul

        self.icon = f"{ICONPATH}/{icon}"

        if name is None:
            name = command

        self.name = name

    def GetResources(self):
        """Docstring missing."""
        return {'Pixmap': self.icon,
                'MenuText': self.name,
                'ToolTip': self.name,
                'CmdType': "ForEdit"
                # bleibt aktiv, wenn sketch editor oder andere tasktab an ist
        }

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        # FreeCAD.ActiveDocument.openTransaction("create " + self.name)
        # dbg info
        # print(f"mod: {self.modul}")

        if self.command != '':
            if self.modul != '':
                modul = self.modul
            else:
                modul = self.name

            FreeCADGui.doCommand("from importlib import reload ")
            FreeCADGui.doCommand(f"import {modul}")
            FreeCADGui.doCommand(f"import {self.lmod}")
            FreeCADGui.doCommand(f"reload({self.lmod})")
            FreeCADGui.doCommand(self.command)

        # FreeCAD.ActiveDocument.commitTransaction()

        if FreeCAD.ActiveDocument is not None:
            FreeCAD.ActiveDocument.recompute()


class _alwaysActive(_Command):

    def IsActive(self):
        return True

# conditions when a command should be active ..


def always():
    """Docstring missing."""
    return True


def ondocument():
    """Execute if a document is active."""
    return FreeCADGui.ActiveDocument is not None


def onselection():
    """Execute if at least one object is selected."""
    return len(FreeCADGui.Selection.getSelection()) > 0


def onselection1():
    """Execute if exactly one object is selected."""
    return len(FreeCADGui.Selection.getSelection()) == 1


def onselection2():
    """Execute if exactly two objects are selected."""
    return len(FreeCADGui.Selection.getSelection()) == 2


def onselection3():
    """Execute if exactly three objects are selected."""
    return len(FreeCADGui.Selection.getSelection()) == 3


def onselex():
    """Execute if at least one subobject is selected."""
    return len(FreeCADGui.Selection.getSelectionEx()) != 0


def onselex1():
    """Execute if exactly one subobject is selected."""
    return len(FreeCADGui.Selection.getSelectionEx())==1


# the menu entry list
menu_elist = []

# create menu entries


def c1a(menu, isactive, name, *info):
    """Docstring missing."""
    global _Command
    name1 = f"Nurbs_{name}"
    t = _Command(name, *info)
    t.IsActive = isactive
    FreeCADGui.addCommand(name1, t)
    menu_elist.append([menu, name1, name, isactive, info])


def c2a(menu, isactive, title, name, *info):
    """Docstring missing."""
    global _Command
    t = _Command(name, *info)
    title1 = f"Nurbs_{title}"
    t.IsActive = isactive
    FreeCADGui.addCommand(title1, t)
    menu_elist.append([menu, title1, name, isactive, info])


def c2b(menu, isactive, title, name, text, icon, cmd=None, *info):
    """Docstring missing."""
    global _Command

    if cmd is None:
        cmd = f"{re.sub(r' ', '', text)}()"

    if name == 0:
        name = re.sub(r' ', '', text)

    t = _Command(name, text, icon, cmd, *info)

    if title == 0:
        title = f"TT{re.sub(r' ', '', text)}"

    name1 = f"Nurbs_{title}"
    t.IsActive = isactive

    FreeCADGui.addCommand(name1, t)
    menu_elist.append([menu, name1])


# the menu entry list
menu_elist2 = []
# create menu entries


def c3b(menu, isactive, name, text, icon=None, cmd=None, *info):
    """Docstring missing."""
    global _Command2

    if cmd is None:
        cmd = f"{re.sub(r' ', '', text)}()"

    if name == 0:
        name = re.sub(r' ', '', text)

    act = _Command2(name, text, icon, cmd, *info)

    title = re.sub(r' ', '', text)

    # print(f"title: {title}")

    name1 = f"Nurbs_{title}"

    act.IsActive = isactive

    FreeCADGui.addCommand(name1, act)

    menu_elist2.append([menu, name1])
    return name1


def c3bI(menu, isactive, name, text, icon=None, cmd=None, tooltip='', *info):
    """Docstring missing."""
    global _Command2

    if cmd is None:
        cmd = f"{re.sub(r' ', '', text)}()"

    if name == 0:
        name = re.sub(r' ', '', text)

    if icon is None:
        pic = re.sub(r' ', '', text)
        icon = f"{pic}.svg"

    if tooltip == '':
        tooltip = name

    act = _Command2(name, text, icon, cmd, tooltip=tooltip, *info)
    title = re.sub(r' ', '', text)
    name1 = f"Nurbs_{title}"
    act.IsActive = isactive
    FreeCADGui.addCommand(name1, act)
    menu_elist2.append([menu, name1])
    return name1


def c3bG(menu, isactive, name, text, icon=None, cmd=None, *info):
    """Docstring missing."""
    #
    if cmd is None:
        cmd = f"_{re.sub(r' ', '', text + 'GUI')}()"

    if name == 0:
        name = re.sub(r' ', '', text + 'GUI')

    act = _Command2(name, text, icon, cmd, *info)
    # if title ==0:
    title = re.sub(r' ', '', text)
    name1 = f"Transportation_{title}"
    act.IsActive = isactive
    FreeCADGui.addCommand(name1, act)
    menu_elist2.append([menu, name1])
    return name1


# special conditions for actions
def onneedle():
    """Open the needle file."""
    docname = FreeCAD.ParamGet(
        'User parameter:Plugins/nurbs').GetString("Document", "Needle")
    try:
        FreeCAD.getDocument(docname)
        return True
    except:
        return False


def onspread():
    """Check existence of a spreadsheet object."""
    try:
        FreeCAD.ActiveDocument.Spreadsheet
        return True
    except:
        return False

#


if FreeCAD.GuiUp:
    # Assign commands
    # Categories, ready to be modified
    cg1 = "N_Bezier"

    c2a([cg1, "create"], always, "Nurbs Editor", "nurbs", "Test cylinder noisy",
        "zebra.svg", "runtcn()")

    c2a([cg1, "create"], always, "Nurbs Editor", "nurbs", "Test cylinder plain",
        "zebra.svg", "runtcp()")

# --- Command Definition


class NurbsWorkbench(FreeCADGui.Workbench):
    """Nurbs."""

    MenuText = "Nurbs WB"
    ToolTip = "Nurbs Editing"

    Icon = '''
/* XPM */
static char * nurbs_xpm[] = {
"16 16 2 1",
".  c #E12DEC",
"+  c #FFFFFF",
"................",
"..++...++...++..",
"..++...++...++..",
"..++++++++++++..",
"..++...++...++..",
"..++...++...++..",
"..++...++...++..",
"..++++++++++++..",
"..++...++...++..",
"..++...++...++..",
"..++...++...++..",
"..++++++++++++..",
"..++...++...++..",
"..++...++...++..",
"................",
"................"};'''

    def GetClassName(self):
        """Docstring missing."""
        return "Gui::PythonWorkbench"

    def __init__(self, version):
        """Docstring missing."""
        self.version = version

    def Initialize(self):
        """Docstring missing."""
        FreeCADGui.activateWorkbench("DraftWorkbench")
        FreeCADGui.activateWorkbench("SketcherWorkbench")

        try:
            pass
        except:
            pass

        # for cmd_item in menu_elist:
        #    self.appendToolbar(t[0], t[1])

        menus = {}
        menu_lst = []

        for cmd_item in menu_elist:

            try:
                # print("ig1: try")
                menus[tuple(cmd_item[0])].append(cmd_item[1])
            except:
                # print("ig2: except")
                menus[tuple(cmd_item[0])] = [cmd_item[1]]
                menu_lst.append(tuple(cmd_item[0]))

        for menu in menu_lst:
            self.appendMenu(list(menu), menus[menu])


FreeCADGui.addWorkbench(NurbsWorkbench(__vers__))
