import datetime
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from bounty.forms import (ProjectForm, ProjectStatusForm, DonationForm,
        ContributionForm)
from bounty.models import Project, Donation, Contribution, Notification
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

def index(request):
    created = Project.objects.exclude(status="completed").order_by('-created')[:4]
    completed = Project.objects.filter(status="completed").order_by('-completed_date')[:4]
    donations = Donation.objects.paid().order_by('-created')[:4]
    contributions = Contribution.objects.all().order_by('-created')[:4]
    return render_to_response('index.html', RequestContext(request, {
        'created': created,
        'completed': completed,
        'donations': donations,
        'contributions': contributions}))

@login_required
def profile(request):
    created_projects = request.user.project_set.all()
    contributed_projects = Project.objects.filter(contributions__user=request.user)
    donated_projects = Project.objects.filter(donations__user=request.user)
    return render_to_response('profile.html', RequestContext(request,
        {'created': created_projects,
            'contributed': contributed_projects,
            'donated': donated_projects
            }))

@login_required
def new_project(request):
    if request.POST:
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            return redirect(form.instance.get_absolute_url())
    else:
        form = ProjectForm()
    return render_to_response('project_form.html', RequestContext(
        request, {'form': form})) 

def view_project(request, project_id):
    page_dict = {}
    project = get_object_or_404(Project, id=project_id)
    page_dict['project'] = project
    if request.user.has_perm('project.can_change_status'):
        page_dict['status_form'] = ProjectStatusForm(instance=project)
    if request.user.has_perm('project.can_change_project') or request.user == project.creator:
        page_dict['can_change_project'] = True
    if request.user.is_authenticated() and project.status=="accepted":
        page_dict['donation_form'] = DonationForm()
    if request.user.is_authenticated():
        try:
            page_dict['wants_notification'] = Notification.objects.get(user=request.user, project = project).notify
        except ObjectDoesNotExist:
            page_dict['wants_notification'] = False

    return render_to_response('view_project.html', RequestContext(
        request, page_dict))

def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.creator != request.user and not request.user.has_perm('contribution.can_change_contribution'):
        return HttpResponse('not permitted', status='403 forbidden')

    if request.POST:
        form = ProjectForm(instance=project, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(form.instance.get_absolute_url())
    else:
        form = ProjectForm(instance=project)
    return render_to_response('project_form.html', RequestContext(request, {'form': form}))

def change_project_status(request, project_id):
    if not request.POST:
        return HttpResponse("bad method", status='405 method not allowed')
    if not request.user.has_perm('project.can_change_status'):
        return HttpResponse('not permitted', status='403 forbidden')
    project = get_object_or_404(Project, id=project_id)
    form = ProjectStatusForm(instance=project, data=request.POST)
    instance = form.save(commit=False)
    if instance.status == 'completed':
        instance.completed_date = datetime.date.today()
    instance.save()
    return HttpResponse(instance.status)

@login_required
def donate(request, project_id):
    if not request.POST:
        return HttpResponse("bad method", status='405 method not allowed')
    project = get_object_or_404(Project, id=project_id)
    form = DonationForm(request.POST)
    if form.is_valid():
        donation = form.save(commit=False)
        donation.user = request.user
        donation.project = project
        donation.save()
        return render_to_response("donate.html", RequestContext(
            request, {'amount': form.cleaned_data['amount'],
                'project': project, 'item_code': donation.id}))
    else:
        return render_to_response("form.html", RequestContext(
            request, {'form': form}))

@login_required
def cancel_notification(request, project_id):
    return _change_notify(request, project_id, False)

@login_required
def enable_notification(request, project_id):
    return _change_notify(request, project_id, True)

def _change_notify(request, project_id, notify):
    project = get_object_or_404(Project, id=project_id)
    notification, created = Notification.objects.get_or_create(
            project=project, user=request.user)
    notification.notify=notify
    notification.save()
    return redirect(project.get_absolute_url())

def donation_notify(request): 
    if not request.POST:
        return HttpResponse("bad method", status='405 method not allowed')

    if request.POST['ap_securitycode'] != settings.ALERTPAY_SECURITY_CODE:
        return HttpResponse("not permitted", status='403 not permitted')

    if request.POST['ap_status'].lower() == 'success':
        donation = get_object_or_404(Donation, id=request.POST['ap_itemcode'],
                amount=request.POST['ap_amount'])
        donation.status = 'paid'
        donation.save()
    
    return HttpResponse("received")

def list_projects(request, project_status=None):
    projects = Project.objects.all().order_by('status', '-created')
    if project_status:
        projects = projects.filter(status=project_status)

    return render_to_response("project_list.html", RequestContext(request, 
        {'projects': projects}))

@login_required
def new_contribution(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.POST:
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.user = request.user
            contribution.project = project
            contribution.save()
            return redirect(contribution.get_absolute_url())
    else:
        form = ContributionForm()
    return render_to_response('contribution_form.html', RequestContext(request, {'form': form})) 

def contribution(request, project_id, contribution_id):
    project = get_object_or_404(Project, id=project_id)
    contribution = get_object_or_404(project.contributions, id=contribution_id)
    return render_to_response('view_contribution.html', RequestContext(request,
        {'contribution': contribution, 'project': project, 'can_edit': contribution.user == request.user or request.user.has_perm('contribution.can_change_contribution')}))

def edit_contribution(request, project_id, contribution_id):
    project = get_object_or_404(Project, id=project_id)
    contribution = get_object_or_404(project.contributions, id=contribution_id)
    if contribution.user != request.user and not request.user.has_perm('contribution.can_change_contribution'):
        return HttpResponse('not permitted', status='403 forbidden')

    if request.POST:
        form = ContributionForm(instance=contribution, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(form.instance.get_absolute_url())
    else:
        form = ContributionForm(instance=contribution)
    return render_to_response('contribution_form.html', RequestContext(request, {'form': form}))

