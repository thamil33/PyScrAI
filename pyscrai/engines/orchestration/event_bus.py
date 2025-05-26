# pyscrai/engines/event_bus.py

from collections import defaultdict
from typing import Callable, Any, DefaultDict

class EventBus:
    """
    A simple publish-subscribesystem for inter-engine communication.
    Allows different parts of the system to communicate without direct dependencies.
    """
    def __init__(self):
        """Initializes the EventBus."""
        self.subscribers: DefaultDict[str, list[Callable[[Any], None]]] = defaultdict(list)
        print("EventBus initialized.")

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Subscribes a callback function to a specific event type.
        Args:
            event_type (str): The type of event to subscribe to.
            callback (Callable[[Any], None]): The function to call when the event is published.
        """
        if not event_type:
            raise ValueError("Event type cannot be empty.")
        if not callable(callback):
            raise TypeError("Callback must be a callable function.")
        
        self.subscribers[event_type].append(callback)
        print(f"Callback {callback.__name__} subscribed to event '{event_type}'.")

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Unsubscribes a callback function from a specific event type.
        Args:
            event_type (str): The type of event to unsubscribe from.
            callback (Callable[[Any], None]): The callback function to remove.
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                print(f"Callback {callback.__name__} unsubscribed from event '{event_type}'.")
                if not self.subscribers[event_type]: # Remove event type if no subscribers left
                    del self.subscribers[event_type]
            except ValueError:
                print(f"Warning: Callback {callback.__name__} not found for event '{event_type}' during unsubscribe.")
        else:
            print(f"Warning: Event type '{event_type}' not found during unsubscribe.")

    def publish(self, event_type: str, data: Any = None):
        """
        Publishes an event to all subscribed callbacks for that event type.
        Args:
            event_type (str): The type of event to publish.
            data (Any, optional): The data to pass to the event callbacks. Defaults to None.
        """
        if event_type in self.subscribers:
            print(f"Publishing event '{event_type}' with data: {str(data)[:100]}... ({len(self.subscribers[event_type])} subscribers)")
            # Iterate over a copy in case a callback modifies the subscriber list
            for callback in list(self.subscribers[event_type]):
                try:
                    callback(data)
                except Exception as e:
                    # Log the error and continue to other subscribers
                    print(f"Error in callback {callback.__name__} for event '{event_type}': {e}")
        else:
            print(f"No subscribers for event '{event_type}'. Event not published.")

if __name__ == '__main__':
    # This section is for basic testing and demonstration.
    print("Running EventBus example...")
    event_bus = EventBus()

    # Define some callback functions
    def handler_alpha(data: Any):
        print(f"Handler Alpha received: {data}")

    def handler_beta(data: Any):
        print(f"Handler Beta received: {data}")
        if isinstance(data, dict) and data.get("error"): 
            raise ValueError("Simulated error in Handler Beta")

    def handler_gamma(data: Any):
        print(f"Handler Gamma (also for EVENT_X) received: {data}")

    # Subscribe handlers to events
    event_bus.subscribe("EVENT_X", handler_alpha)
    event_bus.subscribe("EVENT_X", handler_beta)
    event_bus.subscribe("EVENT_Y", handler_beta)
    event_bus.subscribe("EVENT_X", handler_gamma)

    # Publish some events
    print("\nPublishing EVENT_X with simple data:")
    event_bus.publish("EVENT_X", "Hello from EVENT_X!")

    print("\nPublishing EVENT_Y with a dictionary:")
    event_bus.publish("EVENT_Y", {"message": "Data for EVENT_Y", "value": 123})
    
    print("\nPublishing EVENT_Z (no subscribers):")
    event_bus.publish("EVENT_Z", "This should not be seen by any handler.")

    # Unsubscribe a handler
    print("\nUnsubscribing handler_alpha from EVENT_X...")
    event_bus.unsubscribe("EVENT_X", handler_alpha)
    event_bus.publish("EVENT_X", "Hello again from EVENT_X after Alpha unsubscribe!")

    # Test error handling in a subscriber
    print("\nPublishing EVENT_X with data that causes an error in Beta handler:")
    event_bus.publish("EVENT_X", {"message": "Trigger error", "error": True})

    # Test unsubscribing a non-existent handler or event type
    print("\nAttempting to unsubscribe a non-existent handler:")
    def non_existent_handler(data: Any): pass
    event_bus.unsubscribe("EVENT_X", non_existent_handler)
    event_bus.unsubscribe("NON_EXISTENT_EVENT", handler_alpha)

    print("\nEventBus example finished.")
