import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from apps.alpha_base.models import Alpha_Menu, Alpha_Table
from datetime import datetime

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models

PwC = 'PwC'
COMPANY = [
    (PwC, _('PwC')),
]

TRUE = True
FALSE = False
BOOLEAN = [
    (TRUE, _('True')),
    (FALSE, _('False'))
]

# class Alpha_Role(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     name                = models.CharField(verbose_name='Role Name', max_length=50, unique=True)
#     is_admin            = models.BooleanField(verbose_name='Is Admin', choices=BOOLEAN, default=False)
#     desc                = models.TextField(verbose_name='Description', null=True, blank=True)
#     class Meta:
#         verbose_name_plural = '2. Alpha Role'
#     def __str__(self):
#         str_value = self.name
#         return str_value

class Alpha_User(AbstractUser):
    department          = models.CharField(max_length=100, blank=True, null=True)
    full_name           = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'username'  # Default is 'username', but you can set a custom field like 'email'
    class Meta:
        verbose_name_plural = '1. Alpha User'
    def __str__(self):
        return self.username

class Alpha_Department(models.Model):
    id                  = models.AutoField(primary_key=True)
    order               = models.IntegerField(verbose_name='Order')
    department          = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = '2. Alpha Department'
    def __str__(self):
        return self.department

class Alpha_Group(Group):
    description = models.TextField(blank=True, null=True, help_text="Optional description for the group.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the group was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the group was last updated.")

    class Meta:
        verbose_name_plural = "3. Alpha Groups"


class Alpha_Permission(Permission):
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the permission.")

    class Meta:
        verbose_name_plural = "4. Alpha Permissions"


class Alpha_Menu_Permission(models.Model):
    id                  = models.AutoField(primary_key=True)
    group               = models.ForeignKey(Alpha_Group, verbose_name='Group', on_delete=models.PROTECT)
    menu                = models.ForeignKey(Alpha_Menu, verbose_name='Menu', on_delete=models.PROTECT)
    permission          = models.BooleanField(verbose_name='Permission', choices=BOOLEAN)
    class Meta:
        verbose_name_plural = '5. Alpha Menu Permission'
        unique_together=(("group", "menu"),)


class Alpha_Content_Type(ContentType):
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="A description of this content type."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "6. Alpha Content Types"



# class Alpha_API_Permission(models.Model):
#     id                  = models.AutoField(primary_key=True)
#     role                = models.ForeignKey(Alpha_Role, verbose_name='Role', on_delete=models.PROTECT)
#     api                 = models.ForeignKey(Alpha_API, verbose_name='API', on_delete=models.PROTECT)
#     permission          = models.BooleanField(verbose_name='Permission', choices=BOOLEAN)
#     class Meta:
#         verbose_name_plural = '4. Alpha API Permission'
#         unique_together=(("role", "api"),)
