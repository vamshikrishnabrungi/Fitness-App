from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from docs.build_workout_rebuild_reference import (
    add_page_number,
    set_cell_margins,
    set_cell_shading,
    set_repeat_header,
    set_table_geometry,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Research materials" / "blueprints" / "Runlete_Workout_Data_Information.docx"

NAVY = RGBColor(24, 49, 83)
BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
TEAL = RGBColor(23, 121, 118)
INK = RGBColor(32, 38, 45)
MUTED = RGBColor(91, 102, 113)
WHITE = RGBColor(255, 255, 255)

LIGHT_BLUE = "E8EEF5"
LIGHT_TEAL = "E6F3F2"
LIGHT_GOLD = "FFF4CE"
LIGHT_RED = "FDEBEC"
LIGHT_GRAY = "F2F4F7"
MID_GRAY = "D7DDE5"


def set_font(run, size=None, color=None, bold=None, italic=None, name="Calibri") -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def configure_document(doc: Document) -> None:
    doc.core_properties.title = "Runlete Workout Data Information"
    doc.core_properties.subject = "Workout knowledge, constrained-AI planning, deterministic validation, database and governance blueprint"
    doc.core_properties.author = "Runlete"
    doc.core_properties.keywords = "Runlete, workout planner, exercise data, sport demands, PostgreSQL, AI governance"
    doc.core_properties.comments = "Architecture authority; scientific content approval remains a separate controlled workflow."

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.right_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    tokens = {
        "Heading 1": (16, BLUE, 18, 10),
        "Heading 2": (13, BLUE, 14, 7),
        "Heading 3": (12, DARK_BLUE, 10, 5),
    }
    for style_name, (size, color, before, after) in tokens.items():
        style = doc.styles[style_name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for style_name in ("List Bullet", "List Number"):
        style = doc.styles[style_name]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(11)
        style.paragraph_format.left_indent = Inches(0.375)
        style.paragraph_format.first_line_indent = Inches(-0.188)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.line_spacing = 1.25

    header = section.header
    hp = header.paragraphs[0]
    hp.text = "RUNLETE  /  WORKOUT DATA INFORMATION"
    hp.paragraph_format.space_after = Pt(2)
    set_font(hp.runs[0], size=8.5, color=MUTED, bold=True)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fr = fp.add_run("System blueprint  |  Page ")
    set_font(fr, size=8.5, color=MUTED)
    add_page_number(fp)

    first_header = section.first_page_header
    first_header.paragraphs[0].text = ""
    first_footer = section.first_page_footer
    first_footer.paragraphs[0].text = ""


def add_cover(doc: Document) -> None:
    for _ in range(4):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run("SYSTEM BLUEPRINT")
    set_font(r, size=10.5, color=TEAL, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("Runlete Workout\nData Information")
    set_font(r, size=30, color=NAVY, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(34)
    r = p.add_run(
        "The canonical blueprint for workout knowledge, constrained-AI planning, "
        "exercise data, athlete inputs, validation, adaptation and governance"
    )
    set_font(r, size=14, color=MUTED)

    add_callout(
        doc,
        "Purpose",
        "This document defines how Runlete must represent and use workout information. "
        "It is not an exercise library, a workout library, or a collection of sport programs. "
        "It is the specification from which the PostgreSQL schema, Admin Studio, planner, APIs and tests will be built.",
        LIGHT_TEAL,
    )

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(28)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"Version 1.0  |  {date.today().isoformat()}")
    set_font(r, size=10.5, color=MUTED, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Status: architecture authority; scientific content approval remains separate")
    set_font(r, size=9.5, color=MUTED, italic=True)
    doc.add_page_break()


def add_callout(doc: Document, title: str, body: str, fill: str = LIGHT_BLUE) -> None:
    table = doc.add_table(rows=2, cols=1)
    set_table_geometry(table, [9360])
    title_cell = table.cell(0, 0)
    body_cell = table.cell(1, 0)
    set_repeat_header(table.rows[0])
    set_cell_shading(title_cell, fill)
    set_cell_shading(body_cell, fill)
    p = title_cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(title)
    set_font(r, size=11, color=DARK_BLUE, bold=True)
    p = body_cell.paragraphs[0]
    p.add_run(body)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    for run in p.runs:
        set_font(run, size=10.5, color=INK)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)


def add_code_block(doc: Document, code: str) -> None:
    table = doc.add_table(rows=2, cols=1)
    set_table_geometry(table, [9360])
    header = table.cell(0, 0)
    cell = table.cell(1, 0)
    set_repeat_header(table.rows[0])
    set_cell_shading(header, LIGHT_BLUE)
    set_cell_shading(cell, LIGHT_GRAY)
    set_cell_margins(header, top=90, start=120, bottom=90, end=120)
    set_cell_margins(cell, top=120, start=120, bottom=120, end=120)
    header_paragraph = header.paragraphs[0]
    header_paragraph.paragraph_format.space_after = Pt(0)
    header_run = header_paragraph.add_run("Canonical structure — illustrative YAML")
    set_font(header_run, size=9.2, color=DARK_BLUE, bold=True)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(code)
    set_font(run, size=8.1, color=INK, name="Consolas")
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)


def add_bullets(doc: Document, items: list[str], level: int = 0) -> None:
    style = "List Bullet" if level == 0 else "List Bullet 2"
    for item in items:
        p = doc.add_paragraph(item, style=style)
        if level:
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.2


def add_numbered(doc: Document, items: list[str]) -> None:
    for number, item in enumerate(items, 1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.375)
        paragraph.paragraph_format.first_line_indent = Inches(-0.188)
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.line_spacing = 1.25
        paragraph.add_run(f"{number}.  {item}")


def add_table(
    doc: Document,
    headers: list[str],
    rows: list[list[str]],
    widths: list[int],
    *,
    font_size: float = 9.2,
    header_fill: str = LIGHT_BLUE,
) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    header = table.rows[0]
    set_repeat_header(header)
    for index, label in enumerate(headers):
        cell = header.cells[index]
        set_cell_shading(cell, header_fill)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(label)
        set_font(r, size=9.5, color=INK, bold=True)
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cells[index].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.08
            r = p.add_run(str(value))
            set_font(r, size=font_size, color=INK)
    set_table_geometry(table, widths)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)


def add_label_detail(doc: Document, rows: list[tuple[str, str]], fill: str = LIGHT_GRAY) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    set_repeat_header(table.rows[0])
    for index, label in enumerate(("Attribute", "Specification")):
        cell = table.rows[0].cells[index]
        set_cell_shading(cell, LIGHT_BLUE)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(label)
        set_font(r, size=9.3, color=INK, bold=True)
    for label, detail in rows:
        cells = table.add_row().cells
        set_cell_shading(cells[0], fill)
        p = cells[0].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(label)
        set_font(r, size=9.3, color=DARK_BLUE, bold=True)
        p = cells[1].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.08
        r = p.add_run(detail)
        set_font(r, size=9.3, color=INK)
    set_table_geometry(table, [2700, 6660])
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)


def add_contents(doc: Document) -> None:
    doc.add_heading("How to use this blueprint", level=1)
    doc.add_paragraph(
        "Read Sections 1–4 to understand the planning model; Sections 5–9 to design the knowledge data; "
        "Sections 10–14 to implement generation and athlete experience; and Sections 15–18 to build the database, "
        "administration, validation and delivery workflow."
    )
    add_table(
        doc,
        ["Part", "Question answered"],
        [
            ["1. Product contract", "What Runlete is building—and what it refuses to become"],
            ["2. System flow", "How athlete context becomes a validated workout and later adaptation"],
            ["3. Five knowledge layers", "Where each kind of knowledge belongs"],
            ["4–6. Demands and qualities", "How sport evidence becomes trainable priorities"],
            ["7–9. Method data", "How exercises, effects, tags and relationships are represented"],
            ["10–12. Planning", "How programs, phases, weeks, sessions and prescriptions are assembled"],
            ["13–14. Inputs and outputs", "What we collect and what the athlete sees"],
            ["15. AI selection contract", "What AI selects, what it receives and how every output is validated"],
            ["16–18. Platform delivery", "PostgreSQL, Admin Studio, governance, testing and implementation order"],
        ],
        [2700, 6660],
    )


