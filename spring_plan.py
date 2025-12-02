"""
Spring Plan Automation - Add and Update MIS tasks in Year 5 Plan board
Always uses Year 5 Plan board with Spring Plan group
"""

import time
import json
import requests
from datetime import datetime, timedelta
from monday_importer import MondayImporter

# API Token - Always the same
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU5Mjk4NDI1NSwiYWFpIjoxMSwidWlkIjo2NTcyMTMxNCwiaWFkIjoiMjAyNS0xMi0wMlQxNzoyMTo1MC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjQ0NDY1NTQsInJnbiI6InVzZTEifQ.oHP8gGwt-5fDSeChJfE_uy3jJcuqopgyZ1lGgcFmL40"

# Task definitions
MIS_TASKS = {
    "MIS 1": [
        {"name": "Onboarding with details of the task and the purpose of the challenge", "hours": 10},
        {"name": "Familiarization with current progress", "hours": 10},
        {"name": "Refine solution with technical and business details", "hours": 50},
        {"name": "Research impacts and stakeholders of the topic", "hours": 20},
        {"name": "Develop an engaging elevator pitch for the topic", "hours": 20},
        {"name": "Develop presentation slides with engaging visuals and technical and business depth", "hours": 20},
        {"name": "Polishing and Practicing presentation slides", "hours": 15},
    ],
    "MIS 2": [
        {"name": "Onboarding with details of the rubric and purpose of the presentation", "hours": 10},
        {"name": "Understand the developed presentation; key points of slides, details on MVP, self-certification plan, and comparisons", "hours": 30},
        {"name": "Refine talking points on slides and practice presentation", "hours": 40},
    ]
}

# Hardware tasks (Jan 5, 2026 to May 15, 2026)
HARDWARE_TASKS = {
    "AVT BOLT VINYL": [
        {"name": "Taking the stickers out - Record the Bolt before to determine where stickers are currently placed, Peel the stickers out of the chassis", "hours": 2},
        {"name": "Wash and Degrease the car - Handwash chevy bolt", "hours": 2},
        {"name": "4 Doors - NOT REMOVING THE PANEL", "hours": 60},
        {"name": "Hood", "hours": 15},
        {"name": "Antenna Fin", "hours": 2},
        {"name": "Side Panels, behind the doors/front of the doors", "hours": 21},
        {"name": "Roof - Remove the rack with sensors but not the panel", "hours": 30},
        {"name": "Trunk - Not removing the back panel", "hours": 30},
        {"name": "Front headlight panel", "hours": 30},
        {"name": "Both Side mirrors", "hours": 6},
        {"name": "Charging Port", "hours": 2},
    ],
    "Ventilation System": [
        {"name": "Implementation of fan and duct with OEM Sill Plate", "hours": 20},
        {"name": "Implementation and creating of an electrical circuit, electrical routing, and optimized fan speed - speed varied via voltage input", "hours": 20},
    ],
    "ZED 2i Mounting": [
        {"name": "Implementation of ZED 2i - internal", "hours": 10},
        {"name": "Cable routing", "hours": 5},
        {"name": "Mounting bracketry", "hours": 5},
    ],
    "Old Comp. Cars": [
        {"name": "Continuation of scrapping/salvaging", "hours": 20},
    ],
    "Rear rack New Arrangement": [
        {"name": "Run FEA and CFD simulation to support the reason for the new arrangement", "hours": 20},
        {"name": "Working on the bottom shelf arrangement if necessary", "hours": 15},
        {"name": "Physically executing the new arrangement on the new bought plywood", "hours": 15},
    ],
    "Cable Management": [
        {"name": "Working on finding the best possible way for the hardware cable routing", "hours": 20},
    ],
    "Create new wiring Diagrams in Rapid Harness": [
        {"name": "Add all components that are currently part of our system", "hours": 20},
        {"name": "Update layout based on new rear rack layout", "hours": 10},
    ],
    "Simulink Design for Rear rack": [
        {"name": "Update Simulation to better represent our sine inverter", "hours": 10},
        {"name": "Add loads to our outputs to test load stress", "hours": 10},
        {"name": "Integrate Power system design into overall Simulink Architecture, including sensors", "hours": 50},
    ],
    "Blue light system": [
        {"name": "Debug frequency problem of blue lights during manual driving", "hours": 20},
    ],
    "Draw.IO Flowchart": [
        {"name": "Add additional depth to our design structure and overall architecture", "hours": 20},
    ],
    "Waterproofing cable": [
        {"name": "Decide whether placing the sensors - Zed 2i Mount as an example - would be a better idea than placing them inside the car", "hours": 20},
        {"name": "If yes, work on finding ways on how to waterproof the sensors and the cables", "hours": 30},
    ],
}

