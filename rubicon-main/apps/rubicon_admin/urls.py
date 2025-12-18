from django.urls import path
from . import views
# from alpha.settings import VITE_OP_TYPE

urlpatterns = [
    path('assistant_product/', views.AssistantProduct.as_view()),
    path('assistant_ref_info/', views.AssistantRefInfo.as_view()),
    path('intelligence/', views.Intelligence.as_view()),
    path('web_cache/', views.WebCache.as_view()),
    path('code_mapping/', views.CodeMapping.as_view()),
    path('complementation_code_mapping/', views.ComplementationCodeMapping.as_view()),
    path('complement_db_search/', views.ComplementDbSearch.as_view()),
    path('complementation_code_mapping_l4/', views.ComplementationCodeMappingL4.as_view()),
    path('complementation_code_mapping_extended/', views.ComplementationCodeMappingExtended.as_view()),
    path('ner/', views.Ner.as_view()),
    path('unstructured_index/', views.UnstructuredIndex.as_view()),
    path('unstructured_test/', views.UnstructuredTest.as_view()),
    path('spec_table_meta/', views.SpecTableMeta.as_view()),
    path('predefined/', views.Predefined.as_view()),
    path('predefined_rag/', views.PredefinedRAG.as_view()),
    path('managed_response/', views.MAnagedResponse.as_view()),
    path('dashboard/', views.Dashboard.as_view()),
    path('prompt_template/', views.PromptTemplate.as_view()),
    path('appraisal_check/', views.AppraisalCheck.as_view()),
    path('chat/', views.Chat.as_view()),
    path('chat_test/', views.ChatTest.as_view()),
    path('test_query/', views.testQuery.as_view()),
    path('privacy/', views.Privacy.as_view()),
    path('managed_word/', views.ManagedWord.as_view()),
    path('product_search/', views.ProductSearch.as_view()),
    path('cpt_mapping_data/', views.CPTMappingData.as_view()),
    path('cpt_upd_del_data/', views.CPTUpdDelData.as_view()),

]
