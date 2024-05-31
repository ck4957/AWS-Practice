import re

class HttpVerb:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    ALL = "*"

class EFFECT:
    ALLOW = "Allow"
    DENY = "Deny"

class AuthPolicy:
    def __init__(self, aws_account_id, principal, api_options):
        self.aws_account_id = aws_account_id
        self.principal_id = principal
        self.version = "2012-10-17"
        self.path_regex = re.compile('^[/.a-zA-Z0-9-\*]+$')
        self.allow_methods = []
        self.deny_methods = []

        if not api_options or 'restApiId' not in api_options:
            self.rest_api_id = "*"
        else:
            self.rest_api_id = api_options['restApiId']

        if not api_options or 'region' not in api_options:
            self.region = "*"
        else:
            self.region = api_options['region']

        if not api_options or 'stage' not in api_options:
            self.stage = "*"
        else:
            self.stage = api_options['stage']

    def _add_method(self, effect, verb, resource, conditions):
        if not self.path_regex.match(resource):
            raise ValueError("Invalid resource path: " + resource)

        resource_arn = f"arn:aws:execute-api:{self.region}:{self.aws_account_id}:{self.rest_api_id}/{self.stage}/{verb}/{resource}"

        if effect.lower() == "allow":
            self.allow_methods.append({
                'resourceArn': resource_arn,
                'conditions': conditions
            })
        elif effect.lower() == "deny":
            self.deny_methods.append({
                'resourceArn': resource_arn,
                'conditions': conditions
            })

    def allow_all_methods(self):
        self._add_method(EFFECT.ALLOW, "*", "*", None)

    def deny_all_methods(self):
        self._add_method(EFFECT.DENY, "*", "*", None)

    def allow_method(self, verb, resource):
        self._add_method(EFFECT.ALLOW, verb, resource, None)

    def deny_method(self, verb, resource):
        self._add_method(EFFECT.DENY, verb, resource, None)

    def allow_method_with_conditions(self, verb, resource, conditions):
        self._add_method(EFFECT.ALLOW, verb, resource, conditions)

    def deny_method_with_conditions(self, verb, resource, conditions):
        self._add_method(EFFECT.DENY, verb, resource, conditions)