import Rhino.Geometry as rg
import math

# Inputs:
# C : Circle
# d : float (distance from sphere center to circle center)

# Outputs:
# S       : Sphere
# Center  : Point3d
# Trimmed : Brep
# CutPlane: Plane

tol = 1e-6

S = None
Center = None
Trimmed = None
CutPlane = None

if C is not None:
    r = C.Radius
    plane = C.Plane
    CutPlane = plane

    # Sphere radius: R^2 = r^2 + d^2
    R = math.sqrt(r * r + d * d)

    # Sphere center: along circle plane normal
    Center = plane.Origin + plane.ZAxis * d
    S = rg.Sphere(Center, R)

    sphere_brep = S.ToBrep()

    # Make a sufficiently large cutting plane surface
    size = R * 4.0 + r * 4.0 + abs(d) * 2.0
    udom = rg.Interval(-size, size)
    vdom = rg.Interval(-size, size)
    cutter = rg.PlaneSurface(plane, udom, vdom).ToBrep()

    # Split sphere by the circle plane
    pieces = sphere_brep.Split(cutter, tol)

    if pieces and len(pieces) > 0:
        kept = None

        # Keep the piece on the same side as the sphere center
        # relative to the cutting plane
        for piece in pieces:
            amp = rg.AreaMassProperties.Compute(piece)
            if amp is None:
                continue

            c = amp.Centroid
            vec = c - plane.Origin

            # signed distance direction test
            side = rg.Vector3d.Multiply(vec, plane.ZAxis)

            # sphere center is always on the side indicated by d
            # if d >= 0, keep positive side; if d < 0, keep negative side
            if d >= 0 and side >= -tol:
                kept = piece
                break
            elif d < 0 and side <= tol:
                kept = piece
                break

        # fallback: choose the piece whose centroid is closer to the sphere center
        if kept is None:
            best_dist = None
            for piece in pieces:
                amp = rg.AreaMassProperties.Compute(piece)
                if amp is None:
                    continue
                dist = amp.Centroid.DistanceTo(Center)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    kept = piece

        Trimmed = kept