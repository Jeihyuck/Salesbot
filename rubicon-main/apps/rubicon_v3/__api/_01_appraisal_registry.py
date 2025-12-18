import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from dataclasses import dataclass

from apps.rubicon_v3.__function.definitions import channels
from apps.rubicon_v3.__function.__encryption_utils import retry_function
from apps.rubicon_v3.__external_api.__dkms_encode import DKMS_Encoder
from alpha._db import chat_log_collection, search_log_collection

dkms_encoder = DKMS_Encoder()


class AppraisalRegistry:
    @dataclass
    class AppraisalRegistryParams:
        message_id: str
        channel: str
        country_code: str
        thumb_up: bool
        selected_list: list[str]
        comment: str

    def __init__(self, input_params: AppraisalRegistryParams):
        self.input_params = input_params

    def register(self):
        # Process the input parameters
        # For selected_list, make sure to convert all the integer strings to integers
        # The validation for string integers already happened
        selected_list = self.input_params.selected_list
        if isinstance(selected_list, list):
            selected_list = [int(item) for item in self.input_params.selected_list]

        # Encrypt the comment using DKMS
        encrypted_comment = None
        if self.input_params.comment:
            encrypted_comment = retry_function(
                dkms_encoder.getEncryptedValue, self.input_params.comment
            )

        # Create the appraisal dictionary
        appraisal = {
            "thumb_up": self.input_params.thumb_up,
            "selection": selected_list,
            "comment": encrypted_comment,
        }

        # Set up the update data
        update_data = {"appraisal": appraisal}

        update_results = None
        # Check which collection to update based on the channel
        if self.input_params.channel in [channels.DOTCOMSEARCH]:
            # For dotcom search, we update the search log collection
            update_results = search_log_collection.update_one(
                {"message_id": self.input_params.message_id},
                {"$set": update_data},
            )
        else:
            # Update the chat log collection with the appraisal data
            update_results = chat_log_collection.update_one(
                {"message_id": self.input_params.message_id},
                {"$set": update_data},
            )

        return {
            "success": True,
            "data": {
                "update_results": {
                    "matched_count": update_results.matched_count,
                    "modified_count": update_results.modified_count,
                }
            },
            "message": (
                "Appraisal registered successfully"
                if update_results.modified_count > 0
                else "No changes made to the appraisal"
            ),
        }
