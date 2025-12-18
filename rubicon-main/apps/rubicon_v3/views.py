import json
import traceback
import pytz
import copy
import pandas as pd

from datetime import datetime, timezone
from bson.objectid import ObjectId

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication

from .throttling import (
    NonMultiUserIdThrottle,
    NonMultiSessionIdThrottle,
    MultiUserIdThrottle,
    MultiSessionIdThrottle,
)

from adrf.views import APIView
from apps.__common import alpha
from apps.rubicon_v3.__api import (
    _01_appraisal,
    _01_appraisal_registry,
    _01_appraisal_check,
    _02_log_check,
    _07_supplementary_info,
    _10_dashboard,
    _12_dashboard_export,
    _13_chat_history,
    _15_guardrail,
    _16_action,
    _17_response_check,
)
from apps.rubicon_v3.__api.search_summary import (
    _00_search_summary,
    __search_log as search_log,
)
from apps.rubicon_v3.__external_api._14_azure_email_alert import (
    send_process_error_alert,
)

from django.http import HttpResponse, StreamingHttpResponse
from apps.rubicon_v3.__function import (
    _00_default_greeting,
    _00_rubicon,
    __django_cache as django_cache,
    __django_rq as django_rq,
    __rubicon_log as rubicon_log,
)
from apps.rubicon_v3.__function.__exceptions import HttpStatus
from apps.rubicon_v3.__external_api._01_cis_base import CIS_Base
from apps.rubicon_v3.__external_api._02_cis_category import CIS_Category

from alpha.settings import VITE_OP_TYPE

from apps.rubicon_v3.validation_utils import (
    validate_no_multiple_values,
    validate_no_extra_fields_completion,
    validate_no_extra_fields_search,
    validate_no_extra_fields_appraisal,
    validate_no_extra_fields_appraisal_registry,
    validate_no_extra_fields_action,
    validate_no_extra_fields_supplementary,
    combine_errors,
)
from apps.rubicon_v3.serializers import (
    CompletionSerializer,
    FileSerializer,
    SearchSerializer,
    AppraisalSerializer,
    AppraisalRegistrySerializer,
    ActionSerializer,
    SupplementarySerializer,
)
from apps.rubicon_v3.exceptions import (
    PayloadTooLargeException,
    InvalidFileTypeException,
    TooManyFilesException,
    TotalSizeTooLargeException,
    InvalidImageResolutionException,
)

django_cache_client = django_cache.DjangoCacheClient()


def parse_form_data(data_dict):
    # Try to json load the data
    for key, value in data_dict.items():
        try:
            data_dict[key] = json.loads(value[0])
        except json.JSONDecodeError:
            data_dict[key] = value[0]
    return data_dict


def get_current_time_in_timezone(timezone_str, date_format="%Y-%m-%d %H:%M:%S"):
    """
    Get the current time in the specified timezone, or UTC if not specified or invalid.

    Args:
        timezone_str (str): The timezone identifier (e.g., "America/New_York", "Asia/Seoul")
        date_format (str, optional): The format to use for the datetime string.
                                    Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        str: Formatted current datetime string in the specified timezone
    """
    if timezone_str:
        try:
            # Try to use the specified timezone
            tz = pytz.timezone(timezone_str)
            return datetime.now(tz).strftime(date_format)
        except pytz.exceptions.UnknownTimeZoneError:
            # Invalid timezone, fall back to UTC
            return datetime.now(timezone.utc).strftime(date_format)
    else:
        # No timezone specified, use UTC
        return datetime.now(timezone.utc).strftime(date_format)


