#!/usr/bin/env python3
"""
Generate Figure 1: 4-Layer Reliability-Oriented Framework Diagram

Creates a professional diagram showing:
  Layer 1: Open Foundation Model
  Layer 2: Domain Adaptation (PEFT/LoRA)
  Layer 3: Reliability Annotation Layer
  Layer 4: Benchmark-Driven Evaluation

Usage:
    python tools/generate_figure1.py --output paper/figures/framework.pdf
    python tools/generate_figure1.py --output paper/figures/framework.png --dpi 300
"""

import os
import argparse

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
except ImportError:
    print("matplotlib not installed. Install with: pip install matplotlib")
    print("Or generate the figure manually using the description below.")
    sys.exit(1)


def draw_framework(output_path: str, dpi: int = 300):
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Colors
    colors = {
        'layer1': '#4A90D9',  # Blue
        'layer2': '#7B68EE',  # Purple
        'layer3': '#E67E22',  # Orange
        'layer4': '#27AE60',  # Green
        'text': '#2C3E50',
        'light': '#ECF0F1',
    }

    # Layout
    layer_width = 8
    layer_height = 1.5
    gap = 0.3
    start_x = 1
    start_y = 8.5

    # Title
    ax.text(5, 9.5, 'Reliability-Oriented Framework for Vietnamese Legal LLM',
            fontsize=14, fontweight='bold', ha='center', va='center',
            color=colors['text'])

    # Layer 4 (top)
    y4 = start_y
    rect4 = FancyBboxPatch((start_x, y4), layer_width, layer_height,
                            boxstyle="round,pad=0.1", facecolor=colors['layer4'],
                            edgecolor='#1E8449', linewidth=2, alpha=0.9)
    ax.add_patch(rect4)
    ax.text(start_x + layer_width/2, y4 + layer_height/2 + 0.3,
            'Layer 4: Benchmark-Driven Evaluation',
            fontsize=12, fontweight='bold', ha='center', va='center', color='white')
    ax.text(start_x + layer_width/2, y4 + layer_height/2 - 0.2,
            'CitAcc | RAS | RAR | ESR | UCR | AbsAcc',
            fontsize=9, ha='center', va='center', color='white', style='italic')

    # Layer 3
    y3 = y4 - layer_height - gap
    rect3 = FancyBboxPatch((start_x, y3), layer_width, layer_height,
                            boxstyle="round,pad=0.1", facecolor=colors['layer3'],
                            edgecolor='#D35400', linewidth=2, alpha=0.9)
    ax.add_patch(rect3)
    ax.text(start_x + layer_width/2, y3 + layer_height/2 + 0.3,
            'Layer 3: Reliability Annotation Layer',
            fontsize=12, fontweight='bold', ha='center', va='center', color='white')
    ax.text(start_x + layer_width/2, y3 + layer_height/2 - 0.2,
            'Citation Grounding | Temporal Validity | Reliability Supervision',
            fontsize=9, ha='center', va='center', color='white', style='italic')

    # Layer 2
    y2 = y3 - layer_height - gap
    rect2 = FancyBboxPatch((start_x, y2), layer_width, layer_height,
                            boxstyle="round,pad=0.1", facecolor=colors['layer2'],
                            edgecolor='#5B4BA0', linewidth=2, alpha=0.9)
    ax.add_patch(rect2)
    ax.text(start_x + layer_width/2, y2 + layer_height/2 + 0.3,
            'Layer 2: Domain Adaptation',
            fontsize=12, fontweight='bold', ha='center', va='center', color='white')
    ax.text(start_x + layer_width/2, y2 + layer_height/2 - 0.2,
            'PEFT / LoRA Fine-tuning on Vietnamese Legal Corpus',
            fontsize=9, ha='center', va='center', color='white', style='italic')

    # Layer 1 (bottom)
    y1 = y2 - layer_height - gap
    rect1 = FancyBboxPatch((start_x, y1), layer_width, layer_height,
                            boxstyle="round,pad=0.1", facecolor=colors['layer1'],
                            edgecolor='#2E6DA4', linewidth=2, alpha=0.9)
    ax.add_patch(rect1)
    ax.text(start_x + layer_width/2, y1 + layer_height/2 + 0.3,
            'Layer 1: Open Foundation Model',
            fontsize=12, fontweight='bold', ha='center', va='center', color='white')
    ax.text(start_x + layer_width/2, y1 + layer_height/2 - 0.2,
            'Qwen2.5-7B | SeaLLMs-v3 | Multilingual LLM',
            fontsize=9, ha='center', va='center', color='white', style='italic')

    # Arrows between layers
    for y_top, y_bot in [(y4, y3), (y3, y2), (y2, y1)]:
        ax.annotate('', xy=(5, y_bot + layer_height + 0.05),
                    xytext=(5, y_top - 0.05),
                    arrowprops=dict(arrowstyle='->', color=colors['text'], lw=2))

    # Side labels
    # Left: Input
    ax.text(0.3, (y1 + y4 + layer_height) / 2, 'Input\nQuery',
            fontsize=10, ha='center', va='center', color=colors['text'],
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=colors['light'], edgecolor='gray'))

    # Right: Output
    ax.text(9.7, (y1 + y4 + layer_height) / 2, 'Output\nAnswer +\nReliability\nScore',
            fontsize=10, ha='center', va='center', color=colors['text'],
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=colors['light'], edgecolor='gray'))

    # Arrows from side labels
    ax.annotate('', xy=(start_x - 0.05, y1 + layer_height/2),
                xytext=(0.7, y1 + layer_height/2),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    ax.annotate('', xy=(9.3, y4 + layer_height/2),
                xytext=(start_x + layer_width + 0.05, y4 + layer_height/2),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    # VLegal-Bench label
    ax.text(5, y1 - 0.5, 'VLegal-Bench: 22 Tasks | 10,450 Samples | 5 Categories',
            fontsize=10, ha='center', va='center', color=colors['text'],
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F9E79F', edgecolor='#F39C12'))

    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Figure 1 saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate framework diagram")
    parser.add_argument("--output", type=str, default="paper/figures/framework.pdf",
                        help="Output file path (pdf, png, svg)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="Resolution for raster formats")
    args = parser.parse_args()

    draw_framework(args.output, args.dpi)

    # Also generate PNG for easy viewing
    if not args.output.endswith('.png'):
        png_path = args.output.rsplit('.', 1)[0] + '.png'
        draw_framework(png_path, 150)
        print(f"PNG preview saved to: {png_path}")


if __name__ == "__main__":
    main()
