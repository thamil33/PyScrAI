def test_create_agent_template(db_session):
    agent_template = AgentTemplate(name="Test Agent", description="A test agent template.")
    db_session.add(agent_template)
    db_session.commit()
    
    assert agent_template.id is not None

def test_load_agent_template(db_session):
    agent_template = db_session.query(AgentTemplate).filter_by(name="Test Agent").first()
    
    assert agent_template is not None
    assert agent_template.name == "Test Agent"

def test_create_scenario_template(db_session):
    scenario_template = ScenarioTemplate(name="Test Scenario", description="A test scenario template.")
    db_session.add(scenario_template)
    db_session.commit()
    
    assert scenario_template.id is not None

def test_load_scenario_template(db_session):
    scenario_template = db_session.query(ScenarioTemplate).filter_by(name="Test Scenario").first()
    
    assert scenario_template is not None
    assert scenario_template.name == "Test Scenario"