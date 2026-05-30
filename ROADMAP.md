# Roadmap

**Last updated**: 2026-05-26

## Immediate (This Week)

### 1. Start RAFT-AT Training
**Status**: Blocked (workstation offline)
**Priority**: HIGH — this is the key novelty contribution

- [ ] Wake up workstation (100.72.47.109)
- [ ] Run RAFT-AT training command (see PROJECT_STATUS.md)
- [ ] Monitor training (expected: 2-4 hours on RTX 3090 Ti)
- [ ] Merge LoRA adapter after training
- [ ] Run inference on all 5 tasks
- [ ] Calculate reliability metrics

**Expected outcome**: Non-zero AbsAcc on multiple tasks (currently 0.060 aggregate, 0.261 on task 4.2)

### 2. Update Paper with RAFT-AT Results
**Status**: Waiting on #1
**Priority**: HIGH

- [ ] Update Table 4 (aggregate reliability) with RAFT-AT row
- [ ] Update Table 5 (per-task breakdown)
- [ ] Update radar chart with RAFT-AT coordinates
- [ ] Add RAFT-AT analysis paragraph to Section 4
- [ ] Update conclusion with RAFT-AT findings

## Short-Term (Next 2 Weeks)

### 3. Strengthen Paper Novelty
**Status**: Needs discussion
**Priority**: HIGH — reviewer concern

Current weakness: paper is primarily an empirical study. Dataset is inherited, metrics are adaptations. RAFT-AT would be the clear method contribution.

Options to strengthen:
- Formalize the reliability metric definitions with theoretical grounding
- Add ablation study (which metrics matter most?)
- Compare with other reliability frameworks (e.g., calibration methods)
- Add error analysis section

### 4. Additional Experiments
**Status**: Not started
**Priority**: MEDIUM

- [ ] Ablation: remove each metric one at a time
- [ ] Cross-model evaluation (test on Qwen, LLaMA)
- [ ] Per-category analysis (which task categories benefit most?)
- [ ] Statistical significance tests

### 5. Paper Polish
**Status**: Draft complete, needs review
**Priority**: MEDIUM

- [ ] Proofread all sections
- [ ] Check LaTeX formatting
- [ ] Verify all citations
- [ ] Add acknowledgments
- [ ] Final figure quality check

## Long-Term (After Submission)

### 6. Reproducibility Package
- [ ] Clean up scripts for public release
- [ ] Write detailed setup instructions
- [ ] Create example notebooks
- [ ] Package annotations for distribution

### 7. Extended Evaluation
- [ ] More tasks (if VLegal-Bench expands)
- [ ] More models (GPT-4, Claude, Gemini)
- [ ] Human evaluation study
- [ ] Cross-lingual comparison

## Blockers

| Blocker | Impact | Mitigation |
|---------|--------|------------|
| Workstation offline | Cannot train RAFT-AT | Wake up machine |
| Paper novelty weak | Reviewer rejection risk | RAFT-AT + ablation study |
| AbsAcc low | Reliability claim weak | RAFT-AT training (expected fix) |

## Dependencies

```
RAFT-AT Training → Paper Update → Submission
       ↓
  Novelty Analysis → Additional Experiments → Paper Polish
```
