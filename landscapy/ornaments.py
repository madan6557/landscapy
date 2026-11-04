"""Weighted, deterministic ornament objects bound to generated surfaces."""
import bpy
import math
import random
import colorsys
import hashlib
from mathutils import Vector,Matrix
from bpy.props import PointerProperty,FloatProperty,IntProperty,FloatVectorProperty,EnumProperty,BoolProperty
from . import attachments

def source_poll(self,ob): return ob.type=='MESH' and not ob.get('lp_ornament_owner')

class LPOrnamentSlot(bpy.types.PropertyGroup):
    object: PointerProperty(type=bpy.types.Object,poll=source_poll,name='Source Object')
    weight: FloatProperty(default=1,min=0)
    scale: FloatProperty(default=1,min=.001)
    offset: FloatProperty(default=0)
    rotation: FloatVectorProperty(size=3,subtype='EULER',default=(0,0,0))
    tint: FloatVectorProperty(size=3,subtype='COLOR',default=(1,1,1),min=0,max=1)

def attachment_slots(settings,category):
    return settings.fruit_slots if category=='FRUIT' else settings.ornament_slots

def attachment_value(settings,category,key):
    return getattr(settings,('fruit_' if category=='FRUIT' else 'ornament_')+key)

def attachment_enabled(settings,category):
    return settings.fruit_enabled if category=='FRUIT' else settings.ornaments_enabled

def attachment_status(settings,category,value):
    setattr(settings,'fruit_status' if category=='FRUIT' else 'ornament_status',value)

def owned(owner,category=None):
    uid=owner.landscapy.uid
    return [o for o in bpy.data.objects if uid and o.get('lp_ornament_owner')==uid and not o.get('lp_variant')
            and (category is None or o.get('lp_attachment_kind','ORNAMENT')==category)]

