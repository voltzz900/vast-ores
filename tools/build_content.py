#!/usr/bin/env python3
"""Builds Vast Ores and Vast Depths, two content mods for Horizon.

Inspired by the AllTheOres and Allthemodium mods, but clean-room: nothing here comes from their jars.
Materials, numbers, recipes and every texture are our own; textures are drawn below.
File formats follow Minecraft 26.3's own data (flat features, `condition`/`modifier` loot).

Usage: build_content.py <output dir>   (writes <output dir>/vastores and <output dir>/vastdepths)
"""
import json
import random
import shutil
import struct
import sys
import zlib
from pathlib import Path

# ---- materials ---------------------------------------------------------------

# name, colour, tool tier, (count, size, min y, max y, shape), english, portuguese
ORES = [
    ("aluminum", 0xC9D1D9, "stone", (8, 9, -16, 96, "trapezoid"), "Aluminum", "Alumínio"),
    ("lead", 0x5E6A8A, "stone", (7, 9, -48, 64, "trapezoid"), "Lead", "Chumbo"),
    ("nickel", 0xCFC79A, "stone", (6, 8, -48, 64, "trapezoid"), "Nickel", "Níquel"),
    ("osmium", 0x9DB6C9, "iron", (6, 8, -48, 48, "trapezoid"), "Osmium", "Ósmio"),
    ("platinum", 0x9FE3F0, "iron", (4, 6, -64, 16, "trapezoid"), "Platinum", "Platina"),
    ("silver", 0xDDE6EE, "iron", (5, 8, -48, 32, "trapezoid"), "Silver", "Prata"),
    ("tin", 0xBFD3DC, "stone", (9, 9, -16, 96, "trapezoid"), "Tin", "Estanho"),
    ("uranium", 0x7FD14A, "iron", (4, 6, -64, 24, "trapezoid"), "Uranium", "Urânio"),
    ("zinc", 0xB8C2A8, "stone", (7, 9, -32, 80, "trapezoid"), "Zinc", "Zinco"),
    ("iridium", 0xE8E3F2, "diamond", (2, 4, -64, -16, "uniform"), "Iridium", "Irídio"),
]
GEMS = [
    ("ruby", 0xD8213A, (3, 5, -32, 32, "trapezoid"), "Ruby", "Rubi"),
    ("sapphire", 0x2A4FD8, (3, 5, -32, 32, "trapezoid"), "Sapphire", "Safira"),
    ("peridot", 0x7DCB2E, (3, 5, -32, 32, "trapezoid"), "Peridot", "Peridoto"),
]
# name, colour, dust recipe (inputs, count), english, portuguese
ALLOYS = [
    ("bronze", 0xC98A3C, (["copper"] * 3 + ["tin"], 4), "Bronze", "Bronze"),
    ("brass", 0xD9B84A, (["copper"] * 3 + ["zinc"], 4), "Brass", "Latão"),
    ("constantan", 0xD69A70, (["copper", "nickel"], 2), "Constantan", "Constantan"),
    ("electrum", 0xE8D16A, (["gold", "silver"], 2), "Electrum", "Electrum"),
    ("invar", 0xA9B3A6, (["iron", "iron", "nickel"], 3), "Invar", "Invar"),
    ("steel", 0x6F767D, (["iron", "minecraft:coal", "minecraft:coal"], 1), "Steel", "Aço"),
    ("enderium", 0x1F6E6B, (["lead"] * 3 + ["platinum", "minecraft:ender_pearl", "minecraft:ender_pearl"], 4), "Enderium", "Endério"),
    ("lumium", 0xF2E7A0, (["tin"] * 3 + ["silver", "minecraft:glowstone_dust", "minecraft:glowstone_dust"], 4), "Lumium", "Lúmio"),
    ("signalum", 0xE2531E, (["copper"] * 3 + ["silver"] + ["minecraft:redstone"] * 4, 4), "Signalum", "Sinálio"),
]
VANILLA = [
    ("iron", 0xD8D8D8, "Iron", "Ferro"),
    ("gold", 0xF5D13B, "Gold", "Ouro"),
    ("copper", 0xE07A4C, "Copper", "Cobre"),
]

