"""Nurbs editor.

Inspired from microelly freecad-nurbbs.

Some portions of code are derived from microelly code.

References:
    https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline
    https://forum.freecad.org/viewtopic.php?p=561221#p561221 by Crish_G
    http://www.opencascade.com/doc/occt-6.9.0 # version number could be different
      /refman/html/class_geom___b_spline_surface.html

Notes:
    works in new wb scheme

    1) numpy array are stored sequentially for a very fast acces
       see examples/example_nparray.py for some explanation

    2) BSplines and NURBS (Non Uniform Rational Bspline Surface)

      BSS is a short term for "BSpline Surface"

      When Weights are different from 1 we have a NURBS, ie the surface
       is Rational.
      Rational characteristic is defined in each parametric direction (U, V).

      Definitions:
        Poles:
          Poles are alos called "control points".

        Weights:
          In homogeneous coordinates, the poles are 4D : (x, y, z, w)
          In NURBS Weights are the 'w' coordinates of the poles.
          So always: len(weights) = len(poles)

        Knots is a sequence of parameter values that determines where and
          how Poles affect the NURBS curve.
          Knot vector should be in non decreasing order.
          Number of knots = Numpoles + degree + 1.

          Most often in Nurbs articles, knots arrays are written WITH knot
          repetition, in OpenCascade, knots are described by 2 arrays:
            - knots (without repetition)
            - multiplicities, see below.

        Multiplicities (Mults) are repetition of knots.
          So always: len(mults) = len(knots).
          1 <= Mults(i) <= Degree

          This knots vector = [0.0, 0.0, 0.0, 1.0, 2.0, 2.0, 2.0] written
          in Traditional way will became:
            knots = [0.0, 1.0, 2.0]
            mults = [3, 1, 3]

        Mults could have some special cases, where the knots are regularly
          spaced in one parametric direction (PD) in other word difference
          between two consecutive knots is constant.

          - "Uniform": all the mults are equal to 1.
          - "Quasi-uniform": all the mults are equal to 1, except for first
             and last knots, and these are equal to Degree + 1.
          - "Piecewise Bezier": all the mults are equal to Degree except for
             first and last knots, which are equal to Degree + 1.
             Resulting surface is a concatenation of Bezier patches in PD.

         In "not periodic" surface:
           - bounds of knots and mults tables are:  1 < knot < NbKnots
              where NbKnots is the number of knots of the BSS in parametric
              direction.
          - first and last mults may be UDegree+1 (this is recommended if you
              want the curve to start and finish on the first and last pole).
          - Poles.ColLength() == Sum(UMults(i)) - UDegree - 1 >= 2 (for U)
          - Poles.RowLength() == Sum(VMults(i)) - VDegree - 1 >= 2 (for U)

         In "periodic" surfaces:
          - first and last mults must be the same.
          - given k periodic knots and p periodic poles in PD:
              - period is such that: period = Knot(k+1) - Knot(1),
              - poles and knots tables in PD can be considered as infinite tables,
                such that:
                  - Knot(i + k) = Knot(i) + period,
                  - Pole(i + p) = Pole(i)
          - Poles.ColLength() == Sum(UMults(i)) except first or last. (for U)
          - Poles.RowLength() == Sum(VMults(i)) except first or last. (for V)

         Note: Data structure tables for a periodic BSpline surface are more complex
           than those of a non-periodic one.

Versions:
    v 0.1 - 2023 onekk

Licence:
    GNU Lesser General Public License (LGPL)

"""

__version__ = "0.1"


import time
import random

import FreeCAD
import FreeCADGui

import Draft
import Part

import numpy as np

import freecad.nurbswb.nurbs_dialog  # noqa

from freecad.nurbswb.nurbs_tools import ensure_document, clear_doc, setview  # noqa


import PySide


class NurbsObj:
    """Docstring missing."""

    def __init__(self, obj):
        """Docstring missing."""
        obj.Proxy = self
        self.obj2 = obj

    def attach(self, vobj):
        """Docstring missing."""
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


class VP_NurbsObj:
    """Docstring missing."""

    def __init__(self, obj):
        """Docstring missing."""
        obj.Proxy = self
        self.Object = obj

    def attach(self, obj):
        """Assign scene sub-graph of view provider, this method is mandatory."""
        obj.Proxy = self
        self.Object = obj
        return

    def updateData(self, fp, prop):
        """Handle a property change in the handled feature."""
        return

    def getDisplayModes(self, obj):
        """Docstring missing."""
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        """Return name of default display mode.

        It must be defined in getDisplayModes.
        """
        return "Shaded"

    def setDisplayMode(self, mode):
        """Map display mode defined in attach with those defined in getDisplayModes.

        Since they have same names nothing needs to be done. This method is optional.
        """
        return mode

    def onChanged(self, vp, prop):
        """Docstring missing."""
        pass

    def showVersion(self):
        """Docstring missing."""
        # print(f"svd_bg: {self.Object.Object.Name}")
        msg = ["Nurbs Object:"]
        msg.extend((f"- Version {__version__}",
                    f"Object Name: {self.Object.Object.Name}",
                    f"Object Label: {self.Object.Object.Label}"))
        msg_txt = "\n".join(msg)
        PySide.QtGui.QMessageBox.information(
            None, "About ", msg_txt)

    def setupContextMenu(self, obj, menu):
        """Docstring missing."""
        cl = self.Object.Proxy.__class__.__name__
        action = menu.addAction("About " + cl)
        action.triggered.connect(self.showVersion)

        action = menu.addAction("Edit ...")
        action.triggered.connect(self.edit)

        # for m in self.cmenu + self.anims():
        #     action = menu.addAction(m[0])
        #     action.triggered.connect(m[1])

    def getIcon(self):
        """Docstring missing."""
        return """
            /* XPM */
            static const char * ViewProviderNurbs_xpm[] = {
            "16 16 6 1",
            "   c None",
            ".  c #141010",
            "+  c #615BD2",
            "@  c #C39D55",
            "#  c #000000",
            "$  c #57C355",
            "        ........",
            "   ......++..+..",
            "   .@@@@.++..++.",
            "   .@@@@.++..++.",
            "   .@@  .++++++.",
            "  ..@@  .++..++.",
            "###@@@@ .++..++.",
            "##$.@@$#.++++++.",
            "#$#$.$$$........",
            "#$$#######      ",
            "#$$#$$$$$#      ",
            "#$$#$$$$$#      ",
            "#$$#$$$$$#      ",
            " #$#$$$$$#      ",
            "  ##$$$$$#      ",
            "   #######      "};
            """

    def __getstate__(self):
        """Docstring missing."""
        return None

    def __setstate__(self, state):
        """Docstring missing."""
        return None

    def edit(self):
        """Docstring missing."""
        FreeCAD.tt = self
        self.Object.Object.generatePoles = False
        self.Object.Object.Label = "Nurbs individual"
        # FIXME: Add the proper edit dialog
        # self.miki = nurbswb.nurbs_dialog.mydialog(self.Object)

    def setEdit(self, vobj, mode=0):
        """Docstring missing."""
        self.edit()
        return True

    def unsetEdit(self, vobj, mode=0):
        """Docstring missing."""
        return True

    def doubleClicked(self, vobj):
        """Docstring missing."""
        return False


