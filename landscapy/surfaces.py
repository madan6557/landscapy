"""Customizable materials shared by foliage slots and solid surface roles."""
import bpy
import hashlib
import json
from pathlib import Path
from bpy.props import PointerProperty, FloatProperty, FloatVectorProperty, EnumProperty, BoolProperty, StringProperty

IMAGE_FIELDS = ('image', 'normal', 'roughness_image', 'opacity_image', 'height_image', 'emission_image')
LIBRARY_LOOKS = {
    'BARK_GROOVES': ('Bark Grooves', 'Bark_Grooves.png'),
    'BARK_FLAKES': ('Bark Flakes', 'Bark_Flakes.png'),
    'BARK_WAVES': ('Bark Waves', 'Bark_Waves.png'),
    'WOOD_RINGS': ('Cut Wood Rings', 'Wood_Rings.png'),
    'STONE_STRATA': ('Stone Strata', 'Stone_Strata.png'),
    'STONE_FACETS': ('Stone Facets', 'Stone_Facets.png'),
    'STONE_PEBBLES': ('Stone Pebbles', 'Stone_Pebbles.png'),
    'MUSHROOM_SPOTS': ('Mushroom Spots', 'Mushroom_Spots.png'),
    'MUSHROOM_RIBS': ('Mushroom Ribs', 'Mushroom_Ribs.png'),
    'MUSHROOM_MOTTLE': ('Mushroom Mottle', 'Mushroom_Mottle.png'),
    'MOSS_PATCHES': ('Moss Patches', 'Moss_Patches.png'),
}
ROLE_LOOK = {'Bark':'BARK_GROOVES','Wood':'BARK_FLAKES','Cut Wood':'WOOD_RINGS',
             'Inner Wood':'WOOD_RINGS','Rock':'STONE_STRATA','Cracks':'STONE_FACETS',
             'Moss':'MOSS_PATCHES','Stem':'BARK_WAVES','Cap':'MUSHROOM_SPOTS',
             'Gills':'MUSHROOM_RIBS'}

def properties():
    return {
        'image': PointerProperty(type=bpy.types.Image, name='Base Color Image'),
        'normal': PointerProperty(type=bpy.types.Image, name='Normal Map (UV)'),
        'roughness_image': PointerProperty(type=bpy.types.Image, name='Roughness Map'),
        'opacity_image': PointerProperty(type=bpy.types.Image, name='Opacity Map'),
        'height_image': PointerProperty(type=bpy.types.Image, name='Height / Bump Map'),
        'emission_image': PointerProperty(type=bpy.types.Image, name='Emission Map'),
        'material_override': PointerProperty(type=bpy.types.Material, name='Custom Material', description='Use this material as-is; regeneration never rewrites its nodes'),
        'tint': FloatVectorProperty(size=3, subtype='COLOR', default=(1,1,1), min=0, max=1),
        'hue': FloatProperty(default=.5, min=0, max=1),
        'saturation': FloatProperty(default=1, min=0, max=2),
        'value': FloatProperty(default=1, min=0, max=4),
        'roughness': FloatProperty(default=.85, min=0, max=1),
        'normal_strength': FloatProperty(default=1, min=0, max=5),
        'bump_strength': FloatProperty(default=.2, min=0, max=1),
        'bump_distance': FloatProperty(default=.05, min=0, max=2),
        'opacity': FloatProperty(default=1, min=0, max=1),
        'use_alpha': BoolProperty(default=True, name='Use Image Alpha'),
        'emission_color': FloatVectorProperty(size=3, subtype='COLOR', default=(1,1,1), min=0, max=1),
        'emission_strength': FloatProperty(default=0, min=0, max=100),
        'projection': EnumProperty(items=[('UV','UV','Uses UVMap'),('BOX','Box / Triplanar','Generated coordinates; normal maps still use UVMap')], default='UV'),
        'mapping_scale': FloatVectorProperty(size=3, default=(1,1,1), min=.001),
        'mapping_offset': FloatVectorProperty(size=3, default=(0,0,0)),
        'mapping_rotation': FloatProperty(default=0, subtype='ANGLE'),
        'extension': EnumProperty(items=[(x,x.title(),'') for x in ['REPEAT','EXTEND','CLIP']], default='REPEAT'),
        'procedural_scale': FloatProperty(default=8, min=.01, max=1000),
        'detail': FloatProperty(default=2, min=0, max=15),
        'contrast': FloatProperty(default=.6, min=0, max=1),
    }