class Base(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    VALID_KEYS = {
        "MODEL_CODE",
        "PLANT",
        "COMPANY",
        "DIVISION",
        "MODEL_DIVISION",
        "MODEL_NAME",
        "SHORT_DESC",
        "LONG_DESC",
        "BASIC_MODEL",
        "PRODUCT",
        "NAME_E",
        "PRODUCT_CLASS",
        "UNIT",
        "HS_NO",
        "NET_WEIGHT",
        "GROSS_WEIGHT",
        "VOLUMN",
        "U_SIZE",
        "STATUS",
        "DOM_EXP",
        "PRODUCT_COMMODITY",
        "SALES_TYPE",
        "STORAGE",
        "DISTRIBUTION_CHANNEL",
        "SALES_ORG",
        "ACCOUNT_UNIT",
        "REQUESTER",
        "REQUEST_DATE",
        "APPROVAL_EMPLOYEE",
        "APPROVAL_DATE",
        "UPDATE_PERSON",
        "UPDATE_DATE",
        "INCH",
        "EAN_CODE",
        "UPC_CODE",
        "CONFIRMED_DROP_DATE",
        "SVC_CONFIRMED_DROP_DATE",
        "GLOBAL_STATUS",
        "STATUS_MODIFIED_DATE",
        "STATUS_MODIFIED_BY",
        "GPM_CODE",
        "PRODUCT_IN_DIVISION",
        "BUFFER",
        "SRA",
        "SALES_DROP_DATE",
        "GLOBAL_P_STATUS",
        "RTS",
        "RSRA",
        "RTS_INIT_DATE",
        "SRA_INIT_DATE",
        "SRA_DEV_DATE",
        "RTS_COM_DATE",
        "SRA_COM_DATE",
        "RTS_UPDATE_DATE",
        "SRA_UPDATE_DATE",
        "BUYER_NAME",
        "PROD_DEV_PLANT",
        "FORCAST_MODEL_CODE",
        "MODEL_GROUP_CODE",
        "NECESSITY_EHMS_APP",
        "EHMS_CONFIRM_FLAG",
        "EHMS_CONFIRM_DATE",
        "EHMS_CONFIRM_USER",
        "EHMS_ISSUED_VENDOR",
        "GLOBAL_MATERIAL_TYPE",
        "NON_STD_BAR",
        "CM_IND",
        "PRODUCT_NAME_MARKETING",
        "BOM_CONFIRMED_DATE",
        "FMP_DATE",
        "U_WIDTH",
        "U_LENGTH",
        "U_HEIGHT",
        "PRODUCT_HIER",
        "HS_NUMBER_P",
        "BRAND_TYPE",
        "URGENCY_ORDER",
        "APP_INFO_FLAG",
        "EANYN",
        "UPCYN",
        "CREATE_PERSON",
        "CREATE_DATE",
    }

    REQUIRED_KEYS = {"MODEL_CODE", "PLANT"}

    async def post(self, request):

        try:
            request_body = request.body.decode("utf-8")
            body_dict = json.loads(request_body)
            data_list = body_dict.get("dataList", [])
            if not isinstance(data_list, list):
                return Response(
                    {
                        "status": "error",
                        "message": "dataList must be a list",
                    },
                    status=400,
                )
            for index, data in enumerate(data_list):
                if not isinstance(data, dict):
                    return Response(
                        {
                            "status": "error",
                            "message": f"{index}번째 항목이 객체가 아닙니다.",
                        },
                        status=400,
                    )
                # 1. 필수 파라미터 누락 체크
                """missing_params = self.REQUIRED_KEYS - data.keys()
                if missing_params:
                    return Response(
                        {
                            "status": "error",
                            "message": "Missing required parameters",
                            "missing_parameters": list(missing_params),
                            "error_index": index,
                        },
                        status=400,
                    )"""
                # 2. 유효하지 않은 키 체크
                invalid_keys = [
                    key for key in data.keys() if key not in self.VALID_KEYS
                ]
                if invalid_keys:
                    return Response(
                        {
                            "status": "error",
                            "message": "Invalid keys found",
                            "invalid_keys": invalid_keys,
                            "error_index": index,
                        },
                        status=400,
                    )
            cis_base = CIS_Base()
            done, msg = cis_base.upsert_product(data_list)
            if done:
                return Response(
                    {
                        "status": "success",
                        "message": str(msg),
                        "processed_count": len(data_list),
                    },
                    status=200,
                )
            else:
                return Response(
                    {
                        "status": "error",
                        "message": str(msg),
                    },
                    status=500,
                )
        except json.JSONDecodeError:
            return Response(
                {"status": "error", "message": "Invalid JSON format"}, status=400
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"An unexpected error occurred: {str(e)}",
                },
                status=500,
            )


class Category(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    VALID_KEYS = {
        "MODEL_CODE",
        "PLANT",
        "DIVISION",
        "PRODUCT_GROUP_CODE",
        "PRODUCT_ABBR_CODE",
        "PROJECT_CODE",
        "MODEL_GROUP_CODE",
        "DEV_PROJECT_CODE",
        "SEGMENT",
        "DEV_MODEL_CODE",
        "FORECAST_MODEL_CODE",
        "BASIC_MODEL",
        "MATERIAL_TYPE",
        "UPDATE_PERSON",
        "COMPANY",
        "MODEL_NAME",
        "PRODUCT_GROUP_DESC",
        "PRODUCT_ABBR_DESC",
        "PRODUCT_CODE",
        "PRODUCT_NAME",
        "PROJECT_NAME",
        "DEV_MODEL_ID",
    }

    REQUIRED_KEYS = {"MODEL_CODE", "PLANT"}

    async def post(self, request):

        try:
            request_body = request.body.decode("utf-8")
            body_dict = json.loads(request_body)
            data_list = body_dict.get("dataList", [])
            if not isinstance(data_list, list):
                return Response(
                    {
                        "status": "error",
                        "message": "dataList must be a list",
                    },
                    status=400,
                )
            for index, data in enumerate(data_list):
                if not isinstance(data, dict):
                    return Response(
                        {
                            "status": "error",
                            "message": f"{index}번째 항목이 객체가 아닙니다.",
                        },
                        status=400,
                    )
                # 1. 필수 파라미터 누락 체크
                """missing_params = self.REQUIRED_KEYS - data.keys()
                if missing_params:
                    return Response(
                        {
                            "status": "error",
                            "message": "Missing required parameters",
                            "missing_parameters": list(missing_params),
                            "error_index": index,
                        },
                        status=400,
                    )"""
                # 2. 유효하지 않은 키 체크
                invalid_keys = [
                    key for key in data.keys() if key not in self.VALID_KEYS
                ]
                if invalid_keys:
                    return Response(
                        {
                            "status": "error",
                            "message": "Invalid keys found",
                            "invalid_keys": invalid_keys,
                            "error_index": index,
                        },
                        status=400,
                    )
            # 모든 검증 통과했으면 성공
            cis_tree = CIS_Category()
            done, msg = cis_tree.upsert_product(data_list)
            if done:
                return Response(
                    {
                        "status": "success",
                        "message": str(msg),
                        "processed_count": len(data_list),
                    },
                    status=200,
                )
            else:
                return Response(
                    {
                        "status": "error",
                        "message": str(msg),
                    },
                    status=500,
                )
        except json.JSONDecodeError:
            return Response(
                {"status": "error", "message": "Invalid JSON format"}, status=400
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"An unexpected error occurred: {str(e)}",
                },
                status=500,
            )


