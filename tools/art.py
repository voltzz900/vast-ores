"""Hand-drawn 16x16 sprites for Vast Ores and Vast Depths.

Every sprite is a grid drawn pixel by pixel below. In item and block grids, `.` is transparent and the digits 0-6
pick a tone from the material's ramp: 0 the outline, 1-2 shadow, 3 the base colour, 4-5 light, 6 the highlight.
Ore grids lay those digits over a stone grid, whose letters a-d are that stone's tones, darkest first.
Light comes from the top left.

A ramp is drawn from the material's colour (shadows lean blue, highlights lean warm, as pixel artists shade), or
picked by hand in RAMPS. A finished PNG in art/<mod>/<block|item>/<name>.png replaces any of these.
"""
import colorsys

# ---- tones -------------------------------------------------------------------

def hexes(*values):
    return [int(v.lstrip("#"), 16) for v in values]


# Hand-picked ramps, darkest first, for the materials that should stand out.
RAMPS = {
    "stellarite": hexes("#2b1405", "#6b3a0e", "#a5621a", "#d9952b", "#f0b33a", "#fbd96a", "#fff6c8"),
    "infernium": hexes("#2a0805", "#6b1a0c", "#a8321a", "#d9502a", "#f07a3a", "#ffb45e", "#fff0b0"),
    "voidium": hexes("#14051f", "#3d0f5c", "#6e1f94", "#9d33c6", "#c23ce6", "#e07cf5", "#fbd8ff"),
    "ruby": hexes("#2a0208", "#6e0816", "#a8122a", "#d8213a", "#f0566a", "#ff9aa8", "#ffe6ea"),
    "sapphire": hexes("#040a2e", "#0d1f6e", "#1a36a8", "#2a4fd8", "#5a7ef0", "#9ab4ff", "#e6eeff"),
    "peridot": hexes("#0c2004", "#2a5208", "#4f8a14", "#7dcb2e", "#a6e65a", "#d0f59a", "#f4ffe0"),
}

# Lightness change, hue shift (degrees, toward blue below and toward yellow above) and saturation factor per tone.
STEPS = [(-0.42, -14, 1.1), (-0.30, -10, 1.15), (-0.17, -5, 1.1), (0.0, 0, 1.0), (0.10, 4, 0.95), (0.20, 8, 0.85), (0.32, 12, 0.6)]


def ramp(mat, colour):
    if mat in RAMPS:
        return RAMPS[mat]
    r, g, b = ((colour >> s & 255) / 255 for s in (16, 8, 0))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    # A light metal keeps room above its base tone, so its highlights don't all turn white.
    room = min(1.0, (0.97 - l) / 0.32) if l > 0.6 else 1.0
    if room < 1.0:
        l -= 0.08
    for dl, dh, fs in STEPS:
        dl = dl * room if dl > 0 else dl
        # Toward blue (240) in the shadows, toward yellow (60) in the light: along the shorter way round.
        goal = 240 if dh < 0 else 60
        delta = ((goal - h * 360 + 180) % 360) - 180
        nh = (h * 360 + max(-abs(dh), min(abs(dh), delta)) * (1 if s > 0.08 else 0.3)) % 360 / 360
        nl = max(0.04, min(0.97, l + dl))
        nr, ng, nb = colorsys.hls_to_rgb(nh, nl, max(0.0, min(1.0, s * fs)))
        out.append(round(nr * 255) << 16 | round(ng * 255) << 8 | round(nb * 255))
    return out


def rgba(colour):
    return ((colour >> 16) & 255, (colour >> 8) & 255, colour & 255, 255)


CLEAR = (0, 0, 0, 0)


def paint(grid, tones, letters=None):
    """Grid to pixels: digits index `tones`, letters index `letters` (a dict), `.` is clear."""
    px = []
    for row in grid:
        line = []
        for ch in row:
            if ch == ".":
                line.append(CLEAR)
            elif ch.isdigit():
                line.append(rgba(tones[int(ch)]))
            else:
                line.append(rgba(letters[ch]))
        px.append(line)
    return px


# ---- items -------------------------------------------------------------------

INGOT = [
    "................",
    "................",
    "................",
    "................",
    "........0000000.",
    "......0066555540",
    "....006655555430",
    "..00665555543320",
    ".066555555443220",
    ".044444444442210",
    ".033333333332110",
    ".02222222222110.",
    "..00000000000...",
    "................",
    "................",
    "................",
]

NUGGET = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....000........",
    "....06540.000...",
    "...0655430650...",
    "...05443205430..",
    "...04332104320..",
    "....0221002110..",
    ".....00...000...",
    "................",
    "................",
    "................",
]

RAW = [
    "................",
    "................",
    "................",
    "......000.......",
    "....0065400.....",
    "...0655544300...",
    "..065545433420..",
    "..0554433343320.",
    ".065443223343210",
    ".054432112332210",
    ".043321123322110",
    ".03322112222110.",
    "..0221101111100.",
    "...00000000000..",
    "................",
    "................",
]

DUST = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".......00.......",
    "......0650......",
    ".....065540.....",
    "....06564430....",
    "...0654643320...",
    "..065443362210..",
    ".05443322221110.",
    "..000000000000..",
    "................",
]

PLATE = [
    "................",
    "................",
    "................",
    "................",
    "...0000000000...",
    "..066666666650..",
    "..065555555530..",
    "..065555545530..",
    "..065554555530..",
    "..065455555530..",
    "..065555555530..",
    "..053333333320..",
    "...022222222210.",
    "....0000000000..",
    "................",
    "................",
]

GEAR = [
    "................",
    "......0000......",
    "..000.0650.000..",
    "..0650065540540.",
    "...06555555430..",
    "..0655544554320.",
    "0065540000443200",
    "0655540..0433220",
    "0544430..0332210",
    "0044430000322100",
    "..0443300003210.",
    "...04333332210..",
    "..0320022210320.",
    "..000.0220.000..",
    "......0000......",
    "................",
]

ROD = [
    "................",
    "................",
    "............00..",
    "...........0650.",
    "..........06530.",
    ".........06530..",
    "........06530...",
    ".......06530....",
    "......06530.....",
    ".....06530......",
    "....06530.......",
    "...06530........",
    "..05430.........",
    "..0320..........",
    "..000...........",
    "................",
]

GEM = [
    "................",
    "................",
    "......0000......",
    ".....066550.....",
    "....06655540....",
    "...0665555430...",
    "..066555554330..",
    "..044444443320..",
    "...0444433220...",
    "....04433220....",
    ".....043220.....",
    "......0320......",
    ".......00.......",
    "................",
    "................",
    "................",
]

# W and w are the handle's wood, light and dark; the head takes the steel ramp.
HAMMER = [
    "................",
    "........0000000.",
    ".......066555430",
    ".......055444320",
    ".......044333210",
    "..........0Ww0..",
    ".........0Ww0...",
    "........0Ww0....",
    ".......0Ww0.....",
    "......0Ww0......",
    ".....0Ww0.......",
    "....0Ww0........",
    "...0Ww0.........",
    "..0Ww0..........",
    "..000...........",
    "................",
]
WOOD = {"W": 0x9A6A3A, "w": 0x6B4423}
STEEL = hexes("#1e2226", "#3b4249", "#5d666e", "#7f8992", "#a3adb5", "#c6ced4", "#eef2f4")

# ---- blocks ------------------------------------------------------------------

# Two slabs of metal, their seams staggered like bricks.
STORAGE = [
    "6666666666666665",
    "6555555552655543",
    "6544444442654432",
    "6544444442654432",
    "6544544442654432",
    "6544444442654432",
    "5433333332543322",
    "3222222221322221",
    "6666666666666665",
    "6555265555555543",
    "6544265444444432",
    "6544265444444432",
    "6544265444454432",
    "6544265444444432",
    "5433254333333322",
    "3222132222222221",
]