class LPSurface(bpy.types.PropertyGroup):
    role: StringProperty()
    customized: BoolProperty(default=False, name='Customize Surface', description='Off preserves legacy generator color/style; on uses settings below')
    plant_starter_image: StringProperty(options={'HIDDEN'},description='Tracks only the preset image Landscapy assigned to this surface')
    __annotations__ = {'role': StringProperty(), 'customized': BoolProperty(default=False, name='Customize Surface'),
                       'plant_starter_image': StringProperty(options={'HIDDEN'}),
                       'library_look': EnumProperty(name='Library Look',items=[(key,label,'Original stylized image; apply with Use Look') for key,(label,_) in LIBRARY_LOOKS.items()]),
                       **properties()}

def roles(settings):
    if settings.kind == 'Tree': return ['Bark']
    if settings.kind == 'Mushroom': return ['Stem', 'Cap', 'Gills']
    if settings.kind == 'Prop':
        if settings.prop in ['Pebble','Boulder','Flat Rock','Shard','Stack']: return ['Rock','Cracks','Moss']
        if settings.prop == 'Hollow Log': return ['Wood','Cut Wood','Inner Wood']
        if settings.prop in ['Stump','Fallen Trunk','Broken Branch']: return ['Wood','Cut Wood']
        return ['Wood']
    return ['Stem']

def ensure(settings):
    result = {}
    for role in roles(settings):
        entry = next((x for x in settings.surfaces if x.role == role), None)
        if entry is None:
            entry = settings.surfaces.add(); entry.role = role
            entry.use_alpha = False
            entry.library_look = ROLE_LOOK.get(role,'BARK_GROOVES')
        result[role] = entry
    return result

def values(entry):
    data = {}
    for prop in entry.bl_rna.properties:
        key = prop.identifier
        if key == 'rna_type' or prop.type in ['POINTER','COLLECTION'] or prop.is_readonly: continue
        value = getattr(entry,key)
        data[key] = list(value) if getattr(prop,'is_array',False) else value
    return data

def data_image(image):
    """Do not change colorspace of an image also used as albedo by another asset."""
    if image.colorspace_settings.name == 'Non-Color': return image
    key = f'{image.name_full}|{image.filepath}'
    for existing in bpy.data.images:
        if existing.get('lp_data_source') == key: return existing
    copy = image.copy(); copy.name = image.name + ' • LP Data'
    copy.colorspace_settings.name = 'Non-Color'; copy['lp_data_source'] = key
    return copy