def add_product_contract(doc: Document) -> None:
    doc.add_heading("1. Product contract", level=1)
    add_callout(
        doc,
        "Core decision",
        "Runlete is a constrained-AI physical-preparation planning system backed by reviewed knowledge. "
        "Reviewed demands, rules and templates create the valid planning space; AI composes workouts only from approved candidates; deterministic code validates the complete result before use.",
        LIGHT_GOLD,
    )
    doc.add_heading("1.1 Scope", level=2)
    add_bullets(
        doc,
        [
            "Physical preparation for individual athletes aged 16 and above.",
            "Running sessions, cycling sessions and swimming sessions may be prescribed directly; technical practice for other sports is treated as external load.",
            "Strength, power, speed, deceleration, change of direction, reactive agility, conditioning, regional tissue capacity, mobility and recovery-support work.",
            "One primary sport or running event drives the plan; secondary sports modify workload and supporting priorities.",
            "Pain input triggers conservative modification, stopping or referral—not diagnosis or rehabilitation treatment.",
        ],
    )
    doc.add_heading("1.2 Explicit exclusions", level=2)
    add_bullets(
        doc,
        [
            "No sport-technique or tactical coaching inside physical-preparation retrieval.",
            "No arbitrary workout generation from a prompt without an active planning context.",
            "No free-form production tags, invented exercise IDs or unbounded prescriptions.",
            "No copied source prose or unowned media.",
            "No silent changes to historical plans when content or rules are updated.",
        ],
    )
    doc.add_heading("1.3 Success criteria", level=2)
    add_bullets(
        doc,
        [
            "Every accepted plan is reproducible from its stored athlete snapshot, candidate packet, model output and version lineage; idempotent retries reuse the accepted result.",
            "Every selection and dose can be traced to a demand, goal, phase, recipe, rule and eligibility decision.",
            "Every displayed method resolves to one approved canonical ID.",
            "No invalid plan can be persisted or shown.",
            "Content can be reviewed and published through Admin Studio without redeploying application code.",
        ],
    )


def add_system_flow(doc: Document) -> None:
    doc.add_heading("2. End-to-end planning and adaptation flow", level=1)
    doc.add_paragraph(
        "The system is hierarchical. Later stages may refine an earlier decision but cannot contradict it. "
        "A session cannot introduce a quality, method or load that the program and current athlete state do not permit."
    )
    rows = [
        ["1", "Athlete state", "Identity, history, readiness, constraints, recent load and feedback"],
        ["2", "Sport/event/position demands", "Demand vector and physical-quality priorities"],
        ["3", "Goal and training phase", "Required adaptations and time horizon"],
        ["4", "Schedule and restrictions", "Available days, practice conflicts, equipment and safety eligibility"],
        ["5", "Program planner", "Program archetype, phase sequence and objective allocation"],
        ["6", "Weekly structure", "High/low placement, session purposes and recovery spacing"],
        ["7", "Session template", "Ordered blocks and required selection slots"],
        ["8", "Method selection", "Eligible exercise, drill or protocol IDs"],
        ["9", "Prescription", "Bounded sets, reps, time, intensity, rest, tempo and progression"],
        ["10", "Validation", "Safety, schedule, workload, duration, conflict and completeness invariants"],
        ["11", "Athlete presentation", "Only actionable workout information and short rationale"],
        ["12", "Completion and feedback", "Actual load, reps, RPE, pain, completion and session response"],
        ["13", "Next-week adjustment", "Bounded, auditable progression, hold, substitution, deload or replan"],
    ]
    add_table(doc, ["Step", "Stage", "Output"], rows, [700, 2600, 6060], font_size=9.0)
    add_callout(
        doc,
        "Invariant",
        "Templates provide structure. Rules and athlete constraints create the eligible candidate space. AI selects and composes inside that space. "
        "Deterministic validation is the final authority and rejects any output that bypasses the chain.",
    )


def add_five_layers(doc: Document) -> None:
    doc.add_heading("3. Five knowledge layers", level=1)
    rows = [
        [
            "1. Exercise, drill and modality library",
            "What training methods exist?",
            "Identity, execution, requirements, safety, media and relations",
            "Fixed programs, sport priorities or universal dosage",
        ],
        [
            "2. Exercise-effect profiles",
            "What adaptation can each method support, and at what cost?",
            "One primary effect, up to three secondary effects, technical/fatigue/impact cost",
            "Claims that one exercise is universally sport-specific",
        ],
        [
            "3. Sport-demand profiles",
            "What must an athlete tolerate or express in a defined sport context?",
            "Evidence-backed demand facts by sport, event, position, level and context",
            "Exercise lists or copied programs",
        ],
        [
            "4. Prescription knowledge",
            "How much, how hard, how often, and under what conditions?",
            "Executable bounds, conflicts, progression, deload and stop rules",
            "Unbounded advice prose",
        ],
        [
            "5. Program and session templates",
            "What structure must a valid plan, week or session contain?",
            "Archetypes, phases, weekly patterns, session blocks and selection slots",
            "Thousands of nearly identical workouts",
        ],
    ]
    add_table(
        doc,
        ["Layer", "Question", "Stores", "Must not store"],
        rows,
        [2100, 2250, 2940, 2070],
        font_size=8.6,
    )
    doc.add_heading("3.1 Why the layers must remain separate", level=2)
    add_bullets(
        doc,
        [
            "An exercise is authored once; sports reference its effects rather than duplicating it.",
            "A sport-demand fact can change without rewriting exercise instructions.",
            "A prescription can change by athlete level or phase without creating another exercise record.",
            "A template can replace a method while preserving the same training objective.",
            "Evidence and approval can be versioned independently from athlete-facing wording and media.",
        ],
    )


