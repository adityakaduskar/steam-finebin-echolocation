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

1. **References**: checked on 2026-11-11 against arXiv, Crossref, OpenReview, PubMed and publisher pages (DBLP was unreachable). 23 of 29 were correct; 5 were fixed (two author-name encodings, the full Replica author list, one spelling, the Embree article number). `alain2017understanding` is cited as arXiv 2016; it may alternatively be cited as an ICLR 2017 workshop paper.
2. **Anonymised code**: `scripts/make_anonymous_bundle.sh` builds `paper/supplementary_anonymous.zip` (18 MB; TMLR allows 100 MB of anonymised PDF/ZIP supplementary material). Rebuild it after the last commit before submitting.
3. **AI-use disclosure**: TMLR's FAQ requires a first-page footnote stating LLM use (added) and says LLMs cannot be authors; see `AUTHOR_REVIEW.md` J22.
4. **Licence**: Apache-2.0 added (`LICENSE`, `NOTICE`); change it if you prefer another.
5. Not included yet: the click-cost sweep (queue 8 part B, still training when the draft was written).
6. Controls for two confounds (blind + auxiliary loss; sonar + forward-only beams; 3 seeds each) are queued as queue 9 (`habitat_audio/queue9.sh`).
7. **Author judgement**: 26 marked passages, see `AUTHOR_REVIEW.md` and `main_review.pdf`.
8. TMLR facts (checked 2026-11-11): double-blind, rolling, no fee, no page limit, template mandatory, main body over 12 pages gets a longer review timeline (ours is longer), arXiv posting allowed with the `preprint` style option, author list frozen at submission.
