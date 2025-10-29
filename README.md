# TodoTxt for Sublime Text

A comprehensive Sublime Text plugin for managing todo.txt files.

## Features

### Task Management

- **Add New Task** - Create tasks with automatic creation date below cursor position
- **Toggle Task Completion** - Mark tasks as complete/incomplete with completion dates
- **Priority Management**
  - Increase priority (move up from B to A, or add A if none)
  - Decrease priority (move down from A to B, or remove at Z)
  - Remove priorities from selected tasks

### Organization

- **Sort by Context** - Group tasks by @context tags
- **Sort by Project** - Group tasks by +project tags
- **Sort by Priority** - Order by (A) through (Z) priority levels
- **Sort by Due Date** - Order by due:YYYY-MM-DD dates (earliest first)
- **Sort by Creation Date** - Order by task creation dates
- **Sort by Status** - Move completed tasks to bottom

### Task Movement

- **Archive Completed Tasks** - Move completed tasks to done.txt
- **Move to Someday** - Defer tasks to someday.txt for future consideration
- **Move to Waiting** - Move tasks to waiting.txt for blocked/waiting items
- **Move to Todo** - Bring tasks back from someday.txt or waiting.txt to todo.txt

### Visual Features

- **Due Date Highlighting** - Color-coded due dates (red for past, orange for today, green for future)
- **Note References** - Hover over `note:filename` to preview note contents
- **Note Highlighting** - Visual indication of existing vs missing note files
- **Autocomplete** - Context (@) and project (+) tag suggestions

### Keyboard Shortcuts

- `Ctrl+Shift+Space` - Add new task
- `Ctrl+Shift+X` - Toggle task completion
- `Ctrl+Shift+C` - Increase priority
- `Ctrl+Shift+Z` - Decrease priority

## Usage

### Quick Start

1. Create a new file named `todo.txt`
2. Press `Ctrl+Shift+Space` to add your first task
3. Use the command palette (Ctrl+Shift+P) to access all TodoTxt commands

### Task Format

The plugin follows the todo.txt format specification:

- `(A) Task description` - Task with priority
- `2025-10-29 Task description` - Task with creation date
- `x 2025-10-29 Task description` - Completed task
- `Task @context +project due:2025-12-31` - Task with metadata
- `Task note:notes/task-details.md` - Task with linked note file

### File Organization

The plugin supports multiple files in the same directory:

- `todo.txt` - Active tasks
- `done.txt` - Archived completed tasks
- `someday.txt` - Future/deferred tasks
- `waiting.txt` - Blocked/waiting tasks

## Commands

All commands are available through the command palette (Ctrl+Shift+P):

- TodoTxt: Add New Task - `todo_txt_add_new_task`
- TodoTxt: Toggle Task Completion - `todo_txt_toggle_task_completion`
- TodoTxt: Increase Priority - `todo_txt_increase_priority`
- TodoTxt: Decrease Priority - `todo_txt_decrease_priority`
- TodoTxt: Remove Priorities - `todo_txt_remove_priority`
- TodoTxt: Sort by Context - `todo_txt_sort_by_context`
- TodoTxt: Sort by Project - `todo_txt_sort_by_project`
- TodoTxt: Sort by Priority - `todo_txt_sort_by_priority`
- TodoTxt: Sort by Due Date - `todo_txt_sort_by_due_date`
- TodoTxt: Sort by Creation Date - `todo_txt_sort_by_creation_date`
- TodoTxt: Sort by Status - `todo_txt_sort_by_status`
- TodoTxt: Archive Completed Tasks - `todo_txt_archive_completed`
- TodoTxt: Move to Someday - `todo_txt_move_to_someday`
- TodoTxt: Move to Waiting - `todo_txt_move_to_waiting`
- TodoTxt: Move to Todo - `todo_txt_move_to_todo`

## License

MIT
