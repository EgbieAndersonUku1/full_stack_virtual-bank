
from __future__ import annotations

import json
from django.http import JsonResponse, HttpRequest
from typing import Callable, Any
from django.utils.translation import gettext_lazy as _


def handle_json_post_request(request: HttpRequest, func:  Callable[[Any], Any]) -> JsonResponse:
    """
    Handles a JSON POST request and passes the parsed body to a callable function.

    Args:
        request (HttpRequest): Django request object.
        func (callable): Function that processes parsed JSON data.

    Returns:
        JsonResponse
    """

    if not isinstance(request, HttpRequest):
        raise TypeError(f"Expected a type request but got type {type(request).__name__}")
    
    # Ensure func is actually callable
    if not callable(func):
        raise TypeError(
            f"Expected a callable but got {type(func).__name__}"
        )


    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            data = func(body)
            return JsonResponse({"data": data})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)



def create_json_msg(field_name: str, field_value: str, is_available: bool) -> dict:
    """
    Creates a standardised JSON response message for field availability checks.

    This helper formats a consistent API response indicating whether a given
    field value (e.g. username, email) is available or already exists.

    The function:
    - Normalises field name and value to lowercase
    - Inverts the `is_available` flag since the db returns True if it exists and False if it doesn't
    - Generates a human-readable message

    Args:
        field_name (str): Name of the field being validated (e.g. "username").
        field_value (str): Value being checked (e.g. "john123").
        is_available (bool): Whether the value already exists in the database.

    Returns:
        dict: Standardised JSON-serialisable response containing:
            - FIELD_NAME: the field value
            - IS_AVAILABLE: boolean indicating availability
            - MSG: human-readable status message
    """

    try:
        field_name = field_name.lower()
        field_value = field_value.lower()
    except AttributeError as e:
       return {
            "FIELD_NAME": '',
            "IS_AVAILABLE": '',
            "MSG": _("An error occurred and the request could not be processed"),
            "ERROR": f"{type(e).__name__}: {e}"
        }

    return {"FIELD_NAME": field_value,
               "IS_AVAILABLE": not is_available if field_name != '' else False,
               "MSG": _(f"The {field_name} is not avaialbe" if is_available else f"The {field_name} is available"),
               "ERROR": '',
               }