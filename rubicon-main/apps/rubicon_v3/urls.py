from django.urls import path
from . import views

urlpatterns = [
    path("completion/", views.Completion.as_view(), name="completion"),
    path("appraisal/", views.Appraisal.as_view(), name="appraisal"),
    path("appraisal-registry/", views.AppraisalRegistry.as_view(), name="appraisal-registry"),
    path("appraisal-check/", views.AppraisalCheck.as_view(), name="appraisal-check"),
    path("log-check/", views.LogCheck.as_view(), name="log-check"),
    path("supplementaryinfo/", views.SupplementaryInfo.as_view(), name="supplementaryinfo"),
    path("statistics/", views.DashboardData.as_view(), name="statistics"),
    path("statistics/download/", views.DashboardExport.as_view(), name="statistics_download"),
    path("completion/chathistory/", views.ChatHistory.as_view(), name="chathistory"),
    path("ai-bot-chat-history/", views.AIBotChatHistory.as_view(), name="ai-bot-chathistory"),
    path("action/", views.Action.as_view(), name="action"),
    path("guardrail/", views.Guardrail.as_view(), name="guardrail"),
    path("health/", views.HealthCheck, name="Health Check"),
    path("base", views.Base.as_view(), name="base"),
    path("category", views.Category.as_view(), name="category"),
    path("response-check/", views.ResponseCheck.as_view(), name="response-check"),
    path("search-summary/", views.SearchSummary.as_view(), name="search-summary"),
]
