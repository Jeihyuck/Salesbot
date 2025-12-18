from django.contrib import admin
from alpha.settings import API_URL_PREFIX
from django.db import models
from django.forms import TextInput, Textarea
# Register your models here.
admin.site.site_url = '/' + API_URL_PREFIX



from django.contrib import admin
from django import forms

from apps.__common.admin import ExportCsvMixin
from ..alpha_base.models import Alpha_Menu
# from ..alpha_service.models import Alpha_Service
# from ..alpha_product.models import Alpha_Product
# from ..alpha_analytic_space.models import Alpha_Analytic_Space

from django.utils.html import format_html
from django.urls import reverse

from django.contrib import admin
from django import forms

from ..__common.admin import ExportCsvMixin
# from apps.alpha_auth.models import Alpha_Department
from apps.alpha_auth.models import Alpha_Department, Alpha_Group, Alpha_Permission, Alpha_Menu_Permission, Alpha_Content_Type

from .models import Alpha_User
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Permission


# admin.site.register(Alpha_User, UserAdmin)
@admin.register(Alpha_User)
class Alpha_User_Admin(admin.ModelAdmin, ExportCsvMixin):
    # form = Alpha_Role_Admin_Form
    empty_value_display = '-empty-'

    list_filter = ('username', 'full_name', 'department', 'is_superuser', 'is_staff', 'is_active' )
    list_display = ('username', 'full_name', 'department', 'is_superuser', 'is_staff', 'is_active' )
    search_fields = ['username', 'full_name', 'department', 'is_superuser', 'is_staff', 'is_active' ]


@admin.register(Alpha_Department)
class Alpha_Department_Admin(admin.ModelAdmin, ExportCsvMixin):
    # form = Alpha_Department_Admin_Form
    empty_value_display = '-empty-'

    list_filter = ('id', 'order', 'department')
    list_display = ('id', 'order', 'department')
    search_fields = ['id', 'order', 'department']

@admin.register(Alpha_Group)
class Alpha_Group_Admin(admin.ModelAdmin, ExportCsvMixin):
    # form = Alpha_Department_Admin_Form
    empty_value_display = '-empty-'
    # filter_horizontal = ('permissions', 'user_set',)
    list_filter = ('id', 'name', 'description', 'created_at', 'updated_at')
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    search_fields = ['id', 'name', 'description', 'created_at', 'updated_at']

    # def get_fieldsets(self, request, obj=None):
    #     # Add a new fieldset for managing users
    #     fieldsets = super().get_fieldsets(request, obj)
    #     fieldsets += (('Users in Group', {'fields': ('user_set',)}),)
    #     return fieldsets

@admin.register(Alpha_Permission)
class Alpha_Permission_Admin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'content_type', 'description')
    list_filter = ('content_type',)
    search_fields = ('name', 'codename', 'description')
    ordering = ('content_type', 'codename')

@admin.register(Alpha_Menu_Permission)
class Alpha_Menu_Permission_Admin(admin.ModelAdmin):
    list_display = ('group', 'menu')
    list_filter = ('menu', 'group')
    ordering = ('group', 'menu')

@admin.register(Alpha_Content_Type)
class Alpha_Content_Type_Admin(admin.ModelAdmin):
    list_display = ('app_label', 'model', 'description', 'created_at', 'updated_at')
    search_fields = ('app_label', 'model', 'description')
    ordering = ('app_label', 'model')
    list_filter = ('app_label',)

    def delete_unused_contenttypes(self, request, queryset):
        """
        Deletes ContentTypes that are not associated with any models.
        """
        deleted_count = 0
        for content_type in queryset:
            if not content_type.model_class():
                content_type.delete()
                deleted_count += 1
        self.message_user(request, f"{deleted_count} unused content types deleted.")

    delete_unused_contenttypes.short_description = "Delete unused content types"

admin.site.unregister(Group)
# admin.site.unregister(Permission)


# from django.contrib import admin
# from django.contrib.auth.models import Alpha_User, Group
# # from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
# from django.utils.html import format_html


# # Custom GroupAdmin to display users in each group
# class GroupAdmin(admin.ModelAdmin):
#     list_display = ('name', 'user_count', 'view_users_link')

#     def user_count(self, obj):
#         return obj.user_set.count()

#     user_count.short_description = 'Number of Users'

#     def view_users_link(self, obj):
#         return format_html(
#             '<a href="/admin/alpha_auth/alpha_user/?groups__id__exact={}">View Users</a>',
#             obj.id
#         )

#     view_users_link.short_description = 'Users'

# # Unregister the original Group admin and register the custom one
# admin.site.unregister(Group)
# admin.site.register(Group, GroupAdmin)


# # Custom UserAdmin to manage groups
# class UserAdmin(DefaultUserAdmin):
#     list_display = ('username', 'email', 'is_staff', 'group_list')
#     list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

#     def group_list(self, obj):
#         return ", ".join([group.name for group in obj.groups.all()])

#     group_list.short_description = 'Groups'


# # Unregister the original User admin and register the custom one
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)
