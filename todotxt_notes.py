import os
import re

import sublime
import sublime_plugin


class TodoTxtOpenNoteCommand(sublime_plugin.TextCommand):
    """Open a note file referenced in a todo.txt task"""

    def run(self, edit, file_path):
        # Resolve relative paths based on the todo.txt file's directory
        todo_file_dir = os.path.dirname(self.view.file_name())
        full_path = os.path.join(todo_file_dir, file_path)

        # Normalize the path
        full_path = os.path.normpath(full_path)

        if not os.path.exists(full_path):
            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)

            # Create an empty file
            with open(full_path, "w") as f:
                pass

        # Open the file in Sublime Text
        self.view.window().open_file(full_path)


class TodoTxtNoteNavigator(sublime_plugin.EventListener):
    """Make note: references hoverable with preview"""

    NOTE_PATTERN = r"\bnote:(\S+)"
    MAX_PREVIEW_LINES = 500

    def on_hover(self, view, point, hover_zone):
        if not self._should_process_hover(view, point, hover_zone):
            return

        note_info = self._get_note_at_point(view, point)
        if note_info:
            self._show_note_popup(view, point, note_info)

    def _should_process_hover(self, view, point, hover_zone):
        """Check if we should process this hover event"""
        return view.match_selector(point, "text.todo") and hover_zone == sublime.HOVER_TEXT

    def _get_note_at_point(self, view, point):
        """Extract note information if hovering over a note reference"""
        line_region = view.line(point)
        line_text = view.substr(line_region)

        match = re.search(self.NOTE_PATTERN, line_text)
        if not match:
            return None

        note_start = line_region.begin() + match.start()
        note_end = line_region.begin() + match.end()
        note_region = sublime.Region(note_start, note_end)

        if not note_region.contains(point):
            return None

        note_file = match.group(1)
        todo_file_dir = os.path.dirname(view.file_name())
        full_path = os.path.normpath(os.path.join(todo_file_dir, note_file))

        return {
            "note_file": note_file,
            "full_path": full_path,
            "exists": os.path.exists(full_path),
        }

    def _read_file_preview(self, file_path):
        """Read the first N lines of a file for preview"""
        try:
            lines = []
            with open(file_path, "r", encoding="utf-8") as f:
                for i in range(self.MAX_PREVIEW_LINES):
                    line = f.readline()
                    if not line:  # EOF reached
                        break
                    lines.append(line.rstrip("\n\r"))
            return "\n".join(lines) if lines else None
        except Exception as e:
            return f"Error: {str(e)}"

    def _build_popup_html(self, note_info, content_preview):
        """Build the HTML for the popup"""
        import html

        note_file = note_info["note_file"]
        full_path = note_info["full_path"]
        exists = note_info["exists"]

        action_text = "Click to open" if exists else "Click to create"

        if not exists:
            full_path = f"<span style='color: red;'>{html.escape(full_path)}</span><br>"
        else:
            full_path = f"<span style='font-size: 0.9em; color: color(var(--foreground) alpha(0.7));'>{html.escape(full_path)}</span><br>"

        # Only show status if file doesn't exist
        status_html = ""

        content_html = ""
        if exists:
            if content_preview is None or content_preview == "":
                # Empty file - show placeholder
                content_html = """
                    <div style="margin-top: 20px; overflow-y: auto; font-family: monospace;">
                        <div style="font-size: 0.9em; color: color(var(--foreground) alpha(0.5)); font-style: italic;">&lt;EMPTY FILE&gt;</div>
                    </div>
                """
            elif content_preview.startswith("Error:"):
                content_html = f'<div style="margin-top: 20px; color: red; font-size: 0.9em;">{html.escape(content_preview)}</div>'
            else:
                # Escape HTML and replace newlines with <br> for proper display
                escaped_content = html.escape(content_preview).replace("\n", "<br>")
                content_html = f"""
                    <div style="margin-top: 20px; overflow-y: auto; font-family: monospace;">
                        <div style="font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word;">{escaped_content}</div>
                    </div>
                """

        return f"""
        <body style="padding: 8px;">
            <div style="font-family: system;">
                <strong>Note:</strong> {html.escape(note_file)}<br>
                {status_html}
                {full_path}
                <br>
                <a href="open">{action_text}</a>
                {content_html}
            </div>
        </body>
        """

    def _show_note_popup(self, view, point, note_info):
        """Show the popup with note information and preview"""
        content_preview = None
        if note_info["exists"]:
            content_preview = self._read_file_preview(note_info["full_path"])

        html = self._build_popup_html(note_info, content_preview)

        view.show_popup(
            html,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            max_width=600,
            on_navigate=lambda href: self.open_note(view, note_info["note_file"]),
        )

    def open_note(self, view, file_path):
        """Trigger the command to open/create the note file"""
        view.run_command("todo_txt_open_note", {"file_path": file_path})


class TodoTxtNoteHighlighter(sublime_plugin.EventListener):
    """Highlight note: references"""

    NOTE_PATTERN = r"\bnote:(\S+)"

    def on_modified_async(self, view):
        if view.match_selector(0, "text.todo"):
            self.highlight_notes(view)

    def on_load_async(self, view):
        if view.match_selector(0, "text.todo"):
            self.highlight_notes(view)

    def highlight_notes(self, view):
        # Clear existing regions
        view.erase_regions("note_references_exists")
        view.erase_regions("note_references_missing")

        # Find all note:path patterns
        regions = view.find_all(self.NOTE_PATTERN)

        todo_file_dir = os.path.dirname(view.file_name())
        existing_regions = []
        missing_regions = []

        for region in regions:
            text = view.substr(region)
            match = re.match(self.NOTE_PATTERN, text)
            if match:
                note_file = match.group(1)
                full_path = os.path.normpath(os.path.join(todo_file_dir, note_file))

                if os.path.exists(full_path):
                    existing_regions.append(region)
                else:
                    missing_regions.append(region)

        # Highlight existing notes with normal underline
        view.add_regions(
            "note_references_exists",
            existing_regions,
            scope="entity.name.filename.note.todo",
            flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE,
        )

        # Highlight missing notes with red underline
        view.add_regions(
            "note_references_missing",
            missing_regions,
            scope="region.redish",
            flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE,
        )