def add_demand_model(doc: Document) -> None:
    doc.add_heading("4. Sport-demand model: the depth required for planning", level=1)
    doc.add_paragraph(
        "A demand profile is useful only when it changes a planner decision. A label such as ‘explosive’ or ‘rotational’ is insufficient. "
        "Each demand fact must specify context, magnitude or range where available, evidence confidence, the implied physical quality, "
        "and exactly which planning decisions it may influence."
    )
    add_label_detail(
        doc,
        [
            ("Context", "Sport, event, position, level, sex/age where relevant, competition or training, surface, equipment and environmental conditions."),
            ("Observation", "The measured or reported demand with value, range, distribution and unit where evidence permits."),
            ("Interpretation", "Direct finding, evidence-supported training implication or clearly labeled practitioner inference."),
            ("Decision link", "The quality priority, weekly exposure, session type, method constraint or monitoring action that may change."),
            ("Confidence", "Evidence hierarchy, population match, sample limitations, uncertainty and review status."),
        ],
    )

    dimensions = [
        [
            "Force requirements",
            "Peak/mean force where useful; impulse; RFD window; relative vs absolute demand; unilateral/bilateral expression; external resistance/contact; frequency of high-force actions.",
            "Weights maximum-strength, explosive-strength, eccentric or isometric priorities; informs loading method, prerequisites and weekly high-neural exposure.",
            "Do not infer a barbell percentage directly from one sport-force measurement or confuse high force with high power.",
        ],
        [
            "Direction of force",
            "Distribution of vertical, horizontal, lateral and rotational force by task phase—not one label for the entire sport.",
            "Balances force-orientation exposure across acceleration, jumping, braking, lateral movement and rotational transfer; influences method mix and cueing.",
            "Do not select an exercise merely because it visually imitates the sport action.",
        ],
        [
            "Contraction behavior",
            "Concentric, eccentric, isometric and stretch-shortening demands; action duration; joint angle; yielding vs overcoming; fast vs slow SSC exposure.",
            "Determines whether the plan needs force production, braking, positional isometrics, tendon/region capacity or reactive elastic work and where it belongs in the week.",
            "Do not treat contraction tags as interchangeable or prescribe high eccentric/SSC load without recovery accounting.",
        ],
        [
            "Movement speed",
            "Velocity range, acceleration distance, maximum-velocity exposure, contact time, action frequency and quality-loss threshold.",
            "Determines sprint modality, rest completeness, neural freshness, technical prerequisites and high/low scheduling.",
            "Do not turn speed work into conditioning by shortening recovery until mechanics deteriorate.",
        ],
        [
            "Duration of efforts",
            "Distribution—not only average—of bouts, rallies, shifts, repetitions and continuous work; intensity within each duration band.",
            "Selects energy-system modality, interval duration, density, session volume and event-specific progression.",
            "Do not copy competition duration directly into every training interval.",
        ],
        [
            "Recovery between efforts",
            "Within-bout pauses, between-effort recovery, substitutions/rotations, between-event recovery and day-to-day congestion.",
            "Sets work-to-rest ranges, cluster design, repeated-effort targets and recovery spacing across the week.",
            "Do not assume short competition recovery means all training should use incomplete rest.",
        ],
        [
            "Joint positions",
            "Positions where force is absorbed or produced; ROM demands; trunk orientation; single-leg stance; overhead/contact constraints; time spent near critical positions.",
            "Influences exercise ROM, positional isometrics, unilateral choices, mobility prerequisites and substitutions while preserving the target effect.",
            "Do not force sport-like joint shapes under load when a safer general method trains the same quality.",
        ],
        [
            "Repeated-effort demands",
            "Number and clustering of efforts; inter-effort recovery; output decay; accumulated contacts/sprints/throws; late-game or late-race behavior.",
            "Determines whether the athlete needs capacity to reproduce output, aerobic recovery between efforts, or event-specific speed endurance.",
            "Do not use exhaustive circuits as a universal repeated-effort solution.",
        ],
        [
            "Competition schedule",
            "Season length, match frequency, tournament density, travel, priority events, start windows, role minutes and taper opportunity.",
            "Controls phase selection, weekly structure, maintenance dose, taper, top-up work, deload and when progressions are prohibited.",
            "Do not let a gym template override the competition calendar.",
        ],
        [
            "Commonly stressed tissues",
            "Tissue exposure by magnitude, rate, volume, joint position, surface and recent workload; population-specific patterns with uncertainty.",
            "Adds capacity priorities, exposure monitoring, conflict checks and conservative substitutions. It does not create injury-prevention claims.",
            "Do not diagnose, predict individual injury or prescribe rehabilitation from epidemiology alone.",
        ],
        [
            "Position/event demands",
            "How a role or event deviates materially from the sport average: movement distribution, contact, work density, range, external load and schedule.",
            "Adjusts priority weights, weekly exposures and constraints without duplicating the entire sport profile.",
            "Do not create role differences when evidence or practical consequence is trivial.",
        ],
    ]
    add_table(
        doc,
        ["Demand dimension", "What the data must capture", "Planner consequence", "Guardrail"],
        dimensions,
        [1500, 3000, 3000, 1860],
        font_size=8.0,
    )


def add_special_demand_patterns(doc: Document) -> None:
    doc.add_heading("5. High-value demand patterns that require explicit modeling", level=1)
    doc.add_heading("5.1 Rotation and force transfer", level=2)
    add_label_detail(
        doc,
        [
            ("Model", "Separate producing rotation, resisting rotation, decelerating rotation and transferring force between lower and upper body. Record direction, stance, movement freedom, intent and velocity."),
            ("Planner use", "Choose among ballistic throws, cable/band rotation, anti-rotation, carries and compound lifts according to the required effect and phase—not because a movement looks sport-specific."),
            ("Dose drivers", "Ballistic intent and full recovery for rotational power; time/position/load for isometric resistance; controlled range and fatigue for capacity work."),
            ("Validation", "Prevent redundant high rotational stress near high-volume striking, throwing or serving; respect equipment, space and technical level."),
        ],
        LIGHT_TEAL,
    )
    doc.add_heading("5.2 Isometric force capacity", level=2)
    add_label_detail(
        doc,
        [
            ("Model", "Record joint angle or position, overcoming vs yielding intent, hold duration, external load, unilateral/bilateral stance and whether the goal is force, position, analgesic support or local endurance."),
            ("Planner use", "Use isometrics when a position must be maintained, force must transfer with little movement, dynamic loading is constrained, or a phase requires low-skill force exposure."),
            ("Dose drivers", "Short maximal intent and long recovery differ from longer submaximal holds; these must be different prescription families."),
            ("Validation", "Do not label every static exercise as equivalent. Match angle, intent and duration to the target effect and athlete tolerance."),
        ],
        LIGHT_TEAL,
    )
    doc.add_heading("5.3 Local muscular endurance", level=2)
    add_label_detail(
        doc,
        [
            ("Model", "Identify the region, contraction pattern, force level, work duration, duty cycle, ROM and whether fatigue must be resisted continuously or across repeated bouts."),
            ("Planner use", "Select local capacity work only when the demand profile and phase require it; distinguish it from global conditioning and aerobic development."),
            ("Dose drivers", "Time under tension, repetitions, work-to-rest, external load and technical-quality limits. The target region—not general exhaustion—defines success."),
            ("Validation", "Avoid fatigue circuits that degrade important movement quality or duplicate sport-practice load."),
        ],
        LIGHT_TEAL,
    )
    doc.add_heading("5.4 Plyometrics and elastic/reactive work", level=2)
    add_label_detail(
        doc,
        [
            ("Model", "Record direction, amplitude, contact type, contact-time intent, bilateral/unilateral pattern, continuous vs reset execution, landing demand, surface and total contacts."),
            ("Planner use", "Progress from landing/low-amplitude rhythm to higher-force or faster-contact variants only when level, recent exposure, pain and movement prerequisites pass."),
            ("Dose drivers", "Contacts, sets, repetitions, approach, intensity, recovery and quality-loss stopping rule. High-intensity contacts are not interchangeable with low-level contacts."),
            ("Validation", "Account for sport jump/sprint contacts, surface, footwear, competition proximity and other eccentric load before adding volume."),
        ],
        LIGHT_TEAL,
    )


