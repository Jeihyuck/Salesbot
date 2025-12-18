from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_api_key.permissions import HasAPIKey
from django.http import HttpResponse
# from icecream import ic
from apps.__common import alpha
from apps.rubicon_admin.__api import _01_assistant_product, _01_assistant_ref_info, _01_predefined, _01_predefined_rag, _01_intelligence, _02_ner
from apps.rubicon_admin.__api import _04_code_mapping, _04_complement_code_mapping_extended, _04_complement_code_mapping_l4, _07_managed_response, _09_prompt_template, _10_dashboard, _10_chat, _10_test_query, _11_appraisal_check
from apps.rubicon_admin.__api import _10_chat_test, _06_unstructured_index, _06_unstructured_test, _06_spec_table_meta
from apps.rubicon_admin.__api import _04_complement_code_mapping, _12_managed_word, _13_web_cache, _05_product_search
from apps.rubicon_admin.__api import _04_complement_db_search, _90_privacy, _04_cpt_mapping_data, _04_cpt_upd_del_data
from alpha.settings import VITE_OP_TYPE


class AssistantProduct(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_assistant_product, logging_level="simple")

class AssistantRefInfo(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_assistant_ref_info, logging_level="simple")

class Predefined(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_predefined, logging_level="simple")

class PredefinedRAG(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_predefined_rag, logging_level="simple")

class Intelligence(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _01_intelligence, logging_level="simple")

class WebCache(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _13_web_cache, logging_level="simple")

class Ner(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _02_ner, logging_level="simple")

class CodeMapping(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_code_mapping, logging_level="simple")

class ComplementationCodeMapping(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_complement_code_mapping, logging_level="simple")
    
class ComplementDbSearch(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_complement_db_search, logging_level="simple")

class ComplementationCodeMappingL4(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_complement_code_mapping_l4, logging_level="simple")
    
class ComplementationCodeMappingExtended(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_complement_code_mapping_extended, logging_level="simple")
    
class PromptTemplate(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _09_prompt_template, logging_level="simple")

class Dashboard(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _10_dashboard, logging_level="simple")

class UnstructuredIndex(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _06_unstructured_index, logging_level="simple")

class UnstructuredTest(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _06_unstructured_test, logging_level="simple")
    
class SpecTableMeta(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _06_spec_table_meta, logging_level="simple")
    
class MAnagedResponse(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _07_managed_response, logging_level="simple")

class Chat(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _10_chat, logging_level="simple")

class ChatTest(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _10_chat_test, logging_level="simple")

class testQuery(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _10_test_query, logging_level="simple")
    
class AppraisalCheck(APIView):
    # permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _11_appraisal_check, logging_level="simple")
    
class ManagedWord(APIView):
    # permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    permission_classes = [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _12_managed_word, logging_level="simple")

class Privacy(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _90_privacy, logging_level="simple")

class CPTMappingData(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_cpt_mapping_data, logging_level="simple")

class CPTUpdDelData(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _04_cpt_upd_del_data, logging_level="simple")
    
class ProductSearch(APIView):
    permission_classes = [IsAuthenticated] if VITE_OP_TYPE == 'PROD' else [AllowAny]
    def post(self, request):
        return alpha.stdResponse(request, _05_product_search, logging_level="simple")