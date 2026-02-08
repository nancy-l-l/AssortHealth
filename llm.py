import json
from openai import OpenAI

class LLM:
    def __init__(self, model:str='gpt-5.2'):
        self.client = OpenAI()
        self.model = model
    
    def extract_and_respond(self, system_prompt:str, user_msg: str) -> dict:
        schema_hint = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "assistant_message": {"type": "string"},
                "extracted": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "patient": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "full_name": {"type": ["string", "null"]},
                                "dob": {"type": ["string", "null"]},
                            },
                            "required": ["full_name", "dob"],
                        },
                        "insurance": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "payer_name": {"type": ["string", "null"]},
                                "insurance_id": {"type": ["string", "null"]},
                            },
                            "required": ["payer_name", "insurance_id"],
                        },
                        "medical": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "chief_complaint": {"type": ["string", "null"]},
                            },
                            "required": ["chief_complaint"],
                        },
                        "demographics": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "address": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "street": {"type": ["string", "null"]},
                                        "city": {"type": ["string", "null"]},
                                        "state": {"type": ["string", "null"]},
                                        "zip": {"type": ["string", "null"]},
                                    },
                                    "required": ["street", "city", "state", "zip"],
                                }
                            },
                            "required": ["address"],
                        },
                        "intent": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "skip_insurance_id": {"type": ["boolean", "null"]},
                            },
                            "required": ["skip_insurance_id"],
                        },
                    },
                    "required": ["patient", "insurance", "medical", "demographics", "intent"],
                },

            },
            "required": ["assistant_message", "extracted"],
        }


        resp = self.client.responses.create(
            model=self.model,
            input=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_msg},
            ],
            text={
                'format':{
                    'type':'json_schema',
                    'name':'intake_step',
                    'schema': schema_hint,
                    'strict': True,
                }
            },
        )
        
        raw = resp.output_text
        return json.loads(raw)
    