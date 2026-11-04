"""Seeded surface growth and evaluated path ivy; no botanical simulation."""
import bpy, math, random
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from . import paths, fronds


def _surface_components(triangles):
    """Map BVH triangles to edge-connected target surface islands."""
    parents=list(range(len(triangles)))
    def find(index):
        while parents[index]!=index:
            parents[index]=parents[parents[index]]
            index=parents[index]
        return index
    def union(a,b):
        a=find(a); b=find(b)
        if a!=b: parents[b]=a
    edge_owner={}
    for index,triangle in enumerate(triangles):
        a,b,c=triangle
        for edge in (tuple(sorted((a,b))),tuple(sorted((b,c))),tuple(sorted((c,a)))):
            other=edge_owner.setdefault(edge,index)
            union(index,other)
    return [find(index) for index in range(len(triangles))]


def generate(builder,s,ob):
    inv=ob.matrix_world.inverted(); ctrl=s.controller
    target=s.target if s.target and s.target.type=='MESH' else ctrl if ctrl and ctrl.type=='MESH' else None
    if s.mode=='Individual':
        return [(Vector(),Vector((0,0,1)),{'frame':fronds.frame(Vector((0,0,1)),Vector((0,-1,0))),'width':s.ivy_leaf_size*.8,'height':s.ivy_leaf_size,'pivot':0.,'segments':s.subdivisions})]
    if s.mode=='Volume': raise ValueError('Ivy uses Auto, Surface, Path, or Individual; Volume is not supported')
    if s.mode=='Path' and (not ctrl or ctrl.type!='CURVE'): raise ValueError('Ivy Path mode requires a curve controller')
    if s.mode=='Surface' and not target: raise ValueError('Ivy Surface mode requires a mesh controller or target')
    if target==ob: raise ValueError('Ivy surface target cannot be the generator itself')
    if ctrl and ctrl.type=='CURVE' and target and s.ivy_projection=='CUSTOM' and Vector(s.ivy_ray_direction).length<1e-6:
        raise ValueError('Custom Ivy ray direction must be nonzero')
    bvh=None; components=[]; component_triangles={}; component_bounds={}; component_bvhs={}; world_vertices=[]
    if target:
        ev=target.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        try:
            me.calc_loop_triangles()
            if not me.loop_triangles: raise ValueError('Ivy surface target has no triangles')
            triangles=[tuple(t.vertices) for t in me.loop_triangles if t.area>1e-12]
            if not triangles: raise ValueError('Ivy surface target has no nondegenerate triangles')
            components=_surface_components(triangles)
            world_vertices=[target.matrix_world@v.co for v in me.vertices]
            for triangle_index,(triangle,component) in enumerate(zip(triangles,components)):
                component_triangles.setdefault(component,[]).append(triangle_index)
                points=[world_vertices[index] for index in triangle]
                if component not in component_bounds:
                    component_bounds[component]=([min(p[axis] for p in points) for axis in range(3)],
                                                 [max(p[axis] for p in points) for axis in range(3)])
                else:
                    lower,upper=component_bounds[component]
                    for axis in range(3):
                        lower[axis]=min(lower[axis],*(p[axis] for p in points))
                        upper[axis]=max(upper[axis],*(p[axis] for p in points))
            bvh=BVHTree.FromPolygons(world_vertices,triangles,all_triangles=True)
        finally: ev.to_mesh_clear()
    rng=random.Random(s.seed); curves=[]; stopped=0
    # Stored paths and normals are world-space until emitted into the generator.
    if ctrl and ctrl.type=='CURVE':
        for path in paths.curve_paths(ctrl):
            samples=paths.resample(path,s.ivy_step); pts=[]; normals=[]
            for p in samples:
                if bvh:
                    if s.ivy_projection=='NEAREST':
                        hit,n,_,distance=bvh.find_nearest(p,s.ivy_probe)
                    else:
                        local=Vector((0,0,-1)) if s.ivy_projection=='DOWN' else Vector(s.ivy_ray_direction)
                        direction=(ob.matrix_world.to_3x3()@local).normalized()
                        hit,n,_,distance=bvh.ray_cast(p-direction*.001,direction,s.ivy_probe+.001)
                    if hit is None:
                        if len(pts)>1: curves.append((pts,normals))
                        pts=[]; normals=[]; stopped+=1; continue
                    pts.append(hit+n*s.ivy_offset); normals.append(n)
                else:
                    pts.append(p); normals.append(Vector((0,-1,0)))
            if len(pts)>1: curves.append((pts,normals))
    elif bvh:
        seed=ob.matrix_world@Vector(s.ivy_start)
        hit,normal,triangle_index,distance=bvh.find_nearest(seed)
        if hit is None: raise ValueError('No surface found at ivy seed')
        # Growth Direction is authored in generator-local space, like the seed.
        growth=ob.matrix_world.to_3x3()@Vector(s.ivy_direction)
        if growth.length<1e-6: raise ValueError('Ivy growth direction must be nonzero')
        pending=[(hit,normal,growth.normalized(),s.length,0,components[triangle_index])]
        branch_count=0; iterations=0
        while pending:
            position,normal,heading,length,depth,component=pending.pop(0)
            pts=[position+normal*s.ivy_offset]; normals=[normal.copy()]
            for step in range(min(20000,max(1,math.ceil(length/s.ivy_step)))):
                iterations+=1
                if iterations>s.ivy_max_steps: stopped+=1; pending.clear(); break
                forward=heading-normal*heading.dot(normal)
                desired=growth-normal*growth.dot(normal)
                if forward.length<.001 and desired.length>.001:
                    forward=desired.normalized()
                elif forward.length<.001:
                    forward=normal.to_track_quat('Z','Y')@Vector((0,1,0))
                forward.normalize()
                if desired.length>.001: forward=forward.lerp(desired.normalized(),s.ivy_up_bias).normalized()
                forward=Quaternion(normal,rng.uniform(-s.ivy_wander,s.ivy_wander))@forward
                travel=min(s.ivy_step,max(.001,length-step*s.ivy_step))
                proposal=position+forward*travel
                projected,n,triangle_index,_=bvh.ray_cast(proposal+normal*s.ivy_probe,-normal,2*s.ivy_probe)
                search=travel*(1+s.ivy_gap_bridge)
                if projected is None:
                    # Sweep along the current tangent to catch a connected
                    # surface at a corner before trying a nearest-point jump.
                    corner_origin=position+normal*max(.001,s.ivy_offset*.25)
                    projected,n,triangle_index,_=bvh.ray_cast(corner_origin,forward,search)
                if projected is None:
                    projected,n,triangle_index,_=bvh.find_nearest(proposal,search)
                if projected is None or triangle_index is None or not 0<=triangle_index<len(components):
                    stopped+=1; break
                next_component=components[triangle_index]
                same_island=next_component==component
                delta=projected-position; distance=delta.length
                if distance<travel*.2 and same_island and s.ivy_gap_bridge>0:
                    # BVH nearest-point ties at an island edge can keep
                    # returning the current island, preventing a configured
                    # bridge from ever being considered. Probe nearby island
                    # BVHs explicitly and accept only forward, bounded jumps.
                    best=None; search_sq=search*search
                    for candidate_component,(lower,upper) in component_bounds.items():
                        if candidate_component==component: continue
                        box_distance_sq=sum((lower[axis]-proposal[axis])**2 if proposal[axis]<lower[axis]
                                            else (proposal[axis]-upper[axis])**2 if proposal[axis]>upper[axis]
                                            else 0. for axis in range(3))
                        if box_distance_sq>search_sq: continue
                        if candidate_component not in component_bvhs:
                            indices=component_triangles[candidate_component]
                            component_bvhs[candidate_component]=(BVHTree.FromPolygons(
                                world_vertices,[triangles[index] for index in indices],all_triangles=True),indices)
                        island_bvh,index_map=component_bvhs[candidate_component]
                        alt,alt_normal,local_index,alt_distance=island_bvh.find_nearest(proposal,search)
                        if alt is None or local_index is None or not 0<=local_index<len(index_map): continue
                        alt_delta=alt-position; alt_length=alt_delta.length
                        if alt_length<travel*.2 or alt_length>search+1e-6: continue
                        if alt_delta.dot(forward)<travel*.15 or alt_normal.dot(normal)<math.cos(s.ivy_corner_limit): continue
                        score=alt_distance+max(0.,travel-alt_delta.dot(forward))*.25
                        if best is None or score<best[0]:
                            best=(score,alt,alt_normal,index_map[local_index],alt_delta,alt_length)
                    if best is not None:
                        _,projected,n,triangle_index,delta,distance=best
                        next_component=components[triangle_index]
                        same_island=False
                if not same_island and s.ivy_gap_bridge<=0:
                    stopped+=1; break
                if distance>search+1e-6 or n.dot(normal)<math.cos(s.ivy_corner_limit):
                    stopped+=1; break
                if distance<travel*.2:
                    # At a sharp connected corner the new face may begin at
                    # the same edge point. Change tangent and continue rather
                    # than counting the zero-distance handoff as a dead end.
                    tangent=heading-n*heading.dot(n)
                    next_heading=tangent
                    if next_heading.length<.001:
                        next_heading=growth-n*growth.dot(n)
                    if same_island and n.dot(normal)<.999 and next_heading.length>.001:
                        position=projected; normal=n; component=next_component
                        heading=next_heading.normalized()
                        continue
                    stopped+=1; break
                heading=delta.normalized(); position=projected; normal=n; component=next_component
                pts.append(position+normal*s.ivy_offset); normals.append(normal.copy())
                if depth==0 and branch_count<s.ivy_branches and step>2 and step%max(3,int(s.ivy_branch_spacing/s.ivy_step))==0:
                    branch_count+=1; sign=1 if branch_count%2 else -1
                    pending.append((position.copy(),normal.copy(),Quaternion(normal,sign*s.ivy_branch_angle)@heading,length*s.ivy_branch_length,1,component))
            if len(pts)>1: curves.append((pts,normals))
    else:
        direction=ob.matrix_world.to_3x3()@Vector(s.ivy_direction)
        if direction.length<1e-6: raise ValueError('Ivy growth direction must be nonzero')
        origin=ob.matrix_world@Vector(s.ivy_start); direction.normalize()
        pts=paths.resample([origin,origin+direction*s.length],s.ivy_step)
        curves=[(pts,[Vector((0,-1,0)) for _ in pts])]
    points=[]; candidates=[]
    for pts,normals in curves:
        # Remove any coincident projected stations before constructing tubes.
        clean=[(pts[0],normals[0])]
        for p,n in zip(pts[1:],normals[1:]):
            if (p-clean[-1][0]).length>1e-5: clean.append((p,n))
        if len(clean)<2: continue
        pts,normals=zip(*clean); local=[inv@p for p in pts]
        builder.tube(local,s.ivy_radius,s.ivy_vine_sides,.18)
        walked=0.; next_leaf=s.ivy_leaf_spacing*.5; step_length=max(s.ivy_leaf_spacing,1/max(.001,s.density))
        if s.density<=0: continue
        for a,b,na,nb in zip(pts,pts[1:],normals,normals[1:]):
            segment=(b-a).length
            while next_leaf<=walked+segment:
                t=(next_leaf-walked)/segment; p=a.lerp(b,t); n=na.lerp(nb,t).normalized(); tangent=(b-a).normalized()
                side=tangent.cross(n).normalized(); sign=1 if len(candidates)%2 else -1
                axis=(tangent*math.cos(s.ivy_leaf_spread)+side*sign*math.sin(s.ivy_leaf_spread)).normalized()
                axis_local=(inv.to_3x3()@axis).normalized()
                normal_local=(ob.matrix_world.to_3x3().transposed()@n).normalized()
                candidates.append((inv@p,axis_local,{'frame':fronds.frame(axis_local,normal_local),'width':s.ivy_leaf_size*.8,'height':s.ivy_leaf_size,'pivot':0.,'segments':s.subdivisions}))
                next_leaf+=step_length
            walked+=segment
    if len(candidates)>s.limit:
        points=[candidates[(i*len(candidates))//s.limit] for i in range(s.limit)]
    else: points=candidates
    s['lp_ivy_paths']=len(curves); s['lp_ivy_stops']=stopped; s['lp_ivy_cards']=len(points)
    return points


def draw(layout,s):
    if s.kind!='Ivy': return
    header,body=layout.panel('LP_Ivy',default_closed=False); header.label(text='Ivy Growth')
    if body:
        for key in ['ivy_start','ivy_direction','length','ivy_step','ivy_radius','ivy_vine_sides','ivy_leaf_spacing','ivy_leaf_size','ivy_leaf_spread','ivy_offset','ivy_probe','ivy_wander','ivy_up_bias','ivy_branches','ivy_branch_spacing','ivy_branch_angle','ivy_branch_length','ivy_max_steps']:
            body.prop(s,key)
        if not s.live_surface:
            body.prop(s,'ivy_gap_bridge'); body.prop(s,'ivy_corner_limit')
        if s.controller and s.controller.type=='CURVE' and s.target and s.target.type=='MESH':
            body.prop(s,'ivy_projection')
            if s.ivy_projection=='CUSTOM': body.prop(s,'ivy_ray_direction')
            body.label(text='Projection mode change needs Regenerate.' if s.live_surface else 'Ray misses split the vine.',icon='INFO')
        body.label(text='Mesh live: seed vine and side guides project to the surface.' if s.live_surface and s.controller and s.controller.type=='MESH' else
                   'Mesh: seeded growth. Curve + Target mesh: live surface snap.' if s.live_surface and s.controller and s.controller.type=='CURVE' and s.target else
                   'Mesh: seeded surface growth. Curve: follow each spline.')
        body.label(text='Density = leaves/m; spacing sets the minimum interval.')
