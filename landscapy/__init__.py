"""Landscapy: editable stylized nature generators for Blender 5.2."""
bl_info = {'name': 'Landscapy', 'author': 'Morneven', 'version': (0, 58, 0),
           'blender': (5, 2, 0), 'location': 'View3D > Sidebar > Landscapy',
           'description': 'Stylized trees, textured foliage cards and nature props', 'category': 'Add Mesh'}
import bpy
import bmesh
import math
import random
import colorsys
import json
import uuid
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy.props import (BoolProperty, FloatProperty, IntProperty, StringProperty,
                       EnumProperty, PointerProperty, CollectionProperty, FloatVectorProperty)

ROOT = Path(__file__).parent
from . import surfaces, canopy, attachments, ornaments, fronds, ivy, paths, mushrooms, snapping, impostors, preview, wood_props, rocks, roots, tube_frames, instance_cards, surface_distribution, live_surface, live_tree_fronds
from . import wood_junctions
TREE_PRESETS = {
    'Broadleaf': (6, .16, 16, 1.6, .1), 'Banyan': (7, .32, 24, 3.1, .15),
    'Giant': (14, .6, 32, 4, .12), 'Mountain Bonsai': (3.5, .24, 14, 1.9, 1.1),
    'Twisted Pine': (6, .2, 15, 1.7, .7), 'Conifer': (7, .17, 30, 1.9, 0),
    'Palm': (7, .22, 10, 2.7, .34), 'Banana': (2.65, .23, 9, 2.4, .20),
    'Willow': (7, .3, 22, 2.8, .1), 'Acacia': (6, .25, 18, 3.3, .2),
    'Baobab': (8, 1.0, 12, 2.4, .1), 'Dead Tree': (6, .18, 14, 1.8, .3),
    'Mangrove': (6.5, .28, 24, 2.8, .12), 'Pine': (8, .18, 36, 2.2, 0),
    'Coconut': (7, .24, 12, 3.25, .92), 'Bonsai Tree': (3.3, .24, 8, 2.3, 1.2),
    'Apple': (5.8, .17, 24, 1.8, .04), 'Mango': (7.2, .25, 24, 2.25, .08),
    'Grape Vine': (3.6, .16, 18, 1.85, .22)}
TREE_FORM_DEFAULTS = {
    'Broadleaf': (2,.52,.12), 'Banyan': (3,.42,.20), 'Giant': (3,.48,.08),
    'Mountain Bonsai': (3,.64,.10), 'Bonsai Tree': (2,.64,.10),
    'Twisted Pine': (3,.42,.14), 'Conifer': (2,.34,.08), 'Pine': (2,.34,.08),
    'Palm': (1,.42,.14), 'Coconut': (1,.42,.14), 'Banana': (1,.42,.26),
    'Willow': (2,.25,.32), 'Acacia': (2,.14,.05), 'Baobab': (2,.44,.08),
    'Mangrove': (2,.40,.12), 'Dead Tree': (3,.52,.12),
    'Apple': (3,.55,.08), 'Mango': (3,.48,.12), 'Grape Vine': (2,.28,.18),
}
TRUNK_TYPES = [
    ('AUTO','Follow Plant Type','Use the trunk and branch architecture recommended by Plant Type'),
    ('BRANCHED','Branched Woody','Single woody trunk with crown branches'),
    ('CONIFER','Conifer Leader','Straight central leader with shortening branch whorls'),
    ('TWISTED_CONIFER','Twisted Conifer','Curved leader with conifer branch whorls'),
    ('PALM','Palm Crown','Unbranched stem with leaves at the crown'),
    ('PSEUDOSTEM','Broad Pseudostem','Soft, unbranched stem with broad leaves from the crown'),
    ('BONSAI','Bonsai','Low, asymmetric woody branching'),
    ('STILT','Mangrove Stilt','Woody crown with raised stilt-root system'),
    ('WILLOW','Drooping Branches','Long branches and hanging secondary growth'),
    ('UMBRELLA','Umbrella Crown','Wide, flattened branch crown'),
    ('BAOBAB','Massive Trunk','Heavy trunk and broad, compact crown'),
    ('DEAD','Dead Branches','Sparse woody branching without foliage'),
    ('VINE','Trellised Vine','Low trunk with long, nearly horizontal cordons and fruiting shoots'),
]
PLANT_TRUNK = {
    'Banyan':'BRANCHED','Giant':'BAOBAB','Mountain Bonsai':'BONSAI','Bonsai Tree':'BONSAI',
    'Twisted Pine':'TWISTED_CONIFER','Conifer':'CONIFER','Pine':'CONIFER',
    'Palm':'PALM','Coconut':'PALM','Banana':'PSEUDOSTEM','Willow':'WILLOW',
    'Acacia':'UMBRELLA','Baobab':'BAOBAB','Dead Tree':'DEAD','Mangrove':'STILT',
    'Apple':'BRANCHED','Mango':'BRANCHED','Grape Vine':'VINE','Broadleaf':'BRANCHED',
}
PLANT_FRUIT_TYPE = {
    'Banana':'BANANA_BUNCH','Coconut':'COCONUT_CROWN','Apple':'AXILLARY_POME',
    'Mango':'HANGING_PANICLE','Grape Vine':'GRAPE_CLUSTER',
    'Pine':'CONE_CLUSTER','Conifer':'CONE_CLUSTER','Twisted Pine':'CONE_CLUSTER',
}
PLANT_TRUNK_OPTIONS = {
    # Plant Type is the parent of the architecture controls. Keep alternatives
    # in-family so a Palm cannot accidentally turn into a generic conifer.
    'Broadleaf': {'BRANCHED','WILLOW','UMBRELLA','BONSAI'},
    'Banyan': {'BRANCHED','STILT'}, 'Giant': {'BAOBAB','BRANCHED'},
    'Mountain Bonsai': {'BONSAI','BRANCHED'}, 'Bonsai Tree': {'BONSAI','BRANCHED'},
    'Twisted Pine': {'TWISTED_CONIFER','CONIFER'}, 'Conifer': {'CONIFER','TWISTED_CONIFER'},
    'Pine': {'CONIFER','TWISTED_CONIFER'}, 'Palm': {'PALM'}, 'Coconut': {'PALM'},
    'Banana': {'PSEUDOSTEM'}, 'Willow': {'WILLOW','BRANCHED'},
    'Acacia': {'UMBRELLA','BRANCHED'}, 'Baobab': {'BAOBAB'},
    'Dead Tree': {'DEAD'}, 'Mangrove': {'STILT','BRANCHED'},
    'Apple': {'BRANCHED','WILLOW'}, 'Mango': {'BRANCHED','WILLOW'},
    'Grape Vine': {'VINE'},
}
TREE_LEAF_OPTIONS = {
    'BRANCHED': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'CONIFER': ('Conifer','Single'), 'TWISTED_CONIFER': ('Conifer','Single'),
    'PALM': ('Palm',), 'PSEUDOSTEM': ('Banana',),
    'BONSAI': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'STILT': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'WILLOW': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'UMBRELLA': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'BAOBAB': ('Cloud','Single','Opposite','Alternate','Spiral','Whorl'),
    'DEAD': ('None',), 'VINE': ('Cloud','Single','Alternate','Spiral','Whorl'),
}
TREE_LEAF_AVAILABLE = ('Cloud','Single','Opposite','Alternate','Spiral','Whorl','Conifer','Palm','Banana',
                       'Grass','Tallgrass','Flower','Flower Cluster')
FRUIT_TYPE_LABELS = {
    'CUSTOM': ('Custom Placement','Use the manual zone and height settings'),
    'BANANA_BUNCH': ('Banana Bunch','One hanging bunch from the upper pseudostem'),
    'AXILLARY_POME': ('Axillary Fruit','Individual fruits spaced along secondary branches'),
    'GRAPE_CLUSTER': ('Grape Cluster','Dangling clusters near distal vine nodes'),
    'COCONUT_CROWN': ('Coconut Crown Cluster','Clusters at palm frond bases'),
    'HANGING_PANICLE': ('Hanging Panicle','Grouped fruit on drooping terminal shoots'),
    'RACEME': ('Raceme','An elongated hanging chain attached to woody shoots'),
    'CAULIFLOROUS': ('Cauliflorous','Fruit on the trunk or old lower branches'),
    'TERMINAL_CYME': ('Terminal Cluster','Compact clusters at shoot tips'),
    'AXILLARY_POD': ('Axillary Pods','Pods distributed along secondary branch nodes'),
    'CONE_CLUSTER': ('Conifer Cones','Cone clusters on upper conifer branches'),
}
PLANT_FRUIT_OPTIONS = {
    'BRANCHED': ('CUSTOM','AXILLARY_POME','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','CAULIFLOROUS','TERMINAL_CYME','AXILLARY_POD'),
    'BONSAI': ('CUSTOM','AXILLARY_POME','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','CAULIFLOROUS','TERMINAL_CYME','AXILLARY_POD'),
    'STILT': ('CUSTOM','AXILLARY_POME','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','CAULIFLOROUS','TERMINAL_CYME','AXILLARY_POD'),
    'WILLOW': ('CUSTOM','AXILLARY_POME','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','TERMINAL_CYME','AXILLARY_POD'),
    'UMBRELLA': ('CUSTOM','AXILLARY_POME','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','TERMINAL_CYME'),
    'BAOBAB': ('CUSTOM','AXILLARY_POME','CAULIFLOROUS','TERMINAL_CYME'),
    'VINE': ('CUSTOM','GRAPE_CLUSTER','RACEME','TERMINAL_CYME'),
    'CONIFER': ('CUSTOM','CONE_CLUSTER','TERMINAL_CYME'),
    'TWISTED_CONIFER': ('CUSTOM','CONE_CLUSTER','TERMINAL_CYME'),
    'PALM': ('CUSTOM','COCONUT_CROWN'), 'PSEUDOSTEM': ('CUSTOM','BANANA_BUNCH'),
    'DEAD': ('CUSTOM',),
}
TRUNK_BARK_LOOK = {
    'BRANCHED':'BARK_GROOVES','CONIFER':'BARK_GROOVES','TWISTED_CONIFER':'BARK_WAVES',
    'PALM':'BARK_FLAKES','PSEUDOSTEM':'BARK_FLAKES','BONSAI':'BARK_GROOVES',
    'STILT':'BARK_GROOVES','WILLOW':'BARK_GROOVES','UMBRELLA':'BARK_FLAKES',
    'BAOBAB':'BARK_GROOVES','DEAD':'BARK_FLAKES','VINE':'BARK_GROOVES',
}
PATTERNS = ['Cloud','Single','Opposite','Alternate','Spiral','Whorl','Conifer','Palm','Banana','Grass','Tallgrass','Flower','Flower Cluster']
LEAF_TYPE_LABELS = {
    'None': ('No Foliage','Bare structural branches; selected automatically for dead-tree profiles'),
    'Cloud': ('Canopy Cluster','Overlapping leaf cards that fill a canopy or bush'),
    'Single': ('Single Card','Independent leaf cards'),
    'Opposite': ('Opposite Pairs','Paired leaves at each station on a rachis'),
    'Alternate': ('Alternate','One leaf alternating sides at each station'),
    'Spiral': ('Spiral','Leaves rotate around the rachis between stations'),
    'Whorl': ('Whorled','Several leaves radiate from each station'),
    'Conifer': ('Needle Spray','Short narrow foliage in pairs along a rachis; conifer inspired'),
    'Palm': ('Pinnate Frond','Leaflets arranged on both sides of a rachis; coconut inspired'),
    'Banana': ('Broad Lamina','One broad continuous blade along a midrib; banana inspired'),
    'Grass': ('Grass Tuft','Short grass cards grouped into tufts'),
    'Tallgrass': ('Tall Grass','Long upright grass cards'),
    'Flower': ('Flower','One flower ornament'),
    'Flower Cluster': ('Flower Cluster','Several flowers grouped together'),
}
MUSHROOMS = ['Button','Dome','Parasol','Bell','Funnel','Morel','Puffball','Coral','Bracket','Oyster']
PROPS = ['Pebble','Boulder','Flat Rock','Shard','Stack','Stump','Hollow Log','Fallen Trunk','Broken Branch','Root','Vine']
PROP_DEFAULTS = {
    'Pebble': (.16,1.0,.35,0), 'Boulder': (.16,1.0,.7,0),
    'Flat Rock': (.16,1.0,.7,0), 'Shard': (.16,1.0,.6,0), 'Stack': (.16,1.0,.5,0),
    'Stump': (.38,1.5,.6,.1), 'Hollow Log': (.42,2.1,.6,.3),
    'Fallen Trunk': (.32,2.5,.6,.35), 'Broken Branch': (.25,1.7,.6,.25),
    'Root': (.30,2.1,.6,.7), 'Vine': (.15,2.5,.65,.7),
}
ROCK_DEFAULTS = {
    'Pebble': ((1.2,1,.65),.18,0,.08,4),
    'Boulder': ((1,1,.95),.28,2,.22,4),
    'Flat Rock': ((1.3,1,.6),.36,2,.28,4),
    'Shard': ((.85,.8,1.4),.16,1,.05,4),
    'Stack': ((1.1,1,.75),.24,2,.34,4),
}
def enum(names):
    return [(n, n, '') for n in names]

def effective_trunk(settings):
    return settings.trunk_type if settings.trunk_type!='AUTO' else PLANT_TRUNK.get(settings.preset,'BRANCHED')

def trunk_type_items(settings,context):
    allowed=PLANT_TRUNK_OPTIONS.get(settings.preset,set(PLANT_TRUNK.values()))
    return [item for item in TRUNK_TYPES if item[0]=='AUTO' or item[0] in allowed]

def tree_leaf_options(settings):
    trunk=effective_trunk(settings)
    if trunk=='DEAD': return ('None',)
    recommended=recommended_leaf(settings.preset,trunk)
    profile=tuple(key for key in TREE_LEAF_OPTIONS.get(trunk,TREE_LEAF_OPTIONS['BRANCHED']) if key!='None')
    ordered=tuple(dict.fromkeys(profile+TREE_LEAF_AVAILABLE))
    return (recommended,)+tuple(key for key in ordered if key!=recommended)

def recommended_leaf(preset,trunk):
    if trunk=='DEAD': return 'None'
    if trunk=='PALM': return 'Palm'
    if trunk=='PSEUDOSTEM': return 'Banana'
    if trunk in {'CONIFER','TWISTED_CONIFER'}: return 'Conifer'
    return {'Apple':'Alternate','Mango':'Alternate','Grape Vine':'Alternate'}.get(preset,'Cloud')

def leaf_type_items(settings,context):
    options=(tree_leaf_options(settings) if settings.kind=='Tree' else PATTERNS)
    recommended=recommended_leaf(settings.preset,effective_trunk(settings)) if settings.kind=='Tree' else None
    return [(key,LEAF_TYPE_LABELS[key][0]+(' • Recommended' if key==recommended else ''),LEAF_TYPE_LABELS[key][1]) for key in options]

def fruit_type_items(settings,context):
    options=(PLANT_FRUIT_OPTIONS.get(effective_trunk(settings),tuple(FRUIT_TYPE_LABELS))
             if settings.kind=='Tree' else tuple(FRUIT_TYPE_LABELS))
    return [(key,*FRUIT_TYPE_LABELS[key]) for key in options]

def apply_trunk_surface(settings):
    if settings.kind!='Tree': return
    entry=surfaces.ensure(settings).get('Bark')
    if not entry or entry.material_override: return
    if entry.customized and not (entry.image and entry.image.name==entry.plant_starter_image): return
    look=TRUNK_BARK_LOOK.get(effective_trunk(settings),'BARK_GROOVES')
    image_path=ROOT/'textures'/surfaces.LIBRARY_LOOKS[look][1]
    if not image_path.is_file(): return
    image=bpy.data.images.load(str(image_path),check_existing=True); image.pack()
    entry.library_look=look; entry.image=image; entry.customized=True; entry.plant_starter_image=image.name

def wind_changed(settings,context):
    owner=settings.id_data
    if isinstance(owner,bpy.types.Object):
        owner.update_tag(refresh={'OBJECT'})
        for child in owner.children:
            if not child.get('lp_live_ornaments'): continue
            modifier=child.modifiers.get('Landscapy Wind')
            if modifier and modifier.node_group: modifier.node_group.update_tag()
            child.update_tag(refresh={'OBJECT'})

def wind_link_changed(settings,context):
    wind_changed(settings,context)
    owner=settings.id_data
    if isinstance(owner,bpy.types.Object):
        for child in owner.children:
            if child.get('lp_live_ornaments'): wind_modifier(child)

def preview_changed(settings,context):
    owner=settings.id_data
    if isinstance(owner,bpy.types.Object): preview.sync(owner)

def live_distribution_changed(settings,context):
    owner=settings.id_data
    if isinstance(owner,bpy.types.Object) and settings.live_surface:
        group=live_surface.localize(owner)
        if group: group.update_tag()
        owner.update_tag(refresh={'OBJECT'})

def live_ornament_changed(settings,context):
    owner=settings.id_data
    if not isinstance(owner,bpy.types.Object): return
    owner.update_tag(refresh={'OBJECT'})
    for child in owner.children:
        if child.get('lp_ornament_owner')!=settings.uid or not child.get('lp_live_ornaments'): continue
        modifier=child.modifiers.get('Landscapy Live Ornaments')
        if modifier and modifier.node_group: modifier.node_group.update_tag()
        child.update_tag(refresh={'OBJECT'})

def trunk_profile_changed(settings,context):
    # Root morphology is linked to the selected trunk profile, then remains
    # fully editable in the Root System panel.
    roots.preset(settings); apply_trunk_surface(settings)
    if settings.kind=='Tree':
        if settings.pattern not in tree_leaf_options(settings):
            settings.pattern=recommended_leaf(settings.preset,effective_trunk(settings))
        if settings.fruit_type not in PLANT_FRUIT_OPTIONS.get(effective_trunk(settings),tuple(FRUIT_TYPE_LABELS)):
            settings.fruit_type=PLANT_FRUIT_TYPE.get(settings.preset,'CUSTOM')
            if settings.fruit_type not in PLANT_FRUIT_OPTIONS.get(effective_trunk(settings),()):
                settings.fruit_type='CUSTOM'

