# Paper: "When Do Echoes Help? Learned Echolocation for Exploring Unseen Buildings in a Sample-Accurate Acoustic Simulator"

`main.pdf` (21 pages) is built from `main.tex`, `appendix.tex`, `refs.bib`, `figs/`.

## Venue and template

**Target: Transactions on Machine Learning Research (TMLR)**, using the official TMLR LaTeX style (`tmlr.sty`, `tmlr.bst`, from
github.com/JmlrOrg/tmlr-style-file) in anonymous-submission mode. Reasons for this choice:

* TMLR accepts on two criteria, whether the claims are supported by the evidence and whether some audience would be interested, not on
  novelty or headline numbers. The paper contains negative results (echoes do not help point-goal navigation; learned click aiming does
  not raise coverage; binaural head scan no better than blind) that are exactly what this standard is meant to admit.
* Rolling submission, no deadline, no page limit: the full validation tables and per-seed, per-building results fit without cuts.
* The study is modest in scale (one dataset, 3 seeds, 2M steps), which is a common reason for rejection at NeurIPS/ICML/ICLR main tracks.
* It does not compete with the echo-engine paper planned for the NeurIPS 2027 Evaluations & Datasets track.

To show author names (after acceptance or for a preprint) change `\usepackage{tmlr}` to `\usepackage[preprint]{tmlr}` (or `[accepted]`)
and fill in `\author`.

## Build

```bash
conda run -n paper tectonic -X compile main.tex        # conda env "paper" = conda-forge tectonic; downloads LaTeX packages on first run
conda run -n ss python paper/make_figures.py           # regenerate figs/*.pdf from the raw logs (run from the repository root, CPU only)
python3 paper/gen_tables.py                            # regenerate figs/tab_per_building.tex and figs/tab_wipe.tex
```

`figs/per_building.json` was extracted from `habitat_audio/runs/q6_*/eval_*.log` and `q7_*/eval_*.log`.

## Where each result comes from

| Paper section | Runs / files |
|---|---|
| Sec. 3, App. A (simulator validation) | `experiment/results/`, `experiment/results_sparse/`, `experiment/results_box*/` |
| Sec. 5 P1–P3 | queues 1–3 on Habitat test scenes (`habitat_audio/runs/queue_results.md`, `queue2_results.md`, `queue3_results.md`) |
| Sec. 5 P4, Table 2 | queue 4 (`queue4_results.md`) |
| Sec. 5 P5, App. E | queue 5 (`queue5_results.md`) |
| Experiment 1 | queue 6 (`q6_*`, `queue6_results.md`) |
| Experiment 2 | queue 7 part B (`q7_range_*`, `queue7_results.md`) |
| Experiment 3 | queue 7 part A (`runs/probe/`, `habitat_audio/probe_map.py`) |
| Experiment 4 | queue 8 part A (`<run>/wipe<N>_<scene>.log`, `queue8_results.md`) |

## Open items before submission (need the author)

1. **References**: `refs.bib` was written from memory. Every entry (authors, venue, year, pages) must be checked against the source.
2. **Anonymised code link**: TMLR is double-blind; the repository must be shared through an anonymising service or as supplementary material.
3. **AI-use statement**: the paper discloses AI assistance; check it against TMLR's current policy and edit as you see fit.
4. **Licence** for the repository's own code is still unchosen.
5. Not included yet: the click-cost sweep (queue 8 part B, still training when the draft was written).
6. Known weaknesses a reviewer will raise are listed in the paper's Limitations section (3 seeds, small buildings, blind agents trained
   without the auxiliary loss, figure-of-eight beams in Experiment 1).