RAW_BLOCK = [
    "1155443321554311",
    "1554432215544321",
    "5544332155433211",
    "4443321133332213",
    "3333321113322155",
    "2332215543211354",
    "3121155443211543",
    "2111554433211133",
    "1111544332215541",
    "1311443332155443",
    "5532333221554433",
    "4432122211544332",
    "4332111311433322",
    "3321155432133223",
    "2211154432112112",
    "1111344332543111",
]

# Stones the ores sit in: a-d are each stone's tones, darkest first.
STONES = {
    "stone": (hexes("#5c5c5c", "#6d6d6d", "#7d7d7d", "#8e8e8e"), [
        "ccbcccdcccbcccdc",
        "cbbccddccbbccccc",
        "ccccccdccccbbccb",
        "cdcccccbcccccdcc",
        "ccbbcccbbccccddc",
        "ccccdcccccdcccbc",
        "bccccddcccccccbb",
        "bbcccccccbbcccdc",
        "ccdccbcccbcdcccc",
        "cccccbbccccddccb",
        "dcccccccdcccccbb",
        "ddccbccccccbcccc",
        "ccccbbccdccbbcdc",
        "cbcccccddcccccdd",
        "cbbccdccccbcccdc",
        "ccccccccbbcccccc",
    ]),
    "deepslate": (hexes("#2a2a30", "#34343a", "#3e3e45", "#4c4c54"), [
        "bbbbcbbbbbbcbbbb",
        "aabbbbbaabbbbbaa",
        "bbbcbbbbbbbbcbbb",
        "cbbbbbcbbbbbbbbc",
        "bbaaabbbbbaaabbb",
        "bbbbbbcbbbbbbbcb",
        "bcbbbbbbbcbbbbbb",
        "aabbbaaaabbbbaab",
        "bbbbbbbbcbbbcbbb",
        "bbcbbbbbbbbbbbbb",
        "abbbbaabbbbaaabb",
        "bbbcbbbbbcbbbbbb",
        "cbbbbbbcbbbbbbcb",
        "bbaaabbbbbbaabbb",
        "bbbbbcbbbbbbbbbb",
        "bcbbbbbbbcbbbcbb",
    ]),
    "netherrack": (hexes("#3a1414", "#5a1e1e", "#6e2a2a", "#8a3a36"), [
        "cbcdcbbcbcdcbbcb",
        "bacbbabcbbcbaabc",
        "cbdcbbcdcabccbdc",
        "bcccabccbbcdcbcb",
        "abcbbcbaccbcbacb",
        "cbdcbcbbcdcbbcdc",
        "bcbaabccbcbabcbb",
        "cdcbbcdcbbcbbcdc",
        "bcbbcbcbadcbcbcb",
        "abccbabcbcbbcbab",
        "cbcdcbbcdcbacdcb",
        "bcbcbacbbcbbcbcb",
        "cdcbbcdcbacdcbbc",
        "bcbabcbcbbcbcabc",
        "cbcdcbabcdcbbcdc",
        "bacbbcbcbcbabcbb",
    ]),
    "end_stone": (hexes("#a9a66c", "#c4c184", "#d9d79a", "#e8e6b0"), [
        "ccdcccccccdccccc",
        "cccccbccccccccdc",
        "cdccccccacccbccc",
        "ccccdccccccccccc",
        "cbcccccdccccdccb",
        "cccacccccbccccac",
        "ccccccdcccccccdc",
        "dccbccccccaccccc",
        "cccccccccccccbcc",
        "cacccdcccbcccccc",
        "ccccccccccccdccc",
        "ccbcccacccccccac",
        "ccccdcccccdccccc",
        "cdccccccbccccbcc",
        "ccccbccdccccccdc",
        "cccccccccacccccc",
    ]),
}

