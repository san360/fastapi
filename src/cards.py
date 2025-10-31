from microsoft_agents.hosting.core import CardFactory
from typing import Optional
from .openai_service import TokenUsage

def create_profile_card(profile):
    """
    Create an adaptive card for displaying user profile information.
    """
    return CardFactory.adaptive_card(
        {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": (
                                [
                                    {
                                        "type": "Image",
                                        "altText": "",
                                        "url": profile.get("imageUri", ""),
                                        "style": "Person",
                                        "size": "Small",
                                    }
                                ]
                                if profile.get("imageUri")
                                else []
                            ),
                        },
                        {
                            "type": "Column",
                            "width": "auto",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "weight": "Bolder",
                                    "text": profile.get("displayName", ""),
                                },
                                {
                                    "type": "Container",
                                    "spacing": "Small",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": profile.get("jobTitle", ""),
                                            "spacing": "Small",
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": profile.get("mail", ""),
                                            "spacing": "None",
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": profile.get("givenName", ""),
                                            "spacing": "None",
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": profile.get("surname", ""),
                                            "spacing": "None",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                }
            ],
        }
    )


def create_pr_card(pr):
    """
    Create an adaptive card for displaying pull request information.
    """
    return CardFactory.adaptive_card(
        {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.0",
            "body": [
                {
                    "type": "TextBlock",
                    "text": pr.title or "No Title",
                    "weight": "Bolder",
                    "size": "Medium",
                },
                {"type": "TextBlock", "text": f"PR ID: {pr.id}"},
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Pull Request",
                    "url": pr.url or "#",
                }
            ] if pr.url else [],
        }
    )


def create_openai_response_card(
    response: str,
    category: str = "general",
    token_usage: Optional[TokenUsage] = None
):
    """
    Create an adaptive card for displaying OpenAI responses with formatting.

    Args:
        response: The AI response text
        category: Category of the query (e.g., "technical", "creative")
        token_usage: Optional token usage statistics

    Returns:
        Adaptive card attachment
    """
    # Category icons and colors
    category_config = {
        "general": {"icon": "🤖", "color": "Accent"},
        "technical": {"icon": "🔧", "color": "Good"},
        "code_helper": {"icon": "💻", "color": "Attention"},
        "data_analysis": {"icon": "📊", "color": "Good"},
        "creative": {"icon": "🎨", "color": "Accent"},
        "business": {"icon": "📈", "color": "Good"},
        "learning": {"icon": "📚", "color": "Accent"},
        "summarization": {"icon": "📝", "color": "Good"},
    }

    config = category_config.get(category, category_config["general"])

    # Build card body
    card_body = [
        {
            "type": "TextBlock",
            "text": f"{config['icon']} AI Response",
            "weight": "Bolder",
            "size": "Medium",
            "color": config["color"],
        },
        {
            "type": "TextBlock",
            "text": response,
            "wrap": True,
            "spacing": "Medium",
        },
    ]

    # Add token usage footer if available
    if token_usage:
        card_body.append({
            "type": "TextBlock",
            "text": (
                f"_Tokens: {token_usage.total_tokens} "
                f"(~${token_usage.estimated_cost:.4f})_"
            ),
            "size": "Small",
            "isSubtle": True,
            "spacing": "Medium",
        })

    return CardFactory.adaptive_card(
        {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": card_body,
        }
    )
