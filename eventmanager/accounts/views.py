from accounts.forms import LoginForm
from accounts.forms import SignUpForm
from accounts.forms import ChangeEmailForm
from accounts.forms import AccountDetailsForm
from accounts.forms import UserForm

from django.contrib import messages


from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash

from django.contrib.auth.decorators import login_required


from django.contrib.auth.forms import PasswordChangeForm

from django.contrib.auth.models import User

from django.shortcuts import render
from django.shortcuts import redirect

from accounts.models import AccountDetails
from events.models import Invite
from events.models import Event

from eventmanager.slugify import *


def index(request):
    return render(request, 'accounts/index.html')


def login(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return render(request, 'accounts/index.html')
        else:
            context = {'form': form, 'wrong_credentials': True}
            return render(
                request,
                'accounts/login.html',
                context
            )

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def home(request):
    return render(request, 'accounts/index.html')


@login_required
def signout(request):
    logout(request)
    return render(request, 'accounts/index.html')


def signup(request):
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        auth_login(request, user)
        dt = AccountDetails.objects.create(user=user)
        unique_slugify(dt, username)
        dt.save()
        return redirect('accounts.account')
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            success_message = 'Your password was successfully updated!'
            messages.success(request, success_message)

            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        'accounts/change_password.html',
        {
            'form': form
        }
    )


@login_required
def change_email(request):
    form = ChangeEmailForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            User.objects.filter(
                email=form.cleaned_data.get('original_email')
            ).update(email=form.cleaned_data.get('new_email'))
            success_message = 'Your email was successfully updated!'
            messages.success(request, success_message)
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'accounts/change_email.html', {'form': form})


def has_already_added_account_info(username):
    try:
        user = User.objects.all().get(username=username)
        AccountDetails.objects.get(user=user)
        return True
    except User.DoesNotExist:
        return False
    except AccountDetails.DoesNotExist:
        return False


@login_required
def account_details(request):
    form = AccountDetailsForm(request.POST, request.FILES or None)

    if request.method == 'POST':
        if has_already_added_account_info(request.user) != 0:
            return edit_account_details(request)
        if form.is_valid():
            details = form.save(commit=False)
            details.user = request.user
            if request.POST.get('birthdate'):
                details.birth_date = request.POST.get['birthdate']
            if 'profile_picture' in request.FILES:
                details.profile_picture = request.FILES['profile_picture']
            details.save()
            context = {'success_message': "added account details."}
            return render(request, 'CRUDops/successfully.html', context)

    context = {'form': form}
    return render(
        request,
        'accounts/additonal_account_information.html',
        context
    )


@login_required
def show_account_details(request):
    if has_already_added_account_info(request.user.username):
        user = User.objects.all().get(username=request.user.username)
        details = AccountDetails.objects.get(user=user)
        return render(
            request,
            'accounts/show_account_details.html',
            {
                'details': details,
                'name': request.user.first_name + request.user.last_name,
                'username': request.user.username,
                'email': request.user.email
            }
        )
    else:
        return account_details(request)


def gеt_user_by_slug(request, slug):
    if request.user.is_authenticated:
        details = AccountDetails.objects.get(slug=slug)
        user = details.user
        details = AccountDetails.objects.get(user=user)
        friend = AccountDetails.is_my_friend(request.user, user)
        return render(
            request,
            'accounts/user_account.html',
            {
                'details': details,
                'name': user.first_name + user.last_name,
                'username': user.username,
                'email': user.email,
                'friends': friend
            }
        )
    context = {'error_message': "Sorry, you are not logged in."}
    return render(request, 'CRUDops/error.html', context)


@login_required
def edit_account_details(request):
    user = User.objects.all().get(username=request.user.username)
    instance = AccountDetails.objects.get(user=user)

    form = AccountDetailsForm(
        request.POST,
        request.FILES or None,
        instance=instance)
    if request.POST:
        if form.is_valid():
            details = form.save(commit=False)
            details.user = request.user

            if request.POST.get('birthdate'):
                details.birth_date = request.POST.get('birthdate')
            if 'profile_picture'in request.FILES:
                details.profile_picture = request.FILES['profile_picture']
            details.save()
            context = {'success_message': "added account details."}
            return render(request, 'CRUDops/successfully.html', context)

    birthdate = str(instance.birth_date) or None

    context = {
        'form': form,
        'birthdate': birthdate
    }

    return render(
        request,
        'accounts/additonal_account_information.html',
        context
    )


@login_required
def list_users(request):
    users = User.objects.all().exclude(username=request.user)

    for user in users:
        if AccountDetails.objects.filter(user=user):
            details = AccountDetails.objects.get(user=user)
            user.details = details
    chunks = [users[x:x + 3] for x in range(0, len(users), 3)]
    context = {'users': chunks}
    return render(request, 'friends/all_accounts.html', context)


@login_required
def search_users(request):
    form = UserForm(request.POST or None)
    users = []
    context = {'form': form}
    logged_in_user = request.user
    if request.method == 'POST':
        if form.is_valid():
            username = request.POST.get('username')
            users = User.objects.all().filter(
                username__icontains=username).exclude(
                username=request.user)

            for user in users:
                if AccountDetails.objects.filter(user=user):
                    details = AccountDetails.objects.get(user=user)
                    user.details = details
                user.my_friend = AccountDetails.is_my_friend(
                    request.user, user)
            context = {'users': users, 'form': form}

    return render(request, 'friends/find_account.html', context)


@login_required
def my_friends(request):
    friends = []
    if AccountDetails.objects.filter(user=request.user).exists():
        friends = AccountDetails.objects.get(user=request.user).friends.all()
        for user in friends:
            if AccountDetails.objects.filter(user=user):
                details = AccountDetails.objects.get(user=user)
                user.details = details
                user.unfriend_url = "users/" + user.details.slug + "/unfriend"

    chunks = [friends[x:x + 3] for x in range(0, len(friends), 3)]
    context = {'users': chunks, 'title': "My friends:"}
    return render(request, 'friends/all_accounts.html', context)


@login_required
def friend(request, slug):
    logged_in_user = request.user
    logged_in_user_details = AccountDetails.objects.get(user=logged_in_user)
    other_user_details = AccountDetails.objects.get(slug=slug)
    other_user = other_user_details.user
    logged_in_user_details.friends.add(other_user)
    context = {
        'success_message': "sent friend request to  " + other_user.username}
    return render(request, 'CRUDops/successfully.html', context)


@login_required
def unfriend(request, slug):
    logged_in_user = request.user
    logged_in_user_details = AccountDetails.objects.get(user=logged_in_user)
    other_user_details = AccountDetails.objects.get(slug=slug)
    other_user = other_user_details.user
    logged_in_user_details.friends.remove(other_user)
    other_user_details.friends.remove(logged_in_user)
    context = {'success_message': "unfriended  " + other_user.username}
    return render(request, 'CRUDops/successfully.html', context)
