# PyScrAI Stage II Development Plan
## Complete End-to-End Scenario Execution

### Current Status
✅ **Foundation Complete**: Native LLM system, AgentRuntime, Orchestration, Database layer
❌ **Missing**: Actual end-to-end scenario execution from template to completion

---

## Stage II Objectives
**Goal**: Execute a complete scenario from template → agents → LLM interactions → database persistence → completion

### Success Criteria
- [ ] Load scenario template from database
- [ ] Create agent instances from agent templates  
- [ ] Start scenario with multiple interacting agents
- [ ] Agents make real LLM calls and respond to each other
- [ ] All interactions logged to database
- [ ] Scenario runs to natural completion
- [ ] Results stored and retrievable via API

---

## Phase 2.1: Template Integration & Agent Creation (Priority 1)

### 2.1.1 Fix Template Loading
**Files**: `pyscrai/factories/scenario_factory.py`, `pyscrai/factories/agent_factory.py`
- [ ] Fix `create_scenario_run_from_template()` method
- [ ] Fix `create_agent_instance()` method  
- [ ] Ensure templates load from database correctly
- [ ] Connect agent templates to engine types (Actor/Narrator/Analyst)

### 2.1.2 Engine Factory Integration
**Files**: `pyscrai/factories/agent_factory.py`
- [ ] Update `create_agent_engine()` to use specialized engines
- [ ] Map agent template types to correct engine classes
- [ ] Ensure engines get proper configuration from templates

---

## Phase 2.2: Complete Scenario Execution Pipeline (Priority 1)

### 2.2.1 Scenario Runner Integration
**Files**: `pyscrai/engines/scenario_runner.py`
- [ ] Fix integration with ScenarioFactory
- [ ] Ensure agents are created and started properly
- [ ] Connect to database for state persistence

### 2.2.2 Agent Interaction System
**Files**: `pyscrai/engines/orchestration/engine_manager.py`
- [ ] Implement agent-to-agent communication
- [ ] Create event routing between agents
- [ ] Add conversation flow management

### 2.2.3 LLM Integration Completion
**Files**: All engine files
- [ ] Update NarratorEngine and AnalystEngine to use native LLM
- [ ] Add prompt engineering templates for each engine type
- [ ] Implement conversation memory/context

---

## Phase 2.3: Database Integration & Persistence (Priority 2)

### 2.3.1 Execution Logging
**Files**: `pyscrai/engines/agent_runtime.py`, database models
- [ ] Log all agent interactions to database
- [ ] Store LLM requests/responses
- [ ] Track scenario state changes
- [ ] Record execution metrics

### 2.3.2 API Integration
**Files**: `pyscrai/databases/api/`
- [ ] Create scenario execution endpoints
- [ ] Add real-time status monitoring
- [ ] Implement scenario control (start/stop/pause)

---

## Phase 2.4: End-to-End Testing & Demo (Priority 1)

### 2.4.1 Create Test Scenario
**Files**: New test files
- [ ] Create simple 2-agent conversation scenario template
- [ ] Create corresponding agent templates (Actor + Narrator)
- [ ] Define conversation flow/events

### 2.4.2 Integration Test
**Files**: `tests/test_end_to_end_scenario.py`
- [ ] Test complete scenario execution
- [ ] Verify database persistence
- [ ] Validate LLM interactions
- [ ] Check API endpoints

### 2.4.3 Demo Script
**Files**: `demo_scenario_execution.py`
- [ ] Create runnable demo script
- [ ] Show scenario from start to finish
- [ ] Display agent interactions
- [ ] Show database results

---

## Implementation Order

### Week 1: Core Integration
1. **Fix Template Loading** (2.1.1)
2. **Update Engine Factory** (2.1.2)  
3. **Complete LLM Integration** (2.2.3)

### Week 2: Scenario Execution
4. **Fix Scenario Runner** (2.2.1)
5. **Agent Interaction System** (2.2.2)
6. **Database Logging** (2.3.1)

### Week 3: Testing & Demo
7. **Create Test Scenario** (2.4.1)
8. **Integration Testing** (2.4.2)
9. **Demo Script** (2.4.3)

---

## Key Files to Modify

### High Priority
- `pyscrai/factories/scenario_factory.py` - Fix template loading
- `pyscrai/factories/agent_factory.py` - Fix agent creation
- `pyscrai/engines/narrator_engine.py` - Add LLM integration
- `pyscrai/engines/analyst_engine.py` - Add LLM integration
- `pyscrai/engines/scenario_runner.py` - Fix integration issues

### Medium Priority  
- `pyscrai/engines/orchestration/engine_manager.py` - Agent communication
- `pyscrai/engines/agent_runtime.py` - Database logging
- `pyscrai/databases/api/routes/scenarios.py` - Execution endpoints

### Testing
- `tests/test_end_to_end_scenario.py` - Integration test
- `demo_scenario_execution.py` - Demo script

---

## Expected Outcome

**Before Stage II**: Foundation components exist but don't work together
**After Stage II**: Complete working system where:

```python
# This should work end-to-end:
runner = ScenarioRunner(db)
scenario_id = await runner.start_scenario(
    template_name="supernatural_vision",
    agent_configs=[
        {"template_name": "pope_leo_xiii", "instance_name": "Pope Leo XIII"},
        {"template_name": "narrator", "instance_name": "Scene Narrator"}
    ]
)

# Agents interact using real LLMs, all logged to database
await runner.send_event_to_scenario(scenario_id, "vision_begins", {
    "prompt": "A supernatural vision appears before the Pope"
})

# Scenario runs to completion with full database persistence
```

This plan focuses on **integration over new features** - making existing components work together for complete scenario execution.
