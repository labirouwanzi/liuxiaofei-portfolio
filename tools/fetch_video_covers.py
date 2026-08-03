# -*- coding: utf-8 -*-
"""抓取小红书视频原封面,保存到 images/video-N.jpg"""
import urllib.request
import re
import os
from PIL import Image

links = [
    ('6a445520000000001603f7dd', 'ABT1TC-OiF_eLzLDlGCRicSSY8GTTI62JccCCP4N4n37w='),
    ('6a57647f000000001102f078', 'ABHso199fn7fAp2bGoTtw1GsBYhof5Uj5QdCFRX1fqV1s='),
    ('6a3d2fdb000000001101dc43', 'ABdB5g0tjgOlsATWTAQ9i8J-plmLgRnJHvGnDNU35TY08='),
    ('6a648b47000000000f01188c', 'ABLl4h9USBPfExJrxZe1oDiCeD96fcXnul0brA1RwQWqk='),
]
HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Referer': 'https://www.xiaohongshu.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=25).read()

for i, (nid, tok) in enumerate(links, start=1):
    url = ('https://www.xiaohongshu.com/discovery/item/%s'
           '?source=webshare&xhsshare=pc_web&xsec_token=%s&xsec_source=pc_share') % (nid, tok)
    try:
        html = fetch(url).decode('utf-8', 'ignore')
        # 笔记封面在 sns-webpic-qc 域名下(og:image 是 logo,忽略)
        imgs = re.findall(r'https?://sns-webpic-qc\.xhscdn\.com/[^"\\ ]+', html)
        imgs += ['https:' + u for u in re.findall(r'//sns-webpic-qc\.xhscdn\.com/[^"\\ ]+', html)]
        # 去重,优先带 spectrum 路径的
        seen, cand = set(), None
        for u in imgs:
            if u in seen:
                continue
            seen.add(u)
            if 'spectrum' in u:
                cand = u
                break
        if cand is None and seen:
            cand = next(iter(seen))
        print('[视频%d] %s' % (i, ('封面URL: ' + cand[:70]) if cand else '无图'))
        if not cand:
            print('    无封面,跳过')
            continue
        raw = fetch(cand)
        dest = 'images/video-%d.jpg' % i
        with open(dest, 'wb') as f:
            f.write(raw)
        im = Image.open(dest)
        print('    已保存 %s  %s  宽高比 %.3f  %dKB'
              % (dest, im.size, im.size[0] / im.size[1], len(raw) // 1024))
    except Exception as e:
        print('[视频%d] 失败: %s %s' % (i, type(e).__name__, str(e)[:90]))
