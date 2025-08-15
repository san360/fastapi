from microsoft.agents.hosting.core import CardFactory

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
