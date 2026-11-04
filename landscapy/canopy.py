"""Bounded, overlapping canopy lobes with area-balanced shell coverage.

Samples are deterministic and independent of appearance seeds. The hard instance
limit is applied across the entire crown, never by cutting off later branches.
"""
import math
import random
import numpy as np
from mathutils import Vector, Matrix

def area(r):
    p=1.6075
    return 4*math.pi*((r.x**p*r.y**p+r.x**p*r.z**p+r.y**p*r.z**p)/3)**(1/p)

def inside(point,center,radii,margin=1.):
    return sum(((point[i]-center[i])/radii[i])**2 for i in range(3)) < margin*margin


def _visible_fraction(slot,opacity,alpha_mode):
    """Measure the active atlas region so transparent space is not counted as leaf."""
    if slot.material_override: return .55
    u0,v0,u1,v1=slot.uv_region
    u=np.linspace(u0,u1,32,endpoint=False,dtype=np.float32)+(u1-u0)/64
    v=np.linspace(v0,v1,32,endpoint=False,dtype=np.float32)+(v1-v0)/64
    def sample_image(image,channel):
        if not image or min(image.size)<1: return np.ones((32,32),dtype=np.float32)
        width,height=image.size[:]
        values=np.empty(len(image.pixels),dtype=np.float32)
        image.pixels.foreach_get(values)
        pixels=values.reshape(height,width,image.channels)
        xs=np.clip((u*width).astype(np.int32),0,width-1)
        ys=np.clip((v*height).astype(np.int32),0,height-1)
        if channel=='alpha': return pixels[ys[:,None],xs[None,:],3] if slot.use_alpha and image.channels>=4 else np.ones((32,32),dtype=np.float32)
        return pixels[ys[:,None],xs[None,:],:min(3,image.channels)].mean(axis=2)
    alpha=sample_image(slot.image,'alpha')*sample_image(slot.opacity_image,'color')
    alpha*=slot.opacity*opacity
    threshold=.45 if alpha_mode=='Cutout' else .35
    return max(.02,float(np.mean(alpha>threshold)))


class CoverageGrid:
    """Nine low-resolution views guide candidates toward uncovered crown cells."""
    def __init__(self,centers,radii,footprint,resolution=40):
        self.resolution=resolution
        self.views=[]
        for index in range(9):
            if index<8:
                angle=index*math.tau/8; c=math.cos(angle); s=math.sin(angle)
                projected=[(p.x*c+p.y*s,p.z) for p in centers]
                reach=[(math.hypot(r.x*c,r.y*s),r.z) for r in radii]
                axis=(c,s)
            else:
                projected=[(p.x,p.y) for p in centers]
                reach=[(r.x,r.y) for r in radii]
                axis=None
            low=[min(point[j]-size[j] for point,size in zip(projected,reach)) for j in range(2)]
            high=[max(point[j]+size[j] for point,size in zip(projected,reach)) for j in range(2)]
            span=max(high[0]-low[0],high[1]-low[1],.001)*1.12
            origin=((low[0]+high[0]-span)*.5,(low[1]+high[1]-span)*.5)
            radius=max(1,min(4,round(math.sqrt(max(footprint,1e-5)/math.pi)*resolution/span)))
            self.views.append((axis,origin,span,radius,np.zeros((resolution,resolution),dtype=np.uint16)))

    def cells(self,point):
        for axis,origin,span,radius,grid in self.views:
            projected=(point.x*axis[0]+point.y*axis[1],point.z) if axis else (point.x,point.y)
            x=round((projected[0]-origin[0])*self.resolution/span)
            y=round((projected[1]-origin[1])*self.resolution/span)
            x0=max(0,x-radius); x1=min(self.resolution,x+radius+1)
            y0=max(0,y-radius); y1=min(self.resolution,y+radius+1)
            yield grid[y0:y1,x0:x1]

    def gain(self,point):
        return sum(float(np.mean(1/(1+cell))) for cell in self.cells(point) if cell.size)

    def add(self,point):
        for cell in self.cells(point): cell+=1

    def filled(self):
        return [int(np.count_nonzero(view[-1])) for view in self.views]

