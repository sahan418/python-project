# test_app.py
import json
import pytest
from datetime import datetime, timedelta
from app import app, db, Task

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test data
        task1 = Task(title="Test Task 1", description="Description 1", status="pending")
        task2 = Task(title="Test Task 2", description="Description 2", status="completed")
        db.session.add(task1)
        db.session.add(task2)
        db.session.commit()
        
        with app.test_client() as client:
            yield client
            
        db.session.remove()
        db.drop_all()

def test_get_tasks(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['title'] == 'Test Task 1'
    assert data[1]['title'] == 'Test Task 2'

def test_get_tasks_with_filter(client):
    response = client.get('/api/tasks?status=completed')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['title'] == 'Test Task 2'
    assert data[0]['status'] == 'completed'

def test_get_task(client):
    response = client.get('/api/tasks/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['title'] == 'Test Task 1'
    assert data['status'] == 'pending'

def test_get_nonexistent_task(client):
    response = client.get('/api/tasks/999')
    assert response.status_code == 404

def test_create_task(client):
    new_task = {
        'title': 'New Task',
        'description': 'New Description',
        'status': 'in_progress',
        'due_date': (datetime.utcnow() + timedelta(days=1)).isoformat()
    }
    
    response = client.post(
        '/api/tasks',
        data=json.dumps(new_task),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['title'] == 'New Task'
    assert data['status'] == 'in_progress'
    
    # Verify task was added to database
    all_tasks = client.get('/api/tasks')
    assert len(json.loads(all_tasks.data)) == 3

def test_create_task_missing_title(client):
    response = client.post(
        '/api/tasks',
        data=json.dumps({'description': 'Missing title'}),
        content_type='application/json'
    )
    
    assert response.status_code == 400

def test_update_task(client):
    update_data = {
        'title': 'Updated Task',
        'status': 'completed'
    }
    
    response = client.put(
        '/api/tasks/1',
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['title'] == 'Updated Task'
    assert data['status'] == 'completed'
    assert data['description'] == 'Description 1'  # Should be unchanged

def test_delete_task(client):
    # First confirm task exists
    response = client.get('/api/tasks/1')
    assert response.status_code == 200
    
    # Delete task
    response = client.delete('/api/tasks/1')
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get('/api/tasks/1')
    assert response.status_code == 404
    
    # Check total count
    all_tasks = client.get('/api/tasks')
    assert len(json.loads(all_tasks.data)) == 1

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'