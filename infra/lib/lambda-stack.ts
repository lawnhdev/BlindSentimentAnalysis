import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';
import * as sqs from 'aws-cdk-lib/aws-sqs'; // Import SQS module
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class LambdaStack extends cdk.Stack {
  public readonly blindPostsQueue: sqs.Queue;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
      super(scope, id, props);

      // Define SQS Queue
      const queue = new sqs.Queue(this, 'BlindPostUrlQueue', {
          queueName: 'BlindPostUrlQueue',
          visibilityTimeout: Duration.seconds(300) // Adjust visibility timeout as needed
      });
      this.blindPostsQueue = queue;

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

      const blindPostScraper = new DockerImageFunction(this, 'BlindPostScraper', {
        code: DockerImageCode.fromImageAsset('../lambda'),
        //runtime: lambda.Runtime.PYTHON_3_12,
        //handler: 'main.lambda_handler',
        functionName: `blind-post-scraper`,
        timeout: Duration.minutes(5),
        memorySize: 512
      });

      // Create Event Source Mapping between SQS Queue and Lambda Function
      blindPostScraper.addEventSource(new SqsEventSource(queue, {
          batchSize: 10
      }));

      // Grant permissions for EC2 instance to access DynamoDB table
      blindPostsTable.grantReadWriteData(blindPostScraper);
      blindCommentsTable.grantReadWriteData(blindPostScraper);
  }
}