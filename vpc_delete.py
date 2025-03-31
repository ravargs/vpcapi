import boto3
from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VpcDetails')

def get_vpc_id(event):
    if 'vpcId' in event:
        return event['vpcId']

    if 'vpcName' in event:
        response = ec2.describe_vpcs(Filters=[
            {'Name': 'tag:Name', 'Values': [event['vpcName']]}
        ])

        vpcs = response.get('Vpcs', [])
        if len(vpcs) == 1:
            return vpcs[0]['VpcId']
        elif len(vpcs) > 1:
            raise ValueError(f"Multiple VPCs found with name: {event['vpcName']}")
        else:
            raise ValueError(f"No VPC found with name: {event['vpcName']}")

    raise ValueError("Either 'vpcId' or 'vpcName' must be provided in the event")

def delete_subnets(vpc_id):
    # Describe subnets in the VPC
    response = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnets = response.get('Subnets', [])
    
    # Delete each subnet
    for subnet in subnets:
        ec2.delete_subnet(SubnetId=subnet['SubnetId'])

def delete_security_groups(vpc_id):
    # Describe security groups in the VPC
    response = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    security_groups = response.get('SecurityGroups', [])
    
    # Delete each security group (except the default one)
    for sg in security_groups:
        if sg['GroupName'] != 'default':
            ec2.delete_security_group(GroupId=sg['GroupId'])

def lambda_handler(event, context):
    try:
        # Get VPC ID from either vpcId or vpcName
        vpc_id = get_vpc_id(event)

        # Delete dependencies
        delete_subnets(vpc_id)
        delete_security_groups(vpc_id)

        # Delete VPC
        ec2.delete_vpc(VpcId=vpc_id)

        # Delete entry from DynamoDB if VPC deletion succeeds
        table.delete_item(
            Key={'vpcId': vpc_id}
        )

        return {
            'status': 'deleted',
            'vpcId': vpc_id,
            'message': 'VPC and DynamoDB entry successfully removed'
        }
    except ClientError as e:
        return {'error': str(e)}
    except ValueError as e:
        return {'error': str(e)}
