"""The treasure chest, as plain drawings: no imports, no side effects.

Seen in 3/4 from the front: the lid's lit top, its front, then the box front with two
iron bands and a gold lock plate. Light from the top left. Every drawing is 24 wide and
has its K outline; the box's bottom row is the drawing's last row, so frames line up
when bottom-aligned (pixel.strip does that).

The Mimic imports CHEST_CLOSED to disguise itself, so keep its look in step with the
real chest: same size, same bands, same lock.
"""

# Closed: 24 x 18
CHEST_CLOSED = [
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KSSTLLTTTTTTTTTTTTLLTTK",
    "KSSTTLGTTTTTTTTTTTTLGTTK",
    "KSTTTLGTTTTTTTTTTTTLGTBK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBYYYOBBBBLGBbK",
    "KTBBBLGBBBBYWYOBBBBLGBbK",
    "KKKKKDDKKKKYKYOKKKKDDKKK",
    "KTBBBLGBBBBYKYOBBBBLGBbK",
    "KTBBBLGBBBBOOOOBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]

# Open: 24 x 20. The lid stands up behind the box, showing its shaded inside; the box
# is full of gold.
CHEST_OPEN = [
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KTTTLLTTTTTTTTTTTTLLTbK",
    "KbBBBDGBBBBBBBBBBBBDGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KbBBBDGBBBBBBBBBBBBDGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
    "KTbbbbbYWYbbbbbbYOYbbbBK",
    "KTbOYYOYWYOYYOYOYYWYObbK",
    "KTOYWYYOYYOYOYYWYOYYOYbK",
    "KSSTTLLTTTTTTTTTTTTLLTTK",
    "KTBBBLGBBBBYKYOBBBBLGBbK",
    "KTBBBLGBBBBOOOOBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]

# Trapped: 24 x 18. The closed chest, rigged: a red lock with a bone-white skull
# keyhole, dart holes in the front planks and green venom seeping from the seam.
CHEST_TRAPPED = [
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KSSTLLTTTTTTTTTTTTLLTTK",
    "KSSTTLGTTTTTTTTTTTTLGTTK",
    "KSTTTLGTTTTTTTTTTTTLGTBK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBLGGDBBBBLGBbK",
    "KTBBBLGBBBBGRFDBBBBLGBbK",
    "KKKKKDDKVEKGrRDKKEVDDKKK",
    "KTBBBLGBVBBGKGDBBVBLGBbK",
    "KTBBBLGBEBBDDDDBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBKBLGBKBBBKBBBKBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]

# Opening, frame 2 of 4: 24 x 20. The lid lifted a crack; gold light spills out.
CHEST_LID_CRACKED = [
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KSSTLLTTTTTTTTTTTTLLTTK",
    "KSSTTLGTTTTTTTTTTTTLGTTK",
    "KSTTTLGTTTTTTTTTTTTLGTBK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
    "KOYYOYYYWYYYYYWYYYOYYOOK",
    "KSSTTLLTTTTTTTTTTTTLLTTK",
    "KTBBBLGBBBBYKYOBBBBLGBbK",
    "KTBBBLGBBBBOOOOBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]

# Opening, frame 3 of 4: 24 x 20. The lid swinging up, seen edge-on: a thin lit rim
# over its shaded inside, with the gold showing below.
CHEST_LID_HALF = [
    "........................",
    "..KKKKKKKKKKKKKKKKKKKK..",
    ".KSSTLLTTTTTTTTTTTTLLTTK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KbBBBDGBBBBBBBBBBBBDGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KKKKKKKKKKKKKKKKKKKKKKKK",
    "KTTTTTTTTTTTTTTTTTTTTTBK",
    "KTbOYYOYWYOYYOYOYYWYObbK",
    "KTOYWYYOYYOYOYYWYOYYOYbK",
    "KSSTTLLTTTTTTTTTTTTLLTTK",
    "KTBBBLGBBBBYKYOBBBBLGBbK",
    "KTBBBLGBBBBOOOOBBBBLGBbK",
    "KTBBbLGBBBBBBBBBBBBLGBbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    "KTBBBLGBBBBBBBBBBBBLGBbK",
    "KTBBBLGBBBbBBBBBBBBLGBbK",
    "KBBBBLGBBBBBBBBBbBBLGbbK",
    "KbbbbDDbbbbbbbbbbbbDDbbK",
    ".KKKKKKKKKKKKKKKKKKKKKK.",
]
