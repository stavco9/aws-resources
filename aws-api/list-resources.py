import boto3
import csv
import argparse
import json
import config
from logger import logger
from typing import Optional
from functools import reduce
import collections

# AWSAPI class is used to list resources and get resource details.
class AWSAPI:
    
    # Initialize the AWSAPI class: Create an AWS session with the given profile and region.
    def __init__(self, profile: Optional[str], region: str):
        if profile is None:
            self.session = boto3.Session(region_name=region)
        else:
            self.session = boto3.Session(profile_name=profile, region_name=region)

        self.region = region
        
        self.special_resource_group_name_mapping = config.special_resource_group_name_mapping
        self.services_not_split_by_slash = config.services_not_split_by_slash
        self.services_keep_service_arn = config.services_keep_service_arn
        self.service_to_resource_group_name_mapping = config.service_to_resource_group_name_mapping
        self.blacklist_resource_types = config.blacklist_resource_types
        self.whitelist_resource_types = config.whitelist_resource_types

    # List all resources using the Resource Explorer API. Filter by the given regions. Return a list of resource dictionaries.
    def list_resources_v2(self, query_regions: list[str]):
        list_resources = []

        filter_string = f'region:{",".join(query_regions)}'
        logger.info(filter_string)

        client = self.session.client('resource-explorer-2')

        response = client.list_resources(Filters={'FilterString': filter_string})
        next_token = response.get('NextToken')
        
        # Continue listing resources until there are no more resources to list.
        while next_token is not None and next_token != '':
            list_resources.extend(response.get('Resources'))
            response = client.list_resources(NextToken=next_token)
            next_token = response.get('NextToken')
        list_resources.extend(response.get('Resources'))
        
        return list_resources

    # Convert the resource group name to camel case if it is not in the special resource group name mapping.
    def to_camel_case(self, string: str):
        if self.special_resource_group_name_mapping.get(string.lower()) is not None:
            return self.special_resource_group_name_mapping.get(string.lower())

        # Convert the string from format "resource-group-name" to "ResourceGroupName".
        return ''.join(x for x in string.title() if not x.isspace()).replace('-', '')

    # Convert the service name in the ARN to camel case.
    def get_service_name(self, service_name_in_arn: str):
        return self.to_camel_case(service_name_in_arn)
    
    # Convert the resource group name in the ARN to camel case if it is not in the service to resource group name mapping.
    def get_resource_group_name(self, resource_service: str, resource_group_name_in_arn: str):
        if self.service_to_resource_group_name_mapping.get(resource_service) is not None:
            return self.service_to_resource_group_name_mapping.get(resource_service)
        
        return self.to_camel_case(resource_group_name_in_arn)
    
    # Get the resource id from the ARN.
    # For some services, the resource id is the same as the ARN.
    # For others, it is the last part of the ARN after the last colon or slash.
    def get_resource_id(self, resource_service: str, resource_arn: str):
        if resource_service in self.services_keep_service_arn:
            return resource_arn

        if resource_service in self.services_not_split_by_slash:
            return resource_arn.split(':')[-1]

        return resource_arn.split('/')[-1]

    # Build a response object from the Cloud Control API response.
    def build_response_object(self, response: dict, resource_arn: str, resource_type: str, resource_region: str, resource_account_id: str, resource_service: str, resource_group: str, resource_id: str):
        response_object = json.loads(response.get('ResourceDescription').get('Properties'))
        response_object['Identifier'] = response.get('ResourceDescription').get('Identifier')
        response_object['Arn'] = resource_arn
        response_object['ResourceType'] = resource_type
        response_object['Region'] = resource_region
        response_object['AccountId'] = resource_account_id
        response_object['Service'] = resource_service
        response_object['ResourceGroup'] = resource_group

        return response_object

    # List the details of the resources using the Cloud Control API.
    def list_resource_details(self, resource_list: list[dict]):
        resource_details = []
        client = self.session.client('cloudcontrol')

        # Iterate through the list of resources and get the details of each resource.
        for resource in resource_list:
            resource_arn = resource.get('Arn')
            resource_type = resource.get('ResourceType')
            resource_region = resource.get('Region')
            resource_account_id = str(resource.get('OwningAccountId'))

            # Check if the resource type is whitelisted or blacklisted.
            is_whitelisted = len(self.whitelist_resource_types) == 0 or "*" in self.whitelist_resource_types or resource_type in self.whitelist_resource_types
            is_blacklisted = resource_type in self.blacklist_resource_types
            if is_whitelisted and not is_blacklisted:

                # Get the service and resource group name from the resource type in the ARN.
                resource_service = resource_type.split(':')[0]
                resource_group = resource_type.split(':')[1].split('/')[0]

                # Get the partition, service, and resource group name from the resource ARN
                # and convert them to Cloud Control API type name format.
                resource_partition = resource_arn.split(':')[1].upper()
                resource_service = self.get_service_name(resource_service)
                resource_group = self.get_resource_group_name(resource_service, resource_group)
                resource_id = self.get_resource_id(resource_service, resource_arn)
                type_name = f"{resource_partition}::{resource_service}::{resource_group}"

                logger.debug(f"Original resource ARN: {resource_arn}")        
                logger.debug(f"Resource ID to query: {resource_id}")
                logger.debug(f"Type Name: {type_name}")

                try:
                    # Get the details of the resource using the Cloud Control API.
                    response = client.get_resource(TypeName=type_name, Identifier=resource_id)
                    # Build a response object from the Cloud Control API response.
                    resource_details.append(self.build_response_object(
                        response, resource_arn,resource_type,resource_region,
                        resource_account_id, resource_service, resource_group, resource_id))
                except client.exceptions.TypeNotFoundException:
                    logger.warning(f"Type {type_name} not found for resource. Skipping...")
                except client.exceptions.ResourceNotFoundException:
                    logger.warning(f"Resource {resource_id} not found for type {type_name}. Skipping...")
                except client.exceptions.ThrottlingException:
                    logger.error(f"Throttling exception for resource {resource_arn} !!!")
                except Exception as e:
                    logger.error(f"Error for resource {resource_arn}: {e} !!!")
            else:
                logger.debug(f"Resource of type {resource_type} is ignored. Skipping...")

        return resource_details
    
    def to_json(self, report: list[dict]):
        with open('report.json', 'w') as f:
            json.dump(report, f, indent=4)

    # Output the report by resource type to a CSV file.
    def to_csv_by_resource_type(self, report: list[dict], region: Optional[str] = None):
        if len(report) == 0:
            logger.warning(f"No resources found for region: {region if region is not None else 'all regions'}. No CSV file will be created.")
            return
        
        # Split the report by resource type.
        split_by_resource_type = collections.defaultdict(list)
        for resource in report:
            split_by_resource_type[resource.get('ResourceType')].append(resource)

        # Iterate through the split report and output the resources to a CSV file.
        for resource_type, resources in split_by_resource_type.items():
            output_filename = resource_type.replace(":", "_").replace("/", "_").replace("-", "_")
            if region is not None:
                output_filename = f'{output_filename}_{region.replace("-", "_")}'
            output_filename = f'report_{output_filename}.csv'
            
            self.to_csv(resources, output_filename)

    # Output the report by all services to a CSV file.
    def to_csv_all_services(self, report: list[dict], region: Optional[str] = None):
        if len(report) == 0:
            logger.warning(f"No resources found for region: {region if region is not None else 'all regions'}. No CSV file will be created.")
            return
        
        # Output the report to a CSV file.
        if region is None:
            self.to_csv(report, 'report.csv')
        else:
            self.to_csv(report, f'report_{region.replace("-", "_")}.csv')

    def to_csv(self, report: list[dict], filename: str):
        keys = reduce(lambda x, y: x.union(y), [set[str](row.keys()) for row in report])
        
        logger.info(f"Report will be output to file: {filename}")

        with open(filename, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(report)

# Main function to list resources and output the report.
def main(profile: str, region: str, query_regions: Optional[list[str]], log_level: str, output_by_region: bool, output_by_resource_type: bool, output_json: bool):

    # Set the log level.
    logger.set_level(log_level.upper())
    logger.info(f"Log level set to: {logger.get_level_name()}")

    resources = []
    
    # If no query regions are provided, use the region provided.
    if query_regions is None:
        query_regions = [region]

    # Create an AWSAPI object to list resources.
    aws_api = AWSAPI(profile, region)

    # List all resources using the Resource Explorer API.
    resources = aws_api.list_resources_v2(query_regions)

    logger.info(f"Found {len(resources)} resources in regions: {query_regions}")

    # Split the resources by region.
    split_by_region = collections.defaultdict(list)

    # Iterate through the resources and split them by region.
    for resource in resources:
        split_by_region[resource.get('Region')].append(resource)

    # Initialize a list to store the details of all resources in all regions.
    resource_details_all_regions = []

    # Iterate through the resources and split them by region.
    for resource_region, resources in split_by_region.items():
        resource_region_original = resource_region
        logger.info(f"Listing resources in region: {resource_region}")
        # If the region is global, use the us-east-1 region as the aggregator region.
        if resource_region == 'global':
            resource_region = 'us-east-1'

        # Create an AWSAPI object to list resources in the region.
        aws_regional_api = AWSAPI(profile, resource_region)
        
        # List the details of the resources using the Cloud Control API.
        resource_details_regional = aws_regional_api.list_resource_details(resources)
        logger.info(f"Found {len(resource_details_regional)} resources in region: {resource_region_original}")

        if output_by_region:
            if output_by_resource_type:
                logger.info(f"Outputting report by resource type for region: {resource_region_original}")
                aws_api.to_csv_by_resource_type(report=resource_details_regional, region=resource_region_original)
            else:
                logger.info(f"Outputting report by all services for region: {resource_region_original}")
                aws_api.to_csv_all_services(report=resource_details_regional, region=resource_region_original)
        
        resource_details_all_regions.extend(resource_details_regional)

    if not output_by_region:
        if output_by_resource_type:
            logger.info(f"Outputting report by resource type for all regions")
            aws_api.to_csv_by_resource_type(report=resource_details_all_regions)
        else:
            logger.info(f"Outputting report by all services for all regions")
            aws_api.to_csv_all_services(report=resource_details_all_regions)
    
    if output_json:
        logger.info(f"Outputting report in JSON format for all regions")
        aws_api.to_json(report=resource_details_all_regions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description ='Please provide aws profile name and region.')
    parser.add_argument('--profile', type = str, required=False, help ='The AWS Profile Name. If not provided, the default profile will be used.')
    parser.add_argument('--region', type = str, required=True, help ='The AWS Region where the resource explorer api is the aggregator. Please go to https://resource-explorer.console.aws.amazon.com/resource-explorer/home to check the aggregator region.')
    parser.add_argument('--query-regions', nargs="*", type = str, required=False, help ='Space separated list of AWS Regions to query. For example: --query-regions "eu-central-1 us-east-1". For Global services (e.g. IAM, Route53) please specify "global".')
    parser.add_argument('--log-level', type = str, required=False, help ='The log level. For example: --log-level "DEBUG".', default='INFO')
    parser.add_argument('--output-by-region', action='store_true', required=False, help ='Output the report by region.')
    parser.add_argument('--output-by-resource-type', action='store_true', required=False, help ='Output the report by resource type.')
    parser.add_argument('--output-json', action='store_true', required=False, help ='Output the report in JSON format.')
    args = parser.parse_args()

    main(args.profile, args.region, args.query_regions, args.log_level, args.output_by_region, args.output_by_resource_type, args.output_json)