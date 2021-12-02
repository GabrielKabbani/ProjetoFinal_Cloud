#IMPORTS:

import boto3
import time

#CRIANDO FUNÇÕES:

def create_key_pair(region, name):
    ec2_client = boto3.client("ec2", region_name=region)
    key_pair = ec2_client.create_key_pair(KeyName=name)
    private_key = key_pair["KeyMaterial"]
    with os.fdopen(os.open("aws_ec2_key_{0}.pem".format(name), os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
        handle.write(private_key)
    return name

#já foram criadas, nao precisa mais rodar:
#KP_NV = create_key_pair("us-east-1", "us-east-1-KP") 
#KP_OH = create_key_pair("us-east-2", "us-east-2-KP") 

ec2_client_2 = boto3.client("ec2", region_name="us-east-2")
ec2_client_1 = boto3.client("ec2", region_name="us-east-1")

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
        InstanceType="t2.micro",
        UserData = usrdata,
        KeyName = "us-east-2-KP"
    )
    print('postgres instance created\n')

def create_instance_with_django():

    ip_post=str(get_instance_ip('KABBANI_WITH_DB_OK', ec2_client_2,'ip'))
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
        InstanceType="t2.micro",
        UserData = usrdata,
        KeyName = "us-east-1-KP"
    )
    print('django instance created\n')


def create_AMI(name, id, reg):
    instance = reg.create_image(
      Name=name,
      NoReboot=False,
      InstanceId=id
    )
    



#EXECUTANDO EM ORDEM (sleeps são para ter tempo da máquina inicial rodar quando ela é referenciada por outra função)


create_instance_with_db()
time.sleep(60)
create_instance_with_django()
time.sleep(60)
create_AMI('AMI_KABBANI',get_instance_ip('KABBANI_WITH_DJANGO_OK', ec2_client_1, 'id'), ec2_client_1) 