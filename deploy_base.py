#!/usr/bin/python

import sys
import os
import boto3
import time


def set_credentials(region=''):
    # Get environment variables and set as variables to create auth client
    # request
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
    region_name = os.environ.get('AWS_DEFAULT_REGION')

    if region_name is None:
        region_name = region

    # If any of the Access Credentials were not provided, set them on the
    # command line
    if aws_access_key_id is None or aws_secret_access_key is None or aws_session_token is None:
        print('\nAWS Credentials: ')
    if aws_access_key_id is None:
        aws_access_key_id = raw_input('AWS_ACCESS_KEY_ID: ')
    if aws_secret_access_key is None:
        aws_secret_access_key = raw_input('AWS_SECRET_ACCESS_KEY: ')
    if aws_session_token is None:
        aws_session_token = raw_input('AWS_SESSION_TOKEN: ')

    credentials = {'aws_access_key_id': aws_access_key_id, 'aws_secret_access_key': aws_secret_access_key,
                   'aws_session_token': aws_session_token, 'region_name': region_name}

    return credentials


def set_s3_client(credentials):
    # Create S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return s3


def set_cf_client(credentials):
    # Create CloudFormation client
    cf = boto3.client(
        'cloudformation',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return cf


def set_ec2_client(credentials):
    # Create EC2 client
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        aws_session_token=credentials['aws_session_token'],
        region_name=credentials['region_name']
    )
    return ec2


def set_s3_bucket_name(ddi, raw_account_name):
    # Convert raw_account_name to s3-formatted bucket name
    account_name = raw_account_name.replace(' ', '-').lower()
    s3_bucket_name = ddi + '-' + account_name + '-cf-templates'
    return s3_bucket_name


def set_ec2_key_name(raw_account_name, environment, region):
    # Convert raw_account_name to ec2 key name
    account_name = raw_account_name.replace(' ', '-').lower()
    environment = environment.lower()
    ec2_key_name = region + '-' + environment + '-' + account_name
    return ec2_key_name


def set_sns_topic_name(raw_sns_topic_name):
    sns_topic_name = raw_sns_topic_name.replace(' ', '-').lower()
    return sns_topic_name


def create_s3_bucket(s3, s3_bucket_name, region):
    buckets = s3.list_buckets()['Buckets']
    bucket_exists = False
    for element in buckets:
        if s3_bucket_name in element['Name']:
            bucket_exists = True
    if bucket_exists is False:
        s3.create_bucket(Bucket=s3_bucket_name, ACL='private',
                         CreateBucketConfiguration={'LocationConstraint': region})
        s3.put_bucket_versioning(Bucket=s3_bucket_name, VersioningConfiguration={'Status': 'Enabled'})
        s3.put_bucket_lifecycle(
            Bucket=s3_bucket_name,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'ID': 'DeletePreviousVersions',
                        'Prefix': '',
                        'Status': 'Enabled',
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': 365
                        }
                    }
                ]
            }
        )


def upload_s3_object(s3, s3_bucket_name, environment, cf_directory, cf_templates_list):
    for i, cf_file in enumerate(cf_templates_list):
        s3.upload_file(cf_directory + '/' + cf_file,
                       s3_bucket_name, environment.lower() + '/' + cf_file)


def get_bucket_url(s3_bucket_name, environment):
    bucket_url = 'https://s3.amazonaws.com/' + \
        s3_bucket_name + '/' + environment.lower()

    return bucket_url


def get_cf_template_url(bucket_url, cf_object):
    cf_template_url = bucket_url + '/' + cf_object

    return cf_template_url


def get_cf_stack_outputs(cf, stack_name):
    stack_description = cf.describe_stacks(StackName=stack_name)
    stack_outputs_list = stack_description['Stacks'][0]['Outputs']

    stack_outputs = {}
    position = 0
    for element in stack_outputs_list:
        key = stack_outputs_list[position]['OutputKey']
        value = stack_outputs_list[position]['OutputValue']
        stack_outputs.update({key: value})
        position += 1

    return stack_outputs


def get_stack_resources(cf, stack_name):
    stack_resource_list = cf.list_stack_resources(StackName=stack_name)
    stack_summaries = stack_resource_list['StackResourceSummaries']

    stack_resources = {}
    position = 0
    for element in stack_summaries:
        key = element['LogicalResourceId']
        value = element['PhysicalResourceId']
        stack_resources.update({key: value})
        position += 1

    return stack_resources


