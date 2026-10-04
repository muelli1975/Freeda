"""Rule-of-thirds overlay confined to the actual stereo eye areas."""
from PIL import Image, ImageDraw
from .geometry import frame_geometry_for_total_width, mm_to_px
from .models import LayoutMode, PrintRenderOptions
from .render import crop_eye
from .cropping import fit_linked_crop

def crop_grid(image, source, options):
    from .print_render import _bands
    result = image.convert("RGBA")
    overlay = Image.new("RGBA",result.size)
    draw=ImageDraw.Draw(overlay)
    count=3 if options.layout==LayoutMode.LRL else 2
    rows=2 if options.layout==LayoutMode.BOTH else 1
    if isinstance(options,PrintRenderOptions):
        width=mm_to_px(options.width_mm,options.dpi)
        height=mm_to_px(options.height_mm,options.dpi)
        bleed=mm_to_px(options.bleed_mm,options.dpi)
    else:
        width,height=image.size
        bleed=0
    geom=frame_geometry_for_total_width(width,options.frame_percent,count)
    frame,eye_w=geom.frame_px,geom.eye_width
    if isinstance(options,PrintRenderOptions):
        first_h=height if rows==1 else (height+frame*(2 if options.caption else 1))//2
        second_h=height+frame-first_h
        _,_,_,_,symbol_band,caption_band=_bands(eye_w,frame,options.caption,options.font_family,"II",options.caption_size_percent,count)
        heights=[first_h] if rows==1 else [first_h,second_h]
        eye_heights=[h-2*frame-symbol_band-caption_band+(frame if options.caption and index==rows-1 else 0) for index,h in enumerate(heights)]
    else:
        left=source.crop((0,0,source.width//2,source.height))
        crop=fit_linked_crop(left.size,options.crop,options.eye_aspect)
        eye=crop_eye(left,crop)
        eye_h=max(1,round(eye_w*eye.height/eye.width))
        row_h=(height+frame*(rows-1)+(frame if options.caption else 0))//rows
        heights=[row_h]*rows
        eye_heights=[eye_h]*rows
    y=bleed+frame
    for row_h,eye_h in zip(heights,eye_heights):
        for index in range(count):
            x=bleed+frame+index*(eye_w+frame)
            for fraction in (1/3,2/3):
                vx=round(x+eye_w*fraction)
                hy=round(y+eye_h*fraction)
                for points in ((vx,y,vx,y+eye_h-1),(x,hy,x+eye_w-1,hy)):
                    draw.line(points,fill=(0,0,0,130),width=3)
                    draw.line(points,fill=(255,255,255,200),width=1)
        y+=row_h-frame
    return Image.alpha_composite(result,overlay)
