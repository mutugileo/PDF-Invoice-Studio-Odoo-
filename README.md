# PDF Invoice Studio

Status stamps and branding for Odoo 17 invoices, configured from Invoicing Settings.

Odoo's invoice report has no watermark, prints the billing address twice when the
shipping address matches it, has no field for a company seal or signatory, and
hardcodes the label "Tax ID". This module adds those, through template inheritance
rather than replacing the report.

## What it adds

| Feature | Why |
| :--- | :--- |
| Status watermark | PAID / PARTIALLY PAID / OVERDUE / DRAFT / CANCELLED / REVERSED. Odoo has no watermark anywhere. |
| Address collapsing | Core prints the same address twice when shipping matches billing. |
| Seal + signature | No field exists for either in core. |
| Custom fiscal label | Core hardcodes `vat_label` or "Tax ID"; print "KRA PIN", "GSTIN", etc. |
| Payment instructions block | Formatted panel below the totals. |
| Bulk ZIP export | Always final invoices, and includes vendor bills. See caveat below. |

## Requirements

- Odoo **17.0** (Community or Enterprise)
- `wkhtmltopdf` — Odoo cannot render PDFs without it

## Install

```bash
python odoo-bin -d <database> --addons-path=<paths> -i pdf_invoice_studio
```

Then: **Invoicing → Configuration → Settings → PDF Invoice Studio**.

All settings live on `res.company`, so multi-company databases keep separate
branding. Nothing is stored on the invoice, so a settings change takes effect on
the next print.

## Tests

```bash
python odoo-bin -d <database> --addons-path=<paths> \
  -i pdf_invoice_studio --test-enable --test-tags pdf_invoice_studio --stop-after-init
```

26 tests. They cover the watermark status precedence, the colour blending, malformed
input, and the rendered report itself — the last matters because the template *is*
the product, and a bug that only appears at render time is invisible to unit tests
of the helpers.

## Rendering notes

These were all found by printing real PDFs, not by reading code. Each has a comment
at the relevant line; this is the summary.

- **CSS `opacity` is ignored** by wkhtmltopdf on the watermark, which printed it at
  full strength. The intensity is therefore blended into the colour in Python and
  reaches the renderer as a flat hex.
- **`position: fixed` neither repeats across pages nor anchors to the viewport**
  once the layout has a positioned ancestor. The stamp is positioned absolutely
  inside `.page`, and prints on the first page only.
- **A filled stamp covers the amounts.** It is drawn as a hollow outline
  (`-webkit-text-stroke`) so figures underneath stay legible. The intensity ceiling
  is capped for the same reason and is pinned by a test.
- **Stamp size scales with wording length.** One size cannot serve both ends: 58px
  left "OVERDUE" lost on a dense 30-line invoice, while "PARTIALLY PAID" clips long
  before the size that fixes that.
- **Bootstrap's flex grid does not lay out** in wkhtmltopdf's WebKit. The seal and
  signature use a real two-cell `<table>`; `row`/`col-6` collapsed them into a
  single left-hand column.

## Known limitations

- The stamp prints on the **first page only**.
- Tested on **17.0 only**. Not verified on 16.0 or 18.0. Odoo 18 replaced
  `check_access_rights`/`check_access_rule` with `check_access`, which the bulk
  export controller uses.
- **Odoo 17 already ships a bulk "Export ZIP"** action. This module's differs only
  in that core falls back to a pro-forma for invoices never printed, and skips
  vendor bills. Do not market ZIP export as new.
- No QR code. Core already generates a payment QR.

## Licence

OPL-1. Copyright (c) Codzure.
