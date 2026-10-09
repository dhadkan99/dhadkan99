
import os
import io
import math
import requests

from PIL import Image, ImageDraw, ImageFont, ImageSequence

USERNAME = "dhadkan99"
TOKEN = os.getenv("GITHUB_TOKEN", "")

BACKGROUND_URL = (
    "https://user-images.githubusercontent.com/74038190/"
    "225813708-98b745f2-7d22-48cf-9150-083f1b00d6c9.gif"
)

OUTPUT = "profile/animated-banner.gif"

WIDTH = 960
HEIGHT = 540

NAVY = "#06132F"
PINK = "#F044D6"
BLUE = "#1689E8"
PURPLE = "#A06AF0"
GOLD = "#FFD166"
WHITE = "#FFFFFF"
MUTED = "#BBD6FF"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "dhadkan99-readme-banner",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def github_get(endpoint, params=None):
    response = requests.get(
        f"https://api.github.com/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def search_count(query):
    result = github_get(
        "search/issues",
        {"q": query, "per_page": 1},
    )
    return result["total_count"]


def get_stats():
    user = github_get(f"users/{USERNAME}")

    # GitHub commit search includes indexed public commits.
    commits_response = requests.get(
        "https://api.github.com/search/commits",
        headers=HEADERS,
        params={
            "q": f"author:{USERNAME}",
            "per_page": 1,
        },
        timeout=30,
    )
    commits_response.raise_for_status()
    commits = commits_response.json()["total_count"]

    prs = search_count(f"author:{USERNAME} type:pr")
    issues = search_count(f"author:{USERNAME} type:issue")

    repos = []
    page = 1

    while True:
        batch = github_get(
            f"users/{USERNAME}/repos",
            {
                "per_page": 100,
                "page": page,
                "type": "owner",
            },
        )
        repos.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    languages = {}

    for repo in repos:
        if repo.get("fork"):
            continue

        language = repo.get("language")

        if language:
            languages[language] = languages.get(language, 0) + 1

    top_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:4]

    return {
        "commits": commits,
        "prs": prs,
        "issues": issues,
        "languages": top_languages,
        "public_repos": user["public_repos"],
    }


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/"
        + ("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


TITLE_FONT = font(42, True)
SUBTITLE_FONT = font(18)
LABEL_FONT = font(17, True)
VALUE_FONT = font(35, True)
SMALL_FONT = font(15)


def rounded_panel(draw, bounds, outline=PINK, radius=16):
    draw.rounded_rectangle(
        bounds,
        radius=radius,
        fill=(6, 19, 47, 215),
        outline=outline,
        width=3,
    )


def draw_card(draw, x, y, label, value, color):
    rounded_panel(
        draw,
        (x, y, x + 270, y + 100),
        outline=color,
    )

    draw.text(
        (x + 18, y + 14),
        label,
        font=LABEL_FONT,
        fill=color,
    )

    draw.text(
        (x + 18, y + 45),
        str(value),
        font=VALUE_FONT,
        fill=WHITE,
    )


def overlay_stats(frame, stats):
    base = frame.convert("RGBA")

    overlay = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(overlay)

    # Translucent background for readability
    draw.rounded_rectangle(
        (15, 15, 945, 360),
        radius=18,
        fill=(4, 12, 32, 185),
    )

    draw.text(
        (40, 32),
        "dhadkan99",
        font=TITLE_FONT,
        fill=WHITE,
        stroke_width=1,
        stroke_fill=NAVY,
    )

    draw.line(
        (40, 91, 450, 91),
        fill=PINK,
        width=4,
    )

    draw.text(
        (40, 105),
        "Full-Stack Developer | Frontend Specialist",
        font=SUBTITLE_FONT,
        fill=MUTED,
    )

    # GitHub statistics
    draw_card(
        draw, 35, 150,
        "COMMITS", stats["commits"], PINK,
    )

    draw_card(
        draw, 345, 150,
        "PULL REQUESTS", stats["prs"], BLUE,
    )

    draw_card(
        draw, 655, 150,
        "ISSUES", stats["issues"], GOLD,
    )

    draw.text(
        (40, 275),
        "TOP LANGUAGES",
        font=LABEL_FONT,
        fill=PINK,
    )

    language_colors = [PINK, BLUE, PURPLE, GOLD]
    languages = stats["languages"]

    total = sum(count for _, count in languages) or 1

    for index, (language, count) in enumerate(languages):
        x = 40 + index * 225
        y = 315

        draw.text(
            (x, y),
            language[:15],
            font=SMALL_FONT,
            fill=WHITE,
        )

        draw.rounded_rectangle(
            (x, y + 25, x + 180, y + 34),
            radius=4,
            fill=(65, 77, 110, 220),
        )

        bar_width = max(8, int((count / total) * 180))

        draw.rounded_rectangle(
            (x, y + 25, x + bar_width, y + 34),
            radius=4,
            fill=language_colors[index],
        )

    draw.text(
        (40, 500),
        "KATHMANDU, NEPAL  |  BUILDING THE WEB",
        font=SMALL_FONT,
        fill=WHITE,
        stroke_width=1,
        stroke_fill=NAVY,
    )

    return Image.alpha_composite(base, overlay).convert("RGB")


def generate():
    os.makedirs("profile", exist_ok=True)

    print("Fetching GitHub statistics...")
    stats = get_stats()
    print(stats)

    print("Downloading Mario GIF...")
    response = requests.get(BACKGROUND_URL, timeout=60)
    response.raise_for_status()

    source = Image.open(io.BytesIO(response.content))

    # Sample frames to keep the generated GIF manageable.
    total_frames = getattr(source, "n_frames", 1)
    step = max(1, math.ceil(total_frames / 48))

    output_frames = []
    durations = []

    elapsed = 0

    for index, frame in enumerate(ImageSequence.Iterator(source)):
        duration = frame.info.get(
            "duration",
            source.info.get("duration", 100),
        ) or 100

        elapsed += duration

        if index % step != 0:
            continue

        background = frame.convert("RGBA")
        background = background.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.NEAREST,
        )

        result = overlay_stats(background, stats)
        output_frames.append(result)

        durations.append(max(20, elapsed))
        elapsed = 0

    if not output_frames:
        raise RuntimeError("No GIF frames generated")

    # Preserve the trailing time from sampled frames.
    durations[-1] += elapsed

    output_frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=output_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    generate()
