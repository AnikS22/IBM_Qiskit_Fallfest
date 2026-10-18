# R2: Ultrasound CT, Full-Waveform Inversion and the Compute Bottleneck

Prepared 2026-10-17 for the Aperion deck (Qiskit Fall Fest 2026).

**Key to labels.** A **Verified** row was checked against the primary source text: article full text via PMC BioC, the Nature supplementary PDF, the IT'IS database file, or a PubMed/Crossref record. A **Derived** row is our own arithmetic on verified inputs, and the deck should say so. **Secondary** means the number comes only from press coverage. **Unverified** means we could not confirm it.

**Primary paper.** G = Guasch L, Calderón Agudo O, Tang M-X, Nachev P, Warner M. "Full-waveform inversion imaging of the human brain." *npj Digit. Med.* 3, 28 (2020). doi:[10.1038/s41746-020-0240-8](https://doi.org/10.1038/s41746-020-0240-8)
- PMC copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC7060331/
- Supplementary Information PDF ("G-SI"): https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_MOESM1_ESM.pdf

---

## 1. Guasch et al. 2020: verification of the deck's numbers

| Claim | Number | Source | Exact quote / location | Confidence |
|---|---|---|---|---|
| Transducers | 1,024, each acting as both source and receiver | [G](https://pmc.ncbi.nlm.nih.gov/articles/PMC7060331/) | Methods, *In silico model*: "We used 1024 transducers that acted as both sources and receivers, generating just over a million source-receiver records of acoustic pressure, each record lasting 240 μs." Fig. 1c: "Prototype helmet containing 1024 transducers held rigidly in a 3D-printed framework." | Verified |
| Acquisition time | ~2 s | G | Discussion: "it takes ~2 seconds in total to acquire a full data set for all 1024 sources each recorded on 1024 receivers." | Verified |
| Caveat on the 2 s | "a few tens of seconds" in practice | [G-SI](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_MOESM1_ESM.pdf) p.7 | "successive sources can be safely activated about every 2 ms … Acquisition of a complete dataset therefore requires only about two seconds … With these additional considerations [repeat firing, triggering between heartbeats], data acquisition will still be complete within a few tens of seconds." | Verified |
| Compute time | ~32 h elapsed, for the Fig. 3 result | G | Discussion: "The results shown in Fig. 3 required ~32 hours elapsed time to complete, running on a conventional cluster of 128, CPU-based, 24-core, compute nodes." | Verified |
| Cores | 128 × 24 = 3,072 | G (arithmetic) | The paper says "128, CPU-based, 24-core, compute nodes". The figure 3,072 does not appear in the paper. | Derived |
| Hardware peak | ~60 TFLOPS | G | "The hardware that we used has a peak performance of ~60 tera-flop" | Verified |
| Target | <10 min | G | "Our target is to reduce this elapsed time to below 10 minutes; this requires a speed up of ~200 times." | Verified |
| Speed-up needed | ~200× | G | Same sentence. Check: 32 h = 1,920 min, and 1,920 / 10 = 192. | Verified |
| Peak needed | ~12 PFLOPS | G | "requires hardware capable of operating usefully at a peak of ~12 peta-flop." | Verified |
| How 12 PFLOPS could be reached | A small array of ≥1 PFLOPS GPU servers | G | "Individual high-performance GPU-based servers are currently able to achieve speeds in excess of one peta-flop, so that a small array of these would in principle be capable of producing a final model in < 10 minutes." | Verified, but a projection, not a measurement |
| Proposed GPU system | 12 servers × 8 GPUs (64 GB each); ~USD 100k per server; ~$1.2 M capital, ~$2 M installed | G-SI pp.7–8, *Speed of FWI computation* | "2-PetaFLOP GPU-based servers, with a total of 512 GB of GPU memory distributed across 8 GPUs" … "Across twelve such servers, we can therefore invert 96 sources simultaneously" … "The capital cost of this system is about $1.2 million, and perhaps $2 million once it is powered, cooled and configured." | Verified, but a projection |
| Cost per inversion | ~$15 at full utilisation; "a few tens of dollars" realistically | G and G-SI p.8 | G-SI: "about $15 per FWI-run provided that the hardware is utilised, on average, about three times an hour to generate about 26,000 images per year … the true amortised capital cost is consequently likely to be a few tens of dollars per FWI job." Main text: "a few tens of dollars to invert a 3D transcranial dataset on a 500-μm grid." | Verified |
| Share of compute spent on wave propagation | >95% | G-SI p.8 | "More than 95% of the compute required for an FWI inversion is spent propagating waves through a model using that propagator" | Verified. **This is the key justification for targeting the forward solver.** |
| Peak frequency | 400 kHz | G | "a three-cycle tone burst having a peak amplitude at a frequency of 400 kHz" | Verified |
| Usable band | ~100–850 kHz | G | "a useful bandwidth for FWI extending from ~100–850 kHz" | Verified |
| Grid spacing | 0.5 mm (500 μm) | G | Methods: "We used the MIDA 3D numerical model of the human head, at the original sample spacing of 500 μm"; Results: "the 500 μm grid that we used to represent the model" | Verified |
| Number of model parameters | ~10⁸ | G | Methods, *FWI algorithm*: "For the 3D model shown in Fig. 3, this hyper-surface had ~10⁸ dimensions." (In the PMC text the superscript is flattened to "108".) | Verified |
| **440³ grid / 85 M cubes** | **Not in the paper** | (none) | G gives no grid dimensions. 440³ = 85.2 M cells, which is about 220 mm per side at 0.5 mm. The paper's ~10⁸ cells corresponds to about 464³. MIDA's MRI field of view was 240 × 240 mm at 500 μm ([Iacono 2015, PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0124126)), so ≥480 cells in-plane. | **Unverified. Rephrase as "~10⁸ grid cells of 0.5 mm (Guasch 2020)."** |
| Resolution | ~0.9 mm (half-wavelength at 850 kHz) | G-SI p.5 | "the maximum frequency employed is about 850 kHz, having a wavelength of about 1.8 mm in the brain … The corresponding resolution for FWI is half the wavelength, that is about 0.9 mm." Time-of-flight tomography gives ~19 mm, so FWI is "about 20 times better resolved in linear dimension". | Verified |
| Iteration schedule | 8 frequency bands × 10 iterations = 80 iterations, each using ~1/10 of the sources | G | Methods, *FWI iteration*: "eight finite-frequency bands … Within each frequency band, we used ten iterations in total, using a tenth of the data at each iteration, so that data from each source was used just once per frequency band." G-SI: "we used about 100 sources per iteration." | Verified |
| Cycle-skipping criterion | Half a cycle | G | "the data generated by the starting model must not be shifted in time by more than half a wave cycle at the lowest frequencies … When that condition is not met, the data are 'cycle skipped', and FWI will then typically fail." | Verified |
| Skull effect on the signal (ex vivo) | Arrival advanced ~2.5 μs (one cycle at 400 kHz); amplitude reduced ~5× (≈14 dB) | G | Results: "The principal effect of interposing the skull is to advance the arrival time by ~2.5 μs, which corresponds to one cycle at the 400-kHz dominant frequency, and to reduce the transmitted amplitude by about a factor of five." The paper also says "This delay means that the observed data are cycle skipped". | Verified (14 dB = 20·log₁₀5 is derived) |
| In vivo SNR | 39 dB average; FWI robust below 2 dB | G | "Signal-to-noise ratios calculated in this way for the in vivo data, averaged over all orientations, were 39 dB … FWI remains robust at signal-to-noise ratios below 2 dB." | Verified |
| What "in vivo" covered | Single-channel transcranial traces from one author, **not an image** | G | "using one of the authors as a subject". Fig. 6 shows "Un-processed, un-stacked, transcranial, ultrasound signals … generated using a single source and single receiver". | Verified |
| Haemorrhage result | Recovered and auto-segmented, **in silico only** | G, Figs 8–9 | "The haemorrhage is well recovered by full-waveform inversion at high resolution in all slices." "The target pathology is well recovered in the FWI image, and has good tissue contrast with other features of the brain." The model used "physical properties for blood-infused soft tissue" and "a homogeneous starting model for the brain, and the true model for the skull". The paper gives no size, volume or contrast in numbers. | Verified. **Starting from the true skull is a caveat.** |
| Prototype weight and power | ~30 kg and ~350 W now; portable target <10 kg | G-SI p.7 | "In total it weighs about 30 kg and consumes about 350 W … the total weight would likely be less than 10 kg." | Verified |
| Data volume | ~2 GB raw, a few hundred MB after compression | G-SI p.7 | "The total, uncompressed, volume of data acquired will be about 2 GB" | Verified |
| License | CC BY 4.0 | [Nature page](https://www.nature.com/articles/s41746-020-0240-8) | "Open Access This article is licensed under a Creative Commons Attribution 4.0 International License … The images or other third party material in this article are included in the article's Creative Commons license, unless indicated otherwise in a credit line to the material." Crossref license field: creativecommons.org/licenses/by/4.0. | Verified. No figure caption carries a third-party credit line. |

### Figures in Guasch 2020 (all CC BY 4.0; credit "Guasch et al., npj Digit. Med. 3, 28 (2020), CC BY 4.0")

Every figure URL follows the pattern `https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_FigN_HTML.png`. Replace N with the figure number.

| Fig | What it shows (caption) | Direct URL | Deck use |
|---|---|---|---|
| 1 | "Experimental geometry": (a) 3D transducer array, (b) a wavefield snapshot dominated by skull reflections, (c) the 1,024-transducer prototype helmet | [Fig1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig1_HTML.png) (PMC mirror: [jpg](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/417c/7060331/43185939192a/41746_2020_240_Fig1_HTML.jpg)) | Slides 5/6: the helmet. Slide 7: wavefield snapshot. |
| 2 | 2D brain without skull: time-of-flight tomography vs FWI | [Fig2](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig2_HTML.png) | Why FWI rather than ray tomography |
| 3 | "Models of acoustic wave speed": true, starting (true skull, otherwise homogeneous) and recovered models, in 3 orthogonal sections | [Fig3](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig3_HTML.png) | Slide 8: "this is what 32 h buys you" |
| 4 | Homogeneous (water) start: conventional FWI fails; AWI, and AWI followed by FWI, succeed | [Fig4](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig4_HTML.png) | Slide 8: nonconvexity / cycle skipping |
| 5 | 3D data inverted with 2D FWI vs 2D data with 2D FWI (2D is inadequate) | [Fig5](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig5_HTML.png) | Why the problem must be 3D (so the cost is unavoidable) |
| 6 | Un-processed in vivo transcranial traces (single source and receiver) | [Fig6](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig6_HTML.png) | Signal gets through the skull |
| 7 | Ex vivo skull vs in silico data, with and without skull | [Fig7](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig7_HTML.png) | Slide 7: "delayed pulse" |
| 8 | "Recovery of a large haemorrhage by FWI": true vs recovered slices | [Fig8](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig8_HTML.png) | Slide 6: the clinical payoff |
| 9 | Auto-segmented haemorrhage: true vs FWI | [Fig9](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41746-020-0240-8/MediaObjects/41746_2020_240_Fig9_HTML.png) | Optional |

---

## 2. Follow-up work by the Imperial group and others, 2020–2026

| Claim | Number | Source | Exact quote / location | Confidence |
|---|---|---|---|---|
| Stride (open-source USCT/FWI platform) | Python; Devito-generated solvers; Mosaic parallel runtime | Cueto C, Bates O, Strong G, Cudeiro J, Luporini F, Calderón Agudo O, Gorman G, Guasch L, Tang M-X. *Comput. Methods Programs Biomed.* 221, 106855 (2022). doi:[10.1016/j.cmpb.2022.106855](https://doi.org/10.1016/j.cmpb.2022.106855); arXiv [2110.03345](https://arxiv.org/abs/2110.03345) | Abstract: "The wave-equation solvers are generated automatically using Devito … the parallelisation routines are provided through the custom actor-based library Mosaic." | Verified |
| Stride 3D head benchmark | 0.75 mm grid; 367 × 411 × 340 grid ("more than 51 million unknown parameters"); 1,024 transducers; 500 kHz; 300 μs; dt = 0.150 μs (2,000 steps); CFL 0.60; 100–600 kHz; 8 iterations per band; 128 shots per iteration | arXiv 2110.03345v3, §3 (3D example) | "The model is sampled with a spacing of 0.750 mm … resulting in a grid of size 367×411×340 and more than 51 million unknown parameters … Modelling was carried out over 300 µs, with time steps of 0.150 µs (maximum CFL constant of 0.60)." | Verified |
| Stride per-shot cost | **5.82 ± 0.36 min per shot gradient** (1 forward + 1 adjoint) on a 128-core AMD EPYC 7742 node (32 OpenMP threads) | same | "each shot gradient calculation took 5.82 ± 0.36 min, including time spent in work distribution." | Verified |
| Stride scaling | Near-ideal up to 128 nodes (~2% loss) | same | "Mosaic achieves nearly ideal scaling up to 128 compute nodes … approximately, to a 2% loss in performance" | Verified |
| Algorithmic speed-up | **30% less time**, up to 1000× less memory (2D numerical experiments) | Protopapa L, Cueto C, et al. arXiv [2111.04700](https://arxiv.org/abs/2111.04700) (2021) | "our methods lead to a 30% reduction in reconstruction time and up to three orders of magnitude less memory". Intro: "realistic 3D imaging problems taking tens of hours to compute in high-performance computer clusters and requiring hundreds of gigabytes in memory." | Verified |
| First transcranial-like FWI prototype | Ring of 40 transducers with rotations; 2.5D phantom | Cudeiro-Blanco J … Guasch L. *Ultrasound Med Biol* 48(10):1995 (2022). doi:[10.1016/j.ultrasmedbio.2022.05.023](https://doi.org/10.1016/j.ultrasmedbio.2022.05.023) | "We have built a ring of 40 transducers … To our knowledge, this is the first prototype ever used for transcranial-like imaging." | Verified (PubMed abstract) |
| Dual-probe phantom | 2D FWI of a 2:5-scale brain phantom inside a 3D-printed skull mimic, using commercial cardiac probes | Robins TC, Cueto C, Cudeiro J, Bates O, Calderón Agudo O, Strong G, Guasch L, Warner M, Tang M-X. *Ultrasound Med Biol* 49(10):2302 (2023). doi:[10.1016/j.ultrasmedbio.2023.06.001](https://doi.org/10.1016/j.ultrasmedbio.2023.06.001); [PMC7616382](https://pmc.ncbi.nlm.nih.gov/articles/PMC7616382/) | "the first demonstration of this method in recovering a high-resolution 2-D reconstruction of a brain and skull ultrasound imaging phantom using experimentally acquired data." | Verified |
| Skull registration without MRI (MOFI) | In silico and in vitro only | Bates O, Cueto C, Coleman C, Smith CAB, Guasch L, Calderón Agudo O. arXiv [2601.14533](https://arxiv.org/abs/2601.14533) (Jan 2026) | "We demonstrate that MOFI accurately recovers the position of skull templates in silico and in vitro" | Verified |
| **In vivo 3D FWI brain image from this group** | **None found** | arXiv author search, PubMed, web search | No 2023–2026 in vivo transcranial FWI image from Guasch/Warner/Tang was found. Published work is in silico, phantom, or ex vivo. | Verified absence, as of 2026-10-17 (searches can miss things) |
| Clinical trials | **None registered** | ClinicalTrials.gov API v2, queries "full waveform inversion", "ultrasound tomography brain", "transcranial ultrasound tomography" | No FWI or USCT brain-imaging trial was returned. | Verified absence |
| Measured <10 min 3D brain FWI | **Not demonstrated** | (none) | The 10-minute figure remains a projection in G-SI (12 GPU servers). No published measured wall-clock time for full 3D transcranial FWI under 10 minutes was found. Stride's measured 5.82 min per shot gradient (CPU) × ~100 shots per iteration × ~80 iterations, if run serially, is ~775 node-hours. | Derived / absence |
| Rochester group (Duric, the SoftVue lineage): stroke phantoms | In silico, in vitro, ex vivo. Hemorrhages "as small as 0.7 cm" visualised through a replica skull. 100–700 kHz (ideal) vs 300–700 kHz (current hardware). | Mitcham T … Duric N. *Med Phys* 52(10):e18090 (2025). doi:[10.1002/mp.18090](https://doi.org/10.1002/mp.18090) | Abstract: "hemorrhages as small as 0.7 cm in diameter can be visualized through the replica skull using UST" | Verified (PubMed abstract) |
| SoftVue, cadaver brain through skull | ~0.75 mm resolution without skull; a 40-cc water-filled "hemorrhage" inclusion visualised through cadaver skull | Marini TJ … Duric N. *Eur J Radiol* 205:113193 (2026). doi:[10.1016/j.ejrad.2026.113193](https://doi.org/10.1016/j.ejrad.2026.113193) | "The spatial resolution of the images without the skull was approximately 0.75 mm … the implanted water-filled inclusion mimicking hemorrhage was visualized through the skull" | Verified (PubMed abstract) |
| Deep-learning shortcut (alternative to the quantum approach) | 1.13 s per 2D slice (PEN-FWI) | Ren J et al. *IEEE TMI* 43(6):2332 (2024). doi:[10.1109/TMI.2024.3363144](https://doi.org/10.1109/TMI.2024.3363144) | "The imaging time for a horizontal cross-sectional image of the brain is only 1.13 seconds." | Verified (abstract). 2D, simulation and lab only. **Name this as a competing approach.** |

---

## 3. Other USCT and transcranial physics

| Claim | Number | Source | Exact quote / location | Confidence |
|---|---|---|---|---|
| Delphinus SoftVue: FDA PMA | Approved Oct 12, 2021; adjunct to mammography for dense breasts | [BioSpace / Delphinus press release](https://www.biospace.com/delphinus-receives-fda-approval-for-its-softvue-3d-whole-breast-ultrasound-tomography-system) | "premarket approval (PMA)" … "adjunct to digital mammography in the screening of asymptomatic women with dense breast tissue". Scan time: "an average of three minutes" per breast. Records "reflection, speed and direction of sound waves". | Verified (company PR; PMA number not confirmed) |
| Butterfly Ultrasound-on-Chip | ">9,000" CMUT elements; 1–12 MHz | [butterflynetwork.com/technology](https://www.butterflynetwork.com/technology) | "over 9,000 silicate elements that vibrate to generate and receive sound waves"; "9,000 element 2D matrix array"; "1-12MHz frequency range"; "capacitive micromachined ultrasonic transducer (CMUT) technology" | Verified |
| Butterfly module count in the Midjourney prototype | 40 modules; 8,960 transducers per chip, each 200 μm | [Medical Design & Outsourcing, J. Hammerand, Jun 18 2026](https://www.medicaldesignandoutsourcing.com/?p=279249) | Butterfly: "40 Butterfly Ultrasound-on-Chip imaging modules per system"; "8,960 transducers"; "just 200 microns wide" | Secondary (quotes Butterfly) |
| Midjourney "Ultrasonic CT" announced | June 18, 2026 | [Decrypt, J. Nelson](https://decrypt.co/371606/midjourney-pivots-ai-images-medical-imaging-build-better-mri); MD&O as above | Decrypt dates it June 18, 2026. The primary page [midjourney.com/medical](https://midjourney.com/medical) returned 403 to our fetcher. | Secondary |
| Midjourney claims | "60 seconds"; "in many ways superior to even MRI"; ~500,000 transducers; "over two petaflops" | MD&O; Decrypt | MD&O quoting Midjourney: "just sound and water and 60 seconds". DeVivo (Butterfly CEO): "about half a million sensors scanning simultaneously and over two petaflops of processing power." Decrypt: "approximately 500,000 ultrasonic transmitters and receivers." | Secondary. **Inconsistency: 40 × 8,960 = 358,400, not ~500k.** |
| Spa and scale targets | SF spa "around the end of 2027"; >50,000 scanners by ~2031; "a billion scans a month" | MD&O; Decrypt | "Around the end of 2027 we'll open up the Spa"; "a fleet of over 50,000 scanners worldwide" by 2031; Decrypt: "over the next six years". | Secondary |
| Regulatory status | No FDA clearance; body-composition maps first | MD&O; Decrypt | MD&O: diagnostic use "requires FDA approval"; "Midjourney did not say whether this equipment actually exists as a prototype or if the video is AI-generated." | Secondary |
| Reconstruction method | **Undisclosed** | MD&O; Decrypt | Decrypt says only "AI-powered image reconstruction" and "a massive cluster where thousands of computers split the task". No solver is named. | Secondary. **Say "solver undisclosed".** |
| Unconfirmed: "~20 min per scan" for the current prototype | (none) | Only an aggregator ([letsdatascience](https://letsdatascience.com/news/midjourney-unveils-full-body-ultrasonic-scan-spa-cd947611)) | (none) | **Unverified. Do not use.** |
| Cortical skull sound speed | 2,813.7 m/s (IT'IS mean, n=13, range 2,190–3,360) | IT'IS V4.1 (see §4) | Row "Skull Cortical" | Verified |
| Skull attenuation (cortical) | 54.553 Np/m/MHz (≈ **4.7 dB/cm/MHz**), linear in f | IT'IS V4.1, "Attenuation Constant" α₀ for Skull Cortical, b = 1 | Conversion: 54.553 × 8.686 / 100 = 4.74 dB/cm/MHz | Verified value; conversion derived |
| Skull attenuation (cancellous/diploë) | 47 Np/m/MHz^1.2 (≈4.1 dB/cm at 1 MHz) | IT'IS V4.1 "Skull Cancellous" | α₀ = 47, b = 1.2 | Verified value; conversion derived |
| Measured skull attenuation | 13.3 ± 0.97 dB/cm across ~8 mm samples; absorption only 2.7 dB/cm (longitudinal) | Pinton G, Aubry J-F, Bossy E, Muller M, Pernot M, Tanter M. *Med Phys* 39:299 (2012). doi:[10.1118/1.3668316](https://doi.org/10.1118/1.3668316) | "The experimentally measured attenuation across the approximately 8 mm thick samples was 13.3 ± 0.97 dB/cm." "only a small part of the attenuation is due to absorption … the majority … is due to reflection, scattering, and mode conversion." | Verified. The test frequency is not stated in the abstract (believed ~1 MHz; check the full text before quoting "per MHz"). |
| Why the 0.5–1 MHz window | Diploë dominates skull loss; the transkull window is 0.5–1.0 MHz | Fry FJ, Barger JE. *J Acoust Soc Am* 63:1576 (1978). doi:[10.1121/1.381852](https://doi.org/10.1121/1.381852) | "The dominant feature in determining human adult skull losses is the middle layer (diploe) of cancellous bone … with selection of appropriate frequencies (0.5-1.0 MHz) … it will be possible to perform clinically significant transkull diagnostic imaging" | Verified |
| Why conventional (pulse-echo) ultrasound fails through adult skull | Skull distorts and attenuates; ~33% intensity reflected at each water–bone interface | G (Intro and Results); Pinton 2012; impedance calc from IT'IS | G: "conventional ultrasound neuroimaging" fails because the skull distorts the signal; scattering at bone interfaces is "the principal mechanism for transcranial signal attenuation". Derived: Z_bone = 1908 × 2813.7 = 5.37 MRayl, Z_water = 994 × 1482 = 1.47 MRayl, R = ((5.37 − 1.47)/(5.37 + 1.47))² ≈ 0.33. | Quotes verified; R derived |
| Conventional-imaging frequency vs FWI | Diagnostic probes are 1–12 MHz (Butterfly); FWI uses 0.1–0.85 MHz | Butterfly; G | Attenuation scales ~linearly with f, so at 5 MHz cortical loss is ~24 dB/cm per IT'IS (derived), roughly 5× the loss at 1 MHz. | Derived |

---

## 4. Tissue sound speeds (for slide 11)

**IT'IS V4.1.** Hasgall PA et al., IT'IS Database for thermal and electromagnetic parameters of biological tissues, Version 4.1 (2022). Downloaded file: https://itis.swiss/assets/Downloads/TissueDb/Database-V4-1.zip, file "Thermal_dielectric_acoustic_MR properties_database_V4.1(Excel).txt", column "Tissue Speed of Sound [m/s]". Browsable page: https://itis.swiss/virtual-population/tissue-properties/database/acoustic-properties/speed-of-sound/

**Guasch SI Table 1.** G-SI, "Supplementary Table 1. Physical properties of tissue types", pp. 9–11. The values match IT'IS almost exactly; Guasch drew on the same literature.

| Tissue | IT'IS V4.1 mean (m/s) [SD, n, range] | Guasch SI Table 1 (m/s) | Density (kg/m³) | Confidence |
|---|---|---|---|---|
| Brain (generic) | **1,546.3** [20.2, n=17, 1,506–1,565] | brainstem 1,546.3 | 1,045.5 | Verified |
| Brain grey matter | 1,500 (**placeholder**: n = −1, IT'IS default for missing data) | **1,505.0** | 1,044.5 | Verified. Grey-matter value is weakly sourced. |
| Brain white matter | 1,552.5 [29.0, n=2] | 1,552.5 | 1,041.0 | Verified |
| Blood | **1,578.2** [11.3, n=9, 1,559–1,590] | 1,578.2 (arteries, veins) | 1,049.8 | Verified |
| CSF | 1,504.5 [3.5, n=2] | 1,504.5 | 1,007.0 | Verified |
| Skull cortical (inner/outer table) | **2,813.7** [337, n=13, 2,190–3,360] | 2,813.7 | 1,908 | Verified |
| Skull cancellous (diploë) | 2,117.5 [289, n=5] | 2,117.5 | 1,178.3 | Verified |
| Skull (IT'IS composite entry) | 2,770.35 (n=1) | (none) | 1,908 | Verified |
| Mandible / vertebra | 3,514.9 (IT'IS "Bone (Cortical)") | 3,514.9 | 1,908 | Verified |
| Skin (epidermis/dermis) | 1,624 [91.8, n=3] | 1,624.0 | 1,109 | Verified |
| Subcutaneous fat | 1,440.2 [21.9, n=16] | 1,477.0 (subcut.) / 1,440.2 (adipose) | 911 | Verified |
| Muscle (temporalis, scalp) | 1,588.4 [21.6, n=24] | 1,588.4 | 1,090.4 | Verified |
| Dura | 1,500 (placeholder) | 1,600.0 | 1,174 | Verified |
| Water | 1,482.3 (n=1; ~20 °C) | background 1,480.0 | 994 | Verified. The paper's prose rounds to "~1500 ms⁻¹". |

**Contrast that matters for stroke.** Blood (1,578) minus brain grey matter (1,505) is about 73 m/s, roughly a 5% contrast. Against white matter (1,552.5) the contrast is only ~26 m/s (~1.7%). Both figures are derived.

---

## 5. FWI mathematics references

| Claim | Number | Source | Exact quote / location | Confidence |
|---|---|---|---|---|
| FWI founded as least-squares waveform fitting | (none) | Tarantola A. "Inversion of seismic reflection data in the acoustic approximation." *Geophysics* 49(8):1259–1266 (1984). doi:[10.1190/1.1441754](https://doi.org/10.1190/1.1441754) | Title and bibliographic data verified via Crossref (paywalled; text not quoted) | Verified (bibliographic) |
| Standard FWI review | (none) | Virieux J, Operto S. "An overview of full-waveform inversion in exploration geophysics." *Geophysics* 74(6):WCC1–WCC26 (2009). doi:[10.1190/1.3238367](https://doi.org/10.1190/1.3238367) | Bibliographic data verified via Crossref | Verified (bibliographic) |
| Adjoint-state gradient | Gradient for one source = 1 forward + 1 adjoint solve, then cross-correlation | Plessix R-E. *Geophys J Int* 167(2):495–503 (2006). doi:[10.1111/j.1365-246X.2006.02978.x](https://doi.org/10.1111/j.1365-246X.2006.02978.x). Operational confirmation: Stride §3 ("one forward propagation and one adjoint propagation of the acoustic solver") and Protopapa 2021 ("every iteration involves solving the wave equation over a discretised spatiotemporal grid and storing the numerical solution to calculate gradient updates") | Verified |
| Multiscale low-to-high frequency strategy (against cycle skipping) | (none) | Bunks C, Saleck FM, Zaleski S, Chavent G. *Geophysics* 60(5):1457 (1995). doi:[10.1190/1.1443880](https://doi.org/10.1190/1.1443880). In practice: G uses 8 bands from 100 to 850 kHz. | Verified (bibliographic + G) |
| Nonconvexity | "non-linear and non-convex" | G, Methods | "Typically, the problem will be non-linear and non-convex, and therefore it requires that the model is updated iteratively, and that the starting point is within the basin of attraction of the global minimum." | Verified |
| Cost scaling | Cost ∝ I × S × N_t × V (× 2 for forward + adjoint) | Structure from G and Stride (each iteration = S shots × [forward + adjoint] over N_t steps on V cells). G-SI: >95% of compute is wave propagation. | Our formalisation; each factor is cited | Derived |
| Guasch-scale plug-in | I ≈ 80, S ≈ 100 per iteration, N_t ≈ 2,400, V ≈ 10⁸ → ~4 × 10¹⁵ cell-updates | I and S from G; V from G; N_t = 240 μs / ~0.1 μs (dt scaled from Stride's 0.15 μs at 0.75 mm to 0.5 mm) | 80 × 100 × 2 × 2,400 × 10⁸ ≈ 3.8 × 10¹⁵ | **Derived estimate; label it.** |
| Grid scaling with frequency | V ∝ f_max³ and N_t ∝ f_max, so cost ∝ f_max⁴ per solve | Protopapa 2021: "The computational cost depends on the grid size, which is controlled by the maximum frequency being modelled" (they use n = 5 grid points per wavelength) | Quote verified; f⁴ derived |
| Stability (CFL) | dt ≤ C·dx / c_max; Stride used CFL 0.60 | Stride §3 | "time steps of 0.150 µs (maximum CFL constant of 0.60)" | Verified. **c_max is set by bone (2,800–3,500 m/s), so bone shrinks dt about 2× relative to soft tissue.** |

---

## Slide mapping

**Slide 5: Current tech table**

| Modality | Images brain through skull? | Status | Cite |
|---|---|---|---|
| CT / MRI | Yes | Hospital-bound | G intro: "transport to hospital routinely introduces delays of an hour or more" |
| Handheld ultrasound (Butterfly, 9,000-element CMUT, 1–12 MHz) | No (adult skull) | FDA-cleared, portable | Butterfly site; Fry & Barger 1978 |
| Breast USCT (Delphinus SoftVue) | n/a (breast); cadaver-brain feasibility 2026 | FDA PMA Oct 2021 | BioSpace PR; Marini 2026 |
| Transcranial FWI (Imperial) | In silico, plus ex vivo/phantom | Research, no trials | G 2020; Robins 2023 |
| Midjourney Ultrasonic CT | Whole body; brain not claimed | Pre-regulatory; solver undisclosed | MD&O; Decrypt (Jun 18 2026) |

**Slide 6: The caveat**
- Scan ~2 s (practical: "a few tens of seconds", G-SI) versus compute ~32 h on 128 × 24-core CPU nodes (~60 TFLOPS peak).
- Target <10 min, which needs ~200× speed-up, or ~12 PFLOPS.
- A projected 12 × 8-GPU servers (~$1.2 M) would cost ~$15 to "a few tens of dollars" per scan. This is not yet demonstrated.
- >95% of the compute is the wave propagator (G-SI). That is our target.
- Image: Fig. 8 (haemorrhage, in silico) plus Fig. 1c (helmet).

**Slide 7: The forward problem**
- Acoustic wave equation, (1/c²)∂²p/∂t² = ∇²p + s. G's synthetic data were "purely acoustic" (Methods).
- Delayed pulse: the skull shifts arrival by ~2.5 μs, one full cycle at 400 kHz, and cuts amplitude ~5× (G, Fig. 7).
- Grid update: second-order finite differences in time on a regular cubic grid ("high-order time-stepping finite-differences", G-SI).
- Stability: CFL. Stride used dt = 0.15 μs at 0.75 mm with CFL 0.60. Bone at ~2,800 m/s sets the time step.

**Slide 8: The inverse problem**
- Misfit f(m) = ½‖d_obs − F(m)‖².
- Adjoint gradient: 1 forward + 1 adjoint solve per source (Plessix 2006; Stride).
- Update: m ← m − α·P·∇f, with preconditioned steepest descent (G).
- Cost O(I · S · N_t · V). Guasch-scale: 80 × ~100 × ~2,400 × ~10⁸, giving ~4 × 10¹⁵ cell-updates (derived).
- Nonconvex, with the half-cycle cycle-skipping rule (G). Fig. 4 shows a water start failing without AWI.

**Slide 11: Classical 1D baseline speeds**
- Water 1,482 (IT'IS) / 1,480 (Guasch background)
- Scalp 1,624
- Fat 1,440
- Skull cortical 2,814
- Diploë 2,118
- CSF 1,504.5
- Grey matter 1,505 (Guasch) / white matter 1,552.5
- Blood 1,578.2
- Generic "brain" 1,546.3 (IT'IS)

Use the layered 1D profile scalp → cortical → diploë → cortical → CSF → brain → blood clot.

---

## Images & graphs

| # | Graphic | Data / source | License |
|---|---|---|---|
| 1 | **Compute timeline vs target** (log-y bar or step chart): 2 s scan; 32 h measured (2020 CPU); projected ~10 min on 96 GPUs (G-SI); target <10 min; a reference line for the "golden hour". Optional: Stride's 5.82 min per single-shot gradient. | G, G-SI, Stride | Our own chart from cited numbers (free to use) |
| 2 | **FLOPS gap**: 60 TFLOPS (used) vs 12 PFLOPS (needed), 200× ratio | G Discussion | Own chart |
| 3 | **FWI loop diagram**: model m → forward solve (wave equation) → synthetic d → misfit vs observed → adjoint solve → gradient → update → repeat (×80). Annotate ">95% of time" on both solve boxes. | G Methods; G-SI p.8 | Own diagram |
| 4 | **Sound-speed map**: G Fig. 3 (true / start / recovered), and Fig. 8 for haemorrhage | Links in §1 | CC BY 4.0, attribute Guasch et al. 2020 |
| 5 | **Helmet photo**: G Fig. 1c | Link in §1 | CC BY 4.0 |
| 6 | **Wavefield snapshot**: G Fig. 1b (skull reflections) for slide 7 | Link in §1 | CC BY 4.0 |
| 7 | **1D layered sound-speed profile** (bar or step plot) through the skull | §4 table (IT'IS + G-SI Table 1) | Own chart; cite IT'IS V4.1 and Guasch SI |
| 8 | **Cost scaling bar**: I, S, N_t, V factors multiplied up to ~4 × 10¹⁵ | §5 derived row | Own chart, labelled "estimate" |
| 9 | **Resolution comparison**: time-of-flight ~19 mm vs FWI ~0.9 mm at 850 kHz | G-SI p.5 | Own chart |
| 10 | Optional: G Fig. 4 (cycle skipping: a water start fails) | Link in §1 | CC BY 4.0 |

Avoid reusing Midjourney or Butterfly imagery: it is proprietary, and its provenance is unclear (MD&O: "did not say whether … the video is AI-generated").
