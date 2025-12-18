import uuid
from icecream import ic
from django.db.models import F, Q
from django_pandas.io import read_frame
from django.forms.models import model_to_dict
# from sqlalchemy.orm import load_only
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from django.core.paginator import Paginator
from apps.alpha_auth.models import Alpha_User, Alpha_Role, Alpha_Menu_Permission, Alpha_API_Permission
from apps.alpha_base.models import Alpha_Menu, Alpha_API
from apps.alpha_auth import __function

from alpha.settings import DEBUG, bcolors, BASE_URL, API_URL_PREFIX


# def __check_custom_permission(request_dict):
#     # ic(request_dict)
#     try:
#         alpha_user, alpha_role = account_function.getRoleByUsername(request_dict['user']['username'])
#         # ic(alpha_user.__dict__)
#         # ic(alpha_role.__dict__)

#         user_division = alpha_user.org_level_1[0:2]
#         user_branch = alpha_user.org_level_2

#         # ic(user_division)
#         check_permission_type = request_dict['query']['checkPermissionType']

#         with session_scope() as session:
#             result_set = session.query(meta).filter(meta.name == check_permission_type)
#         fields = ['value']

#         # result_set = result_set.options(load_only(*fields)).all()
#         # data = [u.__dict__['value'] for u in result_set]

#         # ic(data)
#         if check_permission_type == 'division':
#             if alpha_role.name == 'DEV' or alpha_role.name == 'ADMIN':
#                 result_set = result_set.options(load_only(*fields)).all()
#                 data = [u.__dict__['value'] for u in result_set]

#             elif alpha_role.name == 'DIVISION_USER' or alpha_role.name == 'BRANCH_USER':
#                 result_set = result_set.filter(meta.value == user_division).options(load_only(*fields)).all()
#                 data = [u.__dict__['value'] for u in result_set]


#         elif check_permission_type == 'branch':
#             if alpha_role.name == 'DEV' or alpha_role.name == 'ADMIN':
#                 result_set = result_set.options(load_only(*fields)).all()
#                 data = [u.__dict__['value'] for u in result_set]
#             elif alpha_role.name == 'DIVISION_USER':
#                 result_set = result_set.filter(meta.parent_value == user_division).options(load_only(*fields)).all()
#                 data = [u.__dict__['value'] for u in result_set]
#             elif alpha_role.name == 'BRANCH_USER':
#                 result_set = result_set.filter(meta.value == user_branch).options(load_only(*fields)).all()
#                 data = [u.__dict__['value'] for u in result_set]

#         elif check_permission_type == 'object':
#             object_uuid = request_dict['query']['objectUUID']
#             alpha_ServiceAlpha_API = Alpha_API.objects.get(object_uuid = object_uuid)
#             alpha_ServiceAlpha_API_permission = Alpha_API_Permission.objects.get(object = alpha_ServiceAlpha_API, role = alpha_role)

#             data = alpha_ServiceAlpha_API_permission.permission
#             # ic(data)

#         return {'success': True, 'data': data}
#     except Exception as e:
#
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}    


def createUser(request_dict):
    # Check if user exists in 'auth_user'
    check_exist_user = User.objects.filter(username=request_dict['query']['username']).exists()
    # Check if user exists in 'alpha_auth_alpha_user'
    check_exist_alpha_user = Alpha_User.objects.filter(user__username=request_dict['query']['username']).exists()

    if check_exist_user == True and check_exist_alpha_user == False:
        User.objects.filter(username=request_dict['query']['username']).delete()
    elif check_exist_user == False and check_exist_alpha_user == True:
        Alpha_User.objects.filter(username=request_dict['query']['username']).delete()
    elif check_exist_user == True and check_exist_alpha_user == True:
        return 'User Already Exists', None, None

    password = str(uuid.uuid4()).replace('-', '')[:10]

    created_user = User.objects.create_user(username=request_dict['query']['username'], email=request_dict['query']['email'], password=password)
    user = Alpha_User.objects.create(user=created_user,
        name=request_dict['query']['name'],
        email=request_dict['query']['email'], 
        init_password=password,
        grade=request_dict['query']['grade'],
        company=request_dict['query']['company'],
        org_level_1=request_dict['query']['org_level_1'],
        org_level_2=request_dict['query']['org_level_2'],
        org_level_3=request_dict['query']['org_level_3'],
        role=Alpha_Role.objects.get(id=request_dict['query']['role']))
    user = model_to_dict(user)
    user['password'] = password

    return user, None, None



