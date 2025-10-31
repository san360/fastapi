# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
System prompts and prompt templates for OpenAI interactions.
Provides context-aware prompts based on user message content.
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime


# Base system prompts for different scenarios
SYSTEM_PROMPTS: Dict[str, str] = {
    "general": """You are a helpful AI assistant integrated into Microsoft Teams.
Your goal is to provide clear, concise, and accurate answers to users.

Guidelines:
- Be friendly and professional
- Format responses with markdown for better readability
- Use bullet points and numbered lists when appropriate
- Keep responses focused and relevant
- If you're unsure about something, acknowledge it
- Provide examples when helpful

Current context: You're responding in a Teams chat environment.""",

    "technical": """You are a technical expert assistant integrated into Microsoft Teams.
Your goal is to provide detailed technical explanations and solutions.

Guidelines:
- Provide accurate technical information with examples
- Include code snippets with proper markdown formatting (use ```language syntax)
- Explain best practices and potential pitfalls
- Break down complex concepts into understandable parts
- Reference official documentation when relevant
- Consider security, performance, and scalability in your answers

Current context: You're helping with technical/development questions.""",

    "data_analysis": """You are a data analysis expert integrated into Microsoft Teams.
Your goal is to help users understand and analyze data.

Guidelines:
- Provide clear insights from data
- Use statistical concepts when appropriate
- Suggest visualizations that would be helpful (describe them textually)
- Explain trends, patterns, and anomalies
- Make actionable recommendations
- Be precise with numbers and calculations
- Acknowledge limitations in data or analysis

Current context: You're helping with data analysis and interpretation.""",

    "creative": """You are a creative writing and brainstorming assistant integrated into Microsoft Teams.
Your goal is to help users with creative tasks and idea generation.

Guidelines:
- Think creatively and suggest innovative ideas
- Help with brainstorming, content creation, and writing
- Adapt to the user's tone and style preferences
- Provide multiple options or variations when helpful
- Be encouraging and supportive
- Help refine and improve ideas

Current context: You're helping with creative and writing tasks.""",

    "code_helper": """You are a coding assistant expert integrated into Microsoft Teams.
Your goal is to help users write, understand, and debug code.

Guidelines:
- Provide working code examples with clear comments
- Use proper syntax highlighting (```python, ```javascript, etc.)
- Explain what the code does and why
- Include error handling and edge cases
- Suggest best practices and optimizations
- Provide test cases or usage examples
- Help debug issues by asking clarifying questions

Current context: You're helping with coding and programming tasks.""",

    "business": """You are a business and productivity assistant integrated into Microsoft Teams.
Your goal is to help users with business tasks and decision-making.

Guidelines:
- Provide practical, actionable business advice
- Structure information clearly with headings and lists
- Consider multiple perspectives and stakeholders
- Include pros and cons for decisions
- Be professional and objective
- Help with planning, analysis, and communication

Current context: You're helping with business and productivity tasks.""",

    "learning": """You are an educational tutor integrated into Microsoft Teams.
Your goal is to help users learn and understand new concepts.

Guidelines:
- Explain concepts in clear, simple language
- Use analogies and examples to illustrate ideas
- Break down complex topics into digestible parts
- Encourage questions and curiosity
- Provide practice examples when appropriate
- Check understanding by summarizing key points
- Adapt explanation depth based on the question

Current context: You're helping someone learn a new concept.""",

    "summarization": """You are a summarization expert integrated into Microsoft Teams.
Your goal is to help users understand and condense information.

Guidelines:
- Extract key points and main ideas
- Create structured summaries with clear sections
- Prioritize the most important information
- Use bullet points for clarity
- Maintain accuracy to the source material
- Highlight actionable items or decisions
- Keep summaries concise yet comprehensive

Current context: You're helping summarize or condense information.""",
}


# Keyword patterns for detecting prompt categories
PROMPT_KEYWORDS: Dict[str, List[str]] = {
    "technical": [
        "api", "framework", "library", "sdk", "protocol", "architecture",
        "infrastructure", "deployment", "server", "database", "cloud",
        "networking", "security", "authentication", "authorization", "system"
    ],

    "code_helper": [
        "code", "programming", "function", "algorithm", "script", "debug",
        "bug", "error", "exception", "syntax", "compile", "runtime",
        "python", "javascript", "java", "c#", "typescript", "sql",
        "write a function", "write code", "implement", "develop"
    ],

    "data_analysis": [
        "analyze", "data", "statistics", "chart", "graph", "visualization",
        "trend", "pattern", "metric", "dashboard", "report", "insight",
        "calculate", "percentage", "average", "sum", "count", "correlation"
    ],

    "creative": [
        "write", "create", "brainstorm", "idea", "story", "content",
        "creative", "draft", "compose", "imagine", "design", "invent",
        "slogan", "tagline", "narrative", "poem", "article"
    ],

    "business": [
        "business", "strategy", "plan", "proposal", "meeting", "presentation",
        "revenue", "cost", "roi", "stakeholder", "project", "roadmap",
        "decision", "market", "customer", "sales", "marketing", "budget"
    ],

    "learning": [
        "explain", "learn", "understand", "what is", "how does", "teach",
        "tutorial", "guide", "example", "concept", "theory", "principle",
        "why does", "difference between", "compare"
    ],

    "summarization": [
        "summarize", "summary", "tldr", "brief", "overview", "key points",
        "main ideas", "condense", "highlights", "recap", "digest"
    ],
}