class Nurbs(NurbsObj):
    """Docstring missing."""

    def __init__(self, obj, uc=5, vc=5):
        """Docstring missing."""
        NurbsObj.__init__(self, obj)

        print(f"Nurbs.obj: {obj.Name}")
        self.TypeId = "Nurbs"

        self.add_properties(obj)

        # Base

        obj.model = ["NurbsSurface", "NurbsCylinder", "NurbsSphere",
                     "NurbsTorus",]

        # Nurbs

        # obj.poles =  # Unassigned here
        obj.weights = [1] * (uc * vc)
        obj.degree_u = 3
        obj.degree_v = 3
        obj.knot_u = [0, 0, 0, 0.33, 0.67, 1, 1, 1,]
        obj.knot_v = [0, 0, 0, 0.33, 0.67, 1, 1, 1,]

        # Generator

        obj.nNodes_u = uc
        obj.nNodes_v = vc
        obj.stepU = 100
        obj.stepV = 100
        obj.generatePoles = True

        # XYZ

        obj.expertMode = False
        obj.polnumber = 0
        # other properties are stored here
        # height and radius could be assigned or not.
        # as example a cylinder and a torus has a radius and an height
        # a sphere has a radius only
        # a torus has two radiuses and a height in Z
        # surfaces has different definition
        obj.Height = 1.0
        obj.Radius = 200
        obj.Radius2 = 150

        # Helper
        obj.grid = True
        obj.gridCount = 6
        obj.polpoints = False

        # Shape
        obj.solid = True
        obj.base = True
        obj.baseHeight = 100

        if obj.expertMode:
            for elem in ["degree_u", "degree_v", "poles",
                         "knot_u", "knot_v", "nNodes_u", "nNodes_v",
                         "weights", "solid",]:
                obj.setEditorMode(elem, 0)

        if obj.generatePoles:
            for elem in ["nNodes_u", "nNodes_v"]:
                obj.setEditorMode(elem, 0)

        self.hide_var_prop(obj)

    def hide_var_prop(self, obj):
        """Hide variable properties.

        Variable properties are those that are not neede for some models.
        """
        # not gui editable for now
        for elem in ["polnumber", "polselection", "gridobj",
                     "polgrid", "polobj"]:
            # 0 to make editable for testing
            obj.setEditorMode(elem, 2)

    def hide_mod_prop(self, obj):
        """Hide model dependant properties."""
        #
        for elem in ["Height", "Radius", "Radius2"]:
            # 0 to make editable for testing
            obj.setEditorMode(elem, 2)

    def add_properties(self, obj):
        """Add properties to the object."""
        # Category Base
        obj.addProperty(
            "App::PropertyEnumeration", "model", "Base", "")

        # Category Nurbs

        # Part.BSplineSurface.buildFromPolesMultsKnots
        # Args:
        #   poles (sequence of sequence of Base.Vector),
        #   umults, vmults,
        #   uknots, vknots,
        #   uperiodic, vperiodic,
        #   udegree, vdegree,
        #   weights (sequence of sequence of float)

        obj.addProperty(
            "App::PropertyStringList", "poles", "Nurbs", "")

        obj.addProperty(
            "App::PropertyFloatList", "weights", "Nurbs", "")

        obj.addProperty(
            "App::PropertyInteger", "degree_u", "Nurbs", "")

        obj.addProperty(
            "App::PropertyInteger", "degree_v", "Nurbs", "")

        obj.addProperty(
            "App::PropertyFloatList", "knot_u", "Nurbs", "")

        obj.addProperty(
            "App::PropertyFloatList", "knot_v", "Nurbs", "")

        # Category Generator

        obj.addProperty(
            "App::PropertyInteger", "nNodes_u", "Generator", "")

        obj.addProperty(
            "App::PropertyInteger", "nNodes_v", "Generator", "")

        obj.addProperty(
            "App::PropertyFloat", "stepU", "Generator",
            "size of cell in u direction")

        obj.addProperty(
            "App::PropertyFloat", "stepV", "Generator",
            "size of cell in u direction")

        obj.addProperty(
            "App::PropertyBool", "generatePoles", "Generator",
            "generate Poles from model",)

        # Category XYZ
        obj.addProperty(
            "App::PropertyBool", "expertMode", "XYZ",
            "Activate expert Mode")

        obj.addProperty(
            "App::PropertyInteger", "polnumber", "XYZ",
            "Length of the Nurbs")

        obj.addProperty("App::PropertyLink", "polobj", "XYZ", "")
        obj.addProperty("App::PropertyLink", "gridobj", "XYZ", "")
        obj.addProperty("App::PropertyLink", "polselection", "XYZ", "")
        obj.addProperty("App::PropertyLink", "polgrid", "XYZ", "")

        obj.addProperty(
            "App::PropertyFloat", "Height", "XYZ", "Nurbs Height (Z)")

        obj.addProperty(
            "App::PropertyFloat", "Radius", "XYZ", "Nurbs Radius")

        obj.addProperty(
            "App::PropertyFloat", "Radius2", "XYZ", "Nurbs Radius2")

        # Category Helper

        obj.addProperty(
            "App::PropertyBool", "grid", "Helper",
            "create a grid object in 3D")

        obj.addProperty(
            "App::PropertyInteger", "gridCount", "Helper", "")

        obj.addProperty(
            "App::PropertyBool", "polpoints", "Helper",
            "display Poles as separate Points",)

        # Category Shape
        obj.addProperty(
            "App::PropertyBool", "solid", "Shape",
            "close the surface by a bottom plane")

        obj.addProperty(
            "App::PropertyBool", "base", "Shape",
            "create a base cuboid under the surface",)

        obj.addProperty(
            "App::PropertyFloat", "baseHeight", "Shape",
            "height of the base cuboid",)

    def attach(self, vobj):
        """Docstring missing."""
        print("attach -------------------------------------")
        self.Object = vobj.Object
        self.obj2 = vobj.Object

    def onChanged(self, fp, prop):
        """Docstring missing."""
        # print "changed ",prop

        if prop == "model":
            print(f"Nurbs model: {fp.model}")
            if fp.model in ("NurbsCylinder", "NurbsSphere", "NurbsTorus"):
                fp.setEditorMode("Radius", 0)
            if fp.model in ("NurbsCylinder", "NurbsTorus"):
                fp.setEditorMode("Height", 0)
            if fp.model in ("NurbsTorus"):
                fp.setEditorMode("Radius2", 0)
            else:
                self.hide_mod_prop(fp)

        if prop == "nNodes_u" and fp.nNodes_u <= fp.degree_u:
            fp.nNodes_u = fp.degree_u + 1

        elif prop == "nNodes_v" and fp.nNodes_v <= fp.degree_v:
            fp.nNodes_v = fp.degree_v + 1

        elif prop == "expertMode":

            if fp.expertMode:
                v = 0
            else:
                v = 2

            for a in ["degree_u", "degree_v", "poles", "knot_u",
                      "knot_v", "nNodes_u", "nNodes_v", "weights",]:
                try:
                    fp.setEditorMode(a, v)
                except:
                    pass

        elif prop == "generatePoles":
            if fp.generatePoles:
                v = 0
            else:
                v = 2

            for a in ["nNodes_u", "nNodes_v", "stepU", "stepV"]:
                try:
                    fp.setEditorMode(a, v)
                except:
                    pass

        elif prop in ("stepU", "stepV", "nNodes_u", "nNodes_v"):
            a = FreeCAD.ActiveDocument.Nurbs
            a.Proxy.obj2 = a

            try:
                # FIXME: on Update shape is modified.
                print(f"prop: {prop} try executed")
                ps = a.Proxy.getPoints()

                # dbg info
                print(f"----- BEFORE -------------- points: {len(ps)}")

                a.Proxy.togrid(ps)
                # a.Proxy.elevateVline(2,100)

                # try to point where the change is made
                a.Proxy.updatePoles()
                a.Proxy.showGriduv()

                # dbg info added
                ps = a.Proxy.getPoints()
                print(f"----- AFTER -------------- points: {len(ps)}")

                a.Proxy.update(fp)

            except:
                print(f"prop: {prop} except executed")
                pass

        return

    def update(self, fp):
        """Docstring missing."""
        if hasattr(fp, "polobj"):
            print("-------------------- polobj.set")
            if fp.polobj is not None:
                FreeCAD.ActiveDocument.removeObject(fp.polobj.Name)

            fp.polobj = self.createSurface(fp, fp.poles)

            if fp.polobj is not None:
                fp.polobj.ViewObject.PointSize = 4
                fp.polobj.ViewObject.PointColor = (1.0, 0.0, 0.0)

    def execute(self, fp):
        """Docstring missing."""
        pass

    def onDocumentRestored(self, fp):
        """Docstring missing."""
        print(f"onDocumentRestored {fp.Label} : {fp.Proxy.__class__.__name__}"),
        print(f"onDocumentRestored {fp.Name}"),
        a = FreeCAD.ActiveDocument.Nurbs
        a.Proxy.obj2 = a

        ps = a.Proxy.getPoints()
        a.Proxy.togrid(ps)
        a.Proxy.updatePoles()
        a.Proxy.showGriduv()
        a.Proxy.update(fp)

        if fp.expertMode:
            v = 0
        else:
            v = 2

        for a in ["degree_u", "degree_v", "poles", "knot_u", "knot_v",
                  "nNodes_u", "nNodes_v", "weights",]:
            fp.setEditorMode(a, v)

        if fp.generatePoles:
            v = 0
        else:
            v = 2

        for a in ["nNodes_u", "nNodes_v", "stepU", "stepV"]:
            fp.setEditorMode(a, v)

        # Do not visulize for now
        for a in ["polnumber", "Height", "polselection", "gridobj",
                  "polgrid", "polobj",]:
            fp.setEditorMode(a, 2)

    def create_grid_shape(self, ct=20):
        """Create a grid of BSplineSurface bs with ct lines and rows."""
        #
        ct = ct
        bs = self.bs
        sss = []

        st = 1.0 / ct
        for iu in range(ct + 1):
            pps = []
            for iv in range(ct + 1):
                p = bs.value(st * iu, st * iv)
                pps.append(p)
            tt = Part.BSplineCurve()
            tt.interpolate(pps)
            ss = tt.toShape()
            sss.append(ss)

        for iv in range(1, ct + 1):
            pps = []
            for iu in range(0, ct + 1):
                p = bs.value(st * iu, st * iv)
                # print(iv,iu,st*iu,st*iv)
                pps.append(p)
            tt = Part.BSplineCurve()
            tt.interpolate(pps)
            ss = tt.toShape()

            # Hack
            ss = Part.makePolygon(pps)
            sss.append(ss)

        comp = Part.Compound(sss)
        return comp

    def create_grid(self, bs, ct=20):
        """Docstring missing."""
        comp = self.create_grid_shape(ct)
        grid = Part.show(comp)
        return grid

    def create_uv_grid_shape(self):
        """Create a grid of the poles."""
        #
        bs = self.bs
        sss = []

        nNodes_u = self.obj2.nNodes_u
        nNodes_v = self.obj2.nNodes_v

        print("--- CGS: poles and knots ---")
        print(f"Knots U: {nNodes_u} V: {nNodes_v}")
        print(f"Poles U: {bs.NbUPoles} V: {bs.NbVPoles}")

        # TODO: see why it is repeated the nNodes
        #       closed bspline are not managed, for loop seem to
        #       redefine things and assume allbspline are closed

        nNodes_u = bs.NbUPoles
        nNodes_v = bs.NbVPoles

        for iu in range(nNodes_u):
            # meridiane
            pps = []
            p = bs.getPole(1 + iu, 1)
            pps = [p.add(FreeCAD.Vector(0, -20, 0))]

            for iv in range(nNodes_v):
                p = bs.getPole(1 + iu, 1 + iv)
                pps.append(p)

            p = bs.getPole(1 + iu, nNodes_v)
            pps.append(p.add(FreeCAD.Vector(0, 20, 0)))

            ss = Part.makePolygon(pps)

            # for closed
            ss = Part.makePolygon(pps[1:-1])
            # if iu==nNodes_u-1:
            sss.append(ss)

        for iv in range(nNodes_v):
            # breitengrade
            p = bs.getPole(1, 1 + iv)
            pps = [p.add(FreeCAD.Vector(-20, 0, 0))]
            for iu in range(nNodes_u):
                p = bs.getPole(1 + iu, 1 + iv)
                pps.append(p)

            p = bs.getPole(nNodes_u, 1 + iv)
            pps.append(p.add(FreeCAD.Vector(20, 0, 0)))

            ss = Part.makePolygon(pps)

            # for closed
            pps2 = pps[1:-1]
            pps2.append(pps[1])
            try:
                ss = Part.makePolygon(pps2)
                # horizontal
                # if iv != 1:
                sss.append(ss)
            except:
                print(("kein polygon fuer", pps2))

        comp = Part.Compound(sss)

        print("--- CGS: End ---")

        return comp

    def create_uv_grid(self):
        """Show UV grid."""
        comp = self.create_uv_grid_shape()
        gdo = Part.show(comp)

        gdo.ViewObject.LineColor = (1.0, 0.0, 1.0)
        gdo.ViewObject.LineWidth = 1

        return gdo

    def create_solid(self, bs):
        """Create a solid part with the surface as top."""
        #
        poles = np.array(bs.getPoles())
        ka, kb, tt = poles.shape

        weights = np.array(bs.getWeights())
        multies = bs.getVMultiplicities()

        cs = []

        for n in 0, ka - 1:
            pts = [FreeCAD.Vector(tuple(p)) for p in poles[n]]
            bc = Part.BSplineCurve()
            bc.buildFromPolesMultsKnots(
                pts, multies, bs.getVKnots(), False, 2, weights[n]
            )
            cs.append(bc.toShape())

        poles = poles.swapaxes(0, 1)
        weights = weights.swapaxes(0, 1)
        multies = bs.getUMultiplicities()

        for n in 0, kb - 1:
            pts = [FreeCAD.Vector(tuple(p)) for p in poles[n]]
            bc = Part.BSplineCurve()
            bc.buildFromPolesMultsKnots(
                pts, multies, bs.getUKnots(), False, 2, weights[n]
            )
            cs.append(bc.toShape())

        comp = Part.Compound(cs)
        sdo = Part.show(comp)

        # FIXME: see if FreeCAD.ActiveDocument.ActiveObject could be made
        #        a proper object, now it is not clear what is upgraded

        # create wire and face
        Draft.upgrade(sdo, delete=True)
        FreeCAD.ActiveDocument.recompute()

        Draft.upgrade(FreeCAD.ActiveDocument.ActiveObject, delete=True)
        FreeCAD.ActiveDocument.recompute()

        # bottom face ...
        cur = FreeCAD.ActiveDocument.ActiveObject
        s1 = cur.Shape
        FreeCAD.ActiveDocument.removeObject(cur.Name)

        # solid ...
        sh = Part.makeShell([s1, bs.toShape()])
        return Part.makeSolid(sh)

    def CylinderCoords(self, obj, coor, debug=False):
        """Calculate coord for cylinder."""
        coor = np.array(coor)

        if debug is True:
            print(f"Cylinder coord: {coor}")

        l, d = coor.shape

        xs = coor[:, 0]
        ys = coor[:, 1]
        zs = coor[:, 2]

        xs -= xs.min()
        xs /= xs.max()
        xs *= 2 * np.pi

        if debug is True:
            print(f"xs: min: {xs.min()} max: {xs.max()}")
            print(f"{xs}")

        ys -= ys.min()
        ys /= ys.max()

        if debug is True:
            print(f"ys: min: {ys.min()} max: {ys.max()}")
            print(f"{ys}")

        if debug is True:
            print(f"zs min: {zs.min()} max: {zs.max()}")
            print(f"{zs}")

        if zs.max() != 0.:
            zs -= zs.min()
            zs /= zs.max()

        coor = []
        h = 2000

        for i in range(l):
            r = 400 + 200 * zs[i]

            # coor.append([r * np.cos(xs[i]), r * np.sin(xs[i]), h * ys[i]])
            coor.append([r * np.sin(xs[i]), r * np.cos(xs[i]), h * ys[i]])

        return coor

    def SphereCoords(self, obj, coor, debug=False):
        """Calculate coord for sphere."""
        coor = np.array(coor)

        if debug is True:
            print(f"Sphere coord: {coor}")

        l, d = coor.shape
        xs = coor[:, 0]
        ys = coor[:, 1]
        zs = coor[:, 2]

        xs -= xs.min()
        xs /= xs.max()
        xs *= 2 * np.pi

        if debug is True:
            print(f"xs: min: {xs.min()} max: {xs.max()}")
            print(f"{xs}")

        ys -= ys.min()
        ys /= ys.max()
        ys -= 0.5
        ys *= np.pi

        if debug is True:
            print(f"ys: min: {ys.min()} max: {ys.max()}")
            print(f"{ys}")

        if debug is True:
            print(f"zs min: {zs.min()} max: {zs.max()}")
            print(f"{zs}")

        # same as for cylinder
        if zs.max() != 0.:
            zs -= zs.min()
            zs /= zs.max()

        coor = []
        r = 400

        # Sphere parametrization is:
        # x(u, v) = a * cos(u) * sin(v)
        # y(u, v) = a * sin(u) * sin(v)
        # z(u, v) = a * cos(v)

        for i in range(l):
            r = 400 + 400 * zs[i]
            r = 400 - 60 * zs[i]
            coor.append(
                [
                    r * np.cos(xs[i]) * np.cos(ys[i]),
                    r * np.sin(xs[i]) * np.cos(ys[i]),
                    r * np.sin(ys[i]),
                ]
            )

        return coor

    def SphereCoords2(self, obj, debug=False):
        """Calculate coord for sphere.

        Sphere parametrization is:
            x(u, v) = a * cos(u) * sin(v)
            y(u, v) = a * sin(u) * sin(v)
            z(u, v) = a * cos(v)
        """
        #
        rad = obj.Radius

        coor = []

        stu = obj.stepU
        stv = obj.stepV

        for i in range(l):
            coor.append(
                [
                    rad * np.cos(up) * np.sin(vp),
                    rad * np.sin(up) * np.sin(vp),
                    rad * np.cos(vp)
                ]
            )

        if debug is True:
            print(f"Sphere coord: {coor}")

        return coor

    def createSurface(self, obj, poles=None):
        """Create the nurbs surface and aux parts."""
        # some debug information to tune things
        debug = True
        dbg_poles = False
        dbg_lists = False
        #
        print(f"--- createSurface: {obj.model} ---")

        starttime = time.time()

        # set some common values
        kn_tol = 0.0000001

        # take objects data
        o_deg_u = obj.degree_u
        o_deg_v = obj.degree_v
        o_nNo_u = obj.nNodes_u
        o_nNo_v = obj.nNodes_v

        uc = o_nNo_u
        vc = o_nNo_v

        knot_u, knot_v = self._set_degree(obj, uc, vc)

        # Set default coor needed as they are modified later

        # Keep here as probably it needed for cylinder and sphere
        # moving it afte the model type check, create error.
        print("--- Test obj.poles")

        if poles is not None:
            print("poles are existing so coord are loaded")
            cc = ""
            for l in poles:
                cc += str(l)

            coor = eval(cc)
        else:
            print("poles are None assign coor")
            coor = [
                [0, 0, 1], [1, 0, 1], [2, 0, 1], [3, 0, 1], [4, 0, 1],
                [0, 1, 1], [1, 1, 0], [2, 1, 0], [3, 1, 0], [4, 1, 1],
                # el[2, 2, 3] in microelly code
                [0, 2, 1], [1, 2, 0], [2, 2, 1], [3, 2, 0], [4, 2, 1],
                # el[3, 3, -3] in microelly code
                [0, 3, 1], [1, 3, 0], [2, 3, 1], [3, 3, 1], [4, 3, 1],
                [0, 4, 1], [1, 4, 1], [2, 4, 1], [3, 4, 1], [4, 4, 1],
            ]

        # NOTE: added a debug flag to the coord amend methods

        if obj.model == "NurbsCylinder":
            coor = self.CylinderCoords(obj, coor, True)

        elif obj.model == "NurbsSphere":
            rad = 400
            coor = self.SphereCoords2(obj, rad, True)
            # coor = self.SphereCoords(obj, coor, True)

            # CHECK: Why amend knot_u and knot_w for sphere?
            if obj.degree_u == 3:
                l = [1.0 / (uc - 3) * i for i in range(uc - 2)]
                obj.knot_u = [0, 0, 0, 0] + l + [1, 1, 1, 1]

            if obj.degree_v == 3:
                l = [1.0 / (vc - 3) * i for i in range(vc - 2)]
                obj.knot_v = [0, 0, 0, 0] + l + [1, 1, 1, 1]

        else:
            pass

        # FIXME: old test cases?
        # knot_u=[0,0,0.2,0.4,0.6,0.8,1,1]
        # knot_u=[0,0,0.2, 0.4,0.4, 0.6,0.8,1,1]

        # knot_v=[0,0.5,1]
        # knot_v=[0,0,0.5,1,1]

        # Moved after calculations
        # obj.poles = str(coor)

        # FIXME: weights are not working
        print(obj.weights)

        try:
            weights = np.array(obj.weights)
            weights = weights.reshape(uc, vc)
        except:
            weights = np.ones(uc * vc)
            weights = weights.reshape(uc, vc)

        # -----------------------------------------
        # Assign weight to obj
        # -----------------------------------------

        # TODO: probably move it near poles assign

        obj.weights = list(np.ravel(weights))

        # This assign bs to self.bs, it is only the base object
        bs = Part.BSplineSurface()

        self.bs = bs

        # TODO: see if this could not be moved elsewhere
        bs.increaseDegree(o_deg_u, o_deg_v)

        if obj.model == "NurbsCylinder":
            # cylinder - experimental  play with periodic nurbs
            bs.setUPeriodic()

        elif obj.model == "NurbsSphere":
            # sphere - experimental  play with periodic nurbs
            bs.setUPeriodic()

        else:
            pass

        if debug:
            print("Knots prior knots insertion")
            print(f"knot_u: {knot_u}")
            print(f"knot_v: {knot_v}")
            print(f"bs.NbUKnots: {bs.NbUKnots}")
            print(f"bs.NbVKnots: {bs.NbVKnots}")

        #  mec: split knot vectors in single values vector and multiplicity vector

        for i in range(0, len(knot_u)):
            # if knot_u[i+1] > knot_u[i]:
            bs.insertUKnot(knot_u[i], 1, kn_tol)

        for i in range(0, len(knot_v)):
            # if knot_v[i+1] > knot_v[i]:
            bs.insertVKnot(knot_v[i], 1, kn_tol)

        if debug:
            print("Knots after knots insertion")
            # knot_u and knot_v are not affected.
            print(f"bs.NbUKnots: {bs.NbUKnots}")
            print(f"bs.NbVKnots: {bs.NbVKnots}")

        if debug:
            print(f"Dim nodes U:{o_nNo_u} V:{o_nNo_v}")
            print(f"Len coor: {len(coor)}")
            print(f"bs.NbUPoles: {bs.NbUPoles}")
            print(f"bs.NbUPoles: {bs.NbVPoles}")

            if dbg_lists:
                print(f"bs.getUKnots: {bs.getUKnots()}")
                print(f"bs.getVKnots: {bs.getVKnots()}")
                print(f"bs.getUMults: {bs.getUMultiplicities()}")
                print(f"bs.getVMults: {bs.getVMultiplicities()}")

        if debug:
            t = bs.getPoles()
            print("shape poles", len(t), len(t[0]))

        if obj.model == "NurbsSurface":
            print("Nurbs surface !!!")
            poles2 = np.array(coor).reshape(o_nNo_u, o_nNo_v, 3)

            ku = [1.0 / (o_nNo_u - 1) * i for i in range(o_nNo_u)]
            kv = [1.0 / (o_nNo_v - 1) * i for i in range(o_nNo_v)]
            mu = [3] + [1] * (o_nNo_u - 2) + [3]
            mv = [3] + [1] * (o_nNo_v - 2) + [3]

            w_num = o_nNo_v * (o_nNo_u - 1)
            wgs = [1.0 for i in range(w_num)]
            # np.ones(nNodes_v * (nNodes_u - 1)).tolist()

        elif obj.model in ("NurbsSphere", "NurbsCylinder"):
            # poles position swapped v,u instead of u,v in microelly calls
            poles2 = np.array(coor).reshape(o_nNo_u, o_nNo_v, 3)

            kv = [1.0 / (o_nNo_v - 1) * i for i in range(o_nNo_v)]
            ku = [1.0 / (o_nNo_u - 1) * i for i in range(o_nNo_u)]

            mu = [3] + [1] * (o_nNo_u - 2) + [3]
            mv = [3] + [1] * (o_nNo_v - 2) + [3]

            # weights
            w_num = o_nNo_v * (o_nNo_u - 1)
            wgs = [1.0 for i in range(w_num)]
            # np.ones(nNodes_v * (nNodes_u - 1)).tolist()

            # microelly definition
            # bs.buildFromPolesMultsKnots(poles2,
            #    [3] + [1] * (nNodes_v - 2) + [3],
            #    [2] + [1] * (nNodes_u - 2) + [2],
            #    kv,ku, False, True, 3, 3,
            #    1.0 * np.ones(nNodes_v * (nNodes_u - 1)),)

        elif obj.model == "NurbsTorus":
            # 7 x 4 array
            coor = [
                # line 1
                [20.0, 0, -40], [60, 0, -40], [30, 0, 50], [0, 0, -40],
                [20, 10, -40], [40, 10, -40], [40, 10, 55],
                # line 2
                [0, 10, -40], [20, 15, -40], [65, 15, -40], [60, 15, 75],
                [35, 15, -40], [0, 20, 10], [0, 40, 20],
                # line 3
                [0, 45, 65], [0, 20, 20], [-20, 0, 0], [-40, 0, 20],
                [-70, 0, 75], [-20, 0, 40], [-30, -10, 5],
                # line 4
                [-40, -10, 20], [-40, -10, 55], [-20, -20, 40], [5, -20, 5],
                [0, -40, 30], [0, -45, 65], [5, -20, 10],
            ]

            tt = 10 * np.array(coor)

            poles2 = tt.reshape(7, 4, 3)

            ku = [0, 0.2, 0.4, 0.5, 0.7, 0.8, 1]
            kv = [0, 0.4, 0.6, 1]
            mu = [2, 1, 1, 1, 1, 1, 2]
            mv = [0, 0.4, 0.6, 1]
            w_num = o_nNo_v * (o_nNo_u - 1)
            wgs = [1.0 for i in range(w_num)]
            # np.ones(nNodes_v * (nNodes_u - 1)).tolist()

            # microelly definition see the u and v inverted
            """
            bs.buildFromPolesMultsKnots(
                poles2,
                [2, 1, 1, 1, 1, 1, 2],
                [2, 1, 1, 2],
                [0, 0.2, 0.4, 0.5, 0.7, 0.8, 1],
                [0, 0.4, 0.6, 1],
                True,
                True,
                3,
                3,
                # 1.0 * np.ones(28),
            )
            """

        # TODO: check this code commented out by microelly
        """
        else:
            i=0
            for jj in range(0,nNodes_v):
                for ii in range(0,nNodes_u):

                    try:
                        #print("getpole",bs.getPole(jj+1,ii+1))
                        bs.setPole(jj+1,ii+1,FreeCAD.Vector((coor[i][0],coor[i][1],coor[i][2])),weights[jj,ii])
                        bs.setWeight(jj+1,ii+1,4)
                        # print i,FreeCAD.Vector((coor[i][0],coor[i][1],coor[i][2]))
                        print([ii+1,jj+1,FreeCAD.Vector((coor[i][0],coor[i][1],coor[i][2])),weights[jj,ii]])
                    except:
                            print([ii+1,jj+1,FreeCAD.Vector((coor[i][0],coor[i][1],coor[i][2])),weights[jj,ii]])

                            sayexc("error setPols ii,jj:"+str([ii+1,jj+1]))
                            print("getpole exc reverse --",bs.getPole(jj+1,ii+1))
                            print("getpole exc --",bs.getPole(ii+1,jj+1))
                    i=i+1;
        """

        if debug:
            print(f"poles2 ({len(poles2)}) shape: {poles2.shape}")
            # print(f"poles2 : {poles2}")
            print(f"mu ({len(mu)}): {mu}")
            print(f"mv ({len(mv)}): {mv}")
            print(f"ku ({len(ku)}): {ku}")
            print(f"kv ({len(kv)}): {kv}")
            print(f"U nodes: {o_nNo_u}")
            print(f"V nodes: {o_nNo_v}")
            print(f"Weights: ({len(wgs)}) : {wgs}")

        # NOTE: Part.BSplineSurface.buildFromPolesMultsKnots
        # Args:
        #   poles (sequence of sequence of Base.Vector),
        #   umults, vmults,
        #   uknots, vknots,
        #   uperiodic, vperiodic,
        #   udegree, vdegree,
        #   weights (sequence of sequence of float)

        # FIXME:
        #       - Weights are not correct see why
        #       - Check all occurencies of buildFromPolesMultsKnots as
        #         parameters are swapped

        bs.buildFromPolesMultsKnots(
            poles2, mu, mv, ku, kv, False, False, 3, 3)  # , wgs)

        # -----------------------------------------
        # --- Assign poles (and weight) to obj
        # -----------------------------------------

        # TODO: assign calculated poles to obj.poles
        # FIXME: Seems to be not working flawlessy as modifying
        #     stepU will not result is a correct operation.
        #     it prints "prop: stepU except executed"

        obj.poles = np.array2string(
            poles2, precision=10, separator=',')

        # ----------------------------------------
        # -- create aux parts
        # ----------------------------------------

        # Solid

        if obj.solid:
            obj.Shape = self.create_solid(bs)
        else:
            if FreeCAD.ParamGet("User parameter:Plugins/nurbs").GetBool(
                "createNurbsShape", True
            ):
                obj.Shape = bs.toShape()

        # Grids

        # vis = False
        vis = True

        if obj.grid:
            if obj.gridobj is not None:
                vis = obj.gridobj.ViewObject.Visibility
                FreeCAD.ActiveDocument.removeObject(obj.gridobj.Name)
            obj.gridobj = self.create_grid(bs, obj.gridCount)
            obj.gridobj.Label = "Nurbs Grid"
            obj.gridobj.ViewObject.Visibility = vis

        if 0 and obj.base:
            # create the socket box
            mx = np.array(coor).reshape(o_nNo_v, o_nNo_u, 3)
            print("create box")

            print((mx.shape))
            a0 = tuple(mx[0, 0])
            b0 = tuple(mx[0, -1])
            c0 = tuple(mx[-1, -1])
            d0 = tuple(mx[-1, 0])
            bh = obj.baseHeight

            a = tuple(mx[0, 0] + [0, 0, -bh])
            b = tuple(mx[0, -1] + [0, 0, -bh])
            c = tuple(mx[-1, -1] + [0, 0, -bh])
            d = tuple(mx[-1, 0] + [0, 0, -bh])
            print((a, b, c, d))

            lls = [
                Part.makeLine(a0, b0),
                Part.makeLine(b0, b),
                Part.makeLine(b, a),
                Part.makeLine(a, a0),
            ]
            fab = Part.makeFilledFace(lls)
            lls = [
                Part.makeLine(b0, c0),
                Part.makeLine(c0, c),
                Part.makeLine(c, b),
                Part.makeLine(b, b0),
            ]
            fbc = Part.makeFilledFace(lls)
            lls = [
                Part.makeLine(c0, d0),
                Part.makeLine(d0, d),
                Part.makeLine(d, c),
                Part.makeLine(c, c0),
            ]
            fcd = Part.makeFilledFace(lls)
            lls = [
                Part.makeLine(d0, a0),
                Part.makeLine(a0, a),
                Part.makeLine(a, d),
                Part.makeLine(d, d0),
            ]
            fda = Part.makeFilledFace(lls)
            lls = [
                Part.makeLine(a, b),
                Part.makeLine(b, c),
                Part.makeLine(c, d),
                Part.makeLine(d, a),
            ]
            ff = Part.makeFilledFace(lls)

            surf = bs.toShape()
            fs = [fab, fbc, fcd, fda, ff, surf]
            comp = Part.makeCompound(fs)
            Part.show(comp)
            FreeCAD.ActiveDocument.ActiveObject.Label = "Nurbs with Base"

            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.recompute()

            # bottom face ...
            cur = FreeCAD.ActiveDocument.ActiveObject
            s1 = cur.Shape
            FreeCAD.ActiveDocument.removeObject(cur.Name)

            # solid ...
            s = Part.makeShell([s1, bs.toShape()])

            s = Part.makeShell(fs)

            sol = Part.makeSolid(s)
            #           Part.show(sol)
            obj.Shape = sol

        # create a pole grid with spines

        # vis = False
        vis = True

        try:
            vis = obj.polgrid.ViewObject.Visibility
            FreeCAD.ActiveDocument.removeObject(obj.polgrid.Name)
        except:
            pass

        obj.polgrid = self.create_uv_grid()
        obj.polgrid.Label = "Pole Grid"
        obj.polgrid.ViewObject.Visibility = vis

        nurbstime = time.time()

        print("XB")

        polesobj = None
        comptime = time.time()

        print(f"Obj polpoints: {obj.polpoints}")

        if obj.polpoints:
            # create the poles for visualization
            # the pole point cloud
            pts = [FreeCAD.Vector(tuple(c)) for c in coor]
            vts = [Part.Vertex(pp) for pp in pts]

            # and the surface

            # vts.append(obj.Shape)
            comp = Part.makeCompound(vts)
            comptime = time.time()
            try:
                yy = FreeCAD.ActiveDocument.Poles
            except:
                yy = FreeCAD.ActiveDocument.addObject("Part::Feature", "Poles")

            yy.Shape = comp
            polesobj = FreeCAD.ActiveDocument.ActiveObject

        endtime = time.time()

        print(
            (
                "create nurbs components, surface time ",
                round(nurbstime - starttime, 2),
                round(comptime - nurbstime, 2),
                round(endtime - comptime, 2),
            )
        )

        return polesobj

    @staticmethod
    def _set_degree(obj, uc, vc):
        """Set obj degree based on knot_u and jnot_v.

        made to reduce complexity of createSurface.
        """
        #
        if obj.degree_u == 1:
            l = [1.0 / (uc - 1) * i for i in range(uc)]
            obj.knot_u = [0] + l + [1]
        elif obj.degree_u == 1:
            l = [1.0 / (uc - 2) * i for i in range(uc - 1)]
            obj.knot_u = [0, 0] + l + [1, 1]
        elif obj.degree_u == 3:
            l = [1.0 / (uc - 3) * i for i in range(uc - 2)]
            obj.knot_u = [0, 0, 0] + l + [1, 1, 1]
        else:
            print("obj_degree_u is > 3")

        if obj.degree_v == 1:
            l = [1.0 / (vc - 1) * i for i in range(vc)]
            obj.knot_v = [0] + l + [1]
        elif obj.degree_v == 2:
            l = [1.0 / (vc - 2) * i for i in range(vc - 1)]
            obj.knot_v = [0, 0] + l + [1, 1]
        elif obj.degree_v == 3:
            l = [1.0 / (vc - 3) * i for i in range(vc - 2)]
            obj.knot_v = [0, 0, 0] + l + [1, 1, 1]
        else:
            print("obj_degree_v is > 3")

        return obj.knot_u, obj.knot_v

    def getBS(self):
        """Docstring missing."""
        try:
            rc = self.bs
        except:
            print("BSpline nicht mehr vorhanden, muss neu berechnet werden ....")
            # uc = self.obj2.nNodes_v
            # vc = self.obj2.nNodes_u
            self.createSurface(self.obj2, self.obj2.poles)
            rc = self.bs
        return rc

    def getPoints(self):
        """Get point set for grid."""
        #
        if self.obj2.generatePoles:
            ps = []
            vc = self.obj2.nNodes_v
            uc = self.obj2.nNodes_u
            for v in range(vc):
                for u in range(uc):
                    ps.append(
                        FreeCAD.Vector(u * self.obj2.stepU, v * self.obj2.stepV, 0)
                    )
            return ps
        else:
            print("------ GetPoints ------")
            t = eval(str(self.obj2.poles))
            print(t)
            print("-------------------------")
            return eval(t[0])

    def togrid(self, ps):
        """Return points to 2D grid."""
        self.grid = None
        self.g = np.array(ps).reshape(self.obj2.nNodes_v, self.obj2.nNodes_u, 3)
        return self.g

    def showGriduv(self):
        """Recompute and show the Pole grid."""
        #
        starttime = time.time()
        gg = self.g

        try:
            if not self.calculatePoleGrid:
                return
        except:
            return

        ls = []
        uc = self.obj2.nNodes_v
        vc = self.obj2.nNodes_u

        # straight line grid
        for u in range(uc):
            for v in range(vc):
                if u < uc - 1:
                    ls.append(Part.makeLine(tuple(gg[u][v]), tuple(gg[u + 1][v])))
                if v < vc - 1:
                    ls.append(Part.makeLine(tuple(gg[u][v]), tuple(gg[u][v + 1])))

        comp = Part.makeCompound(ls)

        if self.grid is not None:
            self.grid.Shape = comp
        else:
            gdo = Part.show(comp)
            gdo.ViewObject.hide()

            self.grid = gdo
            self.grid.Label = "Pole Grid"

        FreeCAD.activeDocument().recompute()
        FreeCADGui.updateGui()
        endtime = time.time()
        print(("create PoleGrid time", endtime - starttime))

    def setpointZ(self, u, v, h=0, w=20):
        """Set height and weight of a pole point."""
        #
        # FIXME: why thi inversion here?
        u, v = v, u
        # self.g[v][u][2]=h
        self.g[v][u][2] = 100 * np.tan(0.5 * np.pi * h / 101)
        try:
            wl = self.obj2.weights
            wl[v * self.obj2.nNodes_u + u] = w
            self.obj2.weights = wl
        except:
            print()

    def setpointRelativeZ(self, u, v, h=0, w=0, update=False):
        """Set relative height and weight of a pole point."""
        #
        u, v = v, u
        # self.g[v][u][2] = self.gBase[v][u][2] + h
        # unrestricted
        self.g[v][u][2] = self.gBase[v][u][2] + 100 * np.tan(0.5 * np.pi * h / 101)
        print(f"set  rel h {h}, height {self.g[v][u][2]}")

        if update:
            self.gBase = self.g.copy()

        try:
            wl = self.obj2.weights
            wl[v * self.obj2.nNodes_u + u] = w
            self.obj2.weights = wl
        except:
            print()

    def movePoint(self, u, v, dx, dy, dz):
        """Move relative to a pole point."""
        #
        FreeCAD.ActiveDocument.openTransaction(f"move Point {str((u, v, dx, dy, dz))}")
        # EDITED : g is
        self.g[v][u][0] += dx
        self.g[v][u][1] += dy
        self.g[v][u][2] += dz

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def elevateUline(self, vp, height=40):
        """Change the height of all poles with the same u value."""
        #
        FreeCAD.ActiveDocument.openTransaction("elevate ULine" + str([vp, height]))

        uc = self.obj2.nNodes_u
        # vc = self.obj2.nNodes_v

        for i in range(1, uc - 1):
            self.g[vp][i][2] = height

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def elevateVline(self, vp, height=40):
        """Change height of all poles with the same v value."""
        # FIXME: why here is commented the transaction and above not?

        # FreeCAD.ActiveDocument.openTransaction("elevate VLine" + str([vp,height]))

        # TODO: See why these variables are present here
        # uc = self.obj2.nNodes_u

        vc = self.obj2.nNodes_v

        for i in range(1, vc - 1):
            self.g[i][vp][2] = height

        # self.updatePoles()
        # self.showGriduv()
        # FreeCAD.ActiveDocument.commitTransaction()

    def elevateRectangle(self, v, u, dv, du, height=50):
        """Change height of all poles inside a pole grid rectangle."""
        #
        FreeCAD.ActiveDocument.openTransaction(
            "elevate rectangle " + str((u, v, dv, du, height))
        )

        # TODO: See why these variables are present here
        # uc = self.obj2.nNodes_u
        # vc = self.obj2.nNodes_v

        for iv in range(v, v + dv + 1):
            for iu in range(u, u + du + 1):
                try:
                    self.g[iu][iv][2] = height
                except:
                    pass

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def elevateCircle(self, u=20, v=30, radius=10, height=60):
        """Change the height for poles around a central pole."""
        #
        FreeCAD.ActiveDocument.openTransaction(
            "elevate Circle " + str((u, v, radius, height))
        )

        uc = self.obj2.nNodes_u
        vc = self.obj2.nNodes_v

        g = self.g
        for iv in range(vc):
            for iu in range(uc):
                try:
                    if (g[iu][iv][0] - g[u][v][0]) ** 2 + (
                            g[iu][iv][1] - g[u][v][1]) ** 2 <= radius**2:

                        g[iu][iv][2] = height
                except:
                    pass
        self.g = g

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def elevateCircle2(self, u=20, v=30, radius=10, height=60):
        """Change the height for poles around a cenral pole."""
        #
        FreeCAD.ActiveDocument.openTransaction(
            "elevate Circle " + str((u, v, radius, height))
        )

        # TODO: See why these variables are present here
        # uc = self.obj2.nNodes_u
        # vc = self.obj2.nNodes_v

        g = self.g

        for iv in range(v - radius, v + radius + 1):
            for iu in range(u - radius, u + radius + 1):
                try:
                    g[iu][iv][2] = height
                except:
                    pass
        self.g = g

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def createWaves(self, height=10, depth=-5):
        """Crate wave pattern over all."""
        #
        FreeCAD.ActiveDocument.openTransaction("create waves " + str((height, depth)))

        uc = self.obj2.nNodes_u
        vc = self.obj2.nNodes_v

        for iv in range(1, vc - 1):
            for iu in range(1, uc - 1):
                if (iv + iu) % 2 == 0:
                    self.g[iu][iv][2] = height
                else:
                    self.g[iu][iv][2] = depth

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def addUline(self, vp, pos=0.5):
        """Insert a line of poles after vp, pos is relative to the next Uline."""
        # FIXME: check why the code is commented out

        FreeCAD.ActiveDocument.openTransaction("add ULine " + str((vp, pos)))

        # TODO: See why these variables are present here
        # uc = self.obj2.nNodes_u
        # -vc = self.obj2.nNodes_v

        if pos <= 0:
            pos = 0.00001
        if pos >= 1:
            pos = 1 - 0.00001
        pos = 1 - pos

        g = self.g

        """
        vline = []
        for i in range(uc):
            vline.append(
                [
                    (g[vp - 1][i][0] + g[vp][i][0]) / 2,
                    (g[vp - 1][i][1] + g[vp][i][1]) / 2,
                    0,
                ]
            )  # (g[vp-1][i][2]+g[vp][i][2])/2

        vline = []
        for i in range(uc):
            vline.append(
                [
                    (pos * g[vp - 1][i][0] + (1 - pos) * g[vp][i][0]),
                    (pos * g[vp - 1][i][1] + (1 - pos) * g[vp][i][1]),
                    0,
                ]
            )  # (g[vp-1][i][2]+g[vp][i][2])/2
        """

        vline = np.array(vline)

        gg = np.concatenate((g[:vp], [vline], g[vp:]))
        self.g = gg

        self.obj2.nNodes_v += 1

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def addVline(self, vp, pos=0.5):
        """Insert a line of poles after vp, pos is relative to the next Vline."""
        # FreeCAD.ActiveDocument.openTransaction("add Vline " + str((vp,pos)))

        # uc = self.obj2.nNodes_u
        vc = self.obj2.nNodes_v

        if pos <= 0:
            pos = 0.00001
        if pos >= 1:
            pos = 1 - 0.00001
        pos = 1 - pos

        g = self.g
        g = g.swapaxes(0, 1)

        vline = []
        for i in range(vc):
            vline.append(
                [
                    (pos * g[vp - 1][i][0] + (1 - pos) * g[vp][i][0]),
                    (pos * g[vp - 1][i][1] + (1 - pos) * g[vp][i][1]),
                    0,
                ]
            )  # (g[vp-1][i][2]+g[vp][i][2])/2

        vline = np.array(vline)

        gg = np.concatenate((g[:vp], [vline], g[vp:]))
        gg = gg.swapaxes(0, 1)
        self.g = gg

        self.obj2.nNodes_u += 1

        self.updatePoles()
        self.showGriduv()
        # FreeCAD.ActiveDocument.commitTransaction()

    def addS(self, vp):
        """Add harte kante links, weicher uebergang, harte kante rechts."""
        #
        FreeCAD.ActiveDocument.openTransaction("add vertical S " + str(vp))

        # uc = self.obj2.nNodes_u
        vc = self.obj2.nNodes_v

        g = self.g
        g = g.swapaxes(0, 1)

        vline = []
        for i in range(vc):
            pos = 0.5
            if i < 0.3 * vc:
                pos = 0.0001
            if i > 0.6 * vc:
                pos = 0.9999

            vline.append(
                [
                    (pos * g[vp - 1][i][0] + (1 - pos) * g[vp][i][0]),
                    (pos * g[vp - 1][i][1] + (1 - pos) * g[vp][i][1]),
                    (pos * g[vp - 1][i][2] + (1 - pos) * g[vp][i][2]),
                ]
            )

        vline = np.array(vline)

        gg = np.concatenate((g[:vp], [vline], g[vp:]))

        self.g = gg.swapaxes(0, 1)
        self.obj2.nNodes_u += 1

        self.updatePoles()
        self.showGriduv()
        FreeCAD.ActiveDocument.commitTransaction()

    def updatePoles(self):
        """Recompute polestring and recompute surface."""
        # FIXME: something is wrong here
        uc = self.obj2.nNodes_u
        vc = self.obj2.nNodes_v

        ll = ""

        print(f"--- updatePoles -------------- : {self.g}")

        gf = self.g.reshape(uc * vc, 3)  # wrong?

        print(f"GF: {gf}")

        for i in gf:
            ll += f"{str(list(i))}, "

        ll = f"[{ll}]"

        print(f"LL: {ll}")

        self.obj2.poles = ll
        # self.onChanged(self.obj2,"Height")
        self.update(self.obj2)

    def showSelection(self, pole1, pole2):
        """Show pole grid."""
        try:
            print(("delete ", self.obj2.polselection.Name))
            FreeCAD.ActiveDocument.removeObject(self.obj2.polselection.Name)
        except:
            pass

        print((pole1, pole2))
        [u1, v1] = pole1
        [u2, v2] = pole2

        if u1 > u2:
            u1, u2 = u2, u1
        if v1 > v2:
            v1, v2 = v2, v1

        pts = []

        for u in range(u1, u2 + 1):
            for v in range(v1, v2 + 1):
                # print(u,v, self.bs.getPole(u+1,v+1))
                pts.append(Part.Vertex(self.bs.getPole(u + 1, v + 1)))

        com = Part.Compound(pts)
        pols = Part.show(com)
        pols.Label = "Poles Selection"
        pols.ViewObject.PointSize = 8
        pols.ViewObject.PointColor = (1.0, 1.0, 0.0)
        self.obj2.polselection = pols


