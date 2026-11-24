"""표준노드링크 차로 수를 data.js 의 OSM 도로(H)에 매칭해 h[5]=[정방향, 역방향] 차로 수로 기록.
Match per-direction lane counts from the node-link extract onto OSM roads in data.js.

Usage: python tools/match_lanes.py   (작업 폴더에 data.js, nodelink_cheongdang_lanes.json 필요)
"""
import json,re,math,statistics as st
src=open('data.js',encoding='utf-8').read()
H=json.loads(re.search(r'const H=(\[.*?\]);\n',src,re.S).group(1))
NL=json.load(open('nodelink_cheongdang_lanes.json',encoding='utf-8'))
links=[]
for lid,f,t,lanes,rank,name,spd,conn,p in NL:
    pts=[(p[i],p[i+1]) for i in range(0,len(p),2)]
    links.append((lanes,name,pts,spd))
def nearest(x,z,ux,uz,same):
    best=None;bd=13
    for lanes,name,pts,spd in links:
        for (ax,az),(bx,bz) in zip(pts,pts[1:]):
            vx,vz=bx-ax,bz-az;L=math.hypot(vx,vz)
            if L<0.1: continue
            t=max(0,min(1,((x-ax)*vx+(z-az)*vz)/L/L));d=math.hypot(ax+vx*t-x,az+vz*t-z)
            if d>=bd: continue
            c=(vx*ux+vz*uz)/L
            if (same and c>0.85) or (not same and c<-0.85): bd=d;best=(lanes,spd,name)
    return best
ONE={'trunk','trunk_link','primary'}
res=[]
for h in H:
    del h[5:]
    t,flag,lanes,name,f=h
    pts=[(f[i],f[i+1]) for i in range(0,len(f),2)]
    F=[];Bk=[];S=[]
    for (ax,az),(bx,bz) in zip(pts,pts[1:]):
        L=math.hypot(bx-ax,bz-az)
        if L<1: continue
        ux,uz=(bx-ax)/L,(bz-az)/L;n=max(1,int(L//12))
        for k in range(n):
            x=ax+(bx-ax)*(k+.5)/n;z=az+(bz-az)*(k+.5)/n
            a=nearest(x,z,ux,uz,True);b=nearest(x,z,ux,uz,False)
            if a:F.append(a[0]);S.append(a[1])
            if b:Bk.append(b[0])
    lf=round(st.median(F)) if len(F)>=1 else 0
    lb=round(st.median(Bk)) if len(Bk)>=1 and t not in ONE else 0
    if t not in ONE and lf and not lb: lb=lf
    if t not in ONE and lb and not lf: lf=lb
    res.append([lf,lb,len(F)+len(Bk)])
    h.append([lf,lb])
matched=sum(1 for r in res if r[0]);print('ways',len(H),'matched',matched)
for h,r in zip(H,res):
    if h[3] and r[0]: pass
import collections
c=collections.Counter((h[3] or '#'+h[0],tuple(h[5])) for h in H)
for k,v in sorted(c.items()): print(k,v)
out=re.sub(r'const H=\[.*?\];\n','const H='+json.dumps(H,ensure_ascii=False,separators=(',',':'))+';\n',src,flags=re.S)
open('data.js','w',encoding='utf-8').write(out)