def pattern_changed(settings,context):
    if settings.pattern in {'Flower','Flower Cluster'} and settings.card=='Quad':
        settings.card='Valley'
    if len(settings.textures)==1 and untouched_starter(settings.textures[0]):
        key=starter_key(settings)
        settings.textures[0].image=default_image(key)
        settings.textures[0].starter_pattern=key

class LPTexture(bpy.types.PropertyGroup):
    image: PointerProperty(type=bpy.types.Image)
    starter_pattern: StringProperty(options={'HIDDEN'},description='Tracks only an untouched built-in starter image')
    normal: PointerProperty(type=bpy.types.Image)
    weight: FloatProperty(default=1, min=0)
    aspect: FloatProperty(default=1, min=.01)
    size: FloatProperty(default=1, min=.01)
    pivot: FloatProperty(default=.5, min=0, max=1)
    rotation: FloatProperty(default=0, subtype='ANGLE')
    uv_region: FloatVectorProperty(size=4, default=(0,0,1,1))
    __annotations__.update(surfaces.properties())

class LPSettings(bpy.types.PropertyGroup):
    uid: StringProperty()
    schema: IntProperty(default=1)
    kind: EnumProperty(items=enum(['Tree','Foliage','Ivy','Mushroom','Prop']), default='Foliage')
    preset: EnumProperty(name='Plant Type',items=enum(list(TREE_PRESETS)), default='Broadleaf')
    trunk_type: EnumProperty(name='Trunk Type',items=trunk_type_items,default=0,update=trunk_profile_changed,
                             description='Controls trunk, branch or frond-bearing architecture; roots receive a matching default')
    pattern: EnumProperty(name='Leaf Type',items=leaf_type_items, default=0,update=pattern_changed,
                          description='Foliage formation independent of the Tree Form Preset')
    mushroom: EnumProperty(items=enum(MUSHROOMS))
    prop: EnumProperty(items=enum(PROPS), default='Boulder')
    controller: PointerProperty(type=bpy.types.Object)
    target: PointerProperty(type=bpy.types.Object)
    binding_valid: BoolProperty(default=False)
    binding_message: StringProperty(default='Not bound')
    attachment_local_wind: BoolProperty(default=False,name='Additional Local Wind',description='Enable local sway after target deformation; otherwise only target motion is inherited')
    wind_controller: PointerProperty(type=bpy.types.Object,update=wind_link_changed)
    mode: EnumProperty(items=enum(['Auto','Volume','Surface','Path','Individual']), default='Auto')
    density: FloatProperty(default=30, min=0, max=10000, update=live_distribution_changed)
    gn_surface: BoolProperty(name='Geometry Nodes Surface Points',default=False,description='Sample mesh Surface/Carpet anchors with Geometry Nodes; Regenerate to update the cards')
    live_surface: BoolProperty(name='Live Geometry Cards',default=False,description='Evaluate Surface, Volume, or curve Path cards, Ivy vines, arranged Tree fronds, and Banana blades in Geometry Nodes when Instanced Card Source is enabled')
    live_volume_grid_cells: IntProperty(name='Volume Grid Detail',default=64,min=16,max=128,update=live_distribution_changed,description='Maximum grid cells across the volume diagonal; lower values cap evaluation cost but can increase effective spacing')
    preview_enabled: BoolProperty(name='Preview Density',default=False,description='Show fewer cards in the viewport; render retains full density',update=preview_changed)
    preview_ratio: FloatProperty(name='Preview Cards',default=.25,min=0,max=1,subtype='FACTOR',description='Fraction of whole cards displayed in the viewport; full density remains for render and Build Variants',update=preview_changed)
    instance_cards: BoolProperty(name='Instanced Card Source',default=False,description='Store Quad, Valley/Peak, subdivided, and Banana cards as points while retaining wood or vine mesh')
    canopy_mode: EnumProperty(items=[('COVER','Cover Crown','Bounded overlapping clusters with balanced shell coverage'),('LEGACY','Loose Clusters','Previous Gaussian scatter around branch tips')],default='COVER')
    branch_crown: BoolProperty(name='Branch Canopy Masses',default=False,
                               description='Shape the crown with large groups of cards anchored to limbs')
    canopy_coverage: FloatProperty(name='Crown Coverage',default=1.2,min=0,max=4,description='Coverage target; density and the instance limit still apply')
    canopy_join: FloatProperty(name='Crown Join',default=.85,min=0,max=1.5,description='Fill the space between branch foliage groups; zero leaves separate crown pads')
    cluster_radius: FloatProperty(name='Cluster Radius',default=.75,min=.05,max=5,description='Overlapping lobe radius in local meters')
    canopy_shell: FloatProperty(name='Outer Coverage',default=.72,min=0,max=1,description='Balance exterior shell versus interior fill')
    canopy_alignment: FloatProperty(name='Outward Alignment',default=.7,min=0,max=1,description='Blend random and outward growth on volume fronds; also aims tree canopy cards outward',update=live_distribution_changed)
    canopy_candidates: IntProperty(name='Gap Search Samples',default=4,min=1,max=8,description='Compare this many deterministic positions per card and prefer uncovered crown regions')
    limit: IntProperty(default=3000, min=1, max=100000, update=live_distribution_changed)
    spacing: FloatProperty(default=.04, min=0, update=live_distribution_changed)
    mask: StringProperty(description='Vertex group on controller')
    seed: IntProperty(default=42, min=0, update=live_distribution_changed)
    color_seed: IntProperty(default=61, min=0, update=live_distribution_changed)
    rotation_seed: IntProperty(default=19, min=0, update=live_distribution_changed)
    texture_seed: IntProperty(default=73, min=0, update=live_distribution_changed)
    height: FloatProperty(default=6, min=.05)
    mesh_detail: FloatProperty(name='Solid Mesh Detail',default=2,min=.35,max=3,description='Radial and lengthwise detail for wood, rocks, stems and mushroom caps; cards remain lightweight')
    fuse_wood: BoolProperty(name='Join Wood Junctions',default=True,
                            description='Fuse intersecting wood surfaces before building foliage cards')
    radius: FloatProperty(default=.16, min=.002)
    taper: FloatProperty(default=.85, min=0, max=1)
    branches: IntProperty(default=16, min=1, max=100)
    levels: IntProperty(default=2, min=1, max=4)
    branch_guides: EnumProperty(name='Branch Curves',items=[('HYBRID','Auto + Curve','Generate branches and add guide splines'),('AUTO','Auto Only','Use generated branches; first spline still controls the trunk'),('MANUAL','Curve Only','Use extra guide splines as primary branches; requires a curve controller')],default='HYBRID')
    length: FloatProperty(default=1.6, min=.01,update=live_distribution_changed)
    angle: FloatProperty(default=.6, min=-1.5, max=1.5, subtype='ANGLE')
    curve: FloatProperty(default=.1, min=-3, max=3)
    droop: FloatProperty(default=.15, min=-2, max=2)
    roots: IntProperty(name='Primary Roots',default=5,min=0,max=20)
    root_guides: PointerProperty(name='Root Curves',type=bpy.types.Object,description='Separate curve; each spline shapes one root from the trunk outward')
    root_guide_mode: EnumProperty(name='Root Curves Mode',items=[('AUTO','Automatic Only','Ignore guide curves'),('HYBRID','Auto + Curves','Add guided roots to automatic roots'),('CURVE','Curves Only','Build roots from guide splines only')],default='HYBRID')
    root_guide_ground_follow: FloatProperty(name='Guide Ground Follow',default=0,min=0,max=1,subtype='FACTOR',description='Blend guided root heights toward Ground Mesh; zero preserves the edited curve')
    root_style: EnumProperty(name='Root Form',items=[('SURFACE','Surface','Low roots following the soil'),('BUTTRESS','Buttress','Flared roots joining a broad trunk'),('EXPOSED','Exposed','Raised, winding roots for mountain trees')],default='SURFACE')
    root_length: FloatProperty(name='Root Reach',default=4.4,min=.5,max=20,description='Length relative to trunk radius')
    root_length_random: FloatProperty(name='Reach Variation',default=.2,min=0,max=.8)
    root_width: FloatProperty(name='Base Width',default=.52,min=.05,max=2,description='Root base radius relative to trunk radius')
    root_departure: FloatProperty(name='Departure',default=.24,min=0,max=.8,description='Start roots partway toward the trunk surface instead of all at its center')
    root_tip: FloatProperty(name='Tip Width',default=.12,min=.01,max=.6,description='Tip radius as a fraction of base radius')
    root_taper: FloatProperty(name='Root Taper',default=.8,min=.2,max=4)
    root_tip_bury: FloatProperty(name='Tip Burial',default=.65,min=0,max=2,description='Sink the last part of an automatic root below the ground by a fraction of its base width')
    root_spread: FloatProperty(name='Angle Variation',default=.22,min=0,max=1.2,subtype='ANGLE')
    root_wander: FloatProperty(name='Wander',default=.55,min=0,max=3)
    root_lift: FloatProperty(name='Arch Height',default=.45,min=0,max=4)
    root_sink: FloatProperty(name='Ground Embed',default=.35,min=0,max=1,subtype='FACTOR')
    root_flatten: FloatProperty(name='Vertical Flatten',default=.72,min=.1,max=1,subtype='FACTOR')
    root_buttress_height: FloatProperty(name='Buttress Height',default=1.7,min=.3,max=3,description='Vertical flare at the trunk end of buttress roots')
    root_forks: IntProperty(name='Side Forks',default=1,min=0,max=3)
    root_fork_start: FloatProperty(name='Fork Start',default=.42,min=.1,max=.8,subtype='FACTOR',description='Position of the first side fork along each primary root')
    root_fork_angle: FloatProperty(name='Fork Angle',default=.6,min=.05,max=1.5,subtype='ANGLE')
    root_fork_reach: FloatProperty(name='Fork Reach',default=.5,min=.1,max=1.2,description='Side fork length as a fraction of its parent')
    root_fork_width: FloatProperty(name='Fork Width',default=.46,min=.05,max=.9,description='Side fork base radius as a fraction of its parent')
    root_segments: IntProperty(name='Path Segments',default=6,min=3,max=16)
    root_seed: IntProperty(name='Root Seed',default=137,min=0)
    root_ground: PointerProperty(name='Ground Mesh',type=bpy.types.Object,description='Optional mesh to follow through downward raycasts')
    root_ground_follow: FloatProperty(name='Ground Follow',default=1,min=0,max=1,subtype='FACTOR')
    root_ground_offset: FloatProperty(name='Ground Offset',default=0,min=-2,max=2,subtype='DISTANCE')
    count: IntProperty(default=12, min=1, max=100, update=live_distribution_changed)
    cluster_planes: IntProperty(name='Quads per Canopy Cluster',default=3,min=1,max=8,
                                 description='Editable crossed quad cards used for each branch-led crown mass')
    frond_width: FloatProperty(name='Blade / Frond Width',default=1.2,min=.01,update=live_distribution_changed)
    frond_leaf_width: FloatProperty(name='Leaflet Width',default=.14,min=.005,update=live_distribution_changed)
    frond_taper: FloatProperty(name='Tip Taper',default=.8,min=0,max=.98,update=live_distribution_changed)
    frond_petiole: FloatProperty(name='Bare Stem Fraction',default=.15,min=0,max=.8,update=live_distribution_changed)
    frond_angle: FloatProperty(name='Leaf Sweep',default=.35,min=-1.3,max=1.3,subtype='ANGLE',update=live_distribution_changed)
    frond_droop: FloatProperty(name='Rachis Droop',default=.25,min=-1,max=1.5,update=live_distribution_changed)
    bough_clearance: FloatProperty(name='Trunk Clearance',default=.75,min=0,max=1,subtype='FACTOR',
                                   description='Move Needle Spray cards outward and shorten the hanging fill between tiers to reveal the trunk')
    bough_arch: FloatProperty(name='Lengthwise Arch',default=0,min=-.65,max=.65,
                              description='Curve each Needle Spray card along its length')
    bough_fold: FloatProperty(name='Side Droop',default=.29,min=-.65,max=.65,
                              description='Lower both sides of the Needle Spray card from its fixed midrib')
    frond_leaf_droop: FloatProperty(name='Leaflet Droop',default=.15,min=-1,max=1,update=live_distribution_changed)
    frond_stem_radius: FloatProperty(name='Rachis Radius',default=.012,min=.001,max=.25,update=live_distribution_changed)
    frond_stem_tip: FloatProperty(name='Rachis Tip Radius',default=.08,min=.01,max=1,description='Tip radius as a fraction of base radius',update=live_distribution_changed)
    frond_stem_sides: IntProperty(name='Rachis Radial Sides',default=10,min=3,max=32,description='High-detail radial sides of a live frond rachis; Mid/Low reduce this count',update=live_distribution_changed)
    frond_segments: IntProperty(name='Rachis Segments',default=8,min=2,max=24,update=live_distribution_changed)
    frond_whorl: IntProperty(name='Leaves per Whorl',default=3,min=2,max=8,update=live_distribution_changed)
    blade_edge_tear: FloatProperty(name='Blade Edge Tear',default=.28,min=0,max=.9,subtype='FACTOR',description='Retract random edge sections of Broad Lamina while keeping the midrib intact',update=live_distribution_changed)
    blade_tear_chance: FloatProperty(name='Tear Frequency',default=.38,min=0,max=1,subtype='FACTOR',description='Chance for an edge vertex to form a tear; left and right edges vary independently',update=live_distribution_changed)
    blade_tear_seed: IntProperty(name='Tear Seed',default=409,min=0,description='Changes blade edge tears without moving the fronds',update=live_distribution_changed)
    palm_card_mode: EnumProperty(name='Palm Frond Card Mode',
        items=[('AUTO','Auto (Single on Trees)','Single card on Trees, leaflets on Foliage controller'),
               ('SINGLE','Single Continuous Card','One solid stylized blade per frond branch'),
               ('LEAFLETS','Paired Leaflets','Separate individual leaflet cards along the rachis')],
        default='AUTO', description='Choose between 1 solid continuous card per branch or separate leaflet cards',
        update=live_distribution_changed)
    ivy_start: FloatVectorProperty(name='Growth Seed (Local)',size=3,default=(0,0,0),subtype='TRANSLATION',update=live_distribution_changed)
    ivy_direction: FloatVectorProperty(name='Growth Direction',size=3,default=(0,0,1),update=live_distribution_changed)
    ivy_step: FloatProperty(name='Growth Step',default=.08,min=.01,max=1,update=live_distribution_changed)
    ivy_radius: FloatProperty(name='Vine Radius',default=.012,min=.001,max=.2,update=live_distribution_changed)
    ivy_vine_sides: IntProperty(name='Vine Radial Sides',default=12,min=3,max=32,description='Radial sides of the high-detail ivy vine; Mid and Low reduce this count',update=live_distribution_changed)
    ivy_leaf_spacing: FloatProperty(name='Leaf Spacing',default=.16,min=.02,max=2,update=live_distribution_changed)
    ivy_leaf_size: FloatProperty(name='Leaf Size',default=.32,min=.01,max=3,update=live_distribution_changed)
    ivy_leaf_spread: FloatProperty(name='Leaf Spread Angle',default=1.1,min=0,max=1.57,subtype='ANGLE',update=live_distribution_changed)
    ivy_offset: FloatProperty(name='Surface Offset',default=.025,min=0,max=1,update=live_distribution_changed)
    ivy_probe: FloatProperty(name='Surface Search Distance',default=.3,min=.01,max=5,update=live_distribution_changed)
    ivy_gap_bridge: FloatProperty(name='Gap Bridge (Steps)',default=1,min=0,max=5,description='Maximum small disconnected surface gap, measured in Growth Steps; zero only crosses connected target surfaces',update=live_distribution_changed)
    ivy_corner_limit: FloatProperty(name='Corner Angle Limit',default=math.radians(145),min=math.radians(45),max=math.radians(179),subtype='ANGLE',description='Maximum angle between adjacent target faces that Ivy will follow',update=live_distribution_changed)
    ivy_projection: EnumProperty(name='Curve Surface Projection',items=[
        ('NEAREST','Nearest Surface','Project to the closest evaluated surface point'),
        ('DOWN','Ray Down','Cast from the guide toward generator-local negative Z'),
        ('CUSTOM','Custom Ray','Cast from the guide along the chosen generator-local direction')],
        default='NEAREST',description='Projection for Curve guides on a mesh target; press Regenerate after changing')
    ivy_ray_direction: FloatVectorProperty(name='Ray Direction (Local)',size=3,default=(0,0,-1),
        description='Nonzero ray direction in generator local coordinates',update=live_distribution_changed)
    ivy_wander: FloatProperty(name='Growth Wander',default=.35,min=0,max=1.5,subtype='ANGLE',update=live_distribution_changed)
    ivy_up_bias: FloatProperty(name='Direction Bias',default=.12,min=0,max=1)
    ivy_branches: IntProperty(name='Side Vines',default=4,min=0,max=32,update=live_distribution_changed)
    ivy_branch_spacing: FloatProperty(name='Branch Interval',default=.6,min=.1,max=10,update=live_distribution_changed)
    ivy_branch_angle: FloatProperty(name='Branch Angle',default=.8,min=.1,max=1.5,subtype='ANGLE',update=live_distribution_changed)
    ivy_branch_length: FloatProperty(name='Side Vine Length Ratio',default=.55,min=.05,max=1,update=live_distribution_changed)
    ivy_max_steps: IntProperty(name='Growth Step Budget',default=10000,min=50,max=100000,update=live_distribution_changed)
    size_min: FloatProperty(default=.7, min=.01)
    size_max: FloatProperty(default=1.2, min=.01)
    scale_axes: FloatVectorProperty(size=3, default=(1,1,1), min=.01)
    axis_min: FloatVectorProperty(name='Random Axis Scale Min',size=3,default=(1,1,1),min=.01)
    axis_max: FloatVectorProperty(name='Random Axis Scale Max',size=3,default=(1,1,1),min=.01)
    size_seed: IntProperty(name='Axis Scale Seed',default=29,min=0,update=live_distribution_changed)
    yaw: FloatProperty(default=math.pi, min=0, max=math.pi, subtype='ANGLE')
    pitch: FloatProperty(default=.5, min=0, max=math.pi, subtype='ANGLE')
    roll: FloatProperty(default=.5, min=0, max=math.pi, subtype='ANGLE')
    jitter: FloatProperty(default=.05, min=0)
    hue_min: FloatProperty(default=-.03, min=-.5, max=.5)
    hue_max: FloatProperty(default=.03, min=-.5, max=.5)
    saturation_min: FloatProperty(default=.8, min=0, max=2)
    saturation_max: FloatProperty(default=1.2, min=0, max=2)
    value_min: FloatProperty(default=.7, min=0, max=2)
    value_max: FloatProperty(default=1.2, min=0, max=2)
    color: FloatVectorProperty(size=3, subtype='COLOR', default=(.35,.65,.08), min=0, max=1)
    tint_min: FloatVectorProperty(name='Tint Min',size=3,subtype='COLOR',default=(1,1,1),min=0,max=1)
    tint_max: FloatVectorProperty(name='Tint Max',size=3,subtype='COLOR',default=(1,1,1),min=0,max=1)
    bark: FloatVectorProperty(size=3, subtype='COLOR', default=(.26,.12,.05), min=0, max=1)
    opacity_min: FloatProperty(default=1, min=0, max=1)
    opacity_max: FloatProperty(default=1, min=0, max=1)
    alpha_mode: EnumProperty(items=enum(['Cutout','Soft']), default='Cutout')
    stylized_normals: BoolProperty(name='Stylized Normals', default=True,
        description='Direct foliage card normals outwards from canopy mass for soft volumetric stylized shading')
    normal_bend_factor: FloatProperty(name='Normal Spherical Blend', default=.85, min=0, max=1,
        description='1.0 gives full spherical fluffy shading; 0.0 retains geometric card normals')
    normal_up_bias: FloatProperty(name='Normal Upward Bias', default=.25, min=0, max=1,
        description='Tilts foliage normals slightly upwards towards sunlight')
    card: EnumProperty(items=enum(['Quad','Valley']), default='Quad')
    valley: FloatProperty(default=.08, min=-1, max=1,update=live_distribution_changed)
    bend: FloatProperty(default=.1, min=-3, max=3,update=live_distribution_changed)
    twist: FloatProperty(default=0, min=-3, max=3,update=live_distribution_changed)
    curl: FloatProperty(default=0, min=-3, max=3)
    card_taper: FloatProperty(name='Card Tip Taper',default=0,min=0,max=.98)
    random_card_shape: BoolProperty(name='Randomize Card Bend / Valley',default=False)
    shape_seed: IntProperty(name='Card Shape Seed',default=83,min=0,update=live_distribution_changed)
    bend_min: FloatProperty(name='Bend Min',default=-.1,min=-3,max=3)
    bend_max: FloatProperty(name='Bend Max',default=.2,min=-3,max=3)
    valley_min: FloatProperty(name='Valley Min',default=-.1,min=-1,max=1)
    valley_max: FloatProperty(name='Valley Max',default=.1,min=-1,max=1)
    subdivisions: IntProperty(default=1, min=1, max=12)
    textures: CollectionProperty(type=LPTexture)
    surfaces: CollectionProperty(type=surfaces.LPSurface)
    texture_index: IntProperty(default=0)
    crown: FloatProperty(default=.55, min=.01)
    thickness: FloatProperty(default=.18, min=.01)
    cluster: IntProperty(default=1, min=1, max=100)
    auto_bend: FloatProperty(default=.85, min=0, max=1)
    mushroom_stem_taper: FloatProperty(name='Stem Taper',default=.35,min=0,max=.92)
    mushroom_rim: FloatProperty(name='Cap Rim Lift',default=0,min=-.5,max=.5)
    mushroom_gills: IntProperty(name='Underside Gills',default=12,min=0,max=48)
    mushroom_cap_facets: IntProperty(name='Cap Facets',default=12,min=6,max=48)
    mushroom_cap_rings: IntProperty(name='Cap Rings',default=6,min=2,max=16)
    rock_axes: FloatVectorProperty(name='Rock Proportions',size=3,default=(1,1,1),min=.1,max=5,description='Width, depth and height of each rock')
    rock_facets: IntProperty(name='Rock Facet Detail',default=4,min=1,max=4,description='Base solid mesh subdivision; Solid Mesh Detail scales it for each LOD')
    rock_erosion: FloatProperty(name='Edge Erosion',default=.22,min=0,max=1,description='Irregular layered wear on rock edges and faces')
    rock_cracks: IntProperty(name='Crack Paths',default=2,min=0,max=12)
    rock_crack_width: FloatProperty(name='Crack Width',default=.1,min=.01,max=.5,subtype='ANGLE')
    rock_crack_depth: FloatProperty(name='Crack Depth',default=.1,min=0,max=.5,description='Depth of the angular creases in rock geometry')
    rock_moss: FloatProperty(name='Moss Coverage',default=.2,min=0,max=1,subtype='FACTOR')
    rock_color: FloatVectorProperty(name='Rock Color',size=3,subtype='COLOR',default=(.38,.43,.44),min=0,max=1)
    rock_crack_color: FloatVectorProperty(name='Crack Color',size=3,subtype='COLOR',default=(.12,.16,.16),min=0,max=1)
    rock_moss_color: FloatVectorProperty(name='Moss Color',size=3,subtype='COLOR',default=(.24,.36,.24),min=0,max=1)
    mushroom_cluster_radius: FloatProperty(name='Cluster Spread',default=.55,min=0,max=10)
    mushroom_bend_random: FloatProperty(name='Stem Bend Random',default=.08,min=0,max=2)
    mushroom_bend_threshold: FloatProperty(name='Crown Tilt Random',default=.1,min=0,max=math.pi/2,subtype='ANGLE')
    glow: EnumProperty(items=enum(['None','Under','Cap','All']), default='None')
    glow_strength: FloatProperty(default=3, min=0, max=100)
    glow_color: FloatVectorProperty(size=3, subtype='COLOR', default=(.1,.7,1), min=0, max=1)
    material_style: EnumProperty(items=enum(['Smooth','Bands','Speckles','Grain','Moss','Cracks']), default='Smooth')
    snap_offset: FloatProperty(default=.02)
    snap_mode: EnumProperty(name='Snap Mode',items=[('DOWN','Ray Down','Raycast toward world down'),('CUSTOM','Custom Ray','Raycast in a chosen world direction'),('NEAREST','Nearest Surface','Find the nearest evaluated triangle')],default='DOWN')
    snap_direction: FloatVectorProperty(name='Ray Direction (World)',size=3,default=(0,0,-1))
    snap_distance: FloatProperty(name='Snap Distance',default=10,min=.01,max=1000)
    ornament: PointerProperty(type=bpy.types.Object)
    ornaments_enabled: BoolProperty(default=False,name='Enable Ornaments')
    ornament_type: EnumProperty(name='Ornament Type',items=[
        ('CUSTOM','Custom Object','Place the chosen source object on eligible plant surfaces'),
        ('FLOWER','Flowers','Place flowers on foliage or branch surfaces'),
        ('BUD','Flower Buds','Place compact buds at branch nodes'),
        ('SEED_POD','Seed Pods','Place pods along mature branches'),
    ],default='CUSTOM',update=live_ornament_changed)
    ornament_slots: CollectionProperty(type=ornaments.LPOrnamentSlot)
    ornament_density: FloatProperty(default=.8, min=0, max=10000,name='Ornaments / m²',update=live_ornament_changed)
    ornament_limit: IntProperty(default=150,min=1,max=10000,update=live_ornament_changed)
    ornament_zone: EnumProperty(items=[('FOLIAGE','Foliage / Crown','Attach to foliage cards'),('WOOD','Trunk / Branches','Attach to non-card surfaces'),('ALL','All Surfaces','Use all faces')],default='FOLIAGE')
    ornament_branch_id: IntProperty(name='Branch ID',default=-1,min=-1,description='-1 uses all branches; choose a face and Pick Branch to target one semantic branch')
    ornament_spacing: FloatProperty(default=.15,min=0,update=live_ornament_changed)
    ornament_height_min: FloatProperty(default=0,min=0,max=1,update=live_ornament_changed)
    ornament_height_max: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    ornament_offset: FloatProperty(default=.02,update=live_ornament_changed)
    ornament_seed: IntProperty(default=37,min=0,update=live_ornament_changed)
    ornament_choice_seed: IntProperty(default=53,min=0,update=live_ornament_changed)
    ornament_transform_seed: IntProperty(default=71,min=0,update=live_ornament_changed)
    ornament_color_seed: IntProperty(default=91,min=0,update=live_ornament_changed)
    ornament_size_min: FloatProperty(default=.7,min=.001,update=live_ornament_changed)
    ornament_size_max: FloatProperty(default=1.2,min=.001,update=live_ornament_changed)
    ornament_axes: FloatVectorProperty(size=3,default=(1,1,1),min=.001,update=live_ornament_changed)
    ornament_yaw: FloatProperty(default=math.pi,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    ornament_pitch: FloatProperty(default=.2,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    ornament_roll: FloatProperty(default=.2,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    ornament_color: FloatVectorProperty(size=3,subtype='COLOR',default=(1,1,1),min=0,max=1,update=live_ornament_changed)
    ornament_hue_min: FloatProperty(default=0,min=-.5,max=.5,update=live_ornament_changed)
    ornament_hue_max: FloatProperty(default=0,min=-.5,max=.5,update=live_ornament_changed)
    ornament_sat_min: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    ornament_sat_max: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    ornament_value_min: FloatProperty(default=.8,min=0,max=2,update=live_ornament_changed)
    ornament_value_max: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    ornament_opacity_min: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    ornament_opacity_max: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    ornament_status: StringProperty(default='No ornaments generated')
    fruit_enabled: BoolProperty(default=False,name='Enable Fruit')
    fruit_type: EnumProperty(name='Fruit Type',items=fruit_type_items,default=0,update=live_ornament_changed,
                             description='Placement options follow the selected trunk architecture; choose Custom for free placement')
    fruit_slots: CollectionProperty(type=ornaments.LPOrnamentSlot)
    fruit_density: FloatProperty(name='Fruit / m²',default=5,min=0,max=10000,update=live_ornament_changed)
    fruit_limit: IntProperty(default=150,min=1,max=10000,update=live_ornament_changed)
    fruit_zone: EnumProperty(name='Manual Surface Zone',items=[('FOLIAGE','Foliage / Crown','Attach to foliage cards'),('WOOD','Trunk / Branches','Attach to wood surfaces'),('ALL','All Surfaces','Use all faces')],default='WOOD',update=live_ornament_changed)
    fruit_height_min: FloatProperty(default=0,min=0,max=1,update=live_ornament_changed)
    fruit_height_max: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    fruit_spacing: FloatProperty(default=.15,min=0,update=live_ornament_changed)
    fruit_offset: FloatProperty(default=.02,update=live_ornament_changed)
    fruit_seed: IntProperty(default=137,min=0,update=live_ornament_changed)
    fruit_choice_seed: IntProperty(default=157,min=0,update=live_ornament_changed)
    fruit_transform_seed: IntProperty(default=173,min=0,update=live_ornament_changed)
    fruit_color_seed: IntProperty(default=191,min=0,update=live_ornament_changed)
    fruit_size_min: FloatProperty(default=.7,min=.001,update=live_ornament_changed)
    fruit_size_max: FloatProperty(default=1.2,min=.001,update=live_ornament_changed)
    fruit_axes: FloatVectorProperty(name='Scale Axes',size=3,default=(1,1,1),min=.001,update=live_ornament_changed)
    fruit_yaw: FloatProperty(default=math.pi,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    fruit_pitch: FloatProperty(default=.2,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    fruit_roll: FloatProperty(default=.2,min=0,max=math.pi,subtype='ANGLE',update=live_ornament_changed)
    fruit_color: FloatVectorProperty(size=3,subtype='COLOR',default=(1,1,1),min=0,max=1,update=live_ornament_changed)
    fruit_hue_min: FloatProperty(default=0,min=-.5,max=.5,update=live_ornament_changed)
    fruit_hue_max: FloatProperty(default=0,min=-.5,max=.5,update=live_ornament_changed)
    fruit_sat_min: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    fruit_sat_max: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    fruit_value_min: FloatProperty(default=.8,min=0,max=2,update=live_ornament_changed)
    fruit_value_max: FloatProperty(default=1,min=0,max=2,update=live_ornament_changed)
    fruit_opacity_min: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    fruit_opacity_max: FloatProperty(default=1,min=0,max=1,update=live_ornament_changed)
    fruit_status: StringProperty(default='No fruit generated')
    wind: FloatProperty(default=.08, min=0, max=2,update=wind_changed)
    wind_speed: FloatProperty(default=1.4, min=0, max=10,update=wind_changed)
    wind_phase: FloatProperty(default=0,update=wind_changed)
    wind_direction: FloatProperty(default=0, subtype='ANGLE',update=wind_changed)
    wind_gust: FloatProperty(name='Gust Strength',default=0,min=0,max=3,update=wind_changed)
    wind_turbulence: FloatProperty(name='Turbulence',default=0,min=0,max=2,update=wind_changed)
    wind_trunk: FloatProperty(name='Trunk / Stem Sway',default=1,min=0,max=3,description='Movement of the trunk or base stem',update=wind_changed)
    wind_branch: FloatProperty(name='Branch Bend',default=1,min=0,max=3,description='Extra branch motion, inherited by child branches and attached foliage',update=wind_changed)
    wind_cluster: FloatProperty(name='Cluster Sway',default=.25,min=0,max=3,description='Slow card motion that stays anchored at its base',update=wind_changed)
    wind_flutter: FloatProperty(name='Leaf Flutter',default=0,min=0,max=2,update=wind_changed)
    wind_response: FloatProperty(name='Asset Response',default=1,min=0,max=3,description='Local multiplier even when sharing a controller',update=wind_changed)
    wind_phase_offset: FloatProperty(name='Asset Phase Offset',default=0,subtype='ANGLE',update=wind_changed)
    wind_use_controller: BoolProperty(name='Use Controller Settings',default=True,description='When off, use this asset wind parameters even if a shared controller is assigned',update=wind_link_changed)
    mid_ratio: FloatProperty(default=.5, min=.01, max=1)
    low_ratio: FloatProperty(default=.2, min=.01, max=1)
    mid_texture_scale: FloatProperty(name='Mid Texture Scale',default=.5,min=.0625,max=1,subtype='FACTOR',description='Fraction of each image dimension in the Mid variant')
    low_texture_scale: FloatProperty(name='Low Texture Scale',default=.25,min=.0625,max=1,subtype='FACTOR',description='Fraction of each image dimension in the Low variant')
    mid_triangle_limit: IntProperty(name='Mid Triangle Limit',default=0,min=0,description='0 disables the hard limit; below the wood and one-card minimum it is reported as unmet')
    low_triangle_limit: IntProperty(name='Low Triangle Limit',default=0,min=0,description='0 disables the hard limit; below the wood and one-card minimum it is reported as unmet')
    resolution: EnumProperty(items=enum(['256','512','1024','2048']), default='2048')
    flat_mode: EnumProperty(name='Flat Mode',items=[('SINGLE','Single View','One front billboard'),('MULTI8','Eight Azimuth Views','4 x 2 atlas with camera-selected billboard faces')],default='SINGLE')
    with_normals: BoolProperty(default=False)
    keep_wind: BoolProperty(default=True)
    build_collection: PointerProperty(type=bpy.types.Collection)
    game_export_dir: StringProperty(name='Game Export Folder',default='//Landscapy_Exports',subtype='DIR_PATH')
    bake_directory: StringProperty(name='Flat Bake Directory',default='//Landscapy_Bakes',subtype='DIR_PATH',description='Save the blend first when using a relative Flat bake folder')
    status: StringProperty()

def mesh_object(name, verts, faces, collection, mat=None):
    me=bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob=bpy.data.objects.new(name, me); collection.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

def material(name, color, style='Smooth', image=None, alpha='Soft', glow=0):
    # Share materials by appearance; per-card color comes from mesh attributes.
    key=f'LP::{name}::{tuple(round(c,3) for c in color)}::{style}::{image.name if image else ""}::{alpha}::{glow}'
    if key in bpy.data.materials: return bpy.data.materials[key]
    m=bpy.data.materials.new(key); m.use_nodes=True; m['lp_role']=name; nt=m.node_tree; n=nt.nodes; L=nt.links.new
    p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=.85
    if image:
        tex=n.new('ShaderNodeTexImage'); tex.image=image; tex.extension='CLIP'
        a=n.new('ShaderNodeAttribute'); a.attribute_name='lp_color'
        mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1
        L(tex.outputs['Color'],mix.inputs[1]); L(a.outputs['Color'],mix.inputs[2]); L(mix.outputs[0],p.inputs['Base Color'])
        opa=n.new('ShaderNodeAttribute'); opa.attribute_name='lp_opacity'
        mul=n.new('ShaderNodeMath'); mul.operation='MULTIPLY'; L(tex.outputs['Alpha'],mul.inputs[0]); L(opa.outputs['Fac'],mul.inputs[1])
        out=mul.outputs[0]
        if alpha=='Cutout':
            cut=n.new('ShaderNodeMath'); cut.operation='GREATER_THAN'; cut.inputs[1].default_value=.45; L(out,cut.inputs[0]); out=cut.outputs[0]
        L(out,p.inputs['Alpha'])
    elif style!='Smooth':
        noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value={'Grain':12,'Bands':3,'Speckles':24,'Moss':4,'Cracks':8}.get(style,8)
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(*(c*.4 for c in color),1); ramp.color_ramp.elements[1].color=(*(min(1,c*1.5) for c in color),1)
        L(noise.outputs['Fac'],ramp.inputs[0]); L(ramp.outputs[0],p.inputs['Base Color'])
    if glow: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=glow
    return m

def billboard_material(image,lit=False):
    mat=material('Lit Billboard' if lit else 'Unlit Billboard',(1,1,1),image=image)
    if not lit:
        tree=mat.node_tree; principled=tree.nodes['Principled BSDF']
        base=principled.inputs['Base Color']
        if base.is_linked:
            source=base.links[0].from_socket
            tree.links.new(source,principled.inputs['Emission Color'])
            tree.links.remove(base.links[0])
        base.default_value=(0,0,0,1)
        principled.inputs['Emission Strength'].default_value=1
    return mat

class Builder:
    def __init__(self,detail_scale=2): self.detail_scale=detail_scale; self.v=[]; self.f=[]; self.uv=[]; self.col=[]; self.opacity=[]; self.mi=[]; self.card_flags=[]; self.card_ids=[]; self.next_card_id=0; self.leaf_wind=[]; self.cluster_phase=[]; self.card_phase=[]; self.cluster_wind_scale=1.5; self.branch_ids=[]; self.branch_levels=[]; self.branch_t=[]
    def add(self, vs, fs, color=(1,1,1), opacity=1, uv=None, mat=0, card=False, wind_weights=None, branch_id=-1, branch_level=-1, branch_t=None):
        k=len(self.v); self.v.extend(tuple(v) for v in vs); self.col.extend([(*color,1)]*len(vs)); self.opacity.extend([opacity]*len(vs))
        self.leaf_wind.extend(wind_weights if wind_weights is not None else [float(card)]*len(vs))
        self.branch_ids.extend([branch_id]*len(vs)); self.branch_levels.extend([branch_level]*len(vs))
        self.branch_t.extend(branch_t if branch_t is not None else [0.]*len(vs))
        card_id=self.next_card_id if card else -1
        if card:
            # Nearby cards share a slow cluster phase; each keeps an independent
            # high-frequency flutter phase. A branch ID takes precedence so all
            # cards attached to that branch sway together across cell borders.
            if branch_id>=0: cluster_key=branch_id
            else:
                center=sum((Vector(point) for point in vs),Vector())/len(vs)
                cell=[math.floor(component/max(.2,self.cluster_wind_scale)) for component in center]
                cluster_key=cell[0]*157+cell[1]*263+cell[2]*379
            cluster_phase=(cluster_key*2.399963229728653)%math.tau
            card_phase=(card_id*2.399963229728653)%math.tau
        else: cluster_phase=card_phase=0.
        self.cluster_phase.extend([cluster_phase]*len(vs))
        self.card_phase.extend([card_phase]*len(vs))
        if card: self.next_card_id+=1
        for f in fs:
            self.f.append(tuple(k+i for i in f)); self.mi.append(mat); self.card_flags.append(card); self.card_ids.append(card_id)
            if uv:
                self.uv.extend(uv[i] for i in f)
            else:
                # Solid props previously had all-zero UVs. Project each face in
                # its dominant plane; mapping controls set repetition/scale.
                a,b,c=[Vector(vs[i]) for i in f[:3]]
                normal=(b-a).cross(c-a); axis=max(range(3),key=lambda j:abs(normal[j]))
                axes=[j for j in range(3) if j!=axis]
                self.uv.extend((vs[i][axes[0]],vs[i][axes[1]]) for i in f)
    def tube(self,path,radius,sides=8,end=.05,mat=0,branch_id=-1,branch_level=-1,collar=0.,branch_extent=1.):
        path=[Vector(point) for point in path]
        steps=max(1,math.ceil(self.detail_scale))
        if steps>1:
            smooth=[]
            for i in range(len(path)-1):
                p0=path[max(0,i-1)]; p1=path[i]; p2=path[i+1]; p3=path[min(len(path)-1,i+2)]
                for j in range(steps):
                    t=j/steps; t2=t*t; t3=t2*t
                    smooth.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
            path=smooth+[path[-1]]
        sides=max(3,round(sides*self.detail_scale))
        vs=[]; fs=[]
        for i,(p,(x,y)) in enumerate(zip(path,tube_frames.frames(path))):
            fraction=i/(len(path)-1)
            p=Vector(p)
            r=radius*(1-(1-end)*fraction)
            if collar:
                r=radius*(end+(1-end)*(1-fraction)**.76+collar*max(0.,1-4*fraction)**2)
            vs.extend(p+r*(x*math.cos(a*math.tau/sides)+y*math.sin(a*math.tau/sides)) for a in range(sides))
        fs.append(tuple(reversed(range(sides))))
        for j in range(len(path)-1):
            for i in range(sides): fs.append((j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i))
        fs.append(tuple((len(path)-1)*sides+i for i in range(sides)))
        uv_start=len(self.uv); self.add(vs,fs,mat=mat,branch_id=branch_id,branch_level=branch_level,branch_t=[branch_extent*i/(len(path)-1) for i in range(len(path)) for _ in range(sides)])
        # Cylindrical unwrap on each side strip, with a real 0/1 seam.
        cursor=uv_start+sides; distances=[0.]
        for a,b in zip(path,path[1:]): distances.append(distances[-1]+(Vector(b)-Vector(a)).length)
        for j in range(len(path)-1):
            for i in range(sides):
                self.uv[cursor:cursor+4]=[(i/sides,distances[j]),((i+1)/sides,distances[j]),((i+1)/sides,distances[j+1]),(i/sides,distances[j+1])]; cursor+=4
    def finish(self,ob,mats):
        old=ob.data; me=bpy.data.meshes.new(ob.name); me.from_pydata(self.v,[],self.f); me.update(); ob.data=me
        if old and old.users==0: bpy.data.meshes.remove(old)
        for m in mats: me.materials.append(m)
        for p,i,card in zip(me.polygons,self.mi,self.card_flags):
            p.material_index=i
            p.use_smooth=not card and self.detail_scale>=1.5
        flags=me.attributes.new('lp_card','BOOLEAN','FACE')
        for item,value in zip(flags.data,self.card_flags): item.value=value
        ids=me.attributes.new('lp_card_id','INT','FACE')
        for item,value in zip(ids.data,self.card_ids): item.value=value
        for name,kind,values,field in [('lp_branch_id','INT',self.branch_ids,'value'),('lp_branch_level','INT',self.branch_levels,'value'),('lp_branch_t','FLOAT',self.branch_t,'value')]:
            attr=me.attributes.new(name,kind,'POINT')
            for item,value in zip(attr.data,values): setattr(item,field,value)
        uv=me.uv_layers.new(name='UVMap')
        for d,c in zip(uv.data,self.uv): d.uv=c
        for name,typ,values,field in [('lp_color','FLOAT_COLOR',self.col,'color'),('lp_opacity','FLOAT',self.opacity,'value')]:
            a=me.attributes.new(name,typ,'POINT')
            for d,v in zip(a.data,values): setattr(d,field,v)
        h=max([v[2] for v in self.v]+[.01]); a=me.attributes.new('lp_wind','FLOAT','POINT')
        for d,v in zip(a.data,self.v): d.value=max(0,v[2]/h)**2
        a=me.attributes.new('lp_leaf_wind','FLOAT','POINT')
        for d,v in zip(a.data,self.leaf_wind): d.value=v
        branch_cos,branch_sin=branch_wind_fields(ob,self.branch_ids,self.branch_t)
        for name,values in [('lp_branch_wind_cos',branch_cos),
                            ('lp_branch_wind_sin',branch_sin),
                            ('lp_cluster_phase',self.cluster_phase),
                            ('lp_card_phase',self.card_phase)]:
            attr=me.attributes.new(name,'FLOAT','POINT')
            for item,value in zip(attr.data,values): item.value=value
        s=getattr(ob,'landscapy',None)
        use_stylized_normals=getattr(s,'stylized_normals',True) if s else True
        if use_stylized_normals and any(self.card_flags):
            for p,card in zip(me.polygons,self.card_flags):
                if card: p.use_smooth=True
            card_verts={vi for p,card in zip(me.polygons,self.card_flags) if card for vi in p.vertices}
            card_coords=[me.vertices[i].co for i in card_verts]
            center=(sum(card_coords,Vector())/len(card_coords)-Vector((0,0,.45))) if card_coords else Vector((0,0,2.5))
            blend_fac=getattr(s,'normal_bend_factor',.85) if s else .85
            up_bias=getattr(s,'normal_up_bias',.25) if s else .25
            normals=[]
            for idx,v in enumerate(me.vertices):
                if idx in card_verts:
                    diff=v.co-center; rad=diff.normalized() if diff.length>1e-4 else Vector((0,0,1))
                    normals.append(tuple((rad*blend_fac+Vector((0,0,up_bias))).normalized()))
                else:
                    normals.append(tuple(v.normal))
            try: me.normals_split_custom_set_from_vertices(normals)
            except Exception: pass

def branch_wind_fields(owner,branch_ids,branch_ts):
    """Bake each branch's inherited bend into two phase coefficients per vertex."""
    raw=owner.get('lp_branch_graph')
    if not raw: return [0.]*len(branch_ids),[0.]*len(branch_ids)
    try: graph={row['id']:row for row in json.loads(raw)['branches']}
    except (KeyError,TypeError,ValueError): return [0.]*len(branch_ids),[0.]*len(branch_ids)
    attachments={}
    for branch_id,row in graph.items():
        parent=graph.get(row['parent'])
        if not parent: continue
        path=[Vector(point) for point in parent['points']]
        start=Vector(row['points'][0])
        best=(float('inf'),0.)
        for i,(a,b) in enumerate(zip(path,path[1:])):
            delta=b-a
            along=max(0.,min(1.,(start-a).dot(delta)/max(1e-12,delta.length_squared)))
            distance=(start-a-delta*along).length_squared
            if distance<best[0]: best=(distance,(i+along)/(len(path)-1))
        attachments[branch_id]=best[1]
    cache={}
    def coefficient(branch_id,t):
        if branch_id<=0 or branch_id not in graph: return (0.,0.)
        key=(branch_id,t)
        if key in cache: return cache[key]
        row=graph[branch_id]
        base=coefficient(row['parent'],attachments.get(branch_id,0.))
        path=[Vector(point) for point in row['points']]
        length=sum((b-a).length for a,b in zip(path,path[1:]))
        amplitude=.22*min(1.4,length/1.6)*(.72**(row['level']-1))*t*t
        phase=branch_id*2.399963229728653
        result=(base[0]+amplitude*math.cos(phase),base[1]+amplitude*math.sin(phase))
        cache[key]=result
        return result
    fields=[coefficient(branch_id,t) for branch_id,t in zip(branch_ids,branch_ts)]
    return [item[0] for item in fields],[item[1] for item in fields]

def tree_guides(controller,owner):
    evaluated=paths.curve_paths(controller)
    if not evaluated: raise ValueError('Tree curve controller needs a trunk spline')
    inverse=owner.matrix_world.inverted()
    return [[inverse@point for point in spline] for spline in evaluated]

def distribution(s, ob):
    rng=random.Random(s.seed); ctrl=s.controller; inv=ob.matrix_world.inverted()
    if s.mode=='Individual': return [(Vector((0,0,0)),Vector((0,0,1)))]
    if not ctrl:
        if s.kind=='Foliage' and s.pattern=='Cloud' and s.canopy_mode=='COVER':
            radius=s.cluster_radius/.75
            return canopy.sample(s,[(Vector((0,0,radius)),Vector((radius,radius,radius)))])
        return [(Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(0,2))),Vector((0,0,1))) for _ in range(min(s.limit,int(s.density*4)))]
    if ctrl.type=='CURVE':
        if s.mode not in ['Auto','Path']: raise ValueError('Curve controllers support Auto or Path distribution')
        out=[]
        for path in paths.curve_paths(ctrl):
            out.extend((inv@p,(inv.to_3x3()@t).normalized()) for p,t in paths.stations(path,s.density,s.limit-len(out)))
        return out
    if ctrl.type!='MESH': raise ValueError('Controller must be a mesh or curve')
    if s.mode=='Path': raise ValueError('Path distribution requires a curve controller')
    ev=ctrl.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh(); me.calc_loop_triangles()
    try:
        bm=bmesh.new(); bm.from_mesh(me); closed=all(e.is_manifold for e in bm.edges) and bool(bm.faces); bm.free()
        mode=('Volume' if closed else 'Surface') if s.mode=='Auto' else s.mode
        if mode=='Volume' and not closed: raise ValueError('Volume requires a closed manifold mesh; use Surface for open meshes')
        if mode=='Surface' and s.gn_surface:
            if not me.loop_triangles: raise ValueError('Controller has no faces')
            group=ctrl.vertex_groups.get(s.mask) if s.mask else None
            return surface_distribution.points(s,ctrl,ob,me,group)
        verts=[ctrl.matrix_world@v.co for v in me.vertices]; tris=[tuple(t.vertices) for t in me.loop_triangles]
        if not tris: raise ValueError('Controller has no faces')
        bvh=BVHTree.FromPolygons(verts,tris,all_triangles=True); out=[]; grid={}; cell=max(s.spacing,1e-5)
        def accept(p,n):
            key=tuple(math.floor(c/cell) for c in p)
            if s.spacing:
                for x in (-1,0,1):
                    for y in (-1,0,1):
                        for z in (-1,0,1):
                            if any((p-q).length<s.spacing for q in grid.get((key[0]+x,key[1]+y,key[2]+z),[])): return
            grid.setdefault(key,[]).append(p); out.append((inv@p, ob.matrix_world.to_3x3().inverted()@n))
        if mode=='Volume':
            low=Vector([min(v[i] for v in verts) for i in range(3)]); high=Vector([max(v[i] for v in verts) for i in range(3)]); extent=high-low
            volume=abs(sum(verts[a].dot(verts[b].cross(verts[c]))/6 for a,b,c in tris)); count=min(s.limit,int(volume*s.density))
            for _ in range(max(100,count*30) if count else 0):
                p=Vector([rng.uniform(low[i],high[i]) for i in range(3)]); hit,n,_,_=bvh.find_nearest(p)
                if hit is not None and (p-hit).dot(n)<0: accept(p,Vector((0,0,1)))
                if len(out)>=count: break
        else:
            areas=[(verts[b]-verts[a]).cross(verts[c]-verts[a]).length*.5 for a,b,c in tris]; count=min(s.limit,int(sum(areas)*s.density))
            group=ctrl.vertex_groups.get(s.mask) if s.mask else None
            for _ in range(count):
                idx=rng.choices(range(len(tris)),weights=areas)[0]; tri=tris[idx]; a,b,c=[verts[i] for i in tri]; u=math.sqrt(rng.random()); v=rng.random(); weights=(1-u,u*(1-v),u*v)
                if group:
                    ws=[]
                    for vi in tri:
                        try: ws.append(group.weight(vi))
                        except RuntimeError: ws.append(0)
                    if rng.random()>sum(w*t for w,t in zip(ws,weights)): continue
                accept(a*weights[0]+b*weights[1]+c*weights[2],(b-a).cross(c-a).normalized())
        return out
    finally: ev.to_mesh_clear()

def starter_key(s):
    if s.kind=='Ivy': return 'Ivy'
    if s.kind=='Tree' and s.pattern=='Cloud' and s.preset in {'Willow','Acacia'}: return s.preset
    return s.pattern

def legacy_conifer_starter(slot):
    if slot.starter_pattern!='Conifer' or not slot.image:
        return False
    old_names={'Conifer_Leaflet_RGBA.png','Conifer_Needle_Spray_RGBA.png','Conifer_Needle_Spray_Dense_RGBA.png'}
    path=Path(bpy.path.abspath(slot.image.filepath,library=slot.image.library))
    return (path.name in old_names and
            tuple(part.lower() for part in path.parts[-3:-1])==('landscapy','textures'))

def starter_without_overrides(slot):
    return not slot.material_override and not any(
        getattr(slot,name) for name in surfaces.IMAGE_FIELDS if name!='image'
    )

def untouched_starter(slot):
    return (starter_without_overrides(slot) and bool(slot.starter_pattern) and
            (slot.image==default_image(slot.starter_pattern) or legacy_conifer_starter(slot)))

def default_image(pattern):
    names={'Palm':'Palm_Leaflet_RGBA.png','Banana':'Banana_Blade_RGBA.png','Conifer':'Conifer_Bough_RGBA.png',
           'Ivy':'Ivy_Leaf_RGBA.png','Flower':'Flower_Single_RGBA.png','Flower Cluster':'Flower_Cluster_RGBA.png',
           'Willow':'Willow_Cluster_RGBA.png','Acacia':'Acacia_Cluster_RGBA.png'}
    filename=names.get(pattern) or ('Broadleaf_Single_RGBA.png' if pattern in fronds.PATTERNS else 'Grass_Tuft_RGBA.png' if pattern in ['Grass','Tallgrass'] else 'Broadleaf_Cluster_RGBA.png')
    image=bpy.data.images.load(str(ROOT/'textures'/filename),check_existing=True)
    if not image.packed_file: image.pack()
    return image

def card_steps(builder,s,points,mats,batch_size=128):
    slots=[t for t in s.textures if (t.image or t.material_override) and t.weight>0]
    if not slots:
        t=s.textures.add(); t.starter_pattern=starter_key(s); t.image=default_image(t.starter_pattern); t.extension='CLIP'; slots=[t]
    base=len(mats)
    mats.extend(surfaces.build(t,'Foliage',(1,1,1),'Smooth',material,alpha=s.alpha_mode,foliage=True) for t in slots)
    if not points:
        yield 0,0
        return
    for i,point in enumerate(points):
        pos,normal=point[:2]
        spec=point[2] if len(point)>2 and isinstance(point[2],dict) else None
        r=random.Random(s.seed+i*101); cr=random.Random(s.color_seed+i*101); rr=random.Random(s.rotation_seed+i*101); tr=random.Random(s.texture_seed+i*101)
        sr=random.Random(s.shape_seed+i*101); ar=random.Random(s.size_seed+i*101); tint_rng=random.Random(s.color_seed+i*101+701)
        axes=[s.scale_axes[j]*ar.uniform(s.axis_min[j],s.axis_max[j]) for j in range(3)]
        bend=sr.uniform(s.bend_min,s.bend_max) if s.random_card_shape else s.bend
        valley=sr.uniform(s.valley_min,s.valley_max) if s.random_card_shape else s.valley
        ix=tr.choices(range(len(slots)),weights=[t.weight for t in slots])[0]; slot=slots[ix]
        size=r.uniform(s.size_min,s.size_max)*slot.size*.45; w=size*slot.aspect; h=size
        if spec: w=spec['width']*size/.45*slot.aspect; h=spec['height']*size/.45
        hue,sat,val=colorsys.rgb_to_hsv(*s.color); color=colorsys.hsv_to_rgb((hue+cr.uniform(s.hue_min,s.hue_max))%1,min(1,sat*cr.uniform(s.saturation_min,s.saturation_max)),min(1,val*cr.uniform(s.value_min,s.value_max)))
        color=tuple(c*tint_rng.uniform(s.tint_min[j],s.tint_max[j]) for j,c in enumerate(color))
        opacity=cr.uniform(s.opacity_min,s.opacity_max)
        yaw=rr.uniform(-s.yaw,s.yaw)
        if len(point)>2 and not spec:
            a=s.canopy_alignment; yaw=math.atan2((1-a)*math.sin(yaw)+a*math.sin(point[2]),(1-a)*math.cos(yaw)+a*math.cos(point[2]))
        rot=normal.normalized().to_track_quat('Z','Y').to_matrix().to_4x4() @ Matrix.Rotation(yaw+slot.rotation,4,'Z') @ Matrix.Rotation(rr.uniform(-s.pitch,s.pitch),4,'X') @ Matrix.Rotation(rr.uniform(-s.roll,s.roll),4,'Y')
        if spec:
            rot=spec['frame'].to_4x4() @ Matrix.Rotation(yaw+slot.rotation,4,'Z') @ Matrix.Rotation(rr.uniform(-s.pitch,s.pitch),4,'X') @ Matrix.Rotation(rr.uniform(-s.roll,s.roll),4,'Y')
        jitter=0 if spec else min(s.jitter,s.cluster_radius*.08) if len(point)>2 else s.jitter
        p=pos+Vector([r.uniform(-jitter,jitter) for _ in range(3)])
        subdivisions=max(s.subdivisions,spec.get('segments',1)) if spec else s.subdivisions
        if s.card=='Valley' and subdivisions==1 and not (spec and spec.get('force_quad')):
            coords=[(0,0),(1,0),(1,1),(0,1),(.5,.5)]; fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
        else:
            n=subdivisions; coords=[(x/n,y/n) for y in range(n+1) for x in range(n+1)]; fs=[(y*(n+1)+x,y*(n+1)+x+1,(y+1)*(n+1)+x+1,(y+1)*(n+1)+x) for y in range(n) for x in range(n)]
        vs=[]
        for u,v in coords:
            pivot=spec['pivot']+slot.pivot-.5 if spec else slot.pivot
            x=(u-.5)*w*(1-s.card_taper*v); z=(v-pivot)*h; depth=bend*z*z+s.curl*math.sin(v*math.pi)*h+s.twist*x*z
            if spec and 'bough_profile' in spec:
                arch,fold=spec['bough_profile']
                side=(2*u-1)**2
                depth+=math.sin(math.pi*v)*(arch*h-fold*w*side)
            if spec and spec.get('blade'):
                if spec.get('palm'):
                    # Stylized Palm Frond: 1 continuous blade per dahan (pelepah).
                    # Calibrated to stylized reference: slender petiole, widens smoothly, tapers to pointed tip.
                    w_profile=math.sin(math.pi*(v**.65))*(1.-spec.get('taper',.5)*v*.45)
                    saw=abs(((v*7.)%1.)-.5)*2.
                    edge_cut=.76+.24*saw
                    x*=max(.02,w_profile*edge_cut)
                    # Inverted-V roof fold along midrib (crease)
                    side_dist=abs(2.*u-1.)
                    depth+=((s.frond_droop*.35+.12)*w*(1.-side_dist**1.5))
                else:
                    # A broad lamina keeps most of its width through the middle.
                    # Only the short petiole and tip sections narrow sharply.
                    x*=max(.025,min(1.,v*5)*min(1.,(1-v)*6)*(1-spec['taper']*v*.35))
                    if s.blade_edge_tear and u!=.5:
                        side=0 if u<.5 else 1
                        row=round(v*subdivisions)
                        tear_rng=random.Random(s.blade_tear_seed+i*1009+row*37+side*7919)
                        if tear_rng.random()<s.blade_tear_chance:
                            x*=1-s.blade_edge_tear*tear_rng.uniform(.4,1.)*math.sin(math.pi*v)*abs(2*u-1)
            # Frond cards reverse winding to face outward; both styles use
            # positive valley values as a peak along the face normal.
            if s.card=='Valley': depth+=(1 if spec else -1)*valley*math.sin(math.pi*u)*math.sin(math.pi*v)*size
            local=Vector((x*axes[0],depth*axes[1],z*axes[2])); vertex=p+rot.to_3x3()@local
            if spec and 'spine' in spec:
                path=spec['spine']; f=v*(len(path)-1); j=min(len(path)-2,int(f)); spine=path[j].lerp(path[j+1],f-j)
                local_spine=spec['frame'].transposed()@spine*(size/.45)*axes[2]
                vertex=p+rot.to_3x3()@(local_spine+Vector((x*axes[0],depth*axes[1],-pivot*h*axes[2])))
            elif spec: vertex.z-=spec.get('leaf_droop',0)*h*v*v
            vs.append(vertex)
        u0,v0,u1,v1=slot.uv_region
        if spec and spec.get('root_uv_top'): v0,v1=v1,v0
        uv=[(u0+u*(u1-u0),v0+v*(v1-v0)) for u,v in coords]
        if spec: fs=[tuple(reversed(f)) for f in fs]
        branch_id=spec.get('branch_id',-1) if spec else point[3] if len(point)>3 else -1
        branch_t=spec.get('branch_t',0) if spec else point[4] if len(point)>4 else 0
        branch_level=spec.get('branch_level',-1) if spec else point[5] if len(point)>5 else -1
        builder.add(vs,fs,color,opacity,uv,base+ix,card=True,wind_weights=[v*v for u,v in coords],
                    branch_id=branch_id,branch_level=branch_level,branch_t=[branch_t]*len(vs))
        if spec and 'bough_density' in spec:
            builder.bough_density.append(spec['bough_density'])
        if (i+1)%batch_size==0 or i+1==len(points): yield i+1,len(points)

def cards(builder,s,points,mats):
    for _ in card_steps(builder,s,points,mats): pass

def tree(builder,s,ob,live_frond_anchors=None,live_bough=False):
    rng=random.Random(s.seed); h=s.height
    trunk_form=effective_trunk(s)
    # Ordinary trunks should read as a continuous stem, not as a twisted cable.
    # Reserve visible lateral wobble for the explicitly crooked tree forms.
    if trunk_form=='TWISTED_CONIFER':
        # The deliberate crooked-pine preset keeps a rolling leader.
        trunk=[Vector((s.curve*math.sin(t*2.8)*t,.075*math.sin(t*6),h*t))
               for t in [i/14 for i in range(15)]]
    else:
        # Normal trunks lean in one broad, smooth gesture instead of receiving
        # a repeated sine wave that reads as a twisted cable.
        trunk=[Vector((s.curve*(t*t+.18*math.sin(math.pi*t)*t),
                       .018*math.sin(math.pi*t)*t,h*t))
               for t in [i/14 for i in range(15)]]
    guides=[]
    if s.controller and s.controller.type=='CURVE':
        curves=tree_guides(s.controller,ob); trunk=curves[0]; guides=curves[1:]
    if s.branch_guides=='MANUAL' and not guides:
        raise ValueError('Curve Only requires a curve controller with a trunk spline and at least one branch spline')
    trunk_collar=.45 if trunk_form in {'PALM','PSEUDOSTEM'} else .35 if trunk_form in {'CONIFER','TWISTED_CONIFER','BAOBAB'} else 0
    builder.tube(trunk,s.radius,10,1-s.taper,collar=trunk_collar,branch_id=0,branch_level=0)
    graph=[]; pts=[]; lobes=[]; anchors=[]; primary_tips=[]; radius=s.cluster_radius
    structured=s.pattern in fronds.PATTERNS and not (s.controller and s.controller.type=='MESH')
    willow_sprays=(trunk_form=='WILLOW' and s.pattern=='Cloud' and s.branch_crown and
                  s.canopy_mode=='COVER' and not (s.controller and s.controller.type=='MESH'))
    spray_guides=[]

    def record(branch_id,parent,level,line):
        graph.append({'id':branch_id,'parent':parent,'level':level,
                      'points':[[round(c,6) for c in p] for p in line]})

    record(0,None,0,trunk)

    def trunk_at(t):
        position=max(0.,min(1.,t))*(len(trunk)-1)
        lower=min(len(trunk)-1,int(position))
        upper=min(len(trunk)-1,lower+1)
        return trunk[lower].lerp(trunk[upper],position-lower)

    def add_lobes(line,angle,reach,level,branch_id,bough_tier=None):
        if willow_sprays:
            spray_guides.append((line,angle,reach,level,branch_id))
            return
        if structured:
            if s.pattern=='Conifer':
                if level==1:
                    anchors.append((line[0],(line[-1]-line[0]).normalized(),
                                    reach/max(.01,s.length),branch_id,level,line,bough_tier))
                return
            anchor=line[1] if len(line)>2 else line[0]
            anchors.append((anchor,(line[-1]-anchor).normalized(),reach/max(.01,s.length)*(.85 if level==1 else .65),branch_id,level))
            return
        tip=line[-1]
        if level>1:
            factor=.64**(level-1)
            if trunk_form=='WILLOW':
                drop=max(.12,reach*.55)
                hanging=[tip,tip+Vector((math.cos(angle)*.07,math.sin(angle)*.07,-drop))]
                builder.tube(hanging,max(.002,s.radius*.035*factor),5,.02)
                lobes.append((hanging[-1],(radius*.48*factor,radius*.48*factor,max(.12,drop*.60)),branch_id,1.,level))
            elif trunk_form=='UMBRELLA':
                lobes.append((tip,(radius*.80*factor,radius*.80*factor,radius*.22),branch_id,1.,level))
            else:
                lobes.append((tip,(radius*.82*factor,radius*.82*factor,radius*.86*factor),branch_id,1.,level))
            return
        if trunk_form=='WILLOW':
            drop=reach*.72
            hanging=[tip,tip+Vector((math.cos(angle)*.10,math.sin(angle)*.10,-drop*.45)),tip+Vector((math.cos(angle)*.16,math.sin(angle)*.16,-drop))]
            builder.tube(hanging,s.radius*.065,5,.02)
            lobes.extend([(tip,(radius*.78,radius*.78,radius*.55),branch_id,1.,level),
                          (hanging[1],(radius*.48,radius*.48,drop*.37),branch_id,1.,level),
                          (hanging[-1],(radius*.40,radius*.40,drop*.30),branch_id,1.,level)])
        elif trunk_form=='UMBRELLA':
            lobes.extend([(tip+Vector((0,0,radius*.16)),(radius*1.38,radius*1.38,radius*.30),branch_id,1.,level),
                          (line[min(3,len(line)-1)],(radius*.80,radius*.80,radius*.25),branch_id,min(3,len(line)-1)/(len(line)-1),level)])
        else:
            lobes.extend([(tip+Vector((0,0,radius*.15)),(radius,radius,radius*1.2),branch_id,1.,level),
                          (line[2].lerp(tip,.30) if len(line)>2 else line[0].lerp(tip,.5),
                           (radius*.95,radius*.95,radius),branch_id,.58 if len(line)>2 else .5,level)])

    def descend(primary_base,primary_id,line,reach,wood_radius):
        frontier=[(primary_id,1,line,reach,wood_radius)]
        for level in range(2,s.levels+1):
            next_frontier=[]
            for parent_id,code,parent_line,parent_length,parent_radius in frontier:
                forks=2 if level==2 else 1
                for fork in range(forks):
                    child_rng=random.Random(s.seed*1000003+primary_base*9176+code*53+level*7+fork)
                    sign=1 if fork==0 else -1
                    index=min(len(parent_line)-2,max(0,int((.57+.20*fork)*(len(parent_line)-1))))
                    start=parent_line[index]
                    tangent=(parent_line[index+1]-parent_line[max(0,index-1)]).normalized()
                    side=Vector((-tangent.y,tangent.x,0))
                    if side.length<.1: side=Vector((1,0,0))
                    side.normalize()
                    lift=s.angle*.20-s.droop*.10+child_rng.uniform(-.12,.26)
                    direction=(tangent*.74+side*sign*child_rng.uniform(.38,.72)+Vector((0,0,lift))).normalized()
                    length=parent_length*(.52 if level==2 else .58)*child_rng.uniform(.85,1.15)
                    sweep=(.08*s.curve+child_rng.uniform(.04,.15))*length
                    child=[start+direction*(length*u)+side*sign*sweep*u*u+
                           Vector((0,0,-s.droop*.28*u*u))+
                           (tangent-direction)*(length*.8*u*(1-u)**2)
                           for u in (0,.20,.40,.60,.80,1)]
                    child_code=code*3+fork+1; branch_id=primary_base+child_code
                    remaining=1-index/(len(parent_line)-1)
                    child_radius=max(.001,parent_radius*.61*remaining**.76)
                    builder.tube(child,child_radius,max(4,7-level),.045,branch_id=branch_id,branch_level=level,collar=.32)
                    record(branch_id,parent_id,level,child)
                    angle=math.atan2(direction.y,direction.x)
                    add_lobes(child,angle,length,level,branch_id)
                    next_frontier.append((branch_id,child_code,child,length,child_radius))
            frontier=next_frontier

    def primary(line,base,angle,reach,trunk_factor,automatic=False,bough_tier=None):
        branch_id=base+1
        parent_radius=s.radius*(1-s.taper*trunk_factor)
        wood_radius=max(.001,min(parent_radius*.58,s.radius*.38,reach*.12))
        branch_extent=1.
        wood=line
        if automatic and structured and s.pattern=='Conifer' and trunk_form in {'CONIFER','TWISTED_CONIFER'}:
            # The needle bough carries the distal silhouette. Keep the visible
            # wooden support beneath it and retain the full guide for anchors.
            branch_extent=.58
            wood=[]
            for index in range(4):
                t=branch_extent*index/3
                station=t*(len(line)-1)
                segment=min(len(line)-2,int(station))
                point=line[segment].lerp(line[segment+1],station-segment)
                wood.append(point-Vector((0,0,reach*.32*t*t)))
        builder.tube(wood,wood_radius,6,.065,branch_id=branch_id,branch_level=1,
                     collar=.50,branch_extent=branch_extent)
        record(branch_id,0,1,line)
        primary_tips.append(line[-1])
        add_lobes(line,angle,reach,1,branch_id,bough_tier)
        if not structured and s.canopy_mode=='LEGACY':
            legacy_rng=random.Random(s.seed*1009+branch_id*9173)
            for _ in range(max(3,int(s.density/2))):
                point=line[-1]+Vector((legacy_rng.gauss(0,.4),legacy_rng.gauss(0,.4),legacy_rng.gauss(0,.45)))
                pts.append((point,Vector((0,0,1))))
        # Needle Spray cards represent the complete foliage bough on each
        # primary whorl branch. Bare secondary twigs would puncture that broad
        # silhouette, so this form stops at the designed primary structure.
        if not (s.pattern=='Conifer' and trunk_form in {'CONIFER','TWISTED_CONIFER'}):
            descend(base,branch_id,line,reach,wood_radius)

    if s.branch_guides!='MANUAL':
        conifer=trunk_form in {'CONIFER','TWISTED_CONIFER'}
        terminal_crown=trunk_form in {'PALM','PSEUDOSTEM'}
        crown_heading=random.Random(s.seed+7639).uniform(0,math.tau)
        tier_count=min(7,max(4,round(s.branches/4))) if conifer else 0
        tier_members={}
        if conifer:
            for branch_index in range(s.branches):
                tier=min(tier_count-1,int(((branch_index+.5)/s.branches)*tier_count))
                tier_members.setdefault(tier,[]).append(branch_index)
        for i in range(s.branches):
            u=(i+.5)/max(1,s.branches)
            jitter=rng.uniform(-.18,.18)/max(1,s.branches)
            if terminal_crown:
                # Palm and banana fronds emerge from one crown, not from a
                # generic set of branches spaced along the whole trunk. Their
                # bases spiral through the crown zone instead of sharing one
                # identical point at the trunk tip.
                t=.90+.09*min(1.,u+jitter)
                angle=crown_heading+i*2.399963229728653+rng.uniform(-.075,.075)
                age=1-u
                # Successive leaves open outward as they mature. Keep the
                # outer arches long and the newest leaves upright and short.
                if trunk_form=='PSEUDOSTEM':
                    reach_factor=(.53+.60*min(1.,age*1.46))*rng.uniform(.94,1.06)
                    rise=.29+2.27*u**2.15+rng.uniform(-.045,.045)
                else:
                    reach_factor=(.65+.56*math.sin(math.pi*(.08+.70*age))**.72)*rng.uniform(.95,1.05)
                    rise=.17+1.60*u**2.35+rng.uniform(-.04,.04)
            elif conifer:
                # Conifers grow in visible whorls. Each whorl is level around
                # the leader. Branches are distributed around each tier rather
                # than following one Fibonacci spiral up the trunk.
                tier=min(tier_count-1,int(((i+.5)/s.branches)*tier_count))
                tier_u=tier/max(1,tier_count-1)
                members=tier_members[tier]
                ordinal=members.index(i)
                tier_offset=.014*math.sin(tier*2.4+crown_heading)
                progress=(tier+.48)/tier_count
                t=min(.95,max(.26,.26+.70*(1-(1-progress)**1.24)+tier_offset+rng.uniform(-.015,.015)))
                stagger=.5 if tier%2 else 0
                angle=(ordinal+stagger)*math.tau/len(members)+rng.uniform(-.065,.065)
                reach_factor=(.35+.89*(1-tier_u)**1.12)*rng.uniform(.86,1.14)
                rise=max(-.32,min(.56,-.16+.46*tier_u**1.5+s.angle*.12+rng.uniform(-.04,.04)))
            elif trunk_form=='UMBRELLA':
                t=min(.94,max(.68,.70+.24*min(1.,u+jitter)))
                angle=i*2.399963229728653+rng.uniform(-.16,.16)
                reach_factor=rng.uniform(.88,1.12)
                rise=max(-.10,min(.28,s.angle*.22))
            elif trunk_form=='WILLOW':
                t=min(.97,max(.44,.45+.51*min(1.,u+jitter)))
                angle=i*2.399963229728653+rng.uniform(-.18,.18)
                reach_factor=(.43+.85*math.sin(math.pi*(.25+.71*u))**.8)*rng.uniform(.91,1.09)
                rise=max(.08,min(.84,s.angle*.72+.32*u))
            elif trunk_form=='VINE':
                # Fruiting cordons radiate from a short, low trunk and stay
                # nearly horizontal so leaves and grape clusters form a vine.
                t=min(.9,max(.5,.72+jitter))
                angle=i*2.399963229728653+rng.uniform(-.2,.2)
                reach_factor=rng.uniform(1.15,1.42)
                rise=max(-.16,min(.22,s.angle*.24+rng.uniform(-.06,.06)))
            else:
                # Broadleaf crowns occupy the upper trunk, with a small seeded
                # offset so primary limbs do not form a perfect ladder.
                crown_base=.30 if trunk_form=='BONSAI' else .40
                crown_span=.63 if trunk_form=='BONSAI' else .53
                t=min(.96,max(crown_base,crown_base+crown_span*min(1.,u+jitter)))
                spread=.42 if trunk_form=='BONSAI' else .20
                angle=i*2.399963229728653+rng.uniform(-spread,spread)
                sector=1+.17*math.cos(angle-crown_heading)
                crown_profile=.67+.50*math.sin(math.pi*(.18+.80*u))
                reach_factor=((1.40-.72*u)*rng.uniform(.68,1.28) if trunk_form=='BONSAI'
                              else crown_profile*sector*rng.uniform(.83,1.17))
                rise=max(-.12,min(1.,s.angle*.68+.18*(u-.5)+rng.uniform(-.16,.19)))

            start=trunk_at(t)
            if terminal_crown and not structured:
                # A broad palm-like scaffold beneath mesh-controlled foliage.
                start=trunk[-2]
            reach=max(.05,s.length*reach_factor)
            radial=Vector((math.cos(angle),math.sin(angle),0))
            tangent=Vector((-radial.y,radial.x,0))
            direction=Vector((radial.x,radial.y,rise)).normalized()
            tip=start+direction*reach
            limb_rng=random.Random(s.seed*1009+(i+1)*9176)
            bend=(max(-1.,min(1.,s.curve))*.16+limb_rng.uniform(-.16,.16))*reach
            basal_lift=limb_rng.uniform(.22,.56) if conifer else limb_rng.uniform(.43,.94)
            line=[]
            for k in range(6):
                q=k/5
                point=start.lerp(tip,q)+tangent*(bend*q*q)
                point.z-=max(-.8,min(.8,s.droop))*reach*q*q
                if not terminal_crown:
                    # A short upward departure curves back into the broader limb.
                    point.z+=basal_lift*reach*q*(1-q)**2
                line.append(point)
            if structured and terminal_crown:
                tilt=max(.08,min(2.5,rise))
                direction=Vector((radial.x,radial.y,tilt)).normalized()
                branch_id=(i+1)*128+1
                anchors.append((start,direction,reach_factor,branch_id,1))
                record(branch_id,0,1,[start,start+direction*reach])
                continue
            primary(line,(i+1)*128,angle,reach,t,automatic=True,bough_tier=tier if conifer else None)
            if s.preset=='Banyan' and i%3==0:
                # Start inside the limb while it still has enough cross
                # section to support a hanging root. The free tip is too thin.
                origin=line[3].lerp(line[4],.25)
                landing=Vector((origin.x*.96,origin.y*.96,.04))
                drop=origin.z-landing.z
                aerial=[origin,origin.lerp(landing,.13)+radial*drop*.018,
                        origin.lerp(landing,.55)+radial*drop*.024,landing]
                aerial_id=500000+i
                builder.tube(aerial,s.radius*.075,7,.62,branch_id=aerial_id,branch_level=2)
                record(aerial_id,(i+1)*128+1,2,aerial)

        if structured and conifer:
            # Close the bare tip above the final whorl with a short terminal
            # needle spray. A leader should taper into foliage, not end as a
            # naked spike.
            leader_length=max(.32,min(.86,s.height*.105))
            for leader_index in range(3):
                leader_angle=leader_index*math.tau/3+.37
                radial=Vector((math.cos(leader_angle),math.sin(leader_angle),0))
                spread=.05 if leader_index==0 else .39
                leader_direction=(radial*spread+Vector((0,0,1))).normalized()
                length=leader_length*(1 if leader_index==0 else 1.20)
                base=.84 if leader_index==0 else 1.55
                anchors.append((trunk[-1]-Vector((0,0,leader_length*base)),
                                leader_direction,length/max(.01,s.length),0,0))
    if s.branch_guides!='AUTO':
        for i,guide in enumerate(guides):
            root=min(trunk,key=lambda point:(point-guide[0]).length)
            line=([root]+guide) if (root-guide[0]).length>.001 else guide
            reach=sum((b-a).length for a,b in zip(line,line[1:]))
            if reach<.01: continue
            direction=line[-1]-line[0]
            primary(line,100000+(i+1)*128,math.atan2(direction.y,direction.x),reach,trunk.index(root)/max(1,len(trunk)-1))

    root_paths=roots.build(builder,s,ob,trunk[0],trunk_at=trunk_at,stilt=trunk_form=='STILT')
    for root_id,parent,line in root_paths: record(root_id,parent,0,line)
    s['lp_root_count']=len(root_paths)
    s['lp_branch_count']=sum(item['level']>0 for item in graph)
    s['lp_branch_max_level']=max(item['level'] for item in graph)
    ob['lp_branch_graph']=json.dumps({'schema':1,'branches':graph},separators=(',',':'))
    if willow_sprays: return canopy.willow_sprays(s,spray_guides)
    if structured:
        if live_bough:
            return fronds.boughs(s,anchors,live=True) if trunk_form!='DEAD' else []
        if live_frond_anchors is not None:
            live_frond_anchors.extend(anchors)
            per=1 if s.pattern=='Banana' else s.count*(s.frond_whorl if s.pattern=='Whorl' else 2 if s.pattern in live_surface.PAIRED_PATH_PATTERNS else 1)
            s['lp_frond_requested']=len(anchors)*per
            s['lp_frond_cards']=min(s.limit,len(anchors)*per)
            return []
        return fronds.arrange(builder,s,anchors) if trunk_form!='DEAD' else []
    if s.pattern!='None' and s.canopy_mode=='COVER' and not (s.controller and s.controller.type=='MESH') and trunk_form not in {'PALM','PSEUDOSTEM','DEAD'}:
        if len(primary_tips)>1 and s.canopy_join>0 and trunk_form in {'BRANCHED','BAOBAB'}:
            # A shared interior lobe bridges separated branch pads. The outer
            # tip lobes retain the crown silhouette; Join controls its reach.
            low=Vector(tuple(min(p[i] for p in primary_tips) for i in range(3)))
            high=Vector(tuple(max(p[i] for p in primary_tips) for i in range(3)))
            center=(low+high)*.5
            extent=(high-low)*.5
            join=s.canopy_join
            inner=(max(radius*.55,extent.x*join+radius*.2),
                   max(radius*.55,extent.y*join+radius*.2),
                   max(radius*.75,extent.z*join+radius*.35))
            lobes.append((center,inner,0,center.z/max(.01,h),0,'FILL'))
        if trunk_form=='UMBRELLA': lobes.append((trunk[-1],(radius*1.8,radius*1.8,radius*.32),0,1.,0))
        elif trunk_form=='WILLOW': lobes.append((trunk[-1],(radius*1.2,radius*1.2,radius*.75),0,1.,0))
        else:
            for j in range(max(1,int(len(trunk)*.43)),len(trunk),2):
                lobes.append((trunk[j],(radius*.92,radius*.92,radius*1.15),0,j/(len(trunk)-1),0))
        if s.kind=='Tree' and s.pattern=='Cloud' and s.branch_crown:
            pts=canopy.tree_cluster_cards(s,lobes,s.cluster_planes)
        else:
            pts=canopy.sample(s,lobes,include_branch=True)
    if live_frond_anchors is not None and s.controller and s.controller.type=='MESH': return []
    if s.controller and s.controller.type=='MESH': pts=distribution(s,ob)
    return [] if trunk_form=='DEAD' or s.pattern=='None' or s.density<=0 else pts[:s.limit]

def mushroom(builder,s,ob=None):
    mushrooms.build(builder,s,ob or bpy.context.object)

def props(builder,s):
    if s.prop in wood_props.WOOD_KINDS:
        wood_props.build(builder,s); return
    rocks.build(builder,s)

def wind_modifier(ob):
    s=ob.landscapy; mod=ob.modifiers.get('Landscapy Wind') or ob.modifiers.new('Landscapy Wind','NODES')
    if mod.node_group:
        old=mod.node_group; mod.node_group=None
        if old.users==0: bpy.data.node_groups.remove(old)
    g=bpy.data.node_groups.new('LP Wind '+s.uid,'GeometryNodeTree'); mod.node_group=g
    g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry'); g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=g.nodes; L=g.links.new; inp=n.new('NodeGroupInput'); out=n.new('NodeGroupOutput'); pos=n.new('GeometryNodeSetPosition'); time=n.new('GeometryNodeInputSceneTime')
    parent= s.target if ob.get('lp_live_ornaments') and s.target else None
    wind_settings=parent.landscapy if parent else s
    source=wind_settings.wind_controller if wind_settings.wind_controller and wind_settings.wind_use_controller else parent or ob
    response_owner=parent or ob
    def value(prop,owner=None):
        v=n.new('ShaderNodeValue'); d=v.outputs[0].driver_add('default_value').driver; d.type='AVERAGE'; var=d.variables.new(); var.name='v'; var.targets[0].id=owner or source; var.targets[0].data_path='landscapy.'+prop; return v.outputs[0]
    def calc(op,a,b=None):
        x=n.new('ShaderNodeMath'); x.operation=op
        for index,v in enumerate([a,b]):
            if v is None: continue
            if isinstance(v,(int,float)): x.inputs[index].default_value=v
            else: L(v,x.inputs[index])
        return x.outputs[0]
    phase=calc('ADD',calc('ADD',calc('MULTIPLY',time.outputs['Seconds'],value('wind_speed')),value('wind_phase')),value('wind_phase_offset',response_owner))
    attr=n.new('GeometryNodeInputNamedAttribute'); attr.data_type='FLOAT'; attr.inputs['Name'].default_value='lp_wind'
    leaf=n.new('GeometryNodeInputNamedAttribute'); leaf.data_type='FLOAT'; leaf.inputs['Name'].default_value='lp_leaf_wind'
    branch_cos=n.new('GeometryNodeInputNamedAttribute'); branch_cos.data_type='FLOAT'; branch_cos.inputs['Name'].default_value='lp_branch_wind_cos'
    branch_sin=n.new('GeometryNodeInputNamedAttribute'); branch_sin.data_type='FLOAT'; branch_sin.inputs['Name'].default_value='lp_branch_wind_sin'
    cluster_phase=n.new('GeometryNodeInputNamedAttribute'); cluster_phase.data_type='FLOAT'; cluster_phase.inputs['Name'].default_value='lp_cluster_phase'
    card_phase=n.new('GeometryNodeInputNamedAttribute'); card_phase.data_type='FLOAT'; card_phase.inputs['Name'].default_value='lp_card_phase'
    amp=calc('MULTIPLY',calc('MULTIPLY',attr.outputs['Attribute'],value('wind')),value('wind_response',response_owner))
    gust=calc('MAXIMUM',0,calc('SINE',calc('MULTIPLY',phase,.27)))
    amp=calc('MULTIPLY',amp,calc('ADD',1,calc('MULTIPLY',gust,value('wind_gust'))))
    position=n.new('GeometryNodeInputPosition'); components=n.new('ShaderNodeSeparateXYZ')
    if parent:
        anchor=n.new('GeometryNodeInputNamedAttribute'); anchor.data_type='FLOAT_VECTOR'
        anchor.inputs['Name'].default_value='lp_anchor_position'
        L(anchor.outputs['Attribute'],components.inputs[0])
    else: L(position.outputs['Position'],components.inputs[0])
    spatial=calc('ADD',calc('MULTIPLY',components.outputs['X'],2.1),calc('MULTIPLY',components.outputs['Y'],1.3))
    disturbance=calc('MULTIPLY',calc('SINE',calc('ADD',spatial,calc('MULTIPLY',phase,3.7))),calc('MULTIPLY',amp,value('wind_turbulence')))
    # Existing saved meshes have only lp_cluster_phase; preserve their motion.
    card_phase_fallback=n.new('GeometryNodeSwitch'); card_phase_fallback.input_type='FLOAT'
    L(card_phase.outputs['Exists'],card_phase_fallback.inputs['Switch'])
    L(cluster_phase.outputs['Attribute'],card_phase_fallback.inputs['False'])
    L(card_phase.outputs['Attribute'],card_phase_fallback.inputs['True'])
    flutter_phase=calc('ADD',calc('ADD',calc('MULTIPLY',phase,7),calc('MULTIPLY',spatial,2)),card_phase_fallback.outputs[0])
    flutter=calc('MULTIPLY',calc('SINE',flutter_phase),calc('MULTIPLY',calc('MULTIPLY',leaf.outputs['Attribute'],value('wind_flutter')),calc('MULTIPLY',value('wind'),value('wind_response',response_owner))))
    cluster_wave=calc('SINE',calc('ADD',calc('MULTIPLY',phase,1.7),cluster_phase.outputs['Attribute']))
    cluster=calc('MULTIPLY',cluster_wave,calc('MULTIPLY',calc('MULTIPLY',leaf.outputs['Attribute'],value('wind_cluster')),calc('MULTIPLY',value('wind'),value('wind_response',response_owner))))
    v=n.new('ShaderNodeCombineXYZ')
    sin_phase=calc('SINE',phase); cos_phase=calc('COSINE',phase)
    trunk_amp=calc('MULTIPLY',amp,value('wind_trunk'))
    sway=calc('MULTIPLY',sin_phase,trunk_amp); cross=calc('MULTIPLY',cos_phase,calc('MULTIPLY',trunk_amp,.35))
    branch_wave=calc('ADD',calc('MULTIPLY',sin_phase,branch_cos.outputs['Attribute']),calc('MULTIPLY',cos_phase,branch_sin.outputs['Attribute']))
    branch_amp=calc('MULTIPLY',branch_wave,calc('MULTIPLY',calc('MULTIPLY',value('wind_branch'),value('wind')),value('wind_response',response_owner)))
    branch_amp=calc('MULTIPLY',branch_amp,calc('ADD',1,calc('MULTIPLY',gust,value('wind_gust'))))
    sway=calc('ADD',sway,branch_amp)
    direction=value('wind_direction'); cos=calc('COSINE',direction); sin=calc('SINE',direction)
    side=calc('ADD',cross,calc('ADD',cluster,flutter))
    L(calc('ADD',calc('SUBTRACT',calc('MULTIPLY',sway,cos),calc('MULTIPLY',side,sin)),calc('MULTIPLY',disturbance,.35)),v.inputs['X'])
    L(calc('ADD',calc('ADD',calc('MULTIPLY',sway,sin),calc('MULTIPLY',side,cos)),calc('MULTIPLY',disturbance,.5)),v.inputs['Y'])
    L(calc('MULTIPLY',flutter,.25),v.inputs['Z'])
    L(inp.outputs[0],pos.inputs['Geometry']); L(v.outputs[0],pos.inputs['Offset']); L(pos.outputs[0],out.inputs[0])

def generate_steps(ob,batch_size=128):
    """Stage a source mesh in card batches; closing before commit keeps it intact."""
    # Scripts can move a controller or generator immediately before Generate.
    # Refresh matrix_world before distribution converts world to local space.
    bpy.context.view_layer.update()
    s=ob.landscapy
    keys=('lp_coverage_requested','lp_coverage_emitted','lp_coverage_grid_filled',
          'lp_frond_cards','lp_frond_requested','lp_ivy_stops','lp_ivy_cards',
          'lp_branch_count','lp_branch_max_level','lp_semantic_rebound',
          'lp_root_count','lp_root_ground_misses')
    old_keys={key:(list(s[key]) if hasattr(s[key],'to_list') else s[key]) if key in s else None for key in keys}
    old_graph=ob.get('lp_branch_graph')
    old_uid=s.uid; old_status=s.status
    old_textures=len(s.textures); old_surfaces=len(s.surfaces)
    old_materials=set(bpy.data.materials)
    upgraded_textures=[]
    committed=False
    try:
        if s.kind!='Tree' and 'lp_branch_graph' in ob: del ob['lp_branch_graph']
        was_bound=bool(ob.get('lp_binding_signature'))
        s['lp_coverage_requested']=0; s['lp_coverage_emitted']=0; s['lp_coverage_grid_filled']=[0]*9; s['lp_frond_cards']=0; s['lp_frond_requested']=0; s['lp_ivy_stops']=0; s['lp_ivy_cards']=0
        if any(other!=ob and other.landscapy.uid==s.uid for other in bpy.data.objects): s.uid=uuid.uuid4().hex
        entries=surfaces.ensure(s); role=surfaces.roles(s)[0]
        if s.kind in {'Tree','Foliage'} and s.pattern=='Conifer':
            for index,slot in enumerate(s.textures):
                if legacy_conifer_starter(slot) and starter_without_overrides(slot):
                    upgraded_textures.append((index,slot.image))
                    slot.image=default_image('Conifer')
        if s.kind in {'Tree','Foliage','Ivy'} and not any((slot.image or slot.material_override) and slot.weight>0 for slot in s.textures):
            slot=s.textures.add(); slot.starter_pattern=starter_key(s)
            slot.image=default_image(slot.starter_pattern); slot.extension='CLIP'
            if s.kind=='Ivy': slot.pivot=0
        b=Builder(s.mesh_detail); b.cluster_wind_scale=max(.2,s.cluster_radius*2)
        mats=[surfaces.build(entries[role],role,s.glow_color if s.kind=='Mushroom' and s.glow=='All' else s.bark,s.material_style,material,glow=s.glow_strength if s.kind=='Mushroom' and s.glow=='All' else 0)]
        tree_anchors=[]
        live_bough=live_tree_fronds.branch_bough(s)
        live_tree=live_tree_fronds.enabled(s) and not live_bough
        if s.kind=='Tree':
            tree_cards=tree(b,s,ob,tree_anchors if live_tree else None,live_bough)
            if s.fuse_wood:
                wood_junctions.fuse(b)
            b.bough_density=[] if live_bough else None
            yield from card_steps(b,s,tree_cards,mats,batch_size)
        elif s.kind in {'Foliage','Ivy'}:
            if s.live_surface and s.instance_cards:
                live_surface.supported(s)
                live_slots=[t for t in s.textures if (t.image or t.material_override) and t.weight>0]
                mats.extend(surfaces.build(t,'Foliage',(1,1,1),'Smooth',material,alpha=s.alpha_mode,foliage=True)
                            for t in live_slots)
                yield 1,1
            elif s.kind=='Ivy':
                yield from card_steps(b,s,ivy.generate(b,s,ob),mats,batch_size)
            else:
                points=distribution(s,ob)
                if s.pattern in fronds.PATTERNS: points=fronds.arrange(b,s,points)
                yield from card_steps(b,s,points,mats,batch_size)
        elif s.kind=='Mushroom':
            mats.extend([surfaces.build(entries['Cap'],'Cap',s.glow_color if s.glow in ['Cap','All'] else s.color,s.material_style,material,glow=s.glow_strength if s.glow in ['Cap','All'] else 0),surfaces.build(entries['Gills'],'Gills',s.glow_color if s.glow in ['Under','All'] else s.bark,'Smooth',material,glow=s.glow_strength if s.glow in ['Under','All'] else 0)])
            mushrooms.build(b,s,ob)
            yield 1,1
        else:
            if s.prop in wood_props.WOOD_KINDS:
                if 'Cut Wood' in entries:
                    cut_color=tuple(min(1,channel*1.4+.15) for channel in s.bark)
                    def cut_fallback(role,color,style,glow=0): return wood_props.cut_material(color)
                    mats.append(surfaces.build(entries['Cut Wood'],'Cut Wood',cut_color,'Bands',cut_fallback))
                if 'Inner Wood' in entries:
                    inner_color=tuple(channel*.48 for channel in s.bark)
                    mats.append(surfaces.build(entries['Inner Wood'],'Inner Wood',inner_color,'Grain',material))
                wood_props.build(b,s,ob)
            else:
                mats[0]=surfaces.build(entries['Rock'],'Rock',s.rock_color,s.material_style,material)
                mats.append(surfaces.build(entries['Cracks'],'Cracks',s.rock_crack_color,'Smooth',material))
                mats.append(surfaces.build(entries['Moss'],'Moss',s.rock_moss_color,'Moss',material))
                rocks.build(b,s)
            yield 1,1
        if live_tree:
            live_slots=[t for t in s.textures if (t.image or t.material_override) and t.weight>0]
            live_tree_fronds.commit(ob,b,s,live_slots,mats,tree_anchors)
        elif s.kind in {'Foliage','Ivy'} and s.live_surface and s.instance_cards:
            live_surface.commit(ob,s,live_slots,mats)
        elif s.instance_cards:
            instance_cards.commit(ob,b,mats,s)
            if live_bough:
                live_tree_fronds.remove_guides(ob)
                ob['lp_live_mode']='TreeBough'
        else:
            b.finish(ob,mats)
            instance_cards.clear(ob)
        if not (live_tree or live_bough or s.kind in {'Foliage','Ivy'} and s.live_surface and s.instance_cards) and 'lp_live_mode' in ob:
            del ob['lp_live_mode']
        committed=True
        wind_modifier(ob)
        s.status=('Live boughs • Density and Limit update live. Regenerate after editing shape.'
                  if live_bough else
                  'Live Tree mesh canopy • controller, density, rachises, and cards evaluated in Geometry Nodes'
                  if live_tree and s.controller and s.controller.type=='MESH' else
                  'Live Tree Banana • branch guides, rachises, and blades evaluated in Geometry Nodes'
                  if live_tree and s.pattern=='Banana' else
                  'Live Tree fronds • branch guides and leaf cards evaluated in Geometry Nodes'
                  if live_tree else
                  'Live Banana blades • mesh controller and density evaluated in Geometry Nodes'
                  if s.kind=='Foliage' and s.pattern=='Banana' and s.controller and s.controller.type=='MESH' and s.live_surface and s.instance_cards else
                  'Live Banana rachis and blade • edit Curve to reshape each blade'
                  if s.kind=='Foliage' and s.pattern=='Banana' and s.live_surface and s.instance_cards else
                  'Live mesh fronds • controller, density, rachis, and leaf controls evaluated in Geometry Nodes'
                  if s.kind=='Foliage' and s.pattern in live_surface.ARRANGED_PATH_PATTERNS and s.controller and s.controller.type=='MESH' and s.live_surface and s.instance_cards else
                  'Live Path rachis and arranged leaf cards • controller and density evaluated in Geometry Nodes'
                  if s.kind=='Foliage' and s.pattern in live_surface.ARRANGED_PATH_PATTERNS and s.live_surface and s.instance_cards else
                  'Live Ivy Surface from seed • mesh, growth direction, and density evaluated in Geometry Nodes'
                  if s.kind=='Ivy' and s.controller and s.controller.type=='MESH' and s.live_surface and s.instance_cards else
                  'Live Ivy Path snapped to mesh target • Curve, target, and density evaluated in Geometry Nodes'
                  if s.kind=='Ivy' and s.target and s.live_surface and s.instance_cards else
                  'Live Ivy Path vine and cards • controller and density evaluated in Geometry Nodes'
                  if s.kind=='Ivy' and s.live_surface and s.instance_cards else
                  'Live '+ob.get('lp_live_mode','Surface')+' cards • density and controller evaluated in Geometry Nodes'
                  if s.kind in {'Foliage','Ivy'} and s.live_surface and s.instance_cards else
                  f'{sum(b.card_flags):,} instanced cards / {len(ob.data.polygons):,} solid faces'
                  if s.instance_cards else f'{len(b.v):,} vertices / {len(b.f):,} faces')
        if s.kind=='Prop' and s.prop in wood_props.CUT_KINDS:
            for face in ob.data.polygons:
                if face.material_index==1: face.use_smooth=False
        if s.kind=='Prop' and s.prop in rocks.KINDS:
            for face in ob.data.polygons: face.use_smooth=False
        if s.get('lp_coverage_requested',0)>s.limit:
            s.status+=' • Card limit reached; raise Limit for more coverage'
        if s.get('lp_frond_requested',0)>s.limit: s.status+=' • Frond card limit reached'
        if s.kind=='Ivy' and s.get('lp_ivy_stops',0): s.status+=f" • {s['lp_ivy_stops']} growth stops (edge, gap, or step budget)"
        if was_bound:
            if s.target: attachments.bind(ob,s.target)
            else: attachments.unbind(ob)
        if s.kind=='Tree': s['lp_semantic_rebound']=attachments.rebind_dependents(ob)
        ornaments.rebuild(ob,'ORNAMENT')
        ornaments.rebuild(ob,'FRUIT')
        preview.sync(ob,force=True)
    finally:
        if not committed:
            for index,image in upgraded_textures:
                s.textures[index].image=image
            while len(s.textures)>old_textures: s.textures.remove(len(s.textures)-1)
            while len(s.surfaces)>old_surfaces: s.surfaces.remove(len(s.surfaces)-1)
            for key,value in old_keys.items():
                if value is None:
                    if key in s: del s[key]
                else: s[key]=value
            if old_graph is None:
                if 'lp_branch_graph' in ob: del ob['lp_branch_graph']
            else: ob['lp_branch_graph']=old_graph
            s.uid=old_uid; s.status=old_status
            for mat in set(bpy.data.materials)-old_materials:
                if mat.users==0: bpy.data.materials.remove(mat)

def generate(ob):
    for _ in generate_steps(ob): pass

class LPCreate(bpy.types.Operator):
    bl_idname='landscapy.create'; bl_label='Create Landscapy'; bl_options={'REGISTER','UNDO'}
    kind: EnumProperty(items=enum(['Tree','Foliage','Ivy','Mushroom','Prop']))
    def _new(self,context):
        ctrl=context.active_object; ob=mesh_object('Landscapy '+self.kind,[],[],context.collection); ob.location=context.scene.cursor.location
        s=ob.landscapy; s.uid=uuid.uuid4().hex; s.kind=self.kind
        if ctrl and self.kind=='Mushroom' and ctrl.type=='MESH': s.target=ctrl
        elif ctrl and not ctrl.landscapy.uid and ctrl.type in ['MESH','CURVE']: s.controller=ctrl
        if self.kind=='Mushroom': s.length=.65; s.radius=.08
        if self.kind=='Ivy':
            s.length=3; s.yaw=.15; s.pitch=.12; s.roll=.12; s.bend=.06; s.wind=0; s.jitter=0
        if self.kind=='Tree': apply_trunk_surface(s)
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); context.view_layer.objects.active=ob
        return ob
    def _cleanup(self,context):
        ob=self._created
        if ob and ob.name in bpy.data.objects:
            mesh=ob.data; bpy.data.objects.remove(ob,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
        bpy.ops.object.select_all(action='DESELECT')
        for selected in self._old_selected:
            if selected.name in bpy.data.objects and not selected.hide_get(): selected.select_set(True)
        if self._old_active and self._old_active.name in bpy.data.objects:
            context.view_layer.objects.active=self._old_active
    def execute(self,context):
        self._old_selected=list(context.selected_objects); self._old_active=context.active_object; self._created=None
        try:
            self._created=self._new(context)
            generate(self._created)
        except Exception as exc:
            self._cleanup(context)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self,context,event):
        if bpy.app.background or not context.window: return self.execute(context)
        self._old_selected=list(context.selected_objects); self._old_active=context.active_object; self._created=None
        try:
            bpy.ops.ed.undo_push(message='Before Landscapy Create')
            self._created=self._new(context)
            self._steps=generate_steps(self._created)
            wm=context.window_manager; wm.progress_begin(0,100)
            self._timer=wm.event_timer_add(.04,window=context.window)
            wm.modal_handler_add(self)
        except Exception as exc:
            self._cleanup(context)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def _stop(self,context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
    def modal(self,context,event):
        if event.type=='ESC':
            self._steps.close(); self._stop(context); self._cleanup(context)
            self.report({'INFO'},'Create cancelled; no Landscapy object added')
            return {'CANCELLED'}
        if event.type!='TIMER': return {'RUNNING_MODAL'}
        try: done,total=next(self._steps)
        except StopIteration:
            self._stop(context)
            self.report({'INFO'},'Landscapy asset created')
            return {'FINISHED'}
        except Exception as exc:
            self._steps.close(); self._stop(context); self._cleanup(context)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        context.window_manager.progress_update(100*done/max(1,total))
        self._created.landscapy.status=f'Creating cards {done:,}/{total:,} • Esc to cancel' if total>1 else 'Creating solid mesh • Esc to cancel'
        return {'RUNNING_MODAL'}

class LPGenerate(bpy.types.Operator):
    bl_idname='landscapy.generate'; bl_label='Regenerate'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            if not context.object or not context.object.landscapy.uid: raise RuntimeError('Select a Landscapy generator')
            generate(context.object)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self,context,event):
        if bpy.app.background or not context.window: return self.execute(context)
        source=context.object
        if not source or not source.landscapy.uid:
            self.report({'ERROR'},'Select a Landscapy generator'); return {'CANCELLED'}
        bpy.ops.ed.undo_push(message='Before Landscapy Regenerate')
        self._source=source
        self._steps=generate_steps(source)
        wm=context.window_manager; wm.progress_begin(0,100)
        self._timer=wm.event_timer_add(.04,window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def _stop(self,context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()
    def modal(self,context,event):
        if event.type=='ESC':
            self._steps.close(); self._stop(context)
            self.report({'INFO'},'Regenerate cancelled; previous mesh preserved')
            return {'CANCELLED'}
        if event.type!='TIMER': return {'RUNNING_MODAL'}
        try: done,total=next(self._steps)
        except StopIteration:
            self._stop(context)
            self.report({'INFO'},'Regenerate complete')
            return {'FINISHED'}
        except Exception as exc:
            self._steps.close(); self._stop(context)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        context.window_manager.progress_update(100*done/max(1,total))
        self._source.landscapy.status=f'Generating cards {done:,}/{total:,} • Esc to cancel' if total>1 else 'Generating solid mesh • Esc to cancel'
        return {'RUNNING_MODAL'}

class LPRootGuides(bpy.types.Operator):
    bl_idname='landscapy.root_guides_from_tree'; bl_label='Create Editable Root Curves'; bl_options={'REGISTER','UNDO'}
    bl_description='Create one editable spline per current primary root and switch to Curves Only'
    @classmethod
    def poll(cls,context):
        return bool(context.object and context.object.landscapy.kind=='Tree')
    def execute(self,context):
        source=context.object
        try:
            graph=json.loads(source.get('lp_branch_graph','{}')).get('branches',[])
            root_lines=[row['points'] for row in graph if row['id']<0 and row['parent']==0]
        except (TypeError,ValueError,KeyError): root_lines=[]
        if not root_lines:
            self.report({'ERROR'},'Regenerate a tree with primary roots before creating guide curves')
            return {'CANCELLED'}
        data=bpy.data.curves.new(source.name+' Root Curves','CURVE'); data.dimensions='3D'
        for line in root_lines:
            spline=data.splines.new('POLY'); spline.points.add(len(line)-1)
            for point,co in zip(spline.points,line): point.co=(*co,1)
        guide=bpy.data.objects.new(data.name,data)
        (source.users_collection[0] if source.users_collection else context.collection).objects.link(guide)
        guide.matrix_world=source.matrix_world.copy(); guide.hide_render=True; guide.show_in_front=True
        s=source.landscapy; previous_guide=s.root_guides; previous_mode=s.root_guide_mode
        s.root_guides=guide; s.root_guide_mode='CURVE'
        try: generate(source)
        except Exception as exc:
            s.root_guides=previous_guide; s.root_guide_mode=previous_mode
            bpy.data.objects.remove(guide,do_unlink=True)
            if data.users==0: bpy.data.curves.remove(data)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},f'Created {len(root_lines)} editable root splines')
        return {'FINISHED'}

class LPPreset(bpy.types.Operator):
    bl_idname='landscapy.preset'; bl_label='Load Plant Type'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        s=context.object.landscapy; s.height,s.radius,s.branches,s.length,s.curve=TREE_PRESETS[s.preset]
        s.levels,s.angle,s.droop=TREE_FORM_DEFAULTS[s.preset]
        s.trunk_type='AUTO'
        new_pattern=recommended_leaf(s.preset,PLANT_TRUNK.get(s.preset,'BRANCHED'))
        s.fruit_type=PLANT_FRUIT_TYPE.get(s.preset,'CUSTOM')
        replace=len(s.textures)==1 and untouched_starter(s.textures[0])
        s.pattern=new_pattern
        s.branch_crown=new_pattern=='Cloud'
        fronds.preset(s,s.pattern)
        if s.preset=='Willow':
            s.cluster_radius=.70; s.cluster_planes=3
            s.yaw=.22; s.pitch=.13; s.roll=.16
            s.size_min=.93; s.size_max=1.07
        if s.preset=='Acacia':
            s.length=4.6; s.cluster_radius=1.15
        if s.preset in {'Mountain Bonsai','Bonsai Tree'}: s.canopy_join=.4; s.cluster_radius=.58
        if s.preset=='Mangrove': s.roots=8
        if s.preset in {'Apple','Mango'}:
            # Increase leaflet coverage across the branched crown so these
            # presets read as broadleaf trees, not as sparse fronded forms.
            s.count=18 if s.preset=='Apple' else 16
            s.frond_width=1.42 if s.preset=='Apple' else 1.62
            s.frond_leaf_width=.32 if s.preset=='Apple' else .36
            s.frond_angle=.22; s.frond_droop=.12
        if s.preset=='Pine':
            s.canopy_join=1.0
        s.taper={'Palm':.58,'Coconut':.52,'Banana':.59}.get(s.preset,.85)
        if s.preset=='Palm':
            s.frond_stem_radius=.032
        if s.preset=='Coconut':
            s.frond_stem_radius=.032
            s.frond_width=2.05; s.frond_droop=.53
        if s.preset=='Banana':
            s.frond_stem_radius=.045; s.yaw=.28
            s.fruit_yaw=.20; s.fruit_pitch=.08; s.fruit_roll=.08
        if replace:
            key=starter_key(s); s.textures[0].image=default_image(key); s.textures[0].starter_pattern=key
        roots.preset(s); apply_trunk_surface(s); generate(context.object); return {'FINISHED'}

class LPFrondPreset(bpy.types.Operator):
    bl_idname='landscapy.frond_preset'; bl_label='Load Leaf Type Shape'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        s=context.object.landscapy; fronds.preset(s,s.pattern); generate(context.object); return {'FINISHED'}

class LPStarterTexture(bpy.types.Operator):
    bl_idname='landscapy.starter_texture'; bl_label='Use Starter Leaf Texture'; bl_options={'REGISTER','UNDO'}
    bl_description='Use the built-in texture for the selected pattern. Keep other slots but set their selection weights to zero'
    def execute(self,context):
        s=context.object.landscapy; key=starter_key(s); image=default_image(key); chosen=None
        for slot in s.textures:
            slot.weight=0
            if slot.image==image and not slot.material_override: chosen=slot
        if chosen is None: chosen=s.textures.add(); chosen.image=image; chosen.extension='CLIP'
        chosen.starter_pattern=key
        chosen.weight=1; generate(context.object); return {'FINISHED'}

class LPImport(bpy.types.Operator):
    bl_idname='landscapy.import_textures'; bl_label='Import Texture Images'; bl_options={'REGISTER','UNDO'}
    directory: StringProperty(subtype='DIR_PATH'); files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    filter_glob: StringProperty(default='*.png;*.jpg;*.jpeg;*.tga;*.webp',options={'HIDDEN'})
    def execute(self,context):
        for f in self.files:
            t=context.object.landscapy.textures.add(); t.image=bpy.data.images.load(str(Path(self.directory)/f.name),check_existing=True); t.image.pack(); t.extension='CLIP'
        return {'FINISHED'}
    def invoke(self,context,event): context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

class LPPropPreset(bpy.types.Operator):
    bl_idname='landscapy.prop_preset'; bl_label='Load Prop Shape Defaults'; bl_options={'REGISTER','UNDO'}
    bl_description='Set recommended dimensions for this prop; keep its surface textures and materials'
    def execute(self,context):
        ob=context.object
        if not ob or ob.landscapy.kind!='Prop': return {'CANCELLED'}
        s=ob.landscapy
        s.radius,s.length,s.crown,s.bend=PROP_DEFAULTS[s.prop]
        if s.prop in ROCK_DEFAULTS:
            s.rock_axes,s.rock_erosion,s.rock_cracks,s.rock_moss,s.rock_facets=ROCK_DEFAULTS[s.prop]
        try: generate(ob)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
class LPRemoveTexture(bpy.types.Operator):
    bl_idname='landscapy.remove_texture'; bl_label='Remove Texture Slot'; bl_options={'REGISTER','UNDO'}
    index: IntProperty()
    def execute(self,context): context.object.landscapy.textures.remove(self.index); return {'FINISHED'}

class LPBind(bpy.types.Operator):
    bl_idname='landscapy.bind'; bl_label='Bind / Rebind to Target'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try: attachments.bind(context.object,context.object.landscapy.target)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}

class LPUnbind(bpy.types.Operator):
    bl_idname='landscapy.unbind'; bl_label='Detach Binding'; bl_options={'REGISTER','UNDO'}
    def execute(self,context): attachments.unbind(context.object); return {'FINISHED'}

class LPSnap(bpy.types.Operator):
    bl_idname='landscapy.snap'; bl_label='Snap to Target'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        ob=context.object; target=ob.landscapy.target
        s=ob.landscapy
        try:
            point,normal=snapping.snap(ob,target,s.snap_mode,s.snap_direction,s.snap_distance,s.snap_offset)
            if s.kind=='Mushroom': context.view_layer.update(); generate(ob)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}

