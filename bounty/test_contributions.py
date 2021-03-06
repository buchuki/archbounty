from bounty.forms import ContributionForm
from bounty.models import Contribution, Project

def pytest_funcarg__contribution(request):
    project = request.getfuncargvalue('project')
    return Contribution.objects.create(
            user=project.creator, project=project, percentage=5)

def test_form():
    form = ContributionForm()
    assert len(form.fields) == 3

def test_user_can_edit(client, contribution):
    assert client.login(username=contribution.user.username,
            password=contribution.user.username)
    response = client.post('/projects/%d/contributions/%d/edit/' % (
        contribution.project.id, contribution.id), {'submit': 'true'})
    assert response.status_code != "403 forbidden"

def test_admin_can_edit(client, admin, contribution):
    assert client.login(username=admin.username, password=admin.username)
    response = client.post('/projects/%d/contributions/%d/edit/' % (
        contribution.project.id, contribution.id), {'submit': 'true'})
    assert response.status_code != "403 forbidden"

def test_anon_cant_edit(client, contribution):
    response = client.post('/projects/%d/contributions/%d/edit/' % (
        contribution.project.id, contribution.id), {'submit': 'true'})
    print response.status_code
    assert response.status_code == "403 forbidden"

def test_other_user_cant_edit(client, admin, contribution):
    user = contribution.user
    contribution.user = admin
    contribution.save()
    assert client.login(username=user.username, password=user.username)
    response = client.post('/projects/%d/contributions/%d/edit/' % (
        contribution.project.id, contribution.id), {'submit': 'true'})
    print response.status_code
    assert response.status_code == "403 forbidden"
