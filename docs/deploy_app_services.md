# Deploy the Application Services to CloudRun

## Before you begin
1. Open a terminal and set the following environment variables
```
export REGION=us-central1
export PROJECT_ID=freddo-food-agent-ai
```

2. Enable the necesarry APIs:
```
gcloud services enable artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       run.googleapis.com \
                       storage.googleapis.com \
                       aiplatform.googleapis.com 
```

3. Grant the necessary permissions:

- Get your project number to build the default service account name in the format PROJECT_NUM-compute@developer.gserviceaccount.com
```
gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
```

- Grant the permissions:
```
# Grant Cloud Run service account access to GCS
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:754204885755-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:754204885755-compute@developer.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:754204885755-compute@developer.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:754204885755@cloudbuild.gserviceaccount.com" \
    --role="roles/artifactregistry.repoAdmin"

# Grant Vertex AI User role to the service account
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:754204885755-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Grant Vertex AI Model User role to the service account
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:754204885755-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.modelUser"
```

**Note**: Use the default compute service account

4. If you are under a domain restriction organization policy [restricting](https://cloud.google.com/run/docs/authenticating/public#domain-restricted-sharing) unauthenticated invocations for your project (e.g. Argolis), you will need to temporary disable de Org Policy **iam.allowedPolicyMemberDomains**

![Disable Org Policy iam.allowedPolicyMemberDomains](../images/disable_orgpolicy_allowedPolicyMemberDomains.png)

**Note**: The organization policy should be re-established after the IAM policy assigned during the CloudRun Service deployed

## Deploy the backend service to CloudRun
1. Go to freddo-food-agent-ai/src/backend and edit the file freddo_agent.py to point the MCP ToolBox Cloud Run Service
```
def main(user_input):
    thread_id = "user-thread-1"
    model = ChatVertexAI(model_name="gemini-2.0-flash")
    
    print("Starting Toolbox client initialization...")
    try:
        client = ToolboxClient("https://toolbox-754204885755.us-central1.run.app")
        print("Toolbox client initialized successfully")
        
        print("Attempting to load toolset...")
        tools = client.load_toolset()
        print(f"Tools loaded successfully: {tools}")
        
    except Exception as e:
        print(f"Error with Toolbox: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise
```

**Note**: You can get the MCP ToolBox URL executing:
```
gcloud run services describe toolbox --format 'value(status.url)'
```

2. Go to freddo-food-agent-ai/src/backend and edit the file app.py to point the right URL for your bucket
```
# Initialize GCS client
storage_client = storage.Client()
BUCKET_NAME = "freddo-food-agent-ai-bck01"  # Replace with your bucket name
bucket = storage_client.bucket(BUCKET_NAME)
```

3. Go to freddo-food-agent-ai directoy and deploy the backend service
```
## Create a repository in Artifact Registry
gcloud artifacts repositories create freddo-backend-images \
    --repository-format=docker \
    --location=us-central1 \
    --project=$PROJECT_ID \
    --description="Test repository for freddo-backend images"

## Build the IMAGE
gcloud builds submit src/backend/ --tag us-central1-docker.pkg.dev/$PROJECT_ID/freddo-backend-images/freddo-backend

## Deploy the service
gcloud run deploy freddo-backend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/freddo-backend-images/freddo-backend \
    --platform managed \
    --allow-unauthenticated \
    --region us-central1 \
    --project $PROJECT_ID
```

Outuput:
```
Deploying container to Cloud Run service [freddo-backend] in project [freddo-food-agent-ai] region [us-central1]
✓ Deploying new service... Done.                                                                                                                          
  ✓ Creating Revision...                                                                                                                                  
  ✓ Routing traffic...                                                                                                                                    
  ✓ Setting IAM Policy...                                                                                                                                 
Done.                                                                                                                                                     
Service [freddo-backend] revision [freddo-backend-00001-hk2] has been deployed and is serving 100 percent of traffic.
Service URL: https://freddo-backend-754204885755.us-central1.run.app
```

4. Validate the backend service:
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}' \
  https://freddo-backend-754204885755.us-central1.run.app/chat
```

**Note**: Replace the URL with you Backend Cloud Run Service

## Deploy the frontend service to CloudRun
1. Go to freddo-food-agent-ai/src/frontend/src and edit the file App.js to point the Backend Cloud Run Service URL
```
// Instead of relying on build-time env variables, use window._env_ for runtime config
const BACKEND_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5001'
  : 'https://freddo-backend-754204885755.us-central1.run.app';

console.log('Using backend URL:', BACKEND_URL); // For debugging
```

2. Go to freddo-food-agent-ai directoy and deploy the frontend service
```
## Create a repository in Artifact Registry
gcloud artifacts repositories create freddo-frontend-images \
    --repository-format=docker \
    --location=us-central1 \
    --project=$PROJECT_ID \
    --description="Test repository for freddo-frontend images"

## Build the IMAGE
gcloud builds submit src/frontend/ --tag us-central1-docker.pkg.dev/$PROJECT_ID/freddo-frontend-images/freddo-frontend

## Deploy the service
gcloud run deploy freddo-frontend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/freddo-frontend-images/freddo-frontend \
    --platform managed \
    --allow-unauthenticated \
    --region us-central1 \
    --project $PROJECT_ID
```
Outuput:
```
Deploying container to Cloud Run service [freddo-frontend] in project [freddo-food-agent-ai] region [us-central1]
✓ Deploying new service... Done.                                                                                                                          
  ✓ Creating Revision...                                                                                                                                  
  ✓ Routing traffic...                                                                                                                                    
  ✓ Setting IAM Policy...                                                                                                                                 
Done.                                                                                                                                                     
Service [freddo-frontend] revision [freddo-frontend-00001-ncm] has been deployed and is serving 100 percent of traffic.
Service URL: https://freddo-frontend-754204885755.us-central1.run.app
```

4. Open a Web Browser and use the Service URL from the previus step to connect to the App