def makeNurbs(uc=5, vc=7):
    """Docstring missing."""
    do = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Nurbs")
    do.Label = "Nurbs generated"

    Nurbs(do, uc, vc)

    VP_NurbsObj(do.ViewObject)

    do.ViewObject.ShapeColor = (0.00, 1.00, 1.00)
    do.ViewObject.Transparency = 50

    return do


def nurbs_set_polestring():
    """Create a polestring to put on Obj.poles property."""
    pass


def nurbs_get_poles():
    """Create an array from Obj.poles property."""
    pass


# --- Examples and tests


def createnurbs():
    """Docstring missing."""
    nobj = makeNurbs(6, 10)
    nobj.solid = False
    nobj.base = False
    # nobj.grid=False

    polestring = """[
    [0.0, 0.0, 0.0], [40.0, 0.0, 0.0], [80.0, 0.0, 0.0], [120.0, 0.0, 0.0],
    [160.0, 0.0, 0.0], [200.0, 0.0, 0.0], [0.0, 30.0, 0.0], [40.0, 30.0, 0.0],
    [80.0, 30.0, 0.0], [120.0, 30.0, 0.0], [160.0, 30.0, -60.0], [200.0, 30.0, 0.0],
    [0.0, 60.0, 0.0], [40.0, 60.0, 0.0], [80.0, 60.0, 0.0], [120.0, 60.0, -60.0],
    [160.0, 60.0, -60.0], [200.0, 60.0, 0.0], [0.0, 90.0, 0.0], [40.0, 90.0, 0.0],
    [80.0, 90.0, 0.0], [120.0, 90.0, 0.0], [160.0, 90.0, 0.0], [200.0, 90.0, 0.0],
    [0.0, 120.0, 0.0], [40.0, 120.0, 0.0], [80.0, 120.0, 0.0], [120.0, 120.0, 0.0],
    [160.0, 120.0, 0.0], [200.0, 120.0, 0.0], [0.0, 150.0, 0.0], [40.0, 150.0, 0.0],
    [80.0, 150.0, 100.0], [120.0, 150.0, 100.0], [160.0, 150.0, 80.0],
    [200.0, 150.0, 0.0], [0.0, 180.0, 0.0], [40.0, 180.0, 0.0], [80.0, 180.0, 0.0],
    [120.0, 180.0, 100.0], [160.0, 180.0, 80.0], [200.0, 180.0, 0.0],
    [0.0, 210.0, 0.0], [40.0, 210.0, 100.0], [80.0, 210.0, 0.0], [120.0, 210.0, 0.0],
    [160.0, 210.0, 0.0], [200.0, 210.0, 0.0], [0.0, 240.0, 0.0], [40.0, 240.0,0.0],
    [80.0, 240.0, 0.0], [120.0, 240.0, 0.0], [160.0, 240.0, 0.0],
    [200.0, 240.0, 0.0], [0.0, 270.0, 0.0], [40.0, 270.0, 0.0], [80.0, 270.0, 0.0],
    [120.0, 270.0, 0.0], [160.0, 270.0, 0.0], [200.0, 270.0, 0.0]]"""

    polarr = eval(polestring)

    ps = [FreeCAD.Vector(tuple(v)) for v in polarr]

    nobj.poles = polestring
    # ps = nobj.Proxy.getPoints()

    nobj.Proxy.togrid(ps)
    nobj.Proxy.updatePoles()
    nobj.Proxy.showGriduv()

    FreeCAD.activeDocument().recompute()
    FreeCADGui.updateGui()

    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")

    nobj.ViewObject.startEditing()
    nobj.ViewObject.finishEditing()
    nobj.polselection.ViewObject.hide()


