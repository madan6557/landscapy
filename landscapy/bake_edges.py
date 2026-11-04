"""Fill transparent RGB around an RGBA bake while preserving exact alpha."""
import numpy as np


def dilate_rgba(pixels, radius=8):
    result=np.asarray(pixels,dtype=np.float32).copy()
    known=result[:,:,3]>.01
    for _ in range(radius):
        if known.all(): break
        added=np.zeros_like(known)
        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            y0=max(0,dy); y1=result.shape[0]+min(0,dy)
            x0=max(0,dx); x1=result.shape[1]+min(0,dx)
            ty=slice(y0,y1); tx=slice(x0,x1)
            sy=slice(y0-dy,y1-dy); sx=slice(x0-dx,x1-dx)
            fill=(~known[ty,tx]) & (~added[ty,tx]) & known[sy,sx]
            if not fill.any(): continue
            result[ty,tx,:3][fill]=result[sy,sx,:3][fill]
            added[ty,tx][fill]=True
        if not added.any(): break
        known |= added
    return result


def save_dilated(image,path,radius=8):
    values=np.empty(len(image.pixels),dtype=np.float32)
    image.pixels.foreach_get(values)
    h,w=image.size[1],image.size[0]
    result=dilate_rgba(values.reshape(h,w,4),radius)
    image.pixels.foreach_set(result.reshape(-1))
    image.update()
    image.filepath_raw=str(path)
    image.file_format='PNG'
    image.save()
    image.pack()
    return image
