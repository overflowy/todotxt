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


class TodoTxtSortByContextCommand(sublime_plugin.TextCommand):
    """Sort tasks by context (@word)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by context
        sorted_lines = self._sort_by_context(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_context(self, lines):
        """Sort lines by their context, preserving empty lines"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                context = self._extract_context(stripped)
                tasks.append((context, i, line))

        # Sort by context (case-insensitive), then by original order
        tasks.sort(key=lambda x: (x[0].lower(), x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _extract_context(self, line):
        """Extract the first context (@word) from a line, or empty string if none"""
        match = re.search(r"\s@(\S+)", line)
        return match.group(1) if match else ""

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")


class TodoTxtSortByProjectCommand(sublime_plugin.TextCommand):
    """Sort tasks by project (+word)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by project
        sorted_lines = self._sort_by_project(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_project(self, lines):
        """Sort lines by their project, preserving empty lines"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                project = self._extract_project(stripped)
                tasks.append((project, i, line))

        # Sort by project (case-insensitive), then by original order
        tasks.sort(key=lambda x: (x[0].lower(), x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _extract_project(self, line):
        """Extract the first project (+word) from a line, or empty string if none"""
        match = re.search(r"\s\+(\S+)", line)
        return match.group(1) if match else ""

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")
