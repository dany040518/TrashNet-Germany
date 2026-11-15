## Success Criteria

### Business success
- A user can photograph one item and get the correct German bin or stream in under 3 seconds (target, to be validated).
- The tool shows the answer in plain English with the German term (e.g. "Gelbe Tonne / Yellow bin").
- It reduces wrong-bin disposal among the target group (measured only through a small user test, see Assumptions).

### Data mining / model success
| Criterion | Target | Rationale |
|---|---|---|
| Macro F1 (primary) | ≥ 0.80 on a held-out test set | Treats all five classes equally despite imbalance |
| Per-class recall | ≥ 0.70 for every class | Prevents one class from being sacrificed |
| Restmüll → recyclable stream errors | Tracked separately | Recyclables in Restmüll are the most common real-world mistake |
| Robustness | Macro F1 drop ≤ 10 points on photos with clutter or poor lighting vs. clean photos | Matches the uncontrolled-photo use case |
| Rejection option | Model returns "uncertain" below a confidence threshold | Better than a confident wrong answer |

## German Waste Sorting Rules (Research)

| Stream | What goes in | Common exceptions |
|---|---|---|
| Gelbe Tonne / Gelber Sack | All empty packaging except glass and paper, such as plastic, metal or composite materials, including beverage cartons | Toothbrushes, wet razors and lighters do not belong here even if made of plastic (not packaging) |
| Altpapier (blue bin) | Paper, cardboard and box packaging, shipping boxes, magazines and newspapers | Thermal paper such as receipts or tickets, and wallpaper, go in Restmüll; greasy pizza boxes and coated paper do not belong in paper |
| Bioabfall (Biotonne) | Fruit scraps, coffee grounds, eggshells and wilted vegetables | No plastic. Compostable bags go in the yellow bin, because sorting equipment can't tell them from conventional plastic bags |
| Altglas (container) | All empty glass packaging, sorted by color | Window glass, dishes, mirrors, light bulbs, ceramics and porcelain are excluded; lids may stay on, and if unsure of the color, use the green container |
| Restmüll (grey bin) | Waste that cannot be recycled further and is not hazardous; e.g. tissues, disposable razors, used kitchen paper, cigarette butts | Baking paper goes here, not in paper |
| Out of the 5 classes | E-cigarettes contain lithium-ion batteries and never belong in household waste; single-use deposit containers typically carry a 25-cent deposit, returned to shops | Decide: out-of-scope class or "uncertain" |

**Regional variation.** Rules are set locally, and some areas use a combined "Wertstofftonne" (recyclables bin) instead of the yellow bin. In a UBA-cited survey, 76% of respondents had a yellow bin or sack and 13% a Wertstofftonne. The target city's waste authority (e.g. Hof, Nuremberg) is the final authority.

**Why this problem is real.** Yellow bins and sacks contain up to 40% waste that does not belong there. On average, 39.3% of Restmüll is bio waste. Dry recyclables make up 27.6% of Restmüll.

**Gap to verify:** I found no source for the "fines" claim in your problem statement, so check your housing contract or the city's Abfallsatzung, or soften the wording to "potential consequences".

### Sources
1. UBA, Abfälle im Haushalt: https://www.umweltbundesamt.de/en/node/85899
2. UBA, Mülltrennung (5-chamber system): https://www.umweltbundesamt.de/umwelttipps-fuer-den-alltag/muelltrennung
3. UBA, Restmüll analysis: https://www.umweltbundesamt.de/node/43962
4. UBA, Mülltrennung in Deutschland noch ausbaufähig: https://umweltbundesamt.de/print/78936
5. UBA fact sheet Abfalltrennung: https://www.umweltbundesamt.de/sites/default/files/medien/2503/dokumente/fact_sheet_abfalltrennung.pdf
6. Initiative "Mülltrennung wirkt", first-apartment press release: https://www.muelltrennung-wirkt.de/fileadmin/user_upload/Presse/Pressemitteilungen/2026/09_01_Wohnung/260901_PM_Erste_Wohnung.pdf
7. ÖKO-TEST Ratgeber Abfall: https://www.oekotest.de/freizeit-technik/Ratgeber-Abfall_98935_1.html
8. Lizenzero, Fehlwürfe: https://www.lizenzero.de/blog/weniger-abfall-mehr-recycling-deutschlands-fortschritte-in-der-kreislaufwirtschaft/
9. Verbraucherzentrale NRW, Einwegpfand: https://www.verbraucherzentrale.nrw/wissen/umwelt-haushalt/abfall/fragen-und-antworten-alles-zum-einwegpfand-und-dosenpfand-11505
10. Hanseatic Bank, Pfand overview: https://www.hanseaticbank.de/klarmacher/bezahlen/pfand-auf-flaschen-und-dosen-wie-viel-gibt-es-fuer-leergut-und-wo

## Risks and Assumptions Log

### Assumptions
| ID | Assumption | How to validate |
|---|---|---|
| A1 | Five classes cover the majority of everyday household items | Check the dataset's label distribution; test with a sample of real photos |
| A2 | A single photo shows enough to pick the stream (no need to see the item's contents or condition) | Error analysis on dirty and mixed items |
| A3 | Rules follow the national UBA guidance; local deviations are out of scope for the prototype | Ask the team to pick one reference city |
| A4 | Suitable labeled data exists or can be built within the project timeline | Dataset search in Sprint 1 |
| A5 | Users have a smartphone and take one item per photo | User test with a few international students |

### Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Label mismatch: public datasets are usually material-based (e.g. TrashNet: glass, paper, cardboard, plastic, metal, trash), not bin-based | High | High | Write an explicit material-to-bin mapping; document the rules per class |
| R2 | Same-looking items belong to different bins (clean vs. greasy paper, glass vs. porcelain) | High | Medium | Add an "uncertain" output; report these pairs in the confusion matrix |
| R3 | Class imbalance and few Bioabfall or Altglas images | Medium | Medium | Macro F1, augmentation, class weights |
| R4 | Dataset images (clean, studio backgrounds) differ from real smartphone photos | High | High | Collect a small own test set; evaluate on it separately |
| R5 | Regional rule differences make correct answers location-dependent | Medium | Medium | Fix one reference city; state the limitation |
| R6 | Out-of-scope items (batteries, e-waste, deposit bottles) get a confident wrong answer | Medium | High | Reject option; list unsupported categories in the UI |
| R7 | Rules change (e.g. deposit scope, local systems) | Low | Medium | Cite sources with access dates; review before final delivery |
| R8 | Privacy and licensing of collected photos and datasets | Low | Medium | Use openly licensed data; no personal images |
| R9 | Time limits of the course limit the data work | Medium | Medium | Keep scope to the five classes; prioritize a baseline model |