def add_quality_taxonomy(doc: Document) -> None:
    doc.add_heading("6. Canonical physical-quality taxonomy", level=1)
    doc.add_paragraph(
        "Physical qualities are controlled entities with stable codes. A sport profile assigns priority weights to them; a method-effect profile states which qualities a method can support. "
        "They are not free-form tags and they are not shown in full to athletes."
    )
    rows = [
        ["Force and strength", "maximum_strength; relative_strength; explosive_strength; eccentric_force_capacity; isometric_force_capacity; local_muscular_endurance"],
        ["Speed", "acceleration; maximum_velocity; speed_endurance; movement_speed_expression"],
        ["Braking and direction", "deceleration; planned_change_of_direction; reactive_agility; lateral_movement_capacity"],
        ["Power", "vertical_power; horizontal_power; lateral_power; rotational_power; upper_body_ballistic_power"],
        ["Elastic qualities", "reactive_elastic_strength; fast_stretch_shortening_cycle; slow_stretch_shortening_cycle; landing_force_management"],
        ["Energy-system qualities", "aerobic_capacity; high_intensity_aerobic_power; threshold_capacity; anaerobic_power; anaerobic_capacity; repeated_sprint_ability; repeated_high_intensity_effort"],
        ["Regional capacity", "calf_soleus_capacity; foot_ankle_capacity; tibialis_capacity; hamstring_capacity; adductor_capacity; quadriceps_patellar_capacity; hip_capacity; shoulder_capacity; elbow_wrist_capacity; neck_capacity; grip_capacity"],
        ["Trunk and transfer", "trunk_force_transfer; anti_extension_capacity; anti_rotation_capacity; anti_lateral_flexion_capacity; controlled_rotation_capacity"],
        ["Movement access", "task_relevant_mobility; positional_control; balance_and_stability"],
    ]
    add_table(doc, ["Family", "Initial controlled quality codes"], rows, [2350, 7010], font_size=9.0)
    add_callout(
        doc,
        "Taxonomy rule",
        "Add a new quality only when it changes demand priority, method selection, prescription, validation or reporting. "
        "Synonyms belong in labels/aliases; they do not become additional qualities.",
        LIGHT_GOLD,
    )
    doc.add_heading("6.1 Priority model", level=2)
    add_bullets(
        doc,
        [
            "Base priority comes from sport/event/position demand facts.",
            "Goal and phase modify the base priority for the current block.",
            "Athlete assessment identifies deficits, strengths and prerequisites.",
            "Practice and competition load reduce or satisfy some exposures.",
            "Pain, restrictions, equipment and schedule constrain eligible methods—not the underlying need.",
            "The planner produces a final weekly quality budget: develop, maintain, expose, monitor or omit.",
        ],
    )


def add_method_schema(doc: Document) -> None:
    doc.add_heading("7. Canonical exercise, drill and modality record", level=1)
    doc.add_paragraph(
        "The method record describes what a movement or protocol is and how it can be performed safely. It does not contain a universal workout prescription. "
        "Sets, repetitions, intensity and rest are produced later by prescription rules."
    )
    sections = [
        ["Identity", "Canonical UUIDv7, stable code, display name, aliases, method type, version and lifecycle status"],
        ["Classification", "Primary/secondary movement patterns, laterality, planes, force directions, contraction emphasis, velocity class, chain and loading position"],
        ["Effect profile", "Exactly one primary effect; no more than three secondary effects; role and evidence scope"],
        ["Cost profile", "Technical, fatigue, impact, setup, space and supervision costs using controlled scales"],
        ["Eligibility", "Level, environment, equipment alternatives, space, partner, prerequisites and prohibited contexts"],
        ["Execution", "Original setup, ordered instructions, cues, common errors and corrections"],
        ["Safety", "General stop conditions, conservative considerations, supervision needs and excluded claims"],
        ["Relations", "Regressions, progressions and objective-preserving substitutions with reasons and conditions"],
        ["Media", "Owned/licensed status, asset IDs, angle requirements, review and accessibility text"],
        ["Governance", "Evidence links, review scope, reviewer, generator eligibility, effective/retired dates and audit history"],
    ]
    add_table(doc, ["Section", "Required content"], sections, [2200, 7160], font_size=9.1)
    doc.add_heading("7.1 Controlled movement fields", level=2)
    add_table(
        doc,
        ["Field", "Shape", "Rule"],
        [
            ["primary_pattern", "One controlled code", "The dominant movement organization used for retrieval and balance"],
            ["secondary_patterns", "Zero to two codes", "Only patterns materially required by execution"],
            ["force_direction_primary", "One code", "vertical, horizontal, lateral, rotational or mixed"],
            ["force_direction_secondary", "Zero to two codes", "Used only when meaningfully different from the primary direction"],
            ["contraction_emphasis", "Zero to two codes", "dynamic_concentric, eccentric, isometric, fast_ssc or slow_ssc"],
            ["velocity_class", "One code", "controlled, strength_speed, speed_strength, ballistic or maximal_locomotion"],
            ["laterality", "One code", "bilateral, unilateral, alternating or asymmetrical"],
            ["movement_planes", "One to two codes", "sagittal, frontal, transverse or multiplanar"],
            ["execution_format", "One or more supported modes", "repetition, distance, time, hold, contacts, interval or continuous"],
        ],
        [2500, 2450, 4410],
        font_size=8.8,
    )
    doc.add_heading("7.2 Canonical machine-record skeleton", level=2)
    doc.add_paragraph(
        "The eventual API may expose this through generated contracts, but the logical shape remains stable. "
        "Codes reference normalized tables; they are not free-text labels."
    )
    add_code_block(
        doc,
        "method:\n"
        "  id: uuidv7\n"
        "  stable_code: strength.goblet_squat\n"
        "  type: exercise | athletic_drill | conditioning_modality | assessment\n"
        "  content_version: integer\n"
        "  status: draft | review | published | retired\n"
        "  classification:\n"
        "    primary_pattern: controlled_code\n"
        "    secondary_patterns: [0..2 controlled_codes]\n"
        "    force_directions: {primary: code, secondary: [0..2]}\n"
        "    contraction_emphasis: [0..2 controlled_codes]\n"
        "    velocity_class: controlled_code\n"
        "    laterality: controlled_code\n"
        "    movement_planes: [1..2 controlled_codes]\n"
        "    execution_formats: [one_or_more_codes]\n"
        "  effects:\n"
        "    primary: exactly_one_quality_code\n"
        "    secondary: [0..3 quality_codes]\n"
        "    permitted_roles: [primary | accessory | preparation | capacity | recovery]\n"
        "  costs: {technical, fatigue, impact, setup, supervision}\n"
        "  eligibility: {levels, environments, equipment_options, prerequisites, exclusions}\n"
        "  execution: {setup, ordered_steps, cues, errors_with_corrections}\n"
        "  safety: {stop_conditions, considerations, supervision_requirements}\n"
        "  relations: [regression | progression | substitution + objective + conditions]\n"
        "  media: {asset_ids, ownership, views, alt_text, review_status}\n"
        "  governance: {evidence_ids, reviewer_scope, generator_eligible, release_id}"
    )


def add_tags_and_retrieval(doc: Document) -> None:
    doc.add_heading("8. Tags, structured fields and retrieval", level=1)
    add_callout(
        doc,
        "Tag policy",
        "Tags are a small controlled discoverability layer—not the primary knowledge model. "
        "If a value affects planning, safety, substitution or dosage, it belongs in a typed field or relation instead of a tag.",
        LIGHT_GOLD,
    )
    add_table(
        doc,
        ["Information", "Representation", "Example"],
        [
            ["Primary adaptation", "method_effect relation", "lower_body_strength"],
            ["Movement pattern", "typed classification", "squat"],
            ["Equipment", "method_equipment relation", "kettlebell OR dumbbell"],
            ["Environment", "method_environment relation", "home, gym"],
            ["Sport relevance", "demand → quality → effect matching", "No direct ‘football exercise’ tag"],
            ["Level", "eligibility relation with conditions", "beginner allowed; advanced allowed"],
            ["Synonym", "alias table", "KB goblet squat"],
            ["Discoverability hint", "controlled tag", "minimal_equipment"],
        ],
        [2250, 3750, 3360],
        font_size=9.0,
    )
    doc.add_heading("8.1 Initial controlled tag registry", level=2)
    add_table(
        doc,
        ["Category", "Allowed examples", "Planner authority"],
        [
            ["Logistics", "minimal_equipment; small_space; travel_friendly; low_noise", "Filter or preference only"],
            ["Delivery", "team_station_friendly; solo_friendly; partner_assisted", "Scheduling/setup hint"],
            ["Teaching", "easy_to_coach; technique_prerequisite; external_supervision", "Secondary hint; typed technical cost remains authoritative"],
            ["Presentation", "warm_up_friendly; cooldown_friendly", "UI/search hint; recipe slot remains authoritative"],
        ],
        [1800, 4000, 3560],
        font_size=8.9,
    )
    add_bullets(
        doc,
        [
            "Maximum five controlled tags per method unless the taxonomy owner approves an exception.",
            "No sport names, muscles, qualities, equipment, difficulty levels or injury names as duplicate tags.",
            "Admin users select tags from a registry; they cannot create arbitrary production strings.",
            "Core selection uses normalized joins and rules. Tags may narrow or rank results but never override safety or eligibility.",
        ],
    )


