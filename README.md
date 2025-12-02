# Spring Plan Automation

Automates adding and updating MIS tasks in the Year 5 Plan board on Monday.com.

## Files

- **`monday_importer.py`** - Core Monday.com API library
- **`spring_plan.py`** - Main script (add or update tasks)
- **`requirements.txt`** - Python dependencies

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the main script:

```bash
python spring_plan.py
```

Choose an option:
1. **Add new MIS tasks** - Creates MIS 1 and MIS 2 items with subitems
2. **Update existing subitems** - Updates deadlines, hours, and dependencies for existing tasks

## Configuration

- **Board**: Always uses Year 5 Plan board
- **Group**: Spring Plan group
- **API Token**: Hardcoded in script
- **Start Date**: January 1, 2026
- **End Date**: February 14, 2026
- **Tasks**: MIS 1 (7 subitems) and MIS 2 (3 subitems)

All tasks are automatically distributed evenly across the timeline with dependencies set.