@api_view(["GET"])
def HealthCheck(request):
    return Response({"success": True})


class Appraisal(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for appraisal
        """

        # Create the custom object id for this api call
        object_id = ObjectId()

        # Get form data
        form_data = dict(request.POST)

        # Check for multiple values in form data
        multiple_values = validate_no_multiple_values(form_data, "appraisal")

        # Parse form data
        form_data = parse_form_data(form_data)

        # TEMPORARY: REMOVE PAGING FIELD (THIS IS FROM ADMIN PAGE)
        form_data.pop("paging", None)

        # Check if the action is ut_appraisal
        if (
            form_data.get("action") != "ut_appraisal"
            and hasattr(request, "user")
            and str(request.user) != "AnonymousUser"
        ):
            return alpha.stdResponse(request, _01_appraisal, logging_level="simple")

        # Validate if there are additional fields in form data
        extra_fields = validate_no_extra_fields_appraisal(form_data)

        # Serializer errors dict
        form_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django serializer
        serializer = AppraisalSerializer(data=form_data)
        if not serializer.is_valid():
            form_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Get the validated data from serializer (validated data is truncated appropriately)
        form_data = serializer.normalized_data

        # Helper function to convert snake_case to camelCase
        def snake_to_camel(snake_str):
            """Convert snake_case string to camelCase."""
            components = snake_str.split("_")
            return components[0] + "".join(x.title() for x in components[1:])

        # Format the form data to be one dictionary. (No nested dictionary)
        combined_data = {}
        for key, value in form_data.items():
            camel_key = snake_to_camel(key)
            if isinstance(value, dict):
                for k, v in value.items():
                    combined_data[snake_to_camel(k)] = v
            else:
                combined_data[camel_key] = value

        # Create a copy of the combined data for logging
        logging_data = copy.deepcopy(combined_data)

        # Check if validation errors exist
        if multiple_values or extra_fields or form_data_errors:
            combined_error = combine_errors(
                form_data_errors, multiple_values, extra_fields, {}
            )

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }
            # Create appraisal log with error
            django_rq.run_job_high(
                rubicon_log.create_appraisal_log,
                (logging_data, object_id, combined_error),
                {},
            )
            # rubicon_log.create_appraisal_log(
            #     logging_data, object_id, combined_error
            # )

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "Appraisal",
                    "Object ID": str(object_id),
                    "Message ID": combined_data.get("messageId", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "content_data": content_data},
                )
                # send_process_error_alert(
                #     "Input Validation Triggered",
                #     "validation_error",
                #     error_traceback=combined_error,
                #     context_data=context_data,
                # )

            return Response(error, status=status_code)

        # Create appraisal log
        django_rq.run_job_high(
            rubicon_log.create_appraisal_log, (logging_data, object_id), {}
        )
        # rubicon_log.create_appraisal_log(logging_data, object_id)

        appraisal_registry = _01_appraisal_registry.AppraisalRegistry(
            input_params=_01_appraisal_registry.AppraisalRegistry.AppraisalRegistryParams(
                message_id=combined_data.get("messageId"),
                channel=combined_data.get("channel"),
                country_code=combined_data.get("countryCode"),
                thumb_up=combined_data.get("thumbUp"),
                selected_list=combined_data.get("selectedList"),
                comment=combined_data.get("comment"),
            )
        )
        try:
            response = appraisal_registry.register()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "Appraisal",
                    "Object ID": str(object_id),
                    "Message ID": combined_data.get("messageId", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Appraisal Registry Error", "process_error"),
                    {
                        "error_traceback": traceback_message,
                        "content_data": content_data,
                    },
                )

        return Response(response)


class AppraisalRegistry(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for appraisal registry
        """
        # Get Json Body Data
        data = request.data

        # Create the custom object id for this api call
        object_id = ObjectId()

        # Check if there are no extra fields in json data
        extra_fields = validate_no_extra_fields_appraisal_registry(data)

        # Serializer errors dict
        json_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django serializer
        serializer = AppraisalRegistrySerializer(data=data)
        if not serializer.is_valid():
            json_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Get the validated data from serializer (validated data is truncated appropriately)
        data = serializer.normalized_data
        logging_data = copy.deepcopy(data)

        # Check if validation errors exist
        if extra_fields or json_data_errors:
            combined_error = combine_errors(json_data_errors, {}, extra_fields, {})

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }
            # Create appraisal log with error details
            django_rq.run_job_high(
                rubicon_log.create_appraisal_log, (logging_data, object_id), {}
            )
            # rubicon_log.create_appraisal_log(logging_data, object_id)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "AppraisalRegistry",
                    "Object ID": str(object_id),
                    "Message ID": data.get("messageId", "Unknown"),
                    "Channel": data.get("channel", "Unknown"),
                    "Country Code": data.get("countryCode", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "content_data": content_data},
                )
                # send_process_error_alert(
                #     "Input Validation Triggered",
                #     "validation_error",
                #     error_traceback=combined_error,
                #     context_data=context_data,
                # )

            return Response(error, status=status_code)

        # Create appraisal log
        django_rq.run_job_high(
            rubicon_log.create_appraisal_log, (logging_data, object_id), {}
        )
        # rubicon_log.create_appraisal_log(logging_data, object_id)

        appraisal_registry = _01_appraisal_registry.AppraisalRegistry(
            input_params=_01_appraisal_registry.AppraisalRegistry.AppraisalRegistryParams(
                message_id=data.get("messageId"),
                channel=data.get("channel"),
                country_code=data.get("countryCode"),
                thumb_up=data.get("thumbUp"),
                selected_list=data.get("selectedList"),
                comment=data.get("comment"),
            )
        )
        try:
            response = appraisal_registry.register()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "AppraisalRegistry",
                    "Channel": data.get("channel", "Unknown"),
                    "Country Code": data.get("countryCode", "Unknown"),
                    "Object ID": str(object_id),
                    "Message ID": data.get("messageId", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Appraisal Registry Error", "process_error"),
                    {
                        "error_traceback": traceback_message,
                        "content_data": content_data,
                    },
                )

        return Response(response)


