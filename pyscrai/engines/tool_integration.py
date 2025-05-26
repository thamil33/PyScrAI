"""
Tool Integration System for PyScrAI

Connects agents to external tools and APIs, providing a unified interface
for tool discovery, registration, and execution.
"""

import asyncio
import json
import logging
import inspect
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
from sqlalchemy.orm import Session

from ..databases.models import AgentInstance, ExecutionLog


class ToolDefinition:
    """Represents a tool that can be used by agents."""
    
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        category: str = "general",
        requires_auth: bool = False,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters  # JSON schema for parameters
        self.category = category
        self.requires_auth = requires_auth
        self.rate_limit = rate_limit  # calls per minute
        self.metadata = metadata or {}
        self.usage_count = 0
        self.last_used = None
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool definition to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "requires_auth": self.requires_auth,
            "rate_limit": self.rate_limit,
            "metadata": self.metadata,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat()
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        try:
            self.usage_count += 1
            self.last_used = datetime.utcnow()
            
            # Check if function is async
            if inspect.iscoroutinefunction(self.function):
                result = await self.function(**kwargs)
            else:
                result = self.function(**kwargs)
            
            return {
                "success": True,
                "result": result,
                "tool_name": self.name,
                "execution_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": self.name,
                "execution_time": datetime.utcnow().isoformat()
            }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[str, List[str]] = {}  # category -> tool names
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize with built-in tools
        self._register_builtin_tools()
        
        self.logger.info("ToolRegistry initialized")
    
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        category: str = "general",
        requires_auth: bool = False,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a new tool."""
        try:
            if name in self.tools:
                self.logger.warning(f"Tool '{name}' already exists, overwriting")
            
            tool = ToolDefinition(
                name=name,
                description=description,
                function=function,
                parameters=parameters,
                category=category,
                requires_auth=requires_auth,
                rate_limit=rate_limit,
                metadata=metadata
            )
            
            self.tools[name] = tool
            
            # Update category index
            if category not in self.categories:
                self.categories[category] = []
            if name not in self.categories[category]:
                self.categories[category].append(name)
            
            self.logger.info(f"Registered tool '{name}' in category '{category}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register tool '{name}': {e}", exc_info=True)
            return False
    
    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool."""
        try:
            if name not in self.tools:
                self.logger.warning(f"Tool '{name}' not found")
                return False
            
            tool = self.tools[name]
            category = tool.category
            
            # Remove from tools
            del self.tools[name]
            
            # Remove from category index
            if category in self.categories and name in self.categories[category]:
                self.categories[category].remove(name)
                if not self.categories[category]:
                    del self.categories[category]
            
            self.logger.info(f"Unregistered tool '{name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister tool '{name}': {e}", exc_info=True)
            return False
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        requires_auth: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """List available tools with optional filtering."""
        tools = []
        
        for tool in self.tools.values():
            # Filter by category
            if category and tool.category != category:
                continue
            
            # Filter by auth requirement
            if requires_auth is not None and tool.requires_auth != requires_auth:
                continue
            
            tools.append(tool.to_dict())
        
        return tools
    
    def get_categories(self) -> List[str]:
        """Get list of available tool categories."""
        return list(self.categories.keys())
    
    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search tools by name or description."""
        query_lower = query.lower()
        matching_tools = []
        
        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                matching_tools.append(tool.to_dict())
        
        return matching_tools
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        
        # Text processing tools
        def text_length(text: str) -> int:
            """Get the length of text."""
            return len(text)
        
        def text_upper(text: str) -> str:
            """Convert text to uppercase."""
            return text.upper()
        
        def text_lower(text: str) -> str:
            """Convert text to lowercase."""
            return text.lower()
        
        def word_count(text: str) -> int:
            """Count words in text."""
            return len(text.split())
        
        # Math tools
        def calculate(expression: str) -> Union[float, str]:
            """Safely evaluate mathematical expressions."""
            try:
                # Only allow safe operations
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                
                result = eval(expression)
                return float(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Time tools
        def current_time() -> str:
            """Get current time."""
            return datetime.utcnow().isoformat()
        
        def format_time(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
            """Format timestamp string."""
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime(format_str)
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Register built-in tools
        builtin_tools = [
            {
                "name": "text_length",
                "description": "Get the length of text",
                "function": text_length,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to measure"}
                    },
                    "required": ["text"]
                },
                "category": "text"
            },
            {
                "name": "text_upper",
                "description": "Convert text to uppercase",
                "function": text_upper,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert"}
                    },
                    "required": ["text"]
                },
                "category": "text"
            },
            {
                "name": "text_lower",
                "description": "Convert text to lowercase",
                "function": text_lower,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to convert"}
                    },
                    "required": ["text"]
                },
                "category": "text"
            },
            {
                "name": "word_count",
                "description": "Count words in text",
                "function": word_count,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to count words in"}
                    },
                    "required": ["text"]
                },
                "category": "text"
            },
            {
                "name": "calculate",
                "description": "Safely evaluate mathematical expressions",
                "function": calculate,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
                    },
                    "required": ["expression"]
                },
                "category": "math"
            },
            {
                "name": "current_time",
                "description": "Get current time",
                "function": current_time,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "category": "time"
            },
            {
                "name": "format_time",
                "description": "Format timestamp string",
                "function": format_time,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string", "description": "Timestamp to format"},
                        "format_str": {"type": "string", "description": "Format string", "default": "%Y-%m-%d %H:%M:%S"}
                    },
                    "required": ["timestamp"]
                },
                "category": "time"
            }
        ]
        
        for tool_config in builtin_tools:
            self.register_tool(**tool_config)


class AgentToolManager:
    """Manages tool access and execution for a specific agent."""
    
    def __init__(
        self,
        agent_instance_id: int,
        tool_registry: ToolRegistry,
        db: Session,
        allowed_categories: Optional[List[str]] = None,
        rate_limit_per_minute: int = 60
    ):
        self.agent_instance_id = agent_instance_id
        self.tool_registry = tool_registry
        self.db = db
        self.allowed_categories = allowed_categories or ["text", "math", "time"]
        self.rate_limit_per_minute = rate_limit_per_minute
        self.execution_history: List[Dict[str, Any]] = []
        self.rate_limit_tracker: Dict[str, List[datetime]] = {}  # tool_name -> timestamps
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_instance_id}")
        
        self.logger.info(f"AgentToolManager initialized for agent {agent_instance_id}")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get tools available to this agent."""
        available_tools = []
        
        for category in self.allowed_categories:
            tools = self.tool_registry.list_tools(category=category)
            available_tools.extend(tools)
        
        return available_tools
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        try:
            # Check if tool exists
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "tool_name": tool_name
                }
            
            # Check if agent has access to this tool category
            if tool.category not in self.allowed_categories:
                return {
                    "success": False,
                    "error": f"Access denied to tool category '{tool.category}'",
                    "tool_name": tool_name
                }
            
            # Check rate limits
            if not self._check_rate_limit(tool_name, tool.rate_limit):
                return {
                    "success": False,
                    "error": f"Rate limit exceeded for tool '{tool_name}'",
                    "tool_name": tool_name
                }
            
            # Execute tool
            result = await tool.execute(**parameters)
            
            # Record execution
            execution_record = {
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.agent_instance_id
            }
            
            self.execution_history.append(execution_record)
            
            # Update rate limit tracker
            self._update_rate_limit_tracker(tool_name)
            
            # Log to database
            await self._log_tool_execution(execution_record)
            
            self.logger.debug(f"Executed tool '{tool_name}' for agent {self.agent_instance_id}")
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool_name": tool_name
            }
            
            self.logger.error(f"Tool execution failed for '{tool_name}': {e}", exc_info=True)
            return error_result
    
    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search available tools by query."""
        all_tools = self.tool_registry.search_tools(query)
        
        # Filter by allowed categories
        available_tools = [
            tool for tool in all_tools
            if tool["category"] in self.allowed_categories
        ]
        
        return available_tools
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent tool execution history."""
        return self.execution_history[-limit:]
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage."""
        tool_counts = {}
        total_executions = len(self.execution_history)
        
        for execution in self.execution_history:
            tool_name = execution["tool_name"]
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return {
            "total_executions": total_executions,
            "unique_tools_used": len(tool_counts),
            "tool_usage_counts": tool_counts,
            "most_used_tool": max(tool_counts.items(), key=lambda x: x[1]) if tool_counts else None,
            "available_tools": len(self.get_available_tools()),
            "allowed_categories": self.allowed_categories
        }
    
    def _check_rate_limit(self, tool_name: str, tool_rate_limit: Optional[int]) -> bool:
        """Check if tool execution is within rate limits."""
        now = datetime.utcnow()
        
        # Check global agent rate limit
        if tool_name not in self.rate_limit_tracker:
            self.rate_limit_tracker[tool_name] = []
        
        # Clean old timestamps (older than 1 minute)
        cutoff_time = now - timedelta(minutes=1)
        self.rate_limit_tracker[tool_name] = [
            ts for ts in self.rate_limit_tracker[tool_name]
            if ts > cutoff_time
        ]
        
        # Check global rate limit
        if len(self.rate_limit_tracker[tool_name]) >= self.rate_limit_per_minute:
            return False
        
        # Check tool-specific rate limit
        if tool_rate_limit and len(self.rate_limit_tracker[tool_name]) >= tool_rate_limit:
            return False
        
        return True
    
    def _update_rate_limit_tracker(self, tool_name: str):
        """Update rate limit tracker after tool execution."""
        if tool_name not in self.rate_limit_tracker:
            self.rate_limit_tracker[tool_name] = []
        
        self.rate_limit_tracker[tool_name].append(datetime.utcnow())
    
    async def _log_tool_execution(self, execution_record: Dict[str, Any]):
        """Log tool execution to database."""
        try:
            log_entry = ExecutionLog(
                scenario_run_id=None,  # Will be set if we have scenario context
                agent_instance_id=self.agent_instance_id,
                level="INFO",
                message=f"Tool executed: {execution_record['tool_name']}",
                data={
                    "event_type": "TOOL_EXECUTION",
                    "tool_name": execution_record["tool_name"],
                    "parameters": execution_record["parameters"],
                    "success": execution_record["result"].get("success", False),
                    "execution_time": execution_record["timestamp"]
                }
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log tool execution: {e}", exc_info=True)


class GlobalToolIntegration:
    """Global tool integration system managing all agent tool access."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tool_registry = ToolRegistry()
        self.agent_managers: Dict[int, AgentToolManager] = {}  # agent_id -> manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("GlobalToolIntegration initialized")
    
    def get_tool_registry(self) -> ToolRegistry:
        """Get the global tool registry."""
        return self.tool_registry
    
    async def get_agent_tool_manager(
        self,
        agent_instance_id: int,
        allowed_categories: Optional[List[str]] = None,
        rate_limit_per_minute: int = 60
    ) -> AgentToolManager:
        """Get or create tool manager for an agent."""
        if agent_instance_id not in self.agent_managers:
            manager = AgentToolManager(
                agent_instance_id=agent_instance_id,
                tool_registry=self.tool_registry,
                db=self.db,
                allowed_categories=allowed_categories,
                rate_limit_per_minute=rate_limit_per_minute
            )
            self.agent_managers[agent_instance_id] = manager
        
        return self.agent_managers[agent_instance_id]
    
    async def register_custom_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any],
        category: str = "custom",
        requires_auth: bool = False,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a custom tool globally."""
        return self.tool_registry.register_tool(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            category=category,
            requires_auth=requires_auth,
            rate_limit=rate_limit,
            metadata=metadata
        )
    
    async def cleanup_agent_tools(self, agent_instance_id: int) -> bool:
        """Clean up tool manager for an agent."""
        try:
            if agent_instance_id in self.agent_managers:
                del self.agent_managers[agent_instance_id]
                self.logger.info(f"Cleaned up tool manager for agent {agent_instance_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup agent tools {agent_instance_id}: {e}", exc_info=True)
            return False
    
    def get_global_tool_stats(self) -> Dict[str, Any]:
        """Get global tool usage statistics."""
        total_tools = len(self.tool_registry.tools)
        active_agents = len(self.agent_managers)
        
        # Aggregate usage stats
        total_executions = 0
        tool_usage = {}
        
        for manager in self.agent_managers.values():
            stats = manager.get_tool_usage_stats()
            total_executions += stats["total_executions"]
            
            for tool_name, count in stats["tool_usage_counts"].items():
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + count
        
        return {
            "total_tools": total_tools,
            "active_agents": active_agents,
            "total_executions": total_executions,
            "tool_usage_counts": tool_usage,
            "categories": self.tool_registry.get_categories(),
            "most_used_tool": max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None
        }