def add_method_relationships(doc: Document) -> None:
    doc.add_heading("9. Progressions, regressions and substitutions", level=1)
    doc.add_paragraph(
        "A progression graph is not one universal ladder. Relationships are directional, objective-specific and conditional. "
        "The same method may be a progression for one objective and an inappropriate replacement for another."
    )
    add_table(
        doc,
        ["Relation", "Must preserve", "May change", "Required conditions"],
        [
            ["Regression", "Primary training objective", "Load, ROM, stability demand, velocity, impact, complexity or equipment", "Reason for regression and exit criteria"],
            ["Progression", "Primary objective or planned next objective", "Only the intended progression dimension", "Prerequisites, exposure history, quality and response gate"],
            ["Substitution", "Primary effect and session role", "Movement family, equipment or implementation", "Comparable cost; no new contraindication or schedule conflict"],
        ],
        [1700, 2500, 2720, 2440],
        font_size=8.8,
    )
    doc.add_heading("9.1 Progression dimensions", level=2)
    add_bullets(
        doc,
        [
            "External load or relative intensity.",
            "Volume: sets, repetitions, distance, time or contacts.",
            "Range of motion or positional demand.",
            "Movement velocity or intent.",
            "Stability, laterality or coordination complexity.",
            "Impact, eccentric or stretch-shortening-cycle intensity.",
            "Density through reduced recovery—only when density is the target quality.",
            "Specificity toward the event or position demand.",
        ],
    )
    add_callout(
        doc,
        "Default progression rule",
        "Change the smallest number of variables needed to create the target adaptation while preserving execution quality and schedule coherence. "
        "A planner may progress multiple variables only when an approved rule explicitly permits it.",
    )
    doc.add_heading("9.2 Selection sequence", level=2)
    add_numbered(
        doc,
        [
            "Identify the session slot and required primary effect.",
            "Apply level, safety, environment and equipment eligibility filters.",
            "Apply direction, contraction, velocity and execution-format requirements when they materially affect the objective.",
            "Compare fatigue, impact, technical and setup costs against the weekly budget.",
            "Prefer continuity with the athlete’s recent successful method unless variation has a defined reason.",
            "If the preferred method is ineligible, traverse an approved substitution or regression relation and record the reason.",
        ],
    )


def add_exercise_examples(doc: Document) -> None:
    doc.add_heading("10. Exercise record examples", level=1)
    doc.add_paragraph(
        "These examples demonstrate the data shape; they are not production approvals or fixed prescriptions. "
        "The same record structure applies to exercises, athletic drills and conditioning modalities with type-specific fields."
    )

    doc.add_heading("10.1 Goblet Squat", level=2)
    add_label_detail(
        doc,
        [
            ("Identity", "code: strength.goblet_squat | type: exercise | status: draft | generator eligible: false"),
            ("Classification", "primary pattern: squat | secondary: brace | bilateral | sagittal | closed chain | anterior load | primary force direction: vertical | velocity: controlled"),
            ("Effects", "primary: lower_body_strength | secondary: quadriceps_capacity, hip_capacity, trunk_force_transfer"),
            ("Costs", "technical: low | fatigue: moderate | impact: low | setup: low | supervision: low"),
            ("Eligibility", "beginner–advanced | home/gym | kettlebell OR dumbbell | small space | no partner"),
            ("Tags", "minimal_equipment; small_space; easy_to_coach"),
            ("Execution", "Hold the load close to the chest; establish whole-foot pressure; brace; descend by bending knees and hips; use only a controllable depth; stand without leaning backward."),
            ("Common errors", "Heel lift; uncontrolled knee movement; trunk collapse; uncontrolled descent. Each error requires a stored correction, not merely an error label."),
            ("Safety", "Stop for sharp/increasing pain, loss of balance or inability to control the load. Current lower-limb or low-back symptoms require conservative modification, not diagnosis."),
            ("Relations", "regressions: bodyweight box squat, counterbalance squat | progressions: double-dumbbell front squat, front squat | substitution depends on primary effect and available equipment"),
        ],
    )

    doc.add_heading("10.2 Pogo Jump in Place", level=2)
    add_label_detail(
        doc,
        [
            ("Identity", "code: plyometric.pogo_jump_in_place | type: athletic_drill | status: draft | generator eligible: false"),
            ("Classification", "primary pattern: jump_rebound | bilateral | vertical | fast SSC | ballistic | repeated contacts | forefoot-to-whole-foot controlled contact"),
            ("Effects", "primary: reactive_elastic_strength | secondary: calf_soleus_capacity, foot_ankle_capacity, landing_force_management"),
            ("Costs", "technical: moderate | fatigue: low per set | impact: moderate | setup: low | supervision: conditional"),
            ("Eligibility", "conditional beginner; intermediate–advanced | field/gym/home with suitable surface | requires recent impact tolerance and acceptable landing control"),
            ("Tags", "minimal_equipment; small_space; warm_up_friendly"),
            ("Execution", "Use low amplitude; keep contacts rhythmic and controlled; maintain posture; stop when contact quality, rhythm or position deteriorates."),
            ("Common errors", "Turning the drill into maximal jumps; excessive knee collapse; loud or prolonged contacts; continuing after rhythm or posture deteriorates."),
            ("Safety", "Exclude during unresolved pain or poor recent impact tolerance. Contact volume must include other weekly sprint, jump and sport exposures."),
            ("Relations", "regressions: ankle rocker/raise capacity, low-amplitude snap-down or supported rhythm drill as appropriate | progressions: directional or higher-intensity reactive variants only through explicit gates"),
        ],
        LIGHT_TEAL,
    )

    doc.add_heading("10.3 Half-Kneeling Band Anti-Rotation Press Hold", level=2)
    add_label_detail(
        doc,
        [
            ("Identity", "code: trunk.half_kneeling_band_anti_rotation_press_hold | type: exercise | status: draft | generator eligible: false"),
            ("Classification", "primary pattern: anti_rotation | asymmetrical stance | transverse resistance | isometric emphasis | controlled | cable/band horizontal line of pull"),
            ("Effects", "primary: trunk_force_transfer | secondary: isometric_force_capacity, anti_rotation_capacity, shoulder_capacity"),
            ("Costs", "technical: low–moderate | fatigue: low | impact: low | setup: low | supervision: low"),
            ("Eligibility", "beginner–advanced | home/gym | resistance band OR cable | requires stable anchor and comfortable kneeling position"),
            ("Tags", "minimal_equipment; small_space; low_noise"),
            ("Execution", "Establish a stable half-kneeling position; hold the handle near the chest; press away without allowing trunk or pelvis rotation; maintain breathing and controlled alignment."),
            ("Common errors", "Using excessive resistance; rotating toward the anchor; losing pelvic position; breath holding beyond the intended strategy; unstable band anchor."),
            ("Safety", "Use a secure anchor and controllable resistance. Modify stance or choose another trunk method if kneeling is not tolerated."),
            ("Relations", "regression: tall-kneeling or wider-base anti-rotation variation when appropriate | progression: narrower base, standing/split stance, increased lever or dynamic press only when objective and control justify it"),
        ],
    )


