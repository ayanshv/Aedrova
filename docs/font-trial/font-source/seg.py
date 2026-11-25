import cv2, numpy as np
from PIL import Image
im=np.array(Image.open('/private/tmp/claude-501/-Users-ayanshvarma-Documents-Aedrova/f1c128ef-c970-4214-ba6b-09897c676572/images/21.webp').convert('L'))
ink=(im<140).astype(np.uint8)
n,lab,st,cen=cv2.connectedComponentsWithStats(ink,8)
comps=[(i,)+tuple(st[i]) for i in range(1,n) if st[i][4]>30]
print(len(comps))
# rows by y center
rows=[[],[],[],[]]
bounds=[(0,200),(200,380),(380,530),(530,667)]
for c in comps:
    cy=c[2]+c[4]/2
    for r,(a,b) in enumerate(bounds):
        if a<=cy<b: rows[r].append(c)
for r in rows: print(len(r), sorted(c[2]+c[4]//2 for c in r)[:3])

import json
glyphs=[]
for r,row in enumerate(rows):
    row=sorted(row,key=lambda c:c[1])
    merged=[]
    for c in row:
        if r==0 and c[5]<400 and merged==[] or False: pass
        merged.append(c)
    # merge small dot components (area<600) into overlapping-x neighbor
    big=[c for c in merged if c[5]>=500]
    dots=[c for c in merged if c[5]<500]
    groups=[[c] for c in big]
    for d in dots:
        dx=d[1]+d[3]/2
        for g in groups:
            c=g[0]
            if c[1]-3<=dx<=c[1]+c[3]+3: g.append(d)
    glyphs.append(groups)
    print(r,len(groups),[len(g) for g in groups if len(g)>1])
names=["abcdefghijklm","nopqrstuvwxyz","ABCDEFGHIJKLM","NOPQRSTUVWXYZ"]
# row 1 has 13 groups? row2 13? print metrics
for r,groups in enumerate(glyphs):
    for ch,g in zip(names[r] if r!=1 else names[1],groups):
        x0=min(c[1] for c in g); x1=max(c[1]+c[3] for c in g)
        y0=min(c[2] for c in g); y1=max(c[2]+c[4] for c in g)
        print(ch,x0,y0,x1,y1,"h",y1-y0,"w",x1-x0)
