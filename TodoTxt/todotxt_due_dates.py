import re
from datetime import datetime

import sublime
import sublime_plugin


class TodoTxtDueDateHighlighter(sublime_plugin.EventListener):
    """Highlight due dates based on whether they're past, present, or future"""

    def on_modified_async(self, view):
        if view.match_selector(0, "text.todo"):
            self.highlight_due_dates(view)

    def on_load_async(self, view):
        if view.match_selector(0, "text.todo"):
            self.highlight_due_dates(view)

    def highlight_due_dates(self, view):
        # Clear existing regions
        view.erase_regions("due_date_past")
        view.erase_regions("due_date_today")
        view.erase_regions("due_date_future")

        # Get today's date
        today = datetime.now().date()

        # Find all due:YYYY-MM-DD patterns
        due_pattern = r"\bdue:(\d{4}-\d{2}-\d{2})\b"
        regions = view.find_all(due_pattern)

        past_regions = []
        today_regions = []
        future_regions = []

        for region in regions:
            text = view.substr(region)
            match = re.match(due_pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    due_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    if due_date < today:
                        past_regions.append(region)
                    elif due_date == today:
                        today_regions.append(region)
                    else:
                        future_regions.append(region)
                except ValueError:
                    # Invalid date format, skip
                    pass

        # Apply color regions
        # Past dates - red (error scope)
        view.add_regions(
            "due_date_past",
            past_regions,
            scope="region.redish",
            flags=sublime.DRAW_NO_FILL,
        )

        # Today - yellow/orange (warning scope)
        view.add_regions(
            "due_date_today",
            today_regions,
            scope="region.orangish",
            flags=sublime.DRAW_NO_FILL,
        )

        # Future dates - green (success scope)
        view.add_regions(
            "due_date_future",
            future_regions,
            scope="region.greenish",
            flags=sublime.DRAW_NO_FILL,
        )