class ResponseCheck(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for response check
        """
        # Get Json Body Data
        data = request.data

        # Check parameters
        # TODO: Add parameter checks

        response_check = _17_response_check.ResponseCheck(
            input_params=_17_response_check.ResponseCheck.ResponseCheckParams(
                type=data.get("type"),
                message=data.get("message"),
                message_history=data.get("messageHistory", []),
                session_id=data.get("sessionId"),
                country_code=data.get("countryCode"),
                response_style=data.get("responseStyle"),
                retry=data.get("retry", False),
            )
        )
        try:
            response = response_check.response_check_mux()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}
            print(traceback.format_exc())

        return Response(response)


class LogCheck(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Handle GET request for full log check
        """
        # Get Query Params Data
        data = request.query_params

        # Check parameters
        # TODO: Add parameter checks

        LogCheck = _02_log_check.LogCheck(
            input_params=_02_log_check.LogCheck.LogCheckParams(
                lookup_id=data.get("messageId"),
            )
        )

        try:
            response = LogCheck.get_logs()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}

        return Response(response)


class AppraisalCheck(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for appraisal check
        """
        # Get Json Body Data
        data = request.data

        # Check parameters
        # TODO: Add parameter checks

        # Get current time based on the specified timezone
        current_time = get_current_time_in_timezone(data.get("timezone"))

        try:
            AppraisalCheck = _01_appraisal_check.AppraisalCheck(
                input_params=_01_appraisal_check.AppraisalCheck.AppraisalCheckParams(
                    service=data.get("service", "chat"),
                    start_date=data.get("startDate", current_time),
                    end_date=data.get("endDate", current_time),
                    timezone=data.get("timezone"),
                    channel=(
                        [data.get("channel")]
                        if isinstance(data.get("channel"), str)
                        else data.get("channel")
                    ),
                    thumb_up=(
                        [data.get("thumbUp")]
                        if isinstance(data.get("thumbUp"), str)
                        else data.get("thumbUp")
                    ),
                    status=(
                        [data.get("status")]
                        if isinstance(data.get("status"), str)
                        else data.get("status")
                    ),
                    page=int(data.get("page", 1)),
                    items_per_page=int(data.get("itemsPerPage", 10)),
                )
            )

            response = AppraisalCheck.get_appraisal_data()
        except Exception as e:
            response = {
                "success": False,
                "data": [],
                "meta": {
                    "headers": [
                        "Message ID",
                        "Created On",
                        "Channel",
                        "Subsidiary",
                        "Country",
                        "User",
                        "Query",
                        "Response",
                        "Intelligence",
                        "Product Line",
                        "Product Name",
                        "Thumbs Up/Down",
                        "Selected List",
                        "Comment",
                        "Status",
                    ]
                },
                "pagination": {"page": int(data.get("page", 1)), "total_items": 0},
                "message": f"Error: {str(e)}",
            }

        return Response(response)


class Guardrail(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Handle GET request for guardrail check
        """
        # Get Query Params Data
        data = request.query_params

        # Check parameters
        # TODO: Add parameter checks

        guardrail = _15_guardrail.Guardrail(
            input_params=_15_guardrail.Guardrail.GuardrailParams(
                message=data.get("message"),
                language_code=data.get("languageCode", "ko").lower(),
                country_code=data.get("countryCode", "KR").upper(),
            )
        )
        try:
            response = guardrail.get_guardrail_data()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}
            print(traceback.format_exc())

        return Response(response)


