# Annotation Protocol - Final Version for Paper

## Current draft in paper (paragraph 65):

> Annotation protocol. Annotation is performed by advanced law students (final-year undergraduate and postgraduate level) with demonstrated proficiency in Vietnamese civil, criminal, and administrative law, working under the direct supervision of licensed legal practitioners. All annotators complete a training phase covering the annotation schema, citation grounding conventions, temporal validity reasoning, and inter-annotator calibration exercises before working on production samples. The annotation process follows three stages: (i) independent annotation, in which each annotator labels the sample without consulting others; (ii) adjudication, in which a supervising legal practitioner resolves disagreements by reference to the authoritative statutory text and its official amendment history; and (iii) cross-validation, in which a random 10% of adjudicated samples are re-examined to verify consistency. Each sample is assigned to a team of three annotators. (draft)

---

## Proposed final version:

Annotation protocol. Annotation is performed by advanced law students (final-year undergraduate and postgraduate level) with demonstrated proficiency in Vietnamese civil, criminal, and administrative law, working under the direct supervision of licensed legal practitioners. All annotators complete a training phase covering the annotation schema, citation grounding conventions, temporal validity reasoning, and inter-annotator calibration exercises before working on production samples.

Each sample receives three annotation layers targeting distinct reliability dimensions:

**Citation grounding.** For each sample, annotators identify the authoritative source provisions supporting the correct answer. The annotation records the document name (full official title, e.g., "Bộ luật Dân sự 2015"), article number (e.g., "Điều 463"), clause number when applicable (e.g., "Khoản 1"), and an evidence passage containing the verbatim text from the statutory source. When multiple provisions are relevant, all are recorded. When the question does not explicitly cite a provision, annotators identify the most directly applicable article based on the legal substance of the question.

**Temporal validity.** For each cited provision, annotators record the promulgation date, effective date, expiration date (if applicable), and whether the provision has been superseded by a newer instrument. A binary validity label indicates whether the provision is in force at the query reference date specified in the sample (or at the current date if no reference date is given). This annotation layer is essential for evaluating whether models distinguish between current and historical legal provisions.

**Reliability supervision.** Beyond citation and temporal information, annotators assess the trustworthiness of each sample's expected answer. This includes: (i) evidence sufficiency—whether the information provided in the sample is sufficient to support a correct answer; (ii) unsupported claims—identification of any claims that cannot be grounded in the available evidence; (iii) hallucination type—classification of factual fabrication, citation hallucination (referencing non-existent provisions), or temporal confusion (citing superseded provisions); and (iv) should-abstain labeling—indicating whether a model should decline to answer due to insufficient evidence, ambiguous legal interpretation, or reliance on superseded law.

The annotation process follows three stages: (i) independent annotation, in which each annotator labels the sample without consulting others; (ii) adjudication, in which a supervising legal practitioner resolves disagreements by reference to the authoritative statutory text and its official amendment history; and (iii) cross-validation, in which a random 10% of adjudicated samples are re-examined by all annotators to verify consistency. Each sample is assigned to a team of two independent annotators, with a third annotator available for adjudication when disagreement exceeds threshold on any field.

Edge cases are handled according to documented rules: when a provision has been amended, annotators record both the original and amended versions; when a question references a specific date, temporal validity is assessed relative to that date; when a question is ambiguous or lacks sufficient context, the sample is labeled should-abstain with the specific reason documented.