def build(entry, role, color, style, fallback, alpha='Soft', glow=0, foliage=False):
    if entry.material_override: return entry.material_override
    if not foliage and not entry.customized: return fallback(role,color,style,glow=glow)
    payload = [values(entry), {k:getattr(entry,k).name_full if getattr(entry,k) else None for k in IMAGE_FIELDS}, role, list(color), style, alpha, glow, foliage]
    key = 'LP Surface ' + hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]
    existing = bpy.data.materials.get(key)
    if existing: return existing
    mat = bpy.data.materials.new(key); mat.use_nodes=True; mat['lp_role']=role
    nt=mat.node_tree; n=nt.nodes; L=nt.links.new; bsdf=n.get('Principled BSDF')
    def new(kind,name):
        x=n.new(kind); x.name=name; x.label=name; return x
    coord=new('ShaderNodeTexCoord','Coordinates')
    mapping=new('ShaderNodeMapping','Texture Mapping'); mapping.inputs['Scale'].default_value=entry.mapping_scale
    mapping.inputs['Location'].default_value=entry.mapping_offset; mapping.inputs['Rotation'].default_value[2]=entry.mapping_rotation
    L(coord.outputs['Generated' if entry.projection=='BOX' else 'UV'],mapping.inputs['Vector'])
    normal_mapping=new('ShaderNodeMapping','Normal UV Mapping')
    normal_mapping.inputs['Scale'].default_value=entry.mapping_scale; normal_mapping.inputs['Location'].default_value=entry.mapping_offset; normal_mapping.inputs['Rotation'].default_value[2]=entry.mapping_rotation
    L(coord.outputs['UV'],normal_mapping.inputs['Vector'])
    def texture(field, data=False):
        im=getattr(entry,field)
        if not im: return None
        x=new('ShaderNodeTexImage',field); x.image=data_image(im) if data else im; x.extension=entry.extension
        if entry.projection=='BOX' and field!='normal': x.projection='BOX'; x.projection_blend=.25
        L(normal_mapping.outputs[0] if field=='normal' else mapping.outputs[0],x.inputs['Vector'])
        return x
    def multiply(a,b,name):
        x=new('ShaderNodeMixRGB',name); x.blend_type='MULTIPLY'; x.inputs[0].default_value=1
        for value,socket in [(a,x.inputs[1]),(b,x.inputs[2])]:
            if isinstance(value,tuple): socket.default_value=value
            else: L(value,socket)
        return x.outputs[0]
    base=texture('image'); alpha_output=None
    rgb=new('ShaderNodeRGB','Base Color'); rgb.outputs[0].default_value=(*color,1)
    starter_bark=bool(base and not foliage and entry.image and getattr(entry,'plant_starter_image','')==entry.image.name)
    if base and (foliage or (style!='Smooth' and not starter_bark) or (entry.customized and not starter_bark)):
        appearance=base.outputs['Color']
        if not foliage: appearance=multiply(rgb.outputs[0],appearance,'Albedo Tint')
        if entry.use_alpha: alpha_output=base.outputs['Alpha']
    else:
        appearance=rgb.outputs[0]
        if style!='Smooth':
            noise=new('ShaderNodeTexNoise','Stylized Pattern'); noise.inputs['Scale'].default_value=entry.procedural_scale; noise.inputs['Detail'].default_value=entry.detail
            L(mapping.outputs[0],noise.inputs['Vector']); ramp=new('ShaderNodeValToRGB','Pattern Contrast')
            ramp.color_ramp.elements[0].color=(1-entry.contrast,)*3+(1,); ramp.color_ramp.elements[1].color=(1,1,1,1)
            L(noise.outputs['Fac'],ramp.inputs[0]); appearance=multiply(appearance,ramp.outputs[0],'Pattern Tint')
    appearance=multiply(appearance,(*entry.tint,1),'User Tint')
    hsv=new('ShaderNodeHueSaturation','Hue Saturation Value'); hsv.inputs['Hue'].default_value=entry.hue; hsv.inputs['Saturation'].default_value=entry.saturation; hsv.inputs['Value'].default_value=entry.value
    L(appearance,hsv.inputs['Color']); appearance=hsv.outputs[0]
    if foliage:
        attr=new('ShaderNodeAttribute','Per-card Color'); attr.attribute_name='lp_color'
        appearance=multiply(appearance,attr.outputs['Color'],'Card Variation')
    L(appearance,bsdf.inputs['Base Color'])
    rough=texture('roughness_image',True)
    if rough:
        mul=new('ShaderNodeMath','Roughness Strength'); mul.operation='MULTIPLY'; mul.inputs[1].default_value=entry.roughness; L(rough.outputs['Color'],mul.inputs[0]); L(mul.outputs[0],bsdf.inputs['Roughness'])
    else: bsdf.inputs['Roughness'].default_value=entry.roughness
    normal=texture('normal',True); bump=texture('height_image',True); normal_out=None
    if normal:
        nm=new('ShaderNodeNormalMap','UV Tangent Normal'); nm.uv_map='UVMap'; nm.inputs['Strength'].default_value=entry.normal_strength; L(normal.outputs['Color'],nm.inputs['Color']); normal_out=nm.outputs[0]
    if bump:
        bn=new('ShaderNodeBump','Height Bump'); bn.inputs['Strength'].default_value=entry.bump_strength; bn.inputs['Distance'].default_value=entry.bump_distance
        L(bump.outputs['Color'],bn.inputs['Height'])
        if normal_out: L(normal_out,bn.inputs['Normal'])
        normal_out=bn.outputs[0]
    if normal_out: L(normal_out,bsdf.inputs['Normal'])
    opacity=texture('opacity_image',True)
    def scalar(a,b,label):
        x=new('ShaderNodeMath',label); x.operation='MULTIPLY'
        for i,value in enumerate([a,b]):
            if isinstance(value,(float,int)): x.inputs[i].default_value=value
            else: L(value,x.inputs[i])
        return x.outputs[0]
    alpha_output=scalar(alpha_output if alpha_output else 1.,entry.opacity,'Opacity')
    if opacity: alpha_output=scalar(alpha_output,opacity.outputs['Color'],'Opacity Map')
    if foliage:
        attr=new('ShaderNodeAttribute','Per-card Opacity'); attr.attribute_name='lp_opacity'; alpha_output=scalar(alpha_output,attr.outputs['Fac'],'Card Alpha')
    if alpha=='Cutout':
        cut=new('ShaderNodeMath','Alpha Cutout'); cut.operation='GREATER_THAN'; cut.inputs[1].default_value=.45; L(alpha_output,cut.inputs[0]); alpha_output=cut.outputs[0]
    L(alpha_output,bsdf.inputs['Alpha'])
    emission=texture('emission_image')
    if emission: L(multiply(emission.outputs['Color'],(*entry.emission_color,1),'Emission Tint'),bsdf.inputs['Emission Color'])
    else: bsdf.inputs['Emission Color'].default_value=(*entry.emission_color,1)
    bsdf.inputs['Emission Strength'].default_value=entry.emission_strength
    for i,x in enumerate(n): x.location=((i%5)*220,-(i//5)*210)
    return mat

def draw(layout,entry,kind,index):
    layout.prop(entry,'material_override')
    if entry.material_override:
        layout.label(text='Custom nodes retained as-is on regenerate.'); return
    for field in IMAGE_FIELDS:
        row=layout.row(); row.prop(entry,field)
        op=row.operator('landscapy.load_map',text='',icon='FILE_FOLDER'); op.kind=kind; op.index=index; op.field=field
    for key in ['tint','hue','saturation','value','roughness','normal_strength','bump_strength','bump_distance','opacity','use_alpha','projection','mapping_scale','mapping_offset','mapping_rotation','extension','emission_color','emission_strength']:
        layout.prop(entry,key)
    if not entry.image:
        for key in ['procedural_scale','detail','contrast']: layout.prop(entry,key)
    if entry.projection=='BOX' and entry.normal: layout.label(text='Normal map uses UV; height map follows Box.',icon='INFO')

def draw_library(layout,entry,index):
    row=layout.row()
    row.prop(entry,'library_look',text='Stylized Look')
    row.operator('landscapy.use_surface_look',text='',icon='CHECKMARK').index=index


class LPUseSurfaceLook(bpy.types.Operator):
    bl_idname='landscapy.use_surface_look'; bl_label='Use Stylized Surface Look'; bl_options={'REGISTER','UNDO'}
    index: bpy.props.IntProperty()
    def execute(self,context):
        if not context.object or self.index<0 or self.index>=len(context.object.landscapy.surfaces):
            return {'CANCELLED'}
        entry=context.object.landscapy.surfaces[self.index]
        look=LIBRARY_LOOKS.get(entry.library_look)
        if not look: return {'CANCELLED'}
        path=Path(__file__).parent/'textures'/look[1]
        if not path.is_file():
            self.report({'ERROR'},'Missing Landscapy texture: '+str(path))
            return {'CANCELLED'}
        image=bpy.data.images.load(str(path),check_existing=True)
        image.pack()
        entry.image=image; entry.material_override=None; entry.use_alpha=False; entry.customized=True
        self.report({'INFO'},look[0]+' selected; Regenerate to update the mesh material')
        return {'FINISHED'}

class LPLoadMap(bpy.types.Operator):
    bl_idname='landscapy.load_map'; bl_label='Load Custom Texture Map'; bl_options={'REGISTER','UNDO'}
    filepath: StringProperty(subtype='FILE_PATH')
    kind: StringProperty(default='surface'); index: bpy.props.IntProperty(); field: StringProperty(default='image')
    filter_glob: StringProperty(default='*.png;*.jpg;*.jpeg;*.tga;*.webp;*.exr;*.tif;*.tiff',options={'HIDDEN'})
    def execute(self,context):
        if self.field not in IMAGE_FIELDS: return {'CANCELLED'}
        entries=context.object.landscapy.surfaces if self.kind=='surface' else context.object.landscapy.textures
        if self.index<0 or self.index>=len(entries): return {'CANCELLED'}
        try:
            image=bpy.data.images.load(self.filepath,check_existing=True); image.pack(); setattr(entries[self.index],self.field,image)
            if self.kind=='surface': entries[self.index].customized=True
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}
    def invoke(self,context,event): context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

def save_preset(settings,path):
    path=Path(path); resources=set()
    visited=set()
    def pack_tree(tree):
        if tree in visited: return
        visited.add(tree)
        for node in tree.nodes:
            if node.type=='TEX_IMAGE' and node.image: node.image.pack(); resources.add(node.image)
            if node.type=='GROUP' and node.node_tree: pack_tree(node.node_tree)
    def serialize(entry):
        result=values(entry)
        for field in IMAGE_FIELDS:
            im=getattr(entry,field)
            result[field]=im.name if im else None
            if im: im.pack(); resources.add(im)
        mat=entry.material_override; result['material_override']=mat.name if mat else None
        if mat:
            resources.add(mat)
            if mat.use_nodes: pack_tree(mat.node_tree)
        return result
    def attachment_records(slots):
        records=[]
        for slot in slots:
            record=values(slot); record['object']=slot.object.name if slot.object else None
            if slot.object:
                resources.add(slot.object)
                for mat in slot.object.data.materials:
                    if mat and mat.use_nodes: pack_tree(mat.node_tree)
            records.append(record)
        return records
    data={'schema':4,'settings':values(settings),'textures':[serialize(t) for t in settings.textures],
          'surfaces':[serialize(t) for t in settings.surfaces],
          'ornaments':attachment_records(settings.ornament_slots),
          'fruits':attachment_records(settings.fruit_slots)}
    for key in ['uid','status','binding_valid','binding_message','ornament_status','fruit_status']: data['settings'].pop(key,None)
    resource_path=path.with_name(path.stem+'_resources.blend'); data['resources']=resource_path.name
    bpy.data.libraries.write(str(resource_path),resources,fake_user=True,compress=True)
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')

def load_preset(settings,path):
    path=Path(path); data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') not in [1,2,3,4]: raise ValueError('Unsupported preset schema')
    loaded_images={}; loaded_materials={}; loaded_objects={}
    if data['schema']>=2:
        resources=(path.parent/data['resources']).resolve()
        if not resources.is_file(): raise ValueError('Missing companion preset resource .blend')
        with bpy.data.libraries.load(str(resources),link=False) as (src,dst):
            image_names=list(src.images); material_names=list(src.materials); object_names=list(src.objects); dst.images=list(image_names); dst.materials=list(material_names); dst.objects=list(object_names)
        loaded_images=dict(zip(image_names,dst.images)); loaded_materials=dict(zip(material_names,dst.materials))
        loaded_objects=dict(zip(object_names,dst.objects))
        if loaded_objects:
            collection=bpy.data.collections.get('Landscapy • Preset Sources')
            if not collection: collection=bpy.data.collections.new('Landscapy • Preset Sources'); bpy.context.scene.collection.children.link(collection)
            for ob in loaded_objects.values():
                if ob and not ob.users_collection: collection.objects.link(ob); ob.hide_render=True; ob.hide_set(True)
    def assign(entry,record):
        for key,value in record.items():
            prop=entry.bl_rna.properties.get(key)
            if not prop or prop.is_readonly or key in ['uid','status','rna_type']: continue
            if prop.type not in ['POINTER','COLLECTION']: setattr(entry,key,value)
        for field in IMAGE_FIELDS:
            if field in record: setattr(entry,field,loaded_images.get(record[field]))
        if 'material_override' in record: entry.material_override=loaded_materials.get(record['material_override'])
    assign(settings,data['settings']); settings.textures.clear(); settings.surfaces.clear(); settings.ornament_slots.clear(); settings.fruit_slots.clear()
    for record in data.get('textures',[]):
        t=settings.textures.add(); assign(t,record)
        if data['schema']==1 and record.get('filepath'):
            im_path=Path(record['filepath'])
            if im_path.is_file(): t.image=bpy.data.images.load(str(im_path),check_existing=True)
    for record in data.get('surfaces',[]): assign(settings.surfaces.add(),record)
    for record in data.get('ornaments',[]):
        slot=settings.ornament_slots.add(); assign(slot,record); slot.object=loaded_objects.get(record.get('object'))
    for record in data.get('fruits',[]):
        slot=settings.fruit_slots.add(); assign(slot,record); slot.object=loaded_objects.get(record.get('object'))