def sample(settings,lobes,include_branch=False):
    settings['lp_coverage_requested']=0; settings['lp_coverage_emitted']=0
    settings['lp_coverage_grid_filled']=[0]*9
    if not lobes or settings.density<=0 or settings.canopy_coverage<=0: return []
    radii=[Vector(item[1]) for item in lobes]; centers=[Vector(item[0]) for item in lobes]
    weights=[area(r)*(2.5 if len(lobe)>5 and lobe[5]=='FILL' else 1.)
             for lobe,r in zip(lobes,radii)]
    slots=[t for t in settings.textures if (t.image or t.material_override) and t.weight>0]
    mean_size=(settings.size_min+settings.size_max)*.5*.45
    footprint=mean_size**2 * settings.scale_axes[0]*settings.scale_axes[2]
    opacity=(settings.opacity_min+settings.opacity_max)*.5
    if slots:
        footprint*=sum(t.weight*t.size*t.size*t.aspect*_visible_fraction(t,opacity,settings.alpha_mode) for t in slots)/sum(t.weight for t in slots)
    else: footprint*=.35
    footprint=max(.0001,footprint)
    requested=max(1,math.ceil(sum(weights)*settings.canopy_coverage*(settings.density/30)/footprint))
    settings['lp_coverage_requested']=requested
    target=min(settings.limit,requested)
    rng=random.Random(settings.seed+982451653)
    phases=[rng.random()*math.tau for _ in lobes]
    counts=[0]*len(lobes); accepted=[0]*len(lobes); credits=[0.]*len(lobes); total=sum(weights)
    grid=CoverageGrid(centers,radii,footprint)
    result=[]; max_attempts=target*14
    for attempt in range(max_attempts):
        # Smooth weighted round-robin: every cluster receives samples even when
        # the instance cap is low. This also preserves prefixes when density grows.
        for i,w in enumerate(weights): credits[i]+=w/total
        index=max(range(len(lobes)),key=lambda j:credits[j]); credits[index]-=1
        fill_lobe=len(lobes[index])>5 and lobes[index][5]=='FILL'
        shell=not fill_lobe and (accepted[index]*.5698402909980532)%1 < settings.canopy_shell
        best=None
        for _ in range(1 if fill_lobe else settings.canopy_candidates):
            k=counts[index]; counts[index]+=1
            # Each option belongs to the same shell/interior stratum. Choosing
            # the least-covered option does not change the seed or point budget.
            z=1-2*((k*.7548776662466927+.5)%1)
            phi=phases[index]+k*2.399963229728653
            radial=math.sqrt(max(0,1-z*z)); direction=Vector((radial*math.cos(phi),radial*math.sin(phi),z))
            radius=.89+.11*rng.random() if shell else .82*(rng.random()**(1/3))
            point=centers[index]+Vector([direction[j]*radii[index][j]*radius for j in range(3)])
            if shell and any(j!=index and inside(point,c,r,.86) for j,(c,r) in enumerate(zip(centers,radii))): continue
            score=grid.gain(point)
            if best is None or score>best[0]: best=(score,point,direction)
        if best is None: continue
        _,point,direction=best
        heading=math.atan2(direction.y,direction.x)+math.pi/2
        result.append((point,Vector((0,0,1)),heading,*lobes[index][2:5]) if include_branch else (point,Vector((0,0,1)),heading))
        grid.add(point); accepted[index]+=1
        if len(result)>=target: break
    settings['lp_coverage_emitted']=len(result)
    settings['lp_coverage_grid_filled']=grid.filled()
    return result


def _upright_card_frame(normal):
    """Return a vertical card frame facing a horizontal direction."""
    z=Vector((0,0,1))
    normal=Vector((normal.x,normal.y,0)).normalized()
    x=normal.cross(z).normalized()
    y=z.cross(x).normalized()
    return Matrix((x,y,z)).transposed()