def testRandomB():
    """Docstring missing."""
    nd = FreeCAD.newDocument("Unnamed")
    FreeCAD.setActiveDocument(nd.Name)
    FreeCAD.ActiveDocument = FreeCAD.getDocument(nd.Name)
    FreeCADGui.ActiveDocument = FreeCADGui.getDocument(nd.Name)

    na = 20
    b = 10

    nobj = makeNurbs(b, na)

    nobj.solid = False
    nobj.base = False
    # nobj.grid=False
    nobj.gridCount = 6

    ps = nobj.Proxy.getPoints()

    ps = np.array(ps)
    ps.resize(na, b, 3)

    for k0 in range(10):
        k = random.randint(0, na - 6)
        l = random.randint(1, b - 1)

        for j in range(3):
            ps[k + j][l][2] += 60

        rj = random.randint(0, 2)

        print((k, rj))

        for j in range(rj):
            ps[k + 3 + j][l][2] += 60

    for k0 in range(10):
        k = random.randint(0, na - 5)
        l = random.randint(1, b - 1)

        for j in range(2):
            ps[k + j][l][2] += 30

        rj = random.randint(0, 2)

        print((k, rj))

        for j in range(rj):
            ps[k + 2 + j][l][2] += 30

    ps.resize(na * b, 3)

    nobj.Proxy.togrid(ps)
    nobj.Proxy.elevateVline(2, 0)

    nobj.Proxy.updatePoles()
    nobj.Proxy.showGriduv()

    # FreeCAD.a = nobj
    # FreeCAD.ps = ps

    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")


