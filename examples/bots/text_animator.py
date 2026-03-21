import os, sys, random, subprocess, time, json
import urllib.request
from PIL import Image, ImageDraw, ImageFont

API_KEY = "bottube_sk_dc1a24fb97664272f3fd0b0cf454098be5a9d34247fdaf01"
OUTPUT_DIR = "/tmp/text_animator/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONTS = [
    "Oswald-Bold.ttf",
    "Lora-Bold.ttf",
    "PTSans-Bold.ttf"
]

FALLBACK_QUOTES = [
    {"q": "Talk is cheap. Show me the code.", "a": "Linus Torvalds"},
    {"q": "Programs must be written for people to read.", "a": "Harold Abelson"},
    {"q": "Truth can only be found in one place: the code.", "a": "Robert C. Martin"},
    {"q": "Any fool can write code that a computer can understand.", "a": "Martin Fowler"},
    {"q": "First, solve the problem. Then, write the code.", "a": "John Johnson"},
    {"q": "Experience is the name everyone gives to their mistakes.", "a": "Oscar Wilde"},
    {"q": "In order to be irreplaceable, one must always be different.", "a": "Coco Chanel"},
    {"q": "Java is to JavaScript what car is to Carpet.", "a": "Chris Heilmann"},
    {"q": "Ruby is rubbish! PHP is phpantastic.", "a": "Nikita Popov"},
    {"q": "Code is like humor. When you have to explain it, it’s bad.", "a": "Cory House"},
    {"q": "Fix the cause, not the symptom.", "a": "Steve Maguire"},
    {"q": "Optimism is an occupational hazard of programming.", "a": "Kent Beck"},
    {"q": "Simplicity is the soul of efficiency.", "a": "Austin Freeman"},
    {"q": "Before software can be reusable it first has to be usable.", "a": "Ralph Johnson"},
    {"q": "Make it work, make it right, make it fast.", "a": "Kent Beck"},
    {"q": "It’s not a bug. It’s an undocumented feature!", "a": "Anonymous"},
    {"q": "Software is a great combination between artistry and engineering.", "a": "Bill Gates"},
    {"q": "The best way to get a project done faster is to start sooner.", "a": "Jim Highsmith"},
    {"q": "There is no Ctrl-Z in life.", "a": "Anonymous"},
    {"q": "The only way to learn a new programming language is by writing programs in it.", "a": "Dennis Ritchie"},
    {"q": "Sometimes it pays to stay in bed on Monday.", "a": "Dan Salomon"},
    {"q": "Programming isn't about what you know; it's about what you can figure out.", "a": "Chris Pine"},
    {"q": "Testing leads to failure, and failure leads to understanding.", "a": "Burt Rutan"},
    {"q": "The function of good software is to make the complex appear to be simple.", "a": "Grady Booch"},
    {"q": "Your most unhappy customers are your greatest source of learning.", "a": "Bill Gates"},
    {"q": "Quality is a product of a conflict between programmers and testers.", "a": "Yegor Bugayenko"},
    {"q": "Everybody in this country should learn to program a computer.", "a": "Steve Jobs"},
    {"q": "A good programmer is someone who always looks both ways before crossing a one-way street.", "a": "Doug Linder"},
    {"q": "Don’t comment bad code - rewrite it.", "a": "Brian Kernighan"},
    {"q": "I'm not a great programmer; I'm just a good programmer with great habits.", "a": "Kent Beck"},
    {"q": "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.", "a": "Antoine de Saint-Exupery"},
    {"q": "If debugging is the process of removing bugs, then programming must be the process of putting them in.", "a": "Edsger Dijkstra"},
    {"q": "Hardware is easy to protect: lock it in a room. Software is harder.", "a": "Richard Stallman"},
    {"q": "I have always wished for my computer to be as easy to use as my telephone.", "a": "Bjarne Stroustrup"},
    {"q": "Innovation is not about saying yes to everything. It's about saying NO to all but the most crucial features.", "a": "Steve Jobs"}
]

