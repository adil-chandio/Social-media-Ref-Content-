#!/usr/bin/env python3
"""Remove a light checkerboard from a supplied black-silhouette PNG and make alpha.
The input silhouette itself is kept solid black; only the pale background is converted
into transparency. Usage: python tools/make_silhouette.py INPUT.png OUTPUT.png
"""
import argparse
from pathlib import Path
from PIL import Image, ImageOps

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');args=ap.parse_args()
    src=Image.open(args.source).convert('RGB')
    gray=ImageOps.grayscale(src)
    # The supplied checkerboard is light (>=~229 luma); all silhouette pixels are black.
    # A linear matte softly antialiases the silhouette edge without leaving checker squares.
    lut=[255 if v<=8 else 0 if v>=224 else round(255*(224-v)/(224-8)) for v in range(256)]
    alpha=gray.point(lut)
    # Tight crop plus a small transparent safety margin for clean scaling in the edit.
    box=alpha.point([255 if v>18 else 0 for v in range(256)]).getbbox()
    if not box: raise ValueError('No dark silhouette found in input')
    l,t,r,b=box; pad=16
    box=(max(0,l-pad),max(0,t-pad),min(src.width,r+pad),min(src.height,b+pad))
    rgba=Image.new('RGBA',src.size,(0,0,0,0));rgba.putalpha(alpha)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    rgba.crop(box).save(args.output)
    print(f'Saved transparent silhouette: {args.output} ({box[2]-box[0]}x{box[3]-box[1]})')
if __name__=='__main__':main()
