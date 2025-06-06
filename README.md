# Freddo Food Agent AI | LangGrpaph + Gemini + MCP Toolbox + AlloyDB

Note: This project is for demonstration only and is not an officially supported Google product.

## Introduction

This project demonstrates how we can provide our application with advanced search capabilities based on techniques such as embeddings and vector searches to improve the user experience.

The demo shows the search module of an online fashion store. The search engine is able to recommend items from our catalog based on an image provided.

Specifically, the demo showcases the following:

- **Image embedding**: The system extracts a vector representation (embedding) from the uploaded image.
- **Vector search**: The system compares the extracted embedding to a database of embeddings of known items in the catalog.
- **Recommendation**: The system recommends items that are similar to the uploaded image based on the results of the vector search.

## Table of Contents
<!-- TOC depthfrom:2 -->

- [Introduction](#introduction)
- [Table of Contents](#table-of-contents)
- [Understanding the demo](#understanding-the-demo)
    - [Understanding Image Embedding](#understanding-image-embedding)
    - [Using Vector Search](#using-vector-search)
    - [Architecture](#architecture)
- [Deploying](#deploying)
    - [Before you begin](#before-you-begin)
    - [Setting up your Database](#setting-up-your-database)
    - [Deploying MCP ToolBox](#deploying-mcp-toolbox)
    - [Deploying Freddo Agent AI](#deploying-freddo-agent-ai)
    - [Running Freddo Agent AI](#running-freddo-agent-ai)
    - [Clean up Resources](#clean-up-resources)

<!-- /TOC -->

## Understanding the demo
### Understanding Image Embedding
Image embedding simplifies image analysis by converting images into numerical vectors (embeddings) that capture their visual essence. Vertex AI's Multimodal API leverages a powerful pre-trained model to generate these embeddings, enabling tasks like image classification, visual search, and content moderation.

Key Benefits
- **Powerful Pre-Trained Model**: Vertex AI's model is trained on vast datasets, giving it a deep understanding of visual concepts. This eliminates the need to train your own models from scratch.
- **Semantic Understanding**: The model generates embeddings that capture the meaning within images, allowing for similarity comparisons that go beyond pixel-by-pixel analysis.
- **Versatility**: The Vertex AI Multimodal API can handle images, video, and text, opening up possibilities for cross-media analysis and search.

### Using Vector Search
Vector search allows you to find items in a database that are semantically similar to a query, even if they don't share exact keywords. The pgvector extension for PostgreSQL provides tools for storing vectors, creating indexes, and performing vector search operations. AlloyDB, Google's fully-managed PostgreSQL-compatible database, offers specific optimizations for vector search, making it an excellent platform for these applications.

Key Benefits of Using AlloyDB with pgvector
- **Performance**: AlloyDB has built-in optimizations for vector search operations, allowing you to perform similarity-based searches on large datasets with incredible speed.
- **Scalability**: AlloyDB's ability to scale seamlessly ensures that your vector search applications can handle growing data and complex queries without performance bottlenecks.
- **Operational Simplicity**: As a fully-managed service, AlloyDB handles administration tasks, backups, and updates, letting you focus on application development and leveraging optimized vector search features.

### Architecture
![Architecture](images/fashion_item_recommendation_app.png)

This architecture provides an image-based product recommendation system. It leverages Vertex AI to analyze images and generate meaningful representations of their visual content. These representations are stored in AlloyDB for fast similarity searches, allowing the system to recommend visually similar products to users based on their image submissions.

There 3 key components in this architecture: 
- **Cloud Run**: Hosts the frontend and backend components of the recommendation service, providing a serverless platform for code execution.
- **Vertex AI Multimodal Embedding**: Generates the image embedding from a pretrained model. Vertex AI provides a managed platform for creating, deploying, and using these multimodal embedding models.
- **AlloyDB for PostgreSQL**: Stores the image embeddings and relevant catalog item data, providing high-performance, scalable storage, and data retrieval for recommendations.

## Deploying

Deploying this demo consists of 3 steps:

1. Creating your database and initializing it with data
2. Deploying MCP ToolBox service to CloudRun
3. Deploying Freddo Agent AI using a Backend and the Frontend services to CloudRun

### Before you begin
Clone this repo to your local machine:
```
git clone https://github.com/mtoscano84/freddo-food-agent-ai.git
```

### Setting up your Database
Freddo Agent AI Assistant leverages AlloyDB to persist the data, provides context and resolve user queries.

Follow these instructions to set up and configure the database

[Setting up your Database](docs/alloydb.md)

### Deploying MCP ToolBox
MCP ToolBox exposes a set of specialized functionalities, or "tools," that allow the agent to perform actions and access data.

Follow these instructions to deploy MCP ToolBox along with the Tools in CloudRun

[Deploying MCP ToolBox](docs/toolbox.md)

### Deploying Freddo Agent AI
Freddo Agent AI is composed of two Cloud Run Services:

1. **Frontend**: Provides an user interface to interact with the agent and the backend service.
2. **Backend**: This service hosts the core AI agent. It orchestrates user interactions with the different components to provide the answers.

To deploy Freddo Agent AI, follow these instructions:

[Deploy Freddo Agent AI](docs/deploy_app_services.md)

### Running Freddo Agent AI
Start uploading a picture to get recommendations !

![GenAI FashionStore](images/GenAIFashionStore_DemoDark.gif)

### Clean up Resources
[Instructions for cleaning up resources](./docs/clean_up.md)





