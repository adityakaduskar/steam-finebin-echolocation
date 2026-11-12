# Passages that need the author's judgement

Open `main_review.pdf`: every passage below carries a red marker **[J1]** … **[J26]** at its first word. The markers do not appear in
`main.pdf` (they are `\J{n}` macros in `main.tex` and `figs/exp4_text.tex`, visible only when built through `main_review.tex`).

Numbers, tables and figures are generated from the logs and are not listed here; what is listed is everything that is an
**interpretation, a framing choice, a novelty claim, an unmeasured explanation, or a decision only the author can make**.
Each entry says what the draft claims, why it is a judgement call, and what the options are.

## A. Framing and novelty (decide first; they shape the whole paper)

| # | Where | What the draft says | Why it needs you | Options |
|---|---|---|---|---|
| J1 | Abstract, finding (i) | "when a goal vector is supplied, echoes do not improve navigation success (0.38 vs 0.39)" | This comes from **one seed per agent** (preliminary P4), yet sits in the abstract next to three-seed results. | Keep with the words "in a single-seed preliminary run"; or drop from the abstract; or run 2 more seeds of each (about 9 h) and promote it to an experiment. |
| J2 | Introduction, 2nd paragraph | Whether echo-only agents benefit "has not been tested in a controlled way across unseen buildings and random seeds" | Novelty claim. I did not do a systematic literature search; it rests on what I know of the field. | Search (audio-visual navigation, echolocation RL, SoundSpaces follow-ups, robotics sonar RL) and either keep, soften to "to our knowledge", or cite what you find. |
| J5 | Related work, "Echoes as a learning signal" | "We are not aware of a study that trains navigation or exploration policies on self-generated echoes alone and evaluates on held-out buildings with multiple seeds" | Same novelty claim, stated more strongly. | As J2. |
| J3 | Introduction, 3rd paragraph | The reason given for building on Steam Audio is that it is "open source, fast and actively maintained" | The draft does not say why SoundSpaces 2.0, which already renders continuous echoes in Habitat, was not used. A reviewer will ask. Your earlier work found its echoes arrive about 1 ms late (apparent 384 m/s). | State that measured reason (it is yours and it is strong), or give another, or add a short comparison. |
| J6 | Related work, "Exploration and memory" | Our probe "is closest to" Wijmans et al. 2023 and "extends that finding" | Positioning against the most similar prior paper. Their agents had egomotion input; ours do not. Whether "extends" is fair is your call. | Keep; or describe as "a related observation in a different setting". |
| J4 | Introduction, "Summary of findings" | "The representation mattered more than the amount of acoustic simulation" | A headline interpretation of Experiment 1 (see J10, J17). | Keep if you accept J10; otherwise tone down to the plain numbers. |
| J26 | Contributions, item 1 | "three fixes for defects in the upstream code" | Claims bugs in Valve's code. They are real in our build, but have not been reported upstream or confirmed by Valve. | Report them to the Steam Audio GitHub (strengthens the claim), or reword to "three changes needed to build and run without Intel IPP on GCC 11". |

## B. Explanations that were reasoned, not measured