class SupplementaryInfo(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for supplementary information
        """
        # Get Json Body Data
        data = request.data

        # Check if there are no extra fields in json data
        extra_fields = validate_no_extra_fields_supplementary(data)

        # Serializer errors dict
        json_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django serializer
        serializer = SupplementarySerializer(data=data)
        if not serializer.is_valid():
            json_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Check if validation errors exist
        if extra_fields or json_data_errors:
            combined_error = combine_errors(json_data_errors, {}, extra_fields, {})

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "SupplementaryInfo",
                    "Message ID": data.get("messageId", "Unknown"),
                    "Supplement Info": data.get("supplementInfo", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "content_data": content_data},
                )

            return Response(error, status=status_code)

        Supplement = _07_supplementary_info.SupplementaryInfoV2(
            input_params=_07_supplementary_info.SupplementaryInfoV2.SupplementaryParams(
                message_id=data.get("messageId"),
                supplement_info=data.get("supplementInfo"),
            )
        )
        try:
            response = Supplement.supplementary_info_api_mux()
        except Exception as e:
            response = {"success": False, "data": [], "message": f"Error: {str(e)}"}
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                content_data = {
                    "API": "SupplementaryInfo",
                    "Message ID": data.get("messageId", "Unknown"),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Supplementary Info Error", "process_error"),
                    {
                        "error_traceback": traceback_message,
                        "content_data": content_data,
                    },
                )

        return Response(response)


class DashboardData(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for dashboard data
        """
        # Get Json Body Data
        data = request.data

        # Check parameters
        # TODO: Add parameter checks

        # Get current time based on the specified timezone
        current_time = get_current_time_in_timezone(data.get("timezone"))

        try:
            Dashboard = _10_dashboard.Dashboard(
                input_params=_10_dashboard.Dashboard.DashboardParams(
                    api_type=data.get("type"),
                    service=data.get("service", "chat"),
                    start_date=data.get("startDate", current_time),
                    end_date=data.get("endDate", current_time),
                    timezone=data.get("timezone"),
                    channel=(
                        [data.get("channel")]
                        if isinstance(data.get("channel"), str)
                        else data.get("channel")
                    ),
                    intelligence=(
                        [data.get("intelligence")]
                        if isinstance(data.get("intelligence"), str)
                        else data.get("intelligence")
                    ),
                    country_code=(
                        [data.get("country")]
                        if isinstance(data.get("country"), str)
                        else data.get("country")
                    ),
                    subsidiary=(
                        [data.get("subsidiary")]
                        if isinstance(data.get("subsidiary"), str)
                        else data.get("subsidiary")
                    ),
                    product_line=(
                        [data.get("productLine")]
                        if isinstance(data.get("productLine"), str)
                        else data.get("productLine")
                    ),
                    product_name=(
                        [data.get("productName")]
                        if isinstance(data.get("productName"), str)
                        else data.get("productName")
                    ),
                    thumb_type=data.get("thumbType"),
                    thumb_up=(
                        [data.get("thumbUp")]
                        if isinstance(data.get("thumbUp"), str)
                        else data.get("thumbUp")
                    ),
                    interval=data.get("interval"),
                    locale=data.get("locale"),
                )
            )

            response = Dashboard.dashboard_api_mux()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}

        return self._add_cors_headers(Response(response))

    @classmethod
    def _add_cors_headers(cls, response):
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response


