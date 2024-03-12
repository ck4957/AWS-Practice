import * as cdk from 'aws-cdk-lib';
import { Bucket, CfnBucket } from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';

class L3Bucket extends Construct {
  constructor(scope: Construct, id: string, expiration: number) {
    super(scope, id);

    new Bucket(this, 'L3Bucket', {
      lifecycleRules: [{
        expiration: cdk.Duration.days(expiration)
      }]
    })
  }
}

export class CdkStarterStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here

    // example resource
    // const queue = new sqs.Queue(this, 'CdkStarterQueue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });

    // create an s3 bucket 3 ways: 
    // L1 Construct
    new CfnBucket(this, 'MyL1Bucket', {
      lifecycleConfiguration: {
        rules: [{
          expirationInDays: 1,
          status: 'Enabled'
        }]
      }
    })

    const duration = new cdk.CfnParameter(this, 'duration', {
      default: 6,
      minValue: 1,
      maxValue: 10,
      type: 'Number'
    })

    // L2 Construct
    const myL2Bucket = new Bucket(this, 'MyL2Bucket', {
      lifecycleRules: [{
        expiration: cdk.Duration.days(duration.valueAsNumber)
      }]
    })

    // L3 Construct
    new L3Bucket(this, 'MyL3Bucket', 3);

    // Cfn Outputs - shown after deployment
    new cdk.CfnOutput(this, 'MyL2BucketName', {
      value: myL2Bucket.bucketName
    })
  }
}
