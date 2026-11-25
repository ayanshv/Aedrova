import sys; sys.path.insert(0,'/tmp/claude-501/pylib')
import cv2, numpy as np, statistics
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.ttGlyphPen import TTGlyphPen
exec(open('seg.py').read().split("import json")[0].replace("print(","(lambda *a:None)("))
base=TTFont('/tmp/claude-501/jk/PlusJakartaSans.ttf')
font=instancer.instantiateVariableFont(base,{"wght":600})
os2=font['OS/2']; upm=font['head'].unitsPerEm
CAP=os2.sCapHeight; XH=os2.sxHeight
print("upm",upm,"cap",CAP,"xh",XH,"asc",font['hhea'].ascent,"desc",font['hhea'].descent)
names=["abcdefghijklm","nopqrstuvwxyz","ABCDEFGHIJKLM","NOPQRSTUVWXYZ"]
glyphs=[]
for r,row in enumerate(rows):
    row=sorted(row,key=lambda c:c[1])
    big=[c for c in row if c[5]>=500]; dots=[c for c in row if c[5]<500]
    groups=[[c] for c in big]
    for d in dots:
        dx=d[1]+d[3]/2
        for g in groups:
            if g[0][1]-3<=dx<=g[0][1]+g[0][3]+3: g.append(d)
    glyphs.append(groups)
flat={0:"hilkm",1:"nruzvwx",2:"AEFHILM",3:"NPRTUVXYZ"}
ref={0:"acem",1:"nruvwxz",2:"ACDEHLM",3:"NPRSTUVXYZ"}  # height reference letters
def bbox(g):
    return (min(c[1] for c in g),min(c[2] for c in g),max(c[1]+c[3] for c in g),max(c[2]+c[4] for c in g))
SCALE=SB={}
SC={};BASE={}
for r,groups in enumerate(glyphs):
    d={ch:g for ch,g in zip(names[r],groups)}
    BASE[r]=statistics.median(bbox(d[ch])[3] for ch in flat[r])
    hs=[BASE[r]-bbox(d[ch])[1] for ch in flat[r] if ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or ch in "mnruvwxz"]
    h=statistics.median(hs)
    SC[r]=(CAP if r>=2 else XH)/h
print(SC,BASE)
gray=im.astype(np.float32)
U=4
glyf=font['glyf']; hmtx=font['hmtx']
order=font.getGlyphOrder()
cmap=font.getBestCmap()
def trace(g,r):
    x0,y0,x1,y1=bbox(g); pad=6
    X0,Y0,X1,Y1=x0-pad,y0-pad,x1+pad,y1+pad
    mask=np.zeros(im.shape,np.uint8)
    for c in g: mask[lab==c[0]]=1
    mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
    crop=np.where(mask[Y0:Y1,X0:X1]>0,gray[Y0:Y1,X0:X1],255).astype(np.float32)
    big=cv2.resize(crop,None,fx=U,fy=U,interpolation=cv2.INTER_CUBIC)
    big=cv2.GaussianBlur(big,(0,0),U*0.6)
    bw=(big<150).astype(np.uint8)*255
    cs,h=cv2.findContours(bw,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    return cs,h[0],(X0,Y0)
T,K=88,0.62
def bearings(g,r):
    x0,y0,x1,y1=bbox(g)
    m=np.zeros(im.shape,bool)
    for c in g: m|=(lab==c[0])
    top=BASE[r]-(CAP if r>=2 else XH)/SC[r]
    rows_=range(int(max(y0,top)),int(min(y1,BASE[r])))
    L=[];R=[]
    for y in rows_:
        xs=np.where(m[y,x0:x1])[0]
        if len(xs): L.append(xs[0]); R.append((x1-x0)-1-xs[-1])
    gl=np.mean(L)*SC[r] if L else 0; gr=np.mean(R)*SC[r] if R else 0
    cl=lambda v:max(8,min(95,v))
    return cl(T-K*gl),cl(T-K*gr)
for r,groups in enumerate(glyphs):
    for ch,g in zip(names[r],groups):
        cs,hier,(X0,Y0)=trace(g,r)
        s=SC[r]/U
        pen=TTGlyphPen(None)
        bx0=bbox(g)[0]; SBL,SBR=bearings(g,r); left=SBL-(bx0-X0)*SC[r]
        for c,hh in zip(cs,hier):
            if len(c)<8: continue
            a=cv2.approxPolyDP(c,1.0,True)[:,0,:].astype(float)
            pts=[(round(left+x*s),round((BASE[r]-(Y0+y/U))*SC[r])) for x,y in a]
            area=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))/2
            outer = hh[3]==-1
            if outer==(area>0): pts=pts[::-1]   # outer clockwise (area<0), holes counter-clockwise
            pen.moveTo(pts[0])
            for p in pts[1:]: pen.lineTo(p)
            pen.closePath()
        gn=cmap[ord(ch)]
        glyf[gn]=pen.glyph()
        w=round((bbox(g)[2]-bx0)*SC[r]+SBL+SBR)
        hmtx[gn]=(w,round(SBL))
for t in ("GPOS","GSUB","kern","GDEF","STAT","HVAR","MVAR"):
    if t in font: del font[t]
# rename
fam="Aedrova Title"
for rec in font['name'].names:
    if rec.nameID in (1,16): rec.string=fam
    elif rec.nameID in (2,17): rec.string="SemiBold"
    elif rec.nameID==4: rec.string=fam
    elif rec.nameID==6: rec.string="AedrovaTitle"
    elif rec.nameID==3: rec.string="AedrovaTitle-1.0"
font['OS/2'].usWeightClass=600
font.save('AedrovaTitle.ttf')
print("saved")