# The top tier: one ore each, in a harder place, each needing the tier below to mine.
# name, colour, base, dimension, (count, size, min y, max y), english, portuguese, mining speed, durability (unused: the gear is unbreakable)
SUPER = [
    ("stellarite", 0xF0B33A, "deepslate", "overworld", (2, 4, -64, -40), "Stellarite", "Estelarita", 12.0, 4000),
    ("infernium", 0xE0562A, "netherrack", "nether", (2, 3, 8, 40), "Infernium", "Infernium", 14.0, 6000),
    ("voidium", 0xC23CE6, "end_stone", "end", (2, 3, 10, 80), "Voidium", "Voidium", 16.0, 8000),
]
# Tool stats per tier: (attack damage added to the player's 1, attack speed modifier) for each kind.
# Netherite is sword 7/-2.4, axe 9/-3.0, pickaxe 5/-2.8, shovel 5.5/-3.0; each tier hits harder and a
# little faster, up to a voidium sword that takes most mobs in one hit.
TOOL_STATS = {
    "stellarite": {"sword": (11.0, -2.4), "axe": (13.0, -3.0), "pickaxe": (7.0, -2.8), "shovel": (7.5, -3.0)},
    "infernium": {"sword": (17.0, -2.2), "axe": (19.0, -2.9), "pickaxe": (10.0, -2.7), "shovel": (10.5, -2.9)},
    "voidium": {"sword": (29.0, -2.0), "axe": (31.0, -2.8), "pickaxe": (15.0, -2.6), "shovel": (15.5, -2.8)},
}
# Armour per tier: (helmet, chestplate, leggings, boots armour points, toughness per piece, knockback resistance
# per piece). Netherite is 3/8/6/3, 3, 0.1.
ARMOR_STATS = {
    "stellarite": ((4, 9, 7, 4), 4.0, 0.15),
    "infernium": ((5, 10, 8, 5), 6.0, 0.2),
    "voidium": ((6, 12, 10, 6), 8.0, 0.25),
}
SUPER_ALLOYS = [
    ("infernium_stellarite_alloy", 0x8FD08A, ("infernium", "stellarite"), "Infernium-Stellarite Alloy", "Liga de Infernium-Estelarita"),
    ("voidium_stellarite_alloy", 0xD97C9A, ("voidium", "stellarite"), "Voidium-Stellarite Alloy", "Liga de Voidium-Estelarita"),
    ("voidium_infernium_alloy", 0x7F8CE6, ("voidium", "infernium"), "Voidium-Infernium Alloy", "Liga de Voidium-Infernium"),
]


# ---- PNG drawing -------------------------------------------------------------

def png(pixels):
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def rgb(colour, f=1.0):
    r, g, b = (colour >> 16) & 255, (colour >> 8) & 255, colour & 255
    return tuple(max(0, min(255, int(c * f))) for c in (r, g, b)) + (255,)


def blank():
    return [[(0, 0, 0, 0)] * 16 for _ in range(16)]


BASES = {  # base colour, noise, streaks
    "stone": (0x7A7A7A, 0.12, False),
    "deepslate": (0x3C3C42, 0.14, True),
    "netherrack": (0x6E2A2A, 0.16, False),
    "end_stone": (0xD9D79A, 0.07, False),
}


def ground(rnd, base):
    colour, noise, streaks = BASES[base]
    px = blank()
    for y in range(16):
        for x in range(16):
            f = 1 + rnd.uniform(-noise, noise) + (0.1 if streaks and y % 4 == 0 else 0)
            px[y][x] = rgb(colour, f)
    return px


def ore(colour, seed, base):
    rnd = random.Random(seed)
    px = ground(rnd, base)
    for _ in range(5):
        cx, cy = rnd.randint(2, 13), rnd.randint(2, 13)
        for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (1, 1)][: rnd.randint(3, 5)]:
            x, y = cx + dx, cy + dy
            if 0 <= x < 16 and 0 <= y < 16:
                px[y][x] = rgb(colour, 0.75 + 0.35 * rnd.random())
        if 0 <= cy - 1 < 16:
            px[cy - 1][cx] = rgb(colour, 1.25)
    return px


def storage(colour):
    px = blank()
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            seam = x % 8 == 0 or y % 8 == 0
            f = 0.6 if edge else 0.85 if seam else 1.05 - 0.02 * ((x + y) % 4)
            if not edge and (x in (1, 2) and 0 < y < 15 or y in (1, 2) and 0 < x < 15):
                f = max(f, 1.2)
            px[y][x] = rgb(colour, f)
    return px


def raw_block(colour, seed):
    rnd = random.Random(seed)
    px = blank()
    for y in range(16):
        for x in range(16):
            px[y][x] = rgb(colour, 0.7 + 0.4 * rnd.random())
    for _ in range(4):
        x, y = rnd.randint(0, 15), rnd.randint(0, 15)
        for _ in range(rnd.randint(3, 6)):
            if 0 <= x < 16 and 0 <= y < 16:
                px[y][x] = rgb(colour, 0.45)
            x += rnd.choice((-1, 0, 1)); y += 1
    return px


def shape(colour, cells, outline=0.5, light=1.25, dark=0.8):
    """Fill `cells`; light top-left edges, dark bottom-right, outline around."""
    px = blank()
    for x, y in cells:
        f = 1.0
        if (x - 1, y) not in cells or (x, y - 1) not in cells:
            f = light
        elif (x + 1, y) not in cells or (x, y + 1) not in cells:
            f = dark
        px[y][x] = rgb(colour, f)
    for x, y in list(cells):
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < 16 and 0 <= ny < 16 and (nx, ny) not in cells and px[ny][nx][3] == 0:
                px[ny][nx] = rgb(colour, outline)
    return px


