# Pitch Deck Playbook (Qiskit Fall Fest)

About 5 minutes and about 9 slides. Every slide earns points on a specific rubric line. Judges include non-technical people.

| # | Slide | Time | Rubric it scores | What's on it |
|---|---|---|---|---|
| 1 | **The person** | 30s | Problem 15% | One real patient or clinician story. One photo or one number. No quantum yet. |
| 2 | **The problem, sized** | 30s | Problem 15% | Who it affects, how many people, cost or lives. One sentence a newcomer can repeat. |
| 3 | **How it's solved today & where it breaks** | 30s | Quantum Rationale 20% | The current classical method and the exact wall it hits (too slow, approximations fail, data too scarce). |
| 4 | **Why quantum (plain language)** | 40s | Quantum Rationale 20% | One analogy plus one diagram: why this problem is *quantum-shaped*. No hype words. |
| 5 | **What we built** | 40s | Technical 20% | Pipeline diagram: classical part → quantum part → output. Point out where the seam is. Show circuit / Qiskit features used. |
| 6 | **Results vs classical** | 40s | Results 10% + Hardware +5 | One chart: classical baseline vs simulator vs real IBM hardware vs mitigated. Error bars. Name the backend. |
| 7 | **Honest limits** | 30s | Quantum Rationale 20% (tie-breaker) | What this does NOT prove. What scale or hardware would be needed to beat classical, and roughly when. |
| 8 | **Impact & roadmap** | 20s | Q&A/Learning 10% | Back to the person from slide 1. What one more month looks like. Continue / narrow / stop. |
| 9 | **Team** | 10s | Teamwork 10% | Four faces, and what each person owned. Everyone speaks at some point. |

## Rules that win points
- **Open and close on the human.** Use the same person on slide 1 and slide 8.
- **One idea per slide.** Headlines should be sentences ("Classical solvers stall past 40 patients"), not labels ("Results").
- **Anti-hype is the flex.** Say "we found classical still wins at this size, and here's the crossover." The rubric explicitly rewards that over overclaiming.
- **Show the hardware job.** Screenshot the IBM job ID and backend name. It's +5 and judges are told to ask for it.
- **One chart, not five.** Baseline vs quantum, error bars, a one-line takeaway written on the chart.
- **Plain-language test.** Practice the one-sentence answer to "explain it to someone with no physics background." Judges literally ask this.
- **Stay within time.** Going over costs points on the Presentation 5.
- **Prep Q&A.** Each teammate owns the answers for their part. Likely questions:
  - Why quantum instead of classical?
  - What would need to improve to beat classical?
  - Walk me through your circuit.
  - What did you build vs reuse?
  - How do you know it worked?
  - What surprised you?
  - What did each of you contribute?
  - What would you do with another month?

## Visual style
- Dark or clean background, one accent color, big type (≥28pt body).
- Diagrams over bullets. If a slide has more than 3 bullets, cut it.
- Equations only in backup slides.

## Backup slides (for Q&A, not presented)
- Circuit diagram + transpiled depth / 2-qubit gate count
- Error-mitigation settings (resilience level, twirling, ZNE)
- Full benchmark table
- References (2–4 current papers)