| # | Where | What the draft says | Why it needs you | Options |
|---|---|---|---|---|
| ~~J7~~ | Sec. 3.5 | **Resolved 2026-11-11 by measurement** (`habitat_audio/nogpu_checks.py`): first-bounce energy of a co-located click is 0.990 of the mirror-correct value (min 0.976 over 200 poses). The sentence now states this; marker removed. | Note it evaluates the engine's lobe formula by ray casting, not the engine's output. | Accept, or ask for a direct engine comparison. |
| J10 | Experiment 1, Result 2 | Head-scan is no better than blind because the spectrogram "leaves the policy to recover" range and bearing | One explanation among several: 3 clicks vs 1, different encoder input size (6×65×64 vs 2×64×32), 2M steps possibly too few, cardioid² vs omni click. None were isolated. | Present as a hypothesis; or add a control (binaural single click; or sonar image built from the three scan clicks). |
| J11 | Experiment 1, Result 3 | Beam choice is noise because "the sonar image already resolves direction" | Plausible, untested; and that beam set fired backwards as well. The queue 9 control (forward beams) will speak to this. | Wait for queue 9, then rewrite this paragraph from its result. |
| J12 | Experiment 1, ablations | Zeroed echoes make the sonar agent "slow down sharply … it does not move confidently" | "Confidently" is an intention attributed to a policy. The data are 11.1 cells and 8.7 collisions. | Replace with the numbers only, or keep. |
| J13 | Experiment 2, Result 5 | The learned-beam agent "trades distance travelled for not hitting things" | Describes a correlation (short path, few collisions) as a trade. | Keep; or state the two numbers without the word "trades". |
| J19 | Discussion, "Active sensing" | "A plausible reason is that the coverage reward favours continuous forward motion…" | Speculation about why aiming did not raise coverage. | Keep marked as speculation; delete; or test with a task where sideways information matters (e.g. doorway finding). |
| J14 | Experiment 3, Result 9 | Blind agents remember best because they "can avoid re-covering ground only by integrating [their] own movements" | Functional explanation of a decoding result. Experiment 4 supports it partly (J23). | Keep with a pointer to Experiment 4; or state only the AUROC ordering. |
| J15 | Experiment 3, Result 10 | "The recurrent state retains somewhat less geometric information than a pooled copy of the latest echo" | The gap is 0.803 vs 0.832 for one agent and zero for the other two; decoders are small; the observation was pooled to 512 numbers. "Perceive rather than remember" may be too strong a title for Result 10. | Soften the heading to "memory adds no geometric information beyond the current echo"; or keep. |
| J23 | Experiment 4, Result 11 | The 15 % drop for blind agents "supports the reading" that they rely on longer path memory | Causal claim from 3 seeds, 2 buildings, a 3-cell difference (all three seeds do drop). Echo agents' coverage rose slightly when wiped, which is itself unexplained. | Keep with those caveats stated; or add wipe intervals 5, 10, 50 to show a dose-response curve (evaluation only, about 2 h). |
| J24 | Experiment 4, Result 12 | Short-term memory "is what keeps these agents from walking into the same obstacle repeatedly" | Mechanism not observed directly. A measurement is prepared (`ppo_eval --log-collisions`, `collision_repeats.py`) and queued behind the training runs. | Wait for that result, then keep, reword or delete. |
| ~~J25~~ | Experiment 4, "Repeatability" | **Resolved 2026-11-11 by measurement**: the cause is not threading; Steam Audio redraws its rays every run. Identical clicks give sonar images correlating at 0.94–0.97. Text and Appendix G updated; marker removed. | New fact worth your attention: the agents' sonar observations are noisy at a fixed pose. | Decide whether this belongs in the main text of Sec. 4 as a property of the environment. |

## C. Design choices a reviewer will question

| # | Where | What the draft says | Why it needs you | Options |
|---|---|---|---|---|
| J8 | Sec. 4.1 | Every surface has the same material (absorption 0.10/0.20/0.30, scattering 0.05) | No justification is given; real rooms mix materials, and Replica has semantic labels that could assign them. | Justify (isolates geometry from material effects), or list as a limitation (already partly there), or run one check with a different absorption. |
| J9 | Preliminary P5 | λ = 0.05 was "fixed for the main experiments" after seeing λ = 0.02 and 0.1 | The penalty was tuned by looking at **held-out** buildings in single-seed runs. That is a mild form of test-set tuning. | Say so explicitly in the Limitations; or re-select λ on training buildings. |
| J20 | Limitations, "Confounds we did not remove" | Blind agents had no auxiliary loss; Experiment 1 beams were figure-of-eight | Queue 9 is running both controls now (blind + auxiliary loss; sonar + forward beams, 3 seeds each). | When queue 9 ends, either replace the Experiment 1 rows with the controlled versions or add them as extra rows and delete this limitation. |
| J17 | Discussion, "Representation over raw signal" | "We do not claim that binaural input cannot work, only that at this training budget … it did not" | How strongly to state the main negative result about binaural input. In a single-seed run at λ = 0.02 the head-scan agent reached 36.7 cells (Appendix E), far above its three-seed mean of 26.6 here. | Keep the cautious wording; consider running head-scan at λ = 0.02 with 3 seeds before making any claim about it. |

