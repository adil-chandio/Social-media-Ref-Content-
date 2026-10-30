#!/usr/bin/env python3
"""Create the pure-black, transparent portrait silhouette for Adil's intro.
The closed Bezier outline is hand-traced from assets/adil-portrait.jpg, then rendered
at 4x and antialiased. No facial, clothing, or background pixels survive in the cutout.
"""
from pathlib import Path
from PIL import Image, ImageDraw

S=4
mask=Image.new('L',(512*S,512*S),0)
d=ImageDraw.Draw(mask)
def pt(p): return (round(p[0]*S),round(p[1]*S))
def cubic(p0,p1,p2,p3,n=24):
    pts=[]
    for i in range(1,n+1):
        t=i/n; u=1-t
        x=u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0]
        y=u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]
        pts.append((x,y))
    return pts

# Smooth silhouette contour: crown, hair, face/neck, shoulders, jacket and arms.
segments=[
 ((195,119),(186,101),(187,77),(194,60)),
 ((194,60),(199,47),(212,38),(223,34)),
 ((223,34),(235,24),(248,23),(260,30)),
 ((260,30),(265,33),(270,27),(278,26)),
 ((278,26),(295,23),(311,38),(319,51)),
 ((319,51),(328,66),(331,84),(327,102)),
 ((327,102),(330,121),(326,140),(323,155)),
 ((323,155),(319,177),(313,190),(329,200)),
 ((329,200),(343,208),(361,210),(378,217)),
 ((378,217),(399,223),(410,244),(416,269)),
 ((416,269),(425,301),(431,342),(434,366)),
 ((434,366),(436,382),(430,392),(423,402)),
 ((423,402),(426,415),(418,427),(399,434)),
 ((399,434),(391,438),(388,445),(388,457)),
 ((388,457),(386,479),(378,497),(371,512)),
 ((371,512),(315,514),(207,514),(151,512)),
 ((151,512),(144,493),(141,472),(136,455)),
 ((136,455),(131,443),(117,437),(103,429)),
 ((103,429),(86,420),(78,409),(79,393)),
 ((79,393),(78,369),(82,342),(89,316)),
 ((89,316),(97,285),(105,259),(111,241)),
 ((111,241),(117,225),(130,219),(148,214)),
 ((148,214),(168,209),(184,201),(194,190)),
 ((194,190),(203,179),(203,164),(199,148)),
 ((199,148),(195,137),(193,126),(195,119)),
]
points=[segments[0][0]]
for seg in segments: points.extend(cubic(*seg))
d.polygon([pt(p) for p in points],fill=255)
mask=mask.resize((512,512),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(512,512),(0,0,0,0));out.putalpha(mask)
out.save(Path(__file__).resolve().parents[1]/'assets'/'adil-silhouette.png')
