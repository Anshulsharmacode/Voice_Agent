"""
Orchestrator tools for managing ReAct Agents
"""

from typing import Dict, Any
from logs.logger import logger

def get_create_react_agent_tool():
    """Tool to create a new ReAct Agent"""
    return {
        "type": "function",
        "function": {
            "name": "create_react_agent",
            "description": "Create a new ReAct Agent for complex tasks",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name for the new ReAct Agent"
                    },
                    "task_description": {
                        "type": "string", 
                        "description": "Description of the task this agent will handle"
                    }
                },
                "required": ["agent_name"]
            }
        }
    }

def get_get_agent_status_tool():
    """Tool to get status of an agent"""
    return {
        "type": "function",
        "function": {
            "name": "get_agent_status",
            "description": "Get the status of a specific ReAct Agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to check"
                    }
                },
                "required": ["agent_name"]
            }
        }
    }

def get_send_task_to_agent_tool():
    """Tool to send a task to a specific agent"""
    return {
        "type": "function",
        "function": {
            "name": "send_task_to_agent",
            "description": "Send a task to a specific ReAct Agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to send task to"
                    },
                    "task": {
                        "type": "string",
                        "description": "Task to send to the agent"
                    }
                },
                "required": ["agent_name", "task"]
            }
        }
    }

# def get_execute_simple_task_tool():
#     """Tool to execute simple tasks directly"""
#     return {
#         "type": "function",
#         "function": {
#             "name": "execute_simple_task",
#             "description": "Execute a simple task directly without creating a ReAct Agent",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "task": {
#                         "type": "string",
#                         "description": "Simple task to execute (e.g., basic response, open link)"
#                     }
#                 },
#                 "required": ["task"]
#             }
#         }
#     }

def get_list_agents_tool():
    """Tool to list all active agents"""
    return {
        "type": "function",
        "function": {
            "name": "list_agents",
            "description": "List all active ReAct Agents and their status",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

def get_abort_agent_tool():
    """Tool to abort a specific agent"""
    return {
        "type": "function",
        "function": {
            "name": "abort_agent",
            "description": "Abort a specific ReAct Agent's current task",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to abort"
                    }
                },
                "required": ["agent_name"]
            }
        }
    } 
    

def get_terminate_agent_tool():
    """Tool to terminate a specific agent"""
    return {
        "type": "function",
        "function": {
            "name": "terminate_agent",
            "description": "Terminate a specific ReAct Agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to terminate"
                    }
                },
                "required": ["agent_name"]
            }
        }
    }