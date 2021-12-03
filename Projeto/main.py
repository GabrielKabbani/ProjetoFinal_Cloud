#IMPORTS:

import boto3
import time
import os

#CRIANDO FUNÇÕES:

def create_key_pair(region, name):
    ec2_client = boto3.client("ec2", region_name=region)
    key_pair = ec2_client.create_key_pair(KeyName=name)
    private_key = key_pair["KeyMaterial"]
    with os.fdopen(os.open("../../keys_projeto/aws_ec2_key_{0}.pem".format(name), os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
        handle.write(private_key)
    return name

#já foram criadas, nao precisa mais rodar:
# KP_NV = create_key_pair("us-east-1", "us-east-1-KP") 
# KP_OH = create_key_pair("us-east-2", "us-east-2-KP") 

ec2_client_2 = boto3.client("ec2", region_name="us-east-2")
ec2_client_1 = boto3.client("ec2", region_name="us-east-1")
ec2LoadBalancer = boto3.client('elbv2', region_name="us-east-1")
ec2AutoScalling = boto3.client('autoscaling', region_name="us-east-1")

def get_instance_ip(instance, client, option): #pra funcionar, não podem ter outras instancias com o mesmo nome rodando
    reservations = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance]}])
    #print('RESERVATIONS: \n {0}'.format(reservations))
    if option=='ip': 
        for instance in reservations['Reservations']:
            for subinst in instance['Instances']:
                if subinst['State']['Name']=='running':
                    ip=subinst['PublicIpAddress']
                    return str(ip)

    elif option=='id':
        for instance in reservations['Reservations']:
            for subinst in instance['Instances']:
                if subinst['State']['Name']=='running':
                    ip=subinst['InstanceId']
                    return str(ip)

#security group functions:

def security_group_lb():
    region = boto3.resource("ec2", region_name="us-east-1")
    sg = region.create_security_group(
        GroupName='lbKabbani',
        Description='load balancer SG'
    )

    sg.authorize_ingress(
        CidrIp="0.0.0.0/0",
        FromPort=80,
        ToPort=80,
        IpProtocol="tcp"
    )

    response = ec2_client_1.describe_security_groups(
        Filters=[
            dict(Name='group-name', Values=['lbKabbani'])
    ])


    res =  response['SecurityGroups'][0]['GroupId']
    print("LB Security Group created \n")
    return res


def security_group_django():
    region = boto3.resource("ec2", region_name="us-east-1")
    sg = region.create_security_group(
        GroupName='djangoKabbani',
        Description='django SG'
    )

    sg.authorize_ingress(
        CidrIp="0.0.0.0/0",
        FromPort=8080,
        ToPort=8080,
        IpProtocol="tcp"
    )

    sg.authorize_ingress(
        CidrIp="0.0.0.0/0",
        FromPort=22,
        ToPort=22,
        IpProtocol="tcp"
    )

    response = ec2_client_1.describe_security_groups(
        Filters=[
            dict(Name='group-name', Values=['djangoKabbani'])
    ])


    res =  response['SecurityGroups'][0]['GroupId']
    print("Django Security Group created \n")
    return res

id_sg_django = str(security_group_django())

def security_group_postgres():
    region = boto3.resource("ec2", region_name="us-east-2")
    sg = region.create_security_group(
        GroupName='postKabbani',
        Description='postgres SG'
    )

    sg.authorize_ingress(
        CidrIp="0.0.0.0/0",
        FromPort=5432,
        ToPort=5432,
        IpProtocol="tcp"
    )

    sg.authorize_ingress(
        CidrIp="0.0.0.0/0",
        FromPort=22,
        ToPort=22,
        IpProtocol="tcp"
    )

    response = ec2_client_2.describe_security_groups(
        Filters=[
            dict(Name='group-name', Values=['postKabbani'])
    ])

    res =  response['SecurityGroups'][0]['GroupId']
    print("Postgres Security Group created \n")
    return res

    


def create_instance():
    instances = ec2_client_2.run_instances(
        ImageId="ami-020db2c14939a8efb",
        MaxCount=1,
        MinCount=1,
        TagSpecifications=[
            {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'KABBANI_PROJETO'
                },
                {
                    'Key': 'Owner',
                    'Value': 'KABBANI'
                },
                {
                    'Key': 'RunId',
                    'Value': '12345'
                }
            ]
            }
        ],
        InstanceType="t2.micro",
        KeyName = "us-east-2-KP"
    )
    print('instance created')


def create_instance_with_db():
    with open("creating_postgres_from_cl.sh", "r") as f:
      usrdata = f.read()
    scdb=str(security_group_postgres())
    instances = ec2_client_2.run_instances(
        ImageId="ami-020db2c14939a8efb",
        MaxCount=1,
        MinCount=1,
        TagSpecifications=[
            {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'KABBANI_WITH_DB_OK'
                },
                {
                    'Key': 'Owner',
                    'Value': 'KABBANI'
                },
                {
                    'Key': 'RunId',
                    'Value': '12345'
                }
            ]
            }
        ],
        SecurityGroupIds=[scdb],
        InstanceType="t2.micro",
        UserData = usrdata,
        KeyName = "us-east-2-KP"
    )
    print('postgres instance created\n')

