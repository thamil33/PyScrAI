"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the UserControlFlowTools to allow the agent to get user input dynamically.
If the agent doesn't have enough information to complete a task, it will use the toolkit to get the information it needs from the user.
"""

from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.function import UserInputField
from agno.tools.toolkit import Toolkit
from agno.tools.user_control_flow import UserControlFlowTools
from agno.utils import pprint


class EmailTools(Toolkit):
    def __init__(self, *args, **kwargs):
        super().__init__(
            name="EmailTools", tools=[self.send_email, self.get_emails], *args, **kwargs
        )

    def send_email(self, subject: str, body: str, to_address: str) -> str:
        """Send an email to the given address with the given subject and body.

        Args:
            subject (str): The subject of the email.
            body (str): The body of the email.
            to_address (str): The address to send the email to.
        """
        return f"Sent email to {to_address} with subject {subject} and body {body}"

    def get_emails(self, date_from: str, date_to: str) -> str:
        """Get all emails between the given dates.

        Args:
            date_from (str): The start date (in YYYY-MM-DD format).
            date_to (str): The end date (in YYYY-MM-DD format).
        """
        return [
            {
                "subject": "Hello",
                "body": "Hello, world!",
                "to_address": "test@test.com",
                "date": date_from,
            },
            {
                "subject": "Random other email",
                "body": "This is a random other email",
                "to_address": "john@doe.com",
                "date": date_to,
            },
        ]


agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[EmailTools(), UserControlFlowTools()],
    markdown=True,
    debug_mode=True,
)

run_response = agent.run("Send an email with the body 'What is the weather in Tokyo?'")

# We use a while loop to continue the running until the agent is satisfied with the user input
while run_response.is_paused:
    for tool in run_response.tools_requiring_user_input:
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

    run_response = agent.continue_run(run_response=run_response)
    if not run_response.is_paused:
        pprint.pprint_run_response(run_response)
        break


run_response = agent.run("Get me all my emails")

while run_response.is_paused:
    for tool in run_response.tools_requiring_user_input:
        input_schema: Dict[str, Any] = tool.user_input_schema

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

    run_response = agent.continue_run(run_response=run_response)
    if not run_response.is_paused:
        pprint.pprint_run_response(run_response)
        break
