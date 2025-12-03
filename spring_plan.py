"""
Spring Plan Automation - Add tasks to Year 5 Plan board
Always uses Year 5 Plan board with Spring Plan group
Automatically sets planned hours, deadlines, and dependencies
"""

import time
import json
import requests
from datetime import datetime, timedelta
from monday_importer import MondayImporter

# API Token - Always the same
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjU5Mjk4NDI1NSwiYWFpIjoxMSwidWlkIjo2NTcyMTMxNCwiaWFkIjoiMjAyNS0xMi0wMlQxNzoyMTo1MC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjQ0NDY1NTQsInJnbiI6InVzZTEifQ.oHP8gGwt-5fDSeChJfE_uy3jJcuqopgyZ1lGgcFmL40"

# ============================================================================
# TASK DEFINITIONS - Organized by date ranges
# ============================================================================
# Date ranges:
# - MIS 1, MIS 2, Mathworks: Jan 1 to Feb 1, 2026
# - CDE/R: Jan 1 to April 1, 2026
# - SRS: Jan 1 to April 15, 2026
# - Rest: Jan 1 to May 15, 2026

# Tasks with Jan 1 to Feb 1, 2026 deadline
TASKS_FEB1 = {
    "MIS 1": [
        {"name": "Onboarding with details of the task and the purpose of the challenge", "hours": 10},
        {"name": "Familiarization with current progress", "hours": 10},
        {"name": "Make a presentation about summer competition goals and plans and rehearsing it", "hours": 15},
        {"name": "Refine solution with technical and business details", "hours": 50},
        {"name": "Determine primary target for product of Ride Shares, Personal, or Both autonomous vehicles", "hours": 10},
        {"name": "Research impacts and stakeholders of the topic", "hours": 20},
        {"name": "Research how topic will be integrated into an Autonomous Vehicle", "hours": 20},
        {"name": "Research other Direct/Indirect companies/products with similar products to our topic", "hours": 15},
        {"name": "Benchmark how our product is different and unique", "hours": 10},
        {"name": "Research challenges posed by our solution/topic", "hours": 10},
        {"name": "Develop an engaging elevator pitch for the topic", "hours": 20},
        {"name": "Develop Technical prototypes (CAD/Simulations/system diagrams)", "hours": 15},
        {"name": "Research cost of implementation", "hours": 15},
        {"name": "Research estimated revenue, increase in customer experience, and Key objectives reached", "hours": 20},
        {"name": "Research any legal restrictions with utilizing product and fees associated with Topic", "hours": 15},
        {"name": "Develop presentation slides with engaging visuals and technical and business depth", "hours": 20},
        {"name": "Polishing and Practicing presentation slides", "hours": 15},
    ],
    "MIS 2": [
        {"name": "Onboarding with details of the rubric and purpose of the presentation", "hours": 10},
        {"name": "Understand the developed presentation; key points of slides, details on MVP, self-certification plan, and comparisons", "hours": 30},
        {"name": "Refine talking points on slides and practice presentation", "hours": 40},
    ],
    "Mathworks": [
        {"name": "Onboarding the simulation stack and any required MathWorks knowledge", "hours": 18},
        {"name": "Practicing presentation", "hours": 5},
        {"name": "Integrating 3 RoadRunner scenarios with CI/CD", "hours": 30},
        {"name": "Create a script that loads scenario parameters that failed a test are rerun", "hours": 20},
        {"name": "Integrate randomness of scenario parameters into simulation scenarios", "hours": 15},
    ],
}

# Tasks with Jan 1 to April 1, 2026 deadline
TASKS_APR1 = {
}

# Tasks with Jan 1 to April 15, 2026 deadline
TASKS_APR15 = {
    "SRS": [
        {"name": "Address any feedback from judges on Year 5 SRS Draft", "hours": 25},
        {"name": "Create a more thorough and detailed safety plan/checklist - Document the frequency of inspections that are done and what systems need to be checked - Create a paper trail for safety inspections (weekly/ biweekly/ monthly checks) - Verify requirements through routine inspections/checks so that they can used as evidence in the future", "hours": 30},
        {"name": "Revise Open Source Software disclosure table - Verify that all software currently entered is still in use - Consult team leaders and add any new open source software being used", "hours": 10},
        {"name": "Verify with Perception, VFOV, HFOV, and detection range metrics - To account for new pieces of information being added to the perception stack, ensure the metrics being used in the perception functional requirements are correct", "hours": 10},
        {"name": "Review of testing requirements - Ensure functional requirements have measurable test requirements - Also identify the testing method for each functional requirement (e.g. On Car, In Sim, etc.)", "hours": 40},
        {"name": "Test functional requirements and document the results - Attend track days, test SRS functional requirements with the appropriate technical department, and document the results of each test - When documenting the results, leave comments on how the test was conducted and an explanation of its success or failure", "hours": 80},
    ],
    "SSTR": [
        {"name": "Review safety artifacts from Year 1 – 4", "hours": 20},
        {"name": "Run Safety Case tests", "hours": 80},
        {"name": "Run any previously failed RTM tests - Focus on FAILED tests. However if time permits, circle back and test previously PASSED tests - Make sure to take notes and comments for every test run", "hours": 90},
        {"name": "Develop Assessments of technical system safety requirements", "hours": 10},
        {"name": "Develop Assessments of any identified/reported system or issues", "hours": 20},
        {"name": "Conclusion", "hours": 10},
        {"name": "Final Safety Case Presentation Dev", "hours": 0},
    ],
}