def create_instance_with_django():
    ip_post=get_instance_ip('KABBANI_WITH_DB_OK', ec2_client_2,'ip')
    print('ip postgres within django command line: {}\n'.format(ip_post))
    replacements = {'ip_django': ip_post}
    with open('creating_django_from_cl.sh') as infile, open('creating_django_from_cl_ip.sh', 'w') as outfile:
        for line in infile:
            for src, target in replacements.items():
                line = line.replace(src, target)
            outfile.write(line)
        
    with open("creating_django_from_cl_ip.sh", "r") as f:
        usrdata = f.read()

    instances = ec2_client_1.run_instances(
        ImageId="ami-0279c3b3186e54acd",
        MaxCount=1,
        MinCount=1,
        TagSpecifications=[
            {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'KABBANI_WITH_DJANGO_OK'
                },
                {
                    'Key': 'Owner',
                    'Value': 'KABBANI'
                },
                {
                    'Key': 'RunId',
                    'Value': '12345'
                }
            ]
            }
        ],
        SecurityGroupIds=[id_sg_django],
        InstanceType="t2.micro",
        UserData = usrdata,
        KeyName = "us-east-1-KP"
    )
    print('django instance created\n')


def create_AMI(name, ids, reg):
    print('id django within ami creation: {}\n'.format(ids))
    instance = reg.create_image(
      Name=name,
      NoReboot=False,
      InstanceId=ids
    )
    print("AMI created\n")
    return instance['ImageId']

def terminate_instance(ids, client):
    print('id django within instance termination: {}\n'.format(ids))
    idkill = ['{}'.format(ids)]
    client.terminate_instances(InstanceIds=idkill)
    print("Instance destroyed\n")


def target_group(): 
    describe = ec2_client_1.describe_vpcs()
    res = describe["Vpcs"][0]["VpcId"] #ver qual ta entrando
    target_group = ec2LoadBalancer.create_target_group(
        Name="targetKABBANI",
        Protocol="HTTP",
        Port=8080,
        HealthCheckEnabled=True,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='8080',
        HealthCheckPath='/admin/',
        TargetType="instance",
        VpcId=res,
        Matcher={
        'HttpCode': '200,302,301,404,403',
        }
    )
    print('Target group created\n')
    return target_group["TargetGroups"][0]["TargetGroupArn"]


def creating_load_balancer(): 
    sclb=str(security_group_lb())
    des = ec2_client_1.describe_subnets()
    subnets=[]
    for subnet in des['Subnets']:
        subnets.append(subnet['SubnetId'])
    load_balancer = ec2LoadBalancer.create_load_balancer(
        Name='lBkabbani',
        SecurityGroups=[sclb],
        Tags=[
        {
            'Key': 'SGLB',
            'Value': 'lB'
        }
        ],
        IpAddressType='ipv4',
        Subnets=subnets
    )


    print('Load Balancer created\n')
    return load_balancer

    


def auto_scalling(tg, imgid):
    with open("creating_django_from_cl_ip.sh", "r") as f:
        usrdata = f.read()

    ec2AutoScalling.create_launch_configuration(
                LaunchConfigurationName='confname',
                ImageId=imgid,
                SecurityGroups=[id_sg_django],
                InstanceType='t2.micro', 
                UserData = usrdata
        )
    
    regions =[]
    describe_regions= ec2_client_1.describe_availability_zones()
    for region in describe_regions["AvailabilityZones"]:
        regions.append(region["ZoneName"])
    ec2AutoScalling.create_auto_scaling_group(
        AutoScalingGroupName="asgKabbani",
        LaunchConfigurationName="confname", 
        TargetGroupARNs=[tg],
        AvailabilityZones=regions,
        MinSize=1,
        MaxSize=3
    )

    print('AutoScalling created\n')


def finalizing_load_balancer(tg,lbr):
    ec2AutoScalling.attach_load_balancer_target_groups(
        TargetGroupARNs=[tg],
        AutoScalingGroupName='asgKabbani'
    )
    ec2LoadBalancer.create_listener(
      LoadBalancerArn=lbr,
      DefaultActions=[{ 'Type': 'forward', 'TargetGroupArn': tg}],
      Protocol='HTTP',
      Port=80  
    )
    print('LB done\n')




#EXECUTANDO EM ORDEM (sleeps são para ter tempo da máquina inicial rodar quando ela é referenciada por outra função)


create_instance_with_db()
time.sleep(200) #tempo elevado porque quando deixei menos, o funcionamento oscilava
create_instance_with_django()
time.sleep(60)
idami=create_AMI('AMI_KABBANI',get_instance_ip('KABBANI_WITH_DJANGO_OK', ec2_client_1, 'id'), ec2_client_1)
time.sleep(200)
terminate_instance(get_instance_ip('KABBANI_WITH_DJANGO_OK', ec2_client_1, 'id'), ec2_client_1)
time.sleep(200)
tg=target_group()
time.sleep(20)
LB= creating_load_balancer()
filteredLB = LB['LoadBalancers'][0]['LoadBalancerArn']
time.sleep(20)
auto_scalling(tg,idami)
time.sleep(20)
finalizing_load_balancer(tg,filteredLB)