class DashboardExport(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for dashboard data download
        """
        # Get Json Body Data
        data = request.data

        # Check parameters
        # TODO: Add parameter checks

        # Get current time based on the specified timezone
        current_time = get_current_time_in_timezone(data.get("timezone"))

        try:
            Export = _12_dashboard_export.DashboardExport(
                input_params=_12_dashboard_export.DashboardExport.DashboardExportParams(
                    api_type=data.get("type"),
                    service=data.get("service", "chat"),
                    start_date=data.get("startDate", current_time),
                    end_date=data.get("endDate", current_time),
                    timezone=data.get("timezone"),
                    channel=(
                        [data.get("channel")]
                        if isinstance(data.get("channel"), str)
                        else data.get("channel")
                    ),
                    intelligence=(
                        [data.get("intelligence")]
                        if isinstance(data.get("intelligence"), str)
                        else data.get("intelligence")
                    ),
                    country_code=(
                        [data.get("country")]
                        if isinstance(data.get("country"), str)
                        else data.get("country")
                    ),
                    subsidiary=(
                        [data.get("subsidiary")]
                        if isinstance(data.get("subsidiary"), str)
                        else data.get("subsidiary")
                    ),
                    product_line=(
                        [data.get("productLine")]
                        if isinstance(data.get("productLine"), str)
                        else data.get("productLine")
                    ),
                    product_name=(
                        [data.get("productName")]
                        if isinstance(data.get("productName"), str)
                        else data.get("productName")
                    ),
                    thumb_type=data.get("thumbType"),
                    thumb_up=(
                        [data.get("thumbUp")]
                        if isinstance(data.get("thumbUp"), str)
                        else data.get("thumbUp")
                    ),
                    locale=data.get("locale"),
                    status=(
                        [data.get("status")]
                        if isinstance(data.get("status"), str)
                        else data.get("status")
                    ),
                )
            )

            df = Export.dashboard_export_api_mux()
        except Exception as e:
            df = pd.DataFrame(
                [{"success": False, "data": {}, "message": f"Error: {str(e)}"}]
            )

        # Create a response with CSV content type
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")

        # Set the Content-Disposition header to force download
        filename = f"{data.get('type')}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_export.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Use pandas to write the DataFrame directly to the HTTP response
        # Use utf-8-sig encoding to include BOM
        df.to_csv(path_or_buf=response, index=False, encoding="utf-8-sig")

        return response


class ChatHistory(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Handle GET request for chat history
        """
        # Get Query Params Data
        data = request.query_params

        # Check parameters
        # TODO: Add parameter checks

        chat_history = _13_chat_history.ChatHistory(
            input_params=_13_chat_history.ChatHistory.ChatHistoryParams(
                user_id=data.get("userId"),
                channel=data.get("channel"),
                message_count=(
                    int(data.get("messageCount")) if data.get("messageCount") else None
                ),
                page=int(data.get("page", 1)),
                items_per_page=int(data.get("itemsPerPage", 10)),
                session_id=data.get("sessionId"),
            )
        )
        try:
            response = chat_history.get_chat_history()
        except Exception as e:
            response = {
                "success": False,
                "data": [],
                "pagination": {
                    "total_items": 0,
                    "total_pages": 0,
                    "page": int(data.get("page", 1)),
                    "items_per_page": int(data.get("itemsPerPage", 10)),
                },
                "message": f"Error: {str(e)}",
            }

        return Response(response)


class AIBotChatHistory(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for AI bot chat history
        """
        # Get Json Body Data
        data = request.data

        # Check parameters
        # TODO: Add parameter checks

        aibot_chat_history = _13_chat_history.AIBotChatHistory(
            input_params=_13_chat_history.AIBotChatHistory.AIBotChatHistoryParams(
                type=data.get("type"),
                user_id=data.get("userId"),
                session_id=data.get("sessionId"),
                message_count=(
                    int(data.get("messageCount")) if data.get("messageCount") else None
                ),
                meta_data=data.get("metaData", {}),
            )
        )
        try:
            response = aibot_chat_history.aibot_chat_history_mux()
        except Exception as e:
            response = {"success": False, "data": [], "message": f"Error: {str(e)}"}

        return Response(response)


class Action(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for action
        """
        # Get Json Body Data
        data = request.data

        # Create the custom object id for this api call
        object_id = ObjectId()

        # Check if there are no extra fields in json data
        extra_fields = validate_no_extra_fields_action(data)

        # Serializer errors dict
        json_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django Serializer
        serializer = ActionSerializer(data=data)
        if not serializer.is_valid():
            json_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Get the validated data from serializer (validated data is truncated appropriately)
        data = serializer.normalized_data
        logging_data = copy.deepcopy(data)

        # Check if validation errors exist
        if extra_fields or json_data_errors:
            combined_error = combine_errors(json_data_errors, {}, extra_fields, {})

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }
            # Create action log with error
            django_rq.run_job_high(
                rubicon_log.create_action_log,
                (logging_data, object_id, combined_error),
                {},
            )
            # rubicon_log.create_action_log(data, object_id, combined_error)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "API": "Rubicon Action",
                    "Object ID": str(object_id),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "context_data": context_data},
                )
                # send_process_error_alert(
                #     "Input Validation Triggered",
                #     "validation_error",
                #     error_traceback=combined_error,
                #     context_data=context_data,
                # )

            return Response(error, status=status_code)

        # Create action log
        django_rq.run_job_high(
            rubicon_log.create_action_log, (logging_data, object_id), {}
        )
        # rubicon_log.create_action_log(data, object_id)

        action = _16_action.Action(
            input_params=_16_action.Action.ActionParams(
                action_type=data.get("actionType"),
                action_info=data.get("actionInfo"),
            )
        )
        try:
            response = action.action_api_mux()
        except Exception as e:
            response = {"success": False, "data": {}, "message": f"Error: {str(e)}"}
            traceback_message = traceback.format_exc()
            print(traceback_message)

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                context_data = {
                    "API": "Rubicon Action",
                    "Object ID": str(object_id),
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Action API Error", "process_error"),
                    {
                        "error_traceback": traceback_message,
                        "context_data": context_data,
                    },
                )

        return Response(response)


