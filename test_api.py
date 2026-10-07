import pytest
from fastapi.testclient import TestClient
from task_api import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DB_PATH', str(tmp_path / 'test.db'))
    with TestClient(main.app) as client:
        yield client

def test_lifecycle(client):
    assert client.get('/health').json() == {'status':'ok'}
    response = client.post('/tasks', json={'title':'  Write tests  ','description':'pytest'})
    assert response.status_code == 201
    task = response.json()
    assert task['title'] == 'Write tests'
    tid = task['id']
    assert len(client.get('/tasks?completed=false').json()) == 1
    response = client.patch(f'/tasks/{tid}', json={'completed':True})
    assert response.json()['completed'] is True
    assert client.get('/tasks?completed=false').json() == []
    assert len(client.get('/tasks?completed=true').json()) == 1
    assert client.delete(f'/tasks/{tid}').status_code == 204
    assert client.get(f'/tasks/{tid}').status_code == 404

def test_validation(client):
    assert client.post('/tasks', json={'title':'   '}).status_code == 422
    assert client.post('/tasks', json={'title':''}).status_code == 422
    assert client.get('/tasks?limit=999').status_code == 422
    assert client.patch('/tasks/999', json={'completed':True}).status_code == 404
    response = client.post('/tasks', json={'title':'Task'})
    tid = response.json()['id']
    assert client.patch(f'/tasks/{tid}', json={'title':None}).status_code == 422
    assert client.patch(f'/tasks/{tid}', json={}).status_code == 422
