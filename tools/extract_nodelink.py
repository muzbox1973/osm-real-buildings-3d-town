"""국토교통부 ITS 전국표준노드링크(MOCT_LINK)에서 지정 범위의 링크만 잘라 JSON으로 저장.

Extract the links inside a lat/lon bounding box from the Korean national standard
node-link dataset (ITS, MOCT_LINK shapefile) and save them as compact JSON.

사용법 / Usage
  1) https://www.its.go.kr/nodelink/nodelinkRef 에서 NODELINKDATA.zip 을 받는다.
  2) unzip NODELINKDATA.zip MOCT_LINK.*
  3) pip install pyshp pyproj
  4) python extract_nodelink.py MOCT_LINK 36.7745 127.1430 36.7865 127.1660 36.7805 127.1545 out.json

출력 형식 / Output: [[LINK_ID, F_NODE, T_NODE, LANES, ROAD_RANK, ROAD_NAME, MAX_SPD, CONNECT, [x,z,...]], ...]
x = 동쪽(m), z = 남쪽(m), 기준점(lat0, lon0) 기준. LANES 는 링크 진행 방향의 차로 수.
"""
import json
import math
import sys

import pyproj
import shapefile

# MOCT_LINK.prj: ITRF2000 Central Belt 60 (GRS80, lat0 38, lon0 127, FE 200000, FN 600000)
TM = "+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m"


def main():
    if len(sys.argv) != 9:
        print(__doc__)
        sys.exit(1)
    shp, s, w, n, e, lat0, lon0, out = sys.argv[1:]
    s, w, n, e, lat0, lon0 = map(float, (s, w, n, e, lat0, lon0))
    to_ll = pyproj.Transformer.from_crs(TM, "EPSG:4326", always_xy=True)
    to_tm = pyproj.Transformer.from_crs("EPSG:4326", TM, always_xy=True)
    x0, y0 = to_tm.transform(w, s)
    x1, y1 = to_tm.transform(e, n)
    kx = 111320 * math.cos(math.radians(lat0))
    kz = 110950
    reader = shapefile.Reader(shp, encoding="cp949")
    rows = []
    for sr in reader.iterShapeRecords(bbox=[x0, y0, x1, y1]):
        r = sr.record
        pts = []
        for X, Y in sr.shape.points:
            lon, lat = to_ll.transform(X, Y)
            pts += [round((lon - lon0) * kx, 1), round((lat0 - lat) * kz, 1)]
        rows.append([r["LINK_ID"], r["F_NODE"], r["T_NODE"], r["LANES"], r["ROAD_RANK"],
                     r["ROAD_NAME"], r["MAX_SPD"], r["CONNECT"], pts])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print(f"{len(rows)} links -> {out}")


if __name__ == "__main__":
    main()