class LPWind(bpy.types.Operator):
    bl_idname='landscapy.wind_controller'; bl_label='Create Shared Wind'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        target=context.object; ob=bpy.data.objects.new('Landscapy Wind',None); context.collection.objects.link(ob); ob.empty_display_type='ARROWS'; ob['lp_wind_controller']=True
        for prop in ['wind','wind_speed','wind_phase','wind_direction','wind_gust','wind_turbulence','wind_trunk','wind_branch','wind_cluster','wind_flutter']:
            setattr(ob.landscapy,prop,getattr(target.landscapy,prop))
        target.landscapy.wind_controller=ob; wind_modifier(target); preview.sync(target,force=True); return {'FINISHED'}

class LPSavePreset(bpy.types.Operator):
    bl_idname='landscapy.save_preset'; bl_label='Save User Preset'
    filepath: StringProperty(subtype='FILE_PATH')
    def execute(self,context):
        try: surfaces.save_preset(context.object.landscapy,self.filepath)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self,context,event): self.filepath='Landscapy_Preset.json'; context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

class LPLoadPreset(bpy.types.Operator):
    bl_idname='landscapy.load_preset'; bl_label='Load User Preset'; bl_options={'REGISTER','UNDO'}
    filepath: StringProperty(subtype='FILE_PATH')
    def execute(self,context):
        try:
            surfaces.load_preset(context.object.landscapy,self.filepath)
            generate(context.object)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self,context,event): context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

