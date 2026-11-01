#!/usr/bin/env python3
"""S01 v12 — genuine 3D composition in Blender (bpy, headless Cycles CPU).
Frames 1-270 @30fps = the 0-9s graphics sequence (loops x2 in final video).
Everything is modeled/keyframed in 3D: extruded type, beveled bag, stool,
cash stack, wireframe cube, photo plates for hands/logo/jen, camera push.
Renders RGBA PNGs to /tmp/b3d/####.png
"""
import bpy, math, os
from mathutils import Vector

import os as _os0
OUT = _os0.environ.get('OUTDIR', '/tmp/b3d')
os.makedirs(OUT, exist_ok=True)
F = 'assets/fonts/Anton-Regular.ttf'
FM = 'assets/fonts/Manrope-800.ttf'

def rgba(c):
    return tuple(c) + (1.0,) if len(c) == 3 else tuple(c)

def lin(c255):
    return tuple(((c / 255.0) ** 2.2) for c in c255)

# palette (sRGB 255 -> linear)
INK = lin((16, 16, 18)); BONE = lin((244, 241, 234)); RED = lin((255, 85, 96))
LIME = lin((130, 195, 10)); WHITE = lin((236, 236, 234)); GREY = lin((206, 206, 204))
FLASH = lin((185, 10, 8)); MAROON = lin((78, 20, 28)); GOLD = lin((212, 175, 55))
WOOD = lin((150, 115, 80)); WOODD = lin((105, 78, 55)); ROSE = lin((196, 72, 84))
DRED = lin((92, 8, 10))

sc = bpy.context.scene
for o in list(sc.objects):
    bpy.data.objects.remove(o)
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 6
sc.cycles.use_denoising = True
sc.render.resolution_x = 720
sc.render.resolution_y = 1280
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.render.motion_blur_shutter = 0.6
sc.frame_start = 1
sc.frame_end = 270

# ---------- world with per-scene colour keys ----------
w = bpy.data.worlds['World']; w.use_nodes = False
w.color = BONE
w.keyframe_insert('color', frame=1)
w.color = BONE; w.keyframe_insert('color', frame=13)
w.color = INK; w.keyframe_insert('color', frame=14)
w.color = INK; w.keyframe_insert('color', frame=26)
w.color = LIME; w.keyframe_insert('color', frame=27)
w.color = LIME; w.keyframe_insert('color', frame=40)
w.color = WHITE; w.keyframe_insert('color', frame=41)
w.color = WHITE; w.keyframe_insert('color', frame=56)
w.color = GREY; w.keyframe_insert('color', frame=57)
w.color = GREY; w.keyframe_insert('color', frame=89)
w.color = FLASH; w.keyframe_insert('color', frame=90)
w.color = FLASH; w.keyframe_insert('color', frame=97)
w.color = DRED; w.keyframe_insert('color', frame=98)
w.color = DRED; w.keyframe_insert('color', frame=176)
w.color = MAROON; w.keyframe_insert('color', frame=177)
w.color = MAROON; w.keyframe_insert('color', frame=270)
for fc in w.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'CONSTANT'

# ---------- camera (ortho, like AE comp) ----------
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 3.5556
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co)
co.location = (0, -6, 0); co.rotation_euler = (math.radians(90), 0, 0)
sc.camera = co
# jen push-in
cam.keyframe_insert('ortho_scale', frame=177)
cam.ortho_scale = 1.78
cam.keyframe_insert('ortho_scale', frame=225)
cam.ortho_scale = 1.78
cam.keyframe_insert('ortho_scale', frame=270)

# ---------- light ----------
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 500; ld.size = 6
lo = bpy.data.objects.new('key', ld); sc.collection.objects.link(lo)
lo.location = (1.5, -4, 3); lo.rotation_euler = (math.radians(55), 0, math.radians(20))
ld2 = bpy.data.lights.new('fill', 'AREA'); ld2.energy = 120; ld2.size = 8
lo2 = bpy.data.objects.new('fill', ld2); sc.collection.objects.link(lo2)
lo2.location = (-2, -5, 1); lo2.rotation_euler = (math.radians(80), 0, math.radians(-25))