## D. Recommendations and speculation beyond the data

| # | Where | What the draft says | Why it needs you | Options |
|---|---|---|---|---|
| J16 | Discussion, first paragraph | "benchmarks intended to measure the value of echolocation should not provide a goal vector" | A recommendation to the field resting on a single-seed result (J1). | Keep as a suggestion; soften; or remove. |
| J18 | Discussion, "Representation over raw signal" | A physical device "needs a four-capsule (tetrahedral) microphone and a pulse-compressed emitter" | Engineering speculation; nothing in the paper tests hardware. You raised the assistive-device idea; whether it belongs in this paper is your choice. | Keep one sentence, move to a "future work" line, or delete. |

## E. Declarations only the author can make

| # | Where | What the draft says | Why it needs you |
|---|---|---|---|
| J21 | Reproducibility statement | Checkpoints and raw impulse responses "are not included … because of their size" | Decide whether to publish the 3 GB of checkpoints (e.g. Zenodo, Hugging Face) so results can be re-evaluated without retraining; TMLR reviewers may ask. |
| J22 | "Use of AI assistance" and the first-page footnote | The AI wrote the code and the first draft; "the author … posed the research questions, selected the experiments and takes responsibility for all content" | This is your statement, made in your name. Confirm each clause is true as you would put it, in particular "selected the experiments": several experiments were proposed by the assistant and approved by you. TMLR's FAQ expects "the ideas, claims and results" to be human-sourced. |

## Suggested order of work

1. J3, J2/J5, J6: the framing depends on facts only you can supply or check.
2. J1, J9, J16, J17: decide how much weight single-seed results may carry; consider the extra seeds.
3. Wait for queue 9, then resolve J11 and J20.
4. Go through section B and, for each, choose "measure", "label as hypothesis" or "delete".
5. Rewrite the Introduction, Discussion and Conclusion in your own words; they carry almost all of the judgement.
6. J21, J22 last, once the content is final.

## Update 2026-11-11: literature search for J2 / J5 (done by a research agent; I did not read these papers myself)

The search found **prior work that the first draft missed**, so both novelty sentences were rewritten and five references added.
You must read at least the first one before submission.

1. **Zhu, Rahtu, Zhao, "Beyond Visual Field of View: Perceiving 3D Environment with Echoes and Vision", arXiv:2207.01136.** A PointGoal
   agent in Habitat/SoundSpaces whose only inputs are GPS and binaural echoes of its own sweep. Reported SPL on Replica: echoes 0.547,
   GPS-only 0.491. **This is the closest prior work and it reports the opposite of our preliminary P4** (echoes did not help our
   point-goal agent). The draft now cites it and says the discrepancy was not investigated. Judgement needed: explain the difference
   (their acoustics, wall sliding, training budget, no seeds reported) or run the three-seed point-goal experiment before claiming anything.
2. Hu, Purushwalkam, Harwath, Grauman, "Learning to Map Efficiently by Active Echolocation", IROS 2023: agent with vision learns *when* to emit. Relevant to Experiment 2.
3. Yu et al., "Echo-Enhanced Embodied Visual Navigation", Neural Computation 2023: learned emitter added to visual point-goal navigation, five runs.
4. Mohan & Vanderelst (SSCI 2020) and Nguyen & Vanderelst (SSCI 2022): echo-only deep RL in 2-D bat simulations.
5. Not added, consider: Velmurugan et al., "Saranga", Science Robotics 2026 (real ultrasonic drone, hand-designed controller).

The first names of the authors in the five new BibTeX entries (zhu2022beyond, hu2023learning, yu2023echo, mohan2020training,
nguyen2022toward) and their page numbers are **unverified**: the agent could not open two of the papers. Check them.
The agent found no follow-up to Wijmans et al. 2023 that probes the memory of echo or audio agents.