def get_stack_complete(cf, stack_name):
    # Loop until stack is done building, then return True
    stack_status = ''
    while stack_status != 'CREATE_COMPLETE':
        stack_description = cf.describe_stacks(StackName=stack_name)
        stack_status = stack_description['Stacks'][0]['StackStatus']
        if stack_status != 'CREATE_COMPLETE':
            time.sleep(20)
    return True


def get_stack_deployed(cf, stack_name):
    # Determine if stack is deployed, return value
    try:
        cf.describe_stacks(StackName=stack_name)
    except:
        stack_deployed = False
    else:
        stack_deployed = True

    return stack_deployed


def get_cf_directory_templates(cf_directory):
    cf_templates_list = []
    for f in os.listdir(cf_directory):
        if f.endswith('.template'):
            cf_templates_list.append(f)

    return cf_templates_list


def get_template_defaults(cf, **kwargs):
    # This function can take stack_name for an already deployed stack, or a
    # TemplateBody / TemplateURL
    stack_name = kwargs.pop('stack_name', None)
    template_url = kwargs.pop('template_url', None)
    template_body = kwargs.pop('template_body', None)

    if stack_name is not None:
        template = cf.get_template_summary(StackName=stack_name)
    elif template_url is not None:
        template = cf.get_template_summary(TemplateURL=template_url)
    elif template_body is not None:
        template = cf.get_template_summary(TemplateBodyL=template_body)
    else:
        template = None

    if template is not None:
        # Create dict of template parameter default values
        template_parameters = template['Parameters']

        template_defaults = {}
        position = 0
        for element in template_parameters:
            key = element['ParameterKey']
            try:
                value = element['DefaultValue']
            except:
                value = None
            template_defaults.update({key: value})
            position += 1
        return template_defaults
    else:
        # No template specified
        return None


def create_parameters_dict(cf, cf_templates_list, bucket_url):
    cf_template_url_list = []
    for element in cf_templates_list:
        template_url = get_cf_template_url(bucket_url, element)
        cf_template_url_list.append(template_url)

    cf_parameters_list = []
    for element in cf_template_url_list:
        template_defaults = get_template_defaults(cf, template_url=element)
        cf_parameters_list.append(template_defaults)

    position = 0
    cf_default_parameters_dict = {}
    for template in cf_templates_list:
        # Remove .template extension
        cf_template_name = template.split('.template')[0]
        cf_default_parameters_dict[cf_template_name] = cf_parameters_list[position]
        position += 1

    return cf_default_parameters_dict


def print_stack_resources(stack_name, stack_resources_dict):
    print('\n' + stack_name + ' Resources: ')
    for key in stack_resources_dict:
        print(' ' + key + ': ' + stack_resources_dict[key])


def create_parameters_json(cf_default_parameters_dict):
    parameters_json = []
    new_dict = {}
    for value in cf_default_parameters_dict:
        new_dict['ParameterKey'] = value
        new_dict['ParameterValue'] = cf_default_parameters_dict[value]
        parameters_json.append(new_dict.copy())

    return parameters_json


def create_parameters_files(cf_default_parameters_dict):
    for stack in cf_default_parameters_dict:
        template = stack + '.template'
        parameters_file_json = create_parameters_json(cf_default_parameters_dict[stack])
        parameters_file_name = template + '.parameters'
        write_file(parameters_file_name, parameters_file_json)

        print('\nCreated ' + parameters_file_name)


def deploy_cf_stack(cf, bucket_url, cf_stack_parameters_dict, parameters_json):
    cf_template_url = get_cf_template_url(bucket_url, cf_stack_parameters_dict['cf_template'])

    stack_name = cf_stack_parameters_dict['stack_prefix'] + '-' + cf_stack_parameters_dict['cf_stack_name']

    if get_stack_deployed(cf, stack_name) is False:
        cf.create_stack(
            StackName=stack_name,
            TemplateURL=cf_template_url,
            Parameters=parameters_json,
            TimeoutInMinutes=30,
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            OnFailure='ROLLBACK'
        )

    return stack_name


