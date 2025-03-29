import boto3
import re
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')
table = dynamodb.Table('VpcDetails')

def lambda_handler(event, context):
    try:
        vpc_name = event['vpcName']
        cidr = event['cidrBlock']
        idempotency_token = event.get('idempotencyToken', str(uuid.uuid4()))
        
        # CIDR validation
        if not re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\/([1-2][0-9]|3[0-2]))$', cidr):
            return {'error': 'Invalid CIDR format'}
        
        # Check idempotency first
        existing = table.query(
            IndexName='idempotencyToken-index',
            KeyConditionExpression='idempotencyToken = :token',
            ExpressionAttributeValues={':token': idempotency_token}
        )
        if existing.get('Items'):
            return existing['Items'][0]
        
        # Check unique VPC name
        name_check = table.query(
            IndexName='vpcName-index',
            KeyConditionExpression='vpcName = :name',
            FilterExpression='attribute_not_exists(deletedDate)',
            ExpressionAttributeValues={':name': vpc_name}
        )
        if name_check.get('Items'):
            return {'error': 'VPC name already exists'}

        # Check unique CIDR
        cidr_check = table.query(
            IndexName='cidrBlock-index',
            KeyConditionExpression='cidrBlock = :cidr',
            FilterExpression='attribute_not_exists(deletedDate)',
            ExpressionAttributeValues={':cidr': cidr}
        )
        if cidr_check.get('Items'):
            return {'error': 'CIDR already in use'}

        # Create VPC
        vpc = ec2.create_vpc(CidrBlock=cidr)
        ec2.create_tags(
            Resources=[vpc['Vpc']['VpcId']],
            Tags=[{'Key': 'Name', 'Value': vpc_name}]
        )

        # Store in DynamoDB
        item = {
            'vpcId': vpc['Vpc']['VpcId'],
            'vpcName': vpc_name,
            'cidrBlock': cidr,
            'status': 'ACTIVE',
            'createdDate': datetime.utcnow().isoformat() + 'Z',
            'idempotencyToken': idempotency_token
        }
        
        table.put_item(Item=item)
        return item
        
    except ClientError as e:
        return {'error': str(e)}
