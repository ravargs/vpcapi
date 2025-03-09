import boto3
import time
from datetime import datetime

ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Parse input parameters
        vpc_name = event['VpcName']
        vpc_cidr = event['VpcCidr']
        subnets = event['Subnets']

        # Create VPC
        vpc = ec2.create_vpc(CidrBlock=vpc_cidr)
        vpc_id = vpc['Vpc']['VpcId']
        
        # Wait for VPC to be available
        ec2.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
        
        # Add name tag to VPC
        ec2.create_tags(
            Resources=[vpc_id],
            Tags=[{'Key': 'Name', 'Value': vpc_name}]
        )

        # Create subnets with AZ specification
        subnet_configs = []
        for subnet in subnets:
            response = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=subnet['Cidr'],
                AvailabilityZone=subnet['AvailabilityZone']
            )
            subnet_id = response['Subnet']['SubnetId']
            
            # Add name tag to subnet
            ec2.create_tags(
                Resources=[subnet_id],
                Tags=[{'Key': 'Name', 'Value': subnet['Name']}]
            )
            
            subnet_configs.append({
                'SubnetName': subnet['Name'],
                'SubnetId': subnet_id,
                'CidrBlock': subnet['Cidr'],
                'AvailabilityZone': subnet['AvailabilityZone']
            })

        # Store configuration in DynamoDB
        table = dynamodb.Table('VpcConfigurations')
        item = {
            'VpcId': vpc_id,
            'VpcName': vpc_name,
            'CidrBlock': vpc_cidr,
            'Subnets': subnet_configs,
            'CreationTime': datetime.now().isoformat()
        }
        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': {
                'VpcId': vpc_id,
                'Subnets': subnet_configs
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }
