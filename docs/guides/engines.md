# Working with Engines

This guide explains PyScrAI's engine architecture and how to work with different engine types.

## Engine Architecture

PyScrAI uses an extensible engine architecture with `BaseEngine` as the foundation.

### BaseEngine

The `BaseEngine` class provides core functionality:

```python
from pyscrai.engines import BaseEngine

class BaseEngine:
    """Base class for all PyScrAI engines."""
    
    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[RunResponse]:
        """Process an event and generate a response."""
        
    async def aprocess_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[RunResponse]:
        """Asynchronously process an event."""
        
    def get_state(self) -> Dict[str, Any]:
        """Get the current engine state."""
        
    def load_state(self, state: Dict[str, Any]) -> None:
        """Load a state into the engine."""
```

### Actor Engine

The `ActorEngine` extends `BaseEngine` to simulate characters:

```python
from pyscrai.engines import ActorEngine
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Create an Agno agent
llm_model = OpenAIChat(model="gpt-3.5-turbo")
agent = Agent(model=llm_model)

# Create an actor engine
actor = ActorEngine(
    agent=agent,
    character_name="Captain Pegleg Pete",
    personality_traits="A gruff pirate who loves treasure"
)

# Process an event
response = actor.process_event(
    event_type="dialogue_prompt",
    event_data={"prompt": "What do you think about parrots?"}
)
```

## Event Processing

Engines process events through the `process_event` method:

```python
# Synchronous processing
response = engine.process_event(
    event_type="event_type",
    event_data={...}
)

# Asynchronous processing
response = await engine.aprocess_event(
    event_type="event_type",
    event_data={...}
)
```

## State Management

Engines support state persistence:

```python
# Get current state
state = engine.get_state()

# Load state
engine.load_state(state)
```

## Creating Custom Engines

1. Inherit from `BaseEngine`:
```python
from pyscrai.engines import BaseEngine

class CustomEngine(BaseEngine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Custom initialization
        
    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[RunResponse]:
        # Custom event processing
        return response
```

2. Implement required methods:
- `process_event` / `aprocess_event`
- `get_state` / `load_state`

## Best Practices

1. **Event Processing**
   - Validate event data before processing
   - Handle all possible event types
   - Provide meaningful error messages
   - Use appropriate logging

2. **State Management**
   - Include all necessary state in `get_state()`
   - Validate state when loading
   - Handle missing or invalid state gracefully

3. **Error Handling**
   - Catch and log exceptions
   - Return meaningful error responses
   - Maintain consistent state

4. **Async Support**
   - Implement both sync and async methods
   - Use appropriate async patterns
   - Handle cancellation properly

## Example: Custom Narrator Engine

Here's an example of a custom engine for narration:

```python
from pyscrai.engines import BaseEngine
from typing import Optional, Dict, Any
from agno.run.response import RunResponse

class NarratorEngine(BaseEngine):
    def __init__(
        self,
        style: str = "descriptive",
        tone: str = "neutral",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.style = style
        self.tone = tone
        
    def process_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Optional[RunResponse]:
        if event_type == "narrate_scene":
            scene = event_data.get("scene")
            if not scene:
                self.logger.error("No scene provided for narration")
                return None
                
            # Enhance scene with style and tone
            prompt = f"Narrate this scene in a {self.style} style with a {self.tone} tone: {scene}"
            
            try:
                response = self.agent.run(message=prompt)
                return response
            except Exception as e:
                self.logger.error(f"Error during narration: {e}")
                return None
                
        return None
        
    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({
            "style": self.style,
            "tone": self.tone
        })
        return state
        
    def load_state(self, state: Dict[str, Any]) -> None:
        super().load_state(state)
        self.style = state.get("style", self.style)
        self.tone = state.get("tone", self.tone)
```

Using the custom engine:

```python
narrator = NarratorEngine(
    agent=narrator_agent,
    style="vivid",
    tone="mysterious"
)

response = narrator.process_event(
    event_type="narrate_scene",
    event_data={
        "scene": "The old mansion stood silent in the moonlight"
    }
)
```
