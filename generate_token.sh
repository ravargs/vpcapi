# Replace the client-id, username,password and secret hash

TOKEN=$(aws cognito-idp initiate-auth \
   --client-id xxxx \
   --auth-flow USER_PASSWORD_AUTH \
   --auth-parameters USERNAME=xxxx,PASSWORD="xxxxx",SECRET_HASH=xxxxxx \
   --query 'AuthenticationResult.IdToken' \
   --output text)
echo $TOKEN
