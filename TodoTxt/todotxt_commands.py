import os
import re
from datetime import datetime

import sublime
import sublime_plugin

DONE_FILE = "done.txt"


class TodoTxtToggleTaskCompletionCommand(sublime_plugin.TextCommand):
    """Toggle task completion: mark complete or uncomplete"""

    def run(self, edit):
        view = self.view

        # Get current date
        today = datetime.now().strftime("%Y-%m-%d")

        # Process each selection/cursor (in reverse to handle insertions correctly)
        for region in reversed(view.sel()):
            # If it's a single cursor (empty selection), process the line at cursor
            if region.empty():
                lines_to_process = [view.line(region)]
            else:
                # For selections, process all lines that intersect with the selection
                lines_to_process = view.lines(region)

            # Process each line (in reverse to handle insertions correctly)
            for line in reversed(lines_to_process):
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


class TodoTxtSortByDueDateCommand(sublime_plugin.TextCommand):
    """Sort tasks by due date (due:YYYY-MM-DD)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by due date
        sorted_lines = self._sort_by_due_date(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_due_date(self, lines):
        """Sort lines by their due date"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                due_date = self._extract_due_date(stripped)
                tasks.append((due_date, i, line))

        # Sort by due date (None/invalid dates last), then by original order
        # Use a tuple where None becomes a far future date for sorting
        tasks.sort(key=lambda x: (x[0] if x[0] is not None else "9999-99-99", x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _extract_due_date(self, line):
        """Extract the due date (due:YYYY-MM-DD) from a line, or None if none"""
        match = re.search(r"\bdue:(\d{4}-\d{2}-\d{2})\b", line)
        if match:
            date_str = match.group(1)
            # Validate the date format
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                return None
        return None

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")


class TodoTxtSortByPriorityCommand(sublime_plugin.TextCommand):
    """Sort tasks by priority (A) through (Z)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by priority
        sorted_lines = self._sort_by_priority(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_priority(self, lines):
        """Sort lines by their priority"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                priority = self._extract_priority(stripped)
                tasks.append((priority, i, line))

        # Sort by priority (None/no priority last), then by original order
        # Priority A comes before B, etc. Tasks without priority go to the end
        tasks.sort(key=lambda x: (x[0] if x[0] is not None else "ZZZ", x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _extract_priority(self, line):
        """Extract the priority (A) through (Z) from a line, or None if none"""
        # Priority format in todo.txt: (A) at the beginning of the line
        # Can be after completion marker: x 2025-10-29 (A) task
        match = re.match(r"^(?:x\s+\d{4}-\d{2}-\d{2}\s+)?\(([A-Z])\)\s+", line)
        if match:
            return match.group(1)
        return None

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")


class TodoTxtSortByCreationDateCommand(sublime_plugin.TextCommand):
    """Sort tasks by creation date (YYYY-MM-DD at start of task)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by creation date
        sorted_lines = self._sort_by_creation_date(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_creation_date(self, lines):
        """Sort lines by their creation date"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                creation_date = self._extract_creation_date(stripped)
                tasks.append((creation_date, i, line))

        # Sort by creation date (None/invalid dates last), then by original order
        # Use a tuple where None becomes a far future date for sorting
        tasks.sort(key=lambda x: (x[0] if x[0] is not None else "9999-99-99", x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _extract_creation_date(self, line):
        """Extract the creation date from a line, or None if none"""
        # Creation date formats in todo.txt:
        # - (A) 2025-10-29 task (with priority)
        # - 2025-10-29 task (without priority)
        # - x 2025-10-29 2025-10-15 task (completed, completion date then creation date)

        # Check for completed task: x YYYY-MM-DD YYYY-MM-DD
        match = re.match(r"^x\s+\d{4}-\d{2}-\d{2}\s+(\d{4}-\d{2}-\d{2})\s+", line)
        if match:
            date_str = match.group(1)
            if self._validate_date(date_str):
                return date_str

        # Check for task with priority: (A) YYYY-MM-DD
        match = re.match(r"^\([A-Z]\)\s+(\d{4}-\d{2}-\d{2})\s+", line)
        if match:
            date_str = match.group(1)
            if self._validate_date(date_str):
                return date_str

        # Check for task without priority: YYYY-MM-DD at start
        match = re.match(r"^(\d{4}-\d{2}-\d{2})\s+", line)
        if match:
            date_str = match.group(1)
            if self._validate_date(date_str):
                return date_str

        return None

    def _validate_date(self, date_str):
        """Validate a date string"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")


class TodoTxtSortByStatusCommand(sublime_plugin.TextCommand):
    """Sort tasks by status (incomplete first, completed last)"""

    def run(self, edit):
        view = self.view

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Sort lines by status
        sorted_lines = self._sort_by_status(lines)

        # Replace the entire content
        view.replace(edit, region, "\n".join(sorted_lines))

    def _sort_by_status(self, lines):
        """Sort lines by their completion status"""
        # Separate empty lines from task lines
        tasks = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:
                is_completed = self._is_completed(stripped)
                # Use 0 for incomplete, 1 for completed to sort incomplete first
                tasks.append((1 if is_completed else 0, i, line))

        # Sort by status (incomplete=0 first, completed=1 last), then by original order
        tasks.sort(key=lambda x: (x[0], x[1]))

        # Return sorted lines
        return [task[2] for task in tasks]

    def _is_completed(self, line):
        """Check if a task is completed (starts with 'x ')"""
        return line.startswith("x ")

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")


class TodoTxtArchiveCompletedCommand(sublime_plugin.TextCommand):
    """Archive completed tasks to DONE_FILE"""

    def run(self, edit):
        view = self.view

        # Get the todo.txt file path
        todo_file = view.file_name()
        if not todo_file:
            sublime.status_message("TodoTxt: Please save the file first")
            return

        # Get the DONE_FILE path (same directory as todo.txt)
        todo_dir = os.path.dirname(todo_file)
        done_file = os.path.join(todo_dir, DONE_FILE)

        # Get all lines in the file
        region = sublime.Region(0, view.size())
        content = view.substr(region)
        lines = content.split("\n")

        # Separate completed and incomplete tasks
        completed_tasks = []
        incomplete_tasks = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                if stripped.startswith("x "):
                    completed_tasks.append(line)
                else:
                    incomplete_tasks.append(line)

        # If no completed tasks, show message and return
        if not completed_tasks:
            sublime.status_message("TodoTxt: No completed tasks to archive")
            return

        # Append completed tasks to DONE_FILE
        try:
            # Check if we need to add a newline first
            needs_newline = False
            if os.path.exists(done_file) and os.path.getsize(done_file) > 0:
                with open(done_file, "rb") as f:
                    # Seek to the last byte
                    f.seek(-1, os.SEEK_END)
                    last_char = f.read(1)
                    # Check if last character is not a newline
                    needs_newline = last_char not in (b"\n", b"\r")

            with open(done_file, "a", encoding="utf-8") as f:
                if needs_newline:
                    f.write("\n")
                for task in completed_tasks:
                    f.write(task + "\n")
        except Exception as e:
            sublime.status_message("TodoTxt: Error writing to {0} - {1}".format(DONE_FILE, str(e)))
            return

        # Replace the current file content with only incomplete tasks
        view.replace(edit, region, "\n".join(incomplete_tasks))

        # Show success message
        task_count = len(completed_tasks)
        task_word = "task" if task_count == 1 else "tasks"
        sublime.status_message(
            "TodoTxt: Archived {0} {1} to {2}".format(task_count, task_word, DONE_FILE)
        )

    def is_enabled(self):
        """Only enable in todo.txt files"""
        return self.view.match_selector(0, "text.todo")