def create_ec2_key_pair(ec2, ec2_key_name):
    try:
        key_pair = ec2.create_key_pair(
            KeyName=ec2_key_name
        )
        ec2_key = key_pair['KeyMaterial']
    except:
        ec2_key = None
    return ec2_key


def write_file(file_name, file_content):
    output_file_name = file_name
    # Opens output file, if file exists it will be overwritten
    output_file = open(output_file_name, 'w+')
    file_content = str(file_content)
    output_file.write(file_content + '\n')
    output_file.close()


def main(argv):
    print('NOTE: Please run "faws env" and set your environment variables before running this script.')

    # Collect Parameters
    print('Please enter parameters. Leave blank to use (default) values.')

    # Script Parameters
    print('\nScript Parameters: ')
    cf_directory = raw_input(' CloudFormation Template Directory Path: (my home)')
    if cf_directory == '':
        cf_directory = '/Users/matt6757/scripts/cftemplates'

    cf_templates_list = get_cf_directory_templates(cf_directory)
    cf_templates_list_string = raw_input(
        'The following templates were found:\n'
        ' ' + str(cf_templates_list) +
        '\nPlease hit <enter> if this list is correct, '
        'otherwise enter a comma-delimited list of file names: ')
    if cf_templates_list_string is not '':
        cf_templates_list = cf_templates_list_string.replace(' ', '').split(',')

    # Account Parameters
    print('\nAccount Parameters: ')
    ddi = raw_input(' Rackspace Account Number: ')
    raw_account_name = raw_input(' Rackspace Account Name: ')
    s3_bucket_name = set_s3_bucket_name(ddi, raw_account_name)

    # VPC Parameters
    print('\nVPC Parameters: ')
    region = raw_input(' Region (us-east-1): ')
    if region == '':
        region = 'us-east-1'
    environment = raw_input(' Environment (Production): ')
    if environment == '':
        environment = 'Production'
    stack_prefix = raw_input(' Stack Prefix (prod): ')
    if stack_prefix == '':
        stack_prefix = 'prod'

    # Set AWS Credentials
    credentials = set_credentials(region)

    # Initialize AWS Clients
    s3 = set_s3_client(credentials)
    cf = set_cf_client(credentials)
    ec2 = set_ec2_client(credentials)

    # Determine how the script is being used TODO integrate cmd line args / --help
    script_action = raw_input('\nSelect an action:\n'
                              ' 1. Deploy Bucket, Key, and Create Parameters Files\n'
                              ' 2. Create Parameters Files\n'
                              ' 3. Deploy Default Stacks\n'
                              ' 4. Deploy Single Stack\n')

    if script_action is '1':
        print('Deploying Bucket, Key, and Creating Parameters Files')
        # Create CloudFormation S3 Bucket & Upload CloudFormation templates
        create_s3_bucket(s3, s3_bucket_name, region)
        upload_s3_object(s3, s3_bucket_name, environment,
                         cf_directory, cf_templates_list)
        bucket_url = get_bucket_url(s3_bucket_name, environment)

        # Create EC2 Key Pair, output to file
        ec2_key_name = set_ec2_key_name(raw_account_name, environment, region)
        ec2_key = create_ec2_key_pair(ec2, ec2_key_name)
        if ec2_key is not None:
            ec2_key_file_name = ec2_key_name + '.pem'
            write_file(ec2_key_file_name, ec2_key)

        if ec2_key is not None:
            print('\nEC2 Key Pair: ')
            print('Key File Created: ' + ec2_key_file_name)
            print('Key Name: ' + ec2_key_name)
            print('Key Value:\n' + ec2_key)
        else:
            print('\nEC2 Key "' + ec2_key_name + '" already exists.')

        # Create Parameters Files
        cf_default_parameters_dict = create_parameters_dict(cf, cf_templates_list, bucket_url)
        create_parameters_files(cf_default_parameters_dict)

    if script_action is '2':
        print('Creating Parameters Files')

        # Create Parameters Files
        cf_default_parameters_dict = create_parameters_dict(cf, cf_templates_list, bucket_url)
        create_parameters_files(cf_default_parameters_dict)

    if script_action is '3':
        # Define Base Network parameters, Deploy Stack
        base_network_cf_parameters_list = {'stack_prefix': stack_prefix, 'cf_stack_name': 'BaseNetwork',
                                           'AvailabilityZoneCount': az_count, 'CIDRRange': cidr, 'Environment': environment}
        base_network_stack_name = deploy_cf_stack(cf, bucket_url, cf_default_parameters_dict['base_network'])
        # Verify stack build completed, store dictionary of stack resources
        if get_stack_complete(cf, base_network_stack_name) is True:
            base_network_stack_resources = get_stack_resources(
                cf, base_network_stack_name)

        vpcid = base_network_stack_resources['VPCBase']
        route_table_public = base_network_stack_resources['RouteTablePublic']
        route_table_private_az1 = base_network_stack_resources['RouteTablePrivateAZ1']
        route_table_private_az2 = base_network_stack_resources['RouteTablePrivateAZ2']
        if az_count == 3:
            route_table_private_az3 = base_network_stack_resources['RouteTablePrivateAZ3']
        else:
            route_table_private_az3 = None

        # Define S3 VPC Endpoint parameters, Deploy Stack
        s3_vpc_endpoint_cf_parameters_list = {
            'stack_prefix': stack_prefix, 'cf_stack_name': 'S3-VPC-Endpoint', 'VPCID': vpcid,
            'route_table_public': route_table_public, 'route_table_private_az1': route_table_private_az1,
            'route_table_private_az2': route_table_private_az2, 'route_table_private_az3': route_table_private_az3
        }
        s3_vpc_endpoint_stack_name = deploy_s3_vpc_endpoint_cf_stack(
            cf, bucket_url, s3_vpc_endpoint_cf_parameters_list)

        # Define Route53 Internal Zone parameters, Deploy Stack
        route53_internalzone_cf_parameters_list = {
            'stack_prefix': stack_prefix, 'cf_stack_name': 'Route53-InternalZone', 'VPCID': vpcid,
            'Environment': environment, 'InternalZoneName': internal_zone_name
        }
        route53_internalzone_stack_name = deploy_route53_internalzone_cf_stack(
            cf, bucket_url, route53_internalzone_cf_parameters_list)

        # Define SNS Topic Subscription parameters, Deploy Stack
        sns_topic_subscriptions_cf_parameters_list = {
            'stack_prefix': stack_prefix, 'cf_stack_name': 'SNS-Topic-Subscriptions',
            'SubscriptionEndpoint1': sns_endpoint_1, 'SubscriptionProtocol1': sns_protocol_1,
            'SubscriptionEndpoint2': sns_endpoint_2, 'SubscriptionProtocol2': sns_protocol_2,
            'SubscriptionEndpoint3': sns_endpoint_3, 'SubscriptionProtocol3': sns_protocol_3,
            'DisplayName': raw_sns_topic_name
        }
        sns_topic_subscriptions_stack_name = deploy_sns_topic_subscriptions_cf_stack(
            cf, bucket_url, sns_topic_subscriptions_cf_parameters_list)

        # Verify stack build completed, store dictionary of stack resources -
        # these are grouped because they can all deploy at the same time, but
        # BaseNetwork needs to run first
        if get_stack_complete(cf, s3_vpc_endpoint_stack_name) is True:
            s3_vpc_endpoint_stack_resources = get_stack_resources(
                cf, s3_vpc_endpoint_stack_name)
        if get_stack_complete(cf, route53_internalzone_stack_name) is True:
            route53_internalzone_stack_resources = get_stack_resources(
                cf, route53_internalzone_stack_name)
        if get_stack_complete(cf, sns_topic_subscriptions_stack_name) is True:
            sns_topic_subscriptions_stack_resources = get_stack_resources(
                cf, sns_topic_subscriptions_stack_name)

        # Print Stack Outputs
        print('\nStack Outputs: ')
        print_stack_resources(base_network_stack_name,
                              base_network_stack_resources)
        print_stack_resources(s3_vpc_endpoint_stack_name,
                              s3_vpc_endpoint_stack_resources)
        print_stack_resources(route53_internalzone_stack_name,
                              route53_internalzone_stack_resources)
        print_stack_resources(sns_topic_subscriptions_stack_name,
                              sns_topic_subscriptions_stack_resources)


if __name__ == "__main__":
    main(sys.argv[1:])
