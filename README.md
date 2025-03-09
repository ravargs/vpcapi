# Architecture
## Components
1. API Gateway: To create the REST API.
2. Lambda: To execute our Python code for VPC creation and data retrieval.
3. VPC: To create the network infrastructure.
4. DynamoDB: To store the VPC and subnet details.
5. Cognito User Pools: For authentication.
## Tesing
1. Create VPC
   Generate the authorization token, replace the $TOKEN with the generated token and then run the curl command
```
curl --location 'https://kwra8jqg54.execute-api.ap-south-1.amazonaws.com/dev/create_vpc' \
--header 'Authorization: Bearer $TOKEN' \
--header 'Content-Type: text/plain' \
--data '{
  "VpcName": "MyTestVPC",
  "VpcCidr": "10.0.0.0/16",
  "Region": "ap-south-1",
  "Subnets": [
    {
      "Name": "subnet-1",
      "Cidr": "10.0.1.0/24",
      "AvailabilityZone": "ap-south-1a"
    },
    {
      "Name": "subnet-2",
      "Cidr": "10.0.2.0/24",
      "AvailabilityZone": "ap-south-1b"
    },
    {
      "Name": "subnet-3",
      "Cidr": "10.0.3.0/24",
      "AvailabilityZone": "ap-south-1c"
    }
  ]
}'
```
2. Get VPC details
   Similar to above step generate the authorization token and rn the below command to invoke the api
   ```
   curl -X GET \
   https://kwra8jqg54.execute-api.ap-south-1.amazonaws.com/dev/get_vpc \
   -H "Authorization: Bearer $TOKEN" \
   -H "Content-Type: application/json"
   ```
3. Generating Token
```
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id xxxx \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=testuser,PASSWORD=xxxx,SECRET_HASH=iUf4k4NAex1upXjNWv1vkpet0C/0sF74FYc8tzoXlk8= \
  --query 'AuthenticationResult.IdToken' \
  --output text)
echo $TOKEN  
```

   