# Ore clusters over the stone: three layouts for metals, so no two neighbouring ores look the same, and one for gems.
ORE_METAL = [
    [
        "................",
        "................",
        "..34............",
        ".3554......45...",
        ".2443.....4553..",
        "..21.....34432..",
        "..........221...",
        "......34........",
        ".....3564.......",
        ".....24431......",
        "......221....4..",
        "............453.",
        "...34.......232.",
        "..3553.......1..",
        "..2432..........",
        "...11...........",
    ],
    [
        "................",
        "....45..........",
        "...4554.....34..",
        "...3443....3553.",
        "....21.....2442.",
        "............11..",
        "..34............",
        ".3553....456....",
        ".2442...35543...",
        "..11....24432...",
        ".........211....",
        "...........34...",
        "....45....3553..",
        "...3563...2432..",
        "...2431....11...",
        "....11..........",
    ],
    [
        "................",
        "..........34....",
        ".45......3553...",
        "3554.....2442...",
        "2443......11....",
        ".21.............",
        ".......456......",
        "......35543.....",
        "......24432..34.",
        ".......211..3553",
        "............2432",
        "..34.........11.",
        ".3563...........",
        ".24431....45....",
        "..221....3443...",
        ".........221....",
    ],
]

ORE_GEM = [
    "................",
    "................",
    "...36...........",
    "..3653.....36...",
    "..2442....3663..",
    "...2......2442..",
    "...........22...",
    ".......36.......",
    "......3663......",
    "......2442......",
    ".......22...36..",
    "...........3653.",
    "..36.......2442.",
    ".3663.......2...",
    ".2442...........",
    "..22............",
]


def check():
    for name, grid in list(globals().items()):
        if name.isupper() and isinstance(grid, list) and grid and isinstance(grid[0], str):
            assert len(grid) == 16 and all(len(r) == 16 for r in grid), f"{name}: {[len(r) for r in grid]}"
    for name, (_, grid) in STONES.items():
        assert len(grid) == 16 and all(len(r) == 16 for r in grid), f"stone {name}: {[len(r) for r in grid]}"
    for i, grid in enumerate(ORE_METAL):
        assert len(grid) == 16 and all(len(r) == 16 for r in grid), f"ore {i}: {[len(r) for r in grid]}"


check()


# ---- sprites -----------------------------------------------------------------

def item(kind, mat, colour):
    return paint({"ingot": INGOT, "nugget": NUGGET, "raw": RAW, "dust": DUST, "plate": PLATE,
                  "gear": GEAR, "rod": ROD, "gem": GEM}[kind], ramp(mat, colour))


def storage(mat, colour):
    return paint(STORAGE, ramp(mat, colour))


def raw_block(mat, colour):
    return paint(RAW_BLOCK, ramp(mat, colour))


def hammer():
    return paint(HAMMER, STEEL, WOOD)


def ore(mat, colour, base, gem=False):
    tones, stone = STONES[base]
    cluster = ORE_GEM if gem else ORE_METAL[sum(map(ord, mat)) % len(ORE_METAL)]
    letters = dict(zip("abcd", tones))
    grid = [[o if o != "." else s for o, s in zip(orow, srow)] for orow, srow in zip(cluster, stone)]
    return paint(grid, ramp(mat, colour), letters)


# ---- end-game tools and armour (Vast Depths) ------------------------------------

# The handle is a dark obsidian grip, so every metal's head stands out on it: H light, h dark, k its outline.
# g is the metal's accent inlay.
BLAZE = {"H": 0x6A5A80, "h": 0x3E3350, "k": 0x140E1C}
ACCENTS = {"stellarite": 0xBFE8FF, "infernium": 0xFFE45E, "voidium": 0x7FF5FF}

PICKAXE = [
    "................",
    "..0000000.......",
    ".06655554000....",
    ".0544444g4440...",
    "..000022334440..",
    ".........kH0340.",
    "........kHh0340.",
    ".......kHhk0340.",
    "......kHhk.0340.",
    ".....kHhk..0230.",
    "....kHhk...0230.",
    "...kHhk.....00..",
    "..kHhk..........",
    ".kHhk...........",
    ".kkk............",
    "................",
]

