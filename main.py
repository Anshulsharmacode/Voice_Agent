import asyncio

from llm_service.llm import LLMService


async def main() -> None:
    llm = LLMService(
        model_name="qwen3:0.6b",
        base_url="http://localhost:11434",
        temperature=0.2,
        use_chat=True,
    )

    # Hardcoded questions that should trigger tool use
    questions = [
        # "Search the web for the latest news about NASA Artemis II.",
        # "What's the weather in San Francisco today?",
        "Open this website https://anshulsharma-pr.vercel.app/"

    ]

    for q in questions:
        print(f"\nUSER: {q}")
        answer = await llm.invoke_with_tools(
            q,
            tool_names=None,  # use all available tools
        )
        print(f"ASSISTANT: {answer}")


if __name__ == "__main__":
    asyncio.run(main())
