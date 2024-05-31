import os
from packages import jwt, requests
from auth_policy import AuthPolicy, HttpVerb

API_GATEWAY = {
    'ACCOUNT_INDEX': 4
}

ALLOWED_METHODS = ['GET', 'POST']  # Add your allowed methods here
ALLOWED_RESOURCES = ['api/pets']  # Add your allowed resources here
ALLOWED_SCOPES = ['scope1', 'scope2']  # Add your allowed scopes here

def handler(event, context):
    try:
        if 'type' not in event or event['type'] != "TOKEN" or 'authorizationToken' not in event:
            print("Missing event type or authorization token")
            return {'message': 'Unauthorized'}, 401

        access_token = event['authorizationToken']
        # Verify the JWT token
        issuer = os.getenv('ISSUER')
        audience = os.getenv('AUDIENCE')
        response = requests.get(f'{issuer}/.well-known/jwks.json')
        jwks = response.json()
        unverified_header = jwt.get_unverified_header(access_token)
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }

        if rsa_key:
            try:
                payload = jwt.decode(
                    access_token,
                    rsa_key,
                    algorithms=['RS256'],
                    audience=audience,
                    issuer=issuer
                )
            except jwt.ExpiredSignatureError:
                print('Token expired')
                return {'message': 'Unauthorized'}, 401
            except jwt.JWTClaimsError:
                print('Wrong claims, please check the audience and issuer')
                return {'message': 'Unauthorized'}, 401
            except Exception:
                print('Unable to parse authentication token.')
                return {'message': 'Unauthorized'}, 401
        else:
            print('RSA Key not found.')
            return {'message': 'Unauthorized'}, 401

        # Token is valid, proceed with the request
        claims = payload
        print("JWT Claims: ", claims)
        arn_parts = event['methodArn'].split(':')
        api_path = arn_parts[5].split('/')
        aws_account_id = arn_parts[API_GATEWAY['ACCOUNT_INDEX']]
        api_options = {
            'restApiId': api_path[0],
            'stage': api_path[1]
        }
        api_gateway_method = api_path[2]
        api_gateway_resource = '/'.join(api_path[3:])

        policy = AuthPolicy(event['claims']['sub'], aws_account_id, api_options)
        is_method_allowed = api_gateway_method in ALLOWED_METHODS
        is_resource_allowed = api_gateway_resource in ALLOWED_RESOURCES
        is_scope_allowed = all(scope in ALLOWED_SCOPES for scope in event['claims']['scp'])

        if is_method_allowed and is_resource_allowed and is_scope_allowed:
            policy.allow_method(HttpVerb[api_gateway_method], api_gateway_resource)
        else:
            print(f'isMethodAllowed:{is_method_allowed}, isResourceAllowed:{is_resource_allowed}, isScopeAllowed:{is_scope_allowed}')
            policy.deny_method(HttpVerb[api_gateway_method], api_gateway_resource)

        policy_response = policy.build()
        print("Policy Response: ", policy_response)
        return policy_response

    except Exception as error:
        print("Error: ", error)
        return {'message': 'Unauthorized'}, 401
    
def verify_token(access_token, rsa_key):
    try:
        # Verify the JWT
        payload = jwt.decode(
            access_token,
            rsa_key,
            algorithms='RS256',  # Specify the algorithm here
            audience=os.getenv('AUDIENCE'),
            issuer=os.getenv('ISSUER')
        )
    except jwt.ExpiredSignatureError:
        print('Token expired')
        return False
    except jwt.JWTClaimsError:
        print('Wrong claims, please check the audience and issuer')
        return False
    except Exception:
        print('Unable to parse authentication token.')
        return False

    # Token is valid
    return True