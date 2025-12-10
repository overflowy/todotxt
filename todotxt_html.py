#!/usr/bin/env python3
"""
todotxt-html.py - Generate a beautiful HTML dashboard from todo.txt files

Usage:
    python todotxt-html.py [directory]

If no directory is specified, uses the current directory.
Generates an HTML dashboard and opens it in your default browser.
"""

import argparse
import os
import re
import tempfile
import webbrowser
from collections import Counter, defaultdict, namedtuple
from datetime import date, datetime, timedelta

# ============================================================================
# DATA STRUCTURES
# ============================================================================


Task = namedtuple(
    "Task",
    [
        "raw_line",
        "is_completed",
        "completion_date",
        "priority",
        "creation_date",
        "description",
        "contexts",
        "projects",
        "due_date",
        "source_file",
    ],
)


# ============================================================================
# REGEX PATTERNS (from todotxt_commands.py patterns)
# ============================================================================

COMPLETED_PATTERN = re.compile(r"^x\s+(\d{4}-\d{2}-\d{2})\s+")
COMPLETED_WITH_CREATION_PATTERN = re.compile(r"^x\s+\d{4}-\d{2}-\d{2}\s+(\d{4}-\d{2}-\d{2})\s+")
PRIORITY_PATTERN = re.compile(r"^(?:x\s+\d{4}-\d{2}-\d{2}\s+)?\(([A-Z])\)\s+")
CONTEXT_PATTERN = re.compile(r"(?:^|\s)@(\S+)")
PROJECT_PATTERN = re.compile(r"(?:^|\s)\+(\S+)")
DUE_DATE_PATTERN = re.compile(r"\bdue:(\d{4}-\d{2}-\d{2})\b")
CREATION_DATE_PATTERNS = [
    re.compile(r"^x\s+\d{4}-\d{2}-\d{2}\s+(\d{4}-\d{2}-\d{2})\s+"),  # Completed with creation
    re.compile(r"^\([A-Z]\)\s+(\d{4}-\d{2}-\d{2})\s+"),  # With priority
    re.compile(r"^(\d{4}-\d{2}-\d{2})\s+"),  # Without priority
]


# ============================================================================
# PARSER FUNCTIONS
# ============================================================================


def parse_date(date_str):
    """Safely parse a YYYY-MM-DD date string"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def parse_task(line, source_file):
    """Parse a single line into a Task object"""
    line = line.strip()
    if not line:
        return None

    # Check if completed
    is_completed = False
    completion_date = None
    if line.startswith("x "):
        is_completed = True
        match = COMPLETED_PATTERN.match(line)
        if match:
            completion_date = parse_date(match.group(1))

    # Extract priority
    priority = None
    match = PRIORITY_PATTERN.match(line)
    if match:
        priority = match.group(1)

    # Extract creation date
    creation_date = None
    for pattern in CREATION_DATE_PATTERNS:
        match = pattern.match(line)
        if match:
            creation_date = parse_date(match.group(1))
            break

    # Extract contexts (all @tags)
    contexts = CONTEXT_PATTERN.findall(line)

    # Extract projects (all +tags)
    projects = PROJECT_PATTERN.findall(line)

    # Extract due date
    due_date = None
    match = DUE_DATE_PATTERN.search(line)
    if match:
        due_date = parse_date(match.group(1))

    # Extract description (clean up metadata for display)
    description = line
    # Remove completion marker
    if description.startswith("x "):
        description = re.sub(r"^x\s+\d{4}-\d{2}-\d{2}\s+", "", description)
    # Remove priority
    description = re.sub(r"^\([A-Z]\)\s+", "", description)
    # Remove creation date
    description = re.sub(r"^\d{4}-\d{2}-\d{2}\s+", "", description)
    # Remove contexts, projects and due dates
    description = CONTEXT_PATTERN.sub("", description)
    description = PROJECT_PATTERN.sub("", description)
    description = DUE_DATE_PATTERN.sub("", description)
    # Clean up whitespace (double spaces left by removals)
    description = re.sub(r"\s+", " ", description).strip()

    return Task(
        raw_line=line,
        is_completed=is_completed,
        completion_date=completion_date,
        priority=priority,
        creation_date=creation_date,
        description=description,
        contexts=contexts,
        projects=projects,
        due_date=due_date,
        source_file=source_file,
    )


def parse_file(filepath):
    """Parse all tasks from a file"""
    if not os.path.exists(filepath):
        return []

    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                task = parse_task(line, os.path.basename(filepath))
                if task:
                    tasks.append(task)
    except Exception as e:
        print("Warning: Could not read {0}: {1}".format(filepath, e))

    return tasks


def load_all_tasks(directory):
    """Load tasks from all four files"""
    files = ["todo.txt", "done.txt", "waiting.txt", "someday.txt"]
    result = {}

    for filename in files:
        filepath = os.path.join(directory, filename)
        result[filename] = parse_file(filepath)

    return result


# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================


def count_by_priority(tasks):
    """Count tasks by priority"""
    counter = Counter()
    for task in tasks:
        priority = task.priority if task.priority else "None"
        counter[priority] += 1
    return counter


def count_by_context(tasks):
    """Count tasks by context tag"""
    counter = Counter()
    for task in tasks:
        for context in task.contexts:
            counter[context] += 1
    return counter


def count_by_project(tasks):
    """Count tasks by project tag"""
    counter = Counter()
    for task in tasks:
        for project in task.projects:
            counter[project] += 1
    return counter


def analyze_due_dates(tasks, today):
    """Categorize tasks by due date"""
    result = {"overdue": [], "today": [], "this_week": [], "upcoming": [], "no_due_date": []}

    week_from_now = today + timedelta(days=7)

    for task in tasks:
        if task.due_date is None:
            result["no_due_date"].append(task)
        elif task.due_date < today:
            result["overdue"].append(task)
        elif task.due_date == today:
            result["today"].append(task)
        elif task.due_date <= week_from_now:
            result["this_week"].append(task)
        else:
            result["upcoming"].append(task)

    return result


def analyze_completion_trends(completed_tasks, days=14):
    """Group completed tasks by completion date for the last N days"""
    result = defaultdict(int)
    today = date.today()

    for task in completed_tasks:
        if task.completion_date:
            # Only include tasks completed in the last N days
            if (today - task.completion_date).days <= days:
                result[task.completion_date] += 1

    # Fill in missing dates with 0
    for i in range(days + 1):
        day = today - timedelta(days=i)
        if day not in result:
            result[day] = 0

    # Sort reverse=True so Today is first (Left side of chart)
    return dict(sorted(result.items(), reverse=True))


def analyze_task_age(tasks, today):
    """Analyze age of tasks based on creation date"""
    result = {"today": 0, "this_week": 0, "this_month": 0, "older": 0, "no_date": 0}

    for task in tasks:
        if task.creation_date is None:
            result["no_date"] += 1
        else:
            age_days = (today - task.creation_date).days
            if age_days == 0:
                result["today"] += 1
            elif age_days <= 7:
                result["this_week"] += 1
            elif age_days <= 30:
                result["this_month"] += 1
            else:
                result["older"] += 1

    return result


def analyze_monthly_completions(completed_tasks, months=6):
    """Analyze completed tasks by month for the last N months"""
    today = date.today()
    result = {}

    # Generate the last N months
    for i in range(months):
        # Calculate the month
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_key = date(year, month, 1)
        result[month_key] = {"completed": 0, "created": 0}

    # Count completions per month
    for task in completed_tasks:
        if task.completion_date:
            month_key = date(task.completion_date.year, task.completion_date.month, 1)
            if month_key in result:
                result[month_key]["completed"] += 1

    # Count creations per month (from all tasks that have creation dates)
    for task in completed_tasks:
        if task.creation_date:
            month_key = date(task.creation_date.year, task.creation_date.month, 1)
            if month_key in result:
                result[month_key]["created"] += 1

    return dict(sorted(result.items()))


def calculate_statistics(tasks_by_file):
    """Calculate all statistics"""
    today = date.today()

    # Collect all tasks from all files
    all_tasks = []
    for tasks in tasks_by_file.values():
        all_tasks.extend(tasks)

    # Separate active and completed tasks (regardless of which file they're in)
    completed_tasks = [t for t in all_tasks if t.is_completed]
    active_tasks = [t for t in all_tasks if not t.is_completed]

    return {
        "overview": {filename: len(tasks) for filename, tasks in tasks_by_file.items()},
        "total_active": len(active_tasks),
        "total_completed": len(completed_tasks),
        "priority_distribution": count_by_priority(active_tasks),
        "context_breakdown": count_by_context(active_tasks),
        "project_breakdown": count_by_project(active_tasks),
        "project_breakdown_completed": count_by_project(completed_tasks),
        "due_date_analysis": analyze_due_dates(active_tasks, today),
        "completion_trends": analyze_completion_trends(completed_tasks),
        "task_age": analyze_task_age(active_tasks, today),
        "monthly_overview": analyze_monthly_completions(completed_tasks),
        "generated_at": datetime.now(),
        "all_tasks": all_tasks,
    }


def tasks_to_json(tasks):
    """Convert tasks to JSON for frontend use"""
    import json

    task_list = []
    for task in tasks:
        task_list.append(
            {
                "description": task.description,
                "raw": task.raw_line,
                "completed": task.is_completed,
                "priority": task.priority,
                "contexts": task.contexts,
                "projects": task.projects,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "creation_date": task.creation_date.isoformat() if task.creation_date else None,
                "completion_date": task.completion_date.isoformat()
                if task.completion_date
                else None,
                "source": task.source_file,
            }
        )
    return json.dumps(task_list)


# ============================================================================
# HTML GENERATION
# ============================================================================


def generate_css() -> str:
    """Generate embedded CSS styles - Data Observatory aesthetic"""
    return """
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Geist+Mono:wght@400;500;600&family=Geist:wght@300;400;500;600;700&display=swap');

