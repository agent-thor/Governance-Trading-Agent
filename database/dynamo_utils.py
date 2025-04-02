import boto3
from typing import List, Optional, Dict, Any, Union
from dotenv import load_dotenv
import os
from datetime import datetime
from botocore.exceptions import ClientError

load_dotenv()

class DynamoDBClient:
    def __init__(self, region: str = 'us-east-1'):
        """Initialize DynamoDB client with AWS credentials"""
        required_env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        try:
            self.session = boto3.Session(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=region
            )
            self.client = self.session.client('dynamodb')
        except Exception as e:
            raise ConnectionError(f"Failed to initialize DynamoDB client: {str(e)}")

    def get_table_key_schema(self, table_name: str) -> Dict[str, str]:
        """Retrieve the key schema for a given table"""
        try:
            response = self.client.describe_table(TableName=table_name)
            key_schema = response['Table']['KeySchema'][0]  # Assuming single primary key
            attribute_definitions = response['Table']['AttributeDefinitions']
            key_type = next(attr for attr in attribute_definitions if attr['AttributeName'] == key_schema['AttributeName'])
            return {key_schema['AttributeName']: key_type['AttributeType']}
        except ClientError as e:
            raise Exception(f"Failed to describe table: {str(e)}")
    
    def get_item(self, table_name: str, primary_key: Dict[str, Dict[str, str]], 
             attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            params = {
                'TableName': table_name,
                'Key': primary_key
            }
            if attributes:
                params['AttributesToGet'] = attributes
    
            response = self.client.get_item(**params)
            return response.get('Item', {})
        except ClientError as e:
            raise Exception(f"Failed to get item: {str(e)}")


    def add_item(self, table_name: str, item: Dict[str, Dict[str, str]], 
                 condition: str = "attribute_not_exists(id)") -> Dict[str, Any]:
        try:
            return self.client.put_item(
                TableName=table_name,
                Item=item,
                ConditionExpression=condition
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError("Item already exists")
            raise Exception(f"Failed to add item: {str(e)}")

    def update_item(self, table_name: str, primary_key: Dict[str, Dict[str, str]], 
                    updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not primary_key:
            raise ValueError("Primary key is required for updating an item")

        try:
            return self.client.update_item(
                TableName=table_name,
                Key=primary_key,
                AttributeUpdates=updates
            )
        except ClientError as e:
            raise Exception(f"Failed to update item: {str(e)}")

    def describe_table(self, table_name: str) -> Dict[str, Any]:
        try:
            return self.client.describe_table(TableName=table_name)
        except ClientError as e:
            raise Exception(f"Failed to describe table: {str(e)}")

    def get_last_row(self, table_name: str) -> Union[Dict[str, Any], str]:
        try:
            response = self.client.scan(
                TableName=table_name,
                Limit=1,
                ScanIndexForward=False
            )
            items = response.get('Items', [])
            return items[0] if items else "empty"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return "empty"
            raise Exception(f"Failed to get last row: {str(e)}")

    def get_date(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_auto_increment_id(self, table_name: str) -> int:
        """Generates an auto-increment ID by scanning the table for the highest current ID"""
        try:
            response = self.client.scan(
                TableName=table_name,
                ProjectionExpression="id"
            )
            items = response.get('Items', [])

            if not items:
                return 1  # Start from 1 if the table is empty

            max_id = max(int(item['id']['N']) for item in items)
            return max_id + 1

        except ClientError as e:
            raise Exception(f"Failed to get auto-increment ID: {str(e)}")

    def scan_table(self, table_name: str) -> Dict[str, Any]:
        """Scan the entire table and return all items"""
        try:
            response = self.client.scan(TableName=table_name)
            return response
        except ClientError as e:
            raise Exception(f"Failed to scan table: {str(e)}")
            
    def get_userId_from_APIkey(self, table_name: str, api_key: str) -> Optional[int]:
       """
       Retrieve user ID based on API key from the specified table
       
       Args:
           table_name (str): Name of the DynamoDB table
           api_key (str): API key to search for
       
       Returns:
           Optional[int]: User ID if API key is found, None otherwise
       """
       try:
           # Scan the table to find the item with matching API key
           response = self.client.scan(
               TableName=table_name,
               FilterExpression='api_key = :key',
               ExpressionAttributeValues={
                   ':key': {'S': api_key}
               }
           )
           
           # Check if any items were found
           items = response.get('Items', [])
           
           if not items:
               return None
           
           # Extract and return the user_id 
           # Assuming user_id is stored as a Number (N) type in DynamoDB
           return int(items[0].get('user_id', {}).get('N'))
       
       except ClientError as e:
           raise Exception(f"Failed to retrieve user ID from API key: {str(e)}")
           
    def get_item_by_column(self, table_name: str, column_name: str, value: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Retrieve items from the table based on a specific column value
        
        Args:
            table_name (str): Name of the DynamoDB table
            column_name (str): Name of the column to search
            value (Dict[str, Dict[str, str]]): Value to search for in DynamoDB format
                e.g., {"user_id": {"N": "123"}}
            
        Returns:
            List[Dict[str, Any]]: List of items matching the search criteria
            Returns empty list if no items found or if column doesn't exist
        """
        try:
            # Check if the column exists in the value dict
            if column_name not in value:
                return []
                
            response = self.client.scan(
                TableName=table_name,
                FilterExpression=f'{column_name} = :val',
                ExpressionAttributeValues={
                    ':val': value[column_name]
                }
            )
            
            print(response)
            
            if len(response['Items']) == 0:
                return None
            
            else:
                return response
            
        except ClientError as e:
            raise Exception(f"Failed to get items by column: {str(e)}")
            
    def extract_field(self, data: dict, field: str) -> list:
        """
        Extracts values of a specified field from the given dictionary.
        
        :param data: Dictionary containing items.
        :param field: The field to extract values for.
        :return: List of values corresponding to the specified field.
        """
        items = data.get("Items", [])
        
        extracted_values = []
        for item in items:
            if field in item:
                value_dict = item[field]
                # Extract the actual value based on its type
                if "S" in value_dict:
                    extracted_values.append(value_dict["S"])
                elif "N" in value_dict:
                    extracted_values.append(int(value_dict["N"]))
                elif "BOOL" in value_dict:
                    extracted_values.append(value_dict["BOOL"])
        
        return extracted_values

    
        

    
    