class SearchSummary(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [NonMultiUserIdThrottle]

    async def post(self, request):
        """
        Handle POST request for search summary
        """
        # Create HTTP Status
        status = HttpStatus()

        # Create the custom object id for this api call
        object_id = ObjectId()

        # Get Json Body Data
        data = request.data

        # Validate if there are no extra fields in json data
        extra_fields = validate_no_extra_fields_search(data)

        # Serializer errors dict
        json_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django Serializer
        serializer = SearchSerializer(data=data)
        if not serializer.is_valid():
            json_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Get the validated data from serializer (validated data is truncated appropriately)
        data = serializer.normalized_data
        logging_data = copy.deepcopy(data)

        # Check if validation errors exist
        if extra_fields or json_data_errors:
            combined_error = combine_errors(json_data_errors, {}, extra_fields, {})

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }
            # Create search log with error
            django_rq.run_job_high(
                search_log.create_search_log,
                (logging_data, object_id, combined_error),
                {},
            )

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                params = data.get("params", {})
                channel = "Unknown"
                country_code = "Unknown"
                user_id = "Unknown"
                message_id = data.get("messageId", "Unknown")
                original_query = "Unknown"

                if isinstance(params, dict):
                    channel = params.get("channel", "Unknown")
                    country_code = params.get("countryCode", "Unknown").upper()
                    user_id = params.get("userId", "Unknown")
                    original_query = params.get("message", "Unknown")

                context_data = {
                    "API": "Search Summary",
                    "Channel": channel,
                    "Country Code": country_code,
                    "User ID": user_id,
                    "Message ID": message_id,
                    "Original Query": original_query,
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "context_data": context_data},
                )
                # send_process_error_alert(
                #     "Input Validation Triggered",
                #     "validation_error",
                #     error_traceback=combined_error,
                #     context_data=context_data,
                # )

            return Response(error, status=status_code)

        # Create search log
        django_rq.run_job_high(
            search_log.create_search_log, (logging_data, object_id), {}
        )

        message_id = data["messageId"]
        params = _00_search_summary.create_dataclass_from_dict(
            data["params"], _00_search_summary.RubiconSearchFlow.Params
        )
        search_data = _00_search_summary.create_dataclass_from_dict(
            data["searchData"], _00_search_summary.RubiconSearchFlow.SearchData
        )
        use_cache = data.get("backendCache", True)
        update_status = data.get("updateHttpStatus", False)
        stream = data.get("stream", False)

        # Create a RubiconSearchFlow instance
        search_flow = _00_search_summary.RubiconSearchFlow(
            message_id=message_id,
            object_id=object_id,
            params=params,
            search_data=search_data,
            use_cache=use_cache,
            stream=stream,
            status=status,
        )
        # Run the search flow
        search_flow.enqueue_search_flow()

        # If stream is True, we will return a streaming response
        if data["stream"]:
            # Create a StreamingHttpResponse for the search summary
            response = StreamingHttpResponse(
                search_flow.get_stream_search_summary(),
                status=(status.status if update_status else 200),
                content_type="text/event-stream",
            )

            # Add the streaming specific headers to the response
            response["Cache-Control"] = "no-cache"
            response["Connection"] = "keep-alive"
            response["X-Accel-Buffering"] = "no"

        # If stream is False, we will return a normal response
        else:
            response = Response(
                search_flow.get_non_stream_search_summary(),
                status=(status.status if update_status else 200),
                content_type="application/json",
            )

        # Add the CORS headers to the response
        response["X-Content-Type-Options"] = "nosniff"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response


