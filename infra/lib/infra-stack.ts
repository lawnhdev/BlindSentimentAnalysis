import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3Deployment from 'aws-cdk-lib/aws-s3-deployment';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class InfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'MyVpc', {
      maxAzs: 2, // create 2 availability zones in this VPC
      natGateways: 1, // Number of NAT Gateways
      subnetConfiguration: [
          {
            cidrMask: 24,
            name: 'PublicSubnet',
            subnetType: ec2.SubnetType.PUBLIC, // Public subnet
          },
        ],
    });

    // Create S3 bucket
    const bucket = new s3.Bucket(this, 'BlindScraperBucket', {
      bucketName: 'blind-scraper-bucket',
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Destroy the bucket when stack is deleted (for demo purposes)
      autoDeleteObjects: true,
    });

    // Upload Python script to S3 bucket
    const bucketDeployment = new s3Deployment.BucketDeployment(this, 'BlindScraper', {
      sources: [s3Deployment.Source.asset('../scraper/')],
      destinationBucket: bucket
    });

    const blindPostsTable = new dynamodb.Table(this, 'Posts', {
      tableName: 'Posts', // Specify the table name here
      partitionKey: { name: 'postId', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const blindCommentsTable = new dynamodb.Table(this, 'Comments', {
      tableName: 'Comments',
      partitionKey: { name: 'commentId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'postId', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const securityGroup = new ec2.SecurityGroup(this, `infra-stack-security-group`, {
        vpc: vpc,
        allowAllOutbound: true,
        description: 'CDK Security Group'
    });

    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'SSH into the ec2 instance from anywhere');


    const companiesPerInstance = 9; // Number of EC2 instances... right now we can only have 5 instances due to vcpu limit
    const companies = ["Meta", "Google", "Microsoft", "Amazon", "Apple", "Nvidia", "Tesla", "Netflix", "Salesforce", "Reddit",
                       "AMD", "Oracle", "Snowflake", "Uber", "Lyft", "Samsung", "Intel", "PayPal", "GameStop", "Snap",
                       "Palantir", "ByteDance", "Coinbase", "Robinhood", "Block", "Roblox", "Airbnb", "Shopify",
                       "Visa", "CrowdStrike", "Qualcomm", "Adobe", "Cisco", "Accenture", "IBM", "Dell", "Infosys", "Spotify",
                       "Workday", "DoorDash", "Grubhub", "Cognizant", "Starbucks", "ServiceNow", "SoftBank"];

    // Calculate number of companies per instance
    const numInstances = Math.ceil(companies.length / companiesPerInstance);
    for (let i = 0; i < numInstances; i++) {
        const instance = new ec2.Instance(this, `scraper_ec2_instance_${i}`, {
          instanceType: new ec2.InstanceType('t2.micro'),
          machineImage: ec2.MachineImage.latestAmazonLinux2023(),
          vpc: vpc,
          vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC }, // Launch in the public subnet
          securityGroup: securityGroup,
          userData: ec2.UserData.forLinux()
        });

        // Calculate the slice of companies for this instance
        const startIdx = i * companiesPerInstance;
        const endIdx = Math.min((i + 1) * companiesPerInstance, companies.length);
        const instanceCompanies = companies.slice(startIdx, endIdx);

        instance.userData.addCommands(
            `echo '${JSON.stringify(instanceCompanies)}' > /home/ec2-user/companies.json`,
            'sudo chmod +r /home/ec2-user/companies.json',
            'echo "Starting userdata script"',
            'echo "Downloading script from S3"',
            'aws s3 cp s3://' + bucket.bucketName + '/userdata-script.sh /home/ec2-user/userdata-script.sh',
            'sudo chmod +x /home/ec2-user/userdata-script.sh', // Ensure script is executable
            'aws s3 cp s3://' + bucket.bucketName + '/testscraper.py /home/ec2-user/testscraper.py',
            'sudo chmod +x /home/ec2-user/testscraper.py', // Ensure script is executable
            '/home/ec2-user/userdata-script.sh > /home/ec2-user/userdata-output.log 2>&1', // Execute script and log output
            'echo "Userdata script execution completed"',
            'python3 /home/ec2-user/testscraper.py'
        );

        // 'python3 /home/ec2-user/testscraper.py > /home/ec2-user/test-scraper-result.txt'

        // Allow EC2 instance to read from S3 bucket
        bucket.grantRead(instance);
        // Grant permissions for EC2 instance to access DynamoDB table
        blindPostsTable.grantReadWriteData(instance);
        blindCommentsTable.grantReadWriteData(instance);
    }
  }
}