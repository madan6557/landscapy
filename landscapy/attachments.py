"""Persistent barycentric attachment evaluated by Geometry Nodes.

Only validity checks run in Python. Vertex deformation itself lives in the saved
node graph, sampling the evaluated target in the attached object's local space.
"""
import array
import hashlib
import json
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector
from mathutils.bvhtree import BVHTree

NAME='Landscapy Attachment'
_checking=False

def signature(mesh):
    indices=array.array('i',[0])*len(mesh.loops)
    starts=array.array('i',[0])*len(mesh.polygons)
    mesh.loops.foreach_get('vertex_index',indices)
    mesh.polygons.foreach_get('loop_start',starts)
    h=hashlib.blake2b(digest_size=16)
    h.update(str((len(mesh.vertices),len(mesh.polygons),len(mesh.loops))).encode())
    h.update(indices.tobytes()); h.update(starts.tobytes())
    return h.hexdigest()

def validate_target(ob,target):
    if not target or target.type!='MESH' or target==ob:
        raise ValueError('Choose another mesh as attachment target')
    seen={ob}; current=target
    while current:
        if current in seen: raise ValueError('Attachment dependency cycle is not allowed')
        seen.add(current)
        current=current.landscapy.target if current.get('lp_binding_signature') else None
    # A target parented under its dependent cannot be evaluated without a cycle.
    current=target.parent
    while current:
        if current==ob: raise ValueError('Target cannot be a child of the attached object')
        current=current.parent

def weights(p,a,b,c):
    ab=b-a; ac=c-a; ap=p-a
    aa=ab.dot(ab); bb=ab.dot(ac); cc=ac.dot(ac); d=ap.dot(ab); e=ap.dot(ac)
    denom=aa*cc-bb*bb
    if abs(denom)<1e-14: return (1.,0.,0.)
    v=(cc*d-bb*e)/denom; w=(aa*e-bb*d)/denom
    return (1-v-w,v,w)

def frame(a,b,c):
    tangent=(b-a).normalized(); normal=(b-a).cross(c-a).normalized()
    if tangent.length<.5 or normal.length<.5: raise ValueError('Cannot bind to a degenerate target triangle')
    return tangent,normal.cross(tangent).normalized(),normal

def branch_graph(target):
    payload=target.get('lp_branch_graph') if target else None
    if not payload: return {}
    try:
        rows=json.loads(payload)['branches']
        return {int(row['id']):row for row in rows if int(row['id'])>=0}
    except (ValueError,KeyError,TypeError): return {}

def branch_frame(row,t,transform):
    points=[transform@Vector(p) for p in row['points']]
    position=max(0.,min(1.,t))*(len(points)-1)
    index=min(len(points)-2,int(position))
    center=points[index].lerp(points[index+1],position-index)
    tangent=(points[index+1]-points[index]).normalized()
    if tangent.length<.5: raise ValueError('Degenerate semantic branch path')
    return center,tangent.to_track_quat('Z','Y').to_matrix()

def write_attribute(mesh,name,kind,values,field):
    old=mesh.attributes.get(name)
    if old: mesh.attributes.remove(old)
    attr=mesh.attributes.new(name,kind,'POINT')
    for item,value in zip(attr.data,values): setattr(item,field,value)