# def __create_alpha_superuser(request_dict):
#     user = request_dict['query']['user']
#     username = request_dict['query']['username']
#     # password = request_dict['query']['password']
#     email = request_dict['query']['email']
#     company = request_dict['query']['company']
#     org_level_1 = request_dict['query']['org_level_1']
#     org_level_2 = request_dict['query']['org_level_2']
#     org_level_3 = request_dict['query']['org_level_3']
#     grade = request_dict['query']['grade']
#     role = request_dict['query']['role']
#     password = str(uuid.uuid4()).replace('-', '')[:10]

#     created_user = User.objects.create_superuser(username=user, email=email, password=password)
#     user = Alpha_User.objects.create(user=created_user, username=username, email=email, init_password=password, grade=grade, \
#         company=company,  org_level_1=org_level_1, org_level_2=org_level_2, org_level_3=org_level_3, role=Alpha_Role.objects.get(id=role))
#     user = model_to_dict(user)
#     user['password'] = password

#     return {'data': user}
   


# def __change_password(request_dict):

#     username = request_dict['user']['username']
#     password = request_dict['query']['password']

#     if password != '' and password != None:
#         update_user = User.objects.get(username=username)
#         update_user.set_password(password)
#         update_user.save()
#         Alpha_User.objects.filter(user=update_user).update(init_password = '-', date_password_changed = datetime.now())

   

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
    
    return password, None, None

        # html_content = """<p><span style="font-size:16px;">{} 계정의 패스워드가 &#39;<span class="marker"><strong>{}</strong></span>&#39; 로 초기화되었습니다.</span></p>
        # <br/>
        # <p><span style="font-size:16px;"><a href="https://dp.gscaltex.co.kr/">다이나믹 프라이싱 시스템</a>에 로그인하여 패스워드를 변경 후 사용하시기 바랍니다.</span></p>
        # <br/>
        # <p><span style="font-size:16px;">감사합니다.</span></p>

        # """.format(update_username, password)

        # utils.sendMail('c17392@gscaltex.com', alpha_user.email, '패스워드 초기화 안내', html_content)



def updateUser(request_dict):
    # update_user = Alpha_User.objects.get(id=request_dict['query']['id'])
    role = Alpha_Role.objects.get(id=request_dict['query']['role'])
    # # update_user.set_password(password)
    Alpha_User.objects.filter(id=request_dict['query']['id']).update(\
        name=request_dict['query']['name'], \
        grade=request_dict['query']['grade'], \
        email=request_dict['query']['email'], \
        company=request_dict['query']['company'], \
        org_level_1=request_dict['query']['org_level_1'], \
        org_level_2=request_dict['query']['org_level_2'], \
        org_level_3=request_dict['query']['org_level_3'], \
        role=role)

    return True, None, None, None


def deleteUser(request_dict):
    alpha_user_id = request_dict['query']['id']
    alpha_user = Alpha_User.objects.get(id=alpha_user_id)
    user = User.objects.get(id=alpha_user.user_id)
    # LogEntry.filter(user=user).delete()
    user.delete()
    alpha_user.delete()
    return True, None, None, None



# def __get_alpha_user_info(request_dict):
#     try:
#         user = Alpha_User.objects.values('user__username', 'username','grade', 'email', 'company', 'org_level_1', 'org_level_2', 'role__name').get(user__username=request_dict['user']['username'])
#         # ic(user) 
#         return {'success': True, 'data': user}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}


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
    return data, [{'itemCount': len(users)}], None