:root {
    --bg-void: #09090b;
    --bg-primary: #0c0c0f;
    --bg-elevated: #141418;
    --bg-card: #1a1a1f;
    --bg-hover: #222228;
    --text-primary: #fafafa;
    --text-secondary: #71717a;
    --text-muted: #52525b;
    --accent-ember: #f59e0b;
    --accent-ember-glow: rgba(245, 158, 11, 0.15);
    --accent-cyan: #22d3ee;
    --accent-cyan-glow: rgba(34, 211, 238, 0.12);
    --accent-rose: #fb7185;
    --accent-rose-glow: rgba(251, 113, 133, 0.15);
    --accent-emerald: #34d399;
    --accent-emerald-glow: rgba(52, 211, 153, 0.12);
    --accent-violet: #a78bfa;
    --accent-violet-glow: rgba(167, 139, 250, 0.15);
    --border-subtle: rgba(255, 255, 255, 0.06);
    --border-accent: rgba(255, 255, 255, 0.1);
    --glass: rgba(26, 26, 31, 0.7);
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
    --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.6);
    --shadow-glow: 0 0 60px rgba(245, 158, 11, 0.08);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-void);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}

/* Ambient background effect */
body::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(245, 158, 11, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(34, 211, 238, 0.02) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(167, 139, 250, 0.015) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

/* Noise texture overlay */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.015;
    pointer-events: none;
    z-index: 1;
}

.dashboard {
    position: relative;
    z-index: 2;
    max-width: 1440px;
    margin: 0 auto;
    padding: 3rem 2rem 4rem;
}

/* Header */
.header {
    text-align: center;
    margin-bottom: 4rem;
    animation: fadeUp 0.8s ease-out;
}

.header h1 {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 3.5rem;
    font-weight: 400;
    letter-spacing: -0.02em;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header .subtitle {
    font-family: 'Geist Mono', monospace;
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
}

.header .timestamp {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin-top: 0.5rem;
}

/* Stat Cards Grid */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 3rem;
}

.card {
    position: relative;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.75rem;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    animation: fadeUp 0.6s ease-out backwards;
}

.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.15s; }
.card:nth-child(3) { animation-delay: 0.2s; }
.card:nth-child(4) { animation-delay: 0.25s; }

.card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.02) 100%);
    opacity: 0;
    transition: opacity 0.4s ease;
}

.card:hover {
    transform: translateY(-4px);
    border-color: var(--border-accent);
    box-shadow: var(--shadow-lg);
}

.card:hover::before {
    opacity: 1;
}

.card-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
    font-size: 1.25rem;
}

.card-value {
    font-family: 'Geist Mono', monospace;
    font-size: 2.75rem;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 0.5rem;
    transition: transform 0.3s ease;
}

.card:hover .card-value {
    transform: scale(1.02);
}

.card-label {
    font-family: 'Geist Mono', monospace;
    color: var(--text-muted);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
}

.card-context {
    position: absolute;
    bottom: -100%;
    left: 0;
    right: 0;
    padding: 1rem 1.75rem;
    background: var(--bg-hover);
    border-top: 1px solid var(--border-subtle);
    font-size: 0.8125rem;
    color: var(--text-secondary);
    transition: bottom 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.card:hover .card-context {
    bottom: 0;
}

/* Card variants */
.card.active .card-icon { background: var(--accent-cyan-glow); color: var(--accent-cyan); }
.card.active .card-value { color: var(--accent-cyan); }

.card.success .card-icon { background: var(--accent-emerald-glow); color: var(--accent-emerald); }
.card.success .card-value { color: var(--accent-emerald); }

.card.danger .card-icon { background: var(--accent-rose-glow); color: var(--accent-rose); }
.card.danger .card-value { color: var(--accent-rose); }

.card.warning .card-icon { background: var(--accent-ember-glow); color: var(--accent-ember); }
.card.warning .card-value { color: var(--accent-ember); }

/* Sections */
.section {
    position: relative;
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    overflow: visible;
    animation: fadeUp 0.6s ease-out backwards;
}

.section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
}

