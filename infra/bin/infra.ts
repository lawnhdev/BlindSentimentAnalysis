#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { InfraStack } from '../lib/infra-stack';
import { LambdaStack } from '../lib/lambda-stack';

const app = new cdk.App();
const lambdaStack = new LambdaStack(app, 'LambdaStack', {
    });
const infraStack = new InfraStack(app, 'InfraStack', {
  blindPostsQueue: lambdaStack.blindPostsQueue // allow the infra stack to reference the sqs queue created in lambda stack
});

