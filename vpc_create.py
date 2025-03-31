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
        subnets = event['subnets']  # Expecting a list of subnet details
        idempotency_token = event.get('idempotencyToken', str(uuid.uuid4()))

        # CIDR validation for VPC
        if not re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\/([1-2][0-9]|3[0-2]))$', cidr):
            return {'error': 'Invalid VPC CIDR format'}

        # Validate subnets
        if not isinstance(subnets, list) or len(subnets) != 3:
            return {'error': 'Three subnets must be provided in a list'}

        subnet_ids = []
        for subnet in subnets:
            subnet_name = subnet['subnetName']
            subnet_cidr = subnet['subnetCidrBlock']

            # CIDR validation for Subnet
            if not re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\/([1-2][0-9]|3[0-2]))$', subnet_cidr):
                return {'error': f'Invalid Subnet CIDR format for {subnet_name}'}

            # Check unique subnet name (if needed)
            # You can implement a similar check as done for VPC name if required

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

        # Create Subnets
        for subnet in subnets:
            subnet_name = subnet['subnetName']
            subnet_cidr = subnet['subnetCidrBlock']
            subnet_response = ec2.create_subnet(
                VpcId=vpc['Vpc']['VpcId'],
                CidrBlock=subnet_cidr
            )
            ec2.create_tags(
                Resources=[subnet_response['Subnet']['SubnetId']],
                Tags=[{'Key': 'Name', 'Value': subnet_name}]
            )
            subnet_ids.append(subnet_response['Subnet']['SubnetId'])

        # Store in DynamoDB
        item = {
            'vpcId': vpc['Vpc']['VpcId'],
            'vpcName': vpc_name,
            'cidrBlock': cidr,
            'subnetIds': subnet_ids,
            'subnets': subnets,
            'status': 'ACTIVE',
            'createdDate': datetime.utcnow().isoformat() + 'Z',
            'idempotencyToken': idempotency_token
        }

        table.put_item(Item=item)
        return item

    except ClientError as e:
        return {'error': str(e)}
