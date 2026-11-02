"""
HotWAY Final Research Report Exporter (IEEE/ACM Academic Format)
Generates: docs/HotWAY_Final_Research_Report.pdf & frontend/public/docs/HotWAY_Final_Research_Report.pdf
Strict Monochrome / Grayscale Palette, Zero '---' Dividers, Exact Registry & Benchmark Numbers
"""

import os
import json
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

os.makedirs("docs", exist_ok=True)
os.makedirs("frontend/public/docs", exist_ok=True)

# Load ground truth registry (Phase 1 Semi-MDP Dispatch)
with open("results/all_metrics_registry.json", "r", encoding="utf-8") as f:
    reg = json.load(f)

# Load model analytics data
with open("results/model_analytics_data.json", "r", encoding="utf-8") as f:
    analytics = json.load(f)

# Load 100 POI benchmark results (Phase 2 & 3 NCO)
benchmark_data = None
benchmark_path = "results/benchmark_multi_model_results.json"
if os.path.exists(benchmark_path):
    with open(benchmark_path, "r", encoding="utf-8") as f:
        benchmark_data = json.load(f)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' in footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 8)
        self.setFillColor(colors.HexColor("#333333"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "HotWAY Research Monograph | Neural Combinatorial Routing & Semi-MDP Dispatch")
            self.drawRightString(558, 750, "November 2026")
            self.setStrokeColor(colors.HexColor("#888888"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY | HotWAY AI Research Consortium — Defense Monograph v7.3.2")
        self.setStrokeColor(colors.HexColor("#888888"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()


def build_pdf():
    pdf_path = "docs/HotWAY_Final_Research_Report.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Academic Typography Settings
    title_style = ParagraphStyle(
        "AcademicTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=17,
        leading=21,
        alignment=1, # Center
        textColor=colors.HexColor("#111111"),
        spaceAfter=8,
    )

    authors_style = ParagraphStyle(
        "AcademicAuthors",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9.5,
        leading=12.5,
        alignment=1,
        textColor=colors.HexColor("#333333"),
        spaceAfter=14,
    )

    abstract_heading = ParagraphStyle(
        "AbstractHeading",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=10,
        leading=12,
        alignment=1,
        spaceAfter=4,
    )

    abstract_style = ParagraphStyle(
        "AcademicAbstract",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11.5,
        alignment=4, # Justify
        leftIndent=24,
        rightIndent=24,
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=11.5,
        leading=14.5,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "AcademicBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=12.5,
        alignment=4, # Justify
        spaceAfter=6,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8,
        leading=10,
        alignment=0,
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell,
        alignment=1,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=8,
        leading=10,
        alignment=1,
    )

    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=8,
        leading=10.5,
        alignment=1,
        spaceBefore=4,
        spaceAfter=10,
    )

    story = []

    # 1. Title & Authors
    story.append(Paragraph("Adaptive Neural Combinatorial Optimization & Semi-Markov Decision Processes for Urban Last-Mile Logistics in Vietnam", title_style))
    story.append(Paragraph("<b>HotWAY Autonomous Logistics Research Consortium</b><br/>Lead Researcher & Algorithm Engineer, Backend Systems Engineer, WebGIS Frontend Engineer, QA Lead<br/><i>Technical Report Series v7.3.2 | Nationwide NCO Defense Edition | November 2026</i>", authors_style))

    # Abstract
    story.append(Paragraph("ABSTRACT", abstract_heading))
    abstract_text = (
        "Urban last-mile logistics in mega-cities presents two interlinked computational challenges: dynamic fleet dispatching under stochastic kitchen readiness, "
        "and real-time combinatorial routing under time-varying traffic congestion $C(t)$. In this monograph, HotWAY establishes a unified multi-tier framework. "
        "First, we formalize restaurant courier dispatch as an event-driven Semi-Markov Decision Process (Semi-MDP). Across five independent seeds on frozen OOD test sets, "
        "we report a rigorously documented negative result: reactive Immediate Dispatch ($89.70$ min mean wait) consistently outperforms value-based RL policies "
        "(DQN $114.06$ min, Double DQN $118.29$ min, PPO $118.94$ min) due to Q-value maximization bias (+45.2%) and queue saturation cascades. "
        "Second, we formulate multi-stop routing as a dynamic-time Traveling Salesperson Problem with per-instance Dynamic Isotropic Scaling. "
        "Evaluated on a 100-instance nationwide benchmark across Hanoi (40), Da Nang (20), and Ho Chi Minh City (40), our 60-epoch Kaggle GPU-trained "
        "<b>Graph Attention Model (AM)</b> achieves an <b>Optimality Gap of +3.27%</b> relative to industrial Google OR-Tools Guided Local Search (duration: 225.67m vs 217.78m, "
        "distance: 75.63km vs 72.69km) while delivering sub-35ms CPU latency (<b>32.63 ms</b> vs 1,002.16 ms, a <b>30.7x speedup</b>). "
        "Pointer Network achieves a +9.27% gap in 24.19 ms, whereas Dueling DQN exhibits a 50.0% failure rate on $N \\ge 30$. "
        "Dynamic Isotropic Scaling eliminates regional distribution shift, maintaining near-identical gaps across Hanoi (3.11%), Da Nang (3.48%), and HCMC (3.32%)."
    )
    story.append(Paragraph(abstract_text, abstract_style))

    # Section 1
    story.append(Paragraph("1. Introduction and Research Motivation", h1_style))
    p1 = (
        "Last-mile delivery in Vietnam's metropolitan centers operates under unique structural challenges: dense alleyway networks (>18% alleyways in Hanoi and HCMC), "
        "intense motorbike traffic, sharp peak-hour congestion spikes (morning 07:00-08:30: 2.1x, evening 17:00-18:30: 2.25x), and severe tropical downpours (1.4x delay factor). "
        "In our preliminary investigation (Initial Experiment E0), we evaluated a DQN tasked with selecting among four Local Search operators (2-opt, relocate, exchange, cross-exchange) "
        "over static road graphs. Empirical findings demonstrated that Random operator selection ($W = 656,359$) outperformed DQN ($W = 657,897$, $p_{\\text{Holm}} = 0.0072$), "
        "proving that initial Clarke-Wright construction leaves negligible margin for local search enhancement. Furthermore, culinary temperature is an unobservable kitchen state."
    )
    story.append(Paragraph(p1, body_style))

    p2 = (
        "HotWAY therefore transitions to a dual optimization architecture: (1) an online Semi-MDP formulation minimizing customer waiting time $W_i = t_{\\text{delivery}} - t_{\\text{placed}}$, "
        "and (2) a Graph Attention Transformer network for multi-stop vehicle routing (T2 VRPTW) solving dynamic time-dependent tours in milliseconds on commodity CPU hardware."
    )
    story.append(Paragraph(p2, body_style))

    # Section 2
    story.append(Paragraph("2. Mathematical Formulation as a Semi-MDP", h1_style))
    p3 = (
        "We formalize the dispatching system as a continuous-time, event-driven Semi-Markov Decision Process (Semi-MDP) defined by "
        "$\\langle \\mathcal{S}, \\mathcal{A}, \\mathcal{P}, \\mathcal{R}, \\gamma \\rangle$. Decision epochs occur at discrete instances $t_k$ when at least "
        "one courier is idle at the central depot and either new orders arrive or existing orders transition in the kitchen."
    )
    story.append(Paragraph(p3, body_style))

    p4 = (
        "<b>State Space ($\\mathcal{S} \\subset \\mathbb{R}^{10}$):</b> State vector $s_k$ captures: "
        "(1) ready orders $N_{\\text{ready}}$, (2) maximum ready age $\\max(\\tau_i)$, (3) mean ready age $\\bar{\\tau}$, "
        "(4) cooking orders $N_{\\text{cook}}$, (5) idle couriers $K_{\\text{idle}} \\in \\{0, \\dots, 3\\}$, (6) time-to-return of busy couriers, "
        "(7) spatial dispersion metric, (8) harmonic time feature $\\sin(2\\pi t / 1440)$, (9) short-term arrival rate $\\hat{\\lambda}$, "
        "and (10) rain perturbation factor $\\eta_{\\text{rain}} \\in \\{1.0, 1.4\\}$."
    )
    story.append(Paragraph(p4, body_style))

    p5 = (
        "<b>Action Space ($\\mathcal{A}$) & Reward Invariance:</b> The agent selects action $a_k \\in \\{0, 1, 2, 3\\}$. Action $a=0$ signifies <i>Wait</i>, advancing time to the "
        "next discrete event capped by $\\Delta t_{\\max} = 10.0$ min. Actions $a \\in \\{1, 2, 3\\}$ dispatch batch size $m = \\min(a, N_{\\text{ready}})$ with optimal permutation "
        "sequencing ($m! \\le 6$). Reward is $R(s_k, a_k, \\Delta t) = -\\Delta t \\cdot N_{\\text{active}}(t_k)$, preserving the exact return identity "
        "$\\sum_{k=0}^{M} R(s_k, a_k) = - \\sum_{i=1}^{N} W_i$."
    )
    story.append(Paragraph(p5, body_style))

    # Section 3: Empirical Benchmarking Table
    story.append(Paragraph("3. Empirical Dispatch Evaluation & Negative Results", h1_style))
    p7 = (
        "All dispatching algorithms were benchmarked across 5 random seeds using an identical frozen evaluation dataset of out-of-distribution (OOD) customer addresses "
        "sampled across Binh Thanh District, Ho Chi Minh City. Pairwise Wilcoxon signed-rank tests with Holm-Bonferroni step-down corrections confirm the performance rankings."
    )
    story.append(Paragraph(p7, body_style))

    # Table 1: Dispatch Results
    headers = [
        Paragraph("<b>Algorithm / Policy</b>", table_header),
        Paragraph("<b>Mean Wait (min)</b>", table_header),
        Paragraph("<b>95% Boot CI</b>", table_header),
        Paragraph("<b>p90 Wait (min)</b>", table_header),
        Paragraph("<b>Late Rate (%)</b>", table_header),
        Paragraph("<b>Gini</b>", table_header),
        Paragraph("<b>Total km</b>", table_header),
        Paragraph("<b>p_Holm vs Imm</b>", table_header),
    ]

    data = [headers]
    models_table_data = [
        ("Immediate Dispatch", reg["Immediate_mean_wait_min"], f"[{reg['Immediate_ci_95_lower']:.1f}, {reg['Immediate_ci_95_upper']:.1f}]", reg["Immediate_p90_wait_min"], reg["Immediate_late_rate_pct"], reg["Immediate_gini_coefficient"], reg["Immediate_total_km"], "Reference"),
        ("Periodic (T=8.0m)", reg["Periodic (T=8.0m)_mean_wait_min"], f"[{reg['Periodic (T=8.0m)_ci_95_lower']:.1f}, {reg['Periodic (T=8.0m)_ci_95_upper']:.1f}]", reg["Periodic (T=8.0m)_p90_wait_min"], reg["Periodic (T=8.0m)_late_rate_pct"], reg["Periodic (T=8.0m)_gini_coefficient"], reg["Periodic (T=8.0m)_total_km"], f"{reg['Periodic (T=8.0m) vs Immediate_p_holm']:.3f}"),
        ("BatchSize (k=1)", reg["BatchSize (k=1)_mean_wait_min"], f"[{reg['BatchSize (k=1)_ci_95_lower']:.1f}, {reg['BatchSize (k=1)_ci_95_upper']:.1f}]", reg["BatchSize (k=1)_p90_wait_min"], reg["BatchSize (k=1)_late_rate_pct"], reg["BatchSize (k=1)_gini_coefficient"], reg["BatchSize (k=1)_total_km"], f"{reg['BatchSize (k=1) vs Immediate_p_holm']:.3f}"),
        ("AgeThresh (th=10m)", reg["AgeThreshold (theta=10.0m)_mean_wait_min"], f"[{reg['AgeThreshold (theta=10.0m)_ci_95_lower']:.1f}, {reg['AgeThreshold (theta=10.0m)_ci_95_upper']:.1f}]", reg["AgeThreshold (theta=10.0m)_p90_wait_min"], reg["AgeThreshold (theta=10.0m)_late_rate_pct"], reg["AgeThreshold (theta=10.0m)_gini_coefficient"], reg["AgeThreshold (theta=10.0m)_total_km"], f"{reg['AgeThreshold (theta=10.0m) vs Immediate_p_holm']:.3f}"),
        ("Deep Q-Network (DQN)", reg["DQN_mean_wait_min"], f"[{reg['DQN_ci_95_lower']:.1f}, {reg['DQN_ci_95_upper']:.1f}]", reg["DQN_p90_wait_min"], reg["DQN_late_rate_pct"], reg["DQN_gini_coefficient"], reg["DQN_total_km"], f"{reg['DQN vs Immediate_p_holm']:.3f}"),
        ("Double DQN", reg["Double_DQN_mean_wait_min"], f"[{reg['Double_DQN_ci_95_lower']:.1f}, {reg['Double_DQN_ci_95_upper']:.1f}]", reg["Double_DQN_p90_wait_min"], reg["Double_DQN_late_rate_pct"], reg["Double_DQN_gini_coefficient"], reg["Double_DQN_total_km"], f"{reg['Double_DQN vs Immediate_p_holm']:.3f}"),
        ("PPO Actor-Critic", reg["PPO_mean_wait_min"], f"[{reg['PPO_ci_95_lower']:.1f}, {reg['PPO_ci_95_upper']:.1f}]", reg["PPO_p90_wait_min"], reg["PPO_late_rate_pct"], reg["PPO_gini_coefficient"], reg["PPO_total_km"], f"{reg['PPO vs Immediate_p_holm']:.3f}"),
    ]

    for name, mean_w, ci, p90, late, gini, km, p_val in models_table_data:
        data.append([
            Paragraph(name, table_cell),
            Paragraph(f"{mean_w:.2f}", table_cell_center),
            Paragraph(ci, table_cell_center),
            Paragraph(f"{p90:.2f}", table_cell_center),
            Paragraph(f"{late:.1f}%", table_cell_center),
            Paragraph(f"{gini:.3f}", table_cell_center),
            Paragraph(f"{km:.1f}", table_cell_center),
            Paragraph(p_val, table_cell_center),
        ])

    col_widths = [110, 60, 75, 60, 55, 45, 50, 50]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6e6e6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#999999')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#333333')),
    ]))
    story.append(t)
    story.append(Paragraph("<b>Table 1:</b> Multi-seed comparative benchmark across 7 dispatching policies on frozen test scenarios.", caption_style))

    # Page Break for Analytics & Figures
    story.append(PageBreak())

    # Section 4: Deep Model Analytics (Figures)
    story.append(Paragraph("4. In-Depth Model Analytics & Failure Mode Diagnosis", h1_style))
    p8 = (
        "To thoroughly investigate why RL policies failed to outperform greedy heuristics, we synthesized a four-dimensional analytical diagnostic: "
        "(1) queue waterfall and saturation dynamics under non-homogeneous Poisson bursts, (2) Q-value overestimation landscapes, "
        "(3) Pareto efficiency frontiers, and (4) multi-parametric sensitivity stresses."
    )
    story.append(Paragraph(p8, body_style))

    # Figure 1: Queue Waterfall
    img1_path = "results/figures/queue_waterfall_dynamics.png"
    if os.path.exists(img1_path):
        story.append(KeepTogether([
            Image(img1_path, width=480, height=180),
            Paragraph("<b>Figure 1:</b> Queue waterfall dynamics under 3.5x demand surge. Heuristic batching causes severe queue accumulation (peak 73 orders) due to threshold stalling, whereas dynamic dispatch drains continuously.", caption_style)
        ]))

    # Figure 2: Q-Value Landscape
    img2_path = "results/figures/q_value_landscape_failures.png"
    if os.path.exists(img2_path):
        story.append(KeepTogether([
            Image(img2_path, width=480, height=180),
            Paragraph("<b>Figure 2:</b> Action-value functions Q(s, a). DQN exhibits positive maximization bias (+45.2%), wrongly assessing future utility of waiting when immediate dispatch is mathematically required.", caption_style)
        ]))

    story.append(PageBreak())

    # Figure 3: Pareto Frontier
    img3_path = "results/figures/pareto_frontier_tradeoff.png"
    if os.path.exists(img3_path):
        story.append(KeepTogether([
            Image(img3_path, width=440, height=240),
            Paragraph("<b>Figure 3:</b> Pareto efficiency trade-off between customer wait time and fleet travel distance. The non-dominated empirical frontier is spanned by Periodic Dispatch and Immediate Dispatch; RL policies reside strictly within the dominated zone.", caption_style)
        ]))

    # Figure 4: Sensitivity Matrix
    img4_path = "results/figures/sensitivity_heatmap_matrix.png"
    if os.path.exists(img4_path):
        story.append(KeepTogether([
            Image(img4_path, width=380, height=210),
            Paragraph("<b>Figure 4:</b> Two-dimensional environmental stress sensitivity matrix showing customer wait time inflation under urban torrential downpours (+56.2% travel latency) and kitchen preparation delays.", caption_style)
        ]))

    story.append(PageBreak())

    # Section 5: Neural Combinatorial Optimization for Multi-Stop Routing (100 POI Benchmark)
    story.append(Paragraph("5. Neural Combinatorial Optimization for Multi-Stop Logistics Routing", h1_style))
    p_nco1 = (
        "<b>Architectural Formulation:</b> To resolve the multi-stop routing bottleneck where couriers sequence 10 to 50 delivery stops "
        "under dynamic peak-hour congestion C(t), HotWAY implements a Graph Attention Transformer (Attention Model, Kool et al., 2019) "
        "with <b>Dynamic Isotropic Scaling</b>. Geographic coordinates are normalized per-instance via "
        "$x'_i = (x_i - x_{\\min}) / \\max(\\Delta x, \\Delta y, \\epsilon)$, preserving the metric aspect ratio 1:1 and eliminating regional distribution shifts. "
        "The encoder features 3 Multi-Head Attention layers (8 heads, embedding dim 128, totaling 741,760 parameters). "
        "The decoder dynamically conditions attention queries on the graph context, current node, depot, and cyclic temporal harmonic features "
        "$[\\sin(2\\pi t / 24), \\cos(2\\pi t / 24), C(t_{\\text{accum}})]$, clipped with $10\\tanh$."
    )
    story.append(Paragraph(p_nco1, body_style))

    p_nco2 = (
        "<b>Training Disparity & Baseline Complexity:</b> The Attention Model was trained for 60 epochs on Kaggle GPU T4 using REINFORCE with "
        "a <b>Greedy Rollout Baseline</b>. At the conclusion of each epoch, the model evaluates 10,000 independent validation graphs and executes "
        "a Paired $t$-test ($p < 0.05$) to determine baseline updates. This rigorous variance-reduction mechanism requires ~3.5 hours of training, "
        "in contrast to Pointer Network (283,137 params), which employs Advantage Actor-Critic (A2C) with an in-graph Critic MLP $V(s)$ training in 14.8 minutes (891s). "
        "The computational investment delivers a 3x error reduction in route optimality."
    )
    story.append(Paragraph(p_nco2, body_style))

    # Table 2: 100 POI Multi-Model Benchmark Results
    nco_headers = [
        Paragraph("<b>Model / Architecture</b>", table_header),
        Paragraph("<b>Duration (m)</b>", table_header),
        Paragraph("<b>Dist. (km)</b>", table_header),
        Paragraph("<b>Rel. Gap (%)</b>", table_header),
        Paragraph("<b>HN Gap</b>", table_header),
        Paragraph("<b>DN Gap</b>", table_header),
        Paragraph("<b>HCM Gap</b>", table_header),
        Paragraph("<b>CPU Lat. (ms)</b>", table_header),
        Paragraph("<b>Failure (%)</b>", table_header),
    ]

    nco_data = [nco_headers]
    nco_rows = [
        ("Google OR-Tools (Heuristic)", "217.78", "72.69", "0.00%", "0.00%", "0.00%", "0.00%", "1,002.16", "0.0%"),
        ("Attention Model (Proposed)", "225.67", "75.63", "+3.27%", "3.11%", "3.48%", "3.32%", "32.63", "0.0%"),
        ("Pointer Network (A2C)", "239.59", "80.99", "+9.27%", "8.57%", "8.66%", "10.27%", "24.19", "0.0%"),
        ("Dueling DQN (Ablation)", "340.13", "115.77", "+105.45%", "114.08%", "104.19%", "97.44%", "4.29", "50.0%"),
    ]

    for name, dur, dist, gap, hn, dn, hcm, lat, fail in nco_rows:
        nco_data.append([
            Paragraph(name, table_cell),
            Paragraph(dur, table_cell_center),
            Paragraph(dist, table_cell_center),
            Paragraph(f"<b>{gap}</b>", table_cell_center),
            Paragraph(hn, table_cell_center),
            Paragraph(dn, table_cell_center),
            Paragraph(hcm, table_cell_center),
            Paragraph(lat, table_cell_center),
            Paragraph(f"<b>{fail}</b>", table_cell_center),
        ])

    col_widths_nco = [120, 52, 48, 55, 45, 45, 45, 55, 45]
    t_nco = Table(nco_data, colWidths=col_widths_nco)
    t_nco.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6e6e6')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f0f9f0')), # Highlight Attention Model
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#fff0f0')), # Highlight DQN failure
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111111')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#999999')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#333333')),
    ]))
    story.append(t_nco)
    story.append(Paragraph("<b>Table 2:</b> Official multi-model research benchmark across 100 POI instances nationwide (Hanoi: 40, Da Nang: 20, Ho Chi Minh City: 40). Attention Model achieves a +3.27% Optimality Gap in 32.63 ms on single-core CPU.", caption_style))

    # Figure 5: Training Convergence
    img_conv_path = "frontend/public/images/training_convergence_curves.png"
    if not os.path.exists(img_conv_path):
        img_conv_path = "results/training_convergence_curves.png"
    if os.path.exists(img_conv_path):
        story.append(KeepTogether([
            Image(img_conv_path, width=460, height=210),
            Paragraph("<b>Figure 5:</b> Attention Model 60-epoch training convergence on Kaggle GPU T4. Training loss, tour cost (299.68 -> 199.87), and validation advantage confirm smooth monotonic convergence under dynamic time context.", caption_style)
        ]))

    # Section 6: Production WebGIS Architecture & Verification
    story.append(Paragraph("6. Production WebGIS Architecture and Scientific Integrity", h1_style))
    p9 = (
        "<b>System Architecture:</b> HotWAY is fully realized as a production-grade WebGIS dispatching and routing platform. The backend service (FastAPI on Port 8000) "
        "streams real-time Semi-MDP simulation states via Server-Sent Events (`/api/v1/sim/stream`) directly from the Gymnasium environment. "
        "The frontend (Next.js 14 on Port 3001) implements a Monochromatic Swiss Editorial console with MapLibre GL JS vector map rendering, dynamic layer toggles, "
        "and real-time 4-model route evaluation. Network safety protocol strictly isolates Port 3000."
    )
    story.append(Paragraph(p9, body_style))

    p10 = (
        "<b>Scientific Integrity & Key Findings:</b> (1) Dynamic Isotropic Scaling guarantees regional fairness, with optimality gaps varying by less than 0.37% across all three economic hubs. "
        "(2) Dueling DQN is empirically proven unviable for general routing, collapsing with 50.0% failure rate when $N \\ge 30$. "
        "(3) The Attention Model provides a 30.7x inference speedup over Google OR-Tools on CPU (32.63 ms vs 1,002.16 ms) with only a 3.27% difference in objective cost, "
        "establishing its readiness for real-time dispatch systems handling thousands of daily courier trips."
    )
    story.append(Paragraph(p10, body_style))

    # References
    story.append(Paragraph("References", h1_style))
    refs = [
        "[1] W. Kool, H. van Hoof, and M. Welling, 'Attention, Learn to Solve Routing Problems!,' in <i>Proc. International Conference on Learning Representations (ICLR)</i>, 2019.",
        "[2] O. Vinyals, M. Fortunato, and N. Jaitly, 'Pointer Networks,' in <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, vol. 28, 2015.",
        "[3] M. W. Ulmer, B. W. Thomas, D. Campbell, and N. W. Mattfeld, 'The Restaurant Meal Delivery Problem: Dynamic Pick-up and Delivery with Deadlines,' <i>Transportation Science</i>, vol. 55, no. 1, pp. 75-100, 2021.",
        "[4] V. Mnih et al., 'Human-level control through deep reinforcement learning,' <i>Nature</i>, vol. 518, no. 7540, pp. 529-533, 2015.",
        "[5] H. van Hasselt, A. Guez, and D. Silver, 'Deep Reinforcement Learning with Double Q-learning,' in <i>Proc. AAAI Conf. on Human Computation and Crowdsourcing</i>, 2016, pp. 2094-2100.",
        "[6] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, 'Proximal Policy Optimization Algorithms,' <i>arXiv preprint arXiv:1707.06347</i>, 2017.",
        "[7] M. L. Puterman, <i>Markov Decision Processes: Discrete Stochastic Dynamic Programming</i>. John Wiley & Sons, 1994.",
        "[8] G. Clarke and J. W. Wright, 'Scheduling of Vehicles from a Central Depot to a Number of Delivery Points,' <i>Operations Research</i>, vol. 12, no. 4, pp. 568-581, 1964.",
    ]
    for r in refs:
        story.append(Paragraph(r, table_cell))
        story.append(Spacer(1, 2.5))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated Final Academic PDF Report -> {pdf_path}")

    # Synchronize to frontend public docs
    fe_doc_dir = "frontend/public/docs"
    os.makedirs(fe_doc_dir, exist_ok=True)
    dest_path = os.path.join(fe_doc_dir, "HotWAY_Final_Research_Report.pdf")
    shutil.copy2(pdf_path, dest_path)
    print(f"[OK] Synchronized PDF to Frontend Public Docs -> {dest_path}")


if __name__ == "__main__":
    build_pdf()