class LPSpawnLibraryTree(bpy.types.Operator):
    bl_idname='landscapy.spawn_library_tree'; bl_label='Spawn Interactive Curve Tree'; bl_options={'REGISTER','UNDO'}
    preset: EnumProperty(name='Tree Preset',
        items=[('OAK','Stylized Oak / Broadleaf','Faceted solid leaf clumps'),
               ('ANIME_DOME','Anime Dome Tree','Volumetric fluffy cloud dome puffs'),
               ('PALM','Coconut Palm','1 continuous blade per frond with V-fold'),
               ('BANANA','Banana Tree','Broad lamina blades with banana bunch'),
               ('BONSAI','Mountain Bonsai','Crooked S-twist trunk with foliage'),
               ('DEAD_TREE','Dead Bare Tree','Bare wood branches with no foliage')],
        default='OAK')
    gesture: EnumProperty(name='Trunk Gesture',
        items=[('GENTLE','Gentle Lean','Natural broadleaf lean'),
               ('PALM','Arching Palm','Sweeping curve'),
               ('BANANA','Upright Stalk','Pseudostem gesture'),
               ('BONSAI','Crooked S-Twist','Dramatic mountain bonsai'),
               ('STRAIGHT','Straight','Upright leader')],
        default='GENTLE')
    def execute(self,context):
        from . import trees
        g=self.gesture
        if self.preset=='PALM': g='PALM'
        elif self.preset=='BANANA': g='BANANA'
        elif self.preset=='BONSAI': g='BONSAI'
        ob=trees.create_curve_trunk(f"{self.preset.title()}_Tree",gesture=g)
        trees.setup_tree_modifiers(ob,preset=self.preset)
        return {'FINISHED'}