def testCylinder(def_name=None, c_rand=True, suffix=None, clean_doc=True):
    """Create a Nurbs cylindrical surface for testing.

    Args:
        def_name (string): document name. Defaults to None.
        c_rand (bool): insert random noise. Defaults to True.
        suffix (string): add a suffix to document name. Defaults to None.
        clean_doc (bool): clean document content. Defaults to True.

    Note:
        FIXME: something is not working in recompute.
    """
    #
    if def_name is None:
        def_name = "Nurbs_TestCylinder"

    if suffix is None:
        doc_name = f"{def_name}"
    else:
        doc_name = f"{def_name}_{suffix}"

    if clean_doc is True:
        cl_f = 2
    else:
        cl_f = 0

    out_doc = ensure_document(doc_name, cl_f)

    dest_doc = FreeCAD.activeDocument()

    FreeCAD.setActiveDocument(out_doc)

    print("--- Test Random Cylinder ---")

    uc = 10  # 30
    vc = 10  # 30
    pass1 = 25
    pass2 = 10

    nobj = makeNurbs(uc, vc)
    nobj.model = "NurbsCylinder"

    nobj.solid = False
    nobj.base = False
    # nobj.generatePoles # False # create error
    # nobj.grid = False
    nobj.gridCount = 20

    pps = nobj.Proxy.getPoints()

    # print(f"points: {len(pps)}")

    ps = np.array(pps)
    ps.resize(uc, vc, 3)

    # modified retrieving of ps using numpy indexing
    if c_rand is True:
        for k0 in range(pass1):
            k = random.randint(0, uc - 3)
            l = random.randint(1, vc - 1)

            for j in range(1):
                ps[k + j, l, 2] += 100 * random.random()

            rj = random.randint(0, 1)

            print(f"Trc (k, rj): {k},  {rj}")

            for j in range(rj):
                ps[k + j, l, 2] += 100 * random.random()

        # print(f"len2 ps: {len(ps)}")

        # second loop
        for k0 in range(pass2):
            k = random.randint(0, uc - 3)
            l = random.randint(1, vc - 1)

            for j in range(1):
                ps[k + j, l, 2] += 200 * random.random()

            rj = random.randint(0, 1)

            print(f"Trc (k, rj): {k},  {rj}")

            for j in range(rj):
                ps[k + j, l, 2] += 200 * random.random()

        print(f"len3 ps: {len(ps)}")
        # print(f"Trc ps: {ps}")

    ps.resize(uc * vc, 3)

    print(f"len4 ps: {len(ps)}")
    FreeCADGui.updateGui()

    nobj.Proxy.togrid(ps)
    #   nobj.Proxy.elevateVline(2,0)

    nobj.Proxy.updatePoles()

    nobj.Proxy.showGriduv()

    # why these variables?
    # FreeCAD.a = a
    # FreeCAD.ps = ps

    dest_doc.recompute()
    setview(out_doc, 1)


