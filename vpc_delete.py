def lambda_handler(event, context):
    vpc_id = event['vpcId']
    
    try:
        # Delete VPC first
        ec2.delete_vpc(VpcId=vpc_id)
        
        # Update DynamoDB only if VPC deletion is successful
        table.update_item(
            Key={'vpcId': vpc_id},
            UpdateExpression='SET #status = :status, deletedDate = :date',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'DELETED',
                ':date': str(datetime.now())
            }
        )
        
        return {'status': 'deleted'}
    except ClientError as e:
        return {'error': str(e)}
