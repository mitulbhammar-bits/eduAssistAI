"""Generate a short evidence-grounded report after a run, or a labeled draft now."""
import re
from pathlib import Path
from xml.sax.saxutils import escape
from .config import ROOT


def report_sections(rows=None, summaries=None, metadata=None):
    measured = bool(rows and summaries and metadata)
    if measured:
        by_version = {s['prompt_version']: s for s in summaries}
        version = metadata['production_candidate']
        selected = by_version[version or 'v3']
        v1 = [r for r in rows if r['prompt_version'] == 'v1' and r['response_status'] == 'success']
        slow = max(v1, key=lambda r: r['latency_seconds']) if v1 else None
        latency_text = (f"The slowest basic-prompt request was {slow['question_id']} at "
            f"{slow['latency_seconds']:.3f} seconds, producing {slow['output_tokens']} output tokens. "
            if slow else 'No basic-prompt request completed successfully. ')
        latency_text += ('Longer generation, initial model preparation, CPU scheduling and request overhead '
            'are plausible explanations, but a single trial cannot establish causation. The latency summary '
            'reports mean, median, minimum, maximum and sample standard deviation for each prompt. '
            'Successful calls determine latency and token averages; failed attempts remain visible and '
            'count against JSON validity and promotion eligibility.')
        pricing = metadata['effective_pricing']
        if pricing['input_rate'] is not None:
            cost_text = (f"The effective input and output rates were USD {pricing['input_rate']:.6f} and "
                f"USD {pricing['output_rate']:.6f} per million tokens. The {selected['prompt_version']} "
                f"mean estimated cost was USD {selected['avg_cost_per_request']:.8f}; 10,000 similar "
                f"requests project to USD {selected['projected_monthly_cost_usd']:.4f}. ")
        else:
            cost_text = 'No usable token counts were returned, so no numerical cost estimate is justified. '
        host = metadata['settings']['hosting']
        cost_text += ('These are hypothetical hosting estimates, not invoices or advertised token tariffs. '
            f"The reference is {host['reference_instance']} at USD {host['usd_per_hour']}/hour, "
            f"checked on {host['pricing_date']}. "
            'Local throughput is not a cloud benchmark; idle capacity, startup time, minimum billing and '
            'electricity are excluded. Shorter answers and a smaller suitable model can reduce generation cost.')
        comparison = '; '.join(f"{v}: JSON {by_version[v]['valid_json']:.0%}, "
            f"schema {by_version[v]['schema_valid_rate']:.0%}" for v in ('v1','v2','v3'))
        decision = (f"I selected {version} and verified its production alias through MLflow. "
                    if version else 'No prompt qualified, so no production promotion was performed. ')
        decision += f"Observed results were {comparison}. "
        decision += (f"The candidate had mean latency {selected['avg_latency_seconds']:.3f} seconds, "
            f"mean input/output tokens {selected['avg_input_tokens']:.1f}/{selected['avg_output_tokens']:.1f}, "
            f"and concept coverage {selected['quality_score']:.0%}. ")
    else:
        latency_text = ('Latency results are pending because the model has not been supplied or run. '
            'The five-row Task 1 table will use basic-prompt requests; the complete CSV will contain all '
            'fifteen attempts. UTC timestamps document when requests occur, while a monotonic clock '
            'measures elapsed time. Mean, median, minimum, maximum and sample standard deviation will '
            'be calculated from successful requests. Longer generated answers, initial model preparation '
            'and CPU scheduling are possible causes of a slow request, not findings from this unexecuted draft.')
        cost_text = ('Cost results and monthly projections are pending. Each cost will equal input tokens '
            'divided by one million times the input rate, plus output tokens divided by one million times '
            'the output rate. The mean is multiplied by 10,000 for the monthly estimate. The configurable '
            'reference is Hugging Face AWS intel-spr x4 at USD 0.134/hour, checked on 3 November 2026. '
            'Measured local throughput will convert this hosting assumption into effective token rates. '
            'These are estimates, not cloud invoices; shorter responses are the initial optimization recommendation.')
        decision = ('No prompt has been promoted because there are no measured responses yet. The intended '
            'choice is evidence-driven: the structured JSON prompt is a candidate rather than a presumed '
            'winner. Actual comparisons of quality, JSON validity, latency, tokens and cost will be inserted '
            'after the local experiment. ')
    promotion = decision + (
        'Promotion requires five successful requests, a JSON syntax pass rate of one, exact schema '
        'compliance of one and concept coverage of at least eighty percent. Among eligible prompts, '
        'higher concept coverage takes priority, followed by lower estimated cost and lower mean latency. '
        'This reflects EduAssist\'s requirement that downstream software reliably read answer, confidence '
        'and key_points. A faster prose answer cannot satisfy that interface merely by costing less. '
        'Concept matching is a transparent quality proxy, not proof of factual accuracy, and confidence '
        'labels are not calibrated probabilities. The saved responses therefore need human inspection '
        'before wider use. Schema checks reject wrong fields, invalid confidence values and empty key '
        'points; JSON parsing rejects code fences and duplicate keys. Failed and truncated responses '
        'block promotion instead of disappearing from the denominator. Longer prompts can increase '
        'input consumption, while JSON structure can increase output consumption. Those tradeoffs must '
        'be accepted using the observed token counts and hosting estimate. Five questions cannot establish '
        'production reliability; broader questions and repeated runs are necessary before deployment.')
    method_settings = metadata['settings'] if measured else None
    method_identity = (f"Model: {method_settings['model']}; API: {method_settings['api_version']}. "
                       if measured else '')
    generation = (f"Temperature {method_settings['temperature']}, seed {method_settings['seed']} and a common "
                  f"{method_settings['max_output_tokens']}-token output cap limit variation; "
                  if measured else 'Temperature zero, seed 42 and a common 512-token output cap limit variation; ')
    pricing_reference = (metadata['settings']['hosting']['source_url'] if measured
                         else 'huggingface.co/docs/inference-endpoints/pricing')
    sections = [
        ('Purpose and execution status',
         ('This report accompanies real local-model measurements. ' if measured else
          'DRAFT: no model inference, MLflow runs or screenshots have been collected. ')
         + 'EduAssist needs academic answers in a dependable JSON interface. MLOps primarily manages '
         'data, training, models and deployment; LLMOps also versions prompts, context, output constraints '
         'and inference economics. The assignment permits an open-source local model. No paid API or '
         'Oracle billing is used, and external inference spend is zero.'),
        ('Controlled method',
         'The same five academic questions are evaluated with the exact basic, structured and JSON '
         'prompt templates. Only prompt wording changes. ' + generation + 'deterministic output is not guaranteed. Prompt order '
         'rotates across questions. There are no retries or grammar-enforced JSON shortcuts. ' + method_identity + 'The local '
         'API, configured model identity and server version are preserved in run metadata. Input and '
         'output counts come from the serving model tokenizer, never character-length guesses.'),
        ('Latency interpretation', latency_text),
        ('Token economics', cost_text),
        ('Promotion justification', promotion),
        ('Reproducibility and limits',
         'The notebook, CSVs, raw replies, prompt diffs and MLflow records connect the results to their '
         'sources. Reproduction requires user-supplied model software and dependencies. API secrets, if '
         'local authentication is enabled, come from an environment variable. Capture the five requested '
         'MLflow views after execution and review the final submission checklist. Pricing source: '
         + pricing_reference + '; registry guidance: mlflow.org/docs/latest/genai/prompt-registry/.')]
    return sections, measured


