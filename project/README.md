# project/: everything from the hackathon besides the code

| Path | What it is |
|---|---|
| [`RESULTS-SO-FAR.md`](RESULTS-SO-FAR.md) | Every result in one place, each number linked to the file it came from |
| [`Aperion-Project-Dossier.pdf`](Aperion-Project-Dossier.pdf) / `.html` | The project dossier (PDF and web versions) |
| [`Quantum Brain Ultrasound Explained.pdf`](Quantum%20Brain%20Ultrasound%20Explained.pdf) | Plain-language explainer |
| `deck/project/` | The pitch deck: one HTML file per slide in `slides/`, with order and sections in `deck.json` |
| [`04-TALK-SCRIPT.md`](04-TALK-SCRIPT.md) | The ~5-minute talk script and slide handoffs |
| [`02-PITCH-DECK-PLAYBOOK.md`](02-PITCH-DECK-PLAYBOOK.md) | How each slide maps to a rubric line |
| [`01-TEAM-NOTES.md`](01-TEAM-NOTES.md) | The team's original criteria for the project |
| [`00-EVENT-BRIEF.md`](00-EVENT-BRIEF.md) | Event rules, dates and deliverables, summarised from the official handbook |
| `qiskit-fall-fest-judging-rubric.xlsx` | The official judging rubric |
| `research/` | Four research reports: R1 clinical statistics · R2 ultrasound and FWI · R3 quantum algorithms · R4 audit of our own code and results |
| `brand/`, `website/` | Aperion logo, brand board and project web pages |
| `site/` | Saved copy of the public event handbook pages (HTML and text) |
| `handoff/` | The overnight hand-off package, with its own [`README.md`](handoff/README.md) |

## handoff/

| Folder | Contents |
|---|---|
| `1_pilot/` | `pilot_results.tar.gz`: the team pilot (5 methods on one 1D wave), full `runs/` and console log |
| `2_reconstructions/` | Every inversion run (configs, counts, histories, manifests, logs), as one tarball |
| `3_ibm_job/` | Real hardware job `db9smd9gv2cc73e60pm0`: `raw_counts.json` (every bitstring), `job_metadata.json` (timestamps, measured QPU usage), analysed results, and the exact submit script |
| `4_code_changes/` | The diff of our simulator speed-up, driver scripts and HPC scripts |
| `5_speed/` | The speed crossover: chart, numbers and script |

The same pilot and reconstruction outputs are also unpacked in [`../companion/IBM_Qiskit_Hackathon/`](../companion/IBM_Qiskit_Hackathon/).
