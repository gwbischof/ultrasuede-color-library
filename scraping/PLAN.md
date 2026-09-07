# Ultrasuede® LT colour archive — findings & data plan

Working notes for reconstructing the complete official colour record for
Ultrasuede® LT (marketed as Ultrasuede® **Light** before ~2012) from the
Wayback Machine.

**Status: built.** `../lt.json` holds 36 official solid colours,
17 Light Jungle patterns, and 13 Field's Fabrics custom colours.
`python3 verify.py` passes 1,664 offline checks; with `--links` it also HEADs
every distinct archive URL.

Scope decisions taken:

- Light Jungle is included as a **separate `patterns` section**, not merged into
  the solid colours (it is keyed by pattern # + colour #, not by SKU).
- Only the **LT/Light** colour cards are saved; other product lines' cards
  (HP, ST, XL, LX, TS, …) exist in the archive but are out of scope.
- Field's Fabrics custom colours are a **separate `custom_colors` section**,
  with a hard no-overlap rule against the official 36 (see §6).

---

## 1. What the archive actually contains

**36 distinct colours, across the entire archived official record (2005 → 2024).**

The lineup was remarkably stable. Contrary to the assumption that discontinued
colours were dropped over time, no colour was ever removed while LT was active —
the whole line went from 36 to 0 at once when the product was discontinued.

### Timeline

| Date | Source | Colours | Notes |
|---|---|---|---|
| 2005-02-11 / 2005-04-13 | `ultrasuede.com/products/…/swatches/light.html` | **35** | "STYLE #801". No Café. White is SKU **5832**. |
| 2010-12-01 | `ultrasuede.com/swatches/search_result.php?product=Light` | **36** | Now `8801-` SKUs. White is **5872**. Café present. |
| 2010-12-07 | Colour card `ultrasuede_light.pdf` | **36** | "Style: 801" |
| 2016-04-10 → 2024-08-05 | `swatches.ultrasuede.us/…?product=LT` (19 captures) | **36** | Identical set in every capture. |
| 2017-05-19 | Colour card `ultrasuede_lt.pdf` | **36** | "Style: 8801" |
| 2025-12-16, 2026-01-16 | same URL | **0** | "(0 items found)" — product discontinued. |

### The only two changes ever observed

1. **Café (3434)** — absent from the 2005 pages, present from 2010 onward.
   The single colour *addition* in the record.
2. **White** — SKU **5832** on the 2005 pages, **5872** from 2010 onward.
   The single SKU *renumber* in the record. Same colour name and position.

### A secondary signal worth capturing

Ten colours lost their online sample-order button (the `[+]` became
"sample not available") between the 2019-03-12 and 2019-05-12 captures, and
never got it back:

> Café, Rodeo, Dune, Green Grape, Celadon, Petit Pois, Blonde, Opal, Atlantis, Montauk

They stayed *listed* through 2024, so this is not a delisting — but it is the
closest thing in the record to an early "winding down" marker, so it gets its
own field rather than being folded into the last-listed year.

---

## 2. Sources (all to be recorded per colour)

| id | kind | what | captures |
|---|---|---|---|
| `swatches-lt-*` | swatch index | `swatches.ultrasuede.us/swatches/search_result.php?product=LT` | 19 populated (2016-04 → 2024-08) + 2 empty |
| `uscom-light-2010` | swatch index | `ultrasuede.com/swatches/search_result.php?product=Light` | 2010-12-01 |
| `uscom-light-2005` | swatch page | `ultrasuede.com/products/swatches/light.html` (+ `/products/fashion/…`) | 2005-04-13, 2005-02-11 |
| `colorcard-light-2010` | colour card PDF | `ultrasuede.com/b2b_center/color_cards/ultrasuede_light.pdf` | 2010-12-07 |
| `colorcard-lt-2017` | colour card PDF | `ultrasuede.us/resources/b2b_center/color_cards/ultrasuede_lt.pdf` | 2017-05-19 |
| `uscom-lt-product` | product page | `ultrasuede.com/products/lt.html` | 32 captures, 2013 → 2020 |
| `uscom-light-jungle` | swatch page | `ultrasuede.com/products/swatches/light_jungle.html` | 15 captures (6 distinct), 2005-04 → 2009-04 |
| `uscom-light-jungle-fashion-2005` | swatch page | `ultrasuede.com/products/fashion/swatches/light_jungle.html` | 2005-02-11 |
| `uscom-b2b-jungle-light-2001` | swatch page | `ultrasuede.com/b2b/JungleLight.html` | 2001-05-27 |
| `fields-lt-custom` | retailer category | `shop.fieldsfabrics.com/ultrasuede-lt-custom` | 10 populated (2019-07 → 2024-04) + 1 empty |
| `fields-lt` | retailer category | `shop.fieldsfabrics.com/ultrasuede-lt` | 9 populated (2019-07 → 2023-03) |
| `fields-product-<code>` | retailer product | `shop.fieldsfabrics.com/…_p_<id>.html` | 13, one per Field's-only colour |

**Colour card caveat:** `ultrasuede.us/support/pdf/ultrasuede_lt.pdf` (captured
2022-05-28) is *byte-identical* to the 2017 PDF — the crawler truncated its copy
at exactly 1 MiB (`x-crawler-content-length: 1107829`). So there are only **two
distinct card editions**: 2010 (Light, style 801) and 2017 (LT, style 8801),
the latter still being served in 2022. The complete 2017 file is what we keep.

---

## 3. Images

| Source | Size | Coverage |
|---|---|---|
| `swatches.ultrasuede.us/swatches/images/8801-XXXX.jpg` | 100×100 | **36 / 36** |
| `ultrasuede.com/products/images/lt_l_XXXX.jpg` | 418×418 | **30 / 36** |
| `ultrasuede.com/products/images/lt_XXXX.jpg` | 100×100 | 36 / 36 (same bytes as the first) |
| `swatches.ultrasuede.us/swatches/images_enlarged_view/8801-XXXX.jpg` | large | **0** — never archived |

Large versions currently missing for: Admiral (2467), Sandy (3184), Café (3434),
Celadon (4519), Topiary (4546), Amatista (6442). Will keep hunting for these
across other capture timestamps; fall back to the 100×100 where unavailable.

Layout: `images/8801-XXXX.jpg` (100px) and `images/large/8801-XXXX.jpg` (418px).

---

## 4. Proposed data shape

`../lt.json` is the single output — there is one file, so there is nothing to
keep in sync. The sketch below is written as YAML only because it can carry
inline comments; the real file is JSON with the same keys, in this order.

```yaml
meta:
  product: Ultrasuede® LT
  also_known_as: [Ultrasuede® Light]
  manufacturer: Toray
  status: discontinued
  color_count: 36
  style_numbers:
    - number: "801"     # 2005 swatch pages; 2010 Light colour card
    - number: "8801"    # SKU prefix from 2010; "Style: 8801" on the 2017 card
  composition: 80% polyester ultra-microfiber non-woven, 20% non-fibrous polyurethane binder
  width_in: 58
  first_official_listing: 2005-02-11
  last_official_listing: 2024-08-05
  delisted_by: 2025-12-16
  compiled: 2026-09-06

sources:                     # registry; colours reference these by id
  - id: swatches-lt-2024-08-05
    kind: swatch_index       # swatch_index | swatch_page | color_card | product_page
    title: "Ultrasuede® Swatches — Search Result: Ultrasuede® LT"
    original_url: http://swatches.ultrasuede.us/swatches/search_result.php?product=LT
    archive_url: https://web.archive.org/web/20240805162934/http://swatches.ultrasuede.us/swatches/search_result.php?product=LT
    captured: 2024-08-05
    colors_listed: 36

colors:
  - name: White
    slug: white
    sku: 8801-5872
    code: "5872"
    hex: "#e8e4dd"                 # sampled from the swatch image (centre-crop mean)
    rgb: [232, 228, 221]
    image: images/8801-5872.jpg
    image_large: images/large/8801-5872.jpg
    image_source: https://web.archive.org/web/20221230200254/http://swatches.ultrasuede.us/swatches/images/8801-5872.jpg
    source: https://web.archive.org/web/20240805162934/http://swatches.ultrasuede.us/swatches/search_result.php?product=LT
    sources: [swatches-lt-2024-08-05, colorcard-lt-2017, colorcard-light-2010,
              uscom-light-2010, uscom-light-2005]
    first_listed: 2005-02-11
    last_listed: 2024-08-05
    last_year_listed: 2024
    on_color_cards: ["2010", "2017"]
    online_sample_orderable_until: null   # e.g. 2019-03-12 for the ten
    former_skus:                          # only White has one
      - code: "5832"
        style: "801"
        source: uscom-light-2005
        note: renumbered to 5872 by 2010
```

### Field notes

- `source` — the single "latest archive available where this colour was found",
  as requested. `sources` keeps the full corroboration trail so any entry can be
  cross-checked against an independent source (typically 5 per colour).
- `hex` / `rgb` — derived by sampling the swatch JPEG, not official Toray values.
  Needed to render the web page; will be labelled as approximate.
- `last_year_listed` — **2024 for all 36**, since the line was delisted wholesale.
  `first_listed` is the field that actually varies (2005 for 35, 2010 for Café).
- Every field traces to an archived page; nothing is inferred from third-party
  retailers.

---

## 5. Ultrasuede® Light Jungle Collection

A separate printed line (17 animal prints), keyed by **Pattern # + Color #**
rather than by SKU — the same relationship HP has to HP Jungle on the modern
site.

Seventeen entries, but only **eleven patterns**: Baby Cougar, Bobcat, Cheetah,
Jaguar, Python and Small Pony were each sold in two colourways, and Toray listed
both on the same page. Two entries sharing a name are that, not a duplicate —
the pair share a `pattern` and differ in `color`, which is why the demo tile
prints the colourway under the name.

### Timeline

| Date | Source | Patterns | Notes |
|---|---|---|---|
| 2001-05-27 | `ultrasuede.com/b2b/JungleLight.html` | **17** | Earliest listing. Older image names (`BCoug231.jpg`); no in-stock marks. |
| 2005-02-11 | `products/fashion/swatches/light_jungle.html` | **17** | |
| 2005-04-13 → 2009-04-11 | `products/swatches/light_jungle.html` | **17** | 15 captures, 6 distinct versions. Last capture ever. |
| 2010-12-01 | `ultrasuede.com/swatches/search_result.php` | — | Not in the product menu; Ambiance Jungle still is. |

Same story as the solid colours: **the set of 17 never changed** across the
whole eight-year record — same names, same pattern/colour numbers. The only
change is that **Leopard (143/210) lost its "in stock" asterisk** between
2006-11-09 and 2007-01-05, leaving Cheetah (both colourways), Ocelot and Small
Zebra as the only stocked prints. Recorded per pattern as `in_stock_until`,
mirroring `online_sample_orderable_until` on the solid colours.

### Last year listed

**2009 for all 17** — as with the solid colours, the line went from full to
gone in one step rather than shrinking. The collection has no capture after
2009-04-11, and by the 2010-12-01 site rebuild it is absent from the product
menu (which still offers Ultrasuede® Ambiance Jungle). It never appeared on
`swatches.ultrasuede.us`, which carried HP Jungle from 2016 on. So the record
supports "last listed 2009-04-11, gone by 2010-12-01" — captured in
`meta.light_jungle` as `last_official_listing` / `delisted_by`, with the
reasoning in `delisted_evidence`.

15 of the 17 pattern images are archived (Bobcat/231 and Ocelot/154 are not —
confirmed by a prefix CDX query over the whole `images/jungle/` directory, and
the 2001 page's differently-named copies were never archived either).
The image filenames end in the colour number, which the parser asserts against
the label text — so the image/label pairing is self-checking.

Because those two will never be recoverable, a hand-supplied photograph is
allowed to stand in for them: drop a file at `../images/jungle/bobca231.jpg` or
`../images/jungle/ocelo154.jpg` and the builder picks it up. It is marked
`image_provenance: reference_photo` rather than `wayback`, and the demo labels
it as a reference photograph — a printed pattern cannot be drawn from a hex the
way a solid colour can, but a stand-in must not be mistaken for evidence.

Stored in `../lt.json` under `patterns`, images in `../images/jungle/`.

---

## 6. Field's Fabrics custom colours

Field's Fabrics (Grand Rapids, MI) is a US Ultrasuede retailer that had Toray
dye LT in colours that were never part of the official line. Their catalogue
keeps them in a dedicated category, `shop.fieldsfabrics.com/ultrasuede-lt-custom`
(11 captures, 2017-09-28 empty → 2024-04-17).

### The membership rule

**Absence from Toray's own swatch pages is the test.** An LT colour Field's sold
that is not one of the official 36 is recorded as a custom colour.

Field's own claim — *"Premium Color only Available at Field's Fabrics"*, or a
place in the custom category — is kept as evidence where it appears, but it is
neither necessary nor sufficient. Not sufficient: of the nine items the category
lists, three are **genuine Toray colours** (4529 Petit Pois, 6581 Opal, 7330
Atlantis), all on both colour cards and on Toray's site through 2024, two of them
even titled "Custom Color" by Field's. The official-line check is what keeps
those out. Not necessary: six further colours carry no claim at all yet appear
nowhere in Toray's record either (below).

That yields **13 custom colours**. `verify.py` asserts the disjointness from
three directions (code, slug, name), and separately re-derives the rule from the
snapshot filenames: every Field's LT product code held here must be either one of
the 36 or one of the 13.

Each entry records which kind of evidence put it there, in `custom_basis`:

| # | Name | listed | last year | basis | notes |
|---|---|---|---|---|---|
| 1419 | Blackberry | 2019-07-16 → 2024-04-17 | 2024 | claim | was "Black Berry" in 2016 |
| 1394 | Burgundy | — | — | absence | never captured while offered; every capture reads "Sold Out" |
| 7373 | Ceramic Teal | 2019-07-16 → 2022-07-03 | 2022 | claim | first marked sold out 2022-11-27 |
| 3088 | Fired Clay | 2016-08-01 → 2023-03-29 | 2023 | absence | |
| 2694 | Imperial Blue | 2016-08-01 | 2016 | claim | one capture only; never in the custom category (which post-dates it) |
| 8269 | Inca Gold | 2016-06-15 → 2023-06-06 | 2023 | absence | |
| 9437 | Orquidea | 2022-07-03 → 2023-03-29 | 2023 | absence | live image 404s, so `hex: null` |
| 6588 | Rose Quartz | 2019-07-16 → 2024-04-17 | 2024 | claim | |
| 8267 | Sedona | 2019-07-16 → 2024-07-20 | 2024 | absence | |
| 7337 | Splash Blue | 2019-07-16 → 2024-04-17 | 2024 | claim | |
| 5890 | Stone Grey | 2019-07-16 → 2023-03-25 | 2023 | claim | |
| 5295 | Sunshine | 2019-07-16 → 2023-03-25 | 2023 | claim | |
| 6642 | Zinnia | 2016-08-01 → 2019-07-16 | 2019 | absence | |

"Listed" means *offered*: a listing or title reading "Sold Out" / "Discontinued"
does not count, which is why the dates stop well before the product pages do
(most are still up in 2026, marked discontinued). `sold_out_noted` records the
first capture carrying that marker. Burgundy is the limiting case — the archive
never caught it while it was on sale, so its listed dates are `null` and only
`earliest_evidence` (2019-07-24) is known.

### What "absence" is and is not evidence of

The six colours resting on absence alone — 1394 Burgundy, 3088 Fired Clay,
6642 Zinnia, 8267 Sedona, 8269 Inca Gold, 9437 Orquidea — live in Field's main
LT category, not the custom one, and no capture held here claims them as
exclusive.

An alternative explanation is that they are survivors of the pre-2005 line: the
2001 b2b page advertises **"40 high-fashion colors"** where the archive can only
name 36, and lists a different composition (100% polyester, versus the 80/20
blend from 2005 on). Nothing in the record settles it. They are listed as custom
on the working rule that a colour Toray never listed is not a Toray colour, and
`custom_basis: absent_from_official_line` marks exactly which ones that rule —
rather than Field's own word — is carrying.

### Images

The archive is almost useless here: it holds swatch photographs for only two of
the thirteen (Blackberry and Rose Quartz, 2016-05-30, 60px). So the images come
from the **live Field's site** at 600×600, and every entry is labelled
`image_provenance: live_site` with the date retrieved.

Twelve of the thirteen sit under `assets/images/ultrasuede/<code>.jpg`.
**Orquidea (9437) is the exception**: that path 404s and only the shorter
`assets/images/9437.jpg` exists, which is the one its product page links. Its
photograph is 578×582 and, unlike the rest, carries no watermark. The exception
is listed in `FIELDS_IMG_FLAT` rather than probed, because `build_dataset.py`
does no network access.

Two consequences worth knowing:

- The live photographs carry a white "Field's FABRICS" watermark across the
  middle of the swatch, so these are sampled from four corner patches
  (`sample_color_corners`) rather than a centre crop.
- The two generations of photography **disagree noticeably** — Blackberry reads
  `#781621` in 2016 against `#3b151c` today, Rose Quartz `#f7a7a3` against
  `#ba8b94`. Both archived thumbnails are kept in `../images/fields/archived/`
  and carried on the entry as `archived_swatch` so the discrepancy is visible
  rather than hidden. Treat every hex in this section as approximate.

---

## 7. Files in this directory

| file | purpose |
|---|---|
| `build_dataset.py` | builds `../lt.json` from `snapshots/`. Offline and idempotent |
| `verify.py` | independent re-check of the output; `--links` also HEADs every archive URL |
| `extract_pdf_colors.py` | pulls `<code> <name>` pairs + style number out of a colour-card PDF |
| `plan_images.py` | picks the latest capture of each swatch image → `image_jobs.tsv` |
| `fetch_images.sh` | downloads a job TSV, with the backoff Wayback's rate limiting requires |
| `snapshots/LT/*.html` | all 23 raw LT swatch-index captures (21 populated + 2 empty) |
| `snapshots/hist/*` | the 2001 / 2005 / 2009 / 2010 / 2020 pages and the 2010 card |
| `snapshots/fields/*` | Field's Fabrics category, product and swatch-image captures |
| `cdx_*.json` | raw CDX API responses — the underlying search record |
| `cdx_fields/p_*.json` | per-product capture histories for the Field's items |

### Rebuilding

```bash
cd scraping
python3 build_dataset.py     # regenerate lt.json (no network)
python3 verify.py --links    # full check, including that every link resolves
```

### A note on rate limiting

`web.archive.org` refuses connections after roughly 20 rapid requests, and curl
reports that as exit 7 / HTTP `000` — which looks exactly like a dead link.
Both `fetch_images.sh` and `verify.py --links` retry with backoff for this
reason; a bare loop will produce false failures.
