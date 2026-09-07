# Rare Ultrasuede® LT / Light colours — hunt results

Compiled 2026-09-06; the picture hunt below extended 2026-09-07, and a last
sweep the same day closed it. Everything here is sourced from archived Field's
Fabrics catalogues and colour-list pages — except the ten photographs in *The
pictures Field's still serves*, which are files still on Field's own server.
Raw evidence is saved alongside this file.

## Answers to the four names asked about

| Name asked | Verdict | Line | Code |
|---|---|---|---|
| **Active green** | **CONFIRMED in Light** | Ultrasuede® Light, 58" Extrawide | **#4599** |
| **Sherbert orange** | **CONFIRMED in Light**, as "Orange Sherbet" | Ultrasuede® Light, 58" | **#8281** |
| **Carrot** | Found, but **ST only** — no Light evidence | Ultrasuede® ST | #8169 (45") → #8325 (58") |
| **Mango** | Found, but **ST only** — no Light evidence | Ultrasuede® ST | #6595 (45") → #6678 (58") |

### Active Green #4599 — the key find

Field's sold **two different Active Greens at the same time**, and the two codes
are what separate them:

- **#4599 Active Green — Ultrasuede® LIGHT, 58" Extrawide**
- #4598 Active Green — Ultrasuede® Soft / ST, 45" (later restyled 58" as #4686)

Both appear *in the same document*, in different sections — which is what makes
this conclusive rather than a transcription slip.

Evidence (four independent captures):

1. `ultra_list_0107.pdf` (Field's catalogue, Jan 2007) — `#4599 Active Green`
   under **"ULTRASUEDE® LIGHT Solids – 58" Wide"**; `#4598 Active Green` under
   "Soft cont." on the same sheet.
   → `fields_catalogs/ultra_0107.pdf`
2. `wide_list.htm` captured **2006-12-07**, page titled
   *"Field's Fabrics – Ultrasuede Light Extrawide"*.
3. same page captured **2007-03-17**
4. same page captured **2007-04-03**
   → `fields_oldsite/wide_list_2006*.html`, `wide_list_2007*.html`

No swatch photograph of #4599 was ever archived (checked
`/ultra/swatches/thumb/4599.*` and `/ultra/shopping/4599.htm` — neither exists
in the Wayback index).

**But #4598 is photographed, and it is on the page as Active Green's swatch.**
Field's still serves the Soft/ST one at
`shop.fieldsfabrics.com/assets/images/ultrasuede/4598.jpg`, and the January 2007
sheet that prints the two numbers in adjacent sections is what licenses using
it: same colour, different cloth. The entry carries a `based_on` block naming
the weight, the number and that sheet, and the panel says *"This swatch is based
on the ST version."* under the source. See *The pictures Field's still serves*
below.

*Note when re-checking these files:* a plain `grep 4599` over the raw HTML finds
nothing — the code is broken across tags in the source. Strip the tags first
(as `fields_oldsite/old_alltext.txt` already does) and it is there.

### Orange Sherbet #8281

