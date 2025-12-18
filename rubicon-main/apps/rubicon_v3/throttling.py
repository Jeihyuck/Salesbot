import json

from rest_framework.throttling import (
    UserRateThrottle,
    AnonRateThrottle,
    SimpleRateThrottle,
)


class ChatbotUserThrottle(UserRateThrottle):
    scope = "user_chatbot"


class ChatbotAnonThrottle(AnonRateThrottle):
    scope = "anon_chatbot"


class UserIdThrottle(SimpleRateThrottle):
    """
    Throttle based on user_id provided in request form data
    """

    scope = "user_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Parse form data similar to your parse_form_data function
            user_id = None
            if "userId" in form_data:
                try:
                    # Try to parse as JSON first
                    user_id = json.loads(form_data["userId"][0])
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, use as is
                    user_id = form_data["userId"][0]

            if not user_id:
                return None  # No throttling if no user_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(user_id)}
        except Exception:
            # In case of any error, don't throttle
            return None


class SessionIdThrottle(SimpleRateThrottle):
    """
    Throttle based on session_id provided in request form data
    """

    scope = "session_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Parse form data similar to your parse_form_data function
            session_id = None
            if "sessionId" in form_data:
                try:
                    # Try to parse as JSON first
                    session_id = json.loads(form_data["sessionId"][0])
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, use as is
                    session_id = form_data["sessionId"][0]

            if not session_id:
                return None  # No throttling if no session_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(session_id)}
        except Exception:
            # In case of any error, don't throttle
            return None


from apps.rubicon_v3.__function.definitions import channels

MULTI_INPUT_CHANNELS = [channels.SPRINKLR]


class NonMultiUserIdThrottle(SimpleRateThrottle):
    """
    Throttle based on user_id for non-multi channels
    """

    scope = "non_multi_user_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Check channel first
            channel = None
            if "channel" in form_data:
                try:
                    channel = form_data["channel"][0]
                except (IndexError, TypeError):
                    pass

            # If channel is in multi-user list, don't apply this throttle
            if channel in MULTI_INPUT_CHANNELS:
                return None

            # Get userId from form data
            user_id = None
            if "userId" in form_data:
                try:
                    # Try to parse as JSON first
                    user_id = json.loads(form_data["userId"][0])
                except (json.JSONDecodeError, TypeError, IndexError):
                    # If not JSON, use as is
                    try:
                        user_id = form_data["userId"][0]
                    except (IndexError, TypeError):
                        pass

            if not user_id:
                return None  # No throttling if no user_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(user_id)}
        except Exception:
            # In case of any error, don't throttle
            return None


class NonMultiSessionIdThrottle(SimpleRateThrottle):
    """
    Throttle based on session_id for non-multi channels
    """

    scope = "non_multi_session_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Check channel first
            channel = None
            if "channel" in form_data:
                try:
                    channel = form_data["channel"][0]
                except (IndexError, TypeError):
                    pass

            # If channel is in multi-user list, don't apply this throttle
            if channel in MULTI_INPUT_CHANNELS:
                return None

            # Get sessionId from form data
            session_id = None
            if "sessionId" in form_data:
                try:
                    # Try to parse as JSON first
                    session_id = json.loads(form_data["sessionId"][0])
                except (json.JSONDecodeError, TypeError, IndexError):
                    # If not JSON, use as is
                    try:
                        session_id = form_data["sessionId"][0]
                    except (IndexError, TypeError):
                        pass

            if not session_id:
                return None  # No throttling if no session_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(session_id)}
        except Exception:
            # In case of any error, don't throttle
            return None


class MultiUserIdThrottle(SimpleRateThrottle):
    """
    Throttle based on user_id for multi-user channels only
    """

    scope = "multi_user_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Check channel first
            channel = None
            if "channel" in form_data:
                try:
                    channel = form_data["channel"][0]
                except (IndexError, TypeError):
                    pass

            # If channel is NOT in multi-user list, don't apply this throttle
            if channel not in MULTI_INPUT_CHANNELS:
                return None

            # Get userId from form data
            user_id = None
            if "userId" in form_data:
                try:
                    # Try to parse as JSON first
                    user_id = json.loads(form_data["userId"][0])
                except (json.JSONDecodeError, TypeError, IndexError):
                    # If not JSON, use as is
                    try:
                        user_id = form_data["userId"][0]
                    except (IndexError, TypeError):
                        pass

            if not user_id:
                return None  # No throttling if no user_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(user_id)}
        except Exception:
            # In case of any error, don't throttle
            return None


class MultiSessionIdThrottle(SimpleRateThrottle):
    """
    Throttle based on session_id for multi-user channels only
    """

    scope = "multi_session_id_throttle"

    def get_cache_key(self, request, view):
        try:
            # Get form data
            form_data = dict(request.POST)

            # Check channel first
            channel = None
            if "channel" in form_data:
                try:
                    channel = form_data["channel"][0]
                except (IndexError, TypeError):
                    pass

            # If channel is NOT in multi-user list, don't apply this throttle
            if channel not in MULTI_INPUT_CHANNELS:
                return None

            # Get sessionId from form data
            session_id = None
            if "sessionId" in form_data:
                try:
                    # Try to parse as JSON first
                    session_id = json.loads(form_data["sessionId"][0])
                except (json.JSONDecodeError, TypeError, IndexError):
                    # If not JSON, use as is
                    try:
                        session_id = form_data["sessionId"][0]
                    except (IndexError, TypeError):
                        pass

            if not session_id:
                return None  # No throttling if no session_id provided

            return self.cache_format % {"scope": self.scope, "ident": str(session_id)}
        except Exception:
            # In case of any error, don't throttle
            return None