def createRole(request_dict):
    name = request_dict['query']['name']
    desc = request_dict['query']['desc']
    is_admin = request_dict['query']['is_admin']

    role = Alpha_Role.objects.create(name=name, desc=desc, is_admin=is_admin)
        # auth_table = list(Alpha_Table.objects.all().values())
        # for row in auth_table:
        #     table = Alpha_Table.objects.get(table_uuid=row['table_uuid'])
        #     if is_admin:
        #         bjects.create(role=role, table=table, create=True, read=True, update=True, delete=True)
        #     else:
        #         bjects.create(role=role, table=table, create=False, read=False, update=False, delete=False)

        # auth_menu = list(Alpha_Menu.objects.all().values())
        # for row in auth_menu:
        #     menu = Alpha_Menu.objects.get(menu_uuid=row['menu_uuid'])
        #     if is_admin:
        #         Alpha_Menu_Permission.objects.create(role=role, menu=menu, permission=True)
        #     else:
        #         Alpha_Menu_Permission.objects.create(role=role, menu=menu, permission=False)


    return True, None, None, None


# def __update_alpha_role(request_dict):
#     ic('__update_alpha_role')
#     try:
#         role_id = request_dict['query']['_id']
#         name = request_dict['query']['name']
#         desc = request_dict['query']['desc']
#         # is_admin = request_dict['query']['is_admin']

#         role = Alpha_Role.objects.get(id=role_id)
#         # if role.is_admin == False and is_admin == True:
#         #     auth_table = list(Alpha_Table.objects.all().values())
#         #     for row in auth_table:
#         #         table = Alpha_Table.objects.get(table_uuid=row['table_uuid'])
#         #         bjects.filter(role=role, table=table).update(create=True, read=True, update=True, delete=True)

#         #     auth_menu = list(Alpha_Menu.objects.all().values())
#         #     for row in auth_menu:
#         #         menu = Alpha_Menu.objects.get(menu_uuid=row['menu_uuid'])
#         #         Alpha_Menu_Permission.objects.filter(role=role, menu=menu).update(permission=True)

#         Alpha_Role.objects.filter(id=role_id).update(name=name, desc=desc)

#         return {'success' : True}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}

def deleteRole(request_dict):
    role_id = request_dict['query']['id']
    Alpha_Role.objects.filter(id=role_id).delete()
    return True, None, None, None


def getRoleList(request_dict):
    roles = Alpha_Role.objects.all()
    paginator = Paginator(roles.values('id', 'name', 'is_admin', 'desc'), per_page=request_dict['paging']['itemsPerPage'], orphans=0)
    data = list(paginator.page(int(request_dict['paging']['page'])))
    return data, [{'itemCount': len(roles)}]

# 

# def __update_permission_by_role(request_dict):
#     try:
#         role_id = request_dict['query']['_id']
#         menu_list = request_dict['query']['menu_list']
#         table_list = request_dict['query']['table_list']
#         object_list = request_dict['query']['object_list']

#         role = Alpha_Role.objects.get(id=role_id)
#         role_name = role.name

#         for row in menu_list:
#             menu_uuid = row['menu_uuid']
#             permission = row['permission']
#             menu = Alpha_Menu.objects.get(menu_uuid=menu_uuid)
#             target = menu.menu_item_title + '(' + menu.menu_uuid + ')'
#             try:
#                 menu_permission = Alpha_Menu_Permission.objects.get(role=role, menu=menu)
#                 menu_permission.permission = permission
#                 menu_permission.save()
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'menu', target, json.dumps(permission))
#             except:
#                 Alpha_Menu_Permission.objects.create(role=role, menu=menu, permission=permission)
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'menu', target, json.dumps(permission))

#         for row in table_list:
#             table_uuid = row['table_uuid']
#             create = row['create']
#             read = row['read']
#             update = row['update']
#             delete = row['delete']
#             table = Alpha_Table.objects.get(table_uuid=table_uuid)
#             target = str(table.table_id) + '(' + str(table.table_uuid) + ')'
#             table_permission = copy.deepcopy(row)
#             del table_permission['table_uuid']
#             del table_permission['table_id']
#             try:
#                 table = bjects.get(role=role, table=table)
#                 table.create = create
#                 table.read = read
#                 table.update = update
#                 table.delete = delete
#                 table.save()
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'table', target, json.dumps(table_permission))
#             except:
#                 bjects.create(role=role, table=table, \
#                     create=create, read=read, update=update, delete=delete)
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'table', target, json.dumps(table_permission))

