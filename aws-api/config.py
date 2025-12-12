# Special resource group name mapping.
# This mapping is used to convert the resource group name in the ARN to the Cloud Control API type name format.
# details in https://docs.aws.amazon.com/cloudcontrolapi/latest/userguide/supported-resources.html
special_resource_group_name_mapping = {
    'ec2': 'EC2',
    's3': 'S3',
    'vpc': 'VPC',
    'rds': 'RDS',
    'sqs': 'SQS',
    'ssm': 'SSM',
    'sns': 'SNS',
    'iam': 'IAM',
    'kms': 'KMS',
    'acl': 'ACL',
    'ecr': 'ECR',
    'mfa': 'MFA',
    'ce': 'CE',
    'natgateway': 'NatGateway',
    'elasticloadbalancing': 'ElasticLoadBalancingV2',
    'secretsmanager': 'SecretsManager',
    'loadbalancer': 'LoadBalancer',
    'targetgroup': 'TargetGroup',
    'subgrp': 'DBSubnetGroup',
    'elastic-ip': 'EIP',
    'acm': 'CertificateManager',
    'autoscaling': 'AutoScaling',
    'autoscalinggroup': 'AutoScalingGroup',
    'elasticache': 'ElastiCache',
    'memorydb': 'MemoryDB',
    'parametergroup': 'ParameterGroup',
    'datacatalog': 'DataCatalog',
    'apprunner': 'AppRunner',
    'autoscalingconfiguration': 'AutoScalingConfiguration',
    'dynamodb': 'DynamoDB',
    'db': 'DBInstance',
    'workgroup': 'WorkGroup',
    'og': 'OptionGroup',
    'pg': 'DBParameterGroup',
    'anomalymonitor': 'AnomalyMonitor',
    'hostedzone': 'HostedZone',
    'healthcheck': 'HealthCheck',
    'anomalysubscription': 'AnomalySubscription',
    'vpc-endpoint': 'VPCEndpoint',
    'dhcp-options': 'DHCPOptions'
}

service_to_resource_group_name_mapping = {
    'S3': 'Bucket',
    'SQS': 'Queue'
}

blacklist_resource_types = [
    'acm:certificate',
    'iam:policy',
    'ec2:security-group-rule',
    'elasticloadbalancing:listener/net',
    'elasticloadbalancing:listener/app'
]

whitelist_resource_types = ["*"]

#whitelist_resource_types = [
#    'ec2:instance',
#    'rds:db',
#    'dynamodb:table',
#    's3:bucket',
#    'sqs:queue'
#]