def fetch_dynamic_quotes(count=36):
    quotes = []
    try:
        req = urllib.request.Request("https://dummyjson.com/quotes?limit=50", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            for item in data.get('quotes', []):
                quotes.append({"q": item["quote"], "a": item["author"]})
    except Exception as e:
        print("Dynamic fetch failed, using fallback:", e)
    
    if len(quotes) < count:
        quotes.extend(FALLBACK_QUOTES)
        
    random.shuffle(quotes)
    return quotes[:count]

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    curr_line = []
    for word in words:
        test_line = ' '.join(curr_line + [word])
        # get length
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            curr_line.append(word)
        else:
            if curr_line:
                lines.append(' '.join(curr_line))
            curr_line = [word]
    if curr_line:
        lines.append(' '.join(curr_line))
    return lines

def create_gradient_bg(width, height, color1, color2):
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def render_movie(quote, author, style, font_path, out_file):
    W, H = 720, 720
    FPS = 15
    DURATION = 5.0
    TOTAL_FRAMES = int(FPS * DURATION)
    
    # Palette
    c1 = (random.randint(10, 50), random.randint(10, 50), random.randint(20, 80))
    c2 = (random.randint(20, 60), random.randint(20, 60), random.randint(40, 100))
    bg = create_gradient_bg(W, H, c1, c2)
    
    font_size = 48
    try:
        font = ImageFont.truetype(font_path, font_size)
        font_author = ImageFont.truetype(font_path, 32)
    except:
        font = ImageFont.load_default()
        font_author = font
        
    draw = ImageDraw.Draw(bg)
    lines = wrap_text(f'"{quote}"', font, W - 100, draw)
    
    # Calculate text block height
    line_h = 60
    total_text_h = len(lines) * line_h + 40
    start_y = (H - total_text_h) // 2 - 30
    
    author_text = f"— {author}"
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "image2pipe", "-vcodec", "png", "-r", str(FPS),
        "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "500k", "-maxrate", "1M", "-bufsize", "1M",
        "-t", str(DURATION), out_file
    ]
    p = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    for f in range(TOTAL_FRAMES):
        frame = bg.copy()
        f_draw = ImageDraw.Draw(frame)
        time_ratio = f / TOTAL_FRAMES
        
        if style == "typewriter":
            # Reveal letters
            total_chars = sum(len(l) for l in lines)
            chars_to_show = int((f / (TOTAL_FRAMES * 0.7)) * total_chars)
            chars_to_show = min(chars_to_show, total_chars)
            
            y = start_y
            drawn = 0
            for line in lines:
                if drawn >= chars_to_show: break
                rem = chars_to_show - drawn
                to_draw = line[:rem]
                f_draw.text((50, y), to_draw, font=font, fill=(255, 255, 255))
                drawn += len(to_draw)
                y += line_h
                
            if time_ratio > 0.8:
                f_draw.text((W - 50 - f_draw.textlength(author_text, font=font_author), y + 20),
                            author_text, font=font_author, fill=(200, 200, 200))
                            
        elif style == "slide_up":
            # Slide everything up
            progress = min(1.0, f / (TOTAL_FRAMES * 0.5))
            # easing easeOutCubic
            ease = 1 - pow(1 - progress, 3)
            offset_y = int((1 - ease) * 200)
            alpha = int(ease * 255)
            
            y = start_y + offset_y
            # we must use RGBA to draw with alpha, but PIL simple text fill doesn't support alpha on RGB nicely 
            # without an overlay. Let's do a trick: draw white but blend the whole text layer.
            txt_layer = Image.new('RGBA', (W, H), (0,0,0,0))
            t_draw = ImageDraw.Draw(txt_layer)
            for line in lines:
                t_draw.text((50, y), line, font=font, fill=(255, 255, 255, alpha))
                y += line_h
            if time_ratio > 0.3:
                a_alpha = int(min(1.0, (time_ratio-0.3)*3) * 255)
                t_draw.text((W - 50 - f_draw.textlength(author_text, font=font_author), y + 20),
                            author_text, font=font_author, fill=(200, 200, 200, a_alpha))
            frame.paste(txt_layer, (0,0), txt_layer)
            
        elif style == "fade_words":
            # Fade in words one by one
            words = sum((l.split() for l in lines), [])
            total_words = len(words)
            words_to_show = int((f / (TOTAL_FRAMES * 0.7)) * total_words)
            words_to_show = min(words_to_show, total_words)
            
            y = start_y
            w_idx = 0
            for line in lines:
                x = 50
                for word in line.split():
                    if w_idx < words_to_show:
                        txt_width = f_draw.textlength(word + " ", font=font)
                        f_draw.text((x, y), word, font=font, fill=(255, 255, 255))
                        x += txt_width
                    w_idx += 1
                y += line_h
                
            if time_ratio > 0.8:
                f_draw.text((W - 50 - f_draw.textlength(author_text, font=font_author), y + 20),
                            author_text, font=font_author, fill=(200, 200, 200))
        
        frame.save(p.stdin, 'PNG')
        
    p.stdin.close()
    p.wait()

def upload_video(file_path, idx):
    title = f"Daily Inspiration #{idx}"
    desc = "#quote #inspiration Animated by KineticTypo_Bot_by_Yuzengbao"
    import requests # Fallback to requests for multipart data
    url = "https://bottube.ai/api/upload"
    headers = {"X-API-Key": API_KEY}
    try:
        with open(file_path, 'rb') as f:
            files = {'video': (os.path.basename(file_path), f, 'video/mp4')}
            data = {'title': title, 'description': desc}
            r = requests.post(url, headers=headers, files=files, data=data)
            print(f"Uploaded {file_path}: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Upload failed for {file_path}: {e}")

def main():
    quotes = fetch_dynamic_quotes(36)
    styles = ["typewriter", "slide_up", "fade_words"]
    
    videos = []
    print(f"Loaded {len(quotes)} quotes. Starting rendering...")
    for i, q in enumerate(quotes):
        out_file = os.path.join(OUTPUT_DIR, f"video_{i}.mp4")
        st = styles[i % len(styles)]
        ft = FONTS[i % len(FONTS)]
        
        print(f"[{i+1}/{len(quotes)}] Rendering {st} with {ft}: {q['q'][:30]}...")
        render_movie(q['q'], q['a'], st, ft, out_file)
        
        # Verify size
        size_kb = os.path.getsize(out_file) / 1024
        print(f"   -> Done. Size: {size_kb:.1f} KB")
        videos.append(out_file)
        
    print("\nUploading to BoTTube...")
    for i, v in enumerate(videos):
        upload_video(v, i+1)

if __name__ == "__main__":
    main()