# Date ranges
MIS_START_DATE = datetime(2026, 1, 1)
MIS_END_DATE = datetime(2026, 2, 14)
HARDWARE_START_DATE = datetime(2026, 1, 5)
HARDWARE_END_DATE = datetime(2026, 5, 15)


def get_item_subitems(api_token, item_id):
    """Get all subitems for an item"""
    query = """
    query ($itemId: [ID!]) {
        items(ids: $itemId) {
            id
            name
            subitems {
                id
                name
            }
        }
    }
    """
    
    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.monday.com/v2",
        json={"query": query, "variables": {"itemId": item_id}},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            return []
        if data.get("data", {}).get("items"):
            return data["data"]["items"][0].get("subitems", [])
    return []


def find_year5_board(importer):
    """Find Year 5 Plan board (always the same)"""
    boards = importer.list_boards()
    for board in boards:
        if "year 5 plan" in board["name"].lower() and "subitems" not in board["name"].lower():
            board_id = board["id"]
            groups = importer.get_board_groups(board_id)
            for group in groups:
                if "team leadership" in group["title"].lower():
                    return board, board_id
    return None, None


def find_subitems_board(boards, board_id):
    """Find subitems board for Year 5 Plan"""
    for board in boards:
        if "subitems" in board["name"].lower() and "year 5" in board["name"].lower():
            return board["id"]
    return board_id  # Fallback to main board


def get_spring_group(importer, board_id):
    """Find Spring Plan group"""
    groups = importer.get_board_groups(board_id)
    for group in groups:
        if "spring" in group["title"].lower():
            return group
    return groups[0] if groups else None


def get_columns(importer, board_id):
    """Get required columns from board"""
    columns = importer.get_board_columns(board_id)
    planned_hours_col = None
    deadline_col = None
    dependency_col = None
    
    for col in columns:
        col_title_lower = col["title"].lower()
        col_type = col.get("type", "").lower()
        
        if (col_type in ["hour", "numeric", "duration"] or 
            "hour" in col_title_lower or "time" in col_title_lower or "planned" in col_title_lower):
            if not planned_hours_col:
                planned_hours_col = col
        
        if (col_type == "date" and 
            ("deadline" in col_title_lower or "due" in col_title_lower or "date" in col_title_lower)):
            if not deadline_col:
                deadline_col = col
        elif col_type == "timeline":
            if not deadline_col:
                deadline_col = col
        
        if "dependency" in col_title_lower or "depend" in col_title_lower:
            if not dependency_col:
                dependency_col = col
    
    return planned_hours_col, deadline_col, dependency_col


def update_subitem(importer, subitems_board_id, subitem_id, subitem_data, deadline_date, 
                   planned_hours_col, deadline_col, dependency_col, previous_subitem_id, verbose=False):
    """Update a single subitem with hours, deadline, and dependency"""
    # Set planned hours
    if planned_hours_col:
        try:
            col_type = planned_hours_col.get("type", "").lower()
            if col_type == "hour":
                hours_value = {"hours": subitem_data["hours"], "minutes": 0}
            elif col_type in ["numeric", "numbers"]:
                hours_value = subitem_data["hours"]
            else:
                hours_value = {"hours": subitem_data["hours"], "minutes": 0}
            importer.change_column_value(subitems_board_id, subitem_id, planned_hours_col["id"], hours_value)
            if verbose:
                print(f"      ✓ Set planned hours: {subitem_data['hours']}h")
        except Exception as e:
            print(f"      ⚠️  Could not set planned hours: {e}")
    elif verbose:
        print(f"      ⚠️  Planned hours column not found")
    
    # Set deadline
    if deadline_col:
        try:
            col_type = deadline_col.get("type", "").lower()
            if col_type == "timeline":
                timeline_value = {
                    "from": deadline_date.strftime("%Y-%m-%d"),
                    "to": deadline_date.strftime("%Y-%m-%d")
                }
                importer.change_column_value(subitems_board_id, subitem_id, deadline_col["id"], timeline_value)
            else:
                date_value = {"date": deadline_date.strftime("%Y-%m-%d")}
                importer.change_column_value(subitems_board_id, subitem_id, deadline_col["id"], date_value)
            if verbose:
                print(f"      ✓ Set deadline: {deadline_date.strftime('%b %d, %Y')}")
        except Exception as e:
            print(f"      ⚠️  Could not set deadline: {e}")
    elif verbose:
        print(f"      ⚠️  Deadline column not found")
    
    # Set dependency
    if dependency_col and previous_subitem_id:
        try:
            dep_value = json.dumps({"item_ids": [int(previous_subitem_id)]})
            importer.change_column_value(subitems_board_id, subitem_id, dependency_col["id"], dep_value)
            if verbose:
                print(f"      ✓ Set dependency on previous subitem")
        except Exception as e:
            try:
                dep_value = json.dumps({"pulse_ids": [int(previous_subitem_id)]})
                importer.change_column_value(subitems_board_id, subitem_id, dependency_col["id"], dep_value)
                if verbose:
                    print(f"      ✓ Set dependency on previous subitem")
            except Exception as e2:
                print(f"      ⚠️  Could not set dependency: {e2}")
    elif verbose and previous_subitem_id:
        print(f"      ⚠️  Dependency column not found")


