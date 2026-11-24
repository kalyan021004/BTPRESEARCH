# Report and slide plan

Every number comes from `report/generated/` (tables + `numbers.md`). Never type a result by hand.

## BTP report
1. **Introduction**: why EMG after stroke; why %MVC normalisation is a problem (earlier finding: 33 % vs
   6 % MVC exceedance); aim = MVC-free parameters that separate patients from healthy people.
2. **Data**: Mendeley dataset (citation, licence), 12 healthy + 10 stroke, 8 muscles, directions 1-6,
   missing stroke folders 7-9, file facts (RMS MVC files, 3-digit export).
3. **Methods**
   - Signal processing and reach detection (from config).
   - Table 1: the 10 parameters (`table1_definitions.md`), each with a one-line physiological meaning.
   - Statistics: subject = unit, Mann-Whitney, Cliff's delta / AUC with bootstrap CI, BH-FDR;
     split-half ICC; Spearman redundancy; leave-one-subject-out composite with in-fold selection.
4. **Results**
   - Table 2 + Figure 1 + Figure 2: which parameters differ, and how strongly.
   - Table 3 + Figure 4: which parameters are reliable.
   - Figure 3: which parameters carry the same information.
   - Figure 5: composite score.
   - Ablations: does the conclusion change?
5. **Discussion**: physiological meaning of the parameters that separate; agreement or disagreement
   with the literature; parameters that did NOT differ.
6. **Limitations**: n = 22; no per-patient clinical scores (Fugl-Meyer); healthy ages not reported;
   crosstalk (coherence); dynamic contractions (median frequency);
   movement detection flagged 5 of 189 files (S_12, S_13): 3 reaches split by a short dip, which may
   partly reflect real fragmentation rather than a detection error (see PROGRESS.md decisions log).
7. **Conclusion and next steps**: e.g. longitudinal data (PhysioMio) to test whether the parameters track recovery.

## Slides (about 10)
1. Title  2. Problem and earlier MVC finding  3. Dataset  4. The 10 parameters (Table 1, simplified)
5. Method in one diagram  6. Figure 1  7. Figure 2  8. Reliability + redundancy  9. Composite
10. Conclusions, limitations, next steps

## Verified references (add only after checking)
- Israely S, Leisman G, Carmeli E. EMG datasets from hand-reaching movements... Mendeley Data, 2019. DOI 10.17632/f4hh43nd78.2
- Israely S, Leisman G, et al. Muscle synergies control during hand-reaching tasks in multiple
  directions post-stroke. Front Comput Neurosci 2018;12:10. (Check the full author list.)
- Fang Y et al. Functional corticomuscular connection during reaching is weakened following stroke.
  Clin Neurophysiol 2009;120(5):994-1002. (EEG-EMG coherence, not intermuscular.)
- Hu X, Suresh AK, Rymer WZ, Suresh NL. Assessing altered motor unit recruitment patterns in paretic
  muscles of stroke survivors using surface EMG. J Neural Eng 2015;12(6):066001.
- Nazarpour K et al. A note on the probability distribution function of the surface electromyogram signal.
  Brain Res Bull 2013. (Check volume/pages before citing.)