def ingot_cells():
    return {(x, 6 + row) for row in range(5) for x in range(3 + (4 - row) // 2, 13 - row // 2)}


def nugget_cells():
    return {(x, y) for x in range(6, 10) for y in range(7, 10)} | {(7, 6), (8, 6), (9, 10), (6, 10)}


def raw_cells(seed):
    rnd = random.Random(seed)
    cells = set()
    for cx, cy, r in ((7, 8, 3.6), (10, 6, 2.4), (5, 10, 2.2)):
        for y in range(16):
            for x in range(16):
                if (x - cx) ** 2 + (y - cy) ** 2 <= (r + rnd.random() * 0.6) ** 2:
                    cells.add((x, y))
    return cells


def dust_cells():
    return {(x, y) for y in range(7, 13) for x in range(8 - (y - 5), 8 + (y - 5))}


def plate_cells():
    return {(x, y) for x in range(3, 13) for y in range(4, 12)}


def gear_cells():
    cells = {(x, y) for y in range(16) for x in range(16) if 2.2 ** 2 < (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 5.2 ** 2}
    return cells | {(7, 1), (8, 1), (7, 14), (8, 14), (1, 7), (1, 8), (14, 7), (14, 8),
                    (3, 3), (12, 3), (3, 12), (12, 12), (2, 2), (13, 2), (2, 13), (13, 13)}


def rod_cells():
    return {(i + d, 15 - i) for i in range(3, 13) for d in (0, 1)}


def gem_cells():
    cells = set()
    for y in range(3, 13):
        w = 5 - abs(y - 6) if y <= 6 else max(0, 5 - (y - 6) * 5 // 6)
        cells |= {(x, y) for x in range(8 - w, 8 + w)}
    return cells


def gem_px(colour):
    px = shape(colour, gem_cells(), outline=0.45, light=1.35, dark=0.7)
    px[5][6] = (255, 255, 255, 255)
    px[6][7] = rgb(colour, 1.6)
    return px


def dust_px(colour, seed):
    rnd = random.Random(seed)
    px = shape(colour, dust_cells(), outline=0.55, light=1.15, dark=0.85)
    for _ in range(6):
        x, y = rnd.randint(4, 11), rnd.randint(8, 12)
        if px[y][x][3]:
            px[y][x] = rgb(colour, 1.35)
    return px


def handle(px, length=11, wood=0x6B4423):
    for i in range(1, length):
        px[16 - i][i - 1] = rgb(wood, 1.1)
        if 16 - i + 1 < 16:
            px[16 - i + 1][i - 1] = rgb(wood, 0.75)
    return px


def hammer_px():
    px = handle(blank())
    for x in range(7, 15):
        for y in range(1, 6):
            px[y][x] = rgb(0x9EA4AA, 1.2 if y == 1 else 0.75 if y == 5 else 1.0)
    return px


# ---- the builder -------------------------------------------------------------

class Mod:
    def __init__(self, ns):
        self.ns = ns
        self.files, self.recipes, self.tags = {}, {}, {}
        self.lang_en, self.lang_pt = {}, {}
        self.blocks, self.items = [], []

    def id(self, name):
        return name if ":" in name else f"{self.ns}:{name}"

    def put(self, path, value):
        self.files[path] = value

    def tag(self, registry, name, value):
        self.tags.setdefault((registry, name), []).append(value)

    def recipe(self, name, value):
        self.recipes[name] = value

    def names(self, kind, name, en, pt):
        self.lang_en[f"{kind}.{self.ns}.{name}"] = en
        self.lang_pt[f"{kind}.{self.ns}.{name}"] = pt

    def item(self, name, template, pixels, en, pt, handheld=False, texture=None, tint=None, **extra):
        """`pixels` is drawn into the mod; `texture` instead names one the game has (never copied), `tint` colours it."""
        ns = self.ns
        self.items.append(name)
        self.put(f"data/{ns}/horizon/item/{name}.json", {"template": template, **extra})
        parent = "minecraft:item/handheld" if handheld else "minecraft:item/generated"
        layer = texture or f"{ns}:item/{name}"
        self.put(f"assets/{ns}/models/item/{name}.json", {"parent": parent, "textures": {"layer0": layer}})
        model = {"type": "minecraft:model", "model": f"{ns}:item/{name}"}
        if tint is not None:
            model["tints"] = [{"type": "minecraft:constant", "value": tint}]
        self.put(f"assets/{ns}/items/{name}.json", {"model": model})
        if texture is None:
            self.put(f"assets/{ns}/textures/item/{name}.png", png(pixels))
        self.names("item", name, en, pt)

    def block(self, name, template, pixels, en, pt, drop=None, tier=None):
        ns = self.ns
        self.blocks.append(name)
        self.items.append(name)
        self.put(f"data/{ns}/horizon/block/{name}.json", {"template": template, "item": True})
        self.put(f"assets/{ns}/blockstates/{name}.json", {"variants": {"": {"model": f"{ns}:block/{name}"}}})
        self.put(f"assets/{ns}/models/block/{name}.json", {"parent": "minecraft:block/cube_all", "textures": {"all": f"{ns}:block/{name}"}})
        self.put(f"assets/{ns}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"{ns}:block/{name}"}})
        self.put(f"assets/{ns}/textures/block/{name}.png", png(pixels))
        self.names("block", name, en, pt)
        self.put(f"data/{ns}/loot_table/blocks/{name}.json", drop or self_drop(self.id(name)))
        self.tag("block", "minecraft:mineable/pickaxe", self.id(name))
        for t in tier or ():
            self.tag("block", t, self.id(name))

    def cook(self, name, ingredient, result, xp=0.7):
        for kind, ticks in (("smelting", 200), ("blasting", 100)):
            self.recipe(f"{kind}/{name}", {"type": f"minecraft:{kind}", "cookingtime": ticks, "experience": xp,
                                           "ingredient": ingredient, "result": {"id": result}})

    def pack(self, small, big, label):
        self.recipe(f"storage/{label}_from_small", {"type": "minecraft:crafting_shaped", "key": {"#": small},
                                                    "pattern": ["###", "###", "###"], "result": {"id": big}})
        self.recipe(f"storage/{label}_to_small", {"type": "minecraft:crafting_shapeless", "ingredients": [big],
                                                  "result": {"count": 9, "id": small}})

    def ingot_family(self, mat, colour, en, pt, beacon=True):
        self.item(f"{mat}_ingot", "minecraft:iron_ingot", shape(colour, ingot_cells()), f"{en} Ingot", f"Lingote de {pt}")
        self.item(f"{mat}_nugget", "minecraft:iron_nugget", shape(colour, nugget_cells(), light=1.3), f"{en} Nugget", f"Pepita de {pt}")
        self.block(f"{mat}_block", "minecraft:iron_block", storage(colour), f"Block of {en}", f"Bloco de {pt}")
        self.tag("item", f"c:ingots/{mat}", self.id(f"{mat}_ingot"))
        self.tag("item", f"c:nuggets/{mat}", self.id(f"{mat}_nugget"))
        self.tag("item", f"c:storage_blocks/{mat}", self.id(f"{mat}_block"))
        self.tag("block", f"c:storage_blocks/{mat}", self.id(f"{mat}_block"))
        if beacon:
            self.tag("block", "minecraft:beacon_base_blocks", self.id(f"{mat}_block"))
        self.pack(self.id(f"{mat}_nugget"), self.id(f"{mat}_ingot"), f"{mat}_ingot_nugget")
        self.pack(self.id(f"{mat}_ingot"), self.id(f"{mat}_block"), f"{mat}_block_ingot")

    def parts(self, mat, colour, en, pt, ingot_id, hammer, dust_source=None):
        seed = sum(map(ord, mat))
        self.item(f"{mat}_dust", "minecraft:gunpowder", dust_px(colour, seed), f"{en} Dust", f"Pó de {pt}")
        self.item(f"{mat}_plate", "minecraft:iron_ingot", shape(colour, plate_cells(), light=1.3), f"{en} Plate", f"Placa de {pt}")
        self.item(f"{mat}_gear", "minecraft:iron_ingot", shape(colour, gear_cells()), f"{en} Gear", f"Engrenagem de {pt}")
        self.item(f"{mat}_rod", "minecraft:iron_ingot", shape(colour, rod_cells(), light=1.3), f"{en} Rod", f"Haste de {pt}")
        for part in ("dust", "plate", "gear", "rod"):
            self.tag("item", f"c:{part}s/{mat}", self.id(f"{mat}_{part}"))
        self.cook(f"{mat}_ingot_from_dust", self.id(f"{mat}_dust"), ingot_id, 0.3)
        self.recipe(f"hammer/{mat}_plate", {"type": "minecraft:crafting_shapeless", "ingredients": [hammer, ingot_id],
                                            "result": {"id": self.id(f"{mat}_plate")}})
        self.recipe(f"gear/{mat}_gear", {"type": "minecraft:crafting_shaped", "key": {"P": self.id(f"{mat}_plate"), "I": ingot_id},
                                         "pattern": [" P ", "PIP", " P "], "result": {"id": self.id(f"{mat}_gear")}})
        self.recipe(f"rod/{mat}_rod", {"type": "minecraft:crafting_shaped", "key": {"I": ingot_id}, "pattern": ["I", "I"],
                                       "result": {"count": 4, "id": self.id(f"{mat}_rod")}})
        if dust_source:
            self.recipe(f"hammer/{mat}_dust", {"type": "minecraft:crafting_shapeless", "ingredients": [hammer, dust_source],
                                               "result": {"count": 2, "id": self.id(f"{mat}_dust")}})

    def ore(self, name, mat, colour, base, template, drop, tier, en, pt):
        self.block(name, template, ore(colour, sum(map(ord, name)), base), en, pt, drop=ore_drop(self.id(name), drop), tier=tier)
        self.tag("block", f"c:ores/{mat}", self.id(name))
        self.tag("item", f"c:ores/{mat}", self.id(name))
        self.tag("block", "c:ores", self.id(name))

    def feature(self, mat, targets, biomes):
        """One ore feature per vein of the material's entry in config.json (count 0 leaves it out)."""
        ns = self.ns
        names = []
        for i, vein in enumerate(veins(ns, mat)):
            if vein["count"] <= 0:
                continue
            name = f"ore_{mat}" if i == 0 else f"ore_{mat}_{i + 1}"
            names.append(f"{ns}:{name}")
            self.put(f"data/{ns}/worldgen/feature/{name}.json", {
                "type": "minecraft:ore", "discard_chance_on_air_exposure": 0.0, "size": vein["size"],
                "targets": [{"state": self.id(block), "target": rule} for block, rule in targets]})
            self.put(f"data/{ns}/worldgen/placed_feature/{name}.json", {
                "feature": f"{ns}:{name}",
                "placement": [
                    {"type": "minecraft:count", "count": vein["count"]},
                    {"type": "minecraft:in_square"},
                    {"type": "minecraft:height_range", "height": {"type": f"minecraft:{vein['shape']}",
                        "max_inclusive": {"absolute": vein["max_y"]}, "min_inclusive": {"absolute": vein["min_y"]}}},
                    {"type": "minecraft:biome"},
                ]})
        if names:
            self.put(f"data/{ns}/neoforge/biome_modifier/ore_{mat}.json", {
                "type": "neoforge:add_features", "biomes": biomes, "features": names, "step": "underground_ores"})

    def write(self, out, manifest, tab_icon, tab_title):
        ns = self.ns
        for name, value in self.recipes.items():
            self.put(f"data/{ns}/recipe/{name}.json", value)
        for (registry, name), values in self.tags.items():
            tns, path = name.split(":")
            self.put(f"data/{tns}/tags/{registry}/{path}.json", {"values": sorted(set(values))})
        self.put(f"data/{ns}/horizon/creative_tab/main.json", {"title": tab_title, "icon": self.id(tab_icon), "items": [self.id(i) for i in self.items]})
        self.put(f"assets/{ns}/lang/en_us.json", dict(sorted(self.lang_en.items())))
        self.put(f"assets/{ns}/lang/pt_br.json", dict(sorted(self.lang_pt.items())))
        out = Path(out)
        if out.exists():
            shutil.rmtree(out)
        for path, value in self.files.items():
            target = out / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(value, bytes):
                target.write_bytes(value)
            else:
                target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        (out / "horizon-mod.toml").write_text(manifest)
        print(f"{ns}: {len(self.blocks)} blocks, {len(self.items)} items, {len(self.recipes)} recipes, {len(self.files) + 1} files")


def tag_match(tag):
    return {"predicate_type": "minecraft:tag_match", "tag": tag}


def self_drop(block):
    return {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
            "entries": [{"type": "minecraft:item", "name": block}], "rolls": 1}]}


def ore_drop(block, drop):
    return {"type": "minecraft:block", "pools": [{"entries": [{"type": "minecraft:alternatives", "children": [
        {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": block},
        {"type": "minecraft:item", "modifier": [
            {"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
            {"type": "minecraft:explosion_decay"}], "name": drop},
    ]}], "rolls": 1}]}


# ---- config.json: ore generation, editable without touching this file ---------

CONFIG = Path(__file__).resolve().parent.parent / "config.json"
CONFIG_INFO = ("Ore veins per material. Each vein: count (veins per chunk, 0 turns it off), size (blocks per vein), "
               "min_y/max_y, shape (trapezoid: most in the middle; uniform: even). Edit, then run apply.sh and restart the game. "
               "Only new chunks get the change.")
_config = None


def vein(count, size, lo, hi, shape="trapezoid"):
    return {"count": count, "size": size, "min_y": lo, "max_y": hi, "shape": shape}


def default_veins():
    out = {"vastores": {}, "vastdepths": {}}
    for mat, _, _, (count, size, lo, hi, shape), *_ in ORES:
        if mat == "iridium":
            out["vastores"][mat] = [vein(4, 5, -64, -16, "uniform")]
        else:
            # The second vein stands in for the mining dimension: more ore deep down, below y 0.
            out["vastores"][mat] = [vein(count, size, lo, hi, shape), vein(count, size + 3, -64, 0, "uniform")]
    for mat, _, (count, size, lo, hi, shape), *_ in GEMS:
        out["vastores"][mat] = [vein(count, size, lo, hi, shape), vein(3, 6, -64, 0, "uniform")]
    out["vastdepths"]["stellarite"] = [vein(5, 6, -64, -32, "uniform")]
    out["vastdepths"]["infernium"] = [vein(3, 4, 8, 40, "uniform")]
    out["vastdepths"]["voidium"] = [vein(3, 4, 10, 80, "uniform")]
    return out


def veins(ns, mat):
    """The material's veins from config.json; materials it doesn't list get the defaults, written back."""
    global _config
    if _config is None:
        _config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
        changed = not CONFIG.exists()
        for mod, materials in default_veins().items():
            for name, value in materials.items():
                if name not in _config.setdefault(mod, {}):
                    _config[mod][name] = value
                    changed = True
        _config["_info"] = CONFIG_INFO
        if changed:
            CONFIG.write_text(json.dumps(_config, indent=2, ensure_ascii=False) + "\n")
    return _config[ns][mat]


def manifest(mod_id, name, description, version="0.2.0"):
    return (f'id = "{mod_id}"\nname = "{name}"\nversion = "{version}"\ndescription = "{description}"\n'
            'authors = ["voltzz900"]\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n')


# ---- Vast Ores ---------------------------------------------------------------

def vastores(out):
    m = Mod("vastores")
    hammer = m.id("ore_hammer")
    # The hammer crushes a raw ore into two dusts and flattens an ingot into a plate; it isn't used up.
    m.item("ore_hammer", "minecraft:stick", hammer_px(), "Ore Hammer", "Martelo de Minério", handheld=True,
           max_stack_size=1, crafting_remainder=hammer)
    m.recipe("ore_hammer", {"type": "minecraft:crafting_shaped", "key": {"I": "minecraft:iron_ingot", "S": "minecraft:stick"},
                            "pattern": [" II", " SI", "S  "], "result": {"id": hammer}})
    stone = tag_match("minecraft:stone_ore_replaceables")
    deep = tag_match("minecraft:deepslate_ore_replaceables")

    def ore_pair(mat, colour, tier, gen, en, pt, drop):
        tiers = [f"minecraft:needs_{tier}_tool"] if tier != "stone" else ["minecraft:needs_stone_tool"]
        m.ore(f"{mat}_ore", mat, colour, "stone", "minecraft:iron_ore", drop, tiers, f"{en} Ore", f"Minério de {pt}")
        m.ore(f"deepslate_{mat}_ore", mat, colour, "deepslate", "minecraft:deepslate_iron_ore", drop, tiers,
              f"Deepslate {en} Ore", f"Minério de {pt} de Ardósia Profunda")
        m.feature(mat, [(f"{mat}_ore", stone), (f"deepslate_{mat}_ore", deep)], "#minecraft:is_overworld")

    for mat, colour, tier, gen, en, pt in ORES:
        seed = sum(map(ord, mat))
        m.ingot_family(mat, colour, en, pt)
        m.item(f"raw_{mat}", "minecraft:raw_iron", shape(colour, raw_cells(seed), light=1.2, dark=0.7), f"Raw {en}", f"{pt} Bruto")
        m.block(f"raw_{mat}_block", "minecraft:raw_iron_block", raw_block(colour, seed), f"Block of Raw {en}", f"Bloco de {pt} Bruto")
        m.tag("item", f"c:raw_materials/{mat}", m.id(f"raw_{mat}"))
        m.pack(m.id(f"raw_{mat}"), m.id(f"raw_{mat}_block"), f"raw_{mat}_block")
        ore_pair(mat, colour, tier, gen, en, pt, m.id(f"raw_{mat}"))
        for source in (f"{mat}_ore", f"deepslate_{mat}_ore", f"raw_{mat}"):
            m.cook(f"{mat}_ingot_from_{source}", m.id(source), m.id(f"{mat}_ingot"), 0.7 if source.startswith("raw") else 1.0)
        m.parts(mat, colour, en, pt, m.id(f"{mat}_ingot"), hammer, dust_source=m.id(f"raw_{mat}"))

    for mat, colour, gen, en, pt in GEMS:
        m.item(mat, "minecraft:diamond", gem_px(colour), en, pt)
        m.block(f"{mat}_block", "minecraft:diamond_block", storage(colour), f"Block of {en}", f"Bloco de {pt}")
        m.tag("item", f"c:gems/{mat}", m.id(mat))
        m.tag("block", "minecraft:beacon_base_blocks", m.id(f"{mat}_block"))
        m.pack(m.id(mat), m.id(f"{mat}_block"), f"{mat}_block")
        ore_pair(mat, colour, "iron", gen, en, pt, m.id(mat))
        for source in (f"{mat}_ore", f"deepslate_{mat}_ore"):
            m.cook(f"{mat}_from_{source}", m.id(source), m.id(mat), 1.0)
        m.item(f"{mat}_dust", "minecraft:gunpowder", dust_px(colour, sum(map(ord, mat))), f"{en} Dust", f"Pó de {pt}")
        m.recipe(f"hammer/{mat}_dust", {"type": "minecraft:crafting_shapeless", "ingredients": [hammer, m.id(mat)],
                                        "result": {"id": m.id(f"{mat}_dust")}})

    for mat, colour, en, pt in VANILLA:
        m.parts(mat, colour, en, pt, f"minecraft:{mat}_ingot", hammer, dust_source=f"minecraft:raw_{mat}")

    for mat, colour, (inputs, count), en, pt in ALLOYS:
        m.ingot_family(mat, colour, en, pt)
        m.parts(mat, colour, en, pt, m.id(f"{mat}_ingot"), hammer)
        ingredients = [i if i.startswith("minecraft:") else m.id(f"{i}_dust") for i in inputs]
        m.recipe(f"alloy/{mat}_dust", {"type": "minecraft:crafting_shapeless", "ingredients": ingredients,
                                       "result": {"count": count, "id": m.id(f"{mat}_dust")}})

    m.write(out, manifest("vastores", "Vast Ores",
                          "Ten metals, three gems and nine alloys, with dusts, plates, gears, rods and an ore hammer."),
            "tin_ingot", "Vast Ores")


# ---- Vast Depths ------------------------------------------------------------

def vastdepths(out):
    m = Mod("vastdepths")
    hammer = "vastores:ore_hammer"
    targets = {
        "overworld": ("deepslate_ore_replaceables", "#minecraft:is_overworld", "minecraft:deepslate_diamond_ore"),
        "nether": ("base_stone_nether", "#minecraft:is_nether", "minecraft:ancient_debris"),
        "end": (None, "#minecraft:is_end", "minecraft:ancient_debris"),
    }
    # Each tier mines the next: netherite mines stellarite, stellarite infernium, infernium voidium.
    below = {"stellarite": [], "infernium": [], "voidium": ["stellarite"]}
    for mat, colour, base, dim, gen, en, pt, speed, _durability in SUPER:
        seed = sum(map(ord, mat))
        m.ingot_family(mat, colour, en, pt)
        m.item(f"raw_{mat}", "minecraft:raw_gold", shape(colour, raw_cells(seed), light=1.2, dark=0.7), f"Raw {en}", f"{pt} Bruto")
        m.block(f"raw_{mat}_block", "minecraft:raw_gold_block", raw_block(colour, seed), f"Block of Raw {en}", f"Bloco de {pt} Bruto")
        m.tag("item", f"c:raw_materials/{mat}", m.id(f"raw_{mat}"))
        m.pack(m.id(f"raw_{mat}"), m.id(f"raw_{mat}_block"), f"raw_{mat}_block")
        replace, biomes, template = targets[dim]
        tiers = ["minecraft:needs_diamond_tool", "minecraft:incorrect_for_diamond_tool"]
        if mat != "stellarite":
            tiers.append("minecraft:incorrect_for_netherite_tool")
        tiers += [f"vastdepths:incorrect_for_{t}_tool" for t in below[mat]]
        name = f"{mat}_ore"
        m.ore(name, mat, colour, base, template, m.id(f"raw_{mat}"), tiers, f"{en} Ore", f"Minério de {pt}")
        rule = tag_match(f"minecraft:{replace}") if replace else {"predicate_type": "minecraft:block_match", "block": "minecraft:end_stone"}
        m.feature(mat, [(name, rule)], biomes)
        for source in (name, f"raw_{mat}"):
            m.cook(f"{mat}_ingot_from_{source}", m.id(source), m.id(f"{mat}_ingot"), 2.0)
        m.parts(mat, colour, en, pt, m.id(f"{mat}_ingot"), hammer, dust_source=m.id(f"raw_{mat}"))
        # Tools: our own mining tier, speed and attack; unbreakable, as end-game gear is.
        deny = f"#vastdepths:incorrect_for_{mat}_tool"
        for kind, mine, pt_kind in (("pickaxe", "#minecraft:mineable/pickaxe", "Picareta"), ("axe", "#minecraft:mineable/axe", "Machado"),
                                    ("shovel", "#minecraft:mineable/shovel", "Pá"), ("sword", None, "Espada")):
            damage, attack_speed = TOOL_STATS[mat][kind]
            components = {"minecraft:unbreakable": {}, "!minecraft:repairable": {},
                          "minecraft:attribute_modifiers": [
                              {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage",
                               "amount": damage, "operation": "add_value", "slot": "mainhand"},
                              {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed",
                               "amount": attack_speed, "operation": "add_value", "slot": "mainhand"}]}
            if mine:
                components["minecraft:tool"] = {"rules": [
                    {"blocks": deny, "correct_for_drops": False},
                    {"blocks": mine, "correct_for_drops": True, "speed": speed}], "damage_per_block": 1}
            # The player's own iron tool texture, tinted whole (head and handle) in the metal's colour.
            m.item(f"{mat}_{kind}", f"minecraft:netherite_{kind}", None, f"{en} {kind.title()}", f"{pt_kind} de {pt}",
                   handheld=True, texture=f"minecraft:item/iron_{kind}", tint=colour, components=components)
            shapes = {"pickaxe": ["III", " S ", " S "], "axe": ["II", "IS", " S"], "shovel": ["I", "S", "S"], "sword": ["I", "I", "S"]}
            m.recipe(f"tool/{mat}_{kind}", {"type": "minecraft:crafting_shaped", "key": {"I": m.id(f"{mat}_ingot"), "S": "minecraft:blaze_rod"},
                                            "pattern": shapes[kind], "result": {"id": m.id(f"{mat}_{kind}")}})
            m.tag("item", f"minecraft:{kind}s" if kind != "sword" else "minecraft:swords", m.id(f"{mat}_{kind}"))
        m.put(f"data/vastdepths/tags/block/incorrect_for_{mat}_tool.json", {"values": []})

        # Armour: the game's own iron armour, worn and in the hand, tinted in the metal's colour through a
        # dyeable equipment layer (undyed, it takes `color_when_undyed`). Unbreakable too.
        layer = [{"texture": "minecraft:iron", "dyeable": {"color_when_undyed": (0xFF000000 | colour) - (1 << 32)}}]  # a signed ARGB int
        m.put(f"assets/vastdepths/equipment/{mat}.json", {"layers": {"humanoid": layer, "humanoid_leggings": layer}})
        points, toughness, knockback = ARMOR_STATS[mat]
        pieces = (("helmet", "head", "Helmet", "Capacete", ["III", "I I"], "head_armor"),
                  ("chestplate", "chest", "Chestplate", "Peitoral", ["I I", "III", "III"], "chest_armor"),
                  ("leggings", "legs", "Leggings", "Calças", ["III", "I I", "I I"], "leg_armor"),
                  ("boots", "feet", "Boots", "Botas", ["I I", "I I"], "foot_armor"))
        for (piece, slot, en_piece, pt_piece, pattern, tag), armor in zip(pieces, points):
            def modifier(kind, amount):
                return {"type": f"minecraft:{kind}", "id": f"minecraft:armor.{piece}", "amount": amount,
                        "operation": "add_value", "slot": slot}
            components = {
                "minecraft:unbreakable": {}, "!minecraft:repairable": {},
                "minecraft:equippable": {"slot": slot, "asset_id": m.id(mat),
                                         "equip_sound": "minecraft:item.armor.equip_netherite"},
                "minecraft:attribute_modifiers": [modifier("armor", float(armor)),
                                                  modifier("armor_toughness", toughness),
                                                  modifier("knockback_resistance", knockback)],
            }
            m.item(f"{mat}_{piece}", f"minecraft:netherite_{piece}", None, f"{en} {en_piece}", f"{pt_piece} de {pt}",
                   texture=f"minecraft:item/iron_{piece}", tint=colour, components=components)
            m.recipe(f"armor/{mat}_{piece}", {"type": "minecraft:crafting_shaped", "key": {"I": m.id(f"{mat}_ingot")},
                                             "pattern": pattern, "result": {"id": m.id(f"{mat}_{piece}")}})
            m.tag("item", f"minecraft:{tag}", m.id(f"{mat}_{piece}"))

    for mat, colour, (a, b), en, pt in SUPER_ALLOYS:
        m.ingot_family(mat, colour, en, pt, beacon=False)
        m.recipe(f"alloy/{mat}_ingot", {"type": "minecraft:crafting_shapeless",
                                        "ingredients": [m.id(f"{a}_ingot"), m.id(f"{b}_ingot"), "minecraft:netherite_ingot"],
                                        "result": {"count": 2, "id": m.id(f"{mat}_ingot")}})

    m.write(out, manifest("vastdepths", "Vast Depths",
                          "Stellarite, infernium and voidium: three end-game metals from the deep overworld, the Nether and the End, with their tools and alloys. Needs Vast Ores.",
                          version="0.3.0"),
            "stellarite_ingot", "Vast Depths")


if __name__ == "__main__":
    root = Path(sys.argv[1])
    vastores(root / "vastores")
    vastdepths(root / "vastdepths")
