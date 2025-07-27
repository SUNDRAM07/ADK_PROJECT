from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.mandi_expert.agent import mandi_expert
from .sub_agents.weather_expert.agent import weather_expert
from .sub_agents.soil_expert.agent import soil_expert
from .sub_agents.general_trends_expert.agent import general_trends_expert
# from datetime import datetime 
# from zoneinfo import ZoneInfo


# def current_time()->dict:
#     "get the current date and time in the format of YYYY-MM-DD HH:MM:SS"
#     return{
#         "current_time":datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S"),
#     }

root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash-001",
    description="Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.
    you are also resposible for beautifully asking the user's name and greeting them by name

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - mandi_expert: for mandi prices
    - weather_expert: for weather only if asked about temperatures today and tomorrow and forecast dont answer questions that are based on general trends let them be handled by general_trends_expert.
                        also use this when the person is asking for current weather or weather 4 days from now and anything like that then use this...
    - soil_expert: this would be used whenever the user wants a recommendation of what kind of crop to plant now or analyse on what kind of options the guy the guy has ..
    - general_trends_expert: for anything that requires a google search for eg what kind of trends does weather follow in gurgaon haryana
    what kinds of crops are grown in january in hissar and what is the temperature in jalandhar in november .. these are something that might take a google search 
    """,
    sub_agents=[mandi_expert,soil_expert,weather_expert],
    tools=[
        AgentTool(
            general_trends_expert
        ),
    ],
)