#         for row in object_list:
#             object_uuid = row['object_uuid']
#             permission = row['permission']
#             object = Alpha_API.objects.get(object_uuid=object_uuid)
#             # ic(object.menu_id)
#             menu = Alpha_Menu.objects.get(menu_uuid=object.menu_id)
#             target = str(menu.menu_item_title) + ':' + str(object.object_description) + ' (' + str(object.object_uuid) + ')'
#             try:
#                 object = Alpha_API_Permission.objects.get(role=role, object=object)
#                 object.permission = permission
#                 object.save()
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'object', target, json.dumps(permission))
#             except:
#                 Alpha_API_Permission.objects.create(role=role, object=object, permission=permission)
#                 __function.permissionLogging(request_dict['user']['username'], role_name, 'object', target, json.dumps(permission))

#         return {'success' : True}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}


# def __get_menu_permission(request_dict):
#     try:
#         try:
#             role_id = request_dict['query']['_id']
#             assert role_id != None
#         except:
#             user = Alpha_User.objects.get(user__username=request_dict['user']['username'])
#             role_id = user.role.id
#         try:
#             menu_uuid = request_dict['query']['menu_uuid']
#         except:
#             menu_uuid = ''

#         role = Alpha_Role.objects.get(id=role_id)

#         if menu_uuid == '':
#             auth_menu = list(Alpha_Menu_Permission.objects.filter(role=role).all().values('id', 'role', 'menu', 'permission').annotate(_id=F('id'), roleid=F('role__id'), rolename=F('role__name'), menuid=F('menu__menu_uuid'), menuname=F('menu__menu_item_title')))
#         else:
#             menu = Alpha_Menu.objects.get(menu_uuid=menu_uuid)
#             auth_menu = list(Alpha_Menu_Permission.objects.filter(role=role, menu=menu).values('id', 'role', 'menu', 'permission').annotate(_id=F('id'), roleid=F('role__id'), rolename=F('role__name'), menuid=F('menu__menu_uuid'), menuname=F('menu__menu_item_title')))
        
#         return {'success' : True, 'data': auth_menu}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}


# def __get_table_permission(request_dict):
#     try:
#         try:
#             role_id = request_dict['query']['_id']
#             assert role_id != None
#         except:
#             user = Alpha_User.objects.get(user__username=request_dict['user']['username'])
#             role_id = user.role.id
#         try:
#             table_uuid = request_dict['query']['tableUUID']
#         except:
#             table_uuid = ''

#         # ic(role_id)
#         # ic(table_uuid)
#         role = Alpha_Role.objects.get(id=role_id)

#         if table_uuid == '':
#             auth_table = list(bjects.filter(role=role).all().values('id', 'role', 'table', 'create', 'read', 'update', 'delete').(_id=F('id'), roleid=F('role__id'), rolename=F('role__name'), tableid=F('table__table_uuid'), tablename=F('table__table_id')))
#         else:
#             # ic('one')
#             table = Alpha_Table.objects.get(table_uuid=table_uuid)
#             ic(table)
#             auth_table = list(bjects.filter(role=role, table=table).values('id', 'role', 'table', 'create', 'read', 'update', 'delete').annotate(_id=F('id'), roleid=F('role__id'), rolename=F('role__name'), tableid=F('table__table_uuid'), tablename=F('table__table_id')))
#             ic(auth_table)
#         return {'success' : True, 'data': auth_table}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}

 

# def __get_object_permission(request_dict):
#     try:
#         if request_dict['query']['_id'] != '-':
#             role_id = request_dict['query']['_id']
#         else:
#             user = Alpha_User.objects.get(user__username=request_dict['user']['username'])
#             role_id = user.role.id

#         try:
#             object_uuid = request_dict['query']['object_uuid']
#         except:
#             object_uuid = ''

#         # ic(role_id)
#         # ic(object_uuid)
#         role = Alpha_Role.objects.get(id=role_id)


#         if object_uuid == '':
#             auth_table = list(Alpha_API_Permission.objects.filter(role=role).all().values('id', 'role', 'object', 'permission'))
#         else:
#             auth_table = list(Alpha_API_Permission.objects.filter(role=role, object_uuid=object_uuid).all().values('id', 'role', 'object', 'permission'))

#         return {'success' : True, 'data': auth_table}
#     except Exception as e:
#         return {'success': False, 'error': str(traceback.format_exc()), 'msg': str(e)}

