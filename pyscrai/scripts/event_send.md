# PyScrAI Scenario Event Examples

This document lists common events you can send to a running scenario (e.g., scenario ID 6) using the `send_scenario_event.py` script. Adjust the `--id` value to match your scenario.

---

## 1. User Input Event
Send a user message to the scenario (e.g., to the protagonist or all agents).

```sh
python -m pyscrai.scripts.send_scenario_event --id 6 --type "user_input" --message "Hello, protagonist!"

```

```sh

python -m pyscrai.scripts.send_scenario_event --id 6 --type "user_input" --message "I have something to say." --actor_id "protagonist_agent_id"

```




---

## 2. Scene Transition Event
Change the current scene in the scenario.

```sh
python -m pyscrai.scripts.send_scenario_event --id 6 --type "scene_transition" --data scene_transition.json
```

Where `scene_transition.json` contains:
```json
{
  "scene_name": "forest",
  "description": "The protagonist enters a mysterious forest."
}
```

---

## 3. System Event (Pause Scenario)
Pause the scenario execution.

```sh
python -m pyscrai.scripts.send_scenario_event --id 6 --type "system_pause"
```

---

## 4. Custom Event (Any JSON Payload)
Send a custom event with arbitrary data.

```sh
python -m pyscrai.scripts.send_scenario_event --id 6 --type "custom_event" --data custom_event.json
```

Where `custom_event.json` contains:
```json
{
  "custom_key": "custom_value",
  "note": "This is a custom event payload."
}
```

---

## 5. Targeted Agent Event
Send an event to a specific agent (e.g., agent ID 12).

```sh
python -m pyscrai.scripts.send_scenario_event --id 6 --type "user_input" --message "Only for you!" --agent 12
```

---

## Notes
- You can combine `--message` and `--data` to send both a message and a JSON payload.
- Use `python -m pyscrai.scripts.monitor_scenario --id 6 --watch` to monitor scenario status and responses in real time.
- Event types and payloads may vary depending on your scenario template and agent logic.
