import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('VpcConfigurations')

        # Check if specific VPC ID is requested
        if 'VpcId' in event:
            response = table.get_item(
                Key={'VpcId': event['VpcId']}
            )
            items = [response['Item']] if 'Item' in response else []
        else:
            # Scan the entire table (use query with index for better performance)
            response = table.scan()
            items = response['Items']
            
            # Handle pagination for large datasets
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

        # Filter by VPC Name if specified
        if 'VpcName' in event:
            items = [item for item in items if item['VpcName'] == event['VpcName']]

        return {
            'statusCode': 200,
            'body': items
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }