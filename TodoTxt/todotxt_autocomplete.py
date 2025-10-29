import sublime
import sublime_plugin


class TodoTxtAutocomplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # Only trigger for todo.txt files
        if not view.match_selector(locations[0], "text.todo"):
            return None

        # Get the character before the cursor
        pref = sublime.Region(locations[0] - 1, locations[0])
        pref = view.substr(pref)

        if pref == "@":
            regex = r"\s@\S+"  # Todo item context
        elif pref == "+":
            regex = r"\s\+\S+"  # Todo item project
        else:
            return None

        # Find all matches in the current view
        matches = view.find_all(regex)
        matches = {view.substr(x).lstrip() for x in matches}

        # Create autocomplete list
        autocompletes = [[x, x] for x in sorted(matches)]

        return (
            autocompletes,
            sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS,
        )
