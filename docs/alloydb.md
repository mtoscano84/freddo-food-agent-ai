# Setup and configure AlloyDB
## Before you begin

1. Make sure you have a Google Cloud project and billing is enabled.

2. Set your PROJECT_ID environment variable:
```
export PROJECT_ID=<YOUR_PROJECT_ID>
```

3. [Install](https://cloud.google.com/sdk/docs/install) the gcloud CLI.

4. Set gcloud project:
```
gcloud config set project $PROJECT_ID
```
5. Enable APIs:
```
gcloud services enable alloydb.googleapis.com \
                       compute.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
                       vpcaccess.googleapis.com \
                       aiplatform.googleapis.com
```

6. Install [python](https://cloud.google.com/python/docs/setup#installing_python) and set up a python virtual environment.

7. Make sure you have python version 3.11+ installed.

```
python3 -V
```

8. Download and install [postgres-client cli (psql)](https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/)

## Enable private services access
In this step, we will enable Private Services Access so that AlloyDB is able to connect to your VPC. You should only need to do this once per VPC (per project).

1. Set environment variables:
```
export VPC_NAME=my-vpc
export SUBNET_NAME=my-subnet
export RANGE_NAME=my-allocated-range-default
export DESCRIPTION="peering range for alloydb-service"
```
2- Create VPC Network and subnet:
```
gcloud compute networks create $VPC_NAME \
    --project=$PROJECT_ID \
    --subnet-mode=custom \
    --mtu=1460 \
    --bgp-routing-mode=regional
```
3- Create a subnet:
```
gcloud compute networks subnets create $SUBNET_NAME \
    --project=$PROJECT_ID \
    --range=10.0.0.0/24 \
    --stack-type=IPV4_ONLY \
    --network=$VPC_NAME \
    --region=us-central1
```
4- Create a Firewall rule to allow SSH to the Network:
```
gcloud compute firewall-rules create allow-ssh-$VPC_NAME --network $VPC_NAME --allow tcp:22,tcp:3389,icmp --source-ranges 0.0.0.0/0
```

5. Create an allocated IP address range:
```
gcloud compute addresses create $RANGE_NAME \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --description="$DESCRIPTION" \
    --network=$VPC_NAME
```

6. Ensure you have your Application Authentication Default (ADC) available for you project
```
gcloud auth application-default login
```

7. Create a private connection:
```
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges="$RANGE_NAME" \
    --network=$VPC_NAME
```

## Create a AlloyDB cluster
1. Set environment variables. For security reasons, use a different password for $DB_PASS and note it for future use:
```
export CLUSTER=my-alloydb-cluster
export DB_PASS=my-alloydb-pass
export INSTANCE=my-alloydb-instance
export REGION=us-central1
```

2. Create an AlloyDB cluster:
```
gcloud alloydb clusters create $CLUSTER \
    --password=$DB_PASS\
    --network=$VPC_NAME \
    --region=$REGION \
    --project=$PROJECT_ID
```

3. Create a primary instance:
```
gcloud alloydb instances create $INSTANCE \
    --instance-type=PRIMARY \
    --cpu-count=4 \
    --region=$REGION \
    --cluster=$CLUSTER \
    --project=$PROJECT_ID \
    --ssl-mode=ALLOW_UNENCRYPTED_AND_ENCRYPTED
```

4- Enable the database flag password.complexity_enforce=on. It is a requirement to use Public IP
```
gcloud beta alloydb instances update $INSTANCE \
   --database-flags password.enforce_complexity=on \
   --region=$REGION  \
   --cluster=$CLUSTER \
   --project=$PROJECT_ID \
   --update-mode=FORCE_APPLY
```
Note: The operation takes around 3 minutes to complete

5. Enable Public IP for the AlloyDB Instance
```
gcloud alloydb instances update $INSTANCE \
    --cluster=$CLUSTER  \
    --region=$REGION  \
    --assign-inbound-public-ip=ASSIGN_IPV4
```
Note: The operation takes around 3 minutes to complete

### Set up connection to AlloyDB
For this demo environment, we will set up the connection from the local PC to AlloyDB using Public IP. For productions environment, we recommend to connect using the private IP and a proxy configuration.

1. Open a new terminal, install AlloyDB Auth Proxy:

Install AlloyDB Auth Proxy
```
wget https://storage.googleapis.com/alloydb-auth-proxy/v1.13.1/alloydb-auth-proxy.darwin.arm64 -O alloydb-auth-proxy
chmod +x alloydb-auth-proxy
```
Note: Download the right software for your local machine. Check out the distributions available in https://cloud.google.com/alloydb/docs/auth-proxy/connect#install

2. Run the AlloyDB Auth Proxy, having it listen on its default address of 127.0.0.1:

```
export CLUSTER=my-alloydb-cluster
export INSTANCE=my-alloydb-instance
export REGION=us-central1
export PROJECT_ID=freddo-food-agent-ai
./alloydb-auth-proxy \
  /projects/$PROJECT_ID/locations/$REGION/clusters/$CLUSTER/instances/$INSTANCE --public-ip
```
You will need to allow this command to run while you are connecting to AlloyDB.

3. Verify you can connect to your instance with the psql tool. Enter password for AlloyDB ($DB_PASS environment variable set above) when prompted:
```
psql -h 127.0.0.1 -U postgres
```
4. While connected using psql, create a database and switch to it:
```
CREATE DATABASE recipe_store;
\c recipe_store
```

5. Exit from psql:
```
exit
```

## Initialize data in AlloyDB

Before we can load the data in AlloyDB, we need to setup the integration between AlloyDB and Vertex AI

1. Get the Project Number associated with the Project ID
```
gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
```

2. Grant Vertex AI permission to the AlloyDB Service Agent
```
gcloud projects add-iam-policy-binding $PROJECT_ID \
--member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-alloydb.iam.gserviceaccount.com" \
--role="roles/aiplatform.user"
```
Note: The permission might need until 1 minute to get applied

3- Connect to the AlloyDB Instance to validate the integration
```
psql -h 127.0.0.1 -U postgres -d recipe_store
SELECT array_dims(embedding('text-embedding-005', 'AlloyDB AI')::real[]);
```

4. Go to freddo-food-agent-ai/src/backend/ and edit the db_config_params with your connection string
```
host=127.0.0.1
database=recipe_store
user=postgres
password=MySecure123welcome123!
```

2. Create a GCS Bucket
```
gcloud storage buckets create gs://$BUCKET_NAME --project=$PROJECT_ID --location=$REGION
```

3. Change into the Catalog Image Repository
```
cd genai-fashionmatch/data/catalog_images
```

4. Upload the catalog images from local to the GCS Bucket
```
gcloud storage cp * gs://$BUCKET_NAME --project=$PROJECT_ID
```

5. Make a copy of example-config.ini and name it config.ini
```
cd genai-fashionmatch/fashionmatch-service/setup
cp example-config.ini config.ini
```

6. Update config.ini with your own project, repo names and database information. Keep using 127.0.0.1 as the datastore host IP address for port forwarding.
```
;This module defines data access variables
[CORE]
PROJECT = genai-fashionmatch
LOCATION = us-central1
LANDING_REPO = landing-image-repo-863363744101
CATALOG_REPO = catalog-repo-863363744101

[CONNECTION]
host = 127.0.0.1
port = 5432
database = fashionstore
user = postgres
password = "my-alloydb-pass"
```

7. Install requirements and populate data into database:
```
source load_db.sh
```

8. Upload the architecture to GCS:
```
cd genai-fashionmatch/images
gcloud storage cp fashion_item_recommendation_app.png gs://$BUCKET_NAME --project=$PROJECT_ID
```

## Clean up resources
Clean up after completing the demo.

1. Set environment variables:
```
export VM_INSTANCE=alloydb-proxy-vm
export CLUSTER=my-alloydb-cluster
export REGION=us-central1
export RANGE_NAME=my-allocated-range-default
```

2. Delete Compute Engine VM:
```
gcloud compute instances delete $VM_INSTANCE
```

3. Delete AlloyDB cluster that contains instances:
```
gcloud alloydb clusters delete $CLUSTER \
    --force \
    --region=$REGION \
    --project=$PROJECT_ID
```

4. Delete an allocated IP address range:
```
gcloud compute addresses delete $RANGE_NAME \
    --global
```