def remove(ob):
    data=ob.data; groups=[m.node_group for m in ob.modifiers if m.type=='NODES' and m.node_group]
    prototypes=[node.inputs['Object'].default_value for group in groups for node in group.nodes
                if node.type=='OBJECT_INFO' and node.inputs['Object'].default_value
                and (node.inputs['Object'].default_value.get('lp_live_ornament_prototype')
                     or node.inputs['Object'].default_value.get('lp_live_ornament_rest_proxy'))]
    bpy.data.objects.remove(ob,do_unlink=True)
    if data and data.users==0: bpy.data.meshes.remove(data)
    for group in groups:
        if group.users==0: bpy.data.node_groups.remove(group)
    for prototype in prototypes:
        if prototype.get('lp_live_ornament_rest_proxy'):
            from . import instance_cards
            instance_cards.clear(prototype)
            mesh=prototype.data
            bpy.data.objects.remove(prototype,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
        elif prototype.users==0:
            mesh=prototype.data
            bpy.data.objects.remove(prototype,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.get('lp_ornament_material') and material.users==0: bpy.data.materials.remove(material)

def clear(owner,category=None):
    for ob in owned(owner,category): remove(ob)

def wrap_material(source):
    if source is None:
        source=bpy.data.materials.get('LP Ornament Default') or bpy.data.materials.new('LP Ornament Default'); source.use_nodes=True
    # A fresh snapshot picks up source edits and leaves built variants untouched.
    key='LP Ornament '+hashlib.sha256(source.name_full.encode()).hexdigest()[:16]
    mat=source.copy(); mat.name=key; mat.use_nodes=True; mat['lp_ornament_material']=True
    nt=mat.node_tree; n=nt.nodes; L=nt.links.new
    color=n.new('ShaderNodeAttribute'); color.name='Ornament Tint'; color.attribute_name='lp_ornament_color'
    opacity=n.new('ShaderNodeAttribute'); opacity.name='Ornament Opacity'; opacity.attribute_name='lp_ornament_opacity'
    hsv_attr=n.new('ShaderNodeAttribute'); hsv_attr.name='Ornament HSV'; hsv_attr.attribute_name='lp_ornament_hsv'
    hsv_values=n.new('ShaderNodeSeparateXYZ'); L(hsv_attr.outputs['Vector'],hsv_values.inputs[0])
    principals=[node for node in n if node.type=='BSDF_PRINCIPLED']
    for principal in principals:
        socket=principal.inputs['Base Color']; mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1
        hsv=n.new('ShaderNodeHueSaturation'); hsv.name='Randomize Source HSV'
        if socket.is_linked: L(socket.links[0].from_socket,hsv.inputs['Color'])
        else: hsv.inputs['Color'].default_value=socket.default_value
        for i,key in enumerate(['Hue','Saturation','Value']): L(hsv_values.outputs[i],hsv.inputs[key])
        L(hsv.outputs[0],mix.inputs[1])
        L(color.outputs['Color'],mix.inputs[2]); L(mix.outputs[0],socket)
        socket=principal.inputs['Alpha']; mul=n.new('ShaderNodeMath'); mul.operation='MULTIPLY'
        if socket.is_linked: L(socket.links[0].from_socket,mul.inputs[0])
        else: mul.inputs[0].default_value=socket.default_value
        L(opacity.outputs['Fac'],mul.inputs[1]); L(mul.outputs[0],socket)
    mat['lp_tint_supported']=bool(principals)
    return mat

def rebuild(owner,category='ORNAMENT'):
    from . import instance_cards, preview
    s=owner.landscapy
    use_full=attachment_enabled(s,category) and s.mode!='Individual'
    if use_full:
        # Barycentric anchors need the full evaluated card topology. An asset
        # can enable ornaments after its live graph was created in preview.
        preview.sync(owner)
    if use_full and owner.get('lp_live_mode') and instance_cards.modifier(owner) and category=='ORNAMENT':
        from . import live_ornaments
        return live_ornaments.rebuild(owner)
    snapshot=(instance_cards.full_mesh(owner)
              if use_full
              and instance_cards.modifier(owner) else None)
    try:
        result=_rebuild(owner,snapshot,category)
        if not use_full: preview.sync(owner)
        return result
    finally:
        if snapshot and snapshot.users==0: bpy.data.meshes.remove(snapshot)


def _rebuild(owner,snapshot=None,category='ORNAMENT'):
    from . import Builder,mesh_object
    s=owner.landscapy
    value=lambda key: attachment_value(s,category,key)
    permitted=s.kind in ['Tree','Foliage','Ivy'] and s.mode!='Individual'
    if not permitted or not attachment_enabled(s,category):
        clear(owner,category); attachment_status(s,category,'Disabled / individual mode'); return
    slots=[x for x in attachment_slots(s,category) if x.object and x.weight>0]
    if not slots:
        clear(owner,category); attachment_status(s,category,'Add at least one weighted source object'); return
    for slot in slots:
        if slot.object==owner or slot.object.get('lp_ornament_owner') or slot.object.get('lp_variant'):
            raise ValueError('Ornament source cannot be this generator or a managed output')
        if slot.object.type!='MESH': raise ValueError('Ornament source must be a mesh object')
    density=attachment_value(s,category,'density')
    if density<=0:
        clear(owner,category); attachment_status(s,category,'Density zero'); return
    mesh=snapshot or owner.data; mesh.calc_loop_triangles(); flags=mesh.attributes.get('lp_card'); branch_ids=mesh.attributes.get('lp_branch_id')
    branch_levels=mesh.attributes.get('lp_branch_level'); branch_t=mesh.attributes.get('lp_branch_t')
    low=min((v.co.z for v in mesh.vertices),default=0); high=max((v.co.z for v in mesh.vertices),default=1); height=max(.001,high-low)
    eligible=[]; areas=[]
    for triangle in mesh.loop_triangles:
        is_leaf=bool(flags and flags.data[triangle.polygon_index].value)
        zone=attachment_value(s,category,'zone')
        fruit_type=s.fruit_type if category=='FRUIT' else 'CUSTOM'
        ornament_type=s.ornament_type if category=='ORNAMENT' else 'CUSTOM'
        if category=='FRUIT' and fruit_type!='CUSTOM': zone='ALL'
        if category=='ORNAMENT' and ornament_type in {'BUD','SEED_POD'}: zone='ALL'
        if category=='ORNAMENT' and s.kind=='Tree' and s.ornament_branch_id>=0 and (not branch_ids or any(branch_ids.data[vertex].value!=s.ornament_branch_id for vertex in triangle.vertices)):
            continue
        if zone=='WOOD' and is_leaf: continue
        if zone=='FOLIAGE' and not is_leaf: continue
        z=sum(mesh.vertices[i].co.z for i in triangle.vertices)/3
        normalized_height=(z-low)/height
        height_min=attachment_value(s,category,'height_min'); height_max=attachment_value(s,category,'height_max')
        if ((category=='ORNAMENT' and ornament_type not in {'BUD','SEED_POD'}) or
            (category=='FRUIT' and fruit_type=='CUSTOM')) and not height_min <= normalized_height <= height_max: continue
        branch_id=branch_ids.data[triangle.vertices[0]].value if branch_ids else -1
        if branch_ids and any(branch_ids.data[index].value!=branch_id for index in triangle.vertices):
            branch_id=-1
        level=branch_levels.data[triangle.vertices[0]].value if branch_levels else -1
        t=sum(branch_t.data[index].value for index in triangle.vertices)/3 if branch_t else 0.
        if category=='FRUIT' and s.kind=='Tree':
            if fruit_type!='CUSTOM' and branch_id<0: continue
            if fruit_type=='BANANA_BUNCH' and (is_leaf or branch_id!=0 or not .86<=t<=.99): continue
            if fruit_type=='AXILLARY_POME' and (is_leaf or branch_id<=0 or level<1 or not .24<=t<=.92): continue
            if fruit_type=='GRAPE_CLUSTER' and (is_leaf or branch_id<=0 or level<1 or t<.64): continue
            if fruit_type=='COCONUT_CROWN' and (not is_leaf or normalized_height<.68 or t>.28): continue
            if fruit_type=='HANGING_PANICLE' and (is_leaf or branch_id<=0 or level<1 or t<.70): continue
            if fruit_type=='RACEME' and (is_leaf or branch_id<=0 or level<1 or not .48<=t<=.94): continue
            if fruit_type=='CAULIFLOROUS' and (is_leaf or not (
                    branch_id==0 and .16<=normalized_height<=.76 or
                    branch_id>0 and level==1 and t<=.34)): continue
            if fruit_type=='TERMINAL_CYME' and (is_leaf or branch_id<=0 or level<1 or t<.78): continue
            if fruit_type=='AXILLARY_POD' and (is_leaf or branch_id<=0 or level<1 or not .28<=t<=.92): continue
            # Whole bough cards carry the outer silhouette past the wood tip.
            cone_start=.40 if s.pattern=='Conifer' else .58
            if fruit_type=='CONE_CLUSTER' and (is_leaf or branch_id<=0 or level!=1 or t<cone_start): continue
        elif category=='ORNAMENT' and s.kind=='Tree' and s.ornament_type in {'BUD','SEED_POD'}:
            if is_leaf or branch_id<=0 or level<1: continue
            if s.ornament_type=='BUD' and not .55<=t<=1.: continue
            if s.ornament_type=='SEED_POD' and not .32<=t<=.92: continue
        if triangle.area<=1e-12: continue
        a,b,c=[owner.matrix_world@mesh.vertices[i].co for i in triangle.vertices]
        world_area=(b-a).cross(c-a).length*.5
        if world_area<=1e-12: continue
        eligible.append(tuple(triangle.vertices)); areas.append(world_area)
    if not eligible:
        clear(owner,category); attachment_status(s,category,'No faces match selected zone / biological placement range'); return
    count=min(attachment_value(s,category,'limit'),int(sum(areas)*density))
    if category=='FRUIT' and s.kind=='Tree':
        if eligible and density>0: count=max(1,count)
        if s.fruit_type=='BANANA_BUNCH': count=1 if eligible else 0
        elif s.fruit_type=='COCONUT_CROWN' and eligible: count=min(2,max(1,count))
    if count==0:
        clear(owner,category); attachment_status(s,category,'Area × density produces zero ornaments'); return
    dg=bpy.context.evaluated_depsgraph_get(); dg.update(); ev=owner.evaluated_get(dg); evaluated=ev.to_mesh()
    try:
        if len(evaluated.vertices)!=len(mesh.vertices): raise ValueError('Regenerate before scattering: modifier changes target vertex count')
        evaluated_positions=[v.co.copy() for v in evaluated.vertices]
    finally: ev.to_mesh_clear()
    templates={}; materials=[]; material_indices={}
    try:
        for slot in slots:
            source=slot.object
            if source not in templates:
                evaluated_source=source.evaluated_get(dg); template=evaluated_source.to_mesh()
                if not template.polygons: evaluated_source.to_mesh_clear(); raise ValueError('Ornament source has no evaluated faces: '+source.name)
                templates[source]=(evaluated_source,template)
        builder=Builder(); id_values=[]; anchors=[]; colors=[]; hsv_fields=[]; opacities=[]; smooth=[]; accepted=[]; grid={}
        other_category='ORNAMENT' if category=='FRUIT' else 'FRUIT'
        occupied=[]; seen=set()
        for existing in owned(owner,other_category):
            anchor_attr=existing.data.attributes.get('lp_anchor_position')
            id_attr=existing.data.attributes.get('lp_ornament_id')
            if not anchor_attr: continue
            for index,item in enumerate(anchor_attr.data):
                identity=id_attr.data[index].value if id_attr else index
                if identity in seen: continue
                seen.add(identity); occupied.append(owner.matrix_world@Vector(item.vector))
        cross_spacing=max(value('spacing'),s.fruit_spacing if category=='ORNAMENT' else s.ornament_spacing)
        rng=random.Random(value('seed')); total=0
        hanging=category=='FRUIT' and s.fruit_type in {
            'BANANA_BUNCH','COCONUT_CROWN','GRAPE_CLUSTER','HANGING_PANICLE','RACEME','CONE_CLUSTER'
        }
        up=(owner.matrix_world.to_3x3().inverted_safe()@Vector((0,0,1))).normalized()
        for attempt in range(max(50,count*6)):
            triangle=eligible[rng.choices(range(len(eligible)),weights=areas)[0]]
            u=math.sqrt(rng.random()); v=rng.random(); bary=(1-u,u*(1-v),u*v)
            rest=owner.matrix_world@sum((mesh.vertices[i].co*w for i,w in zip(triangle,bary)),Vector())
            spacing=value('spacing')
            if cross_spacing and any((rest-position).length<cross_spacing for position in occupied): continue
            key=tuple(math.floor(v/max(spacing,1e-6)) for v in rest)
            if spacing and any((rest-p).length<spacing for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1) for p in grid.get((key[0]+x,key[1]+y,key[2]+z),[])): continue
            grid.setdefault(key,[]).append(rest); occupied.append(rest)
            # Each accepted site's separate streams isolate tint/selection/rotation.
            choice=random.Random(value('choice_seed')+attempt*1009)
            slot=choice.choices(slots,weights=[x.weight for x in slots])[0]
            cr=random.Random(value('color_seed')+attempt*1009); tr=random.Random(value('transform_seed')+attempt*1009)
            a,b,c=[evaluated_positions[i] for i in triangle]; point=a*bary[0]+b*bary[1]+c*bary[2]; normal=(b-a).cross(c-a).normalized()
            if normal.length<.5: continue
            if hanging:
                outward=normal-up*normal.dot(up)
                if outward.length_squared<1e-8:
                    outward=up.to_track_quat('Z','Y')@Vector((1,0,0))
                outward.normalize()
                basis=Matrix((outward,up.cross(outward),up)).transposed().to_4x4()
            else:
                basis=normal.to_track_quat('Z','Y').to_matrix().to_4x4()
            for axis,angle in zip('XYZ',slot.rotation): basis=basis@Matrix.Rotation(angle,4,axis)
            for axis,maximum in zip('XYZ',(value('pitch'),value('roll'),value('yaw'))):
                basis=basis@Matrix.Rotation(tr.uniform(-maximum,maximum),4,axis)
            scale=tr.uniform(value('size_min'),value('size_max'))*slot.scale
            scale_matrix=Matrix.Diagonal(Vector((*value('axes'),1)))
            transform=basis@scale_matrix@slot.object.matrix_world.to_3x3().to_4x4()
            origin=point+normal*(value('offset')+slot.offset)
            _,template=templates[slot.object]; template_uv=template.uv_layers.active
            colattr=template.attributes.get('lp_color'); opattr=template.attributes.get('lp_opacity')
            material_map=[]
            for mat in (list(template.materials) or [None]):
                if mat not in material_indices:
                    material_indices[mat]=len(materials); materials.append(wrap_material(mat))
                material_map.append(material_indices[mat])
            start=len(builder.v)
            # Preserve shared vertices, UV seams and source per-card attributes.
            builder.v.extend(tuple(origin+transform.to_3x3()@vertex.co*scale) for vertex in template.vertices)
            builder.col.extend(tuple(colattr.data[i].color) if colattr else (1,1,1,1) for i in range(len(template.vertices)))
            builder.opacity.extend(opattr.data[i].value if opattr else 1. for i in range(len(template.vertices)))
            chosen_branch=branch_ids.data[triangle[0]].value if branch_ids and all(branch_ids.data[i].value==branch_ids.data[triangle[0]].value for i in triangle) else -1
            chosen_level=branch_levels.data[triangle[0]].value if branch_levels else -1
            chosen_t=sum(branch_t.data[i].value*w for i,w in zip(triangle,bary)) if branch_t else 0.
            builder.leaf_wind.extend([0.]*len(template.vertices))
            builder.branch_ids.extend([chosen_branch]*len(template.vertices))
            builder.branch_levels.extend([chosen_level]*len(template.vertices))
            builder.branch_t.extend([chosen_t]*len(template.vertices))
            for polygon in template.polygons:
                builder.f.append(tuple(start+i for i in polygon.vertices)); builder.mi.append(material_map[min(polygon.material_index,len(material_map)-1)]); builder.card_flags.append(False); builder.card_ids.append(-1); smooth.append(polygon.use_smooth)
                builder.uv.extend(tuple(template_uv.data[i].uv) if template_uv else (0,0) for i in polygon.loop_indices)
            hsv=(.5+cr.uniform(value('hue_min'),value('hue_max')),cr.uniform(value('sat_min'),value('sat_max')),cr.uniform(value('value_min'),value('value_max')))
            tint=tuple(value('color')[i]*slot.tint[i] for i in range(3))+(1,)
            opacity=cr.uniform(value('opacity_min'),value('opacity_max')); n=len(template.vertices)
            id_values.extend([total]*n); anchors.extend([point]*n); colors.extend([tint]*n); hsv_fields.extend([hsv]*n); opacities.extend([opacity]*n)
            accepted.append({'source':slot.object.name,'triangle':list(triangle),'weights':list(bary),'branch_id':chosen_branch})
            total+=1
            if total>=count: break
        if not builder.v: clear(owner,category); attachment_status(s,category,'No samples accepted'); return
        category_name='Fruit' if category=='FRUIT' else 'Ornaments'
        obj=mesh_object(owner.name+' • '+category_name,[],[],owner.users_collection[0]); obj.parent=owner; obj.matrix_parent_inverse.identity(); obj.matrix_basis.identity()
        try:
            builder.finish(obj,materials)
            for polygon,value in zip(obj.data.polygons,smooth): polygon.use_smooth=value
            for name,kind,values,field in [('lp_ornament_id','INT',id_values,'value'),('lp_anchor_position','FLOAT_VECTOR',anchors,'vector'),('lp_ornament_color','FLOAT_COLOR',colors,'color'),('lp_ornament_hsv','FLOAT_VECTOR',hsv_fields,'vector'),('lp_ornament_opacity','FLOAT',opacities,'value')]: attachments.write_attribute(obj.data,name,kind,values,field)
            obj['lp_ornament_owner']=s.uid; obj['lp_attachment_kind']=category; obj['lp_ornament_count']=total
            obj.landscapy.target=owner; attachments.bind(obj,owner)
        except Exception:
            remove(obj); raise
        for old in owned(owner,category):
            if old!=obj: remove(old)
        for mat in list(bpy.data.materials):
            if mat.get('lp_ornament_material') and mat.users==0: bpy.data.materials.remove(mat)
        obj['lp_attachment_kind']=category
        attachment_status(s,category,f'{total} {category_name.lower()} • {len(builder.f):,} faces • bound to generator')
        status='fruit_status' if category=='FRUIT' else 'ornament_status'
        if any(not m.get('lp_tint_supported',False) for m in materials): setattr(s,status,getattr(s,status)+' • non-Principled shader: use lp_ornament_color/opacity attributes')
        return obj
    finally:
        for evaluated,mesh in templates.values(): evaluated.to_mesh_clear()

class LPAddOrnament(bpy.types.Operator):
    bl_idname='landscapy.add_ornament'; bl_label='Add Attachment Source'; bl_options={'REGISTER','UNDO'}
    category: EnumProperty(items=[('ORNAMENT','Ornament','Flower, bud, seed pod or custom decoration'),('FRUIT','Fruit','Fruit or fruit cluster')],default='ORNAMENT')
    def execute(self,context): attachment_slots(context.object.landscapy,self.category).add(); return {'FINISHED'}

class LPRemoveOrnament(bpy.types.Operator):
    bl_idname='landscapy.remove_ornament'; bl_label='Remove Attachment Source'; bl_options={'REGISTER','UNDO'}
    index: IntProperty()
    category: EnumProperty(items=[('ORNAMENT','Ornament',''),('FRUIT','Fruit','')],default='ORNAMENT')
    def execute(self,context):
        entries=attachment_slots(context.object.landscapy,self.category)
        if 0<=self.index<len(entries): entries.remove(self.index)
        return {'FINISHED'}

class LPGenerateOrnaments(bpy.types.Operator):
    bl_idname='landscapy.ornaments'; bl_label='Generate / Update Attachments'; bl_options={'REGISTER','UNDO'}
    category: EnumProperty(items=[('ORNAMENT','Ornament',''),('FRUIT','Fruit','')],default='ORNAMENT')
    def execute(self,context):
        try: rebuild(context.object,self.category)
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}

