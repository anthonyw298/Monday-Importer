"""
Monday.com Board Importer
Extracts challenges, tasks, and subtasks from a Word document and imports them into Monday.com
"""

import os
import json
import re
import time
from typing import List, Dict, Any
from docx import Document
import requests

class MondayImporter:
    def __init__(self, api_token: str):
        """
        Initialize the Monday.com importer
        
        Args:
            api_token: Your Monday.com API token
        """
        self.api_token = api_token
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json"
        }
    
    def create_board(self, board_name: str, board_kind: str = "public") -> str:
        """
        Create a new board in Monday.com
        
        Args:
            board_name: Name of the board to create
            board_kind: Type of board ('public', 'private', 'share')
            
        Returns:
            Board ID
        """
        query = """
        mutation ($boardName: String!, $boardKind: BoardKind!) {
            create_board (board_name: $boardName, board_kind: $boardKind) {
                id
                name
            }
        }
        """
        
        variables = {
            "boardName": board_name,
            "boardKind": board_kind.upper()
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error creating board: {data['errors']}")
            board_id = data["data"]["create_board"]["id"]
            print(f"✓ Created board '{board_name}' with ID: {board_id}")
            return board_id
        else:
            raise Exception(f"Failed to create board: {response.text}")
    
    def create_group(self, board_id: str, group_name: str) -> str:
        """
        Create a new group in a board
        
        Args:
            board_id: The board ID
            group_name: Name of the group to create
            
        Returns:
            Group ID
        """
        query = """
        mutation ($boardId: ID!, $groupName: String!) {
            create_group (board_id: $boardId, group_name: $groupName) {
                id
                title
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "groupName": group_name
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error creating group: {data['errors']}")
            group_id = data["data"]["create_group"]["id"]
            return group_id
        else:
            raise Exception(f"Failed to create group: {response.text}")
    
    def move_item_to_group(self, item_id: str, group_id: str) -> bool:
        """
        Move an item to a different group
        
        Args:
            item_id: The item ID
            group_id: The target group ID
            
        Returns:
            True if successful
        """
        query = """
        mutation ($itemId: ID!, $groupId: String!) {
            move_item_to_group (item_id: $itemId, group_id: $groupId) {
                id
            }
        }
        """
        
        variables = {
            "itemId": item_id,
            "groupId": group_id
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error moving item: {data['errors']}")
            return True
        else:
            raise Exception(f"Failed to move item: {response.text}")
    
    def get_board_groups(self, board_id: str) -> List[Dict]:
        """
        Get all groups from a board
        
        Args:
            board_id: The board ID
            
        Returns:
            List of groups
        """
        query = """
        query ($boardId: [ID!]) {
            boards(ids: $boardId) {
                groups {
                    id
                    title
                }
            }
        }
        """
        
        variables = {"boardId": board_id}
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error getting groups: {data['errors']}")
            return data["data"]["boards"][0]["groups"]
        else:
            raise Exception(f"Failed to get groups: {response.text}")
    
    def check_subitems_column(self, board_id: str) -> bool:
        """
        Check if board has a subitems column
        
        Args:
            board_id: The board ID
            
        Returns:
            True if subitems column exists, False otherwise
        """
        query = """
        query ($boardId: [ID!]) {
            boards(ids: $boardId) {
                columns {
                    id
                    type
                }
            }
        }
        """
        
        variables = {"boardId": board_id}
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error checking columns: {data['errors']}")
            columns = data["data"]["boards"][0]["columns"]
            return any(col["type"] == "subitems" for col in columns)
        else:
            raise Exception(f"Failed to check columns: {response.text}")
    
    def add_subitems_column(self, board_id: str) -> bool:
        """
        Add a subitems column to the board
        
        Args:
            board_id: The board ID
            
        Returns:
            True if successful
        """
        query = """
        mutation ($boardId: ID!) {
            create_column (board_id: $boardId, column_type: subitems) {
                id
                type
            }
        }
        """
        
        variables = {"boardId": board_id}
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                # Column might already exist, which is fine
                error_msg = str(data['errors'])
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    return True
                raise Exception(f"Error adding subitems column: {data['errors']}")
            return True
        else:
            raise Exception(f"Failed to add subitems column: {response.text}")
    
    def create_item(self, board_id: str, group_id: str, item_name: str) -> str:
        """
        Create an item (challenge/task) in a board
        
        Args:
            board_id: The board ID
            group_id: The group ID
            item_name: Name of the item
            
        Returns:
            Item ID
        """
        query = """
        mutation ($boardId: ID!, $groupId: String!, $itemName: String!) {
            create_item (board_id: $boardId, group_id: $groupId, item_name: $itemName) {
                id
            }
        }
        """
        
        variables = {
            "boardId": board_id,
            "groupId": group_id,
            "itemName": item_name
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error creating item: {data['errors']}")
            item_id = data["data"]["create_item"]["id"]
            return item_id
        else:
            raise Exception(f"Failed to create item: {response.text}")
    
    def create_subitem(self, parent_item_id: str, subitem_name: str, retries: int = 3) -> str:
        """
        Create a subitem (subtask) under a parent item
        
        Args:
            parent_item_id: The parent item ID
            subitem_name: Name of the subitem
            retries: Number of retry attempts for rate limiting
            
        Returns:
            Subitem ID
        """
        query = """
        mutation ($parentItemId: ID!, $subitemName: String!) {
            create_subitem (parent_item_id: $parentItemId, item_name: $subitemName) {
                id
            }
        }
        """
        
        variables = {
            "parentItemId": parent_item_id,
            "subitemName": subitem_name
        }
        
        for attempt in range(retries):
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    error_msg = str(data['errors'])
                    # Check for rate limiting
                    if "rate limit" in error_msg.lower() and attempt < retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"    ⏳ Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise Exception(f"Error creating subitem: {data['errors']}")
                subitem_id = data["data"]["create_subitem"]["id"]
                return subitem_id
            elif response.status_code == 429:  # Rate limit
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"    ⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            else:
                raise Exception(f"Failed to create subitem: {response.text}")
        
        raise Exception(f"Failed to create subitem after {retries} attempts")
    
    def list_boards(self) -> List[Dict]:
        """
        List all boards accessible to the user
        
        Returns:
            List of boards with id and name
        """
        query = """
        query {
            boards(limit: 100) {
                id
                name
            }
        }
        """
        
        response = requests.post(
            self.api_url,
            json={"query": query},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error listing boards: {data['errors']}")
            return data["data"]["boards"]
        else:
            raise Exception(f"Failed to list boards: {response.text}")
    
    def find_board_by_name(self, board_name: str, exact_match: bool = False) -> Dict:
        """
        Find a board by name (case-insensitive partial match or exact match)
        
        Args:
            board_name: Name of the board to find
            exact_match: If True, requires exact match (ignoring case)
            
        Returns:
            Board dictionary with id and name, or None if not found
        """
        boards = self.list_boards()
        board_name_lower = board_name.lower()
        
        for board in boards:
            if exact_match:
                if board_name_lower == board["name"].lower():
                    return board
            else:
                if board_name_lower in board["name"].lower():
                    return board
        
        return None
    
    def get_board_columns(self, board_id: str) -> List[Dict]:
        """
        Get all columns from a board
        
        Args:
            board_id: The board ID
            
        Returns:
            List of columns with id, title, and type
        """
        query = """
        query ($boardId: [ID!]) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        
        variables = {"boardId": board_id}
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error getting columns: {data['errors']}")
            return data["data"]["boards"][0]["columns"]
        else:
            raise Exception(f"Failed to get columns: {response.text}")
    
    def change_column_value(self, board_id: str, item_id: str, column_id: str, value: Any) -> bool:
        """
        Update a column value for an item
        
        Args:
            board_id: The board ID
            item_id: The item ID
            column_id: The column ID
            value: The value to set (dict/list will be converted to JSON string)
            
        Returns:
            True if successful
        """
        query = """
        mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
            change_column_value (board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
                id
            }
        }
        """
        
        # Convert value to JSON string if it's a dict/list
        # Monday.com API expects JSON scalars as JSON-encoded strings
        if isinstance(value, (dict, list)):
            # Convert to JSON string - this will be the value for the JSON! scalar
            value_json_str = json.dumps(value)
        elif isinstance(value, str):
            # If it's already a string, assume it's a JSON string
            value_json_str = value
        else:
            # For other types, convert to JSON
            value_json_str = json.dumps(value)
        
        # Manually construct the JSON payload to ensure proper encoding
        # The JSON scalar needs to be a string in the variables
        variables = {
            "boardId": board_id,
            "itemId": item_id,
            "columnId": column_id,
            "value": value_json_str
        }
        
        # Use data parameter with manual JSON encoding to have full control
        payload = json.dumps({
            "query": query,
            "variables": variables
        })
        
        response = requests.post(
            self.api_url,
            data=payload,
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error updating column value: {data['errors']}")
            return True
        else:
            raise Exception(f"Failed to update column value: {response.text}")
    
    def get_board_items(self, board_id: str) -> List[Dict]:
        """
        Get all items from a board
        
        Args:
            board_id: The board ID
            
        Returns:
            List of items with id and name
        """
        query = """
        query ($boardId: [ID!]) {
            boards(ids: $boardId) {
                items_page {
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                        }
                    }
                }
            }
        }
        """
        
        variables = {"boardId": board_id}
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                raise Exception(f"Error getting items: {data['errors']}")
            boards_data = data["data"]["boards"]
            if boards_data and boards_data[0].get("items_page"):
                return boards_data[0]["items_page"]["items"]
            return []
        else:
            raise Exception(f"Failed to get items: {response.text}")


class WordDocumentParser:
    """Parse Word documents to extract hierarchical structure"""
    
    def __init__(self, doc_path: str):
        """
        Initialize the parser
        
        Args:
            doc_path: Path to the Word document
        """
        self.doc_path = doc_path
        self.doc = Document(doc_path)
    
    def parse_document(self) -> List[Dict[str, Any]]:
        """
        Parse the document to extract challenges, tasks, and subtasks
        
        Returns:
            List of challenges with nested tasks and subtasks
        """
        challenges = []
        current_challenge = None
        current_task = None
        
        for paragraph in self.doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            
            # Detect heading levels based on style or formatting
            style_name = paragraph.style.name.lower()
            is_bold = any(run.bold for run in paragraph.runs if run.text.strip())
            
            # Try to detect hierarchy based on indentation or numbering
            # Adjust these patterns based on your document structure
            if self._is_challenge(text, style_name, is_bold):
                # Save previous challenge if exists
                if current_challenge:
                    challenges.append(current_challenge)
                
                # Start new challenge
                current_challenge = {
                    "name": text,
                    "tasks": []
                }
                current_task = None
            
            elif self._is_task(text, style_name, is_bold):
                if current_challenge:
                    # Save previous task if exists
                    if current_task:
                        current_challenge["tasks"].append(current_task)
                    
                    # Start new task
                    current_task = {
                        "name": text,
                        "subtasks": []
                    }
            
            elif self._is_subtask(text, style_name, is_bold):
                if current_task:
                    current_task["subtasks"].append(text)
                elif current_challenge:
                    # If no task exists, create one
                    current_task = {
                        "name": "General Tasks",
                        "subtasks": [text]
                    }
                    current_challenge["tasks"].append(current_task)
                    current_task = None
        
        # Don't forget the last challenge
        if current_challenge:
            if current_task:
                current_challenge["tasks"].append(current_task)
            challenges.append(current_challenge)
        
        return challenges
    
    def _is_challenge(self, text: str, style_name: str, is_bold: bool) -> bool:
        """Detect if text is a challenge heading"""
        # Adjust these patterns based on your document
        challenge_patterns = [
            r'^challenge\s+\d+',
            r'^challenge:',
            r'^#\s+',  # Markdown heading
        ]
        
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in challenge_patterns):
            return True
        
        # Check if it's a top-level heading
        if 'heading 1' in style_name or 'title' in style_name:
            return True
        
        return False
    
    def _is_task(self, text: str, style_name: str, is_bold: bool) -> bool:
        """Detect if text is a task"""
        task_patterns = [
            r'^task\s+\d+',
            r'^task:',
            r'^•\s+',  # Bullet point
            r'^-\s+',  # Dash
            r'^\d+\.\s+',  # Numbered list
        ]
        
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in task_patterns):
            return True
        
        if 'heading 2' in style_name:
            return True
        
        return False
    
    def _is_subtask(self, text: str, style_name: str, is_bold: bool) -> bool:
        """Detect if text is a subtask"""
        subtask_patterns = [
            r'^\s+[-•]\s+',  # Indented bullet
            r'^\s+\d+\.\s+',  # Indented number
            r'^subtask',
            r'^sub-task',
        ]
        
        if any(re.match(pattern, text, re.IGNORECASE) for pattern in subtask_patterns):
            return True
        
        if 'heading 3' in style_name:
            return True
        
        return False