.section-title {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.5rem;
    font-weight: 400;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.section-title .icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-ember-glow);
    color: var(--accent-ember);
}

.section-title .icon svg {
    width: 18px;
    height: 18px;
    stroke-width: 2;
}

/* Card icons */
.card-icon svg {
    width: 22px;
    height: 22px;
    stroke-width: 2;
}

/* Empty state icons */
.empty-state svg {
    width: 32px;
    height: 32px;
    stroke-width: 1.5;
    opacity: 0.5;
    margin-bottom: 1rem;
}

.section-badge {
    font-family: 'Geist Mono', monospace;
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 0.375rem 0.75rem;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 6px;
    color: var(--text-muted);
}

/* Due Date Timeline */
.timeline {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
}

.timeline-item {
    position: relative;
    text-align: center;
    padding: 2rem 1rem;
    border-radius: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    overflow: hidden;
}

.timeline-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 40%;
    height: 3px;
    border-radius: 0 0 3px 3px;
    transition: all 0.3s ease;
}

.timeline-item:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: var(--shadow-lg);
}

.timeline-count {
    font-family: 'Geist Mono', monospace;
    font-size: 2.5rem;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 0.75rem;
}

.timeline-label {
    font-family: 'Geist Mono', monospace;
    font-size: 0.625rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.5rem;
}

.timeline-hint {
    font-size: 0.75rem;
    color: var(--text-secondary);
    opacity: 0;
    transform: translateY(8px);
    transition: all 0.3s ease;
}

.timeline-item:hover .timeline-hint {
    opacity: 1;
    transform: translateY(0);
}

/* Timeline variants */
.timeline-item.overdue::before { background: var(--accent-rose); box-shadow: 0 0 20px var(--accent-rose-glow); }
.timeline-item.overdue .timeline-count { color: var(--accent-rose); }
.timeline-item.overdue:hover { border-color: rgba(251, 113, 133, 0.3); background: linear-gradient(to bottom, rgba(251, 113, 133, 0.08), transparent); }

.timeline-item.today::before { background: var(--accent-ember); box-shadow: 0 0 20px var(--accent-ember-glow); }
.timeline-item.today .timeline-count { color: var(--accent-ember); }
.timeline-item.today:hover { border-color: rgba(245, 158, 11, 0.3); background: linear-gradient(to bottom, rgba(245, 158, 11, 0.08), transparent); }

.timeline-item.week::before { background: var(--accent-cyan); box-shadow: 0 0 20px var(--accent-cyan-glow); }
.timeline-item.week .timeline-count { color: var(--accent-cyan); }
.timeline-item.week:hover { border-color: rgba(34, 211, 238, 0.3); background: linear-gradient(to bottom, rgba(34, 211, 238, 0.08), transparent); }

.timeline-item.upcoming::before { background: var(--accent-emerald); box-shadow: 0 0 20px var(--accent-emerald-glow); }
.timeline-item.upcoming .timeline-count { color: var(--accent-emerald); }
.timeline-item.upcoming:hover { border-color: rgba(52, 211, 153, 0.3); background: linear-gradient(to bottom, rgba(52, 211, 153, 0.08), transparent); }

.timeline-item.none::before { background: var(--text-muted); }
.timeline-item.none .timeline-count { color: var(--text-muted); }

/* Bar Charts */
.bar-chart {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.bar-row {
    position: relative; /* Ensure tooltips are relative to the row, but see z-index */
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    border-radius: 10px;
    transition: background 0.3s ease;
    cursor: pointer;
}

.bar-row:hover {
    background: var(--bg-card);
    z-index: 10; /* Bring to front on hover */
}

.bar-label {
    min-width: 90px;
    font-family: 'Geist Mono', monospace;
    font-weight: 500;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.bar-label .priority-badge {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.bar-container {
    flex: 1;
    height: 36px;
    background: var(--bg-card);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
}

.bar-fill {
    height: 100%;
    border-radius: 8px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 1rem;
    animation: barGrow 1s cubic-bezier(0.16, 1, 0.3, 1) backwards;
    overflow: hidden;
}

.bar-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%);
    animation: shimmer 2s infinite;
}

.bar-fill-text {
    position: relative;
    z-index: 1;
    font-family: 'Geist Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--bg-void);
    opacity: 0.9;
}

.bar-count {
    min-width: 50px;
    text-align: right;
    font-family: 'Geist Mono', monospace;
    font-weight: 600;
    font-size: 1rem;
}

.bar-tooltip {
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%) scale(0.9);
    background: var(--bg-card);
    border: 1px solid var(--border-accent);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.8125rem;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: var(--shadow-lg);
    z-index: 100;
}

.bar-row:hover .bar-tooltip {
    opacity: 1;
    transform: translateX(-50%) scale(1);
}