def testSphere(def_name=None, c_rand=True, suffix=None, clean_doc=True):
    """Create a Nurbs spherical surface for testing.

    Args:
        def_name (string): document name. Defaults to None
        c_rand (bool): insert random noise. Defaults to True
        suffix (string): add a suffix to document name. Defaults to None
        clean_doc (bool): clean document content. Defaults to True.
    """
    #
    if def_name is None:
        def_name = "Nurbs_TestSphere"

    if suffix is None:
        doc_name = f"{def_name}"
    else:
        doc_name = f"{def_name}_{suffix}"

    if clean_doc is True:
        cl_f = 2
    else:
        cl_f = 0

    out_doc = ensure_document(doc_name, cl_f)

    dest_doc = FreeCAD.activeDocument()

    FreeCAD.setActiveDocument(out_doc)

    print("--- Test Sphere ---")

    # FreeCAD.ParamGet('User parameter:Plugins/nurbs').SetBool("createNurbsShape",True)

    # for larger tests
    # FreeCAD.ParamGet('User parameter:Plugins/nurbs').SetBool("createNurbsShape",False)

    # na = FreeCAD.ParamGet("User parameter:Plugins/nurbs/randomSphere").GetInt(
    #    "countLatitude", 100)

    # b = FreeCAD.ParamGet("User parameter:Plugins/nurbs/randomSphere").GetInt(
    #     "countLongitude", 100)

    # pass1 = FreeCAD.ParamGet("User parameter:Plugins/nurbs/randomSphere").GetInt(
    #    "countRandom1", 100) #

    # pass2 = FreeCAD.ParamGet("User parameter:Plugins/nurbs/randomSphere").GetInt(
    #     "countRandom2", 100)

    # fixed values for test
    uc = 15
    vc = 15

    pass1 = 15
    pass2 = 10

    nobj = makeNurbs(uc, vc)
    nobj.model = "NurbsSphere"

    nobj.solid = False
    nobj.base = False
    # nobj.grid=False

    # nobj.gridCount=1000

    pps = nobj.Proxy.getPoints()

    ps = np.array(pps)
    ps.resize(uc, vc, 3)

    for k0 in range(pass1):
        k = random.randint(2, uc - 3)
        l = random.randint(1, vc - 1)

        for j in range(1):
            ps[k + j][l][2] += 1 * random.random()

        rj = random.randint(0, 1)

        #       print(k,rj)

        for j in range(rj):
            ps[k + j][l][2] += 1 * random.random()

        if k0 % 1000 == 0:
            print(k0)
            FreeCADGui.updateGui()

    for k0 in range(pass2):
        k = random.randint(2, uc - 3)
        l = random.randint(1, vc - 1)

        for j in range(1):
            ps[k + j][l][2] += 2 * random.random()

        rj = random.randint(0, 1)

        # print(k,rj)

        for j in range(rj):
            ps[k + j][l][2] += 2 * random.random()

        if k0 % 1000 == 0:
            print(k0)
            FreeCADGui.updateGui()

    ps.resize(vc * uc, 3)

    print("A")
    print((time.time()))
    FreeCADGui.updateGui()

    nobj.Proxy.togrid(ps)
    print("B")
    print((time.time()))
    FreeCADGui.updateGui()

    #   a.Proxy.elevateVline(2,0)

    nobj.Proxy.updatePoles()

    print("c")
    print((time.time()))
    FreeCADGui.updateGui()
    nobj.Proxy.showGriduv()
    print("d")
    print((time.time()))
    FreeCADGui.updateGui()

    FreeCAD.ActiveDocument.recompute()
    FreeCAD.ActiveDocument.recompute()

    # FreeCAD.a = a
    # FreeCAD.ps = ps

    dest_doc.recompute()
    setview(out_doc, 1)