# Tasks with Jan 1 to May 15, 2026 deadline
TASKS_MAY15 = {
    "BOR - Environmental Challenges": [
        {"name": "Develop an image state classifier to publish a scored environment conditions (normal, fog, glare) with >= 90% accuracy", "hours": 20},
        {"name": "Develop system to switch between FLIR/LiDAR to FLIR/Stereo in foggy environment conditions", "hours": 15},
        {"name": "Tune Lane Line model to be within .2 meters in sandy and shadowy conditions", "hours": 40},
        {"name": "Tune sensor fusion to detect objects within 20 meters in foggy conditions using stereo camera", "hours": 10},
        {"name": "Calibrate cameras and modify housing to detect all surrounding objects with glare on the camera without slowing FPS rate", "hours": 15},
        {"name": "Investigate use dehazing algorithm to reduce the noise from fog in images", "hours": 10},
        {"name": "Investigate solution to detect and handle windshield glare from interior mounted stereo camera", "hours": 8},
        {"name": "Implement solution to detect and handle windshield glare from interior mounted stereo camera", "hours": 10},
    ],
    "BOR - Sensor Fusion": [
        {"name": "Correct depth fusion script to output the correct distances for detections using LiDAR within +- 0.5m", "hours": 30},
        {"name": "Integrate radar to get heading of objects in perception msg", "hours": 15},
        {"name": "Integrate radar to get the distances of objects (close to the car) below the LiDAR point cloud", "hours": 15},
        {"name": "Implement stitching to use all flir cameras to create a wider FOV in a single image as required for competition standards", "hours": 15},
        {"name": "Implement LiDAR clustering to learn the size and shape of detections", "hours": 20},
    ],
    "Controls": [
        {"name": "Control State Machine Rewrite", "hours": 0},
    ],
    "Sensor Decider": [
        {"name": "Integration of HDMaps into sensor decider", "hours": 10},
        {"name": "Implementation of changing lanes to move around static objects", "hours": 15},
        {"name": "Implementation for Turn Only, Do not turn, and Do not Enter into sensor decider", "hours": 15},
        {"name": "Implementation of Field Of View (FOV) into sensor decider", "hours": 10},
        {"name": "Create sensor decider Queue/fix current logic to interpret incoming objects in this order: Navigation of dynamic obstacles in lane, static objects in lane, light states and railroad gate, yield and mph implementation", "hours": 10},
        {"name": "Fix logic of sensor decider detections to be by object track id instead of object type and cooldown", "hours": 2},
        {"name": "Fix logic of sensor decider detections to use object confidence filtering", "hours": 1},
        {"name": "Implement balloon car following logic", "hours": 5},
        {"name": "Implement parking spot logic", "hours": 10},
        {"name": "Implement logic for foggy conditions when radar detects dynamic objects that flir cameras dont pick up for accurate navigation around unseen objects", "hours": 8},
        {"name": "Change confidence levels for foggy and glare condition detections", "hours": 1},
        {"name": "Integration of lane line detections into sensor decider", "hours": 7},
        {"name": "Incorporate radar object velocity with perception_msg to get object heading and integrate with sensor decider", "hours": 10},
        {"name": "Implementation of right turn on red", "hours": 7},
    ],
    "DYOC - HDMaps": [
        {"name": "Set up HDMaps development environment (qgis, pgadmin, etc.) and successfully run and visualize PathPlanner", "hours": 5},
        {"name": "Review PathPlanner architecture and A* implementation", "hours": 5},
        {"name": "Understand MCity and DYOC database schema", "hours": 5},
        {"name": "Add launch files with presets for different PathPlanner modes", "hours": 3},
        {"name": "Update PathPlanner to prefer earliest lane change in route generation", "hours": 10},
        {"name": "Disallow PathPlanner from crossing solid white lines for lane change", "hours": 10},
        {"name": "PathPlanner should depend on enu_pos rather than bestpos for positioning", "hours": 2},
        {"name": "Add health check service for PathPlanner node status", "hours": 3},
        {"name": "Allow PathPlanner to generate a path with an arbitrary start point that is not on the graph, depending on how lane change on obstacle is implemented", "hours": 10},
        {"name": "Fix when PathPlanner can't find a path and regenerates twice, it won't stop trying", "hours": 2},
        {"name": "Fix when vehicle start point can't be found, PathPlanner gets weird", "hours": 2},
        {"name": "Fix and improve PathPlanner's graph/trajectory and export paths", "hours": 1},
        {"name": "Improve PathPlanner logging and error messages", "hours": 3},
        {"name": "Integrate Perception's blockage detection", "hours": 10},
        {"name": "Implement graph modification and node removal on Perception blockage detection", "hours": 35},
        {"name": "Update database script to add the new sign and object data", "hours": 2},
        {"name": "Modify corners to ensure it meets road standards and is not almost 90 degrees", "hours": 15},
        {"name": "Modify the highway points to shift slightly to the right to properly center the lane", "hours": 5},
        {"name": "Fix duplicate and missing points from DYOC database", "hours": 5},
        {"name": "Figure out a way to verify optimality and implementation correctness of A* in PathPlanner with a small testing suite", "hours": 15},
        {"name": "Investigate possible DDS overload when running GNC and Perception stack (or the whole car stack for that matter)", "hours": 2},
    ],
    "DYOC - Object Detection Model Rework": [
        {"name": "Enhance OD model to achieve detection of objects within 40 meters", "hours": 30},
        {"name": "Implement color correcting in image preprocessing stage to enhance OD detections", "hours": 8},
        {"name": "Improve pedestrian detections with OD model", "hours": 8},
        {"name": "Improve deer detections with OD model", "hours": 6},
        {"name": "Improve orange road closed sign detections with OD model", "hours": 6},
        {"name": "Add CUDA OpenCV package version to car", "hours": 1},
        {"name": "Optimize image preprocessing to run on GPU using CUDA OpenCV package", "hours": 10},
    ],
    "Localization - GNC Localization": [
        {"name": "Understand current localization solution with INS and previous attempts of localization", "hours": 5},
        {"name": "Review robot_localization EKF fundamentals as well as REP-103 and REP-105 for coordinate frames", "hours": 5},
        {"name": "Review Perception's lane detection output", "hours": 5},
        {"name": "Understand centerline representation in HDMaps", "hours": 5},
        {"name": "Investigate and determine vehicle's absolute center", "hours": 10},
        {"name": "Implement and properly test first iteration of centerline localization", "hours": 30},
        {"name": "Iterate on centerline localization (handle possible dropout/failures, intersections, and confidence thresholds, etc.)", "hours": 25},
        {"name": "Implement and test wheel-speed only EKF", "hours": 20},
        {"name": "Implement and test INS only EKF", "hours": 20},
        {"name": "Implement and test a fusion of INS velocity and wheel-speed", "hours": 35},
        {"name": "Implement and test a fusion of the new odometry with centerline localization", "hours": 40},
        {"name": "Create a local map of Perception detection to localize against", "hours": 15},
        {"name": "Implement and properly test first iteration of landmark localization", "hours": 30},
        {"name": "Iterate on landmark localization", "hours": 25},
    ],
    "Object State Classification": [
        {"name": "Add capability to id_mapper to detect and map detection id for railroad gate open/closed", "hours": 6},
        {"name": "Add capability to id_mapper to detect and map detection id for flashing traffic light states", "hours": 6},
    ],
    "HMI": [
        {"name": "Implement dynamic mapping replacing static map image (LTI) - Show the car current location - Route visualization – Highlighted path after waypoints selection - Add every object detected by the car through perception on the map", "hours": 40},
        {"name": "Implement dynamic MCity map - Similar to task 1 but for MCity instead of LTI", "hours": 30},
        {"name": "Upcoming maneuver - Display the upcoming maneuver whenever approaching it - Distance countdown to reach the maneuver", "hours": 20},
        {"name": "Install Git on Jetson - Enable Git on Jetson as currently we just copy the frontend file over manually", "hours": 10},
        {"name": "Rework Final Point/Parking Brake function to allow for multiple calls - Currently, GUI becomes not interactable after pressing the button - Implement Final Point button with Popen or threading to allow for multiple calls", "hours": 5},
        {"name": "Clean-up frontend and backend code before competition", "hours": 2},
    ],
    "Hardware - AVT BOLT VINYL": [
        {"name": "Taking the stickers out - Record the Bolt before to determine where stickers are currently placed - Peel the stickers out of the chassis", "hours": 2},
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
    "Hardware - Ventilation System": [
        {"name": "Implementation of fan and duct with OEM Sill Plate", "hours": 20},
        {"name": "Implementation and creating of an electrical circuit, electrical routing, and optimized fan speed - speed varied via voltage input", "hours": 20},
    ],
    "Hardware - ZED 2i Mounting": [
        {"name": "Implementation of ZED 2i - internal", "hours": 10},
        {"name": "Cable routing", "hours": 5},
        {"name": "Mounting bracketry", "hours": 5},
    ],
    "Hardware - Old Comp. Cars": [
        {"name": "Continuation of scrapping/salvaging", "hours": 20},
    ],
    "Hardware - Rear rack New Arrangement": [
        {"name": "Run FEA and CFD simulation to support the reason for the new arrangement", "hours": 20},
        {"name": "Working on the bottom shelf arrangement if necessary", "hours": 15},
        {"name": "Physically executing the new arrangement on the new bought plywood", "hours": 15},
    ],
    "Hardware - Cable Management": [
        {"name": "Working on finding the best possible way for the hardware cable routing", "hours": 20},
    ],
    "Hardware - Create new wiring Diagrams in Rapid Harness": [
        {"name": "Add all components that are currently part of our system", "hours": 20},
        {"name": "Update layout based on new rear rack layout", "hours": 10},
    ],
    "Hardware - Simulink Design for Rear rack": [
        {"name": "Update Simulation to better represent our sine inverter", "hours": 10},
        {"name": "Add loads to our outputs to test load stress", "hours": 10},
        {"name": "Integrate Power system design into overall Simulink Architecture, including sensors", "hours": 50},
    ],
    "Hardware - Blue light system": [
        {"name": "Debug frequency problem of blue lights during manual driving", "hours": 20},
    ],
    "Hardware - Draw.IO Flowchart": [
        {"name": "Add additional depth to our design structure and overall architecture", "hours": 20},
    ],
    "Hardware - Waterproofing cable": [
        {"name": "Decide whether placing the sensors - Zed 2i Mount as an example - would be a better idea than placing them inside the car", "hours": 20},
        {"name": "If yes, work on finding ways on how to waterproof the sensors and the cables", "hours": 30},
    ],
    "Hardware - Integrate V2X with other sensor data": [
        {"name": "Communicate with perception to integrate V2X data into the perception stack to help detect stop lights", "hours": 30},
        {"name": "Add the code into launch file", "hours": 5},
    ],
}

# Default date range (will be overridden based on task group)
START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 2, 1)

