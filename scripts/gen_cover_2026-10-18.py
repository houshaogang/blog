import urllib.request, urllib.parse, os, io

PROMPT = "melancholic nostalgic scene, person sitting alone by window at dusk looking at old photographs and an old mobile phone, warm golden lamp light fading into blue twilight, watercolor painting style, soft edges, contemplative mood, cinematic composition, no text, no watermark, 8k"
OUT_RAW = "D:/blog/content/posts/cover_2026-10-18-xie-xie_raw.png"
OUT = "D:/blog/content/posts/cover_2026-10-18-xie-xie.png"

url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(PROMPT) + "?width=900&height=383&nologo=true&seed=418"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
data = urllib.request.urlopen(req, timeout=180).read()
with open(OUT_RAW, "wb") as f:
    f.write(data)
print("raw bytes:", len(data), "header:", data[:4].hex())

from PIL import Image
img = Image.open(io.BytesIO(data)).convert("RGB")
print("raw size:", img.size)
if img.size != (900, 383):
    img = img.resize((900, 383), Image.LANCZOS)
img.save(OUT, "PNG")
sz = os.path.getsize(OUT)
with open(OUT, "rb") as f:
    hdr = f.read(4).hex()
print("real png bytes:", sz, "header:", hdr)
assert hdr == "89504e47", "not a real PNG"
assert sz > 200000, "png too small: %d" % sz
print("COVER_OK", OUT)