def testTorus(def_name=None, c_rand=True, suffix=None, clean_doc=True):
    """Create a Nurbs toroidal surface for testing.

    Args:
        def_name (string): document name. Defaults to None
        c_rand (bool): insert random noise. Defaults to True
        suffix (string): add a suffix to document name. Defaults to None
        clean_doc (bool): clean document content. Defaults to True.
    """
    #
    if def_name is None:
        def_name = "Nurbs_TestTorus"

    if suffix is None:
        doc_name = f"{def_name}"
    else:
        doc_name = f"{def_name}_{suffix}"

    if clean_doc is True:
        cl_f = 2
    else:
        cl_f = 0

    out_doc = ensure_document(doc_name, cl_f)

    dest_doc = FreeCAD.activeDocument()

    FreeCAD.setActiveDocument(out_doc)
    #
    uc = 7
    vc = 4

    nobj = makeNurbs(uc, vc)
    nobj.model = "NurbsTorus"

    nobj.solid = False
    nobj.base = False
    # nobj.grid=False
    nobj.gridCount = 20

    pps = nobj.Proxy.getPoints()

    print("points pps", len(pps))

    ps = np.array(pps)

    ps.resize(uc, vc, 3)

    for k0 in range(15):
        k = random.randint(2, uc - 3)
        l = random.randint(1, vc - 1)
        for j in range(1):
            ps[k + j][l][2] += 100 * random.random()

        rj = random.randint(0, 1)

        print(k, rj)

        for j in range(rj):
            ps[k + j][l][2] += 100 * random.random()

    for k0 in range(10):
        k = random.randint(2, uc - 3)
        l = random.randint(1, vc - 1)

        for j in range(1):
            ps[k + j][l][2] += 200 * random.random()

        rj = random.randint(0, 1)

        print(k, rj)

        for j in range(rj):
            ps[k + j][l][2] += 200 * random.random()

    ps.resize(uc * vc, 3)

    print("A")
    print((time.time()))

    FreeCADGui.updateGui()

    nobj.Proxy.togrid(ps)
    print("B")
    print((time.time()))
    FreeCADGui.updateGui()

    # nobj.Proxy.elevateVline(2,0)

    nobj.Proxy.updatePoles()

    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")