def add_prescription_model(doc: Document) -> None:
    doc.add_heading("11. Prescription and constraint knowledge", level=1)
    doc.add_paragraph(
        "A method record answers ‘what can be used.’ A prescription rule answers ‘how it is used for this athlete, objective and phase.’ "
        "Prescription logic must be executable, bounded and auditable."
    )
    add_table(
        doc,
        ["Rule component", "Required structure"],
        [
            ["Scope", "Sport/event/position if relevant; quality; phase; level; method type; environment"],
            ["Conditions", "Typed athlete, schedule, recent-load, assessment and readiness fields using approved operators"],
            ["Action", "Select, require, limit, exclude, substitute, progress, hold, deload, stop or refer"],
            ["Dose bounds", "Sets/reps/time/distance/contacts; intensity method; rest; tempo; frequency; weekly exposure"],
            ["Progression", "Trigger, permitted dimension, increment/range, minimum exposure and success criteria"],
            ["Regression", "Trigger, changed dimension, minimum retained objective and recovery condition"],
            ["Conflict", "Minimum spacing or prohibited combination with practices, competitions or other high-load methods"],
            ["Evidence", "Claim IDs, population/context scope, confidence and reviewer"],
            ["Failure behavior", "Conservative fallback or explicit inability to generate—not an invented value"],
        ],
        [2200, 7160],
        font_size=9.0,
    )
    doc.add_heading("11.1 Intensity hierarchy", level=2)
    doc.add_paragraph(
        "The rule chooses the most reliable available intensity anchor for the method and athlete. It must also define a fallback order. "
        "Examples include percentage of a valid benchmark, velocity, pace, heart-rate zone, RPE/RIR, talk test, technical-quality threshold or submaximal intent. "
        "The hierarchy is event- and method-specific; no single anchor is universal."
    )
    doc.add_heading("11.2 Workload accounting", level=2)
    add_bullets(
        doc,
        [
            "Count both prescribed load and external sport load.",
            "Maintain separate budgets for high-speed running, acceleration, change of direction, jumps/contacts, heavy strength, eccentric stress, throwing/bowling/serving, sparring/contact and conditioning intensity.",
            "Do not collapse all load into one score when different tissues or qualities need separate conflict checks.",
            "Use rolling history to inform decisions, but never let a noisy metric override explicit pain, restriction or competition constraints.",
        ],
    )


def add_template_model(doc: Document) -> None:
    doc.add_heading("12. Program, week and session templates", level=1)
    add_callout(
        doc,
        "Template principle",
        "Templates define required structure and selection slots. They do not contain a final list of exercises for every athlete. "
        "A template becomes a workout only after demand priorities, athlete constraints, method eligibility and prescription rules are applied.",
        LIGHT_GOLD,
    )
    add_table(
        doc,
        ["Template level", "Defines", "Example structural decisions"],
        [
            ["Program archetype", "Purpose, horizon, required phases and transition gates", "General preparation → specific preparation → competition/taper → transition"],
            ["Phase", "Priority qualities, develop/maintain status, volume/intensity direction and entry/exit conditions", "Develop acceleration; maintain maximum strength; expose calf–soleus capacity"],
            ["Weekly structure", "Number and purposes of sessions, high/low pattern, competition/practice anchors and minimum spacing", "High neural day aligned with hard practice; recovery day after competition"],
            ["Session recipe", "Ordered blocks, time budget, required quality slots and allowed optional slots", "Preparation → primary speed/power → primary strength → accessory capacity → cooldown"],
            ["Block recipe", "Slot objective, method type, selection constraints and prescription family", "One vertical-power method with low fatigue cost and full recovery"],
        ],
        [1800, 3950, 3610],
        font_size=8.8,
    )
    doc.add_heading("12.1 Generate the program before workouts", level=2)
    add_numbered(
        doc,
        [
            "Resolve goal dates, competition calendar and available planning horizon.",
            "Create the macrocycle and phase objectives.",
            "Allocate quality priorities and external-load assumptions to phases.",
            "Create weekly structures with recoverable spacing.",
            "Select session recipes that satisfy each week’s objectives.",
            "Fill recipe slots with eligible methods.",
            "Apply prescriptions and validate the complete week before showing any session.",
        ],
    )
    doc.add_heading("12.2 Template selection inputs", level=2)
    add_bullets(
        doc,
        [
            "Primary goal, event and time horizon.",
            "Current phase and competition proximity.",
            "Quality budget and develop/maintain/expose/omit decisions.",
            "Available days, session duration and practice/competition anchors.",
            "Athlete level, recent load, readiness and restrictions.",
            "Equipment, environment, team/solo delivery and setup constraints.",
        ],
    )


def add_athlete_inputs(doc: Document) -> None:
    doc.add_heading("13. Athlete information and onboarding contract", level=1)
    doc.add_paragraph(
        "Runlete should collect only information that changes a decision, improves safety or supports adaptation. "
        "Every required field must have a named consumer in the planner or validator."
    )
    rows = [
        ["Sport identity", "Primary sport; event/discipline; position/role; competition level; secondary sports", "Demand profile and external-load model"],
        ["Goal", "Goal type; target metric; priority; target event/date; acceptable time horizon", "Program archetype and phase allocation"],
        ["Training history", "Training age; recent consistency; recent strength/speed/endurance exposure; previous program", "Level and progression eligibility"],
        ["Current sport load", "Practice days; match/race calendar; minutes/role; running/jump/throw/bowling/sparring/pool/bike exposure as relevant", "Conflict and workload budget"],
        ["Availability", "Training days; preferred days; session duration; travel; unavailable dates", "Weekly structure"],
        ["Resources", "Equipment; facilities; field/pool/road access; space; surface; partner/supervision", "Method and recipe eligibility"],
        ["Performance anchors", "Recent race result; benchmark; validated assessment; pace/HR/velocity/strength anchors where appropriate", "Intensity prescription and deficit analysis"],
        ["Health constraints", "Current pain; professional restrictions; cleared return status; relevant conditions; medications only when explicitly required", "Conservative eligibility and referral"],
        ["Readiness", "Sleep, stress, soreness, motivation and recent session response", "Daily modification within bounded rules"],
        ["Preferences", "Exercise dislikes, accessibility needs, coaching style and notification preference", "Adherence ranking after safety/objective filters"],
    ]
    add_table(doc, ["Input group", "Structured fields", "Planner consumer"], rows, [1800, 4800, 2760], font_size=8.4)
    doc.add_heading("13.1 Required versus optional", level=2)
    add_bullets(
        doc,
        [
            "Required: primary sport/event, goal, availability, session duration, training history, equipment/environment and current restrictions.",
            "Conditionally required: position, competition date, practice schedule, performance anchors and sport-specific exposure measures.",
            "Optional: preferences and additional metrics that do not block a safe baseline plan.",
            "If essential data is missing, the planner requests it or produces a conservative limited plan; it does not guess.",
        ],
    )


def add_output_contract(doc: Document) -> None:
    doc.add_heading("14. Athlete-facing workout information", level=1)
    doc.add_paragraph(
        "The athlete sees enough information to execute the session correctly and understand its purpose. Internal evidence, taxonomies, rule traces and administrative data remain available to staff but do not overload the workout screen."
    )
    add_table(
        doc,
        ["Show to athlete", "Keep internal"],
        [
            ["Session name, date, expected duration and primary objective", "Template IDs, rule IDs and algorithm trace"],
            ["Readiness modification or important safety notice", "Raw health inputs and internal risk flags"],
            ["Ordered blocks with estimated time", "Candidate methods that were rejected"],
            ["Exercise/drill name, owned media, concise setup and execution", "Full evidence records and reviewer notes"],
            ["Sets/reps/time/distance/contacts, intensity, rest and tempo when relevant", "Taxonomy metadata and retrieval scores"],
            ["One short purpose statement and approved substitution when useful", "AI prompt, chain-of-thought or hidden scoring"],
            ["Completion controls: actual load/reps, RPE, pain, completion and note", "Credentials, secrets, private operational metadata"],
        ],
        [4680, 4680],
        font_size=9.0,
    )
    doc.add_heading("14.1 Workout response shape", level=2)
    add_label_detail(
        doc,
        [
            ("Session", "id, title, purpose, date, duration estimate, location, readiness state, status and version references"),
            ("Blocks", "ordered block type, objective, time budget and transition notes"),
            ("Items", "approved method ID, display name, prescription, rest, execution summary, media ID and permitted alternative"),
            ("Safety", "only relevant stop/modify messages for this athlete and session"),
            ("Feedback", "completion, actual dose, session RPE, pain response, difficulty, confidence and optional note"),
        ],
    )