def tree_cluster_cards(settings,lobes,planes=3):
    """Make branch-led canopy masses from editable, crossed textured quads.

    Tree foliage has a different job from a bush scatter: each branch lobe is
    treated as a large crown mass first. Density adds a few offset masses to
    that structure, while the image alpha defines their final leaf silhouette.
    The same broad lobe centers are preserved when density or the card budget
    changes so generation remains stable and wind anchors remain meaningful.
    """
    settings['lp_coverage_requested']=0
    settings['lp_coverage_emitted']=0
    settings['lp_coverage_grid_filled']=[0]*9
    if not lobes or settings.density<=0 or settings.canopy_coverage<=0:
        return []

    source=[]
    for index,lobe in enumerate(lobes):
        center=Vector(lobe[0]); radii=Vector(lobe[1])
        if min(radii)<=0: continue
        branch_id=lobe[2] if len(lobe)>2 else -1
        branch_t=lobe[3] if len(lobe)>3 else .5
        branch_level=lobe[4] if len(lobe)>4 else -1
        source.append((index,center,radii,branch_id,branch_t,branch_level))
    if not source: return []

    # Density is expressed in broad crown groups per branch lobe, not in
    # individual leaflets. Sparse values remove complete groups evenly;
    # higher values add a small number of offset groups without speckling.
    density=max(0.,settings.density/30.)
    copies=min(4,int(density))
    fraction=density-copies
    if density<1:
        wanted=max(1,round(len(source)*density)) if density>0 else 0
        selected=[source[(i*len(source))//wanted] for i in range(wanted)] if wanted else []
        copy_counts={item[0]:1 for item in selected}
    else:
        selected=source
        copy_counts={}
        for item in selected:
            index=item[0]
            rng=random.Random(settings.seed*1000003+index*9176+7919)
            extra=1 if fraction and rng.random()<fraction else 0
            copy_counts[index]=max(1,min(4,copies+extra))

    expected=sum(copy_counts.get(item[0],0) for item in selected)
    settings['lp_coverage_requested']=expected*max(1,settings.cluster_planes)
    budget=max(1,settings.limit)
    if expected>budget:
        selected=[selected[(i*len(selected))//budget] for i in range(budget)]

    plane_count=max(1,min(int(planes),settings.limit//max(1,len(selected))))
    result=[]; centers=[]; bounds=[]
    coverage_scale=max(.05,min(2.5,settings.canopy_coverage))
    for item in selected:
        index,center,radii,branch_id,branch_t,branch_level=item
        copies_for_lobe=copy_counts.get(index,1)
        rng=random.Random(settings.seed*1000003+index*9176+7919)
        phase=rng.uniform(-.18,.18)
        for copy_index in range(copies_for_lobe):
            if len(result)+plane_count>settings.limit: break
            # The first canopy mass sits on the branch lobe. Additional masses
            # overlap it asymmetrically to fill the outer contour and hide gaps.
            if copy_index==0:
                offset=Vector((0,0,0)); scale=1.
            else:
                angle=phase+copy_index*2.399963229728653
                spread=.14+.055*copy_index
                offset=Vector((math.cos(angle)*radii.x*spread,
                               math.sin(angle)*radii.y*spread,
                               rng.uniform(-.10,.10)*radii.z))
                scale=max(.48,.76-.10*(copy_index-1))*rng.uniform(.94,1.06)
            group_center=center+offset
            group_scale=coverage_scale*scale*rng.uniform(.96,1.04)
            for plane in range(plane_count):
                angle=phase+math.pi*plane/max(1,plane_count)+rng.uniform(-.055,.055)
                normal=Vector((math.cos(angle),math.sin(angle),0))
                width=2*math.sqrt((radii.x*math.sin(angle))**2+
                                  (radii.y*math.cos(angle))**2)
                height=2*radii.z
                # A small amount of plane-to-plane scale variation keeps the
                # card group from reading as a perfect sphere while preserving
                # a broad, continuous outer silhouette.
                plane_scale=group_scale*rng.uniform(.93,1.07)
                result.append((group_center,Vector((0,0,1)),{
                    'frame':_upright_card_frame(normal),
                    'width':width*plane_scale*1.08,
                    'height':height*plane_scale*1.06,
                    'pivot':.5,'segments':1,'force_quad':True,
                    'branch_id':branch_id,'branch_level':branch_level,
                    'branch_t':branch_t,
                }))
            centers.append(group_center); bounds.append(radii*group_scale)

    settings['lp_coverage_emitted']=len(result)
    if centers:
        average_area=sum((r.x*r.y+r.x*r.z+r.y*r.z)/3 for r in bounds)/len(bounds)
        grid=CoverageGrid(centers,bounds,max(.0001,average_area*.5))
        for center in centers: grid.add(center)
        settings['lp_coverage_grid_filled']=grid.filled()
    return result


def willow_sprays(settings, guides):
    """Hang curved image cards along the branch arches of a weeping crown."""
    from .fronds import frame

    primary = [guide for guide in guides if guide[3]==1]
    secondary = [guide for guide in guides if guide[3]>1]
    count = settings.cluster_planes
    requested = round((len(primary)*count+len(secondary))*settings.density/30)
    budget = min(settings.limit, requested)
    result = []
    if settings.canopy_coverage>0 and budget>0:
        # Cover the different azimuths first. Fill remaining stations only
        # after each main limb has one continuous hanging spray.
        candidates = [(guide,.77,0) for guide in primary]
        if count>1:
            candidates.extend((guide,.96,1) for guide in primary)
        candidates.extend((guide,.88,0) for guide in secondary)
        for row in range(2,count):
            station = .49+.43*((row*.61803399)%1)
            candidates.extend((guide,station,row) for guide in primary)
        if budget>len(candidates):
            candidates.extend((guide,.60,count) for guide in primary)
            candidates.extend((guide,.58,0) for guide in secondary)
        if budget<len(primary):
            candidates = [candidates[index*len(primary)//budget] for index in range(budget)]

        for (line, angle, reach, level, branch_id), station, row in candidates[:budget]:
            rng = random.Random(settings.seed*1009+branch_id*9176+row*103+int(station*1000))
            shoulder = level==1 and line[0].z>settings.height*.82 and row==0
            if shoulder: station-=.25
            station = min(.99,station+rng.uniform(-.045,.045))
            index = station*(len(line)-1)
            left = min(int(index),len(line)-2)
            origin = line[left].lerp(line[left+1],index-left)
            heading = angle+rng.uniform(-.58,.58)
            radial = Vector((math.cos(heading),math.sin(heading),0))
            side = Vector((-radial.y,radial.x,0))
            down = Vector((0,0,-1))
            height = reach*(.48+1.35*max(0,settings.droop))*rng.uniform(.80,1.13)
            if shoulder: height*=.76
            if origin.z>0:
                height = min(height,max(.08,origin.z-.16))
            width = settings.cluster_radius*settings.canopy_coverage*rng.uniform(1.65,2.12)
            if level>1: width*=.69
            sweep = rng.uniform(.25,.43) if not shoulder else rng.uniform(.52,.68)
            drift = rng.uniform(-.20,.20)
            spine = [height*(down*(.35*t+.65*t*t)+radial*sweep*t*(2-t)+side*drift*t*t)
                     for t in (0,.25,.50,.75,1)]
            result.append((origin,down,{
                'frame':frame(down,radial),'width':width,'height':height,'pivot':0.,
                'segments':2,'spine':spine,'root_uv_top':True,'force_quad':True,
                'branch_id':branch_id,'branch_t':station,'branch_level':level,
            }))
    settings['lp_coverage_requested']=requested
    settings['lp_coverage_emitted']=len(result)
    settings['lp_coverage_grid_filled']=[0]*9
    return result
