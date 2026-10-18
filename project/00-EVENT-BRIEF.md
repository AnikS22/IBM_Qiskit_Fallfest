# Florida Qiskit Fallfest Hackathon 2026: Event Brief

Source: https://quantumkev.github.io/Qiskit_Fall_Fest_2026/handbook/ (+ all sub-pages, saved as text in `site/`) and `qiskit-fall-fest-judging-rubric.xlsx`.

## Key dates
| Date | What |
|---|---|
| Oct 1 | Kickoff + challenge release (briefs live in private repo `challenges/`) |
| **Oct 17–18** | **Local events (this weekend)** |
| Oct 18 | Local ceremony |
| Oct 31 | First-place local winner packet + PR deadline |
| Nov 8 | State final |
| Nov 14 | State championship ceremony |

Theme: **"A decade of quantum on the cloud"** (10 yrs since IBM put a QPU on the cloud).

## Scoring (out of 100, plus up to +5 hardware bonus = 105)
Weighted = Σ(score 1–5 × weight) ÷ 5 × 100

| Criterion | Weight | What gets a 5 |
|---|---|---|
| Problem Definition & Relevance | 15% | Compelling, specific problem; realistic scope; impact clearly argued |
| **Quantum Rationale & Potential** | **20%** (also the **tie-breaker**) | Nuanced near-term vs future view; realistic about advantage; states what scale/hardware would be needed |
| **Technical Implementation (Qiskit)** | **20%** | Polished, documented, reproducible; advanced techniques used correctly (error mitigation, hybrid workflows) |
| Results & Validation | 10% | Baselines, error bars/repeated runs, simulator vs hardware, clear conclusions |
| Innovation & Creativity | 10% | "I hadn't thought of that" |
| Presentation & Communication | 15% | Accessible to anyone, still accurate, **within time (~5 min)** |
| Q&A, Teamwork & Learning | 10% | Every member contributes; growth story; realistic roadmap |

**Hardware bonus:** Simulator 0 · Real IBM device +3 · **Real device + noise analysis / error mitigation +5** (job results must be shown).

Judges' explicit notes:
- "3" = solid student project. 5 is reserved for exceptional.
- **"Reward honesty: a team that explains why quantum may NOT yet beat classical shows more understanding than one that overclaims."**
- Non-technical judges score Problem, Presentation, Results, Q&A, and judge technical criteria on whether you can explain clearly and honestly.
- Score spread of 20+ between judges triggers discussion, so consistency across judges matters.

## Accepted project types
1. **Mapped problem**: real problem → QUBO / Hamiltonian / kernel / circuit; small instance run; state the gap to real scale.
2. **Benchmark / comparison**: same problem classical vs quantum, metric defined *before* the run; report even if classical wins.
3. **Tool**: e.g. domain format → QUBO/Hamiltonian translator, resource estimator.
4. **Analysis**: rigorous "is this quantum-shaped?"; "not a fit yet" is a complete project.

Required sequence (non-optimization): Problem → Current method → Classical baseline → Quantum hypothesis → Experiment → Metrics → Evidence → Limitations → Recommendation (continue / narrow / pause / stop). **Success criteria written before any quantum run.**

Three problem shapes: **Optimization** (QAOA/QUBO, where classical is very strong), **Simulation** (chemistry; strongest theoretical case, but molecules in reach are "chemically uninteresting", so framing matters), **Learning/data** (quantum kernels; "most contested").

Reference example they want you to beat and not copy: **Hetionet**, quantum kernel link prediction for Compound-treats-Disease (hybrid stack PR-AUC 0.7987 vs RF 0.7838). Organizer Kevin Robinson co-authored it.

## Submission (PR to `main` of private repo robertloredo/FAU-Qiskit-Fallfest-2026)
Title: `[SUBMISSION] Team <name> — <project title>`, folder `submissions/team-<name>/` copied from `_TEMPLATE`.
- README.md (required)
- Notebook(s)/source (required)
- USE-CASE.md (required; the problem, industry, why it matters, what it would take to be real)
- requirements.txt (required if code)
- Slides / demo video (required)
- LIMITATIONS.md (strongly encouraged, and we should treat it as required)

## Hardware / tooling constraints
- IBM Quantum Open Plan, us-east: **10 min QPU per rolling 28 days per account**. Four teammates means four accounts and up to ~40 min if each one runs jobs.
- Use `qiskit` 2.x + `qiskit-ibm-runtime`, `QiskitRuntimeService()`, `StatevectorSampler`. **Not** `channel="ibm_quantum"`, `execute()`, `qiskit.Aer`, `IBMQ`.
- Develop on the simulator and submit to hardware once.

## Contacts
Lead Robert Loredo (rloredo2026@fau.edu) · Kevin Robinson (kevin@quantumglobalgroup.io) · Discord https://discord.gg/vz6uTbtJzR
