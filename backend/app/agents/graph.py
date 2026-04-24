from langgraph.graph import StateGraph
from typing import TypedDict

from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.scheduler import Scheduler
from app.agents.llm_enhancer import LLMEnhance
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Define state
class AgentState(TypedDict):
    user_id: int
    analysis: dict
    plan: list
    schedule: list
    
# Initialize agents
analyzer = AnalyzerAgent()
planner = PlannerAgent()
scheduler = Scheduler()
enhancer = LLMEnhance()

# Nodes
def analyze_node(state: AgentState):
    state['analysis'] = analyzer.run(state['user_id'])
    return state

def plan_node(state: AgentState):
    state['plan'] = planner.run(state['analysis'])
    return state

def schedule_node(state: AgentState):
    state['schedule'] = scheduler.generate_weekly_schedule(state["plan"])
    return state

def enhance_node(state: AgentState):
    state['schedule'] = enhancer.enhance(state['schedule'])
    return state
    
#  Build graph
graph = StateGraph(AgentState)

graph.add_node("analyze", analyze_node)
graph.add_node("plan", plan_node)
graph.add_node('enhance', enhance_node)
graph.add_node("schedule", schedule_node)

graph.set_entry_point("analyze")
graph.add_edge("analyze", "plan")
graph.add_edge("plan", "schedule")
graph.add_edge("schedule", "enhance")

app_graph = graph.compile()