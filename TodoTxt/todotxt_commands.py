import re
from datetime import datetime

import sublime
import sublime_plugin


class TodoTxtCompleteTaskCommand(sublime_plugin.TextCommand):
    """Toggle task completion: mark complete or uncomplete"""

    def run(self, edit):
        view = self.view

        # Get current date
        today = datetime.now().strftime("%Y-%m-%d")

        # Process each selection/cursor
        for region in view.sel():
            # Get the line containing the cursor
            line = view.line(region)
            line_text = view.substr(line)
            stripped = line_text.lstrip()

            # If already completed, uncomplete it
            if stripped.startswith("x "):
                # Remove "x YYYY-MM-DD " from the beginning
                # Match "x " followed by optional date and space
                uncompleted = re.sub(r"^(\s*)x\s+(?:\d{4}-\d{2}-\d{2}\s+)?", r"\1", line_text)
                view.replace(edit, line, uncompleted)
            else:
                # Add completion marker at the beginning of the line
                completion_prefix = "x {0} ".format(today)
                view.insert(edit, line.begin(), completion_prefix)

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")
