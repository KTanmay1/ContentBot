# Mistral AI Setup Guide

## Getting Your Mistral API Key

### Step 1: Create an Account
1. Visit [La Plateforme](https://console.mistral.ai/)
2. Click "Sign Up" to create a new account
3. Verify your email address

### Step 2: Generate API Key
1. Log in to your Mistral AI console
2. Navigate to "API Keys" in the left sidebar
3. Click "Create new key"
4. Give your key a descriptive name (e.g., "ContentBot Integration")
5. Copy the generated API key (it will only be shown once)

### Step 3: Configure ContentBot
1. Open your `.env` file in the ContentBot directory
2. Add your Mistral API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```
3. Save the file

### Step 4: Test the Integration
1. Start the ContentBot application
2. Select "Mistral" from the AI Provider dropdown
3. Try generating content to verify the integration works

## Available Mistral Models

The ContentBot supports these Mistral models:
- `mistral-tiny` - Fast and efficient for simple tasks
- `mistral-small` - Balanced performance and quality
- `mistral-medium` - High quality for complex tasks
- `mistral-large` - Best quality for demanding applications

## Pricing Information

Mistral AI offers competitive pricing:
- Pay-per-use model
- Free tier available for testing
- Check [Mistral Pricing](https://mistral.ai/pricing/) for current rates

## Troubleshooting

### Common Issues

**"Mistral AI not available" error:**
- Ensure your API key is correctly set in the `.env` file
- Verify your account has sufficient credits
- Check your internet connection

**Import errors:**
- Make sure the `mistralai` package is installed: `pip install mistralai`
- Restart the application after installing dependencies

**Rate limiting:**
- Mistral AI has rate limits based on your subscription tier
- Consider upgrading your plan if you hit limits frequently

## Support

For additional help:
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Mistral AI Community](https://discord.gg/mistralai)
- ContentBot GitHub Issues