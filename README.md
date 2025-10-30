# TodoTxt for Sublime Text

A comprehensive Sublime Text plugin for managing todo.txt files

![CleanShot 2025-10-30 at 11 38 17@2x](https://github.com/user-attachments/assets/40a9399d-487a-4144-92f5-e00411434cf3)

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

### Quality of Life Improvements

- **Due Date Highlighting** - Color-coded due dates (red for past, orange for today, green for future)
- **Note References** - Hover over `note:filename` to preview note contents
- **Note Highlighting** - Visual indication of existing vs missing note files
- **Autocomplete** - Context (@) and project (+) tag suggestions

## Usage

### Quick Start

1. Create a new file named `todo.txt`
2. Open the command palette (Ctrl+Shift+P) and type "TodoTxt: Add New Task"
3. Use the command palette to access all TodoTxt commands (see Keyboard Shortcuts section to enable hotkeys)

### Keyboard Shortcuts

The plugin includes suggested keyboard shortcuts that are commented out by default to avoid conflicts with other packages. To enable them:

1. Open the command palette (Ctrl+Shift+P)
2. Type "Preferences: TodoTxt Key Bindings"
3. Uncomment the desired shortcuts in the left pane
4. Or copy them to your user key bindings on the right pane

Suggested shortcuts:
- `Ctrl+Shift+Space` - Add new task
- `Ctrl+Shift+X` - Toggle task completion
- `Ctrl+Shift+C` - Increase priority
- `Ctrl+Shift+Z` - Decrease priority

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

- TodoTxt: Add New Task - Opens input panel to create a new task with automatic creation date
- TodoTxt: Toggle Task Completion - Marks selected tasks as complete or incomplete with completion date
- TodoTxt: Increase Priority - Raises task priority (B→A) or adds (A) if no priority exists
- TodoTxt: Decrease Priority - Lowers task priority (A→B) or removes priority at (Z)
- TodoTxt: Remove Priorities - Removes priority markers from selected tasks
- TodoTxt: Sort by Context - Groups and sorts tasks by @context tags alphabetically
- TodoTxt: Sort by Project - Groups and sorts tasks by +project tags alphabetically
- TodoTxt: Sort by Priority - Orders tasks by priority level (A) through (Z), highest first
- TodoTxt: Sort by Due Date - Orders tasks by due date, earliest first, no date last
- TodoTxt: Sort by Creation Date - Orders tasks by creation date, earliest first
- TodoTxt: Sort by Status - Moves all completed tasks to the bottom of the file
- TodoTxt: Archive Completed Tasks - Moves completed tasks to done.txt and removes from current file
- TodoTxt: Move to Someday - Moves selected tasks to someday.txt for future consideration
- TodoTxt: Move to Waiting - Moves selected tasks to waiting.txt for blocked items
- TodoTxt: Move to Todo - Moves selected tasks from someday.txt or waiting.txt back to todo.txt

You can add custom keyboard shortcuts for any command by editing your Sublime Text key bindings. Use these command names:

- `todo_txt_add_new_task`
- `todo_txt_toggle_task_completion`
- `todo_txt_increase_priority`
- `todo_txt_decrease_priority`
- `todo_txt_remove_priority`
- `todo_txt_sort_by_context`
- `todo_txt_sort_by_project`
- `todo_txt_sort_by_priority`
- `todo_txt_sort_by_due_date`
- `todo_txt_sort_by_creation_date`
- `todo_txt_sort_by_status`
- `todo_txt_archive_completed`
- `todo_txt_move_to_someday`
- `todo_txt_move_to_waiting`
- `todo_txt_move_to_todo`

## License

MIT