def runtest():
    """Docstring missing."""
    # TODO: use ensure_document()
    try:
        FreeCAD.closeDocument("Unnamed")
    except:
        pass

    if FreeCAD.ActiveDocument is None:
        FreeCAD.newDocument("Unnamed")
        FreeCAD.setActiveDocument("Unnamed")
        FreeCAD.ActiveDocument = FreeCAD.getDocument("Unnamed")
        FreeCADGui.ActiveDocument = FreeCADGui.getDocument("Unnamed")

    vc = 10
    uc = 10

    nobj = makeNurbs(uc, vc)

    nobj.solid = False
    nobj.base = False
    ps = nobj.Proxy.getPoints()
    nobj.Proxy.togrid(ps)
    nobj.Proxy.updatePoles()
    nobj.Proxy.showGriduv()

    # dest_doc.recompute()
    # setview(out_doc, 1)


def runtcn():
    """Run test cylinder with noise."""
    testCylinder(None, True, "noisy", False)


def runtcp():
    """Run test cylinder without noise."""
    testCylinder(None, False, "plain", False)


def runtest2():
    """Docstring missing."""
    # testRandomB()  # OK
    # Cylinder with random noise
    #testCylinder(None, True, "noisy", False)  # OK
    # Cylinder without noise.
    # testCylinder(None, False, "plain", True)  # OK
    # Test sphere
    testSphere(None, False, "plain", False)  # OK
    # Test torus
    # testTorus(None, True, "noisy", False)  # FAIL


if __name__ == "__main__":
    # runtest()
    runtest2()
