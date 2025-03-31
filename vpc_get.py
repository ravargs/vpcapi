import boto3
from botocore.exceptions import ClientError  # Add missing import

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VpcDetails')  # Ensure table is initialized

def lambda_handler(event, context):
    try:
        vpc_id = event.get('vpcId')
        vpc_name = event.get('vpcName')
        result = []

        if vpc_id:
            # Get by VPC ID
            response = table.get_item(Key={'vpcId': vpc_id})
            if 'Item' in response:
                result.append(response['Item'])
        elif vpc_name:
            # Query by VPC Name using GSI
            response = table.query(
                IndexName='vpcName-index',
                KeyConditionExpression='vpcName = :name',
                ExpressionAttributeValues={':name': vpc_name}
            )
            result = response.get('Items', [])
        else:
            # Scan entire table if no parameters provided
            response = table.scan()
            result = response.get('Items', [])

        return {
            'count': len(result),
            'vpcs': result
        }
    except ClientError as e:
        return {'error': f"AWS API error: {str(e)}"}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}
