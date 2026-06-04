#!/usr/bin/env python3
"""
Simple CLI to parse raw log lines into typed API events using LangChain structured output.
Author: Auto-generated solution for task 6a1d75e5fd30e81cf3126b1a
"""
import argparse
from pathlib import Path
from typing import List, Union

# Pydantic v2 models
from pydantic import BaseModel, Field
from typing_extensions import Annotated

class HttpOkEvent(BaseModel):
    kind: Literal["ok"] = Field(..., description="OK event")
    status: Literal[200] = Field(..., description="HTTP 200 OK")
    path: str = Field(..., description="Request path")
    duration_ms: int = Field(..., description="Duration in ms")

class HttpErrorEvent(BaseModel):
    kind: Literal["error"] = Field(..., description="Error event")
    status: int = Field(..., description="HTTP error status code")
    path: str = Field(..., description="Request path")
    error_message: str = Field(..., description="Error message")

# Union with discriminator
ApiEvent = Annotated[Union[HttpOkEvent, HttpErrorEvent], Field(discriminator="kind")]

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

parser = PydanticOutputParser(pydantic_object=ApiEvent)
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

prompt_template = PromptTemplate(
    input_variables=["log_line"],
    template=(
        "Parse the following log line into a structured API event.\n"
        "The output must be valid JSON matching one of the following schemas:\n"
        f"{parser.get_format_instructions()}\n"
        "Log line: {log_line}\n"
    ),
)

chain = prompt_template | llm | parser

# Sample log lines (mixed 200 and error codes)
SAMPLE_LOG = (
    "GET /api/users 200 OK in 123ms\n"
    "POST /api/orders 404 Not Found: missing resource\n"
    "PUT /api/items/42 500 Internal Server Error: database failure"
)


def parse_line(line: str) -> ApiEvent:
    return chain.invoke({"log_line": line})


def main():
    parser_cli = argparse.ArgumentParser(description="Parse raw log into typed events.")
    parser_cli.add_argument("--text", type=str, help="Raw log text (multiple lines). If omitted, sample log is used.")
    args = parser_cli.parse_args()

    if args.text:
        raw_text = args.text
    else:
        raw_text = SAMPLE_LOG

    # Split into individual events by newline or '---'
    blocks = [b.strip() for b in raw_text.replace("---", "\n").split("\n") if b.strip()]

    events: List[ApiEvent] = []
    for block in blocks:
        try:
            event = parse_line(block)
            events.append(event)
        except Exception as e:
            print(f"Failed to parse line: {block}\nError: {e}")

    # Output each event dump
    for ev in events:
        print(ev.model_dump())

    # Simple table
    header = f"{'kind':<6} | {'path':<20} | {'status':<6}"
    print("\nTable:\n", header)
    print('-' * len(header))
    for ev in events:
        if isinstance(ev, HttpOkEvent):
            print(f"{ev.kind:<6} | {ev.path:<20} | {ev.status:<6}")
        else:
            print(f"{ev.kind:<6} | {ev.path:<20} | {ev.status:<6}")

if __name__ == "__main__":
    main()