AXE = [
    "................",
    "........0000....",
    ".......0665400..",
    "......06555g440.",
    "......0544444430",
    "......0544Hh3320",
    "........kHh03320",
    ".......kHhk.0220",
    "......kHhk...00.",
    ".....kHhk.......",
    "....kHhk........",
    "...kHhk.........",
    "..kHhk..........",
    ".kHhk...........",
    ".kkk............",
    "................",
]

SHOVEL = [
    "................",
    "..........000...",
    ".........06540..",
    "........0665540.",
    "........0554g430",
    "........05444320",
    "........kH433210",
    ".......kHhk0000.",
    "......kHhk......",
    ".....kHhk.......",
    "....kHhk........",
    "...kHhk.........",
    "..kHhk..........",
    ".kHhk...........",
    ".kkk............",
    "................",
]

SWORD = [
    ".............00.",
    "............0650",
    "...........06530",
    "..........06530.",
    ".........06530..",
    "........06530...",
    ".......06530....",
    "...0..06530.....",
    "...0g06530......",
    "....0g630.......",
    "...kH0g0........",
    "..kHk.0g0.......",
    ".kHk....00......",
    "0g0.............",
    ".0..............",
    "................",
]

HELMET = [
    "................",
    "................",
    "....00000000....",
    "...0665555540...",
    "..066555555430..",
    "..0554444g4320..",
    "..054433333320..",
    "..044322222210..",
    "..0430....0320..",
    "..0430....0320..",
    "..0320....0210..",
    "..000......000..",
    "................",
    "................",
    "................",
    "................",
]

CHESTPLATE = [
    "................",
    "..000......000..",
    ".06540....04530.",
    ".05544000044430.",
    ".05445555554430.",
    ".04434444g44320.",
    ".03304444440330.",
    ".02204333330220.",
    "....04333330....",
    "....04333330....",
    "....03222220....",
    "....02222210....",
    "....00000000....",
    "................",
    "................",
    "................",
]

LEGGINGS = [
    "................",
    "................",
    "...0000000000...",
    "...0665555540...",
    "...0544g44430...",
    "...0433333320...",
    "...0433003320...",
    "...0430..0320...",
    "...0430..0320...",
    "...0430..0320...",
    "...0320..0210...",
    "...0320..0210...",
    "...0000..0000...",
    "................",
    "................",
    "................",
]

BOOTS = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "..00000..00000..",
    "..05540..05540..",
    "..04430..04430..",
    "..04430..04430..",
    "..04430..04430..",
    ".004430.004430..",
    ".064430.064430..",
    ".033220.033220..",
    ".000000.000000..",
    "................",
    "................",
]

check()


def tool(kind, mat, colour):
    grid = {"pickaxe": PICKAXE, "axe": AXE, "shovel": SHOVEL, "sword": SWORD}[kind]
    return paint(grid, ramp(mat, colour), {**BLAZE, "g": ACCENTS.get(mat, 0xFFFFFF)})


def armor(piece, mat, colour):
    grid = {"helmet": HELMET, "chestplate": CHESTPLATE, "leggings": LEGGINGS, "boots": BOOTS}[piece]
    return paint(grid, ramp(mat, colour), {"g": ACCENTS.get(mat, 0xFFFFFF)})


# ---- worn armour (64x32, the player model's armour layout) -------------------------
#
# Each box of the model unfolds onto the sheet: for a box w wide, h tall and d deep whose corner is at (u, v),
# the top is at (u+d, v), the bottom at (u+d+w, v), and the sides run along v+d: right (u), front (u+d),
# left (u+d+w), back (u+2d+w). Left arms and legs reuse the right ones. "humanoid" holds the helmet, the
# chestplate and the boots; "humanoid_leggings" the leggings.

