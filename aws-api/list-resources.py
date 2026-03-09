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
    def __init__(self, profile: Optional[str], region: str, output_format: str):
        if profile is None:
            self.session = boto3.Session(region_name=region)
        else:
            self.session = boto3.Session(profile_name=profile, region_name=region)

        self.region = region
        self.output_format = output_format
        self.special_resource_group_name_mapping = config.special_resource_group_name_mapping
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
        
        logger.debug(f"Next token: {next_token}")

        # Continue listing resources until there are no more resources to list.
        while next_token is not None and next_token != '':
            list_resources.extend(response.get('Resources'))
            response = client.list_resources(Filters={'FilterString': filter_string}, NextToken=next_token)
            next_token = response.get('NextToken')
            logger.debug(f"Next token: {next_token}")

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

    # Build a response object from the Cloud Control API response.
    def build_response_object(self, response: list[dict], resource_type: str, resource_region: str, resource_account_id: str, resource_service: str, resource_group: str):
        response_objects = []

        if response.get('ResourceDescriptions') is None:
            logger.warning(f"No resources found for type {resource_type} in region {resource_region}. Skipping...")
            return response_objects

        for response_object in response.get('ResourceDescriptions'):
            response_object = json.loads(response_object.get('Properties'))
            response_object['Identifier'] = response_object.get('Identifier')
            response_object['ResourceType'] = resource_type
            response_object['Region'] = resource_region
            response_object['AccountId'] = resource_account_id
            response_object['Service'] = resource_service
            response_object['ResourceGroup'] = resource_group
            response_objects.append(response_object)

        return response_objects

    # List the details of the resources using the Cloud Control API.
    def list_resource_details(self, resource_list: list[dict]):
        resource_details = {}
        client = self.session.client('cloudcontrol')

        # Iterate through the list of resources and get the details of each resource.
        for resource in resource_list:
            resource_arn = resource.get('Arn')
            resource_type = resource.get('ResourceType')
            resource_region = resource.get('Region')
            resource_account_id = str(resource.get('OwningAccountId'))

            # Check if the resource type is whitelisted or blacklisted.
            is_whitelisted = len(self.whitelist_resource_types) == 0 or "*" in self.whitelist_resource_types or resource_type in self.whitelist_resource_types
            is_blacklisted = False
            for blacklist_type in self.blacklist_resource_types:
                if resource_type == blacklist_type or (
                    resource_type.split(':')[0] == blacklist_type.split(':')[0] and blacklist_type.split(':')[1] == '*'
                ):
                    is_blacklisted = True
                    break
            
            if not is_whitelisted or is_blacklisted:
                logger.debug(f"Resource type {resource_type} is ignored because it is either whitelisted or blacklisted. Skipping...")
                continue

            # Convert the resource type to a key for the resource details dictionary.
            resource_type_key = resource_type.replace(":", "_").replace("/", "_").replace("-", "_")
            if resource_details.get(resource_type_key) is None:
                logger.info(f"Adding new resource type {resource_type} to the resource details.")
                resource_details[resource_type_key] = []
            else:
                logger.debug(f"Resource type {resource_type} already scanned. Skipping...")
                continue

            # Get the service and resource group name from the resource type in the ARN.
            resource_service = resource_type.split(':')[0]
            resource_group = resource_type.split(':')[1].split('/')[0]

            # Get the partition, service, and resource group name from the resource ARN
            # and convert them to Cloud Control API type name format.
            resource_partition = resource_arn.split(':')[1].upper()
            resource_service = self.get_service_name(resource_service)
            resource_group = self.get_resource_group_name(resource_service, resource_group)
            type_name = f"{resource_partition}::{resource_service}::{resource_group}"

            logger.debug(f"Type Name: {type_name}")

            try:
                # Get the details of the resource using the Cloud Control API.
                response = client.list_resources(TypeName=type_name)
                next_token = response.get('NextToken')
        
                # Continue listing resources until there are no more resources to list.
                while next_token is not None and next_token != '':

                    # Build the response object and add it to the resource details dictionary.
                    resource_details[resource_type_key].extend(self.build_response_object(
                        response, resource_type, resource_region, resource_account_id, resource_service, resource_group
                    ))

                    # Get the next token and continue listing resources.
                    response = client.list_resources(TypeName=type_name, NextToken=next_token)
                    next_token = response.get('NextToken')
                
                # Build the response object and add it to the resource details dictionary.
                resource_details[resource_type_key].extend(self.build_response_object(
                    response, resource_type, resource_region, resource_account_id, resource_service, resource_group
                ))

            except client.exceptions.TypeNotFoundException:
                logger.warning(f"Tried to parse resource type for arn {resource_arn} but type {type_name} not found. Skipping...")
                del resource_details[resource_type_key]
            except Exception as e:
                logger.error(f"Error for resource type {resource_type}: {e} !!!")
                del resource_details[resource_type_key]

        return resource_details

    def unify_regions(self, report: dict):
        unified_report = {}
        for region_key, region_resources in report.items():
            for resource_type_key, resource_type_resources in region_resources.items():
                if unified_report.get(resource_type_key) is None:
                    unified_report[resource_type_key] = []
                unified_report[resource_type_key].extend(resource_type_resources)
        return unified_report

    def unify_resource_types(self, report: dict):
        single_list = []
        for resource_type_key, resource_type_resources in report.items():
            single_list.extend(resource_type_resources)
        return single_list

    # Output the report by resource type to a CSV file.
    def export_by_resource_type(self, report: dict, region: Optional[str] = None):
        if region is None:
            region = 'all_regions'

        if len(report.keys()) == 0:
            logger.warning(f"No resources found for region: {region}. No CSV file will be created.")
            return
        
        # Iterate through the split report and output the resources to a CSV file.
        for resource_type_key, resources in report.items():
            if self.output_format == 'csv':
                self.to_csv(resources, f'report_{resource_type_key}_{region}.csv')
            elif self.output_format == 'json':
                self.to_json(resources, f'report_{resource_type_key}_{region}.json')

    # Output the report by all services to a CSV file.
    def export_all_resource_types(self, report: dict, region: Optional[str] = None):
        if region is None:
            region = 'all_regions'
        
        if len(report.keys()) == 0:
            logger.warning(f"No resources found for region: {region}. No CSV file will be created.")
            return

        report_resources = self.unify_resource_types(report)
        if self.output_format == 'csv':
            self.to_csv(report_resources, f'report_{region}.csv')
        elif self.output_format == 'json':
            self.to_json(report_resources, f'report_{region}.json')

    def to_csv(self, report: list[dict], filename: str):
        if not report:
            logger.warning(f"No resources found. No CSV file will be created: {filename}")
            return
        keys = reduce(lambda x, y: x.union(y), [set[str](row.keys()) for row in report])
        
        logger.info(f"Report will be output to file: {filename}")

        with open(filename, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(report)

    def to_json(self, report: list[dict], filename: str):
        logger.info(f"Report will be output to file: {filename}")

        with open(filename, 'w') as f:
            json.dump(report, f, indent=4)

# Main function to list resources and output the report.
def main(profile: str, region: str, query_regions: Optional[list[str]], log_level: str, output_by_region: bool, output_by_resource_type: bool, output_format: str):

    # Set the log level.
    logger.set_level(log_level.upper())
    logger.info(f"Log level set to: {logger.get_level_name()}")

    resources = []
    
    # If no query regions are provided, use the region provided.
    if query_regions is None:
        query_regions = [region]

    # Create an AWSAPI object to list resources.
    aws_api = AWSAPI(profile, region, output_format)

    # List all resources using the Resource Explorer API.
    resources = aws_api.list_resources_v2(query_regions)

    logger.info(f"Found {len(resources)} resources in regions: {query_regions}")

    # Split the resources by region.
    split_by_region = collections.defaultdict(list)

    # Iterate through the resources and split them by region.
    for resource in resources:
        split_by_region[resource.get('Region')].append(resource)

    # Initialize a list to store the details of all resources in all regions.
    resource_details_all_regions = {}

    # Iterate through the resources and split them by region.
    for resource_region, resources in split_by_region.items():
        logger.info(f"Listing resources in region: {resource_region}")
        # If the region is global, use the us-east-1 region as the aggregator region.
        if resource_region == 'global':
            resource_region_for_query = 'us-east-1'
        else:
            resource_region_for_query = resource_region

        # Create an AWSAPI object to list resources in the region.
        aws_regional_api = AWSAPI(profile, resource_region_for_query, output_format)
        
        # List the details of the resources using the Cloud Control API.
        resource_details_regional = aws_regional_api.list_resource_details(resources)
        logger.info(f"Found {len(resource_details_regional)} resource types in region: {resource_region}")

        # Convert the region name to a key for the resource details dictionary.
        resource_region_key = resource_region.replace("-", "_")

        if output_by_region:
            if output_by_resource_type:
                logger.info(f"Outputting report by resource type for region: {resource_region}")
                aws_api.export_by_resource_type(report=resource_details_regional, region=resource_region_key)
            else:
                logger.info(f"Outputting report by all services for region: {resource_region}")
                aws_api.export_all_resource_types(report=resource_details_regional, region=resource_region_key)
        
        resource_details_all_regions[resource_region_key] = resource_details_regional

    if not output_by_region:
        resource_details_all_regions = aws_api.unify_regions(resource_details_all_regions)
        if output_by_resource_type:
            logger.info(f"Outputting report by resource type for all regions")
            aws_api.export_by_resource_type(report=resource_details_all_regions)
        else:
            logger.info(f"Outputting report by all services for all regions")
            aws_api.export_all_resource_types(report=resource_details_all_regions)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description ='Please provide aws profile name and region.')
    parser.add_argument('--profile', type = str, required=False, help ='The AWS Profile Name. If not provided, the default profile will be used.')
    parser.add_argument('--region', type = str, required=True, help ='The AWS Region where the resource explorer api is the aggregator. Please go to https://resource-explorer.console.aws.amazon.com/resource-explorer/home to check the aggregator region.')
    parser.add_argument('--query-regions', nargs="*", type = str, required=False, help ='Space separated list of AWS Regions to query. For example: --query-regions "eu-central-1 us-east-1". For Global services (e.g. IAM, Route53) please specify "global".')
    parser.add_argument('--log-level', type = str, required=False, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help ='The log level. For example: --log-level "DEBUG".', default='INFO')
    parser.add_argument('--output-by-region', action='store_true', required=False, help ='Output the report by region.')
    parser.add_argument('--output-by-resource-type', action='store_true', required=False, help ='Output the report by resource type.')
    parser.add_argument('--output-format', required=True, type=str, choices=['csv', 'json'], help ='Output the report in csv or json format.')
    args = parser.parse_args()

    main(args.profile, args.region, args.query_regions, args.log_level, args.output_by_region, args.output_by_resource_type, args.output_format)