- **#8281 Orange Sherbet — Ultrasuede® LIGHT 58"**, in the Feb 2010 catalogue
  (`fields_catalogs/ultra_0210.pdf`, "ULTRASUEDE® LIGHT Solids 58" Wide").
- #8280 Orange Sherbet — Ultrasuede® Soft, same sheet.
- The Aug 2008 catalogue spells the Soft one **"Orange Shebert"** — which is
  likely where the "sherbert" spelling you'd heard comes from.
  (`fields_catalogs/ultra_0808.pdf`, a scan; rendered to `u0808.png`.)

### Carrot and Mango

Both are real Field's colours, but every source found puts them in **ST/Soft**,
never Light:

- Carrot: #8169 (ST 45", "Custom Color") → #8325 (ST 58", 30% plant-based)
- Mango: #6595 (ST 45", "Custom Color") → #6678 (ST 58")

Checked without a hit: all nine Field's catalogues 2005–2010, all 108 archived
Light/Extrawide/Specials list pages 2002–2010, the 2020/2021/2023 swatch-set
catalogues, Field's full live product index (8,809 products), and every
Field's URL Wayback ever recorded containing "Ultrasuede" (599 URLs).

**Unproven lead:** Light and Soft versions of one colour were numbered
adjacently (4599/4598 Active Green, 8281/8280 Orange Sherbet, and 8276/8275
Burnt Orange, found later). If Light Carrot or Light Mango ever existed,
#8168/#8170 and #6594/#6596 are where to look. This is a pattern-based guess,
not evidence — but the adjacency itself is now doing work, because it is what
licenses showing a Light colour with the Soft one's photograph. See *The
pictures Field's still serves*.

## Bonus: a 14th Field's LT custom colour

**Ultrasuede® LT (Light) Extrawide #100 "LT Blue"** — still live on Field's site,
marked Sold Out, Part Number 100, image `assets/images/100lightblue.jpg`.
Not in `lt.json`. → `fields_live/ltblue.html`, swatch saved as
`images/100_lt_blue.jpg` (300×300, the live product photograph).

## Bonus: 70 Ultrasuede Light colours absent from lt.json

`new_light_colors.json` holds the full machine-readable list with per-colour
capture timestamps. These come from the pre-2011 era, when Field's carried a far
wider Light range (45" and 58" Extrawide) than the 36 Toray ever listed on its
own site — which is where the 2001 claim of *"40 high-fashion colors"* likely
went.

Two caveats on that list:

- **#5832 White** is not new — `lt.json` already records it as White's pre-2010
  SKU. It surfaces here because it is stored as a `former_sku` rather than a code.
- Names are transcribed as printed, including Field's own typos
  ("Eclispe" for Eclipse, "Bourdeax" for Bordeaux).

Colours excluded on inspection: entries under the "55" Milano Upholstery weight"
subsection of the Extrawide page (Azure Blue #4011, Raspberry #7565,
Sandlewood #4083, Oriental Teal #6502, Misty Spruce #4118, New Jade #4229,
Aqualine #4600) are Milano HP, not Light.

## Where this ended up

All of it is now in `lt.json` and on the page, rebuilt by
`python3 scraping/build_dataset.py` and checked by `python3 scraping/verify.py`
(which re-reads the saved captures rather than trusting the builder):

- **69 pre-2011 colours** — 70 minus White #5832, which is White's own pre-2010
  SKU and was already in `colors` as a `former_sku`. They are split by whether a
  picture of them survives (see *The scans* below): 56 are in `custom_colors`
  marked `custom_basis: predates_official_record`, and the 13 with nothing to
  show are in `historical_colors`, under a section headed *Missing image* —
  which is a section about the entries, not about the file. Entries there get no
  swatch well, because there is no swatch: each carries its number, the widths it
  was sold at, and a linked list of every capture it was seen in. Bobcat #177-231
  was in there too until the last sweep found Field's own scan of it — see *The
  pictures Field's still serves*.
- **LT Blue #100** — in `custom_colors` with the live swatch photograph
  (`images/fields/100.jpg`) and ten archived captures of its product page,
  2019-07-24 → 2026-06-12, every one of them already marked Sold Out. It is
  kept in the file but left off the page (`on_page: false`, with the reason in
  `off_page_reason`): Field's is the only source for it, the picture is a
  product photograph rather than a swatch capture, and it is close enough to
  #2424 Lt. Blue that showing the two invites a reading of a difference that is
  really sixteen years of different photography.
- **Two names, twice each.** #2894 Imperial Blue is on the old lists and in
  every catalogue; #2694 Imperial Blue is on the shop that replaced them. Same
  for #2424 Lt. Blue and #100 LT Blue. Each number is printed consistently in
  its own era and nothing says whether a colour was renumbered or two colours
  were given one name, so neither is corrected and the pairs carry a `see_also`
  at each other. The scans settled one of them: #2894 is a pale periwinkle
  (`#d0d9f5`) and #2694 is a deep navy (`#1e1f4a`), so those are two colours
  sharing a name. The two Light Blues (`#7c8c9d`, `#8d8490`) are close enough
  that sixteen years of different photography could account for the gap.

## Bonus: what the Jungle colour numbers mean

Toray's Light Jungle page gives each print a pattern number and a colour
number — *"Pattern: 181  Color: 023"* — and never says what either is. The
colour number is the **ink combination**, not a serial for the print: ten
numbers cover the seventeen entries, 023 is on six of them and 231 on three,
and a pattern sold in two colourways is one drawing run in two sets of inks.

Field's Fabrics printed the combination beside the number, which is what
settles it:

| Colour | Named | Where |
|---|---|---|
| **023** | Cream/Black | 9 catalogue issues, under four different pattern numbers (173, 176, 177, 181) — and the swatch-set list |
| **231** | Tan/Black | swatch-set list, 2020-03 and current: *"176-231-58 Jaguar Tan/Black"* |
| **232** | Cream/Brown | 5 catalogue issues: *"#173-232-58 Small Pony Cream/Brown"* |

One number named the same way under four pattern numbers is the number meaning
the combination rather than the print. Nothing archived here names the other
seven, so those are read off the swatch photographs and marked
`name_source: estimated`: 017 Cream/Taupe, 154 Tan/Rust/Black, 210
Cream/Tan/Black, 227 Beige/Brown, 228 Gold/Black, 229 Gold/Brown, 241
Mauve/Charcoal.

The hexes come from the photographs either way. k-means in CIELAB, then each
cluster reports the median of its **eroded core** — the middle of a region with
the blend along its own boundary cut away, which is where a plain cluster mean
goes wrong on a print. Erosion also settles how many inks there are: ask for
one cluster more than the print has and k-means splits off the blend shell,
which is an outline around everything and has no core at all. Real inks keep
10–87% of themselves under erosion here and spurious ones keep 0–3%, so the
count stops where a cluster loses its core. Fourteen prints read as two inks;
Leopard 210 and Ocelot 154 read as three, which is what the eye reads off them
(a tan fill inside a black outline on cream).

A colourway printed on several patterns takes the median across all of them —
which is what gives **Bobcat 177-231** its palette. Toray never photographed it,
and although Field's did (below), that scan is shown rather than measured: their
logo sits across the middle and clusters as a third ink no other 231 print has,
and the scan's tan reads `#c68f4c` against `#b48e52` and `#b89153` on Toray's
two, which is a different generation of photography rather than a different
ink. Reading it in would have moved Jaguar's and Baby Cougar's published hexes
for nothing. So 231 stays read off those two — the same two inks there — and the
picture is Field's while the numbers are Toray's. Ocelot 154 is the one palette
read off a reference photograph rather than an archived capture, and says so
(`hex_source: reference_photo`).

All of it is in `lt.json` under each pattern's `colorway`. The page is
narrower on purpose: a print's panel shows the combination — the name, then a
hex for each ink — only for the three Field's named. The other seven stay in
the file, marked `name_source: estimated`, rather than standing on the page
where a record should be.

## The scans

Field's old list pages hung a swatch scan off every colour number — *"Click on
color number to see a swatch"* — at `/swatches/<number>.jpg`, with a
postage-stamp copy under `/swatches/thumb/`. The Wayback Machine kept 47 of the
69, and Field's own live site turned out to still hold nine more (see below):

| | |
|---|---|
| full scans, ~400px | 41 |
| thumbnail only, ~100px | 6 (#3800, #3835, #7000, #8200, #9270, #9364) |
| still on Field's live site | 9 |
| nothing at any size | 13 |

Each is a square of cloth on a scanner with Field's logo dropped in white across
the middle. `scraping/plan_old_swatches.py` picks the capture closest in time to
the page capture that linked it — a filename Field's reused would otherwise give
the wrong colour — and `scraping/crop_old_swatches.py` cuts the paper off and
pulls the frame 12% inside the cut edge. The colour is read from the four
corners, well clear of the logo. The six thumbnails are cropped into
`research/swatches_cropped/`, which is the file the colour is read off, and a
squared copy of each is published beside the full scans. Sixty pixels of cloth
with Field's logo across the middle is a poor photograph and the only one these
six will ever have, so the panel shows it and the shader still opens first.

## The pictures Field's still serves

Twenty-two colours came out of that hunt with nothing to show. Nine of them do
have a photograph — it just is not in any archive, and neither is the tenth
picture here, of the one Light Jungle print Toray never captured. Field's leaves
swatch photography in `shop.fieldsfabrics.com/assets/images/ultrasuede/` long after the
product is gone, and the file is still served under the colour number even where
the page it belonged to is not in the Wayback index at all. That is where
`/ultra/shopping/<number>.htm` pointed all along; the archive kept the page for
thirteen of these and the image for none of them.

**Seven under their own Light number** — these are simply their photographs:

| | | |
|---|---|---|
| #2805 | Cobalt | `#282d86` |
| #3968 | Summer Brown 54 | `#563c23` |
| #6647 | Sangria | `#630d2b` |
| #7369S | Aqua 58 | `#62abb1` |
| #8281 | Orange Sherbet | `#f16b07` |
| #9378 | Purple Shadow | `#5d4a60` |
| #9464 | Royal Purple | `#4e2c5f` |

**One under a pattern number** — Bobcat #177-231, the Light Jungle colourway
Toray never captured, at `.../ultrasuede/177-231.jpg`. Field's scan of #177-023
beside it is what identifies the drawing: the two show the same large solid
rounded spots, against the open rosettes of Jaguar 176 and Baby Cougar 181, at
the same coarser magnification Field's scanned everything at. It goes to
`images/jungle/bobca231.jpg` with `image_provenance: fields_live`, and is shown
without being measured — see *what the Jungle colour numbers mean* above.

**Two under another weight's number** — the same colour in a different cloth,
which the panel says outright:

| Light | shown from | weight | the sheet that pairs them |
|---|---|---|---|
| #4599 Active Green | #4598 | ST | `ultra_0107.pdf`, Light Solids 58" and Soft |
| #8276 Burnt Orange | #8275 | ST | `ultra_0210.pdf`, Light and Soft |

A shared name is not enough for the second kind: both numbers have to be printed
against the name on one Field's sheet, in sections for the two weights, which is
what `verify.py` re-checks against the catalogue text. Every candidate that
rested on a name alone was dropped — #2708 Sky Blue against ST 8023-2908, and
#5837 White – Extra-supple against Soft 001, are both real photographs of a
colour of that name, and neither has a document tying it to the Light number.
#4619 Green Glass has a file under its own number — 600px, re-fetched in the
last sweep — that is a flat neutral grey (`#b0b0ae` at all four corners, no
green cast at any of them), so it is read as a different product and left out.

Two generations of photograph live in that folder: 600px with the *Field's
Fabrics Online Store* watermark, and ~100px flatbed scans with the older script
logo — the same scans the old list pages linked, which is why #9378 arrived with
scanner paper still around it and goes through the same crop as the archived
ones. All are read from the four corners, clear of the logo. Fetched and cropped
by `scraping/fetch_live_swatches.py`, recorded in
`research/live_swatch_images.json`.

None of this says Field's had these colours made. Toray's own record does not
start until 2005 and Field's was selling Light from 2002, so absence from the
36 cannot tell a colour Field's commissioned from an early official colour Toray
dropped before it had a website to drop it from — which is why they are marked
`predates_official_record` rather than claiming `exclusive_to`.

## The last sweep, and where it stops

One more pass over every place a picture of the remaining nineteen could be —
the thirteen in *Missing image* and the six known only from a ~100px thumbnail.
It found the Bobcat print above and nothing else, and what it ruled out is worth
keeping, because it is what makes "there is no picture" a finding rather than a
shrug.

| where | what was asked | result |
|---|---|---|
| Field's live server | 304 URLs: every one of the 19 numbers × `<n>.jpg`, `.gif`, `.png`, `<n>S`, `<n>s`, `_thumbnail`, `-58`, `lt`, in `assets/images/ultrasuede/` and `assets/images/` | 4619 and 8200 only (below); `7369s` is byte-identical to `7369S` | 
| Field's live server, by name | 608 URLs: the `100lightblue.jpg` shape — number plus name, and six other stems, for all 19 | `blue.jpg`, `royal.jpg`, `cinnamon.jpg` — a batik, a blue mesh and a brown satin, all with a ruler in frame. Field's generic colour-word files, not Ultrasuede |
| Wayback, Field's swatch folders | full CDX of `fieldsfabrics.com/swatches/*` (2,678 rows) and `/ultra/swatches/*` (80) | 179 full scans and 160 thumbnails, none of them one of the 19; the six thumbnail-only ones have a thumb and no full scan, as before |
| Wayback, Field's shop assets | `shop.fieldsfabrics.com/assets/images/ultrasuede*` | 65 numbers, none of the 19 |
| Toray's swatch server | `swatches.ultrasuede.us` is still up, and its `/swatches/images/<style>-<code>.jpg` scheme still serves. `product=LT`, `Light`, `8801` and four spellings besides | only current styles answer — 8023 (ST) does, 8801 (LT), 2223, 5538, 5539 all 404. The LT files are off the live server; the archived 36 are the 36 |
| ultrasuede.com | `products/images/lt_<n>.jpg` and `lt_l_<n>.jpg`, live and archived | the same 36 small and 30 large already held; the domain now redirects wholesale to `ultrasuede.toray` |
| Field's live catalogue | all 8,809 products, and the `ultrasuede-lt`, `ultrasuede-lt-custom` and `ultrasuede` category pages | 261 Ultrasuede products, none of the 19 |

Two of those hits are not pictures of what they are filed under. **#4619 Green
Glass** is discussed above. **#8200 Cinnamon** is on the live server at its own
number, but it is 97×104 — the same dimensions, byte for byte the same file, as
the thumbnail already held. It adds nothing: the thumbnail is the picture, and
there is no better one anywhere.

### Two leads that do not clear the bar

**#6635 Rapture Rose has a pair, and the pair has no photograph.** The March
2008 sheet (`fields_catalogs/ultra_0308.pdf`) prints `#6635 Rapture Rose` under
*ULTRASUEDE® LIGHT Solids 58"* and `#6634 Rapture Rose` under *ULTRASUEDE® SOFT
Solids 45"* — the same two-sections-one-sheet document that licenses #4599 from
#4598 and #8276 from #8275. It is the only new pair a scan of all nine
catalogues turned up for any of the nineteen. But `.../ultrasuede/6634.jpg` does
not exist, and `assets/images/6634.jpg` is a Boston Red Sox cotton print. The
pairing is recorded here; there is nothing to hang on it.

**#5837 White – Extra-supple is probably #5872 under an older number, and
"probably" is not the bar.** Field's Light 58" list carries exactly one
white-extra-supple at a time: #5837 from 2005-03 to 2008-05, then #5872, which
is Toray's own 8801-5872 — and Toray's record has that colour renumbered from
801-**5832**, in the same window. A digit apart from Field's number, on a site
that also prints "Eclispe" and "Bourdeax". Every reading of this is a succession
argument: no sheet anywhere prints 5837 and 5872 together, or 5837 and 5832, so
there is no document pairing the numbers and #5837 keeps its empty panel.

### What that leaves

Thirteen entries with no picture, and six colours whose only picture is a
postage stamp. The archive has been asked for all nineteen under every path
Field's ever used; Field's own server has been asked under every filename shape
that folder contains; Toray never had them. Anything further would have to come
from outside these two companies — a physical sample set, a colour card, a
trade-show binder — not from another query.

## What is saved here

| folder | contents |
|---|---|
| `fields_catalogs/` | 9 Field's Ultrasuede catalogues, 2005-03 → 2010-02, as PDF + extracted text; the 2008 scan also rendered to PNG |
| `fields_sample_sets/` | swatch-set catalogues 2020-03, 2021-03, 2021-10, and the current live one |
| `fields_oldsite/` | 108 archived captures of Field's Light 45" list, Light Extrawide 58" list, and Specials list, 2002-08 → 2010-03, plus extracted text |
| `fields_live/` | current Field's catalogue: full 36-page product index, Ultrasuede category pages, the LT Blue product page |
| `cdx/` | raw Wayback CDX responses — the underlying search record |
| `images/` | LT Blue swatch, from the live site |
| `swatches_archive/` | 47 archived Field's swatch scans, as fetched |
| `swatches_cropped/` | the 6 thumbnail-sized ones, cropped — the file each colour is read off; a squared copy of each is published in `images/fields_old/` |
| `swatches_live/` | the 10 photographs still on Field's own server, as fetched — nine colours and the Bobcat print |
| `fields_shopping/` | Field's `/ultra/shopping/<number>.htm` pages for the colours with no archived scan — where the image URLs came from |
| `fields_otherweights/` | Field's Soft and HP list pages, 2002–2010, for pairing a Light colour with its number in another weight |
| `toray_otherweights/` | Toray's own swatch pages for every other weight — Soft, ST, HP, Ambiance, Elite, Milano, Riviera, Torale, ER, LX, XL, 2005 → 2026 — searched for the same names and, apart from Sky Blue and White, not carrying them |
| `old_swatch_images.json` | which capture each scan came from, and which page capture linked it |
| `live_swatch_images.json` | the 10 live-site photographs: source URL, whether it needed cropping, and for two of them the weight standing in |
| `new_light_colors.json` | the 70 undocumented Light colours, machine-readable |
| `probe_live.json`, `probe_named.json` | the last sweep's 912 live-server probes and what answered |
| `probe_hits/` | every file those probes returned, including the ones read and rejected |