def main():
    """Main function to run the import process"""
    
    # Configuration
    MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
    if not MONDAY_API_TOKEN:
        print("Please set MONDAY_API_TOKEN environment variable")
        print("You can get your API token from: https://monday.com/monday-api")
        MONDAY_API_TOKEN = input("Enter your Monday.com API token: ").strip()
    
    DOCUMENT_PATH = input("Enter path to the Word document (or press Enter for 'challenges.docx'): ").strip()
    if not DOCUMENT_PATH:
        DOCUMENT_PATH = "challenges.docx"
    
    BOARD_NAME = input("Enter name for the new board (or press Enter for 'Challenges Board'): ").strip()
    if not BOARD_NAME:
        BOARD_NAME = "Challenges Board"
    
    # Parse the document
    print(f"\n📄 Parsing document: {DOCUMENT_PATH}")
    try:
        parser = WordDocumentParser(DOCUMENT_PATH)
        challenges = parser.parse_document()
        print(f"✓ Found {len(challenges)} challenges")
        
        # Print summary
        total_tasks = sum(len(c["tasks"]) for c in challenges)
        total_subtasks = sum(sum(len(t["subtasks"]) for t in c["tasks"]) for c in challenges)
        print(f"  - Total tasks: {total_tasks}")
        print(f"  - Total subtasks: {total_subtasks}")
        
        # Preview mode - show what will be imported
        preview = input("\n📋 Preview structure? (y/n): ").strip().lower()
        if preview == 'y':
            print("\n" + "="*60)
            for idx, challenge in enumerate(challenges, 1):
                print(f"\nChallenge {idx}: {challenge['name']}")
                for task_idx, task in enumerate(challenge['tasks'], 1):
                    print(f"  Task {task_idx}: {task['name']}")
                    for subtask_idx, subtask in enumerate(task['subtasks'], 1):
                        print(f"    Subtask {subtask_idx}: {subtask[:60]}...")
            print("\n" + "="*60)
        
        # Confirm before proceeding
        confirm = input("\n✅ Proceed with import? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Import cancelled.")
            return
        
    except FileNotFoundError:
        print(f"❌ Error: File '{DOCUMENT_PATH}' not found")
        print("Please download the Word document from SharePoint and save it locally")
        return
    except Exception as e:
        print(f"❌ Error parsing document: {e}")
        return
    
    # Initialize Monday.com importer
    print(f"\n🔗 Connecting to Monday.com...")
    importer = MondayImporter(MONDAY_API_TOKEN)
    
    # Create new board
    print(f"\n📋 Creating board: {BOARD_NAME}")
    try:
        board_id = importer.create_board(BOARD_NAME)
    except Exception as e:
        print(f"❌ Error creating board: {e}")
        return
    
    # Check and add subitems column if needed
    print(f"\n🔍 Checking for subitems column...")
    try:
        has_subitems = importer.check_subitems_column(board_id)
        if not has_subitems:
            print("⚠️  Subitems column not found. Adding it...")
            importer.add_subitems_column(board_id)
            print("✓ Subitems column added")
        else:
            print("✓ Subitems column already exists")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify subitems column: {e}")
        print("  You may need to manually add a subitems column in Monday.com")
    
    # Get default group (usually "new_group")
    try:
        groups = importer.get_board_groups(board_id)
        if not groups:
            print("❌ Error: No groups found in board")
            return
        group_id = groups[0]["id"]
        print(f"✓ Using group: {groups[0]['title']}")
    except Exception as e:
        print(f"❌ Error getting groups: {e}")
        return
    
    # Import challenges, tasks, and subtasks
    print(f"\n📥 Importing data to Monday.com...")
    imported_challenges = 0
    imported_tasks = 0
    imported_subtasks = 0
    
    for challenge_idx, challenge in enumerate(challenges, 1):
        try:
            print(f"\n  Challenge {challenge_idx}/{len(challenges)}: {challenge['name'][:50]}...")
            
            # Create challenge item
            challenge_item_id = importer.create_item(board_id, group_id, challenge['name'])
            imported_challenges += 1
            
            # Create tasks as subitems of the challenge
            for task in challenge['tasks']:
                task_item_id = importer.create_subitem(challenge_item_id, task['name'])
                imported_tasks += 1
                
                # Create subtasks as subitems of the task
                for subtask in task['subtasks']:
                    try:
                        importer.create_subitem(task_item_id, subtask)
                        imported_subtasks += 1
                        # Small delay to avoid rate limiting
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"      ⚠️  Failed to import subtask '{subtask[:30]}...': {e}")
            
            print(f"    ✓ Imported {len(challenge['tasks'])} tasks and {sum(len(t['subtasks']) for t in challenge['tasks'])} subtasks")
            
        except Exception as e:
            print(f"    ❌ Error importing challenge: {e}")
            continue
    
    # Summary
    print(f"\n✅ Import complete!")
    print(f"  - Challenges: {imported_challenges}")
    print(f"  - Tasks: {imported_tasks}")
    print(f"  - Subtasks: {imported_subtasks}")
    print(f"\n🔗 View your board at: https://avtpsu.monday.com/boards/{board_id}")


if __name__ == "__main__":
    main()