class Completion(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [
        NonMultiUserIdThrottle,
        NonMultiSessionIdThrottle,
        MultiUserIdThrottle,
        MultiSessionIdThrottle,
    ]

    async def post(self, request):
        """Handle POST request for completions"""

        # Create HTTP Status
        status = HttpStatus()

        # Create the custom object id for this api call
        object_id = ObjectId()

        # Parse form data and files
        form_data = dict(request.POST)
        files_data = dict(request.FILES)

        # Check for multiple values in form data
        multiple_values = validate_no_multiple_values(form_data, "completion")

        # Parse data_dict
        form_data = parse_form_data(form_data)

        # Validate if there are additional fields in form_data
        extra_fields = validate_no_extra_fields_completion(form_data)

        # Serializer errors dict
        form_data_errors = {}
        files_data_errors = {}
        error_messages = []
        status_code = 200

        # Validate input data using Django Serializer
        serializer = CompletionSerializer(data=form_data)
        if not serializer.is_valid():
            form_data_errors = serializer.errors
            error_messages.append("Invalid input data")
            status_code = 400

        # Get the validated data from serializer (validated data is truncated appropriately)
        form_data = serializer.normalized_data
        logging_data = copy.deepcopy(form_data)

        # Validate files data using Django Serializer
        try:
            file_serializer = FileSerializer(data=files_data)
            if not file_serializer.is_valid(raise_exception=True):
                files_data_errors = file_serializer.errors
                error_messages.append("Invalid file data")
                status_code = 400

        except (
            PayloadTooLargeException,
            InvalidFileTypeException,
            TooManyFilesException,
            TotalSizeTooLargeException,
            InvalidImageResolutionException,
        ) as e:
            # The exception itself will be handled by DRF and return the proper status code
            # The status code is set in the exception class
            files_data_errors = {
                "files": [
                    (
                        f"{e.default_code}: {str(e)}"
                        if hasattr(e, "default_code")
                        else f"exception: {str(e)}"
                    )
                ]
            }
            files_serializer_message = (
                e.default_detail
                if hasattr(e, "default_detail")
                else "Invalid file data"
            )
            error_messages.append(files_serializer_message)
            status_code = e.status_code if hasattr(e, "status_code") else 400

        # Check if validation errors exist
        if multiple_values or extra_fields or form_data_errors or files_data_errors:
            combined_error = combine_errors(
                form_data_errors, multiple_values, extra_fields, files_data_errors
            )

            error = {
                "status": "error",
                "message": " | ".join(error_messages),
                "errors": combined_error,
            }
            # Create chat log with error
            django_rq.run_job_high(
                rubicon_log.create_message_log,
                (logging_data, object_id, combined_error),
                {},
            )
            # rubicon_log.create_message_log(
            #     logging_data,
            #     object_id,
            #     combined_error,
            # )

            # Send Alert Email
            if VITE_OP_TYPE in ["STG", "PRD"]:
                # Only extract the original query and message id if message is a list
                original_query = "Unknown"
                message_id = "Unknown"
                if isinstance(form_data.get("message"), list):
                    original_query = str(
                        next(
                            (
                                item.get("content")
                                for item in form_data.get("message", [])
                                if item.get("type") == "text"
                            ),
                            "Unknown",
                        )
                    )
                    message_id = str(
                        next(
                            (
                                item.get("messageId")
                                for item in form_data.get("message", [])
                                if item.get("type") == "text"
                            ),
                            "Unknown",
                        )
                    )
                meta_data = form_data.get("meta")
                country_code = "Unknown"
                if isinstance(meta_data, dict):
                    country_code = meta_data.get("countryCode", "Unknown")
                    if isinstance(country_code, str):
                        country_code = country_code.upper()

                context_data = {
                    "API": "Chat Completion",
                    "Channel": form_data.get("channel", "Unknown"),
                    "Country Code": country_code,
                    "Object ID": str(object_id),
                    "User ID": form_data.get("userId", "Unknown"),
                    "Session ID": form_data.get("sessionId", "Unknown"),
                    "Message ID": message_id,
                    "Original Query": original_query,
                }

                django_rq.run_job_high(
                    send_process_error_alert,
                    ("Input Validation Triggered", "validation_error"),
                    {"error_traceback": combined_error, "context_data": context_data},
                )
                # send_process_error_alert(
                #     "Input Validation Triggered",
                #     "validation_error",
                #     error_traceback=combined_error,
                #     context_data=context_data,
                # )

            return Response(error, status=status_code)

        # Create chat log
        django_rq.run_job_high(
            rubicon_log.create_message_log, (logging_data, object_id), {}
        )
        # rubicon_log.create_message_log(logging_data, object_id)

        # Parse message and meta data
        param_channel = form_data["channel"]
        param_model = form_data["model"]
        param_meta = form_data["meta"]
        param_session_id = form_data["sessionId"]
        param_message = form_data["message"]

        # Extract message content, message id, and country code
        param_message_id = next(
            item for item in param_message if item["type"] == "text"
        )["messageId"]
        param_country_code = str(param_meta["countryCode"]).upper()

        # Set defaults
        param_backend_cache = form_data.get("backendCache", True)
        param_simple = form_data.get("simple", False)
        param_update_http_status = form_data.get("updateHttpStatus", False)
        param_stream = form_data.get("stream", True)

        ##################### Debugging purposes #####################
        if VITE_OP_TYPE == "DEV" and param_channel in ["DEV Debug"]:
            # For debugging purposes only
            param_update_http_status = True

        if VITE_OP_TYPE == "DEV" and param_channel == "DEV Test":
            # For debugging purposes only
            param_stream = False

        ##############################################################

        # Run response generator based on model
        if param_model == "default_greeting":
            # Create InputArguments dataclass
            input_arguments = _00_default_greeting.create_dataclass_from_dict(
                {
                    "message_id": param_message_id,
                    "country_code": param_country_code,
                    **form_data,
                },
                _00_default_greeting.DefaultGreeting.InputArguments,
            )
            # Create a DefaultGreeting Instance
            flow = _00_default_greeting.DefaultGreeting(
                input_args=input_arguments,
                object_id=object_id,
                stream=param_stream,
                status=status,
            )

            # Run the greeting flow
            flow.enqueue_greeting_flow()

        # Else, use RubiconChatFlow
        else:
            # Create InputArguments and InputFiles dataclasses
            input_arguments = _00_rubicon.create_dataclass_from_dict(
                {
                    "message_id": param_message_id,
                    "country_code": param_country_code,
                    **form_data,
                },
                _00_rubicon.RubiconChatFlow.InputArguments,
            )
            input_files = _00_rubicon.create_dataclass_from_dict(
                files_data, _00_rubicon.RubiconChatFlow.InputFiles
            )

            # Create a RubiconChatFlow Instance
            flow = _00_rubicon.RubiconChatFlow(
                input_arguments=input_arguments,
                input_files=input_files,
                object_id=object_id,
                use_cache=param_backend_cache,
                stream=param_stream,
                simple=param_simple,
                status=status,
            )

            # Run the chat flow
            flow.enqueue_chat_flow()

        # If stream is True, we will return a streaming response
        if param_stream:
            # Create a StreamingHttpResponse for the chat completion
            response = StreamingHttpResponse(
                flow.get_stream_response(),
                status=(status.status if param_update_http_status else 200),
                content_type="text/event-stream",
            )

            # Add the streaming specific headers to the response
            response["X-Accel-Buffering"] = "no"

        # If stream is False, we will return a normal response
        else:
            response = Response(
                flow.get_non_stream_response(),
                status=(status.status if param_update_http_status else 200),
                content_type="application/json",
            )

        # If model is rubicon, add a custom header to indicate the language used
        if param_model in ["rubicon"]:
            response["X-Response-Language"] = (
                django_cache_client.get(
                    django_cache.CacheKey.language(param_session_id)
                )
                or "Unknown"
            )

        response = self._add_response_headers(response)

        return response

    @classmethod
    def _add_response_headers(cls, response):
        response["Cache-Control"] = "no-cache"
        response["Connection"] = "keep-alive"
        response["X-Content-Type-Options"] = "nosniff"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response
