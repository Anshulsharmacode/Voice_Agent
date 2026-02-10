from typing import Dict, List
import asyncio
import os

# Global variable to track tasks and their completion status
task_tracker = {
    "tasks": [],
    "completed_tasks": set()
}

def get_plan_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "create_plan",
            "description": "Creates a plan with steps to accomplish the tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "description": "List of steps to accomplish the tasks",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["steps"]
            }
        }
    }

def get_task_is_done_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "task_is_done",
            "description": "Mark a task as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_index": {
                        "type": "integer",
                        "description": "Index of the task to mark as completed (0-based)"
                    }
                },
                "required": ["task_index"]
            }
        }
    }

def get_task_tracker_tool() -> Dict:
    """Renamed from get_plan_status_tool to match __init__ imports"""
    return {
        "type": "function",
        "function": {
            "name": "track_task",
            "description": "Get the current status of the plan with all tasks and their completion status",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

async def create_plan(tasks) -> str:
    """Creates a markdown plan with checkboxes for each step and saves to plan.md"""
    # Handle XML format where tasks might be a list of task elements
    # if isinstance(tasks, str):
    #     try:
    #         # Try to parse XML format
    #         import xml.etree.ElementTree as ET
    #         root = ET.fromstring(tasks)
    #         if root.tag == 'tasks':
    #             tasks = [task.text for task in root.findall('task')]
    #         else:
    #             # Try to parse JSON format as fallback
    #             import json
    #             tasks = json.loads(tasks)
    #     except:
    #         # If both parsing attempts fail, treat as a single task
    #         tasks = [tasks]
    
    # Reset the task tracker
    task_tracker["tasks"] = tasks
    task_tracker["completed_tasks"] = set()
    
    # Create a markdown plan with empty checkboxes
    plan = "# Task Plan\n\n"
    for i, step in enumerate(tasks):
        plan += f"- [ ] {i+1}. {step}\n"
    
    # Save the plan to a file
    plan_file_path = os.path.join(os.path.dirname(__file__), "plan.md")
    with open(plan_file_path, "w") as f:
        f.write(plan)
    
    return plan

async def task_is_done(task_index: int) -> str:
    """Mark a task as completed and update the plan.md file"""
    if task_index < 0 or task_index >= len(task_tracker["tasks"]):
        return f"Error: Task index {task_index} is out of range"
    
    # Mark the task as completed
    task_tracker["completed_tasks"].add(task_index)
    
    # Create the plan markdown content
    plan = "# Task Plan\n\n"
    for i, step in enumerate(task_tracker["tasks"]):
        checkbox = "[x]" if i in task_tracker["completed_tasks"] else "[ ]"
        plan += f"- {checkbox} {i+1}. {step}\n"
    
    # Update the plan.md file
    plan_file_path = os.path.join(os.path.dirname(__file__), "plan.md")
    with open(plan_file_path, "w") as f:
        f.write(plan)
    
    # Check if all tasks are completed
    all_completed = len(task_tracker["completed_tasks"]) == len(task_tracker["tasks"])
    status_message = ""
    if all_completed:
        status_message = f"Task '{task_tracker['tasks'][task_index]}' marked as completed. All tasks have been completed. You can now use the finish tool."
    else:
        remaining = len(task_tracker["tasks"]) - len(task_tracker["completed_tasks"])
        status_message = f"Task '{task_tracker['tasks'][task_index]}' marked as completed. {remaining} tasks remaining."
    
    return f"{status_message}\n\n```markdown\n{plan}```"

async def track_task() -> str:
    """Renamed from get_plan_status to match __init__ imports"""
    if not task_tracker["tasks"]:
        return "No plan has been created yet."
    
    plan = "# Current Task Plan Status\n\n"
    completed_count = 0
    
    for i, step in enumerate(task_tracker["tasks"]):
        checkbox = "[x]" if i in task_tracker["completed_tasks"] else "[ ]"
        plan += f"- {checkbox} {i+1}. {step}\n"
        if i in task_tracker["completed_tasks"]:
            completed_count += 1
    
    total_tasks = len(task_tracker["tasks"])
    remaining = total_tasks - completed_count
    progress_percentage = (completed_count / total_tasks) * 100 if total_tasks > 0 else 0
    
    plan += f"\n## Progress Summary\n"
    plan += f"- Completed: {completed_count}/{total_tasks} tasks ({progress_percentage:.1f}%)\n"
    plan += f"- Remaining: {remaining} tasks\n"
    
    all_completed = completed_count == total_tasks
    if all_completed:
        plan += f"- Status: All tasks completed ✓\n"
    else:
        plan += f"- Status: In progress...\n"
    
    return plan