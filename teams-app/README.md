# Teams App Package

This directory contains the Teams app package for FastAPI Auto Sign-In Agent with SSO.

## Files

- `manifest.json` - Teams app configuration
- `color.png` - Bot icon (192x192 px) - **REPLACE WITH PROPER ICON**
- `outline.png` - Bot icon (32x32 px) - **REPLACE WITH PROPER ICON**
- `FastAPIBot.zip` - Packaged app ready for Teams upload

## ⚠️ Icon Placeholders

The current icons are minimal placeholders. **Replace them** with proper icons:

### color.png
- Size: 192x192 pixels
- Format: PNG with transparency
- Content: Full color bot logo/avatar
- Tools: Canva, Figma, or any image editor

### outline.png
- Size: 32x32 pixels
- Format: PNG with transparency
- Content: White icon on transparent background
- Style: Simple outline/silhouette

### Where to create icons:
- https://favicon.io/ (convert emoji/text to icons)
- https://www.canva.com/ (design custom icons)
- Use your company logo (resize appropriately)

## Regenerate Package

After updating icons:

```bash
# Run the generation script again
python create_teams_app.py
```

This will:
1. Keep your updated icons
2. Regenerate manifest.json (in case of config changes)
3. Repackage FastAPIBot.zip

## Upload to Teams

1. Open Microsoft Teams (desktop or web)
2. Click "Apps" in left sidebar
3. Click "Manage your apps" (bottom left)
4. Click "Upload an app"
5. Select "Upload a custom app"
6. Choose `FastAPIBot.zip`
7. Click "Add"

## Configuration

### Bot Details
- Bot App ID: cc451968-4dc2-46f3-9b4f-f8eae2782b25
- Application ID URI: api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25

### Required Azure Setup
See [../IMPLEMENTATION_STEPS.md](../IMPLEMENTATION_STEPS.md) for complete configuration steps.

## Testing

After upload:
1. Search for "FastAPI Bot" in Teams
2. Start a chat
3. Type: `/me`
4. First time: One-click consent
5. Subsequent: Instant profile (no sign-in!)

## Troubleshooting

If SSO doesn't work:
- Check Azure Entra ID Application ID URI is set correctly
- Verify Azure Bot OAuth has Token Exchange URL enabled
- See [../IMPLEMENTATION_STEPS.md#part-7-troubleshooting](../IMPLEMENTATION_STEPS.md#part-7-troubleshooting)