class LPSpawnLibraryProp(bpy.types.Operator):
    bl_idname='landscapy.spawn_library_prop'; bl_label='Spawn Library Prop'; bl_options={'REGISTER','UNDO'}
    prop_type: EnumProperty(name='Prop Type',
        items=[('LP_Rock','Stylized Rock','Faceted low-poly boulder'),
               ('LP_HollowTrunk','Hollow Trunk','Decayed hollow stump with exposed wood rim'),
               ('LP_Mushroom','Stylized Mushroom','Cap + gills + stem with glow support'),
               ('LP_ShelfMushroom','Tree Shelf Mushroom','Bracket oyster mushroom for tree bark'),
               ('LP_MushroomCluster','Glowing Mushroom Cluster','Three original cap-and-stem forms with cap emission'),
               ('LP_OysterCluster','Oyster Mushroom Cluster','Layered bracket mushrooms for tree surfaces'),
               ('LP_Rock_Rounded','Rounded Rock','Original faceted boulder variation'),
               ('LP_Rock_Shard','Shard Rock','Original angular rock variation'),
               ('LP_BananaBunch','Banana Bunch','Yellow finger tiers with maroon bud'),
               ('LP_CoconutCluster','Coconut Cluster','Coconut sphere cluster'),
               ('LP_AppleCluster','Apple Cluster','Small axillary fruit cluster'),
               ('LP_GrapeCluster','Grape Cluster','Tapered hanging fruit cluster'),
               ('LP_MangoPanicle','Mango Panicle','Elongated hanging fruit cluster')],
        default='LP_Rock')
    def execute(self,context):
        from . import library
        ob=library.append_object(self.prop_type)
        if ob:
            context.view_layer.objects.active=ob; ob.select_set(True)
        return {'FINISHED'}

