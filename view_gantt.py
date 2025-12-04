"""
Gantt Chart Viewer for Monday.com Board
Fetches all groups, items, and subitems from the Year 5 Plan board
and visualizes them as a Gantt chart
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import requests
import json
import time
from monday_importer import MondayImporter
from spring_plan import API_TOKEN, find_year5_board, find_subitems_board

def get_subitem_column_values(api_token, subitem_id, board_id, debug=False, debug_findings=False):
    """Get column values for a subitem, including deadline, planned hours, and dependencies"""
    query = """
    query ($itemId: [ID!], $boardId: [ID!]) {
        items(ids: $itemId) {
            id
            name
            column_values {
                id
                type
                text
                value
            }
            linked_items {
                id
                name
            }
        }
        boards(ids: $boardId) {
            columns {
                id
                title
                type
            }
        }
    }
    """
    
    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json"
    }
    
    # Add retry logic for network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.monday.com/v2",
                json={"query": query, "variables": {"itemId": subitem_id, "boardId": board_id}},
                headers=headers,
                timeout=30  # 30 second timeout
            )
            break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                if debug:
                    print(f"         ⏳ Network error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                if debug:
                    print(f"         ❌ Network error after {max_retries} attempts: {e}")
                return None, None, None, []
        except Exception as e:
            if debug:
                print(f"         ❌ Error making request: {e}")
            return None, None, None, []
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            return None, None, None, []
        
        item_data = data.get("data", {}).get("items", [])
        columns_data = data.get("data", {}).get("boards", [{}])[0].get("columns", [])
        
        if not item_data:
            return None, None, None, []
        
        item = item_data[0]
        column_values = item.get("column_values", [])
        linked_items = item.get("linked_items", [])
        
        # Find deadline, hours, and dependencies columns
        deadline_value = None
        hours_value = None
        dependencies = []
        
        # Create a map of column IDs to titles/types
        col_map = {col["id"]: {"title": col.get("title", ""), "type": col.get("type", "")} 
                  for col in columns_data}
        
        # Debug: show available columns on first call - ALWAYS show for first subitem
        if debug and column_values:
            print(f"\n       📋 ALL COLUMNS FOR THIS SUBITEM:")
            print(f"       Total columns found: {len(column_values)}")
            print(f"       " + "="*70)
            for idx, cv in enumerate(column_values, 1):  # Show all columns
                col_id = cv.get('id')
                col_info = col_map.get(col_id, {})
                col_title = col_info.get('title', f'Unknown (ID: {col_id})')
                col_type = col_info.get('type', 'unknown')
                col_text = cv.get('text') or ''
                col_value = cv.get('value') or ''
                
                # Show full details
                print(f"\n       [{idx}] COLUMN: {col_title}")
                print(f"           ID: {col_id}")
                print(f"           Type: {col_type}")
                print(f"           Text: '{col_text}'" if col_text else "           Text: (empty)")
                print(f"           Value (raw): {repr(col_value)}" if col_value else "           Value: (empty)")
                
                # Try to parse value if it's JSON
                if col_value:
                    try:
                        parsed_value = json.loads(col_value) if isinstance(col_value, str) else col_value
                        if isinstance(parsed_value, dict):
                            print(f"           Value (parsed JSON): {json.dumps(parsed_value, indent=14)}")
                        else:
                            print(f"           Value (parsed): {parsed_value}")
                    except:
                        print(f"           Value (not JSON): {str(col_value)[:200]}")
                
                # Highlight important columns
                if "timerange" in col_id.lower() or "timeline" in col_id.lower() or "timeline" in col_title.lower():
                    print(f"           ⭐ THIS IS A TIMELINE COLUMN")
                if "dependency" in col_id.lower() or "depend" in col_id.lower() or "dependency" in col_title.lower():
                    print(f"           ⭐ THIS IS A DEPENDENCY COLUMN")
                if "numeric" in col_id.lower() and (col_text and col_text.isdigit() or col_value):
                    print(f"           ⭐ THIS MIGHT BE PLANNED HOURS (numeric with value)")
                if "hour" in col_id.lower() or "hour" in col_title.lower():
                    print(f"           ⭐ THIS IS AN HOUR COLUMN")
            
            print(f"       " + "="*70)
        
        for col_val in column_values:
            col_id = col_val.get("id")
            col_info = col_map.get(col_id, {})
            col_type = col_info.get("type", "").lower()
            col_title = col_info.get("title", "").lower()
            col_text = col_val.get("text") or ""
            col_value = col_val.get("value") or ""
            
            # Detect timerange/timeline by ID pattern if type is unknown
            if col_type == "unknown" and col_id:
                if "timerange" in col_id.lower() or "timeline" in col_id.lower():
                    col_type = "timerange"
                elif "dependency" in col_id.lower() or "depend" in col_id.lower():
                    col_type = "dependency"
                elif "hour" in col_id.lower() or "time" in col_id.lower():
                    col_type = "hour"
            
            # Check for deadline/timeline - SIMPLE VERSION
            if not deadline_value and "timerange" in col_id.lower():
                try:
                    if col_value:
                        timeline_data = json.loads(col_value) if isinstance(col_value, str) else col_value
                        if isinstance(timeline_data, dict):
                            if "to" in timeline_data and timeline_data["to"]:
                                deadline_value = datetime.strptime(timeline_data["to"], "%Y-%m-%d")
                            elif "from" in timeline_data and timeline_data["from"]:
                                deadline_value = datetime.strptime(timeline_data["from"], "%Y-%m-%d")
                    if not deadline_value and col_text and " - " in col_text:
                        date_parts = col_text.split(" - ")
                        if len(date_parts) == 2:
                            deadline_value = datetime.strptime(date_parts[1].strip(), "%Y-%m-%d")
                except:
                    pass
            
            # Check for date type columns (deadline column) - SIMPLE VERSION
            if not deadline_value and (col_type == "date" or "deadline" in col_title or "due" in col_title):
                try:
                    if col_value:
                        date_data = json.loads(col_value) if isinstance(col_value, str) else col_value
                        if isinstance(date_data, dict) and "date" in date_data:
                            deadline_value = datetime.strptime(date_data["date"], "%Y-%m-%d")
                    if not deadline_value and col_text:
                        import re
                        matches = re.findall(r'(\d{4}-\d{2}-\d{2})', col_text)
                        if matches:
                            deadline_value = datetime.strptime(matches[0], "%Y-%m-%d")
                except:
                    pass
            
            # Check for planned hours - SIMPLE: check numeric columns with values
            if not hours_value and "numeric" in col_id.lower() and col_value:
                try:
                    hour_str = json.loads(col_value) if isinstance(col_value, str) else str(col_value)
                    hour_str_clean = hour_str.replace('"', '').replace("'", "").strip()
                    if hour_str_clean and hour_str_clean != "null":
                        hours_value = float(hour_str_clean)
                except:
                    # Try text as fallback
                    if col_text and col_text.isdigit():
                        try:
                            hours_value = float(col_text)
                        except:
                            pass
            
            # Check for dependencies - SIMPLE: just check if dependency in ID
            if "dependency" in col_id.lower():
                try:
                    # Try value first
                    if col_value:
                        dep_data = json.loads(col_value) if isinstance(col_value, str) else col_value
                        if isinstance(dep_data, dict):
                            item_ids = dep_data.get("item_ids", []) or dep_data.get("pulse_ids", [])
                            dependencies = [str(dep_id) for dep_id in item_ids] if item_ids else []
                    # Fallback to linked_items
                    if not dependencies and linked_items:
                        dependencies = [str(linked_item.get("id")) for linked_item in linked_items if linked_item.get("id")]
                except:
                    pass
        
        return deadline_value, hours_value, item.get("name", ""), dependencies
    
    return None, None, None, []


def get_all_groups_data(api_token, board_id, subitems_board_id, test_mode=False, filter_group_name=None):
    """Get all groups, items, and subitems with their deadlines and hours"""
    query = """
    query ($boardId: [ID!]) {
        boards(ids: $boardId) {
            groups {
                id
                title
                items_page(limit: 500) {
                    items {
                        id
                        name
                        subitems {
                            id
                            name
                        }
                    }
                }
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
        json={"query": query, "variables": {"boardId": board_id}},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Error fetching board data: {response.text}")
        return []
    
    data = response.json()
    if "errors" in data:
        print(f"❌ API Error: {data['errors']}")
        return []
    
    groups_data = []
    boards_data = data.get("data", {}).get("boards", [])
    if not boards_data:
        return []
    
    groups = boards_data[0].get("groups", [])
    
    # Filter by group name if specified
    if filter_group_name:
        original_count = len(groups)
        groups = [g for g in groups if filter_group_name.lower() in g.get("title", "").lower()]
        if groups:
            print(f"\n🔍 Filtering groups: Found {len(groups)} group(s) matching '{filter_group_name}' (out of {original_count} total)")
        else:
            print(f"\n⚠️  No groups found matching '{filter_group_name}'")
            print(f"   Available groups: {[g.get('title', 'Unknown') for g in boards_data[0].get('groups', [])]}")
            return []
    # In test mode, only process first group
    elif test_mode:
        groups = groups[:1]
        print(f"\n🧪 TEST MODE: Processing only first group")
    
    print(f"\n📊 Found {len(groups)} groups on the board")
    
    for group_idx, group in enumerate(groups, 1):
        group_title = group.get("title", "Unknown")
        items = group.get("items_page", {}).get("items", [])
        
        print(f"  {group_idx}. {group_title}: {len(items)} items")
        
        group_tasks = []
        
        total_subitems = sum(len(item.get("subitems", [])) for item in items)
        processed = 0
        found_deadlines = 0
        missing_deadlines = 0
        
        for item in items:
            item_name = item.get("name", "Unknown")
            item_id = item.get("id")
            subitems = item.get("subitems", [])
            
            for subitem in subitems:
                subitem_id = subitem.get("id")
                subitem_name = subitem.get("name", "Unknown")
                processed += 1
                
                # Special debug: Show ALL columns for first subitem in detail
                if processed == 1:
                    print(f"\n     🔍 DETAILED COLUMN DEBUG for first subitem:")
                    print(f"        Subitem: {subitem_name}")
                    print(f"        Subitem ID: {subitem_id}")
                    print(f"        Item: {item_name}")
                    print(f"        Item ID: {item_id}")
                
                # Show progress every 10 items
                if processed % 10 == 0:
                    print(f"     Processing: {processed}/{total_subitems} subitems...", end='\r')
                
                # Get column values for this subitem (debug columns on first subitem only, but show findings for all)
                debug_cols = (processed == 1)  # Show full column list only for first
                deadline, hours, _, dependencies = get_subitem_column_values(api_token, subitem_id, subitems_board_id, 
                                                                              debug=debug_cols, debug_findings=True)
                
                # Debug output for deadline, hours, and dependencies detection
                if deadline:
                    deadline_str = deadline.strftime("%Y-%m-%d")
                    hours_str = f"{int(hours)}h" if hours else "0h"
                    deps_str = f" | deps: {len(dependencies)}" if dependencies else ""
                    print(f"     ✓ [{processed}/{total_subitems}] Found deadline: {deadline_str} | {hours_str}{deps_str} | {subitem_name[:50]}")
                    found_deadlines += 1
                else:
                    print(f"     ✗ [{processed}/{total_subitems}] NO DEADLINE found for: {subitem_name[:50]}")
                    missing_deadlines += 1
                
                # If no deadline found, skip this subitem
                if not deadline:
                    continue
                
                # Ensure hours is a number
                if hours is None:
                    hours = 0
                
                # Estimate start date (deadline - days based on hours, assuming 8h/day)
                if hours and hours > 0:
                    days_needed = max(1, int(hours / 8))
                    start_date = deadline - timedelta(days=days_needed)
                else:
                    start_date = deadline - timedelta(days=1)
                
                group_tasks.append({
                    "group": group_title,
                    "item": item_name,
                    "task": subitem_name,
                    "start": start_date,
                    "end": deadline,
                    "hours": hours or 0,
                    "subitem_id": subitem_id,
                    "dependencies": dependencies  # List of dependent subitem IDs
                })
        
        if total_subitems > 0:
            print(f"     Processed {processed} subitems" + " " * 20)  # Clear progress line
        
        # Summary for this group
        print(f"     📊 Summary: {found_deadlines} with deadlines, {missing_deadlines} without deadlines")
        
        if group_tasks:
            groups_data.append({
                "group_title": group_title,
                "tasks": group_tasks
            })
            print(f"     → {len(group_tasks)} subitems added to chart")
        else:
            print(f"     ⚠️  No subitems with deadlines in this group")
    
    return groups_data


def calculate_critical_path(tasks):
    """
    Calculate critical path for a group of tasks using longest path algorithm.
    Returns a set of subitem_ids that are on the critical path.
    """
    if not tasks:
        return set()
    
    # Create mapping from subitem_id to task index
    task_map = {task["subitem_id"]: idx for idx, task in enumerate(tasks)}
    
    # Build dependency graph (adjacency list)
    # graph[task_idx] = list of tasks that depend on this task (successors)
    graph = {i: [] for i in range(len(tasks))}
    reverse_graph = {i: [] for i in range(len(tasks))}  # For backward pass
    in_degree = {i: 0 for i in range(len(tasks))}
    
    has_dependencies = False
    for idx, task in enumerate(tasks):
        deps = task.get("dependencies", [])
        for dep_id in deps:
            if dep_id in task_map:
                dep_idx = task_map[dep_id]
                graph[dep_idx].append(idx)  # dep_idx -> idx (dependency -> dependent)
                reverse_graph[idx].append(dep_idx)  # For backward pass
                in_degree[idx] += 1
                has_dependencies = True
    
    # If no dependencies, return empty set (all tasks are independent)
    if not has_dependencies:
        return set()
    
    # Calculate duration for each task (use hours if available, otherwise days)
    durations = {}
    for idx, task in enumerate(tasks):
        hours = task.get("hours", 0)
        if hours and hours > 0:
            # Convert hours to days (assuming 8 hours per day)
            duration = max(1, int(hours / 8))
        else:
            # Fallback to calendar days
            duration = (task["end"] - task["start"]).days + 1
        durations[idx] = max(1, duration)
    
    # Topological sort
    queue = [i for i in range(len(tasks)) if in_degree[i] == 0]
    topo_order = []
    in_degree_copy = in_degree.copy()
    
    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for neighbor in graph[node]:
            in_degree_copy[neighbor] -= 1
            if in_degree_copy[neighbor] == 0:
                queue.append(neighbor)
    
    # If we couldn't process all nodes, there might be cycles - skip critical path
    if len(topo_order) < len(tasks):
        return set()
    
    # Calculate earliest start times (forward pass)
    earliest_start = {i: 0 for i in range(len(tasks))}
    for node in topo_order:
        for neighbor in graph[node]:
            earliest_start[neighbor] = max(
                earliest_start[neighbor],
                earliest_start[node] + durations[node]
            )
    
    # Find the longest path (project duration)
    max_duration = max(earliest_start[i] + durations[i] for i in range(len(tasks)))
    
    # Calculate latest start times (backward pass)
    latest_start = {i: max_duration - durations[i] for i in range(len(tasks))}
    
    # Process in reverse topological order
    for node in reversed(topo_order):
        for predecessor in reverse_graph[node]:
            latest_start[predecessor] = min(
                latest_start[predecessor],
                latest_start[node] - durations[predecessor]
            )
    
    # Critical path: tasks where earliest_start == latest_start (zero slack)
    critical_path = set()
    for idx in range(len(tasks)):
        slack = latest_start[idx] - earliest_start[idx]
        if abs(slack) < 0.01:  # Account for floating point (zero slack = critical)
            critical_path.add(tasks[idx]["subitem_id"])
    
    return critical_path


def create_gantt_chart(test_mode=False, filter_group=None):
    """Create and display Gantt chart from Monday.com board data"""
    print("=" * 60)
    print("Monday.com Gantt Chart Viewer")
    if test_mode:
        print("🧪 TEST MODE: Processing only first group")
    if filter_group:
        print(f"🔍 FILTER MODE: Processing group matching '{filter_group}'")
    print("=" * 60)
    
    print("\n🔗 Connecting to Monday.com...")
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
    
    # Get all groups data
    print("\n📥 Fetching all groups, items, and subitems...")
    groups_data = get_all_groups_data(API_TOKEN, board_id, subitems_board_id, test_mode=test_mode, filter_group_name=filter_group)
    
    if not groups_data:
        print("❌ No data found or no subitems with deadlines")
        return
    
    # Flatten all tasks
    all_tasks = []
    for group_data in groups_data:
        all_tasks.extend(group_data["tasks"])
    
    if not all_tasks:
        print("❌ No tasks with deadlines found")
        return
    
    print(f"\n✅ Found {len(all_tasks)} total subitems with deadlines across {len(groups_data)} groups")
    
    # Calculate critical path for each group
    print("\n🔍 Calculating critical paths for each group...")
    all_critical_path = set()
    total_dependencies = 0
    for group_data in groups_data:
        group_title = group_data["group_title"]
        tasks = group_data["tasks"]
        
        # Count dependencies in this group
        group_deps = sum(len(t.get("dependencies", [])) for t in tasks)
        total_dependencies += group_deps
        
        if group_deps > 0:
            print(f"   {group_title}: {group_deps} dependencies found, calculating critical path...")
            critical_path = calculate_critical_path(tasks)
            all_critical_path.update(critical_path)
            if critical_path:
                print(f"      ✓ {len(critical_path)} tasks on critical path")
            else:
                print(f"      ⚠️  No critical path found (may have cycles or no connected dependencies)")
        else:
            print(f"   {group_title}: No dependencies found, all tasks independent")
    
    print(f"   Total dependencies: {total_dependencies}")
    print(f"   Total critical path tasks: {len(all_critical_path)}")
    
    # Create figure - make it much larger for better visibility
    # Calculate optimal size: more space per task for readability
    fig_height = max(16, len(all_tasks) * 0.4)  # Increased from 0.25 to 0.4
    fig_width = 24  # Increased from 20 to 24
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor('white')
    
    # Generate colors for groups
    import matplotlib.cm as cm
    import numpy as np
    colors = cm.get_cmap('tab20', len(groups_data))
    group_colors = {group_data["group_title"]: colors(i) 
                   for i, group_data in enumerate(groups_data)}
    
    # Create mapping from subitem_id to y_position for drawing arrows
    subitem_to_ypos = {}
    subitem_to_task = {}
    
    # Plot bars
    y_position = 0
    y_labels = []
    y_positions = []
    
    for group_data in groups_data:
        group_title = group_data["group_title"]
        tasks = group_data["tasks"]
        
        # Sort tasks by start date
        tasks.sort(key=lambda x: x["start"])
        
        for task in tasks:
            # Store mapping for arrow drawing
            subitem_to_ypos[task["subitem_id"]] = y_position
            subitem_to_task[task["subitem_id"]] = task
            start = task["start"]
            end = task["end"]
            duration = (end - start).days + 1
            
            color = group_colors.get(group_title, "#95A5A6")
            is_critical = task["subitem_id"] in all_critical_path
            
            # Critical path tasks: brighter color, thicker border
            if is_critical:
                # Make critical path tasks more vibrant
                edge_color = 'red'
                edge_width = 3.0  # Thicker for large display
                alpha = 0.9
            else:
                edge_color = 'black'
                edge_width = 0.8  # Slightly thicker for visibility
                alpha = 0.7
            
            # Larger bar height for better visibility
            bar_height = 0.9
            ax.barh(y_position, duration, left=mdates.date2num(start), 
                   height=bar_height, color=color, alpha=alpha, 
                   edgecolor=edge_color, linewidth=edge_width)
            
            # Add hours label if available (larger font for visibility)
            if task["hours"] > 0:
                mid_date = start + (end - start) / 2
                label_color = 'white' if is_critical else 'black'
                ax.text(mdates.date2num(mid_date), y_position, 
                       f"{int(task['hours'])}h", ha='center', va='center', 
                       fontsize=9, fontweight='bold', color=label_color)
            
            # Create label: Group | Item: Task [CRITICAL] (longer for large display)
            label = f"{group_title} | {task['item']}: {task['task'][:50]}"
            if len(task['task']) > 50:
                label += "..."
            if is_critical:
                label += " [CRITICAL]"
            y_labels.append(label)
            y_positions.append(y_position)
            
            y_position += 1
    
    # Set y-axis (larger font for readability)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=9)
    ax.invert_yaxis()
    
    # Format x-axis as dates (larger font)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=9)
    
    # Set labels and title (larger for visibility)
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tasks (Group | Item: Task)', fontsize=12, fontweight='bold')
    ax.set_title('Year 5 Plan - Complete Gantt Chart with Critical Path (All Groups)', 
                fontsize=18, fontweight='bold', pad=25)
    
    # Draw dependency arrows (after bars are drawn)
    print("\n🔗 Drawing dependency arrows...")
    arrow_count = 0
    for group_data in groups_data:
        tasks = group_data["tasks"]
        for task in tasks:
            deps = task.get("dependencies", [])
            if deps:
                task_y = subitem_to_ypos.get(task["subitem_id"])
                if task_y is not None:
                    task_start = mdates.date2num(task["start"])
                    
                    for dep_id in deps:
                        dep_y = subitem_to_ypos.get(dep_id)
                        if dep_y is not None:
                            dep_task = subitem_to_task.get(dep_id)
                            if dep_task:
                                dep_end = mdates.date2num(dep_task["end"])
                                
                                # Draw arrow from end of dependency to start of task
                                # Arrow from (dep_end, dep_y) to (task_start, task_y)
                                ax.annotate('', 
                                           xy=(task_start, task_y),
                                           xytext=(dep_end, dep_y),
                                           arrowprops=dict(arrowstyle='->', 
                                                          lw=2, 
                                                          color='blue',
                                                          alpha=0.7,
                                                          connectionstyle='arc3,rad=0.2'))
                                arrow_count += 1
    
    if arrow_count > 0:
        print(f"   ✓ Drew {arrow_count} dependency arrows")
    else:
        print(f"   ⚠️  No dependencies found to draw arrows")
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', axis='x')
    ax.set_axisbelow(True)
    
    # Add legend for groups and critical path (larger font)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [Patch(facecolor=group_colors[group_data["group_title"]], 
                            alpha=0.7, label=group_data["group_title"]) 
                      for group_data in groups_data]
    # Add critical path indicator
    legend_elements.append(Line2D([0], [0], color='red', lw=3, 
                                   label='Critical Path', alpha=0.9))
    # Add dependency arrows indicator
    legend_elements.append(Line2D([0], [0], color='blue', lw=2, 
                                   label='Dependencies', alpha=0.7, linestyle='-'))
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
             bbox_to_anchor=(1.02, 1), framealpha=0.95)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout to make room for legend and ensure everything fits
    plt.tight_layout()
    plt.subplots_adjust(right=0.82, top=0.95, bottom=0.08)
    
    # Show summary
    print(f"\n📊 Gantt Chart Summary:")
    print(f"   Total groups: {len(groups_data)}")
    print(f"   Total tasks: {len(all_tasks)}")
    total_hours = sum(t["hours"] for t in all_tasks)
    print(f"   Total hours: {int(total_hours)}")
    
    print(f"\n   Tasks by group:")
    for group_data in groups_data:
        group_hours = sum(t["hours"] for t in group_data["tasks"])
        critical_count = sum(1 for t in group_data["tasks"] if t["subitem_id"] in all_critical_path)
        print(f"     {group_data['group_title']}: {len(group_data['tasks'])} tasks ({critical_count} critical), {int(group_hours)} hours")
    
    # Show plot
    print("\n📊 Displaying Gantt chart...")
    plt.show(block=False)  # Non-blocking so we can save immediately
    
    # Automatically save the chart
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as high-resolution PNG
    png_filename = f"year5_plan_gantt_{timestamp}.png"
    print(f"\n💾 Saving high-resolution PNG...")
    plt.savefig(png_filename, dpi=300, bbox_inches='tight', facecolor='white', 
                edgecolor='none', format='png')
    print(f"✅ Saved as: {png_filename}")
    
    # Also save as PDF for vector quality
    pdf_filename = f"year5_plan_gantt_{timestamp}.pdf"
    print(f"💾 Saving PDF (vector format)...")
    plt.savefig(pdf_filename, bbox_inches='tight', facecolor='white', 
                edgecolor='none', format='pdf')
    print(f"✅ Saved as: {pdf_filename}")
    
    # Ask if user wants SVG (optional, for editing)
    save_svg = input("\n💾 Also save as SVG (editable vector format)? (yes/no): ").strip().lower()
    if save_svg in ['yes', 'y']:
        svg_filename = f"year5_plan_gantt_{timestamp}.svg"
        plt.savefig(svg_filename, bbox_inches='tight', facecolor='white', 
                    edgecolor='none', format='svg')
        print(f"✅ Saved as: {svg_filename}")
    
    print(f"\n📁 Files saved in current directory:")
    print(f"   - {png_filename} (high-res image)")
    print(f"   - {pdf_filename} (vector format)")
    if save_svg in ['yes', 'y']:
        print(f"   - {svg_filename} (editable vector)")
    
    # Keep plot open until user closes it
    input("\nPress Enter to close the chart window...")
    plt.close()


if __name__ == "__main__":
    import sys
    
    # Check for test mode flag
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    # Check for group filter
    filter_group = None
    if "--group" in sys.argv:
        idx = sys.argv.index("--group")
        if idx + 1 < len(sys.argv):
            filter_group = sys.argv[idx + 1]
    elif "-g" in sys.argv:
        idx = sys.argv.index("-g")
        if idx + 1 < len(sys.argv):
            filter_group = sys.argv[idx + 1]
    
    try:
        create_gantt_chart(test_mode=test_mode, filter_group=filter_group)
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install it with: pip install matplotlib")
    except Exception as e:
        print(f"❌ Error creating Gantt chart: {e}")
        import traceback
        traceback.print_exc()
