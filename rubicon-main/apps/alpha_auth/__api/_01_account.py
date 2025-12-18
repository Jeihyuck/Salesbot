import uuid
import traceback
from alpha import __log
from icecream import ic
from django.db.models import F, Q
from django_pandas.io import read_frame
from django.forms.models import model_to_dict
from datetime import datetime
# from sqlalchemy.orm import load_only

from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from apps.alpha_auth.models import Alpha_User
# from apps.alpha_base.models import Alpha_Menu, Alpha_API
from apps.alpha_auth import __function

from alpha.settings import DEBUG, bcolors, BASE_URL, API_URL_PREFIX


def create_user(request_dict):
    user = Alpha_User(
        username=request_dict['query']['id'],  # `id` corresponds to the username
        full_name=request_dict['query']['username'],  # `id` corresponds to the username
        department=request_dict['query']['department'],  # `id` corresponds to the username
        password=make_password(request_dict['query']['password'])  # Hash the password
    )
    user.save()
    return True, None, None, None


def resetPassword(request_dict):
    user = request_dict['query']['user']['id']
    update_user = User.objects.get(id=user)
    # update_username = update_user.username
    password = str(uuid.uuid4()).replace('-', '')[:10]
    # # ic(password)
    update_user.set_password(password)
    update_user.save()
    Alpha_User.objects.filter(user=update_user).update(init_password=password, is_first_login=True, date_password_changed = datetime.now())

    # alpha_user = Alpha_User.objects.get(user=update_user)
    
    return password, None 

# def updateUser(request_dict):
#     # update_user = Alpha_User.objects.get(id=request_dict['query']['id'])
#     role = Alpha_Group.objects.get(id=request_dict['query']['role'])
#     # # update_user.set_password(password)
#     Alpha_User.objects.filter(id=request_dict['query']['id']).update(\
#         name=request_dict['query']['name'], \
#         grade=request_dict['query']['grade'], \
#         email=request_dict['query']['email'], \
#         company=request_dict['query']['company'], \
#         org_level_1=request_dict['query']['org_level_1'], \
#         org_level_2=request_dict['query']['org_level_2'], \
#         org_level_3=request_dict['query']['org_level_3'], \
#         role=role)

#     return True, None, None, None


def deleteUser(request_dict):
    alpha_user_id = request_dict['query']['id']
    alpha_user = Alpha_User.objects.get(id=alpha_user_id)
    user = User.objects.get(id=alpha_user.user_id)
    # LogEntry.filter(user=user).delete()
    user.delete()
    alpha_user.delete()
    return True, None, None, None



def get_user_info(request_dict):
    try:
        user = Alpha_User.objects.values('user__username', 'username','grade', 'email', 'company', 'org_level_1', 'org_level_2', 'role__name').get(user__username=request_dict['user']['username'])
        return {'success': True, 'data': user}
    except Exception as e:
        return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}


def getUserList(request_dict):
    users = Alpha_User.objects

    if request_dict['query']['company'] != "":
        users = users.filter(company = request_dict['query']['company'])
    if request_dict['query']['role'] != "":
        users = users.filter(role__name = request_dict['query']['role'])
    if request_dict['query']['search'] != "" and request_dict['query']['search'] != None :
        users = users.filter(Q(name__icontains=request_dict['query']['search']) | Q(company__icontains=request_dict['query']['search']) | Q(org_level_1__icontains=request_dict['query']['search']) | Q(org_level_2__icontains=request_dict['query']['search']))

    users = users.all().order_by('name')
    paginator = Paginator(users.values('id', 'name', 'grade', 'org_level_1', 'org_level_2', 'org_level_3', 'email', 'company', 'role').annotate(username=F('user__username'), rolename=F('role__name')), per_page=request_dict['paging']['itemsPerPage'], orphans=0)
# 
    data = list(paginator.page(int(request_dict['paging']['page'])))
    return data, [{'itemCount': len(users)}]



# def createRole(request_dict):
#     name = request_dict['query']['name']
#     desc = request_dict['query']['desc']
#     is_admin = request_dict['query']['is_admin']

#     role = Alpha_Group.objects.create(name=name, desc=desc, is_admin=is_admin)

#     return True, None, None, None


# def deleteRole(request_dict):
#     role_id = request_dict['query']['id']
#     Alpha_Group.objects.filter(id=role_id).delete()
#     return True, None, None, None