class LPPanel(bpy.types.Panel):
    bl_label='Landscapy • Stylized Nature'; bl_idname='LP_PT_main'; bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category='Landscapy'
    def draw(self,context):
        l=self.layout
        header,body=l.panel('LP_Library',default_closed=False); header.label(text='Stylized Library Assets',icon='ASSET_MANAGER')
        if body:
            row=body.row(align=True)
            row.operator('landscapy.spawn_library_tree',text='Spawn Library Tree')
            row.operator('landscapy.spawn_library_prop',text='Spawn Library Prop')
        row=l.row()
        for kind in ['Tree','Foliage','Ivy']: row.operator('landscapy.create',text=kind).kind=kind
        row=l.row()
        for kind in ['Mushroom','Prop']: row.operator('landscapy.create',text=kind).kind=kind
        ob=context.object
        if not ob or not ob.landscapy.uid:
            l.label(text='Select a Landscapy generator')
            if ob and ob.get('lp_wind_controller'):
                l.label(text='Shared Wind Controller')
                for prop in ['wind','wind_direction','wind_speed','wind_phase','wind_gust','wind_turbulence','wind_trunk','wind_branch','wind_cluster','wind_flutter']:
                    l.prop(ob.landscapy,prop)
            if ob and ob.type=='MESH':
                l.prop(ob.landscapy,'target'); l.prop(ob.landscapy,'attachment_local_wind'); l.operator('landscapy.bind'); l.operator('landscapy.unbind'); l.label(text=ob.landscapy.binding_message)
            return
        s=ob.landscapy; l.operator('landscapy.generate',icon='FILE_REFRESH'); l.label(text=s.status)
        row=l.row(); row.operator('landscapy.save_preset'); row.operator('landscapy.load_preset')
        if s.kind=='Tree':
            l.prop(s,'preset',text='Plant Type'); l.operator('landscapy.preset')
            l.prop(s,'trunk_type')
        if s.kind=='Tree': l.prop(s,'pattern',text='Leaf Type')
        fronds.draw(l,s)
        ivy.draw(l,s)
        if s.kind=='Tree' or (s.kind=='Foliage' and s.pattern=='Cloud' and not s.controller):
            header,body=l.panel('LP_Canopy',default_closed=False); header.label(text='Canopy Coverage')
            if body:
                for key in ['canopy_mode','canopy_coverage','canopy_join','cluster_radius']: body.prop(s,key)
                if s.kind=='Tree' and s.pattern=='Cloud' and not (s.controller and s.controller.type=='MESH'):
                    body.prop(s,'branch_crown')
                    if s.branch_crown: body.prop(s,'cluster_planes')
                if not (s.kind=='Tree' and s.pattern=='Cloud' and s.branch_crown):
                    for key in ['canopy_shell','canopy_alignment','canopy_candidates']: body.prop(s,key)
                if s.controller and s.controller.type=='MESH': body.label(text='Mesh controller shapes live fronds when enabled.',icon='INFO')
        if s.kind=='Tree':
            header,body=l.panel('LP_Roots',default_closed=True); header.label(text='Root System')
            if body:
                body.operator('landscapy.root_guides_from_tree')
                for key in ['roots','root_guides','root_guide_mode','root_guide_ground_follow','root_style','root_length','root_length_random','root_width','root_departure','root_tip','root_taper','root_tip_bury','root_spread','root_wander','root_lift','root_sink','root_flatten','root_buttress_height','root_forks','root_fork_start','root_fork_angle','root_fork_reach','root_fork_width','root_segments','root_seed','root_ground','root_ground_follow','root_ground_offset']:
                    body.prop(s,key)
                if s.get('lp_root_ground_misses',0):
                    body.label(text=f"{s['lp_root_ground_misses']} root samples missed Ground Mesh",icon='ERROR')
        card_controls=['card','subdivisions','valley','bend','curl','twist','card_taper','random_card_shape']
        if s.random_card_shape: card_controls+=['shape_seed','bend_min','bend_max','valley_min','valley_max']
        shape=({'Tree':['height','mesh_detail','fuse_wood','radius','taper','branches','levels','branch_guides','length','angle','curve','droop']+card_controls,
                'Mushroom':['mushroom','mesh_detail','length','radius','mushroom_stem_taper','bend','mushroom_bend_random','crown','thickness','mushroom_rim','mushroom_cap_facets','mushroom_cap_rings','mushroom_gills','cluster','mushroom_cluster_radius','auto_bend','mushroom_bend_threshold','glow','glow_strength','glow_color'],
                'Prop':(['prop','mesh_detail','crown','rock_axes','rock_facets','rock_erosion','rock_cracks','rock_crack_width','rock_crack_depth','rock_moss']
                        if s.prop in rocks.KINDS else ['prop','mesh_detail','radius','length','crown','bend']),
                'Ivy':card_controls}.get(s.kind,['pattern','count','length','mesh_detail']+card_controls))
        distribution_controls=['controller','mode','density','limit','seed'] if s.kind=='Ivy' else ['controller','mode','density','limit','spacing','mask','seed']
        if s.kind=='Foliage':
            distribution_controls+=['gn_surface','live_surface']
            if s.live_surface and s.controller and s.controller.type=='MESH' and s.mode in {'Auto','Volume'}:
                distribution_controls+=['live_volume_grid_cells']
        if s.kind=='Ivy': distribution_controls+=['live_surface']
        if s.kind=='Tree' and s.pattern in live_surface.ARRANGED_PATH_PATTERNS | {'Banana'}:
            distribution_controls+=['live_surface']
            if s.live_surface and s.controller and s.controller.type=='MESH' and s.mode in {'Auto','Volume'}:
                distribution_controls+=['live_volume_grid_cells']
        if s.kind in {'Tree','Foliage','Ivy'}: distribution_controls+=['instance_cards']
        if s.kind in {'Tree','Foliage','Ivy'}:
            distribution_controls+=['preview_enabled']
            if s.preview_enabled: distribution_controls+=['preview_ratio']
        variation=['color','tint_min','tint_max','bark','material_style','color_seed','texture_seed','rotation_seed','size_min','size_max','scale_axes','size_seed','axis_min','axis_max','yaw','pitch','roll','jitter','hue_min','hue_max','saturation_min','saturation_max','value_min','value_max','opacity_min','opacity_max','alpha_mode']
        if s.kind in {'Tree','Foliage','Ivy'}: variation+=['stylized_normals','normal_bend_factor','normal_up_bias']
        if s.kind=='Prop' and s.prop in rocks.KINDS: variation+=['rock_color','rock_crack_color','rock_moss_color']
        groups=[('Shape',shape),('Distribution',distribution_controls),('Variation',variation),('Attachments',['target','snap_mode','snap_distance','snap_offset']),('Wind',['wind_controller','wind_use_controller','wind','wind_direction','wind_speed','wind_phase','wind_gust','wind_turbulence','wind_trunk','wind_branch','wind_cluster','wind_flutter','wind_response','wind_phase_offset']),('Build',['mid_ratio','low_ratio','mid_texture_scale','low_texture_scale','mid_triangle_limit','low_triangle_limit','flat_mode','resolution','with_normals','keep_wind','build_collection','bake_directory','game_export_dir'])]
        for title,props_ in groups:
            header,body=l.panel('LP_'+title,default_closed=title not in ['Shape'])
            header.label(text=title)
            if body:
                for p in props_: body.prop(s,p)
                if title=='Shape' and s.kind=='Prop': body.operator('landscapy.prop_preset')
                if title=='Distribution' and s.preview_enabled:
                    body.label(text=('Proxy cards; bound ornaments use full source' if s.ornaments_enabled else 'GN point preview; render full') if s.instance_cards else 'Viewport proxy; render uses full source',icon='INFO')
                if title=='Distribution' and s.instance_cards:
                    body.label(text='Quad, Valley/Peak, subdivided, Banana',icon='INFO')
                if title=='Distribution' and s.kind in {'Foliage','Ivy'} and s.live_surface and s.controller and s.controller.type=='CURVE':
                    body.label(text='Curve centerline: no bevel or extrude',icon='INFO')
                if title=='Attachments' and s.snap_mode=='CUSTOM': body.prop(s,'snap_direction')
                if title=='Attachments':
                    body.prop(s,'attachment_local_wind'); body.label(text=s.binding_message); body.operator('landscapy.snap'); body.operator('landscapy.bind'); body.operator('landscapy.unbind')
                if title=='Wind': body.operator('landscapy.wind_controller')
                if title=='Build':
                    body.operator('landscapy.build')
                    body.operator('landscapy.build',text='Build Collection').batch=True
                    body.operator('landscapy.export_game')
                    body.operator('landscapy.export_game',text='Export Game Collection').batch=True
        header,body=l.panel('LP_Textures',default_closed=True); header.label(text='Textures')
        ornaments.draw(l,s)
        if body:
            body.label(text='Solid surfaces / material regions')
            for i,entry in enumerate(s.surfaces):
                if entry.role not in surfaces.roles(s): continue
                head,content=body.panel('LP_surface_'+entry.role,default_closed=True); head.label(text=entry.role)
                if content:
                    surfaces.draw_library(content,entry,i)
                    content.prop(entry,'customized')
                    if entry.customized: surfaces.draw(content,entry,'surface',i)
                    else: content.label(text='Using generator colors and style.')
            body.label(text='Foliage image / material slots'); body.operator('landscapy.import_textures')
            for i,t in enumerate(s.textures):
                head,box=body.panel('LP_texture_'+str(i),default_closed=True); head.label(text=f'Slot {i+1}: '+(t.image.name if t.image else 'Custom material'))
                if box:
                    box.prop(t,'weight'); box.prop(t,'aspect'); box.prop(t,'size'); box.prop(t,'pivot'); box.prop(t,'rotation'); box.prop(t,'uv_region'); surfaces.draw(box,t,'foliage',i); box.operator('landscapy.remove_texture').index=i

from . import variants, game_export
CLASSES=[surfaces.LPSurface,ornaments.LPOrnamentSlot,LPTexture,LPSettings,surfaces.LPLoadMap,surfaces.LPUseSurfaceLook,LPCreate,LPGenerate,LPRootGuides,LPPreset,LPPropPreset,LPFrondPreset,LPStarterTexture,LPImport,LPRemoveTexture,LPBind,LPUnbind,LPSnap,LPWind,LPSavePreset,LPLoadPreset,LPSpawnLibraryTree,LPSpawnLibraryProp,ornaments.LPAddOrnament,ornaments.LPRemoveOrnament,ornaments.LPGenerateOrnaments,ornaments.LPStarterOrnament,ornaments.LPPickBranch,variants.LPBuild,game_export.LPExportGame,LPPanel]
def register():
    for c in CLASSES: bpy.utils.register_class(c)
    bpy.types.Object.landscapy=PointerProperty(type=LPSettings)
    attachments.register()
    impostors.register()
def unregister():
    impostors.unregister()
    attachments.unregister()
    del bpy.types.Object.landscapy
    for c in reversed(CLASSES): bpy.utils.unregister_class(c)