def add_ai_boundary(doc: Document) -> None:
    doc.add_heading("15. Constrained AI workout-selection contract", level=1)
    add_callout(
        doc,
        "Non-negotiable",
        "AI is a planner component, but it is never the database or safety authority. It selects methods and composes prescriptions only from the exact approved candidates and bounds supplied by the backend. "
        "Deterministic code validates completeness, eligibility, dosage, schedule, workload and safety before a plan can be stored or shown.",
        LIGHT_RED,
    )
    add_table(
        doc,
        ["AI may do", "AI may not do"],
        [
            ["Choose among the approved method IDs for each reviewed template slot", "Choose any method outside that slot's supplied candidate list or invent an ID"],
            ["Compose a coherent session from reviewed blocks and eligible candidates", "Add, remove or reorder required blocks contrary to the released recipe"],
            ["Choose dose values inside the supplied fixed values or minimum/maximum bounds", "Create a dose field or persist any value outside approved bounds"],
            ["Prefer suitable variation using objective, level and fatigue-cost context", "Override equipment, environment, level, pain, supervision or schedule exclusions"],
            ["Explain an accepted session in clear athlete language", "Diagnose injury, prescribe rehabilitation or claim medical approval"],
            ["Classify free-text feedback into an approved label set with confidence", "Diagnose injury or prescribe rehabilitation"],
            ["Draft original wording for staff review", "Publish content or bypass review"],
            ["Propose a bounded next-week adjustment that the validator rechecks", "Overwrite calculated facts, completed history or immutable content"],
        ],
        [4680, 4680],
        font_size=9.0,
    )
    doc.add_heading("15.1 Compact AI input", level=2)
    add_bullets(
        doc,
        [
            "Sanitized athlete summary limited to fields necessary for the task.",
            "Current program phase, weekly purpose and reviewed session recipe with exact occurrence and slot IDs.",
            "A compact candidate projection containing only released eligible method IDs, stable codes, effects and relevant costs.",
            "Fixed prescription values or typed dose bounds, permitted substitutions and controlled rationale labels.",
            "Recent feedback trend in structured form; raw notes only when interpretation is the explicit task.",
            "Required response schema, allowed labels, token limit and safety boundary.",
        ],
    )
    doc.add_heading("15.2 Information never sent", level=2)
    add_bullets(
        doc,
        [
            "The full exercise, evidence or sport database.",
            "Unrelated sports, rejected/draft content, internal reviewer notes or copyrighted source prose.",
            "Database credentials, API keys, security rules or operational secrets.",
            "Raw GPS history, identity data or health information not required for the specific task.",
            "Hidden evaluation scores, moderation evidence or other users’ data.",
        ],
    )
    doc.add_heading("15.3 AI output handling", level=2)
    add_numbered(
        doc,
        [
            "Parse against a strict schema.",
            "Require exactly one selection for every slot occurrence and reject missing, duplicate or unknown occurrences.",
            "Reject unknown IDs, extra fields, invalid alternatives and out-of-bound dose values.",
            "Run deterministic safety, schedule, duration, spacing, workload and coherence validation.",
            "If validation fails, provide only structured validation errors for one repair attempt; then use a reviewed fallback or fail safely.",
            "Store provider, model, prompt version, response schema, input hash, attempts, token use, latency, accepted output and validation result—not hidden reasoning.",
        ],
    )
    doc.add_heading("15.4 Reproducibility and cost", level=2)
    add_bullets(
        doc,
        [
            "Model sampling is not treated as inherently deterministic. The accepted structured output is immutable and becomes part of the plan's reproducible record.",
            "An idempotency key and input hash prevent repeated calls from producing multiple plans for the same generation request.",
            "The backend sends only the candidate projection needed for the current plan—not the full exercise or evidence database.",
            "Programs and upcoming weeks are generated when needed and adapted after feedback; Runlete does not make a daily AI call merely to redisplay an unchanged workout.",
        ],
    )


def add_database_architecture(doc: Document) -> None:
    doc.add_heading("16. PostgreSQL knowledge and runtime architecture", level=1)
    doc.add_paragraph(
        "PostgreSQL is the sole authority for workout knowledge and generated plans. PostGIS can share the same managed cluster initially while using separate schemas and permissions. "
        "The old Mongo workout collections are not migrated."
    )
    add_table(
        doc,
        ["Schema/domain", "Representative entities"],
        [
            ["governance", "knowledge_sources; evidence_claims; content_versions; content_reviews; publication_releases; audit_events"],
            ["taxonomy", "sports; sport_events; sport_roles; physical_qualities; movement_patterns; equipment; environments; controlled_tags"],
            ["methods", "training_methods; method_aliases; method_classifications; method_effects; method_costs; method_requirements; method_instructions; method_errors; method_constraints; method_relations; method_media; method_tags"],
            ["demands", "sport_demand_facts; demand_contexts; sport_quality_priorities; position_modifiers; evidence_claim_links"],
            ["prescription", "prescription_rules; rule_conditions; rule_actions; dose_bounds; progression_rules; competition_rules; external_load_conflicts"],
            ["recipes", "program_archetypes; program_phases; weekly_recipes; session_recipes; recipe_blocks; recipe_slots; slot_constraints"],
            ["athlete", "athlete_sport_profiles; athlete_schedules; athlete_constraints; athlete_assessments; athlete_states; external_load_records"],
            ["planning", "training_plans; generation_runs; plan_phases; plan_weeks; planned_sessions; session_blocks; prescribed_items; decision_traces; validation_results"],
            ["feedback", "completion_records; prescribed_item_results; readiness_logs; pain_responses; adaptation_decisions"],
        ],
        [2200, 7160],
        font_size=8.7,
    )
    doc.add_heading("16.1 Identifier and version rules", level=2)
    add_bullets(
        doc,
        [
            "One canonical UUIDv7 primary key per entity; one stable unique code for human-readable references.",
            "Names, aliases, source IDs and provider IDs are metadata—not competing primary identifiers.",
            "Published content versions are immutable. Corrections create a superseding version.",
            "Every plan pins exact content, rule, recipe and algorithm versions.",
            "Foreign keys and unique constraints prevent orphan relations, duplicate codes and conflicting publications.",
            "Draft, reviewed, approved, published, retired and quarantined are explicit lifecycle states; generator eligibility is a separate gate.",
        ],
    )
    doc.add_heading("16.2 Planning transaction", level=2)
    add_numbered(
        doc,
        [
            "Create an immutable athlete-context snapshot.",
            "Select one active publication release and algorithm version.",
            "Build the program and decision trace in a transaction/workspace.",
            "Validate every invariant and referenced ID.",
            "Persist the plan atomically only if validation passes.",
            "Emit an outbox event for notifications, cache refresh and downstream jobs.",
        ],
    )