def setup_graph(ob,target,vertex_count,face_count):
    old=ob.modifiers.get(NAME)
    if old:
        group=old.node_group if old.type=='NODES' else None
        ob.modifiers.remove(old)
        if group and group.users==0: bpy.data.node_groups.remove(group)
    mod=ob.modifiers.new(NAME,'NODES')
    graph=bpy.data.node_groups.new('LP Barycentric Binding','GeometryNodeTree'); graph.is_modifier=True; mod.node_group=graph
    graph.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    graph.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=graph.nodes; L=graph.links.new
    def new(kind,name):
        n=nodes.new(kind); n.name=name; n.label=name; return n
    def vec(op,a,b=None,name='Vector'):
        n=new('ShaderNodeVectorMath',name); n.operation=op
        L(a,n.inputs[0])
        if b is not None: L(b,n.inputs['Scale'] if op=='SCALE' else n.inputs[1])
        return n.outputs[0]
    def attr(name,kind):
        n=new('GeometryNodeInputNamedAttribute',name); n.data_type=kind; n.inputs['Name'].default_value=name
        return n.outputs['Attribute']
    inp=new('NodeGroupInput','Rest Geometry'); out=new('NodeGroupOutput','Bound Geometry')
    info=new('GeometryNodeObjectInfo','Evaluated Target'); info.inputs['Object'].default_value=target; info.transform_space='RELATIVE'
    position=new('GeometryNodeInputPosition','Target Vertex Position')
    positions=[]
    for i in range(3):
        sample=new('GeometryNodeSampleIndex','Triangle Vertex '+str(i)); sample.data_type='FLOAT_VECTOR'; sample.domain='POINT'; sample.clamp=False
        L(info.outputs['Geometry'],sample.inputs['Geometry']); L(position.outputs[0],sample.inputs['Value']); L(attr('lp_bind_i'+str(i),'INT'),sample.inputs['Index'])
        positions.append(sample.outputs['Value'])
    w=new('ShaderNodeSeparateXYZ','Barycentric Weights'); L(attr('lp_bind_weights','FLOAT_VECTOR'),w.inputs[0])
    anchor=vec('ADD',vec('ADD',vec('SCALE',positions[0],w.outputs[0]),vec('SCALE',positions[1],w.outputs[1])),vec('SCALE',positions[2],w.outputs[2]),'Target Anchor')
    ab=vec('SUBTRACT',positions[1],positions[0]); ac=vec('SUBTRACT',positions[2],positions[0])
    tangent=vec('NORMALIZE',ab); normal=vec('NORMALIZE',vec('CROSS_PRODUCT',ab,ac)); bitangent=vec('NORMALIZE',vec('CROSS_PRODUCT',normal,tangent))
    offset=new('ShaderNodeSeparateXYZ','Local Anchor Offset'); L(attr('lp_bind_offset','FLOAT_VECTOR'),offset.inputs[0])
    shift=vec('ADD',vec('ADD',vec('SCALE',tangent,offset.outputs[0]),vec('SCALE',bitangent,offset.outputs[1])),vec('SCALE',normal,offset.outputs[2]))
    move=new('GeometryNodeSetPosition','Follow Surface'); L(inp.outputs[0],move.inputs['Geometry']); L(vec('ADD',anchor,shift),move.inputs['Position'])
    size=new('GeometryNodeAttributeDomainSize','Target Topology Guard'); size.component='MESH'; L(info.outputs['Geometry'],size.inputs['Geometry'])
    guards=[]
    for socket,expected in [('Point Count',vertex_count),('Face Count',face_count)]:
        test=new('ShaderNodeMath','Expected '+socket); test.operation='COMPARE'; test.inputs[1].default_value=expected; test.inputs[2].default_value=.1; L(size.outputs[socket],test.inputs[0]); guards.append(test.outputs[0])
    valid=new('ShaderNodeValue','Binding Valid'); valid.outputs[0].default_value=1.
    for guard in guards:
        test=new('ShaderNodeMath','Topology AND'); test.operation='MULTIPLY'; L(valid.outputs[0] if hasattr(valid,'outputs') else valid,test.inputs[0]); L(guard,test.inputs[1]); valid=test.outputs[0]
    switch=new('GeometryNodeSwitch','Safe Rest Pose If Invalid'); switch.input_type='GEOMETRY'
    L(valid,switch.inputs['Switch']); L(inp.outputs[0],switch.inputs['False']); L(move.outputs[0],switch.inputs['True']); L(switch.outputs[0],out.inputs[0])
    ob.modifiers.move(len(ob.modifiers)-1,0)
    for i,n in enumerate(nodes): n.location=((i%7)*210,-(i//7)*180)
    local=ob.modifiers.get('Landscapy Wind')
    if local: local.show_viewport=local.show_render=ob.landscapy.attachment_local_wind

def bind(ob,target):
    validate_target(ob,target)
    if ob.type!='MESH' or not ob.data.vertices: raise ValueError('Attached object must contain mesh vertices')
    dg=bpy.context.evaluated_depsgraph_get(); dg.update(); evaluated=target.evaluated_get(dg); mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        transform=ob.matrix_world.inverted()@target.matrix_world
        verts=[transform@v.co for v in mesh.vertices]
        triangles=[tuple(t.vertices) for t in mesh.loop_triangles if t.area>1e-12]
        if not triangles: raise ValueError('Target has no nondegenerate mesh faces')
        tree=BVHTree.FromPolygons(verts,triangles,all_triangles=True)
        ids=[[],[],[]]; bary=[]; offsets=[]; anchor_cache={}
        semantic=branch_graph(target)
        branch_ids=mesh.attributes.get('lp_branch_id') if semantic else None
        branch_t=mesh.attributes.get('lp_branch_t') if semantic else None
        semantic_ids=[]; semantic_t=[]; semantic_offsets=[]
        group_ids=ob.data.attributes.get('lp_ornament_id'); group_positions=ob.data.attributes.get('lp_anchor_position')
        for vertex in ob.data.vertices:
            point=vertex.co.copy()
            group=group_ids.data[vertex.index].value if group_ids and group_positions else None
            query=Vector(group_positions.data[vertex.index].vector) if group is not None else point
            if group is not None and group in anchor_cache: hit,index=anchor_cache[group]
            else:
                hit,_,index,_=tree.find_nearest(query)
                if group is not None: anchor_cache[group]=(hit,index)
            if index is None: raise ValueError('No attachment triangle found')
            tri=triangles[index]; a,b,c=[verts[i] for i in tri]; t,bt,n=frame(a,b,c); delta=point-hit
            for j in range(3): ids[j].append(tri[j])
            w=weights(hit,a,b,c)
            bary.append(w); offsets.append((delta.dot(t),delta.dot(bt),delta.dot(n)))
            branch_id=branch_ids.data[tri[0]].value if branch_ids and all(branch_ids.data[i].value==branch_ids.data[tri[0]].value for i in tri) else -1
            if branch_id in semantic and branch_t:
                along=sum(branch_t.data[i].value*weight for i,weight in zip(tri,w))
                center,orientation=branch_frame(semantic[branch_id],along,transform)
                semantic_ids.append(branch_id); semantic_t.append(along); semantic_offsets.append(orientation.transposed()@(point-center))
            else:
                semantic_ids.append(-1); semantic_t.append(0.); semantic_offsets.append(Vector())
        fingerprint=signature(mesh); vertex_count=len(mesh.vertices); face_count=len(mesh.polygons)
    finally: evaluated.to_mesh_clear()
    # Do not partially replace a valid binding until all samples were computed.
    for i in range(3): write_attribute(ob.data,'lp_bind_i'+str(i),'INT',ids[i],'value')
    write_attribute(ob.data,'lp_bind_weights','FLOAT_VECTOR',bary,'vector'); write_attribute(ob.data,'lp_bind_offset','FLOAT_VECTOR',offsets,'vector')
    for name in ('lp_bind_branch_id','lp_bind_branch_t','lp_bind_branch_offset'):
        old=ob.data.attributes.get(name)
        if old: ob.data.attributes.remove(old)
    if any(branch_id>=0 for branch_id in semantic_ids):
        write_attribute(ob.data,'lp_bind_branch_id','INT',semantic_ids,'value')
        write_attribute(ob.data,'lp_bind_branch_t','FLOAT',semantic_t,'value')
        write_attribute(ob.data,'lp_bind_branch_offset','FLOAT_VECTOR',semantic_offsets,'vector')
        ob['lp_bind_semantic_uid']=target.landscapy.uid
    elif 'lp_bind_semantic_uid' in ob: del ob['lp_bind_semantic_uid']
    if 'lp_missing_branch_id' in ob: del ob['lp_missing_branch_id']
    ob.landscapy.target=target; ob.landscapy.binding_valid=True
    ob.landscapy.binding_message='Bound • semantic branch anchors' if ob.get('lp_bind_semantic_uid') else 'Bound • follows evaluated target'
    ob['lp_binding_signature']=fingerprint
    setup_graph(ob,target,vertex_count,face_count)
    if ob.landscapy.uid:
        from . import preview
        preview.sync(ob,force=True)

def unbind(ob):
    mod=ob.modifiers.get(NAME)
    if mod: ob.modifiers.remove(mod)
    if 'lp_binding_signature' in ob: del ob['lp_binding_signature']
    if 'lp_bind_semantic_uid' in ob: del ob['lp_bind_semantic_uid']
    if 'lp_missing_branch_id' in ob: del ob['lp_missing_branch_id']
    for attr in list(ob.data.attributes):
        if attr.name.startswith('lp_bind_'): ob.data.attributes.remove(attr)
    ob.landscapy.binding_valid=False; ob.landscapy.binding_message='Unbound'
    local=ob.modifiers.get('Landscapy Wind')
    if local: local.show_render=local.show_viewport=True
    if ob.landscapy.uid:
        from . import preview
        preview.sync(ob,force=True)

def rebind_dependents(target):
    """Move existing manual bindings with their semantic branch on regeneration."""
    graph=branch_graph(target)
    if not graph: return 0
    dependents=[ob for ob in bpy.data.objects if ob!=target and ob.landscapy.target==target
                and ob.get('lp_binding_signature') and ob.get('lp_bind_semantic_uid')
                and ob.get('lp_ornament_owner')!=target.landscapy.uid]
    if not dependents: return 0
    wind=target.modifiers.get('Landscapy Wind')
    wind_enabled=wind.show_viewport if wind else None
    if wind: wind.show_viewport=False
    count=0
    try:
        bpy.context.view_layer.update()
        for ob in dependents:
            ids=ob.data.attributes.get('lp_bind_branch_id')
            ts=ob.data.attributes.get('lp_bind_branch_t')
            offsets=ob.data.attributes.get('lp_bind_branch_offset')
            if not ids or not ts or not offsets: continue
            missing=next((item.value for item in ids.data if item.value>=0 and item.value not in graph),None)
            if missing is not None:
                ob['lp_missing_branch_id']=missing
                ob.landscapy.binding_valid=False
                ob.landscapy.binding_message=f'Branch ID {missing} missing after regeneration • choose another branch or Rebind'
                continue
            if ob.mode=='EDIT':
                ob.landscapy.binding_valid=False
                ob.landscapy.binding_message='Exit Edit Mode and Rebind after tree regeneration'
                continue
            transform=ob.matrix_world.inverted()@target.matrix_world
            positions=[vertex.co.copy() for vertex in ob.data.vertices]
            if ob.data.users>1: ob.data=ob.data.copy()
            try:
                for i,vertex in enumerate(ob.data.vertices):
                    branch_id=ids.data[i].value
                    if branch_id<0: continue
                    center,orientation=branch_frame(graph[branch_id],ts.data[i].value,transform)
                    vertex.co=center+orientation@Vector(offsets.data[i].vector)
                ob.data.update()
                bind(ob,target)
                count+=1
            except Exception as error:
                for vertex,position in zip(ob.data.vertices,positions): vertex.co=position
                ob.data.update()
                ob.landscapy.binding_valid=False
                ob.landscapy.binding_message=f'Semantic Rebind failed: {error}'
    finally:
        if wind: wind.show_viewport=wind_enabled
    return count

@persistent
def check_bindings(scene,depsgraph):
    global _checking
    if _checking: return
    _checking=True
    try:
        cache={}
        for ob in list(scene.objects):
            expected=ob.get('lp_binding_signature')
            if not expected or not hasattr(ob,'landscapy'): continue
            target=ob.landscapy.target
            if target not in cache:
                current=None
                if target and target.type=='MESH':
                    evaluated=target.evaluated_get(depsgraph); mesh=evaluated.to_mesh()
                    try: current=signature(mesh)
                    finally: evaluated.to_mesh_clear()
                cache[target]=current
            missing=ob.get('lp_missing_branch_id')
            valid=missing is None and cache[target]==expected
            if ob.landscapy.binding_valid!=valid:
                ob.landscapy.binding_valid=valid
                ob.landscapy.binding_message=(('Bound • semantic branch anchors' if ob.get('lp_bind_semantic_uid') else 'Bound • follows evaluated target') if valid
                                             else f'Branch ID {missing} missing after regeneration • choose another branch or Rebind' if missing is not None
                                             else 'Target topology changed or missing • Rebind required')
                modifier=ob.modifiers.get(NAME)
                if modifier and modifier.type=='NODES' and modifier.node_group:
                    node=modifier.node_group.nodes.get('Binding Valid')
                    if node: node.outputs[0].default_value=float(valid)
                    modifier.node_group.update_tag()
                ob.update_tag()
    finally: _checking=False

def register():
    if check_bindings not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(check_bindings)

def unregister():
    if check_bindings in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(check_bindings)
