# Hygiene Product Compliance Audit Skill

A compliance-audit skill for disposable hygiene products sold in mainland China —
sanitary pads, panty liners, diapers, paper towels, wet wipes, and
antimicrobial/bacteriostatic variants. Built for reviewing **product launch
readiness, packaging labels, and marketing claims** against Chinese national
standards and disinfection-product regulations.

The judgment library is derived from standard texts and government publications.
Every rule cites its source clause. Where a source could not be verified, it is
labelled as unconfirmed rather than asserted.

## What it audits

Three layers, applied in order:

1. **Entity qualification** — manufacturer hygiene licence, hygiene-safety
   evaluation filing, OEM responsibility, enterprise standards.
2. **Product standards** — mandatory hygiene requirements (GB 15979-2024) plus
   category-specific performance standards, toxicology, and antimicrobial
   evaluation.
3. **Labels and claims** — mandatory label items, prohibited wording, and
   advertising-law exposure in packaging, detail pages, and livestream scripts.

## Key judgments

**Claiming "bacteriostatic" changes the product's regulatory identity.** A plain
sanitary pad is a Class III disinfection product (hygiene product category) that
needs only the manufacturer's licence. Adding a bacteriostatic claim pulls in the
GB 15979-2024 Table 1 **stability ≥ 1 year** requirement, mandatory
micro-organism-category labelling, toxicology re-testing, and — for
conductive-layer / face-layer actives — dissolve-safety evaluation.

**Initial bacteriostatic rate alone is not sufficient.** It covers only half of
clause 6.5.3. Stability is a mandatory Table 1 item with no exemption.

**High bacteriostatic rate can itself be a risk signal.** Industry validation of
25 products found the conductive-layer and chip products that reported >99.9%
inhibition were judged **dissolvable** — high initial rate and dissolution risk
correlate. See `references/antimicrobial-audit.md`.

**A compliant product is not a compliant advertisement.** GB 15979 and
GB 38598 govern what you may *sell*; the Advertising Law Article 17 governs what
you may *say*. Violations carry a floor of CNY 100,000 when advertising cost
cannot be calculated — precisely the situation with livestream advertising.

**Declared specifications raise the inspection line.** When a product's declared
requirements exceed the applicable standard, inspection judges against the
declared value. Every number on a detail page becomes a compliance obligation.

## Contents

| File | Covers |
|---|---|
| `SKILL.md` | Review workflow, three-layer framework, version calendar, 30 common errors |
| `scripts/label_scan.py` | Prohibited-wording scanner for labels and livestream scripts |
| `references/antimicrobial-audit.md` | Antimicrobial products: stability, dissolution risk, re-wet testing |
| `references/advertising-claims.md` | Advertising Law, China Advertising Association rules, livestream rules |
| `references/production-and-liability.md` | Production norms, inspection rules, penalties, punitive damages |
| `references/raw-materials.md` | Fluff pulp, SAP, face and conductive layers, supplier checklists |
| `references/supplementary-notes.md` | GB 38598 Amendment 1, OEM rules, disinfectant-grade chain, GB/T 8939-2025 |
| `references/launch-review.md` | Launch-readiness review with schedule estimates |
| `references/label-redline-words.md` | Prohibited wording by category |
| `references/audit-checklist.md` | Per-product checklist with sign-off |

## Usage

The scanner runs standalone:

```bash
# Category codes: pad | wetwipe | sanit | antibac | ad
python3 scripts/label_scan.py pad label.txt
python3 scripts/label_scan.py ad livestream_script.txt -o report.txt
```

`ad` mode applies only advertising-law rules — useful for livestream scripts and
product detail pages. Scan the same document in both `ad` and the product
category to catch label prohibitions as well.

Scanner hits are **candidates for human review, not final verdicts**. Reverse
keyword scanning cannot detect missing mandatory items — those still need the
checklist.

## Sources

- GB 15979-2024, GB 38598-2020 (incl. Amendment 1): openstd.samr.gov.cn
- WS 628-2018: nhc.gov.cn
- Disinfection product category catalogue: ndcpa.gov.cn
- Filing platform: credit.jdzx.net.cn
- Standards search: std.samr.gov.cn, ttbz.org.cn
- Advertising Law: samr.gov.cn

## Disclaimer

This library is compiled from public sources for preliminary review. Formal
compliance conclusions must be based on the full standard texts, official
interpretations, and the position of the competent local authority.

## Licence

MIT