# ---------- helpers ----------
def mat(name, col, rough=0.55, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = rgba(col)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m

def emis(name, col, str_=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = rgba(col)
    e.inputs[1].default_value = str_
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(e.outputs[0], o.inputs[0])
    return m

def text_obj(name, body, sz_px, col, extr=0.05, font=F, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = sz_px / (0.52 * 360.0)
    cu.extrude = extr
    cu.bevel_depth = extr * 0.12
    cu.align_x = align; cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(font) if not bpy.data.fonts.get(font) else bpy.data.fonts.get(font)
    ob = bpy.data.objects.new(name, cu); sc.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(emis(name + '_m', col, 1.0))
    return ob

def px(x, y):
    """pixel coords (720x1280) -> world (x,z)"""
    return (x - 360) / 360.0, (640 - y) / 360.0

def kf(ob, frame, loc=None, scale=None, rot=None):
    if loc is not None:
        if len(loc) == 2:
            loc = (loc[0], 0.0, loc[1])
        ob.location = loc; ob.keyframe_insert('location', frame=frame)
    if scale is not None:
        ob.scale = scale; ob.keyframe_insert('scale', frame=frame)
    if rot is not None:
        ob.rotation_euler = rot; ob.keyframe_insert('rotation_euler', frame=frame)

def vis(ob, f0, f1):
    ob.hide_render = True; ob.hide_viewport = True
    ob.keyframe_insert('hide_render', frame=f0)
    ob.keyframe_insert('hide_viewport', frame=f0)
    ob.hide_render = False; ob.hide_viewport = False
    ob.keyframe_insert('hide_render', frame=f0 + 1)
    ob.keyframe_insert('hide_viewport', frame=f0 + 1)
    ob.keyframe_insert('hide_render', frame=f1)
    ob.keyframe_insert('hide_viewport', frame=f1)
    ob.hide_render = True; ob.hide_viewport = True
    ob.keyframe_insert('hide_render', frame=f1 + 1)
    ob.keyframe_insert('hide_viewport', frame=f1 + 1)
    for fc in ob.animation_data.action.fcurves:
        if 'hide' in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'

def visgroup(root, f0, f1):
    vis(root, f0, f1)
    for c in root.children:
        has = c.animation_data and c.animation_data.action and any(
            fc.data_path == 'hide_render' for fc in c.animation_data.action.fcurves)
        if not has:
            vis(c, f0, f1)

def ease(ob, ease_type='BEZIER'):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if 'hide' in fc.data_path:
                continue
            for kp in fc.keyframe_points:
                kp.interpolation = ease_type

def plate(name, path, w_px, h_px, x, y):
    img = bpy.data.images.load(path)
    m = bpy.data.materials.new(name + '_m'); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[1].default_value = 1.0
    nt.links.new(t.outputs['Color'], em.inputs[0])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(t.outputs['Alpha'], mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    ou = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(mx.outputs[0], ou.inputs[0])
    me = bpy.data.meshes.new(name)
    hw, hh = w_px / 720.0, h_px / 720.0
    me.from_pydata([(-hw, 0, -hh), (hw, 0, -hh), (hw, 0, hh), (-hw, 0, hh)], [], [(0, 1, 2, 3)])
    me.uv_layers.new()
    for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        me.uv_layers[0].data[i].uv = uv
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ob.location = (x, 0, y)
    ob.data.materials.append(m)
    return ob

# ---------- diagonal bars backdrop (red scene) ----------
me = bpy.data.meshes.new('bars'); me.from_pydata([(-4, 1.2, -4), (4, 1.2, -4), (4, 1.2, 4), (-4, 1.2, 4)], [], [(0, 1, 2, 3)])
bars = bpy.data.objects.new('bars', me); sc.collection.objects.link(bars)
mb = bpy.data.materials.new('bars_m'); mb.use_nodes = True
nt = mb.node_tree; b = nt.nodes['Principled BSDF']
wav = nt.nodes.new('ShaderNodeTexVoronoi')
wav.inputs['Scale'].default_value = 1.15
wav.inputs['Randomness'].default_value = 0.75
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'
ramp.color_ramp.elements[0].color = rgba(lin((92, 8, 10)))
ramp.color_ramp.elements[1].color = rgba(lin((104, 14, 16)))
ramp.color_ramp.elements[1].position = 0.5
mapn = nt.nodes.new('ShaderNodeMapping'); mapn.inputs['Rotation'].default_value[1] = math.radians(14)
tc = nt.nodes.new('ShaderNodeTexCoord')
nt.links.new(tc.outputs['Object'], mapn.inputs['Vector'])
nt.links.new(mapn.outputs['Vector'], wav.inputs['Vector'])
nt.links.new(wav.outputs['Color'], ramp.inputs['Fac'])
ramp.color_ramp.elements[1].position = 0.45
e3 = ramp.color_ramp.elements.new(0.75); e3.color = rgba(lin((84, 6, 8)))
em2 = nt.nodes.new('ShaderNodeEmission'); em2.inputs[1].default_value = 1.0
nt.links.new(ramp.outputs['Color'], em2.inputs[0])
ou2 = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(em2.outputs[0], ou2.inputs[0])
for n in list(nt.nodes):
    if n.type == 'OUTPUT_MATERIAL' and n != ou2:
        nt.nodes.remove(n)
bars.data.materials.append(mb)
vis(bars, 98, 176)

# ---------- stamp / black extrude type (lime, one line) ----------
LIME_TX = lin((140, 220, 20))
tw = text_obj('tw', 'TWENTY', 99, LIME_TX, 0.045, align='RIGHT')
x, z = px(356, 572)
kf(tw, 1, loc=px(-400, 572)); kf(tw, 8, loc=px(571, 572)); kf(tw, 13, loc=(x, 0, z))
tw.data.extrude = 0.045
tw.data.keyframe_insert('extrude', frame=13)
tw.data.extrude = 0.15
tw.data.keyframe_insert('extrude', frame=18)
vis(tw, 1, 28); ease(tw)
bi = text_obj('bi', 'BILLION', 99, LIME_TX, 0.045, align='LEFT')
x2, z2 = px(364, 572)
bi.location = (x2, 0, z2)
kf(bi, 7, scale=(0.01, 0.01, 0.01)); kf(bi, 12, scale=(1, 1, 1))
bi.data.extrude = 0.045
bi.data.keyframe_insert('extrude', frame=13)
bi.data.extrude = 0.15
bi.data.keyframe_insert('extrude', frame=18)
vis(bi, 7, 28); ease(bi)

# ---------- money bag (beveled cube + bill fan) ----------
bagroot = bpy.data.objects.new('bagroot', None); sc.collection.objects.link(bagroot)
bpy.ops.mesh.primitive_cube_add(size=1)
bag = bpy.context.object; bag.name = 'bag'
bag.scale = (0.92, 0.40, 0.68)
bv = bag.modifiers.new('bev', 'BEVEL'); bv.width = 0.12; bv.segments = 5
bag.data.materials.append(mat('bag_m', lin((95, 160, 60)), 0.45))
flap = None
flaps = []
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1)
    fc_ = bpy.context.object; fc_.name = f'flap{sgn}'
    fc_.scale = (0.55, 0.03, 0.16)
    fc_.location = (sgn * 0.24, -0.21, 0.16)
    fc_.rotation_euler = (0, sgn * math.radians(38), 0)
    fc_.data.materials.append(mat(f'flap_m{sgn}', lin((62, 110, 36)), 0.5))
    flaps.append(fc_)
bills = []
for i, ang in enumerate((-26, -13, 0, 13, 26)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    b = bpy.context.object; b.name = f'bill{i}'
    b.scale = (1.0, 0.024, 0.44)
    b.rotation_euler = (0, math.radians(ang), 0)
    b.location = (math.sin(math.radians(ang)) * 0.45, -0.05, 0.62 + abs(i - 2) * 0.04)
    b.data.materials.append(emis(f'bill_m{i}', lin((238, 235, 224)), 1.0))
    bills.append(b)
for ob in [bag] + flaps + bills:
    ob.parent = bagroot
x, z = px(352, 749)
kf(bagroot, 27, loc=(x - 0.25, 0, -3.2), scale=(1.35, 1.35, 1.35))
kf(bagroot, 40, loc=(x - 0.25, 0, z + 0.10), scale=(1.35, 1.35, 1.35))
kf(bagroot, 41, loc=(x, 0, z), scale=(0.90, 0.90, 0.90))
kf(bagroot, 46, loc=(x, 0, z))
kf(bagroot, 49, loc=(x, 0, z - 0.10))
kf(bagroot, 53, loc=(x, 0, z))
visgroup(bagroot, 27, 89); ease(bagroot)
vis(bag, 0, 0)
for fl in flaps:
    vis(fl, 0, 0)
for b in bills:
    vis(b, 0, 0)
bb = plate('bagbills', 'assets/sprites/bagbills.png', 411, 333, 0, 0)
bb.parent = bagroot; bb.location = (0, 0, 0)
vis(bb, 27, 89)

# ---------- stool ----------
stroot = bpy.data.objects.new('stroot', None); sc.collection.objects.link(stroot)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.42, depth=0.08)
seat = bpy.context.object; seat.name = 'seat'
seat.data.materials.append(mat('seat_m', WOOD, 0.5))
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.42, depth=0.06, location=(0, 0, -0.055))
rim = bpy.context.object; rim.name = 'rim'
rim.data.materials.append(mat('rim_m', WOODD, 0.5))
legs = []
for i, (lx, ly, ang) in enumerate(((-0.28, -0.12, 14), (0.28, -0.12, -14), (-0.20, 0.16, 8), (0.20, 0.16, -8))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.045, depth=0.68, location=(lx, ly, -0.40))
    L = bpy.context.object; L.name = f'leg{i}'
    L.rotation_euler = (math.radians(-ang * 0.4), math.radians(ang), 0)
    L.data.materials.append(mat(f'leg_m{i}', WOODD, 0.5))
    legs.append(L)
for ob in [seat, rim] + legs:
    ob.parent = stroot
x, z = px(360, 800)
kf(stroot, 41, loc=(2.4, 0, z)); kf(stroot, 45, loc=(x, 0, z))
visgroup(stroot, 41, 89); ease(stroot)
vis(seat, 0, 0); vis(rim, 0, 0)
for L in legs:
    vis(L, 0, 0)
xs2, zs2 = px(360, 880)
stp = plate('stoolp', 'assets/sprites/stool.png', 280, 280, xs2, zs2)
kf(stp, 41, loc=(2.4, 0, zs2)); kf(stp, 45, loc=(xs2, 0, zs2))
vis(stp, 41, 89); ease(stp)

bink = text_obj('bink', 'BILLION', 97, INK, 0.04)
bink.rotation_euler = (math.radians(90), math.radians(-8), 0)
x, z = px(362, 350); bink.location = (x, 0, z)
kf(bink, 27, loc=px(362, 350)); kf(bink, 41, loc=px(362, 300))
vis(bink, 27, 56)
tag = text_obj('tag', 'TWENTY', 34, RED, 0.03)
tag.rotation_euler = (math.radians(90), math.radians(-78), 0)
x, z = px(140, 200); tag.location = (x, 0, z)
vis(tag, 27, 56)

# ---------- HE SAID / NO ----------
he = text_obj('he', 'HE SAID', 77, lin((200, 30, 40)), 0.04)
x, z = px(352, 286); he.location = (x, 0, z)
kf(he, 62, scale=(0.2, 0.2, 0.2)); kf(he, 69, scale=(1, 1, 1))
vis(he, 62, 89); ease(he)
no = text_obj('no', 'NO', 228, ROSE, 0.05)
x, z = px(360, 460); no.location = (x, -0.6, z)
kf(no, 74, scale=(0.38, 0.2, 0.2)); kf(no, 82, scale=(1.9, 1, 1))
vis(no, 74, 89); ease(no)

# ---------- cash stack ----------
croot = bpy.data.objects.new('croot', None); sc.collection.objects.link(croot)
bpy.ops.mesh.primitive_cube_add(size=1)
cash = bpy.context.object; cash.name = 'cash'
cash.scale = (0.52, 0.17, 0.30)
cb = cash.modifiers.new('bev', 'BEVEL'); cb.width = 0.04; cb.segments = 3
cash.data.materials.append(mat('cash_m', lin((150, 160, 140)), 0.6))
bpy.ops.mesh.primitive_cube_add(size=1)
cband = bpy.context.object; cband.name = 'cband'
cband.scale = (0.175, 0.19, 0.315)
cband.data.materials.append(mat('cband_m', lin((90, 110, 80)), 0.6))
cband.parent = croot
cash.parent = croot
x, z = px(460, 745)
kf(croot, 98, loc=(3.0, 0, 1.2), rot=(0, math.radians(-35), 0))
kf(croot, 110, loc=(x, 0, z), rot=(0, math.radians(-8), 0))
vis(cash, 0, 0); vis(cband, 0, 0)
cf = plate('cashfist', 'assets/sprites/cashfist.png', 238, 172, 0, 0)
cf.parent = croot; cf.location = (0, 0, 0)
visgroup(croot, 98, 176); ease(croot)

# ---------- glove / hand2 / logo plates ----------
gl = plate('glove', 'assets/sprites/glove2.png', 300, 190, *px(-260, 760))
kf(gl, 102, loc=(*px(-260, 760),)); kf(gl, 112, loc=(*px(140, 760),))
vis(gl, 98, 176); ease(gl)
h2 = plate('hand2', 'assets/sprites/hand2.png', 207, 234, *px(570, 780))
vis(h2, 0, 0)
lg = plate('logo', 'assets/sprites/logo2.png', 161, 108, *px(164, 637))
kf(lg, 107, scale=(0.2, 0.2, 0.2)); kf(lg, 116, scale=(1.0, 1.0, 1.0))
vis(lg, 107, 176); ease(lg)

# ---------- wireframe cube ----------
bpy.ops.mesh.primitive_cube_add(size=1)
wire = bpy.context.object; wire.name = 'wire'
wire.scale = (0.42, 0.42, 0.42)
wm = wire.modifiers.new('wf', 'WIREFRAME'); wm.thickness = 0.010
wire.data.materials.append(emis('wire_m', lin((230, 170, 180)) + (1.0,), 0.8))
kf(wire, 105, loc=(x + 0.11, 0, z + 0.02), rot=(0.4, 0.5, 0))
kf(wire, 176, loc=(x + 0.11, 0, z + 0.02), rot=(0.4 + 1.2, 0.5 + 1.6, 0.6))
vis(wire, 105, 176); ease(wire)
for fc in wire.animation_data.action.fcurves:
    if 'rotation' in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# ---------- 2008 digits ----------
digs = []
for i, ch in enumerate('2008'):
    d = text_obj(f'd{i}', ch, 90, BONE, 0.03)
    x, z = px(300 + i * 80, 135)
    d.location = (x, 0.3, z)
    kf(d, 143 + i * 6, scale=(0.01, 0.01, 0.01))
    kf(d, 146 + i * 6, scale=(1, 1, 1))
    vis(d, 143 + i * 6, 269)
    ease(d)
    for nd in d.data.materials[0].node_tree.nodes:
        if nd.type == 'EMISSION':
            nd.inputs[1].default_value = 0.5
    digs.append(d)

# ---------- jensen plate + subscribe plate ----------
# jen person comes from graded footage in the compositor (layered renders below)
sp = plate('sub', '/tmp/v11b/sub.png', 446, 276, *px(360, 1000)) if os.path.exists('/tmp/v11b/sub.png') else None
if sp is None:
    bpy.ops.mesh.primitive_cube_add(size=1)
    sp = bpy.context.object; sp.name = 'sub'
    sp.scale = (1.24, 0.06, 0.77)
    sb = sp.modifiers.new('bev', 'BEVEL'); sb.width = 0.09; sb.segments = 4
    sp.data.materials.append(emis('sub_m', GOLD, 1.0))
    x, z = px(360, 1000)
    sp.location = (x, 0, z)
    stx = text_obj('subt', 'subscribe\n& like', 46, INK, 0.01, font=FM)
    stx.location = (x, -0.02, z)
    kf(stx, 225, scale=(0.2, 0.2, 0.2)); kf(stx, 235, scale=(1, 1, 1))
    vis(stx, 225, 269); ease(stx)
kf(sp, 225, scale=(0.25, 0.012, 0.154)); kf(sp, 235, scale=(1.24, 0.06, 0.77))
vis(sp, 225, 269); ease(sp)

# ---------- layer mode (transparent passes for compositor) ----------
LAYER = os.environ.get('LAYER', '')
if LAYER:
    sc.render.film_transparent = True
    if LAYER == 'digits':
        vis(sp, 0, 0); vis(stx, 0, 0)
        for d in digs:
            d.location = (d.location[0], 0, d.location[2])
    elif LAYER == 'sub':
        for d in digs:
            vis(d, 0, 0)

# ---------- diagnostics ----------
import os as _os
if _os.environ.get('DIAG'):
    for f in (100,):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        we = w.evaluated_get(dg)
        print('DIAG world color f%d' % f, tuple(round(c, 3) for c in we.color), flush=True)
        for o in sc.objects:
            oe = o.evaluated_get(dg)
            print('DIAG obj', o.name, 'hide_render_eval', oe.hide_render, flush=True)
    raise SystemExit(0)

# ---------- render ----------
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
import sys
argv = sys.argv[5:] if '--' in sys.argv else sys.argv[1:]
a, b = (int(argv[0]), int(argv[1])) if len(argv) >= 2 else (1, 270)
import time
for f in range(a, b + 1):
    sc.frame_set(f)
    sc.render.filepath = f'{OUT}/{f:04d}.png'
    t = time.time()
    bpy.ops.render.render(write_still=True)
    if f % 10 == 0:
        print(f'frame {f} {time.time() - t:.1f}s', flush=True)
print('BLENDER DONE', flush=True)
