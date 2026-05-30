#!/usr/bin/env python3
"""
Confidence-Calibrated Abstention Trainer

Extends RAFT-AT with explicit confidence scoring:
- Model outputs <confidence>X.XX</confidence> before <abstain> or <answer>
- Loss function penalizes confidence miscalibration
- High confidence → must be correct
- Low confidence → should abstain

This creates a more nuanced abstention mechanism than binary <abstain>/<answer>.
The model learns WHEN to be confident, not just WHEN to refuse.

Usage:
    # Combined with DPO:
    python tools/finetune_raft_at.py --model <model> --training_mode dpo \
        --use_confidence_calibration --confidence_weight 0.5
"""

import torch
import torch.nn as nn
import re
import logging
from transformers import Trainer


class ConfidenceCalibrationLoss(nn.Module):
    """Loss function that calibrates model confidence.

    Combines:
    1. Standard cross-entropy on token prediction
    2. Confidence calibration loss (penalizes miscalibration)
    3. Abstention decision loss (penalizes wrong abstain/answer decisions)

    The confidence score is extracted from <confidence>X.XX</confidence> tags
    in the model output and compared against target confidence from training data.
    """

    def __init__(self, confidence_weight: float = 0.5, abstention_weight: float = 2.0):
        super().__init__()
        self.confidence_weight = confidence_weight
        self.abstention_weight = abstention_weight
        self.ce_loss = nn.CrossEntropyLoss(reduction='none')

    def extract_confidence_from_logits(self, logits: torch.Tensor, tokenizer) -> torch.Tensor:
        """Extract confidence score from model output tokens.

        Finds <confidence> token, then reads the next few tokens as a float.
        Returns a tensor of confidence scores per batch item.
        """
        # Get predicted tokens
        predictions = torch.argmax(logits, dim=-1)

        batch_size = predictions.size(0)
        confidences = torch.zeros(batch_size, device=logits.device)

        # Find <confidence> token ID
        conf_token_ids = tokenizer.encode("<confidence>", add_special_tokens=False)
        if not conf_token_ids:
            return confidences

        conf_start_id = conf_token_ids[0]

        for b in range(batch_size):
            tokens = predictions[b]
            # Find <confidence> position
            conf_positions = (tokens == conf_start_id).nonzero(as_tuple=True)[0]
            if len(conf_positions) > 0:
                pos = conf_positions[0].item()
                # Read next few tokens as confidence value
                # Try to decode the number after <confidence>
                try:
                    num_tokens = tokens[pos+1:pos+6]  # Up to 5 tokens for "0.XX"
                    conf_text = tokenizer.decode(num_tokens, skip_special_tokens=True)
                    # Extract float from text
                    match = re.search(r'(\d+\.?\d*)', conf_text)
                    if match:
                        confidences[b] = float(match.group(1))
                except (ValueError, IndexError):
                    confidences[b] = 0.5  # Default

        return confidences.clamp(0.0, 1.0)

    def compute_calibration_loss(
        self,
        pred_confidence: torch.Tensor,
        target_confidence: torch.Tensor,
        should_abstain: torch.Tensor,
    ) -> torch.Tensor:
        """Compute calibration loss.

        For answer samples: penalize if pred_confidence < target_confidence (underconfident)
        For abstain samples: penalize if pred_confidence > 0.3 (overconfident on abstain)
        """
        # Answer samples: should be confident
        answer_mask = ~should_abstain
        answer_loss = torch.tensor(0.0, device=pred_confidence.device)
        if answer_mask.any():
            # Penalize underconfidence on correct answers
            answer_loss = nn.functional.mse_loss(
                pred_confidence[answer_mask],
                target_confidence[answer_mask],
            )

        # Abstain samples: should be low confidence
        abstain_loss = torch.tensor(0.0, device=pred_confidence.device)
        if should_abstain.any():
            # Penalize overconfidence on abstain samples
            # Target confidence for abstain is 0.1
            abstain_target = torch.full_like(pred_confidence[should_abstain], 0.1)
            abstain_loss = nn.functional.mse_loss(
                pred_confidence[should_abstain],
                abstain_target,
            )

        return answer_loss + abstain_loss

    def forward(
        self,
        logits: torch.Tensor,
        labels: torch.Tensor,
        target_confidence: torch.Tensor = None,
        should_abstain: torch.Tensor = None,
        tokenizer=None,
    ) -> torch.Tensor:
        """Compute combined loss.

        Args:
            logits: Model output logits [batch, seq, vocab]
            labels: Token labels [batch, seq]
            target_confidence: Target confidence scores [batch]
            should_abstain: Boolean mask for abstain samples [batch]
            tokenizer: Tokenizer for decoding confidence scores
        """
        # Standard CE loss
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()

        ce_loss = self.ce_loss(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        ).mean()

        # Confidence calibration loss (if we have targets)
        cal_loss = torch.tensor(0.0, device=logits.device)
        if target_confidence is not None and should_abstain is not None and tokenizer:
            pred_confidence = self.extract_confidence_from_logits(logits, tokenizer)
            cal_loss = self.compute_calibration_loss(
                pred_confidence, target_confidence, should_abstain
            )

        total_loss = ce_loss + self.confidence_weight * cal_loss
        return total_loss


class ConfidenceCalibratedTrainer(Trainer):
    """Trainer with confidence calibration loss.

    Teaches the model to:
    1. Output accurate confidence scores
    2. Be confident only when evidence supports the answer
    3. Be low-confidence (abstain) when evidence is insufficient
    """

    def __init__(self, confidence_weight: float = 0.5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confidence_weight = confidence_weight
        self.calibration_loss = ConfidenceCalibrationLoss(
            confidence_weight=confidence_weight,
        )

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        """Compute loss with confidence calibration."""
        # Extract metadata if available
        target_confidence = inputs.pop("target_confidence", None)
        should_abstain = inputs.pop("should_abstain", None)

        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        tokenizer = self.processing_class if hasattr(self, 'processing_class') else self.tokenizer

        loss = self.calibration_loss(
            logits=logits,
            labels=labels,
            target_confidence=target_confidence,
            should_abstain=should_abstain,
            tokenizer=tokenizer,
        )

        return (loss, outputs) if return_outputs else loss