class LPStarterOrnament(bpy.types.Operator):
    bl_idname='landscapy.starter_ornament'; bl_label='Create Editable Starter Source'; bl_options={'REGISTER','UNDO'}
    category: EnumProperty(items=[('ORNAMENT','Ornament',''),('FRUIT','Fruit','')],default='ORNAMENT')
    kind: EnumProperty(items=[('BERRY','Berry','Single stylized berry'),('APPLE','Apple','Stylized pome fruit'),
        ('GRAPE','Grape Cluster','Cluster arranged on a hanging rachis'),('BANANA','Banana Bunch','Curved low-poly fingers hanging from a stalk'),
        ('COCONUT','Coconut Cluster','Several coconuts around a crown base'),('MANGO','Mango Panicle','Fruit group hanging from a panicle'),
        ('POD','Pod','Single tapered stylized pod'),('CONE','Conifer Cone','Layered low-poly cone scales'),
        ('FLOWER','Flower','Folded stylized petals'),('BUD','Flower Bud','Compact closed bud')])
    def execute(self,context):
        from . import Builder,mesh_object,material
        import bmesh
        owner=context.object
        collection=bpy.data.collections.get('Landscapy • Ornament Sources')
        if not collection: collection=bpy.data.collections.new('Landscapy • Ornament Sources'); context.scene.collection.children.link(collection)
        source_names={'BERRY':'Berry','APPLE':'Apple','GRAPE':'Grape Cluster','BANANA':'Banana Bunch',
                      'COCONUT':'Coconut Cluster','MANGO':'Mango Panicle','POD':'Pod','CONE':'Conifer Cone',
                      'FLOWER':'Flower','BUD':'Flower Bud'}
        label=source_names[self.kind]
        fruit_colors={'BERRY':(.72,.025,.012),'APPLE':(.83,.16,.06),'GRAPE':(.36,.12,.58),
                      'BANANA':(.92,.66,.08),'COCONUT':(.42,.22,.08),'MANGO':(.94,.38,.04),
                      'POD':(.28,.52,.12),'CONE':(.42,.25,.10)}
        if self.kind in fruit_colors:
            bm=bmesh.new()
            def ellipsoid(location,scale,subdivisions=2,direction=None):
                result=bmesh.ops.create_icosphere(bm,subdivisions=subdivisions,radius=1)
                verts=result['verts']
                bmesh.ops.scale(bm,verts=verts,vec=Vector(scale))
                if direction is not None:
                    rotation=Vector((0,0,1)).rotation_difference(Vector(direction).normalized()).to_matrix()
                    bmesh.ops.rotate(bm,verts=verts,cent=Vector(),matrix=rotation)
                bmesh.ops.translate(bm,verts=verts,vec=Vector(location))
            def stem(path,radii,sides=6):
                rings=[]
                for (x,y,z),radius in zip(path,radii):
                    rings.append([bm.verts.new((x+radius*math.cos(i*math.tau/sides),
                                                y+radius*math.sin(i*math.tau/sides),z)) for i in range(sides)])
                for lower,upper in zip(rings,rings[1:]):
                    for i in range(sides): bm.faces.new((lower[i],lower[(i+1)%sides],upper[(i+1)%sides],upper[i]))
            if self.kind=='BERRY': ellipsoid((0,0,-.10),(.13,.13,.16),2)
            elif self.kind=='APPLE':
                stem([(0,0,.02),(0,0,-.015)],[.018,.014],5); ellipsoid((0,0,-.12),(.16,.16,.18),2)
            elif self.kind=='GRAPE':
                stem([(0,0,0),(0,0,-.13),(0,0,-.27)],[.025,.021,.015],5)
                for z,radius,count in [(-.10,.07,1),(-.22,.10,3),(-.36,.08,4),(-.49,.055,3),(-.59,.025,1)]:
                    for i in range(count):
                        angle=i*math.tau/max(1,count)+z*2.1
                        ellipsoid((math.cos(angle)*radius*2,math.sin(angle)*radius*2,z),(radius,radius,radius),1)
            elif self.kind=='BANANA':
                from .tube_frames import frames

                peduncle=[(0,0,0),(.075,0,-.018),(.16,0,-.10),
                          (.193,0,-.22),(.198,0,-.60)]
                stem(peduncle,[.032,.034,.031,.025,.013],7)
                for hand,z in enumerate((-.26,-.40,-.53)):
                    scale=1.-hand*.14
                    for index in range(5):
                        angle=index*math.tau/5+hand*.42
                        radial=Vector((math.cos(angle),math.sin(angle),0))
                        center=Vector((.196,0,z))
                        path=[center+radial*(scale*(.040+.205*t))+
                              Vector((0,0,scale*(-.18*t+.245*t*t)))
                              for t in (0.,.18,.36,.58,.79,1.)]
                        radii=(.015,.032,.037,.034,.025,.009)
                        rings=[]
                        for point,(x,y),radius in zip(path,frames(path),radii):
                            rings.append([bm.verts.new(point+radius*scale*
                                          (x*math.cos(i*math.tau/7)+y*math.sin(i*math.tau/7)))
                                          for i in range(7)])
                        bm.faces.new(tuple(reversed(rings[0])))
                        for lower,upper in zip(rings,rings[1:]):
                            for i in range(7):
                                next_i=(i+1)%7
                                bm.faces.new((lower[i],lower[next_i],upper[next_i],upper[i]))
                        bm.faces.new(rings[-1])
                ellipsoid((.198,0,-.625),(.047,.043,.095),1)
            elif self.kind=='COCONUT':
                stem([(0,0,0),(0,0,-.06)],[.055,.045],7)
                for i in range(5):
                    angle=i*math.tau/5
                    ellipsoid((math.cos(angle)*.14,math.sin(angle)*.14,-.13-(i%2)*.035),(.105,.105,.13),1)
            elif self.kind=='POD':
                stem([(0,0,.04),(0,0,-.04)],[.025,.018],5)
                ellipsoid((0,0,-.22),(.075,.075,.28),2,(.08,-.12,-1))
            elif self.kind=='CONE':
                stem([(0,0,.14),(0,0,-.30)],[.028,.012],5)
                for row in range(6):
                    z=.06-row*.065; radius=.075*(1-row/7)
                    for i in range(7):
                        angle=i*math.tau/7+row*.34
                        center=(math.cos(angle)*radius,math.sin(angle)*radius,z)
                        ellipsoid(center,(.043,.036,.052),1,(math.cos(angle)*.55,math.sin(angle)*.55,-.82))
            else: # Mango panicle
                stem([(0,0,0),(0,0,-.10),(0,0,-.24)],[.026,.021,.014],5)
                ellipsoid((0,0,-.05),(.035,.035,.20),1)
                for i,(z,angle) in enumerate([(-.18,-.8),(-.25,.8),(-.34,-.45),(-.43,.6),(-.52,-.2)]):
                    ellipsoid((math.cos(angle)*.10,math.sin(angle)*.10,z),(.09,.075,.13),1)
            mesh=bpy.data.meshes.new(label+' Source'); bm.to_mesh(mesh); bm.free()
            obj=bpy.data.objects.new('Landscapy Source • '+label,mesh); collection.objects.link(obj)
            mesh.materials.append(material('Starter '+label,fruit_colors[self.kind]))
        else:
            builder=Builder()
            if self.kind=='FLOWER':
                for i in range(5):
                    a=i*math.tau/5; direction=Vector((math.cos(a),math.sin(a),0)); side=Vector((-direction.y,direction.x,0))
                    builder.add([direction*.025,direction*.14+side*.065,direction*.24,direction*.14-side*.065,direction*.13+Vector((0,0,.045))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
            else:
                builder.add([Vector((0,0,-.02)),Vector((-.08,0,-.12)),Vector((0,0,-.25)),Vector((.08,0,-.12)),Vector((0,0,-.13))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)])
            obj=mesh_object('Landscapy Source • '+label,[],[],collection); builder.finish(obj,[material('Starter '+label,(.95,.65,.08) if self.kind=='FLOWER' else (.52,.20,.12))])
        obj.hide_render=True; obj.hide_set(True)
        settings=owner.landscapy; slot=attachment_slots(settings,self.category).add(); slot.object=obj
        if self.category=='FRUIT': settings.fruit_enabled=True
        else: settings.ornaments_enabled=True
        return {'FINISHED'}

class LPPickBranch(bpy.types.Operator):
    bl_idname='landscapy.pick_branch'; bl_label='Pick Selected Branch Face'; bl_options={'REGISTER','UNDO'}
    bl_description='Select one tree face in Edit Mode or Object Mode, then use its stable Branch ID for ornaments'
    def execute(self,context):
        owner=context.object
        if not owner or owner.type!='MESH' or owner.landscapy.kind!='Tree' or not owner.landscapy.uid:
            self.report({'ERROR'},'Select a Landscapy tree generator'); return {'CANCELLED'}
        branch_id=None
        if owner.mode=='EDIT':
            import bmesh
            bm=bmesh.from_edit_mesh(owner.data)
            layer=bm.verts.layers.int.get('lp_branch_id')
            face=bm.faces.active if bm.faces.active and bm.faces.active.select else next((f for f in bm.faces if f.select),None)
            if face and layer: branch_id=face.verts[0][layer]
        else:
            attr=owner.data.attributes.get('lp_branch_id')
            face=next((f for f in owner.data.polygons if f.select),None)
            if face and attr: branch_id=attr.data[face.vertices[0]].value
        if branch_id is None or branch_id<0:
            self.report({'ERROR'},'Select a trunk, branch or tree foliage face with a Branch ID'); return {'CANCELLED'}
        owner.landscapy.ornament_branch_id=branch_id
        self.report({'INFO'},f'Branch ID {branch_id} selected; update ornaments to apply')
        return {'FINISHED'}

def draw(layout,s):
    if s.kind not in ['Tree','Foliage','Ivy'] or s.mode=='Individual':
        header,body=layout.panel('LP_Fruit',default_closed=True); header.label(text='Fruit')
        if body: body.label(text='Generated plant mode required')
        header,body=layout.panel('LP_Ornaments',default_closed=True); header.label(text='Ornaments')
        if body: body.label(text='Generated plant mode required')
        return
    for category,title in [('FRUIT','Fruit'),('ORNAMENT','Ornaments')]:
        header,body=layout.panel('LP_'+title.replace(' ','_'),default_closed=True); header.label(text=title)
        if not body: continue
        fruit=category=='FRUIT'; prefix='fruit_' if fruit else 'ornament_'
        slots=attachment_slots(s,category)
        enabled='fruit_enabled' if fruit else 'ornaments_enabled'
        body.prop(s,enabled)
        if fruit:
            body.prop(s,'fruit_type')
            kind={'BANANA_BUNCH':'BANANA','AXILLARY_POME':'APPLE','GRAPE_CLUSTER':'GRAPE','COCONUT_CROWN':'COCONUT',
                  'HANGING_PANICLE':'MANGO','RACEME':'GRAPE','CAULIFLOROUS':'BERRY','TERMINAL_CYME':'BERRY',
                  'AXILLARY_POD':'POD','CONE_CLUSTER':'CONE'}.get(s.fruit_type,'BERRY')
            op=body.operator('landscapy.starter_ornament',text='Create Matching Fruit Source',icon='MESH_UVSPHERE'); op.kind=kind; op.category='FRUIT'
        else:
            body.prop(s,'ornament_type')
            op=body.operator('landscapy.starter_ornament',text='Create Flower Source' if s.ornament_type in {'FLOWER','BUD'} else 'Create Berry Source',icon='OUTLINER_OB_CURVES')
            op.kind='BUD' if s.ornament_type=='BUD' else 'FLOWER' if s.ornament_type=='FLOWER' else 'BERRY'; op.category='ORNAMENT'
        add=body.operator('landscapy.add_ornament',text='Add Custom Source'); add.category=category
        for i,slot in enumerate(slots):
            box=body.box()
            for key in ['object','weight','scale','offset','rotation','tint']: box.prop(slot,key)
            remove_op=box.operator('landscapy.remove_ornament'); remove_op.index=i; remove_op.category=category
        if s.kind=='Tree' and not fruit:
            body.prop(s,'ornament_branch_id'); body.operator('landscapy.pick_branch')
            body.label(text='-1 = all; pick a face, then update ornaments')
        if fruit:
            keys=['zone','density','limit','spacing','height_min','height_max','offset','seed','choice_seed','transform_seed','color_seed','size_min','size_max','axes','yaw','pitch','roll','color','hue_min','hue_max','sat_min','sat_max','value_min','value_max','opacity_min','opacity_max']
            labels={'zone':'Manual Surface Zone','seed':'Position Seed','choice_seed':'Source Choice Seed','transform_seed':'Transform Seed','color_seed':'Color Seed'}
        else:
            keys=['zone','density','limit','spacing','height_min','height_max','offset','seed','choice_seed','transform_seed','color_seed','size_min','size_max','axes','yaw','pitch','roll','color','hue_min','hue_max','sat_min','sat_max','value_min','value_max','opacity_min','opacity_max']
            labels={'seed':'Position Seed','choice_seed':'Source Choice Seed','transform_seed':'Transform Seed','color_seed':'Color Seed'}
        for key in keys:
            prop_name=prefix+key
            if prop_name not in s.bl_rna.properties: continue
            row=body.row(); row.prop(s,prop_name,text=labels.get(key,'') or None)
        update=body.operator('landscapy.ornaments',text='Generate / Update '+title,icon='FILE_REFRESH'); update.category=category
        body.label(text=s.fruit_status if fruit else s.ornament_status)
        if s.live_surface and s.instance_cards:
            body.label(text='Placement follows live geometry; source/type changes need Update',icon='INFO')
