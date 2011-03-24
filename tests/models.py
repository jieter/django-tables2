from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import *
import django_tables as tables
from django_attest import TestContext
from attest import Tests


models = Tests()
models.context(TestContext())


@models.context
def samples():
    class Context(object):
        class UserTable(tables.Table):
            username = tables.Column()
            first_name = tables.Column()
            last_name = tables.Column()
            email = tables.Column()
            password = tables.Column()
            is_staff = tables.Column()
            is_active = tables.Column()
            is_superuser = tables.Column()
            last_login = tables.Column()
            date_joined = tables.Column()

    # we're going to test against User, so let's create a few
    User.objects.create_user('fake-user-1', 'fake-1@example.com', 'password')
    User.objects.create_user('fake-user-2', 'fake-2@example.com', 'password')
    User.objects.create_user('fake-user-3', 'fake-3@example.com', 'password')
    User.objects.create_user('fake-user-4', 'fake-4@example.com', 'password')

    yield Context


@models.test
def simple(dj, samples):
    users = User.objects.all()
    table = samples.UserTable(users)

    for index, row in enumerate(table.rows):
        user = users[index]
        Assert(user.username) == row['username']
        Assert(user.email) == row['email']
