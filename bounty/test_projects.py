from bounty.models import Project, Donation

def test_project(client, user, project):
    client.login(username=user.username, password=user.password)
    assert project.status == 'pending'
    response = client.get('/projects/%d/' % project.id)
    assert 'pending' in response.content

def test_change_status(client, admin, project):
    assert admin.has_perm('projects.project.can_change_status')
    assert client.login(username=admin.username, password=admin.username)
    response = client.post('/projects/%d/change_status/' % project.id,
            {'status': 'accepted'})
    print response.content
    assert response.content == 'accepted'
    revised_project = Project.objects.get(id=project.id)
    assert revised_project.status == 'accepted'

def test_unprivleged_no_change_status(client, user, project):
    assert not user.has_perm('projects.project.can_change_status')
    assert client.login(username=user.username, password=user.username)
    response = client.post('/projects/%d/change_status/' % project.id,
            {'status': 'accepted'})
    print response.content
    assert response.content == 'not permitted'
    revised_project = Project.objects.get(id=project.id)
    assert revised_project.status == 'pending'

