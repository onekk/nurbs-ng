"""Nurbs WB - Next Generation

Filename:
    nurbs_tools.py

Inspired from microelly work on freecad-nurbswb


Portions of code from microelly (c) 2016 - 2019.

Versions:
    v 0.1 - 2023 onekk

Licence:
    GNU Lesser General Public License (LGPL)

"""

import os
import math

import FreeCAD
import FreeCADGui

from FreeCAD import Placement, Rotation

import Part

from pivy import coin

V2d = FreeCAD.Base.Vector2d
V3d = FreeCAD.Vector


# SERVICE METHODS


def clear_doc(doc_name):
    """Clear document deleting all the objects.

    Args:
        doc_name (str): document name

    Returns:
        None

    """
    doc = FreeCAD.getDocument(doc_name)

    try:
        while len(doc.Objects) > 0:
            doc.removeObject(doc.Objects[0].Name)
    except Exception as e:
        print(f"Exception: {e}")


def ensure_document(doc_name, action=0):
    """Ensure existence of a document with doc_name.

    If document not exist it will create it, if exist it will perform an action.

    Args:
        doc_name (str): document name
        action (int): action to perform if document exist. Defaults to 0 could
            assume these values:
                0: do nothing
                1: close and reopen the document with the same name
                2: delete all objects

    Returns:
        str: Document name from obj.Name
    """
    #
    doc_root = FreeCAD.listDocuments()
    doc_exist = False

    for d_name, doc in doc_root.items():
        # debug info do not delete
        print(f"ED: doc name = {d_name}")

        if d_name == doc_name:
            # print("Match name")
            if action == 1:
                # when using clear_doc() is not possible like in Part.Design
                FreeCAD.closeDocument(doc_name)
                doc_exist = False
            elif action == 2:
                doc_exist = True
                clear_doc(doc_name)
                FreeCAD.setActiveDocument(d_name)
            else:
                doc_exist = True
                FreeCAD.setActiveDocument(d_name)

    if doc_exist is False:
        # debug info do not delete
        # print("ED: Create = {}".format(doc_name))
        ndoc = FreeCAD.newDocument(doc_name)
        ndoc.FileName = ndoc.Name
        # print(f'ndoc: {ndoc}')

    return FreeCAD.activeDocument().Name


def setview(doc_name, t_v=0):
    """Set viewport in 3D view.

    Args:
        doc_name (str): document name
        t_v (int): set the view. Defaults to 0. Possible valuese:
            0: Top
            1: Front
            others: Isometric
    """
    FreeCAD.setActiveDocument("")
    FreeCAD.ActiveDocument = None
    FreeCADGui.ActiveDocument = None

    FreeCAD.setActiveDocument(doc_name)

    FreeCADGui.ActiveDocument = FreeCADGui.getDocument(doc_name)
    VIEW = FreeCADGui.ActiveDocument.ActiveView

    # print(dir(VIEW))

    if t_v == 0:
        VIEW.viewTop()
    elif t_v == 1:
        VIEW.viewFront()
    else:
        VIEW.viewIsometric()

    VIEW.setAxisCross(True)
    VIEW.fitAll()


# microelly2 methods

# from original nurbs.py

def set_coin_render():
    """Change render to show triangulations."""
    view = FreeCADGui.ActiveDocument.ActiveView
    viewer = view.getViewer()
    render = viewer.getSoRenderManager()

    glAction = coin.SoGLRenderAction(render.getViewportRegion())
    render.setGLRenderAction(glAction)
    render.setRenderMode(render.WIREFRAME_OVERLAY)


def setNice(flag=True):
    """Make smooth skins."""
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Part")
    w = p.GetFloat("MeshDeviation")
    print(f"Actual MeshDeviation: {w}")

    if flag:
        p.SetFloat("MeshDeviation", 0.05)
    else:
        p.SetFloat("MeshDeviation", 0.5)


def showIsoparametricUCurve(bsplinesurface, u=0.5):
    """Create a curve in 3D space."""
    bc = bsplinesurface.uIso(u)
    Part.show(bc.toShape())


def showIsoparametricVCurve(bsplinesurface, v=0.5):
    """Create a curve in 3D space."""
    bc = bsplinesurface.vIso(v)
    Part.show(bc.toShape())


# nurbswb lib


def surf_curvature(sf, u, v):
    """Calculate Surface Curvature at point."""
    d = 0.01
    d = 0.0001
    
    t1, t2 = sf.tangent(u, v)
    
    if t1 is None or t2 is None:
        print("No tangent for {u},{v}")
        return -1, -1

    t1 = t1.multiply(d)
    t2 = t2.multiply(d)

    vf = sf.value(u, v)

    vfw = vf + t1
    uu, vv = sf.parameter(vfw)
    vfw = sf.value(uu, vv)

    vfe = vf - t1
    uu, vv = sf.parameter(vfe)
    vfe = sf.value(uu, vv)

    ku = vfw + vfe - vf - vf
    ddu = (vfw - vf).Length
    ku = ku.multiply(1.0 / ddu / ddu)

    vfn = vf + t2
    uu, vv = sf.parameter(vfn)
    vfn = sf.value(uu, vv)

    vfs = vf - t2
    uu, vv = sf.parameter(vfs)
    vfs = sf.value(uu, vv)

    kv = vfn + vfs - vf - vf
    ddv = (vfn - vf).Length
    kv = kv.multiply(1.0 / ddv / ddv)

    # ku=round(ku.Length,3)
    # kv=round(kv.Length,3)
    # print ku
    ku = -ku.z
    kv = -kv.z

    ru = None
    rv = None
    if ku != 0:
        ru = round(1 / ku, 3)
    if kv != 0:
        rv = round(1 / kv, 3)

    # print("Krmmungen:",ku,kv,"Krmmungsradien:", ru,rv)

    return ku, kv


# -------------------------------