def word_count(sections):
    return len(re.findall(r"\b[\w'-]+\b", '\n'.join(h + ' ' + p for h, p in sections)))


def write_report(rows=None, summaries=None, metadata=None):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    sections, measured = report_sections(rows, summaries, metadata)
    words = word_count(sections)
    justification_words = word_count([sections[4]])
    if not 500 <= words <= 700 or justification_words < 150:
        raise ValueError(f'Report length out of bounds: {words}; justification {justification_words}.')
    stem = 'assignment_report' if measured else 'assignment_report_DRAFT'
    report_dir = ROOT / 'reports'
    report_dir.mkdir(exist_ok=True)
    markdown = '# EduAssist LLMOps assignment report\n\n'
    markdown += f'Status: {"Measured local execution" if measured else "Draft - execution pending"}. '
    markdown += f'Body: {words} words. Promotion justification: {justification_words} words.\n\n'
    markdown += '\n\n'.join('## ' + h + '\n\n' + p for h, p in sections) + '\n'
    (report_dir / (stem + '.md')).write_text(markdown, encoding='utf-8')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody', fontName='Helvetica', fontSize=10,
                              leading=14, spaceAfter=9, textColor=colors.HexColor('#263547')))
    styles.add(ParagraphStyle(name='ReportHeading', fontName='Helvetica-Bold', fontSize=11,
                              leading=15, spaceBefore=6, spaceAfter=5,
                              textColor=colors.HexColor('#12646f')))
    story = [Paragraph('EduAssist | LLMOps Assignment 2', styles['Title']),
             Paragraph('LOCAL EXECUTION' if measured else 'DRAFT - MODEL EXECUTION PENDING',
                       styles['ReportHeading']),
             Paragraph(f"{words} words | USD | Pricing checked " +
                       (metadata['settings']['hosting']['pricing_date'] if measured else '2026-11-03'), styles['Normal']),
             Spacer(1, 14)]
    for heading, paragraph in sections:
        if heading == 'Promotion justification':
            story.append(PageBreak())
        story += [Paragraph(escape(heading), styles['ReportHeading']),
                  Paragraph(escape(paragraph), styles['ReportBody'])]
    def footer(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(45, 25, 'EduAssist academic exercise | Local inference | No paid API')
        canvas.drawRightString(A4[0] - 45, 25, str(document.page))
    pdf = report_dir / (stem + '.pdf')
    SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=45, leftMargin=45,
                      topMargin=38, bottomMargin=43).build(story, onFirstPage=footer, onLaterPages=footer)
    if measured:
        (report_dir / 'promotion_justification.txt').write_text(sections[4][1] + '\n')
    return pdf


def create_charts(summaries):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    versions = [s['prompt_version'] for s in summaries]
    figure, axes = plt.subplots(2, 2, figsize=(10, 6))
    metrics = [('avg_latency_seconds', 'Mean latency (seconds)'),
               ('avg_cost_per_request', 'Estimated USD per request'),
               ('avg_output_tokens', 'Mean output tokens'), ('valid_json', 'JSON validity rate')]
    for axis, (metric, title) in zip(axes.flat, metrics):
        axis.bar(versions, [s[metric] for s in summaries], color=['#94a3b8','#38a3a5','#186a70'])
        axis.set_title(title)
        axis.set_ylim(bottom=0)
        if metric == 'valid_json':
            axis.set_ylim(0, 1.05)
    figure.suptitle('EduAssist - measured local prompt comparison', fontsize=14)
    figure.tight_layout()
    figure.savefig(ROOT / 'reports' / 'prompt_metrics.png', dpi=170)
    plt.close(figure)
