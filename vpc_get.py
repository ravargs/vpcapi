def lambda_handler(event, context):
    vpc_id = event.get('vpcId')
    vpc_name = event.get('vpcName')
    
    if vpc_id:
        response = table.get_item(Key={'vpcId': vpc_id})
    elif vpc_name:
        response = table.query(
            IndexName='vpcName-index',
            KeyConditionExpression='vpcName = :name',
            ExpressionAttributeValues={':name': vpc_name}
        )
    else:
        return {'error': 'Missing parameters'}
    
    return response.get('Items', [])