/* Priority colors */
.priority-a .bar-fill { background: linear-gradient(90deg, var(--accent-rose) 0%, #f43f5e 100%); }
.priority-a .bar-label .priority-badge { background: var(--accent-rose); box-shadow: 0 0 8px var(--accent-rose-glow); }
.priority-b .bar-fill { background: linear-gradient(90deg, var(--accent-ember) 0%, #f97316 100%); }
.priority-b .bar-label .priority-badge { background: var(--accent-ember); box-shadow: 0 0 8px var(--accent-ember-glow); }
.priority-c .bar-fill { background: linear-gradient(90deg, var(--accent-cyan) 0%, #06b6d4 100%); }
.priority-c .bar-label .priority-badge { background: var(--accent-cyan); box-shadow: 0 0 8px var(--accent-cyan-glow); }
.priority-none .bar-fill { background: linear-gradient(90deg, var(--text-muted) 0%, #6b7280 100%); }
.priority-none .bar-label .priority-badge { background: var(--text-muted); }

/* Age colors */
.age-today .bar-fill { background: linear-gradient(90deg, var(--accent-emerald) 0%, #10b981 100%); }
.age-week .bar-fill { background: linear-gradient(90deg, var(--accent-cyan) 0%, #06b6d4 100%); }
.age-month .bar-fill { background: linear-gradient(90deg, var(--accent-ember) 0%, #f97316 100%); }
.age-older .bar-fill { background: linear-gradient(90deg, var(--accent-rose) 0%, #f43f5e 100%); }
.age-nodate .bar-fill { background: linear-gradient(90deg, var(--text-muted) 0%, #6b7280 100%); }

/* Tag Cloud */
.tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    padding-top: 0.5rem;
}

.tag {
    position: relative;
    padding: 0.625rem 1.25rem;
    border-radius: 100px;
    font-family: 'Geist Mono', monospace;
    font-size: 0.8125rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    animation: fadeUp 0.5s ease-out backwards;
}

.tag:hover {
    transform: translateY(-3px) scale(1.03);
}

.tag-context {
    background: var(--accent-cyan-glow);
    color: var(--accent-cyan);
    border: 1px solid rgba(34, 211, 238, 0.2);
}

.tag-context:hover {
    background: rgba(34, 211, 238, 0.2);
    border-color: rgba(34, 211, 238, 0.4);
    box-shadow: 0 4px 20px var(--accent-cyan-glow);
}

.tag-project {
    background: var(--accent-violet-glow);
    color: var(--accent-violet);
    border: 1px solid rgba(167, 139, 250, 0.2);
}

.tag-project:hover {
    background: rgba(167, 139, 250, 0.2);
    border-color: rgba(167, 139, 250, 0.4);
    box-shadow: 0 4px 20px var(--accent-violet-glow);
}

.tag-count {
    background: rgba(255, 255, 255, 0.15);
    padding: 0.125rem 0.5rem;
    border-radius: 100px;
    font-size: 0.6875rem;
    font-weight: 600;
}

.tag-tooltip {
    position: absolute;
    bottom: calc(100% + 10px);
    left: 50%;
    transform: translateX(-50%) scale(0.9);
    background: var(--bg-card);
    border: 1px solid var(--border-accent);
    border-radius: 10px;
    padding: 0.875rem 1.25rem;
    font-size: 0.8125rem;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: var(--shadow-lg);
    z-index: 100;
    color: var(--text-primary);
}

.tag:hover .tag-tooltip {
    opacity: 1;
    transform: translateX(-50%) scale(1);
}

/* Completion Trend Chart */
.trend-chart {
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 200px;
    padding: 1.5rem 0.5rem 2.5rem;
    position: relative;
}

.trend-chart::before {
    content: '';
    position: absolute;
    bottom: 2.5rem;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--border-subtle);
}

.trend-bar-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    position: relative;
}

.trend-bar-wrapper {
    width: 100%;
    height: 140px;
    display: flex;
    align-items: flex-end;
    position: relative;
}

.trend-bar {
    width: 100%;
    background: linear-gradient(180deg, var(--accent-emerald) 0%, rgba(52, 211, 153, 0.6) 100%);
    border-radius: 6px 6px 0 0;
    min-height: 4px;
    position: relative;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    animation: barGrow 1s cubic-bezier(0.16, 1, 0.3, 1) backwards;
}

.trend-bar::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255,255,255,0.2) 0%, transparent 50%);
    border-radius: inherit;
}

.trend-bar:hover {
    transform: scaleY(1.05);
    filter: brightness(1.15);
    box-shadow: 0 -8px 24px var(--accent-emerald-glow);
    z-index: 10;
}

.trend-bar-tooltip {
    position: absolute;
    bottom: calc(100% + 12px);
    left: 50%;
    transform: translateX(-50%) scale(0.9);
    background: var(--bg-card);
    border: 1px solid var(--border-accent);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-family: 'Geist Mono', monospace;
    font-size: 0.8125rem;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: var(--shadow-lg);
    z-index: 100;
}

.trend-bar:hover .trend-bar-tooltip {
    opacity: 1;
    transform: translateX(-50%) scale(1);
}

.trend-bar-count {
    color: var(--accent-emerald);
    font-weight: 600;
}

.trend-date {
    font-family: 'Geist Mono', monospace;
    font-size: 0.625rem;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    white-space: nowrap;
}

/* Monthly Overview */
.monthly-chart {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 1rem;
}

.month-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.month-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan));
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.3s ease;
}

.month-card:hover {
    transform: translateY(-4px);
    border-color: var(--border-accent);
    box-shadow: var(--shadow-lg);
}

.month-card:hover::before {
    transform: scaleX(1);
}

.month-name {
    font-family: 'Geist Mono', monospace;
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}

.month-value {
    font-family: 'Geist Mono', monospace;
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--accent-emerald);
    line-height: 1;
    margin-bottom: 0.5rem;
}

.month-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.month-bar-container {
    margin-top: 1rem;
    height: 6px;
    background: var(--bg-elevated);
    border-radius: 3px;
    overflow: hidden;
}

.month-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan));
    border-radius: 3px;
    transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.monthly-summary {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-subtle);
}

.summary-item {
    text-align: center;
}

.summary-value {
    font-family: 'Geist Mono', monospace;
    font-size: 1.75rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
}

.summary-value.total {
    color: var(--accent-emerald);
}

.summary-value.average {
    color: var(--accent-cyan);
}

.summary-value.best {
    color: var(--accent-ember);
}

.summary-label {
    font-family: 'Geist Mono', monospace;
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
}

@media (max-width: 1024px) {
    .monthly-chart {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 640px) {
    .monthly-chart {
        grid-template-columns: repeat(2, 1fr);
    }

    .monthly-summary {
        flex-direction: column;
        gap: 1rem;
    }
}

/* Grid layouts */
.grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-muted);
    font-style: italic;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

/* Modal */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-overlay.active {
    opacity: 1;
    visibility: visible;
}

.modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0.95);
    width: 90%;
    max-width: 700px;
    max-height: 80vh;
    background: var(--bg-elevated);
    border: 1px solid var(--border-accent);
    border-radius: 20px;
    z-index: 1001;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6);
}

.modal-overlay.active + .modal,
.modal.active {
    opacity: 1;
    visibility: visible;
    transform: translate(-50%, -50%) scale(1);
}

.modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 2rem;
    border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
    font-family: 'Instrument Serif', Georgia, serif;
    font-size: 1.5rem;
    font-weight: 400;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.modal-title .badge {
    font-family: 'Geist Mono', monospace;
    font-size: 0.75rem;
    padding: 0.25rem 0.625rem;
    background: var(--accent-ember-glow);
    color: var(--accent-ember);
    border-radius: 100px;
}

.modal-close {
    width: 36px;
    height: 36px;
    border: none;
    background: var(--bg-card);
    border-radius: 10px;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.modal-close:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.modal-close svg {
    width: 18px;
    height: 18px;
}

.modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 0;
}

.modal-body::-webkit-scrollbar {
    width: 8px;
}

.modal-body::-webkit-scrollbar-track {
    background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
    background: var(--border-accent);
    border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* Task list */
.task-list {
    list-style: none;
}

.task-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 2rem;
    border-bottom: 1px solid var(--border-subtle);
    transition: background 0.2s ease;
}

.task-item:last-child {
    border-bottom: none;
}

.task-item:hover {
    background: var(--bg-card);
}

.task-checkbox {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border-accent);
    border-radius: 6px;
    flex-shrink: 0;
    margin-top: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.task-item.completed .task-checkbox {
    background: var(--accent-emerald);
    border-color: var(--accent-emerald);
}

.task-item.completed .task-checkbox svg {
    width: 12px;
    height: 12px;
    color: var(--bg-void);
}

.task-content {
    flex: 1;
    min-width: 0;
}

.task-description {
    font-size: 0.9375rem;
    line-height: 1.5;
    margin-bottom: 0.5rem;
    word-wrap: break-word;
}

.task-item.completed .task-description {
    color: gray;
}

.task-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-family: 'Geist Mono', monospace;
    font-size: 0.6875rem;
}

.task-meta-item {
    padding: 0.1875rem 0.5rem;
    border-radius: 4px;
    background: var(--bg-card);
    color: var(--text-muted);
}

.task-meta-item.priority {
    font-weight: 600;
}

.task-meta-item.priority-a {
    background: var(--accent-rose-glow);
    color: var(--accent-rose);
}

.task-meta-item.priority-b {
    background: var(--accent-ember-glow);
    color: var(--accent-ember);
}

.task-meta-item.priority-c {
    background: var(--accent-cyan-glow);
    color: var(--accent-cyan);
}

.task-meta-item.context {
    background: var(--accent-cyan-glow);
    color: var(--accent-cyan);
}

.task-meta-item.project {
    background: var(--accent-violet-glow);
    color: var(--accent-violet);
}

.task-meta-item.due {
    background: var(--accent-ember-glow);
    color: var(--accent-ember);
}

.task-meta-item.due.overdue {
    background: var(--accent-rose-glow);
    color: var(--accent-rose);
}

.task-meta-item.source {
    background: var(--bg-hover);
}

.modal-empty {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-muted);
}

.modal-empty svg {
    width: 48px;
    height: 48px;
    stroke-width: 1;
    opacity: 0.3;
    margin-bottom: 1rem;
}

/* Clickable elements */
.clickable {
    cursor: pointer;
}

.clickable:active {
    transform: scale(0.98);
}

/* Animations */
@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes barGrow {
    from {
        transform: scaleX(0);
        transform-origin: left;
    }
    to {
        transform: scaleX(1);
        transform-origin: left;
    }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}

/* Responsive */
@media (max-width: 1024px) {
    .cards-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .timeline {
        grid-template-columns: repeat(3, 1fr);
    }

    .grid-2 {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .dashboard {
        padding: 1.5rem 1rem 3rem;
    }

    .header h1 {
        font-size: 2.25rem;
    }

    .cards-grid {
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }

    .card {
        padding: 1.25rem;
    }

    .card-value {
        font-size: 2rem;
    }

    .timeline {
        grid-template-columns: repeat(2, 1fr);
    }

    .timeline-item:last-child {
        grid-column: span 2;
    }

    .section {
        padding: 1.5rem;
    }
}

@media (max-width: 480px) {
    .cards-grid {
        grid-template-columns: 1fr;
    }

    .timeline {
        grid-template-columns: 1fr;
    }

    .timeline-item:last-child {
        grid-column: span 1;
    }
}
"""


def generate_overview_cards(stats):
    """Generate overview summary cards with icons and contextual info"""
    total_active = stats["total_active"]
    total_completed = stats["total_completed"]
    due_analysis = stats["due_date_analysis"]
    overdue_count = len(due_analysis["overdue"])
    today_count = len(due_analysis["today"])

    danger_class = " danger" if overdue_count > 0 else ""
    warning_class = " warning" if today_count > 0 else ""
    overdue_context = "Overdue tasks" if overdue_count > 0 else "All caught up!"

    return """
    <div class="cards-grid">
        <div class="card active clickable" data-filter="active" data-title="Active Tasks">
            <div class="card-icon"><i data-lucide="list-todo"></i></div>
            <div class="card-value">{0}</div>
            <div class="card-label">Active Tasks</div>
            <div class="card-context">View active tasks</div>
        </div>
        <div class="card success clickable" data-filter="completed" data-title="Completed Tasks">
            <div class="card-icon"><i data-lucide="circle-check"></i></div>
            <div class="card-value">{1}</div>
            <div class="card-label">Completed</div>
            <div class="card-context">View completed tasks</div>
        </div>
        <div class="card{2} clickable" data-filter="overdue" data-title="Overdue Tasks">
            <div class="card-icon"><i data-lucide="alert-triangle"></i></div>
            <div class="card-value">{3}</div>
            <div class="card-label">Overdue</div>
            <div class="card-context">{4}</div>
        </div>
        <div class="card{5} clickable" data-filter="today" data-title="Due Today">
            <div class="card-icon"><i data-lucide="clock"></i></div>
            <div class="card-value">{6}</div>
            <div class="card-label">Due Today</div>
            <div class="card-context">View tasks due today</div>
        </div>
    </div>
    """.format(
        total_active,
        total_completed,
        danger_class,
        overdue_count,
        overdue_context,
        warning_class,
        today_count,
    )


def generate_priority_chart(stats):
    """Generate priority distribution bar chart with tooltips"""
    priority_dist = stats["priority_distribution"]
    total_active = stats["total_active"]

    if not priority_dist:
        return (
            '<div class="empty-state"><i data-lucide="flag-off"></i>No tasks with priorities</div>'
        )

    # Sort priorities: A, B, C, ..., None
    priorities = sorted([p for p in priority_dist.keys() if p != "None"])
    if "None" in priority_dist:
        priorities.append("None")

    max_count = max(priority_dist.values()) if priority_dist else 1

    priority_descriptions = {
        "A": "Critical priority",
        "B": "Important priority",
        "C": "Normal priority",
        "None": "No priority assigned",
    }

    bars = []
    for i, priority in enumerate(priorities):
        count = priority_dist[priority]
        percentage = (count / max_count * 100) if max_count > 0 else 0
        pct_of_total = round((count / total_active * 100) if total_active > 0 else 0)

        priority_class = "priority-{0}".format(priority.lower())
        priority_label = "({0})".format(priority) if priority != "None" else "None"
        description = priority_descriptions.get(priority, "")
        task_plural = "s" if count != 1 else ""
        delay = i * 0.1

        bars.append(
            """
        <div class="bar-row {0} clickable" style="animation-delay: {1}s" data-filter="priority" data-value="{2}" data-title="Priority {3} Tasks">
            <div class="bar-label"><span class="priority-badge"></span>{4}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {5}%">
                    <span class="bar-fill-text">{6}%</span>
                </div>
            </div>
            <div class="bar-count">{7}</div>
            <div class="bar-tooltip">{8}<br><strong>{9} task{10}</strong></div>
        </div>
        """.format(
                priority_class,
                delay,
                priority,
                priority_label,
                priority_label,
                percentage,
                pct_of_total,
                count,
                description,
                count,
                task_plural,
            )
        )

    return '<div class="bar-chart">{0}</div>'.format("".join(bars))


def generate_tag_cloud(
    items, tag_class, prefix, total_tasks, filter_type=None, elem_id=None, hidden=False
):
    """Generate tag cloud for contexts or projects with tooltips"""

    # Defaults
    if filter_type is None:
        filter_type = tag_class

    wrapper_style = ' style="display:none"' if hidden else ""
    wrapper_id = ' id="{0}"'.format(elem_id) if elem_id else ""

    if not items:
        icon = "at-sign" if tag_class == "context" else "folder"
        return '<div class="empty-state"{0}{1}><i data-lucide="{2}"></i>No {3}s found</div>'.format(
            wrapper_id, wrapper_style, icon, tag_class
        )

    # Sort by count descending, then alphabetically
    sorted_items = sorted(items.items(), key=lambda x: (-x[1], x[0]))

    tags = []
    for i, (name, count) in enumerate(sorted_items[:20]):  # Limit to top 20
        pct = round((count / total_tasks * 100) if total_tasks > 0 else 0)
        task_plural = "s" if count != 1 else ""

        # Adjust tooltip text based on if we are looking at completed or active
        state_text = "completed" if "completed" in filter_type else "active"
        tooltip_text = "{0} {1} task{2} ({3}%)".format(count, state_text, task_plural, pct)
        delay = i * 0.05

        tags.append(
            """
        <div class="tag tag-{0} clickable" style="animation-delay: {1}s" data-filter="{2}" data-value="{3}" data-title="{4}{5}">
            {6}{7}
            <span class="tag-count">{8}</span>
            <div class="tag-tooltip">{9}</div>
        </div>
        """.format(
                tag_class,
                delay,
                filter_type,
                name,
                prefix,
                name,
                prefix,
                name,
                count,
                tooltip_text,
            )
        )

    return '<div class="tag-cloud"{0}{1}>{2}</div>'.format(wrapper_id, wrapper_style, "".join(tags))


def generate_due_date_timeline(stats):
    """Generate due date timeline with hover hints"""
    due_analysis = stats["due_date_analysis"]

    items = [
        ("overdue", "Overdue", len(due_analysis["overdue"]), "overdue", "Overdue Tasks"),
        ("today", "Due Today", len(due_analysis["today"]), "today", "Due Today"),
        ("week", "This Week", len(due_analysis["this_week"]), "week", "Due This Week"),
        ("upcoming", "Upcoming", len(due_analysis["upcoming"]), "upcoming", "Upcoming Tasks"),
        ("none", "No Due Date", len(due_analysis["no_due_date"]), "no-due", "No Due Date"),
    ]

    timeline_items = []
    for css_class, label, count, filter_type, title in items:
        timeline_items.append(
            """
        <div class="timeline-item {0} clickable" data-filter="{1}" data-title="{2}">
            <div class="timeline-count">{3}</div>
            <div class="timeline-label">{4}</div>
        </div>
        """.format(css_class, filter_type, title, count, label)
        )

    return '<div class="timeline">{0}</div>'.format("".join(timeline_items))


def generate_completion_chart(stats):
    """Generate completion trends chart with tooltips"""
    trends = stats["completion_trends"]

    if not trends:
        return '<div class="empty-state"><i data-lucide="bar-chart-3"></i>No completion data available</div>'

    max_count = max(trends.values()) if trends else 1

    bars = []
    # trends is sorted Today -> Past due to analyze_completion_trends change
    for i, (task_date, count) in enumerate(trends.items()):
        height_percent = (count / max_count * 100) if max_count > 0 else 0
        # Ensure minimum visible height for days with completions
        display_height = max(height_percent, 4) if count > 0 else 4
        date_str = task_date.strftime("%d/%m")  # Requested DD/MM format
        iso_date = task_date.isoformat()
        day_name = task_date.strftime("%a")
        full_date = task_date.strftime("%B %d, %Y")

        task_plural = "s" if count != 1 else ""
        delay = i * 0.05

        bars.append(
            """
        <div class="trend-bar-container">
            <div class="trend-bar-wrapper">
                <div class="trend-bar clickable" style="height: {0}%; animation-delay: {1}s" data-filter="completion-date" data-value="{2}" data-title="Completed on {3}">
                    <div class="trend-bar-tooltip">
                        <div>{4}</div>
                        <div><span class="trend-bar-count">{5}</span> task{6} completed</div>
                    </div>
                </div>
            </div>
            <div class="trend-date">{7}<br>{8}</div>
        </div>
        """.format(
                display_height,
                delay,
                iso_date,
                full_date,
                full_date,
                count,
                task_plural,
                day_name,
                date_str,
            )
        )

    return '<div class="trend-chart">{0}</div>'.format("".join(bars))


def generate_monthly_overview(stats):
    """Generate monthly overview chart for the last 6 months"""
    monthly_data = stats["monthly_overview"]

    if not monthly_data:
        return (
            '<div class="empty-state"><i data-lucide="calendar"></i>No monthly data available</div>'
        )

    # Calculate stats
    values = [m["completed"] for m in monthly_data.values()]
    total_completed = sum(values)
    avg_completed = round(total_completed / len(values)) if values else 0
    best_month = max(values) if values else 0
    max_value = max(values) if values else 1

    month_cards = []
    for i, (month_date, data) in enumerate(monthly_data.items()):
        month_name = month_date.strftime("%b %Y")
        completed = data["completed"]
        bar_width = (completed / max_value * 100) if max_value > 0 else 0
        delay = 0.1 + i * 0.08

        month_cards.append(
            """
        <div class="month-card" style="animation: fadeUp 0.5s ease-out {0}s backwards">
            <div class="month-name">{1}</div>
            <div class="month-value">{2}</div>
            <div class="month-label">completed</div>
            <div class="month-bar-container">
                <div class="month-bar" style="width: {3}%"></div>
            </div>
        </div>
        """.format(delay, month_name, completed, bar_width)
        )

    return """
    <div class="monthly-chart">{0}</div>
    <div class="monthly-summary">
        <div class="summary-item">
            <div class="summary-value total">{1}</div>
            <div class="summary-label">Total Completed</div>
        </div>
        <div class="summary-item">
            <div class="summary-value average">{2}</div>
            <div class="summary-label">Monthly Average</div>
        </div>
        <div class="summary-item">
            <div class="summary-value best">{3}</div>
            <div class="summary-label">Best Month</div>
        </div>
    </div>
    """.format("".join(month_cards), total_completed, avg_completed, best_month)


def generate_task_age_section(stats):
    """Generate task age analysis with tooltips"""
    age = stats["task_age"]
    total_active = stats["total_active"]

    items = [
        ("age-today", "Today", age["today"], "Created today - fresh tasks", "Created Today"),
        ("age-week", "This Week", age["this_week"], "Created 1-7 days ago", "Created This Week"),
        (
            "age-month",
            "This Month",
            age["this_month"],
            "Created 8-30 days ago",
            "Created This Month",
        ),
        ("age-older", "Older", age["older"], "Created over 30 days ago", "Older Tasks"),
        ("age-nodate", "No Date", age["no_date"], "No creation date recorded", "No Creation Date"),
    ]

    max_count = max(age.values()) if age else 1

    bars = []
    for i, (css_class, label, count, hint, title) in enumerate(items):
        percentage = (count / max_count * 100) if max_count > 0 else 0
        pct_of_total = round((count / total_active * 100) if total_active > 0 else 0)
        task_plural = "s" if count != 1 else ""
        delay = i * 0.1

        bars.append(
            """
        <div class="bar-row {0} clickable" style="animation-delay: {1}s" data-filter="{2}" data-title="{3}">
            <div class="bar-label">{4}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {5}%">
                    <span class="bar-fill-text">{6}%</span>
                </div>
            </div>
            <div class="bar-count">{7}</div>
            <div class="bar-tooltip">{8}<br><strong>{9} task{10}</strong></div>
        </div>
        """.format(
                css_class,
                delay,
                css_class,
                title,
                label,
                percentage,
                pct_of_total,
                count,
                hint,
                count,
                task_plural,
            )
        )

    return '<div class="bar-chart">{0}</div>'.format("".join(bars))


def generate_html(stats):
    """Generate complete HTML document"""
    css = generate_css()
    timestamp = stats["generated_at"].strftime("%B %d, %Y at %I:%M %p")
    total_active = stats["total_active"]
    total_completed = stats["total_completed"]

    # Generate task JSON for modal
    task_json = tasks_to_json(stats["all_tasks"])

    overview_cards = generate_overview_cards(stats)
    priority_chart = generate_priority_chart(stats)

    # Generate Clouds
    context_cloud = generate_tag_cloud(stats["context_breakdown"], "context", "@", total_active)

    # Generate TWO project clouds (Active and Completed)
    project_cloud_active = generate_tag_cloud(
        stats["project_breakdown"],
        "project",
        "+",
        total_active,
        filter_type="project",
        elem_id="projects-active",
    )

    project_cloud_completed = generate_tag_cloud(
        stats["project_breakdown_completed"],
        "project",
        "+",
        total_completed,
        filter_type="project-completed",
        elem_id="projects-completed",
        hidden=True,
    )

    due_timeline = generate_due_date_timeline(stats)
    completion_chart = generate_completion_chart(stats)
    monthly_overview = generate_monthly_overview(stats)
    age_section = generate_task_age_section(stats)

    # Count unique contexts and projects
    context_count = len(stats["context_breakdown"])
    project_count_active = len(stats["project_breakdown"])
    project_count_completed = len(stats["project_breakdown_completed"])

    modal_js = """
    const tasks = window.TASKS_DATA;
    const today = new Date().toISOString().split("T")[0];

    function getWeekAgo() {
        const d = new Date();
        d.setDate(d.getDate() - 7);
        return d.toISOString().split("T")[0];
    }

    function getMonthAgo() {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        return d.toISOString().split("T")[0];
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function filterTasks(filterType, filterValue) {
        return tasks.filter(task => {
            switch(filterType) {
                case "active":
                    return !task.completed;
                case "completed":
                    return task.completed;
                case "overdue":
                    return !task.completed && task.due_date && task.due_date < today;
                case "today":
                    return !task.completed && task.due_date === today;
                case "week":
                    return !task.completed && task.due_date && task.due_date > today && task.due_date <= getWeekAgo().replace(/-/g, "") ? false :
                           !task.completed && task.due_date && task.due_date > today && task.due_date <= new Date(Date.now() + 7*24*60*60*1000).toISOString().split("T")[0];
                case "upcoming":
                    const weekFromNow = new Date(Date.now() + 7*24*60*60*1000).toISOString().split("T")[0];
                    return !task.completed && task.due_date && task.due_date > weekFromNow;
                case "no-due":
                    return !task.completed && !task.due_date;
                case "priority":
                    if (filterValue === "None") return !task.completed && !task.priority;
                    return !task.completed && task.priority === filterValue;
                case "context":
                    return !task.completed && task.contexts.includes(filterValue);
                case "project":
                    return !task.completed && task.projects.includes(filterValue);
                case "project-completed":
                    // NEW: Filter for completed tasks in a specific project
                    return task.completed && task.projects.includes(filterValue);
                case "completion-date":
                    return task.completed && task.completion_date === filterValue;
                case "age-today":
                    return !task.completed && task.creation_date === today;
                case "age-week":
                    const weekAgo = getWeekAgo();
                    return !task.completed && task.creation_date && task.creation_date > weekAgo && task.creation_date < today;
                case "age-month":
                    const monthAgo = getMonthAgo();
                    const wAgo = getWeekAgo();
                    return !task.completed && task.creation_date && task.creation_date > monthAgo && task.creation_date <= wAgo;
                case "age-older":
                    const mAgo = getMonthAgo();
                    return !task.completed && task.creation_date && task.creation_date <= mAgo;
                case "age-nodate":
                    return !task.completed && !task.creation_date;
                default:
                    return true;
            }
        });
    }

    function renderTaskList(filteredTasks) {
        if (filteredTasks.length === 0) {
            return `<div class="modal-empty"><i data-lucide="inbox"></i><div>No tasks found</div></div>`;
        }

        return `<ul class="task-list">${filteredTasks.map(task => {
            const isOverdue = task.due_date && task.due_date < today && !task.completed;
            const priorityClass = task.priority ? `priority-${task.priority.toLowerCase()}` : "";

            let meta = "";
            if (task.priority) {
                meta += `<span class="task-meta-item priority ${priorityClass}">(${task.priority})</span>`;
            }
            if (task.due_date) {
                meta += `<span class="task-meta-item due ${isOverdue ? "overdue" : ""}">due:${task.due_date}</span>`;
            }
            task.contexts.forEach(ctx => {
                meta += `<span class="task-meta-item context">@${escapeHtml(ctx)}</span>`;
            });
            task.projects.forEach(proj => {
                meta += `<span class="task-meta-item project">+${escapeHtml(proj)}</span>`;
            });
            meta += `<span class="task-meta-item source">${escapeHtml(task.source)}</span>`;

            return `
                <li class="task-item ${task.completed ? "completed" : ""}">
                    <div class="task-checkbox">${task.completed ? '<i data-lucide="check"></i>' : ""}</div>
                    <div class="task-content">
                        <div class="task-description">${escapeHtml(task.description)}</div>
                        <div class="task-meta">${meta}</div>
                    </div>
                </li>
            `;
        }).join("")}</ul>`;
    }

    function openModal(title, filterType, filterValue) {
        const filteredTasks = filterTasks(filterType, filterValue);
        const modal = document.getElementById("taskModal");
        const overlay = document.getElementById("modalOverlay");
        const modalTitle = document.getElementById("modalTitle");
        const modalBody = document.getElementById("modalBody");
        const badge = document.getElementById("modalBadge");

        modalTitle.textContent = title;
        badge.textContent = filteredTasks.length + " task" + (filteredTasks.length !== 1 ? "s" : "");
        modalBody.innerHTML = renderTaskList(filteredTasks);

        overlay.classList.add("active");
        modal.classList.add("active");
        document.body.style.overflow = "hidden";

        lucide.createIcons();
    }

    function closeModal() {
        const modal = document.getElementById("taskModal");
        const overlay = document.getElementById("modalOverlay");

        overlay.classList.remove("active");
        modal.classList.remove("active");
        document.body.style.overflow = "";
    }

    document.getElementById("modalOverlay").addEventListener("click", closeModal);
    document.getElementById("modalClose").addEventListener("click", closeModal);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });

    document.querySelectorAll("[data-filter]").forEach(el => {
        el.addEventListener("click", (e) => {
            // Check if the clicked element or its parent (for bubbled events) has the data-filter
            // In case of trend bars, the listener is on the bar, so 'el' is correct.
            const filterType = el.dataset.filter;
            const filterValue = el.dataset.value || "";
            const title = el.dataset.title || "Tasks";
            openModal(title, filterType, filterValue);
        });
    });

    // Project Toggle Logic
    const projectToggle = document.getElementById('project-toggle');
    if (projectToggle) {
        projectToggle.addEventListener('click', () => {
            const activeCloud = document.getElementById('projects-active');
            const completedCloud = document.getElementById('projects-completed');
            const isShowingActive = activeCloud.style.display !== 'none';

            const activeCount = projectToggle.dataset.activeCount;
            const completedCount = projectToggle.dataset.completedCount;

            if (isShowingActive) {
                // Switch to Completed
                activeCloud.style.display = 'none';
                completedCloud.style.display = 'flex'; // tag-cloud is flex
                projectToggle.innerHTML = completedCount + " completed";
                projectToggle.style.color = "var(--accent-emerald)";
                projectToggle.style.borderColor = "var(--accent-emerald)";
            } else {
                // Switch to Active
                completedCloud.style.display = 'none';
                activeCloud.style.display = 'flex';
                projectToggle.innerHTML = activeCount + " active";
                projectToggle.style.color = ""; // Reset to CSS default
                projectToggle.style.borderColor = "";
            }
        });
    }
    """

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo.txt Dashboard</title>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
    <style>{0}</style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="subtitle">Task Management</div>
            <h1>Todo.txt Dashboard</h1>
            <div class="timestamp">Generated on {1}</div>
        </div>

        {2}

        <div class="section" style="animation-delay: 0.3s">
            <div class="section-header">
                <h2 class="section-title"><span class="icon"><i data-lucide="calendar-clock"></i></span>Due Dates</h2>
                <span class="section-badge">Timeline</span>
            </div>
            {3}
        </div>

        <div class="grid-2">
            <div class="section" style="animation-delay: 0.4s">
                <div class="section-header">
                    <h2 class="section-title"><span class="icon"><i data-lucide="flag"></i></span>Priority Distribution</h2>
                </div>
                {4}
            </div>

            <div class="section" style="animation-delay: 0.45s">
                <div class="section-header">
                    <h2 class="section-title"><span class="icon"><i data-lucide="hourglass"></i></span>Task Age</h2>
                    <span class="section-badge">By creation date</span>
                </div>
                {5}
            </div>
        </div>

        <div class="grid-2">
            <div class="section" style="animation-delay: 0.5s">
                <div class="section-header">
                    <h2 class="section-title"><span class="icon"><i data-lucide="at-sign"></i></span>Contexts</h2>
                    <span class="section-badge">{6} unique</span>
                </div>
                {7}
            </div>

            <div class="section" style="animation-delay: 0.55s">
                <div class="section-header">
                    <h2 class="section-title"><span class="icon"><i data-lucide="folder"></i></span>Projects</h2>
                    <span class="section-badge clickable" id="project-toggle" data-active-count="{8}" data-completed-count="{9}">{8} active</span>
                </div>
                {10}
                {11}
            </div>
        </div>

        <div class="section" style="animation-delay: 0.6s">
            <div class="section-header">
                <h2 class="section-title"><span class="icon"><i data-lucide="trending-up"></i></span>Completion Trends</h2>
                <span class="section-badge">Last 14 days</span>
            </div>
            {12}
        </div>

        <div class="section" style="animation-delay: 0.65s">
            <div class="section-header">
                <h2 class="section-title"><span class="icon"><i data-lucide="calendar-range"></i></span>Monthly Overview</h2>
                <span class="section-badge">Last 6 months</span>
            </div>
            {13}
        </div>
    </div>

    <div class="modal-overlay" id="modalOverlay"></div>
    <div class="modal" id="taskModal">
        <div class="modal-header">
            <h3 class="modal-title">
                <span id="modalTitle">Tasks</span>
                <span class="badge" id="modalBadge">0</span>
            </h3>
            <button class="modal-close" id="modalClose">
                <i data-lucide="x"></i>
            </button>
        </div>
        <div class="modal-body" id="modalBody"></div>
    </div>

    <script>
        window.TASKS_DATA = {14};
        lucide.createIcons();
        {15}
    </script>
</body>
</html>""".format(
        css,
        timestamp,
        overview_cards,
        due_timeline,
        priority_chart,
        age_section,
        context_count,
        context_cloud,
        project_count_active,
        project_count_completed,
        project_cloud_active,
        project_cloud_completed,
        completion_chart,
        monthly_overview,
        task_json,
        modal_js,
    )


# ============================================================================
# MAIN API FUNCTION
# ============================================================================


def generate_dashboard(directory, open_browser=True):
    """
    Generate HTML dashboard from todo.txt files in the given directory.

    Args:
        directory path to directory containing todo.txt files
        open_browser: Whether to open the dashboard in the default browser

    Returns:
        Path to the generated HTML file
    """
    # Validate directory
    if not os.path.isdir(directory):
        raise ValueError("{0} is not a directory".format(directory))

    # Load all tasks
    tasks_by_file = load_all_tasks(directory)

    # Calculate statistics
    stats = calculate_statistics(tasks_by_file)

    # Generate HTML
    html = generate_html(stats)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        temp_path = f.name

    # Open in default browser if requested
    if open_browser:
        webbrowser.open("file://{0}".format(temp_path))

    return temp_path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate a beautiful HTML dashboard from todo.txt files"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing todo.txt files (default: current directory)",
    )
    args = parser.parse_args()

    try:
        directory = os.path.abspath(args.directory)
        print("Loading tasks from {0}...".format(directory))
        temp_path = generate_dashboard(directory, open_browser=True)
        print("Dashboard created: {0}".format(temp_path))
        print("Opening in browser...")
        return 0
    except Exception as e:
        print("Error: {0}".format(e))
        return 1


if __name__ == "__main__":
    exit(main())
