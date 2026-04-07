import Rhino.Geometry as rg
import math

# Grasshopper input:
#   L (float) edge length, default = 2
# Grasshopper output:
#   Cube (Brep)
#   Pts (list[Point3d])
#   VtxPlanes (list[Plane])  # plane at each vertex

if L is None or L <= 0:
    L = 2.0

s = float(L)

# Cube vertices (centered at origin for symmetry)
# 8 corners at (±s/2, ±s/2, ±s/2)
h = s / 2.0
vertices = [
    rg.Point3d(-h, -h, -h),  # 0
    rg.Point3d( h, -h, -h),  # 1
    rg.Point3d( h,  h, -h),  # 2
    rg.Point3d(-h,  h, -h),  # 3
    rg.Point3d(-h, -h,  h),  # 4
    rg.Point3d( h, -h,  h),  # 5
    rg.Point3d( h,  h,  h),  # 6
    rg.Point3d(-h,  h,  h),  # 7
]

Pts = vertices

# Build cube using Rhino Box primitive
base_plane = rg.Plane(rg.Point3d(-h, -h, -h), rg.Vector3d.XAxis, rg.Vector3d.YAxis)
box = rg.Box(base_plane, rg.Interval(0, s), rg.Interval(0, s), rg.Interval(0, s))
Cube = box.ToBrep()

# Cube center (at origin)
center = rg.Point3d(0, 0, 0)

def make_vertex_plane(origin, center_pt):
    # Z axis: vector from center to vertex
    z = rg.Vector3d(origin.X - center_pt.X, origin.Y - center_pt.Y, origin.Z - center_pt.Z)
    if not z.Unitize():
        # fallback (shouldn't happen)
        z = rg.Vector3d.ZAxis

    # Pick a reference vector not parallel to z, to construct X/Y
    ref = rg.Vector3d.ZAxis
    if abs(rg.Vector3d.Multiply(z, ref)) > 0.999:  # nearly parallel
        ref = rg.Vector3d.XAxis

    x = rg.Vector3d.CrossProduct(ref, z)
    if not x.Unitize():
        x = rg.Vector3d.XAxis

    y = rg.Vector3d.CrossProduct(z, x)
    if not y.Unitize():
        y = rg.Vector3d.YAxis

    return rg.Plane(origin, x, y)

VtxPlanes = [make_vertex_plane(p, center) for p in Pts]