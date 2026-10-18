# Aperion: 5-Minute Talk Script

About 700 words. That's roughly 5 minutes at a calm pace. Each person presents the question they asked on the team slide, so the handoffs follow the chain of thought.

Main slides: 1 cover · 2 team · 3 problem · 5 helmet · 6 caveat · 8 why quantum · 10 seven cubes · 13 results · 15 readout wall · 16 hybrid · 19 close. Everything else is backup for Q&A.

---

## Speaker 1 · Clinical (≈1:10)

**[1 · Cover]**
"We're Aperion. Our project asks whether a quantum computer can speed up the slowest step of a new kind of stroke scan, and we'll show you exactly where it works and where it doesn't."

**[2 · Team]**
"We built this as a chain of four questions, one each. Mine was: why does a stroke patient wait for a scanner? [Name] asked why the new technology takes 32 hours. [Name] asked whether that step is quantum-shaped. [Name] asked what the smallest real test is. Each of us will walk you through our part."

**[3 · Problem]**
"Someone collapses with a stroke. Paramedics arrive fast. But there are two kinds of stroke. A clot is treated with a clot-busting drug. A bleed is made worse by that same drug. So nobody can treat until someone sees inside the head, and today that means a CT scanner in a hospital. Every minute of that wait, the patient loses about 1.9 million neurons."

## Speaker 2 · Research (≈0:50)

**[5 · Helmet]**
"Ultrasound is portable, but bone blocks it. In 2020, researchers at Imperial College published a way around that in *npj Digital Medicine*: a helmet of 1,024 ultrasound sensors and an algorithm borrowed from seismic imaging. In simulation it produced brain images sharp enough to see a bleed."

**[6 · Caveat]**
"Here's the catch. Recording the scan takes about two seconds. Turning it into an image took 32 hours on a 128-computer cluster. An emergency needs it in under ten minutes, about 200 times faster. The slow part is simulating sound through the head, over and over, for every sensor."

## Speaker 3 · Quantum (≈1:20)

**[8 · Why quantum]**
"So I asked: is that slow step quantum-shaped, or are we forcing it? Sound carries energy from place to place in the head, but the total stays fixed. A quantum computer works the same way: its operations move values around but keep their total fixed. That match means the sound simulation can be rewritten as a quantum circuit, an idea published by Costa, Jordan and Ostrander in 2019. In principle, 29 qubits could hold the sound in all 85 million points of a head."

*(If asked about other approaches → slide 9: annealing and optimization don't fit because this isn't a search problem; machine learning would need patient data.)*

**[15 · Readout wall]** *(Speaker 3 can also take this one after results)*
"But storing isn't reading. Each round, the algorithm needs about a billion numbers back. A quantum computer gives you one random outcome per run, and reading even one number to 1% accuracy takes about 10,000 runs. A graphics card hands back all billion at once. That's the real wall."

## Speaker 4 · Build (≈1:20)

**[10 · Seven cubes]**
"So we built the smallest honest test: one line of seven cubes from ear to ear, with scalp, skull, brain, skull, scalp. Same physics as the paper, two neighbours instead of six. We turned it into a Qiskit circuit."

**[13 · Results]**
"On a noise-free simulator, the circuit matches the classical simulation. On real IBM hardware, [backend], noise [did X], and error-reduction techniques recovered [Y]. Job ID is on the slide. What surprised us was [one sentence]."

**[16 · Hybrid]**
"So our design gives the quantum computer only questions with a one-number answer: how wrong is this guess overall, or is there a bleed, yes or no? Everything that needs many numbers stays on classical hardware."

## Speaker 1 · Close (≈0:20)

**[19 · Close]**
"Quantum fits the physics of this problem, and today it loses to GPUs on gate count, noise and readout. We can tell you exactly what would have to improve. The goal doesn't change: clot or bleed, answered before the hospital. Thank you."

---

## Plain-language explanations to keep handy

| Concept | Say it like this |
|---|---|
| Full-waveform inversion | "It's like guessing what's in a dark room by clapping and listening to the echoes. Guess, simulate the echo, compare, fix the guess, repeat." |
| Sound speed as an image | "Sound moves faster through bone than brain, and slightly faster through blood. A map of sound speed *is* a picture of the head." |
| Qubits storing 2ⁿ numbers | "Each extra qubit doubles the space. 30 qubits hold about a billion numbers, where a normal computer needs a billion memory slots." |
| Readout problem | "A library where every book is on the shelf, but you can only pull one random word per visit." |
| Shots | "Results come out as dice rolls. You roll thousands of times and count." |
| Noise / error mitigation | "Today's chips make a mistake every few hundred steps. Mitigation is statistical cleanup after the fact. It isn't a fix." |
| Why not faster? | "Sound moves one cube per tick on any computer. Quantum saves memory, not time steps." |

## Likely judge questions and who answers

| Question | Owner | Slide |
|---|---|---|
| Why quantum instead of classical? | Quantum | 8, 9 |
| What would need to improve to beat classical? | Quantum | 14, 18 |
| Walk me through your circuit. | Build | 10, 11 |
| What did you build vs reuse? | Build | 11 |
| How do you know it worked? | Build | 12, 13 |
| Is this clinically real? | Clinical | 17 (no clinical claim) |
| What would you do with another month? | Research | 18 |
| What did each of you contribute? | Everyone | 2 |

## Action shots (team slide)
Candid photos of each person mid-work, not posed headshots. One per person, portrait orientation, similar lighting:
- Clinical: at a whiteboard sketching the clot vs bleed decision
- Research: with the Guasch paper open, pointing at a figure
- Quantum: at a laptop with the circuit diagram on screen
- Build: looking at the IBM Quantum job results page
