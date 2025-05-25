"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the `requires_user_input` parameter to allow users to provide input externally.
"""

from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint


# You can either specify the user_input_fields leave empty for all fields to be provided by the user
@tool(requires_user_input=True, user_input_fields=["to_address"])
def send_email(subject: str, body: str, to_address: str) -> str:
    """
    Send an email.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_address (str): The address to send the email to.
    """
    return f"Sent email to {to_address} with subject {subject} and body {body}"


agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[send_email],
    markdown=True,
)

agent.run("Send an email with the subject 'Hello' and the body 'Hello, world!'")
if agent.is_paused:  # Or agent.run_response.is_paused
    for tool in agent.run_response.tools_requiring_user_input:
        input_schema: List[UserInputField] = tool.user_input_schema

        for field in input_schema:
            # Get user input for each field in the schema
            field_type = field.field_type
            field_description = field.description

            # Display field information to the user
            print(f"\nField: {field.name}")
            print(f"Description: {field_description}")
            print(f"Type: {field_type}")

            # Get user input
            if field.value is None:
                user_value = input(f"Please enter a value for {field.name}: ")
            else:
                print(f"Value: {field.value}")
                user_value = field.value

            # Update the field value
            field.value = user_value

    run_response = (
        agent.continue_run()
    )  # or agent.continue_run(run_response=agent.run_response)
    pprint.pprint_run_response(run_response)

# Or for simple debug flow
# agent.print_response("Send an email with the subject 'Hello' and the body 'Hello, world!'")