# The fronts are drawn by hand; `.` leaves the player showing.
HELM_FRONT = [
    "65555556",
    "544gg445",
    "43....34",
    "32....23",
    "32....23",
    "21....12",
    "21....12",
    "10....01",
]
CHEST_FRONT = [
    "65....56",
    "55444455",
    "54433445",
    "543gg345",
    "54333345",
    "43333334",
    "43322334",
    "43333334",
    "32222223",
    "32333323",
    "21222212",
    "10111101",
]
BELT_FRONT = [
    "........",
    "........",
    "........",
    "........",
    "........",
    "........",
    "........",
    "54444445",
    "321gg123",
    "43333334",
    "32222223",
    "21111112",
]


def plate(w, h, rows=None, ridge=False):
    """A plain plate face: light top and left edge, dark bottom and right, a rivet in each top corner.
    `rows` keeps only those rows (the others stay clear); `ridge` runs a raised line down the middle."""
    grid = []
    for y in range(h):
        line = ""
        for x in range(w):
            if rows is not None and y not in rows:
                line += "."
                continue
            top = rows[0] if rows is not None else 0
            bottom = rows[-1] if rows is not None else h - 1
            if y == top:
                c = "5"
            elif y == bottom:
                c = "1"
            elif x == 0:
                c = "4"
            elif x == w - 1:
                c = "2"
            elif ridge and x in (w // 2 - 1, w // 2):
                c = "4" if x == w // 2 - 1 else "2"
            else:
                c = "3"
            if w > 2 and y == top + 1 and x in (1, w - 2) and h > 3:
                c = "5"
            line += c
        grid.append(line)
    return grid


def put(sheet, u, v, grid):
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            sheet[v + y][u + x] = ch


def unfold(sheet, u, v, w, h, d, front, back, side, top, bottom=None):
    if top is not None:
        put(sheet, u + d, v, top)
    if bottom is not None:
        put(sheet, u + d + w, v, bottom)
    put(sheet, u, v + d, side)
    put(sheet, u + d, v + d, front)
    put(sheet, u + d + w, v + d, side)
    put(sheet, u + 2 * d + w, v + d, back)


def equipment(mat, colour):
    """The worn armour: (humanoid, humanoid_leggings), each a 64x32 pixel grid."""
    outer = [["."] * 64 for _ in range(32)]
    # Helmet on the head box (8x8x8 at 0,0): open face, plated sides, back and crown.
    unfold(outer, 0, 0, 8, 8, 8, HELM_FRONT, plate(8, 8), plate(8, 8), plate(8, 8, ridge=True))
    # Chestplate on the body (8x12x4 at 16,16) and the arms (4x12x4 at 40,16): pauldrons and vambraces, hands bare.
    unfold(outer, 16, 16, 8, 12, 4, CHEST_FRONT, plate(8, 12, ridge=True), plate(4, 12), plate(8, 4))
    arm = plate(4, 12, rows=list(range(0, 4)))
    arm = [a if i < 4 else p for i, (a, p) in enumerate(zip(arm, plate(4, 12, rows=list(range(5, 10)))))]
    unfold(outer, 40, 16, 4, 12, 4, arm, arm, arm, plate(4, 4))
    # Boots on the legs (4x12x4 at 0,16): the lower half, a dark sole underneath.
    boot = plate(4, 12, rows=list(range(6, 12)))
    unfold(outer, 0, 16, 4, 12, 4, boot, boot, boot, None, ["1111"] * 4)

    inner = [["."] * 64 for _ in range(32)]
    # Leggings: a belt round the body's waist, then thighs and knees down to the boots.
    waist = plate(4, 12, rows=list(range(7, 12)))
    unfold(inner, 16, 16, 8, 12, 4, BELT_FRONT, plate(8, 12, rows=list(range(7, 12))), waist, None)
    leg = plate(4, 12, rows=list(range(0, 9)))
    leg[5] = "4554"
    unfold(inner, 0, 16, 4, 12, 4, leg, leg, leg, plate(4, 4))

    letters = {"g": ACCENTS.get(mat, 0xFFFFFF)}
    return (paint(["".join(r) for r in outer], ramp(mat, colour), letters),
            paint(["".join(r) for r in inner], ramp(mat, colour), letters))
