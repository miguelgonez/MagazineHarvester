from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain import LLMChain
from langchain.schema import AgentAction, AgentFinish
from typing import List, Union
import re

class JournalScraperAgent:
    def __init__(self, scraper):
        self.scraper = scraper
        
        # Define tools
        self.tools = [
            Tool(
                name="get_volumes",
                func=self.scraper.get_available_volumes,
                description="Get list of available journal volumes"
            ),
            Tool(
                name="get_issues",
                func=self.scraper.get_volume_issues,
                description="Get list of issues for a specific volume"
            ),
            Tool(
                name="get_pdf",
                func=self.scraper.get_pdf_url,
                description="Get PDF URL for a specific volume and issue"
            )
        ]

    def parse_output(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        """Parse LLM output into agent action or finish"""
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        
        if not match:
            return AgentFinish(
                return_values={"output": "Could not parse LLM output"},
                log=llm_output,
            )
            
        action = match.group(1).strip()
        action_input = match.group(2).strip()
        
        return AgentAction(tool=action, tool_input=action_input, log=llm_output)

    def get_next_action(self, intermediate_steps: List[tuple]) -> Union[AgentAction, AgentFinish]:
        """Determine next action based on previous steps"""
        if not intermediate_steps:
            return AgentAction(tool="get_volumes", tool_input="", log="Initial volume fetch")
        
        last_action, last_output = intermediate_steps[-1]
        
        if last_action.tool == "get_volumes":
            if isinstance(last_output, list) and last_output:
                return AgentAction(
                    tool="get_issues",
                    tool_input=str(last_output[0]),
                    log=f"Fetching issues for volume {last_output[0]}"
                )
        
        elif last_action.tool == "get_issues":
            if isinstance(last_output, list) and last_output:
                volume = int(last_action.tool_input)
                return AgentAction(
                    tool="get_pdf",
                    tool_input=f"{volume},{last_output[0]}",
                    log=f"Fetching PDF for volume {volume}, issue {last_output[0]}"
                )
        
        return AgentFinish(
            return_values={"output": "Completed current sequence"},
            log="No more actions needed"
        )
