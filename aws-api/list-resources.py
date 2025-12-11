import boto3
import csv
import argparse
import json
import config
from logger import logger
from typing import Optional
from functools import reduce
import collections

class AWSAPI:
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

    def list_resources_v2(self, query_regions: list[str]):
        list_resources = []

        filter_string = f'region:{",".join(query_regions)}'
        logger.info(filter_string)

        client = self.session.client('resource-explorer-2')

        response = client.list_resources(Filters={'FilterString': filter_string})
        next_token = response.get('NextToken')
        while next_token is not None and next_token != '':
            list_resources.extend(response.get('Resources'))
            response = client.list_resources(NextToken=next_token)
            next_token = response.get('NextToken')
        list_resources.extend(response.get('Resources'))
        
        return list_resources

    # If the resource group name is not in the mapping, convert it to camel case by default.
    def to_camel_case(self, string: str):
        if self.special_resource_group_name_mapping.get(string.lower()) is not None:
            return self.special_resource_group_name_mapping.get(string.lower())

        return ''.join(x for x in string.title() if not x.isspace()).replace('-', '')

    def get_service_name(self, service_name_in_arn: str):
        return self.to_camel_case(service_name_in_arn)
    
    def get_resource_group_name(self, resource_service: str, resource_group_name_in_arn: str):
        if self.service_to_resource_group_name_mapping.get(resource_service) is not None:
            return self.service_to_resource_group_name_mapping.get(resource_service)
        
        return self.to_camel_case(resource_group_name_in_arn)
    
    def get_resource_id(self, resource_service: str, resource_arn: str):
        if resource_service in self.services_keep_service_arn:
            return resource_arn

        if resource_service in self.services_not_split_by_slash:
            return resource_arn.split(':')[-1]

        return resource_arn.split('/')[-1]

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

    def list_resource_details(self, resource_list: list[dict]):
        resource_details = []
        client = self.session.client('cloudcontrol')

        for resource in resource_list:
            resource_arn = resource.get('Arn')
            resource_type = resource.get('ResourceType')
            resource_region = resource.get('Region')
            resource_account_id = str(resource.get('OwningAccountId'))
            is_whitelisted = len(self.whitelist_resource_types) == 0 or "*" in self.whitelist_resource_types or resource_type in self.whitelist_resource_types
            is_blacklisted = resource_type in self.blacklist_resource_types
            if is_whitelisted and not is_blacklisted:
                resource_service = resource_type.split(':')[0]
                resource_group = resource_type.split(':')[1].split('/')[0]

                resource_partition = resource_arn.split(':')[1].upper()
                resource_service = self.get_service_name(resource_service)
                resource_group = self.get_resource_group_name(resource_service, resource_group)
                resource_id = self.get_resource_id(resource_service, resource_arn)
                type_name = f"{resource_partition}::{resource_service}::{resource_group}"

                logger.debug(f"Original resource ARN: {resource_arn}")        
                logger.debug(f"Resource ID to query: {resource_id}")
                logger.debug(f"Type Name: {type_name}")

                try:
                    response = client.get_resource(TypeName=type_name, Identifier=resource_id)
                    resource_details.append(self.build_response_object(
                        response, resource_arn,resource_type,resource_region,
                        resource_account_id, resource_service, resource_group, resource_id))
                except client.exceptions.TypeNotFoundException:
                    logger.warning(f"Type {type_name} not found for resource. Skipping...")
                except client.exceptions.ResourceNotFoundException:
                    logger.warning(f"Resource {resource_id} not found for type {type_name}. Skipping...")
                except client.exceptions.ThrottlingException:
                    logger.error(f"Throttling exception for resource {resource_arn} !!!!!!!!!!!!!!!!!")
            else:
                logger.debug(f"Resource of type {resource_type} is ignored. Skipping...")

        return resource_details
    
    def to_json(self, report: list[dict]):
        with open('report.json', 'w') as f:
            json.dump(report, f, indent=4)

    def to_csv_by_resource_type(self, report: list[dict]):
        split_by_resource_type = collections.defaultdict(list)
        for resource in report:
            split_by_resource_type[resource.get('ResourceType')].append(resource)

        for resource_type, resources in split_by_resource_type.items():
            output_filename = f'report_{resource_type.replace(":", "_").replace("/", "_").replace("-", "_")}.csv'
            
            self.to_csv(resources, output_filename)

    def to_csv_by_region(self, report: list[dict]):
        split_by_region = collections.defaultdict(list)
        for resource in report:
            split_by_region[resource.get('Region')].append(resource)

        for resource_type, resources in split_by_region.items():
            output_filename = f'report_{resource_type.lower().replace("-", "_")}.csv'
            
            self.to_csv(resources, output_filename)

    def to_csv_all_services(self, report: list[dict]):
        self.to_csv(report, 'report.csv')

    def to_csv(self, report: list[dict], filename: str):
        keys = reduce(lambda x, y: x.union(y), [set[str](row.keys()) for row in report])
        
        with open(filename, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(report)

def main(profile: str, region: str, query_regions: Optional[list[str]], log_level: str):

    logger.set_level(log_level.upper())
    logger.info(f"Log level set to: {logger.get_level_name()}")

    resources = []
    
    if query_regions is None:
        query_regions = [region]

    aws_api = AWSAPI(profile, region)
    resources = aws_api.list_resources_v2(query_regions)

    split_by_region = collections.defaultdict(list)
    for resource in resources:
        split_by_region[resource.get('Region')].append(resource)

    resource_details = []

    for resource_region, resources in split_by_region.items():
        logger.info(f"Listing resources in region: {resource_region}")
        if resource_region == 'global':
            resource_region = 'us-east-1'
        aws_regional_api = AWSAPI(profile, resource_region)
        resource_details.extend(aws_regional_api.list_resource_details(resources))
        
    aws_api.to_json(resource_details)
    #aws_api.to_csv_all_services(resource_details)
    aws_api.to_csv_by_resource_type(resource_details)
    aws_api.to_csv_by_region(resource_details)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description ='Please provide aws profile name and region.')
    parser.add_argument('--profile', type = str, required=False, help ='The AWS Profile Name. If not provided, the default profile will be used.')
    parser.add_argument('--region', type = str, required=True, help ='The AWS Region where the resource explorer api is the aggregator. Please go to https://resource-explorer.console.aws.amazon.com/resource-explorer/home to check the aggregator region.')
    parser.add_argument('--query-regions', nargs="*", type = str, required=False, help ='Space separated list of AWS Regions to query. For example: --query-regions "eu-central-1 us-east-1". For Global services (e.g. IAM, Route53) please specify "global".')
    parser.add_argument('--log-level', type = str, required=False, help ='The log level. For example: --log-level "DEBUG".', default='INFO')
    args = parser.parse_args()

    main(args.profile, args.region, args.query_regions, args.log_level)