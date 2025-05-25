import pytest
import sqlite3

@pytest.fixture
def db_connection():
    connection = sqlite3.connect('data/pyscrai.db')
    yield connection
    connection.close()

def test_tables_created(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    expected_tables = [
        'agent_templates',
        'scenario_templates',
        'event_types',
        'scenario_runs',
        'agent_instances',
        'event_instances',
        'execution_logs'
    ]
    for table in expected_tables:
        assert table in tables

def test_insert_and_retrieve_agent_template(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO agent_templates (name, description) VALUES (?, ?)", 
                   ('Test Agent', 'A test agent for database verification'))
    db_connection.commit()
    
    cursor.execute("SELECT * FROM agent_templates WHERE name = ?", ('Test Agent',))
    agent_template = cursor.fetchone()
    assert agent_template is not None
    assert agent_template[1] == 'Test Agent'
    assert agent_template[2] == 'A test agent for database verification'