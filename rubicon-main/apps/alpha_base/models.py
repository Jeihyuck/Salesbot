import uuid
from django.db import models
from model_clone import CloneMixin
from django.utils.translation import gettext_lazy as _

TRUE = True
FALSE = False
BOOLEAN = [
    (TRUE, _('True')),
    (FALSE, _('False'))
]

class Alpha_Menu(CloneMixin, models.Model):
    id                  = models.UUIDField(primary_key=True, verbose_name='Menu UUID', default=uuid.uuid4)
    parent_menu         = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='sub_menus')
    level               = models.IntegerField(verbose_name='Menu Level')
    name                = models.CharField(verbose_name='Menu Name', max_length=50)
    icon                = models.CharField(verbose_name='Icon', max_length=30, null=True, blank=True)
    url         = models.CharField(verbose_name='URL', max_length=100, null=True, blank=True)
    page_title  = models.JSONField(verbose_name='Page Title', null=True, blank=True)
    group               = models.BooleanField(verbose_name='Group', default=False)
    order               = models.IntegerField(verbose_name='Order')
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

    def __str__(self):
        if self.parent_menu:
            return f"{self.parent_menu} > {self.name}"
        else:
            return self.name

    def get_full_name(self):
        names = [self.name]
        parent = self.parent_menu
        while parent:
            names.insert(0, parent.name)
            parent = parent.parent_menu
        return ' > '.join(names)

    class Meta:
        verbose_name_plural = "1. Menu"


class Alpha_Table(CloneMixin, models.Model):
    id                  = models.UUIDField(primary_key=True, verbose_name='ID', default=uuid.uuid4)
    name                = models.CharField(verbose_name='Table Name', max_length=100)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "2. Table"

START = 'start'
CENTER = 'center'
END = 'end'
FIELD_ALIGN = [
    (START, _('Start')),
    (CENTER, _('Center')),
    (END, _('End'))
]


class Alpha_Table_Field(CloneMixin, models.Model):
    id                  = models.AutoField(primary_key=True)
    table               = models.ForeignKey(Alpha_Table, verbose_name='Object', on_delete=models.CASCADE)
    field_seq           = models.IntegerField(default=100)
    key                 = models.CharField(verbose_name='Data Field Name', max_length=100, null=True, blank=True)
    hide                = models.BooleanField(verbose_name='Hide Field', default=False)
    title               = models.CharField(verbose_name='Label', max_length=100, null=True, blank=True)
    align               = models.CharField(verbose_name='Align', max_length=10, choices=FIELD_ALIGN, default='center', null=True, blank=True)
    width               = models.CharField(verbose_name='Width', max_length=10, default='10%', null=True, blank=True)
    sortable            = models.BooleanField(verbose_name='Sortable', default=False, null=True, blank=True)
    style_class         = models.CharField(verbose_name='Class', max_length=200, null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "3. Table Field"