# Example prompts that generate longer responses
EXAMPLE_PROMPTS: Dict[str, List[str]] = {
    "long_form_analysis": [
        "Explain the benefits and drawbacks of microservices architecture",
        "Analyze the impact of artificial intelligence on modern business",
        "Provide a comprehensive guide to REST API design best practices",
        "Explain how neural networks work in deep learning",
        "Compare different cloud providers for enterprise applications",
    ],

    "creative_content": [
        "Write a creative story about a robot learning to paint",
        "Brainstorm innovative product ideas for remote work collaboration",
        "Create a compelling narrative about the future of space exploration",
        "Write a detailed marketing proposal for a new SaaS product",
    ],

    "technical_tutorial": [
        "Explain how to implement OAuth 2.0 authentication from scratch",
        "Guide me through building a real-time chat application",
        "Explain Docker containerization and provide practical examples",
        "How do I optimize database queries for better performance",
    ],

    "data_visualization": [
        "Create a visualization showing market trends over the last 5 years",
        "Generate a graph comparing different programming languages' popularity",
        "Show me how to create an interactive dashboard for sales data",
        "Visualize the relationship between variables in this dataset",
    ],

    "code_generation": [
        "Write a Python function to implement a binary search tree",
        "Create a React component for a user authentication form",
        "Implement a rate limiting middleware in Node.js",
        "Write SQL queries to analyze user engagement metrics",
    ],
}


def get_system_prompt(user_message: str) -> str:
    """
    Determine appropriate system prompt based on user message content.

    This function analyzes the user's message and selects the most
    appropriate system prompt to guide the AI's response.

    Args:
        user_message: The user's message/question

    Returns:
        Appropriate system prompt string
    """
    user_message_lower = user_message.lower()

    # Check each category for keyword matches
    category_scores: Dict[str, int] = {}

    for category, keywords in PROMPT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in user_message_lower)
        if score > 0:
            category_scores[category] = score

    # If we have matches, use the highest scoring category
    if category_scores:
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return SYSTEM_PROMPTS[best_category]

    # Default to general prompt
    return SYSTEM_PROMPTS["general"]


def get_prompt_category(user_message: str) -> str:
    """
    Get the category of the user's message for analytics/logging.

    Args:
        user_message: The user's message/question

    Returns:
        Category name (e.g., "technical", "creative", "general")
    """
    user_message_lower = user_message.lower()

    category_scores: Dict[str, int] = {}
    for category, keywords in PROMPT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in user_message_lower)
        if score > 0:
            category_scores[category] = score

    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]

    return "general"


def enhance_system_prompt(
    base_prompt: str,
    user_context: Dict[str, any] = None
) -> str:
    """
    Enhance system prompt with additional context.

    Args:
        base_prompt: Base system prompt
        user_context: Optional context (user name, preferences, etc.)

    Returns:
        Enhanced system prompt
    """
    enhanced = base_prompt

    # Add timestamp context
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    enhanced += f"\n\nCurrent date and time: {current_time}"

    # Add user context if available
    if user_context:
        if "user_name" in user_context:
            enhanced += f"\nUser: {user_context['user_name']}"

        if "preferences" in user_context:
            enhanced += f"\nUser preferences: {user_context['preferences']}"

    return enhanced


def get_thinking_message(category: str) -> str:
    """
    Get an appropriate "thinking" message based on the query category.

    Args:
        category: Query category

    Returns:
        Thinking message string
    """
    thinking_messages = {
        "general": "🤔 Thinking...",
        "technical": "🔧 Analyzing technical details...",
        "code_helper": "💻 Processing your code request...",
        "data_analysis": "📊 Analyzing the data...",
        "creative": "💡 Generating creative ideas...",
        "business": "📈 Analyzing business context...",
        "learning": "📚 Preparing explanation...",
        "summarization": "📝 Summarizing information...",
    }

    return thinking_messages.get(category, thinking_messages["general"])


def get_processing_message(category: str) -> str:
    """
    Get an appropriate "processing" message for longer operations.

    Args:
        category: Query category

    Returns:
        Processing message string
    """
    processing_messages = {
        "general": "💭 Generating response...",
        "technical": "⚙️ Preparing technical response...",
        "code_helper": "🔨 Writing code...",
        "data_analysis": "📉 Creating analysis...",
        "creative": "✨ Crafting creative content...",
        "business": "📊 Formulating recommendations...",
        "learning": "🎓 Creating educational content...",
        "summarization": "📋 Creating summary...",
    }

    return processing_messages.get(category, processing_messages["general"])


def should_use_streaming_ux(user_message: str) -> bool:
    """
    Determine if streaming UX should be used based on expected response length.

    Args:
        user_message: User's message

    Returns:
        True if streaming UX is recommended
    """
    user_message_lower = user_message.lower()

    # Indicators of longer responses
    long_response_indicators = [
        "explain", "describe", "how to", "guide", "tutorial",
        "detailed", "comprehensive", "compare", "analyze",
        "write", "create", "generate", "list", "pros and cons"
    ]

    # If message is asking for detailed information
    has_long_indicator = any(
        indicator in user_message_lower
        for indicator in long_response_indicators
    )

    # If message is longer than 100 characters (detailed question)
    is_detailed_question = len(user_message) > 100

    return has_long_indicator or is_detailed_question


# Export commonly used prompts
__all__ = [
    "SYSTEM_PROMPTS",
    "EXAMPLE_PROMPTS",
    "get_system_prompt",
    "get_prompt_category",
    "enhance_system_prompt",
    "get_thinking_message",
    "get_processing_message",
    "should_use_streaming_ux",
]