def add_tasks(task_dict, start_date, end_date, task_type="tasks"):
    """Add new tasks to Spring Plan board"""
    print("🔗 Connecting to Monday.com...")
    importer = MondayImporter(API_TOKEN)
    
    # Find Year 5 Plan board
    print("\n🔍 Finding Year 5 Plan board...")
    year5_board, board_id = find_year5_board(importer)
    if not year5_board:
        print("❌ Year 5 Plan board not found")
        return
    
    print(f"✓ Found board: {year5_board['name']} (ID: {board_id})")
    
    # Find subitems board
    boards = importer.list_boards()
    subitems_board_id = find_subitems_board(boards, board_id)
    print(f"✓ Using subitems board (ID: {subitems_board_id})")
    
    # Find Spring Plan group
    print("\n📋 Finding Spring Plan group...")
    spring_group = get_spring_group(importer, board_id)
    if not spring_group:
        print("❌ No groups found")
        return
    print(f"✓ Found group: {spring_group['title']}")
    group_id = spring_group["id"]
    
    # Get columns
    print("\n📊 Getting columns...")
    planned_hours_col, deadline_col, dependency_col = get_columns(importer, subitems_board_id)
    print(f"✓ Found columns: Planned Hours, Deadline, Dependencies")
    
    # Calculate deadline distribution - flatten all subitems across all items
    all_subitems = []
    for item_name, subitems in task_dict.items():
        for subitem in subitems:
            all_subitems.append({"item": item_name, "subitem": subitem})
    
    total_subitems = len(all_subitems)
    total_days = (end_date - start_date).days
    days_between = total_days / (total_subitems - 1) if total_subitems > 1 else 0
    
    print(f"\n📥 Adding {task_type}...")
    print(f"   Timeline: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    print(f"   Total subitems: {total_subitems}")
    
    imported_items = 0
    imported_subitems = 0
    subitem_idx = 0
    previous_subitem_id = None
    
    for item_name, subitems in task_dict.items():
        try:
            print(f"\n  Creating {item_name}...")
            item_id = importer.create_item(board_id, group_id, item_name)
            imported_items += 1
            print(f"    ✓ Created {item_name}")
            
            for subitem in subitems:
                try:
                    subitem_id = importer.create_subitem(item_id, subitem["name"])
                    imported_subitems += 1
                    subitem_idx += 1
                    
                    deadline_date = start_date + timedelta(days=days_between * (subitem_idx - 1))
                    if deadline_date > end_date:
                        deadline_date = end_date
                    
                    update_subitem(importer, subitems_board_id, subitem_id, subitem, deadline_date,
                                 planned_hours_col, deadline_col, dependency_col, previous_subitem_id, verbose=True)
                    
                    previous_subitem_id = subitem_id
                    deadline_str = f" (deadline: {deadline_date.strftime('%b %d')})"
                    print(f"    ✓ Added subitem: {subitem['name'][:60]}... ({subitem['hours']}h){deadline_str}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    ⚠️  Failed to add subitem: {e}")
        except Exception as e:
            print(f"  ❌ Error creating {item_name}: {e}")
    
    print(f"\n✅ Import complete!")
    print(f"  - Items created: {imported_items}")
    print(f"  - Subitems created: {imported_subitems}")
    print(f"\n🔗 View board: https://monday.com/boards/{board_id}")


def update_tasks():
    """Update existing MIS tasks in Spring Plan board"""
    print("🔗 Connecting to Monday.com...")
    importer = MondayImporter(API_TOKEN)
    
    # Find Year 5 Plan board
    print("\n🔍 Finding Year 5 Plan board...")
    year5_board, board_id = find_year5_board(importer)
    if not year5_board:
        print("❌ Year 5 Plan board not found")
        return
    
    print(f"✓ Found board: {year5_board['name']} (ID: {board_id})")
    
    # Find Spring Plan group
    print("\n📋 Finding Spring Plan group...")
    spring_group = get_spring_group(importer, board_id)
    if not spring_group:
        print("❌ Spring Plan group not found")
        return
    print(f"✓ Found group: {spring_group['title']}")
    
    # Find subitems board
    boards = importer.list_boards()
    subitems_board_id = find_subitems_board(boards, board_id)
    
    # Get MIS items
    query = """
    query ($boardId: [ID!], $groupId: String!) {
        boards(ids: $boardId) {
            groups(ids: [$groupId]) {
                items_page {
                    items {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://api.monday.com/v2",
        json={"query": query, "variables": {"boardId": board_id, "groupId": spring_group["id"]}},
        headers=headers
    )
    
    mis1_item = None
    mis2_item = None
    
    if response.status_code == 200:
        data = response.json()
        if not "errors" in data:
            items = data.get("data", {}).get("boards", [])[0].get("groups", [])[0].get("items_page", {}).get("items", [])
            for item in items:
                if item["name"] == "MIS 1":
                    mis1_item = item
                elif item["name"] == "MIS 2":
                    mis2_item = item
    
    if not mis1_item or not mis2_item:
        print("❌ MIS 1 or MIS 2 not found")
        return
    
    print(f"✓ Found MIS 1 (ID: {mis1_item['id']})")
    print(f"✓ Found MIS 2 (ID: {mis2_item['id']})")
    
    # Get subitems
    print("\n📝 Getting subitems...")
    mis1_subitems = get_item_subitems(API_TOKEN, mis1_item["id"])
    mis2_subitems = get_item_subitems(API_TOKEN, mis2_item["id"])
    
    print(f"  MIS 1 has {len(mis1_subitems)} subitems")
    print(f"  MIS 2 has {len(mis2_subitems)} subitems")
    
    # Combine all subitems
    all_subitems = []
    for subitem in mis1_subitems:
        task_def = None
        for task in MIS_TASKS["MIS 1"]:
            if task["name"].lower() in subitem["name"].lower() or subitem["name"].lower() in task["name"].lower():
                task_def = task
                break
        all_subitems.append({
            "id": subitem["id"],
            "name": subitem["name"],
            "hours": task_def["hours"] if task_def else 8
        })
    
    for subitem in mis2_subitems:
        task_def = None
        for task in MIS_TASKS["MIS 2"]:
            if task["name"].lower() in subitem["name"].lower() or subitem["name"].lower() in task["name"].lower():
                task_def = task
                break
        all_subitems.append({
            "id": subitem["id"],
            "name": subitem["name"],
            "hours": task_def["hours"] if task_def else 8
        })
    
    print(f"\n✓ Total subitems to update: {len(all_subitems)}")
    
    # Get columns
    print("\n📊 Getting columns...")
    planned_hours_col, deadline_col, dependency_col = get_columns(importer, subitems_board_id)
    
    # Calculate deadlines
    total_days = (MIS_END_DATE - MIS_START_DATE).days
    days_between = total_days / (len(all_subitems) - 1) if len(all_subitems) > 1 else 0
    
    # Update subitems
    print(f"\n📥 Updating subitems...")
    updated_count = 0
    previous_subitem_id = None
    
    for idx, subitem in enumerate(all_subitems, 1):
        print(f"\n  {idx}. {subitem['name'][:60]}...")
        print(f"     Hours: {subitem['hours']}")
        
        deadline_date = MIS_START_DATE + timedelta(days=days_between * (idx - 1))
        if deadline_date > MIS_END_DATE:
            deadline_date = MIS_END_DATE
        
        update_subitem(importer, subitems_board_id, subitem["id"], subitem, deadline_date,
                      planned_hours_col, deadline_col, dependency_col, previous_subitem_id, verbose=True)
        previous_subitem_id = subitem["id"]
        updated_count += 1
        time.sleep(0.3)
    
    print(f"\n✅ Update complete!")
    print(f"  - Updated {updated_count} subitems")
    print(f"  - Timeline: {MIS_START_DATE.strftime('%B %d, %Y')} to {MIS_END_DATE.strftime('%B %d, %Y')}")


def main():
    """Main function - choose add or update"""
    print("=" * 60)
    print("Spring Plan Automation - Year 5 Plan Board")
    print("=" * 60)
    print("\nWhat would you like to do?")
    print("1. Add new MIS tasks")
    print("2. Add Hardware tasks")
    print("3. Update existing subitems")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        add_tasks(MIS_TASKS, MIS_START_DATE, MIS_END_DATE, "MIS tasks")
    elif choice == "2":
        add_tasks(HARDWARE_TASKS, HARDWARE_START_DATE, HARDWARE_END_DATE, "Hardware tasks")
    elif choice == "3":
        update_tasks()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()

