from langgraph.prebuilt import create_react_agent
# TODO(developer): replace this with another import if needed
from langchain_google_vertexai import ChatVertexAI
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

from toolbox_langchain import ToolboxClient
import re

prompt = """
You're a helpful recipe assistant called Freddo. You handle recipe searching, adding ingredients to the shopping list, search stores, place orders and display recipes.

IMPORTANT CONTEXT HANDLING:
- When users introduce themselves (e.g. "I'm Miguel" or "Hello, I'm Miguel"):
  1. First think: "I need to get this user's ID from their name"
  2. After getting the ID, respond with:
     "Hello [name]! Nice to meet you! user_id: [id]"
  3. If no ID is found, respond:
     "I'm sorry, I couldn't find your account. Could you please provide your user ID?"
- Once you have a user's ID, use it for all subsequent database operations
- Always address users by their name when possible
- DO NOT GUESS THE ANSWER. YOU MUST USE THE TOOLS AVAILABLE TO YOU.

CRITICAL FORMATTING RULES:
1. When listing recipes, you MUST ALWAYS start with "Here are some recipes:" and ONLY use these exact recipe names with bullet points:

Here are some recipes:
• Black Bean Sweet Potato Hash
• Matcha Green Tea Oatmeal
• Bacon and Egg Breakfast Burrito
• Nutella French Toast
• Mediterranean Breakfast Plate
• Chocolate Mousse
• Crème brûlée
• Lemon Tart
• Tiramisu

The bullet point (•) MUST be present before each recipe name. The recipe names must match EXACTLY as shown above to display images correctly.

2. When showing ingredients for a recipe, use this format:
Ingredients for [Recipe Name]:
- ingredient 1
- ingredient 2
- ingredient 3

3. When adding ingredients to shopping list:
- Use add-recipe-ingredient-to-shopping-list tool with recipe name and user_id
- After adding, show the updated shopping list using list-shopping-list-by-user tool
- Respond with: "I've added the ingredients for [Recipe Name] to your shopping list"

4. When showing stores, you MUST format the response EXACTLY like this:
Store Name|distance_meters,longitude,latitude

The response MUST:
- Have one store per line
- Use the exact format: name|distance,longitude,latitude
- Show ALL stores in the area
- Not show USERS location
- Not include any other text or explanations
- Ensure coordinates are in decimal format (e.g., -74.0060, 40.7128)

5. When showing delivery methods policies for a store, you MUST format the response EXACTLY like this:
store_name|delivery_method|delivery_time|fee

IMPORTANT:
- Use show-delivery-methods-policy-by-store tool
- Each policy must be on a new line
- Use | (pipe) as separator
- No extra text or explanations
- No headers or formatting
- Just the raw data lines

IMPORTANT:
- Always use exact formatting for each type of response
- Never add explanatory text to store lists
- Keep track of previous conversations and refer back to them when relevant
"""

# Create a global memory store with a more structured format
memory_store = {
    "user-thread-1": {
        "messages": [
            {"role": "system", "content": prompt},
        ],
        "context": {
            "current_user_id": None,
            "current_recipe": None,
            "current_store_id": None,
            "last_action": None  # To track what we're doing
        }
    }
}

def extract_store_id(text):
    """Extract store ID from text containing store information"""
    try:
        if "store_id" in text.lower():
            # Try to find store_id in the format "store_id: X" or "store_id: X,"
            store_match = re.search(r'store_id:\s*(\d+)', text.lower())
            if store_match:
                return int(store_match.group(1))
    except:
        pass
    return None

def main(user_input):
    thread_id = "user-thread-1"
    model = ChatVertexAI(model_name="gemini-2.0-flash")
    
    print("Starting Toolbox client initialization...")
    try:
        client = ToolboxClient("https://toolbox-316231368980.us-central1.run.app")
        print("Toolbox client initialized successfully")
        
        print("Attempting to load toolset...")
        tools = client.load_toolset()
        print(f"Tools loaded successfully: {tools}")
        
    except Exception as e:
        print(f"Error with Toolbox: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

    # Initialize memory store if needed
    if thread_id not in memory_store:
        memory_store[thread_id] = {
            "messages": [
                {"role": "system", "content": prompt}
            ],
            "context": {
                "current_user_id": None,
                "current_recipe": None,
                "current_store_id": None,
                "last_action": None
            }
        }

    # Extract recipe name from various contexts
    recipe_keywords = ["add", "ingredients", "recipe for", "show ingredients"]
    if any(keyword in user_input.lower() for keyword in recipe_keywords):
        # Try to find recipe name in the input
        for recipe in ["Black Bean Sweet Potato Hash", "Matcha Green Tea Oatmeal", 
                      "Bacon and Egg Breakfast Burrito", "Nutella French Toast", 
                      "Mediterranean Breakfast Plate", "Chocolate Mousse", 
                      "Crème brûlée", "Lemon Tart", "Tiramisu"]:
            if recipe.lower() in user_input.lower():
                memory_store[thread_id]["context"]["current_recipe"] = recipe
                memory_store[thread_id]["context"]["last_action"] = "set_recipe"
                print(f"Updated current recipe to: {recipe}")
                break

    # Extract store ID from the last assistant message if available
    if len(memory_store[thread_id]["messages"]) > 0:
        last_message = memory_store[thread_id]["messages"][-1]
        if last_message["role"] == "assistant":
            store_id = extract_store_id(last_message["content"])
            if store_id:
                memory_store[thread_id]["context"]["current_store_id"] = store_id
                memory_store[thread_id]["context"]["last_action"] = "set_store"
                print(f"Updated store ID to: {store_id}")

    # Add user message to history
    memory_store[thread_id]["messages"].append({"role": "user", "content": user_input})

    # Create and invoke agent
    agent = create_react_agent(model, tools)
    
    try:
        response = agent.invoke(
            {"messages": memory_store[thread_id]["messages"]},
            config={"configurable": {"thread_id": thread_id}}
        )
        
        content = response["messages"][-1].content
        memory_store[thread_id]["messages"].append({"role": "assistant", "content": content})
        
        print(f"Final context state: {memory_store[thread_id]['context']}")
        return content
        
    except Exception as e:
        print(f"Error in agent: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}"