def add_admin_governance(doc: Document) -> None:
    doc.add_heading("17. Admin Studio and content governance", level=1)
    doc.add_paragraph(
        "Admin Studio edits data through authenticated APIs; the browser never connects directly to PostgreSQL. "
        "Content changes do not require a backend redeployment. Algorithm, schema and safety-engine changes remain reviewed code in GitHub."
    )
    add_table(
        doc,
        ["Admin-editable without redeploy", "GitHub + tests + deployment"],
        [
            ["Exercises, drills, modalities, aliases and original instructions", "Planner algorithm and rule interpreter"],
            ["Effect profiles, controlled tags and method relations", "New operator, action or calculation type"],
            ["Demand facts, evidence links and priority candidates", "Hard safety invariants and authorization"],
            ["Bounded prescription-rule instances", "Database schema and migrations"],
            ["Program/session recipe instances and release status", "API contracts and worker orchestration"],
            ["Media ownership/review status and publication scheduling", "Encryption, secrets and infrastructure"],
        ],
        [4680, 4680],
        font_size=9.0,
    )
    doc.add_heading("17.1 Publication workflow", level=2)
    add_numbered(
        doc,
        [
            "Create or edit a draft version.",
            "Run schema, taxonomy, relation, evidence and safety validation.",
            "Preview diffs and simulate affected golden athlete scenarios.",
            "Collect the required S&C, physiotherapy or specialist review for the record’s scope.",
            "Publish one immutable release in a transaction.",
            "Emit a publication event and invalidate only affected caches.",
            "Use the release for new plans; retain historical plan versions.",
            "Rollback by repointing the active release, never by rewriting history.",
        ],
    )
    doc.add_heading("17.2 Minimum controls", level=2)
    add_bullets(
        doc,
        [
            "MFA/IAP authentication and least-privilege roles: author, reviewer, publisher and administrator.",
            "Optimistic locking to prevent one editor overwriting another.",
            "Before/after values, actor, reason, timestamp, review result and release ID in the audit log.",
            "No hard deletion of published knowledge; retire or quarantine it.",
            "Emergency kill switches for a method, rule, recipe, release or the entire generator.",
        ],
    )


def add_validation_delivery(doc: Document) -> None:
    doc.add_heading("18. Validation, implementation order and definition of done", level=1)
    doc.add_heading("18.1 Validation layers", level=2)
    add_table(
        doc,
        ["Layer", "Must prove"],
        [
            ["Schema", "Types, bounds, enums, versions, unique codes and foreign keys are valid"],
            ["Knowledge", "Evidence links resolve; effect count limits hold; no draft or quarantined content is generator eligible"],
            ["Relations", "No cycles where prohibited; substitutions preserve objective; progression prerequisites resolve"],
            ["Program", "Phase and weekly objectives match goal, event, horizon and competition calendar"],
            ["Schedule", "Sessions fit available days/duration and respect hard/easy, competition and external-load spacing"],
            ["Prescription", "Every item is in range for method, quality, phase and level; recovery and volume are complete"],
            ["Safety", "Pain/restriction conflicts, high-impact exposure, supervision and prohibited combinations are handled"],
            ["Presentation", "Every athlete-visible field is actionable, consistent and backed by the stored plan"],
            ["Adaptation", "Changes are bounded, attributable and do not silently rewrite completed history"],
            ["Reproducibility", "Accepted AI output and every input/content/model/prompt/schema/validator version are stored; retries are idempotent"],
        ],
        [1900, 7460],
        font_size=8.9,
    )
    doc.add_heading("18.2 Ordered implementation", level=2)
    add_numbered(
        doc,
        [
            "Lock the canonical taxonomies, lifecycle states, identifier rules and release model.",
            "Create local PostgreSQL/PostGIS migrations for governance, taxonomy and method layers.",
            "Implement Admin Studio draft/edit/validate/review/publish APIs before bulk content authoring.",
            "Create the reviewed exercise/drill/modality catalogue using the canonical method template.",
            "Complete the Running evidence package and event-specific demand profiles.",
            "Implement prescription rules and program/session recipe schemas; author Running content only after their validation contracts exist.",
            "Build the constrained-AI planner from deterministic eligibility and candidate projection → AI selection/composition → deterministic validation → audited persistence.",
            "Implement athlete onboarding v3 and feedback/adaptation contracts.",
            "Validate golden Running scenarios locally, then deploy the same migrations and code to GCP staging.",
            "Provision production only after staging, security, rollback and reproducibility gates pass.",
            "Expand one sport at a time through the same research, review, rules, recipes and validation gates.",
        ],
    )
    doc.add_heading("18.3 Definition of done", level=2)
    add_bullets(
        doc,
        [
            "The database contains no ambiguous or duplicate canonical concepts.",
            "Every approved method has one primary effect, no more than three secondary effects, complete costs, eligibility and structured relations.",
            "Every demand fact has context, evidence, confidence and a permitted planning implication.",
            "Every rule is executable, bounded, evidence-scoped and testable.",
            "Every recipe can be filled for its intended athlete profiles or fails explicitly with a reason.",
            "Every generated plan records its complete decision and version lineage.",
            "Admin publication, rollback, cache invalidation and audit trails are tested.",
            "No AI-generated value can bypass deterministic validation.",
            "No production release occurs until all representative athlete scenarios pass.",
        ],
    )


def add_appendices(doc: Document) -> None:
    doc.add_page_break()
    doc.add_heading("Appendix A — Planner decision equation", level=1)
    add_callout(
        doc,
        "Runlete strategy",
        "Sport demands determine quality priorities. Goals and phases determine the required adaptation. "
        "Templates determine session structure. Rules determine dosage and progression. Athlete constraints determine eligibility. "
        "Exercises, drills and protocols supply the training methods. AI selects and composes from the approved candidate set. Deterministic validation decides whether the result is usable.",
        LIGHT_TEAL,
    )
    doc.add_heading("Appendix B — Compact generator-selection projection", level=1)
    add_label_detail(
        doc,
        [
            ("Identity", "method_id, stable_code, content_version"),
            ("Objective", "primary_effect, up to three secondary_effects, permitted_training_roles"),
            ("Classification", "primary_pattern, force_direction, contraction_emphasis, velocity_class, laterality, execution_formats"),
            ("Eligibility", "level, environment, equipment alternatives, prerequisites and active constraints"),
            ("Costs", "technical, fatigue, impact, setup and supervision"),
            ("Relations", "eligible regressions, progressions and substitutions for the current objective"),
            ("Governance", "generator_eligible, published_release_id and evidence/review status"),
        ],
    )
    doc.add_paragraph(
        "Full instructions, errors, media and evidence are loaded only after selection or when required for display/validation. "
        "This prevents token-heavy retrieval and keeps the constrained AI selector grounded in only relevant, released options."
    )

    doc.add_heading("Appendix C — Blueprint decisions that require later content work", level=1)
    add_bullets(
        doc,
        [
            "This blueprint does not approve the previous 614 movement candidates or define the final catalogue size.",
            "It does not contain sport-specific programs, templates or prescription values.",
            "It does not complete the Running evidence package or approve sprint/endurance rules.",
            "It does not replace qualified S&C, physiotherapy or specialist review of production content.",
            "It does define the exact structure those later deliverables must satisfy.",
        ],
    )

    doc.add_heading("Appendix D — Source basis", level=1)
    doc.add_paragraph(
        "This blueprint consolidates the agreed Runlete product decisions, the Task 1 current-state audit, the exercise-library audit, "
        "the current generator data-flow analysis, the Running gap report, the PostgreSQL rebuild decision and the Admin Studio publishing model. "
        "Prototype records remain candidate research material and are not treated as approved scientific content."
    )


def finalize_fonts(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if run.font.name is None:
                set_font(run)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if run.font.name is None:
                            set_font(run)


def build() -> Path:
    doc = Document()
    configure_document(doc)
    add_cover(doc)
    add_contents(doc)
    add_product_contract(doc)
    add_system_flow(doc)
    add_five_layers(doc)
    add_demand_model(doc)
    add_special_demand_patterns(doc)
    add_quality_taxonomy(doc)
    add_method_schema(doc)
    add_tags_and_retrieval(doc)
    add_method_relationships(doc)
    add_exercise_examples(doc)
    add_prescription_model(doc)
    add_template_model(doc)
    add_athlete_inputs(doc)
    add_output_contract(doc)
    add_ai_boundary(doc)
    add_database_architecture(doc)
    add_admin_governance(doc)
    add_validation_delivery(doc)
    add_appendices(doc)
    finalize_fonts(doc)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