# ============================================================================


def get_subitem_board(api_token, subitem_id):
    """Get the board ID where a subitem actually exists"""
    query = """
    query ($itemId: [ID!]) {
        items(ids: $itemId) {
            id
            board {
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
        json={"query": query, "variables": {"itemId": subitem_id}},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            return None, None
        if data.get("data", {}).get("items"):
            item = data["data"]["items"][0]
            if item.get("board"):
                return item["board"]["id"], item["board"].get("name", "Unknown")
    return None, None


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


def get_columns(importer, board_id, verbose=False):
    """Get required columns from board"""
    columns = importer.get_board_columns(board_id)
    planned_hours_col = None
    deadline_col = None
    dependency_col = None
    
    if verbose:
        print(f"\n  Available columns on board {board_id}:")
        for col in columns:
            col_title = col.get("title", "Unknown")
            col_type = col.get("type", "unknown")
            col_id = col.get("id", "unknown")
            print(f"    - {col_title} (Type: {col_type}, ID: {col_id})")
    
    for col in columns:
        col_title_lower = col.get("title", "").lower()
        col_type = col.get("type", "").lower()
        
        # Planned hours detection - be more flexible
        if not planned_hours_col:
            # Check for hour type first
            if col_type == "hour":
                planned_hours_col = col
                print(f"  ✓ Selected Planned Hours column: {col.get('title')} (Type: {col_type})")
            # Then check for numeric/numbers
            elif col_type in ["numeric", "numbers"]:
                if "hour" in col_title_lower or "time" in col_title_lower or "planned" in col_title_lower:
                    planned_hours_col = col
                    print(f"  ✓ Selected Planned Hours column: {col.get('title')} (Type: {col_type})")
            # Then check title keywords
            elif "hour" in col_title_lower or "time" in col_title_lower or "planned" in col_title_lower:
                planned_hours_col = col
                print(f"  ✓ Selected Planned Hours column: {col.get('title')} (Type: {col_type})")
        
        # Deadline detection - prioritize timeline, then date
        if not deadline_col:
            if col_type == "timeline":
                deadline_col = col
                print(f"  ✓ Selected Deadline column: {col.get('title')} (Type: {col_type})")
            elif col_type == "date" and ("deadline" in col_title_lower or "due" in col_title_lower or "date" in col_title_lower):
                deadline_col = col
                print(f"  ✓ Selected Deadline column: {col.get('title')} (Type: {col_type})")
        
        # Dependency detection
        if not dependency_col:
            if "dependency" in col_title_lower or "depend" in col_title_lower:
                dependency_col = col
                print(f"  ✓ Selected Dependencies column: {col.get('title')} (Type: {col_type})")
    
    return planned_hours_col, deadline_col, dependency_col


def update_subitem(importer, subitems_board_id, subitem_id, subitem_data, deadline_date, 
                   planned_hours_col, deadline_col, dependency_col, previous_subitem_id, verbose=False):
    """Update a single subitem with hours, deadline, and dependency"""
    # Set planned hours
    if planned_hours_col:
        try:
            col_type = planned_hours_col.get("type", "").lower()
            col_id = planned_hours_col["id"]
            
            # Format value based on column type
            if col_type == "hour":
                hours_value = {"hours": subitem_data["hours"], "minutes": 0}
            elif col_type in ["numeric", "numbers"]:
                # For numeric columns, pass the number directly (will be converted to JSON string by change_column_value)
                hours_value = subitem_data["hours"]
            else:
                # Default to hour format
                hours_value = {"hours": subitem_data["hours"], "minutes": 0}
            
            if verbose:
                print(f"      Attempting to set planned hours: {subitem_data['hours']}h on column '{planned_hours_col.get('title', 'unknown')}' (ID: {col_id}, Type: {col_type})")
                print(f"      Value format: {hours_value}")
            
            result = importer.change_column_value(subitems_board_id, subitem_id, col_id, hours_value)
            if verbose:
                if result:
                    print(f"      ✓ Successfully set planned hours: {subitem_data['hours']}h")
                else:
                    print(f"      ⚠️  Failed to set planned hours (returned False)")
        except Exception as e:
            print(f"      ⚠️  Could not set planned hours: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    elif verbose:
        print(f"      ⚠️  Planned hours column not found")
    
    # Set deadline
    if deadline_col:
        try:
            col_type = deadline_col.get("type", "").lower()
            col_id = deadline_col["id"]
            
            if col_type == "timeline":
                timeline_value = {
                    "from": deadline_date.strftime("%Y-%m-%d"),
                    "to": deadline_date.strftime("%Y-%m-%d")
                }
                if verbose:
                    print(f"      Attempting to set timeline: {timeline_value} on column '{deadline_col.get('title', 'unknown')}' (ID: {col_id})")
                result = importer.change_column_value(subitems_board_id, subitem_id, col_id, timeline_value)
            else:
                date_value = {"date": deadline_date.strftime("%Y-%m-%d")}
                if verbose:
                    print(f"      Attempting to set date: {date_value} on column '{deadline_col.get('title', 'unknown')}' (ID: {col_id}, Type: {col_type})")
                result = importer.change_column_value(subitems_board_id, subitem_id, col_id, date_value)
            
            if verbose:
                if result:
                    print(f"      ✓ Successfully set deadline: {deadline_date.strftime('%b %d, %Y')}")
                else:
                    print(f"      ⚠️  Failed to set deadline (returned False)")
        except Exception as e:
            print(f"      ⚠️  Could not set deadline: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
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


def calculate_weekly_deadlines(subitems_list, start_date, end_date, weight_later_weeks=False):
    """
    Calculate deadlines based on weekly hour distribution.
    Returns a list of (subitem_index, deadline_date) tuples.
    """
    # Calculate total hours
    total_hours = sum(subitem["subitem"].get("hours", 0) for subitem in subitems_list)
    if total_hours == 0:
        return []
    
    # Calculate number of weeks
    total_days = (end_date - start_date).days
    num_weeks = max(1, int(total_days / 7) + (1 if total_days % 7 > 0 else 0))
    
    # Calculate hours per week
    if weight_later_weeks and num_weeks > 12:
        # For longer challenges (May 15), weight more hours toward April/May
        # First ~60% of weeks (Jan-Mar) get 30% of hours
        # Last ~40% of weeks (Apr-May) get 70% of hours
        early_weeks = int(num_weeks * 0.6)
        late_weeks = num_weeks - early_weeks
        early_hours = total_hours * 0.3
        late_hours = total_hours * 0.7
        hours_per_week_early = early_hours / early_weeks if early_weeks > 0 else 0
        hours_per_week_late = late_hours / late_weeks if late_weeks > 0 else 0
    else:
        hours_per_week = total_hours / num_weeks
        hours_per_week_early = hours_per_week
        hours_per_week_late = hours_per_week
    
    # Assign deadlines based on cumulative hours
    deadlines = []
    cumulative_hours = 0
    
    for idx, subitem_data in enumerate(subitems_list):
        subitem = subitem_data["subitem"]
        hours = subitem.get("hours", 0)
        cumulative_hours += hours
        
        # Determine which week this subitem falls into based on cumulative hours
        if weight_later_weeks and num_weeks > 12:
            early_weeks = int(num_weeks * 0.6)
            early_total_hours = total_hours * 0.3
            
            if cumulative_hours <= early_total_hours:
                # Early weeks (Jan-Mar)
                target_week = int(cumulative_hours / hours_per_week_early) if hours_per_week_early > 0 else 0
                target_week = min(target_week, early_weeks - 1)
            else:
                # Late weeks (Apr-May)
                remaining_hours = cumulative_hours - early_total_hours
                target_week = early_weeks + int(remaining_hours / hours_per_week_late) if hours_per_week_late > 0 else early_weeks
                target_week = min(target_week, num_weeks - 1)
        else:
            # Even distribution
            target_week = int(cumulative_hours / hours_per_week) if hours_per_week > 0 else 0
            target_week = min(target_week, num_weeks - 1)
        
        # Calculate deadline date (end of that week - Saturday)
        week_end = start_date + timedelta(days=target_week * 7 + 6)  # End of week (Saturday)
        if week_end > end_date:
            week_end = end_date
        
        deadlines.append((idx, week_end))
    
    return deadlines


def add_tasks_group(task_dict, start_date, end_date, group_name="", weight_later_weeks=False):
    """Add a group of tasks with specific date range, with dependencies reset per task"""
    global previous_subitem_id_global
    
    imported_items = 0
    imported_subitems = 0
    
    # Get columns once (will be cached per board)
    if not hasattr(add_tasks_group, 'board_columns_cache'):
        add_tasks_group.board_columns_cache = {}
    
    for item_name, subitems in task_dict.items():
        # Reset dependencies at the start of each new task
        previous_subitem_id = None
        
        # Filter out empty placeholder items
        valid_subitems = [s for s in subitems if s.get("hours", 0) > 0 or s.get("name", "").strip()]
        
        if not valid_subitems:
            continue
        
        # Calculate deadlines for THIS task independently
        task_subitems_list = [{"item": item_name, "subitem": subitem} for subitem in valid_subitems]
        task_deadline_map = dict(calculate_weekly_deadlines(task_subitems_list, start_date, end_date, weight_later_weeks))
        
        try:
            print(f"\n  Creating {item_name}...")
            print(f"    Total hours: {sum(s.get('hours', 0) for s in valid_subitems)}")
            print(f"    Subitems: {len(valid_subitems)}")
            item_id = importer.create_item(board_id, group_id, item_name)
            imported_items += 1
            print(f"    ✓ Created {item_name}")
            
            subitem_idx = 0
            for subitem in valid_subitems:
                try:
                    subitem_id = importer.create_subitem(item_id, subitem["name"])
                    imported_subitems += 1
                    
                    # Small delay to ensure subitem is fully created
                    time.sleep(0.5)
                    
                    # Find which board the subitem actually exists on
                    actual_subitem_board_id, actual_board_name = get_subitem_board(API_TOKEN, subitem_id)
                    if not actual_subitem_board_id:
                        actual_subitem_board_id = subitems_board_id
                        actual_board_name = "Subitems board"
                    
                    # Get columns from the actual subitem board (cached per board)
                    if actual_subitem_board_id not in add_tasks_group.board_columns_cache:
                        print(f"      Getting columns from board {actual_subitem_board_id}...")
                        subitem_planned_hours_col, subitem_deadline_col, subitem_dependency_col = get_columns(importer, actual_subitem_board_id, verbose=True)
                        add_tasks_group.board_columns_cache[actual_subitem_board_id] = (
                            subitem_planned_hours_col, subitem_deadline_col, subitem_dependency_col
                        )
                    else:
                        subitem_planned_hours_col, subitem_deadline_col, subitem_dependency_col = add_tasks_group.board_columns_cache[actual_subitem_board_id]
                    
                    # Get deadline from THIS task's hour-based calculation
                    deadline_date = task_deadline_map.get(subitem_idx, end_date)
                    subitem_idx += 1
                    
                    update_subitem(importer, actual_subitem_board_id, subitem_id, subitem, deadline_date,
                                 subitem_planned_hours_col, subitem_deadline_col, subitem_dependency_col, previous_subitem_id, verbose=True)
                    
                    # Set dependency for next subitem in THIS task only
                    previous_subitem_id = subitem_id
                    deadline_str = f" (deadline: {deadline_date.strftime('%b %d')})"
                    hours_str = f"{subitem['hours']}h" if subitem.get('hours', 0) > 0 else "0h"
                    print(f"    ✓ Added subitem: {subitem['name'][:60]}... ({hours_str}){deadline_str}")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    ⚠️  Failed to add subitem: {e}")
        except Exception as e:
            print(f"  ❌ Error creating {item_name}: {e}")
    
    return imported_items, imported_subitems


def add_tasks():
    """Add new tasks to Spring Plan board"""
    global importer, board_id, subitems_board_id, group_id, planned_hours_col, deadline_col, dependency_col
    
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
    print("\n📊 Getting columns from subitems board...")
    planned_hours_col, deadline_col, dependency_col = get_columns(importer, subitems_board_id)
    
    print(f"✓ Column detection results:")
    if planned_hours_col:
        print(f"  - Planned Hours: {planned_hours_col.get('title', 'unknown')} (ID: {planned_hours_col.get('id', 'unknown')}, Type: {planned_hours_col.get('type', 'unknown')})")
    else:
        print(f"  - Planned Hours: NOT FOUND")
    if deadline_col:
        print(f"  - Deadline: {deadline_col.get('title', 'unknown')} (ID: {deadline_col.get('id', 'unknown')}, Type: {deadline_col.get('type', 'unknown')})")
    else:
        print(f"  - Deadline: NOT FOUND")
    if dependency_col:
        print(f"  - Dependencies: {dependency_col.get('title', 'unknown')} (ID: {dependency_col.get('id', 'unknown')}, Type: {dependency_col.get('type', 'unknown')})")
    else:
        print(f"  - Dependencies: NOT FOUND")
    
    # Combine all task groups for preview
    all_tasks = {}
    all_tasks.update(TASKS_FEB1)
    all_tasks.update(TASKS_APR1)
    all_tasks.update(TASKS_APR15)
    all_tasks.update(TASKS_MAY15)
    
    # Show preview
    total_items = len(all_tasks)
    total_subitems = sum(len(subitems) for subitems in all_tasks.values())
    
    print(f"\n📋 Preview of tasks to be added:")
    print(f"   Total items: {total_items}")
    print(f"   Total subitems: {total_subitems}")
    print(f"\n   Date ranges:")
    print(f"     - Feb 1, 2026: {len(TASKS_FEB1)} items")
    print(f"     - Apr 1, 2026: {len(TASKS_APR1)} items")
    print(f"     - Apr 15, 2026: {len(TASKS_APR15)} items")
    print(f"     - May 15, 2026: {len(TASKS_MAY15)} items")
    
    confirm = input(f"\n❓ Proceed with adding these tasks? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    print(f"\n📥 Adding tasks...")
    
    total_imported_items = 0
    total_imported_subitems = 0
    
    # Global variable to track previous subitem across all groups for dependencies
    global previous_subitem_id_global
    previous_subitem_id_global = None
    
    # Process each group with its date range (all start on Jan 8)
    start_date_jan8 = datetime(2026, 1, 8)
    
    if TASKS_FEB1:
        print(f"\n📅 Processing tasks with Feb 1, 2026 deadline (Jan 8 - Feb 1)...")
        items, subitems = add_tasks_group(TASKS_FEB1, start_date_jan8, datetime(2026, 2, 1), weight_later_weeks=False)
        total_imported_items += items
        total_imported_subitems += subitems
    
    if TASKS_APR1:
        print(f"\n📅 Processing tasks with Apr 1, 2026 deadline (Jan 8 - Apr 1)...")
        items, subitems = add_tasks_group(TASKS_APR1, start_date_jan8, datetime(2026, 4, 1), weight_later_weeks=False)
        total_imported_items += items
        total_imported_subitems += subitems
    
    if TASKS_APR15:
        print(f"\n📅 Processing tasks with Apr 15, 2026 deadline (Jan 8 - Apr 15)...")
        items, subitems = add_tasks_group(TASKS_APR15, start_date_jan8, datetime(2026, 4, 15), weight_later_weeks=False)
        total_imported_items += items
        total_imported_subitems += subitems
    
    if TASKS_MAY15:
        print(f"\n📅 Processing tasks with May 15, 2026 deadline (Jan 8 - May 15, weighted toward later weeks)...")
        items, subitems = add_tasks_group(TASKS_MAY15, start_date_jan8, datetime(2026, 5, 15), weight_later_weeks=True)
        total_imported_items += items
        total_imported_subitems += subitems
    
    print(f"\n✅ Import complete!")
    print(f"  - Items created: {total_imported_items}")
    print(f"  - Subitems created: {total_imported_subitems}")
    print(f"\n🔗 View board: https://monday.com/boards/{board_id}")


def update_tasks():
    """Update existing tasks in Spring Plan board"""
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
    
    # Get all items in Spring Plan group
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
    
    items = []
    if response.status_code == 200:
        data = response.json()
        if not "errors" in data:
            items = data.get("data", {}).get("boards", [])[0].get("groups", [])[0].get("items_page", {}).get("items", [])
    
    if not items:
        print("❌ No items found in Spring Plan group")
        return
    
    print(f"✓ Found {len(items)} items in Spring Plan group")
    
    # Get all subitems from all items
    print("\n📝 Getting subitems...")
    all_subitems = []
    for item in items:
        subitems = get_item_subitems(API_TOKEN, item["id"])
        print(f"  {item['name']}: {len(subitems)} subitems")
        
        # Try to match with task definitions
        item_tasks = TASKS.get(item["name"], [])
        for subitem in subitems:
            # Find matching task definition
            task_def = None
            for task in item_tasks:
                if task["name"].lower() in subitem["name"].lower() or subitem["name"].lower() in task["name"].lower():
                    task_def = task
                    break
            
            all_subitems.append({
                "id": subitem["id"],
                "name": subitem["name"],
                "hours": task_def["hours"] if task_def else 8  # Default to 8 if not found
            })
    
    print(f"\n✓ Total subitems to update: {len(all_subitems)}")
    
    # Get columns
    print("\n📊 Getting columns...")
    planned_hours_col, deadline_col, dependency_col = get_columns(importer, subitems_board_id)
    
    # Calculate deadlines
    total_days = (END_DATE - START_DATE).days
    days_between = total_days / (len(all_subitems) - 1) if len(all_subitems) > 1 else 0
    
    # Update subitems
    print(f"\n📥 Updating subitems...")
    updated_count = 0
    previous_subitem_id = None
    
    for idx, subitem in enumerate(all_subitems, 1):
        print(f"\n  {idx}. {subitem['name'][:60]}...")
        print(f"     Hours: {subitem['hours']}")
        
        deadline_date = START_DATE + timedelta(days=days_between * (idx - 1))
        if deadline_date > END_DATE:
            deadline_date = END_DATE
        
        update_subitem(importer, subitems_board_id, subitem["id"], subitem, deadline_date,
                      planned_hours_col, deadline_col, dependency_col, previous_subitem_id, verbose=True)
        previous_subitem_id = subitem["id"]
        updated_count += 1
        time.sleep(0.3)
    
    print(f"\n✅ Update complete!")
    print(f"  - Updated {updated_count} subitems")
    print(f"  - Timeline: {START_DATE.strftime('%B %d, %Y')} to {END_DATE.strftime('%B %d, %Y')}")


def input_tasks_manually():
    """Allow user to manually enter tasks"""
    print("\n" + "=" * 60)
    print("Manual Task Entry")
    print("=" * 60)
    print("\nEnter your tasks. Format:")
    print("  Item Name")
    print("    - Subitem Name | Hours")
    print("    - Subitem Name | Hours")
    print("  Item Name")
    print("    - Subitem Name | Hours")
    print("\nType 'DONE' on a new line when finished")
    print("Type 'CANCEL' to cancel")
    print("\nExample:")
    print("  Project Alpha")
    print("    - Task 1 | 10")
    print("    - Task 2 | 20")
    print("  Project Beta")
    print("    - Task 1 | 15")
    print("  DONE")
    print("\n" + "-" * 60)
    
    tasks = {}
    current_item = None
    lines = []
    
    print("\nEnter your tasks (paste or type, then press Enter twice when done):")
    while True:
        try:
            line = input()
            if line.strip().upper() == "DONE":
                break
            if line.strip().upper() == "CANCEL":
                return None
            if line.strip():
                lines.append(line)
        except EOFError:
            break
    
    # Parse the input
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if it's an item (starts with a letter, not indented)
        if not line.startswith("  ") and not line.startswith("    ") and not line.startswith("-"):
            # New item
            current_item = line
            tasks[current_item] = []
        elif line.startswith("-") or line.startswith("  -") or line.startswith("    -"):
            # Subitem
            if current_item is None:
                print(f"⚠️  Warning: Subitem '{line}' has no parent item, skipping")
                continue
            
            # Parse subitem: "- Name | Hours" or "- Name - Hours"
            parts = line.lstrip("- ").strip()
            if "|" in parts:
                name, hours_str = parts.split("|", 1)
            elif " - " in parts:
                name, hours_str = parts.split(" - ", 1)
            else:
                # Try to extract hours from end
                parts_split = parts.rsplit(" ", 1)
                if len(parts_split) == 2 and parts_split[1].replace("h", "").replace("H", "").isdigit():
                    name = parts_split[0]
                    hours_str = parts_split[1]
                else:
                    print(f"⚠️  Warning: Could not parse hours from '{parts}', defaulting to 8 hours")
                    name = parts
                    hours_str = "8"
            
            name = name.strip()
            hours_str = hours_str.strip().replace("h", "").replace("H", "").replace("hours", "").replace("Hours", "").strip()
            
            try:
                hours = int(hours_str)
            except ValueError:
                print(f"⚠️  Warning: Invalid hours '{hours_str}' for '{name}', defaulting to 8 hours")
                hours = 8
            
            tasks[current_item].append({"name": name, "hours": hours})
    
    if not tasks:
        print("❌ No tasks entered")
        return None
    
    return tasks


def input_date_range():
    """Allow user to input date range"""
    print("\n" + "=" * 60)
    print("Date Range Entry")
    print("=" * 60)
    print("\nEnter date range for task distribution")
    print("Format: YYYY-MM-DD")
    
    while True:
        start_str = input("Start date (YYYY-MM-DD) [default: 2026-01-01]: ").strip()
        if not start_str:
            start_str = "2026-01-01"
        
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    while True:
        end_str = input("End date (YYYY-MM-DD) [default: 2026-02-01]: ").strip()
        if not end_str:
            end_str = "2026-02-01"
        
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
    
    if end_date <= start_date:
        print("❌ End date must be after start date")
        return None, None
    
    return start_date, end_date


def main():
    """Main function"""
    print("=" * 60)
    print("Spring Plan Automation - Year 5 Plan Board")
    print("=" * 60)
    print("\nWhat would you like to do?")
    print("1. Add new tasks (from TASKS dictionary in script)")
    print("2. Manually enter tasks")
    print("3. Update existing subitems")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        add_tasks()
    elif choice == "2":
        # Get tasks manually
        manual_tasks = input_tasks_manually()
        if manual_tasks:
            # Get date range
            start_date, end_date = input_date_range()
            if start_date and end_date:
                # Temporarily set global variables
                global TASKS, START_DATE, END_DATE
                original_tasks = TASKS.copy()
                original_start = START_DATE
                original_end = END_DATE
                
                TASKS = manual_tasks
                START_DATE = start_date
                END_DATE = end_date
                
                add_tasks()
                
                # Restore original values
                TASKS = original_tasks
                START_DATE = original_start
                END_DATE = original_end
    elif choice == "3":
        update_tasks()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
