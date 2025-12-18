# from prettyjson import PrettyJSONWidget
from django.contrib import admin
from django import forms
from .models import Alpha_Menu, Alpha_Table, Alpha_Table_Field
from ..__common.admin import ExportCsvMixin
from model_clone import CloneModelAdmin
from django.db.models import JSONField
from icecream import ic
# from django_monaco_editor.widgets import AdminMonacoEditorWidget
# from django.forms import TextInput, Textarea, Select
from django_json_widget.widgets import JSONEditorWidget
from django.db import models



class Alpha_Menu_Admin_Form(forms.ModelForm):
    class Meta:
        model = Alpha_Menu
        fields = ['id', 'parent_menu', 'level',  'name', 'icon', 'url', 'page_title', 'group', 'order']

        widgets = {
            # 'page_title': JSONEditorWidget(attrs={'style': 'height: 200px; width: 800px; margin: 20px, 0px;'})
            'page_title': JSONEditorWidget()
        }

@admin.register(Alpha_Menu)
class Alpha_Menu_Admin(CloneModelAdmin, ExportCsvMixin):
    form = Alpha_Menu_Admin_Form

    empty_value_display = '-empty-'
    list_filter = ('id', 'parent_menu', 'level', 'name', 'icon', 'url', 'page_title', 'group', 'order')
    list_display = ('id', 'parent_menu', 'level', 'name', 'icon', 'url', 'page_title', 'group', 'order')
    search_fields = ['id', 'parent_menu__name', 'level', 'name']
    actions = ['export_as_csv']

    list_per_page = 20
    ordering=('order',)


# codemirror_widget = CodeMirrorTextarea(
#     mode="javascript",
#     theme="cobalt",
#     config={
#         'fixedGutter': True
#         # 'height': 200
#     },
# )

class Alpha_Table_Field_Admin_Form(forms.ModelForm):
    field_seq = forms.CharField(widget=forms.TextInput(attrs={'size': 6}))
    key = forms.CharField(widget=forms.TextInput(attrs={'size': 20}))
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 20}))
    width = forms.CharField(widget=forms.TextInput(attrs={'size': 10}))
    # style_class = forms.CharField(widget=forms.TextInput(attrs={'size': 20}))
    # filter = forms.CharField(widget=(mce_attrs= {
    #     'mode': "textareas",
    #     'content_css' : 'code',
    #     'height': 100,
    #     'width': 600,
    #     'toolbar': '''''',
    #     'menubar': False,
    #     'statusbar': False
    # }), required=False)

    

class Table_Fields(admin.TabularInline):
    model = Alpha_Table_Field
    ordering=('field_seq',)
    form = Alpha_Table_Field_Admin_Form
    extra = 0
    def has_delete_permission(self, request, obj=None):
        #Disable delete
        return True

# class Alpha_Table_Admin_Form(forms.ModelForm):
#     class Meta:
#         model = Alpha_Table
#         fields = ['name', 'access_control_type']

@admin.register(Alpha_Table)
class Alpha_Table_Admin(CloneModelAdmin):
    include_duplicate_action = True
    
    # form = Alpha_Table_Admin_Form

    empty_value_display = '-empty-'
    list_filter = ('id', 'name')
    list_display = ('id', 'name')
    search_fields = ['id', 'name']

    list_per_page = 15
    ordering= ('name',)

    def get_inlines(self, request, obj: Alpha_Table):
        return [Table_Fields]
        # if obj:
        #     if obj.type == 'table':
        #         return [Table_Fields]
        #     else:
        #         return []
        # else:
        #     return []
    # def get_formsets_with_inlines(self, request, obj=None):
    #     for inline in self.get_inline_instances(request, obj):
    #         if obj and obj.type == 'table':
    #             yield inline.get_formset(request, obj), inline

# class Alpha_Table_Field_Admin_Form(forms.ModelForm):
    # filter = forms.CharField(widget=forms.Textarea(attrs={'cols': 40, 'rows': 10, 'class': 'vLargeTextField', 'style': 'width: 800px;'}))

    # class Meta:
    #     model = Alpha_Table_Field
    #     fields = ('__all__')
    
@admin.register(Alpha_Table_Field)
class Alpha_Table_Field_Admin(CloneModelAdmin, ExportCsvMixin):
    empty_value_display = '-empty-'
    list_filter = ('table', 'field_seq', 'title', 'key')
    list_display = ('table', 'field_seq', 'title', 'key')
    search_fields = ['table', 'field_seq', 'title', 'key']
    actions = ['export_as_csv']

    list_per_page = 20
    ordering=('table__name', 'field_seq', 'title')


# class Alpha_API_Form(forms.ModelForm):
#     class Meta:
#         model = Alpha_API
#         fields = ('url', 'action', 'description', 'request_example', 'response_example', 'no_authentication', 'no_access_control')
#         # widgets = {
#         #     'request_example': PrettyJSONWidget(attrs={'initial': 'parsed'}),
#         #     'response_example': PrettyJSONWidget(attrs={'initial': 'parsed'}),
#         # }

# class API_Parameters(admin.TabularInline):
#     model = Alpha_API_Parameters
#     ordering=('seq',)
#     # form = Alpha_Table_Field_Admin_Form
#     extra = 0
#     def has_delete_permission(self, request, obj=None):
#         #Disable delete
#         return True


# @admin.register(Alpha_API)
# class Alpha_API_Admin(admin.ModelAdmin):
#     form = Alpha_API_Form
#     empty_value_display = '-empty-'

#     search_fields =  ['url', 'action']
#     readonly_fields = ['created_on']

#     list_filter = ('url', 'action', 'no_authentication', 'no_access_control')
#     list_display = ('url', 'action', 'no_authentication', 'no_access_control', 'updated_on')
#     list_display_links = ['url', 'action']
#     list_per_page = 15
#     ordering = ('url', 'action')
#     inlines = [API_Parameters]


# @admin.register(Alpha_API_Parameters)
# class Alpha_API_Parameters_Admin(CloneModelAdmin, ExportCsvMixin):
#     # form = Alpha_Table_Field_Admin_Form

#     empty_value_display = '-empty-'
#     list_filter = ('alpha_api', 'seq', 'parameter', 'required', 'description')
#     list_display = ('alpha_api', 'seq', 'parameter', 'required', 'description')
#     search_fields = ['alpha_api', 'seq', 'parameter', 'required', 'description']
#     actions = ['export_as_csv']

#     list_per_page = 20
#     ordering=('alpha_api', 'seq')

