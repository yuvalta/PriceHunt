# PriceHunt 🛍️

An AI-powered WhatsApp shopping assistant that helps you find better deals on AliExpress. Simply send a product link or search query, and PriceHunt will find cheaper alternatives for you!

## Features

- 🔍 Product search by keywords and price range
- 🔗 Direct product link processing
- 💰 Price comparison with similar products
- 🤖 WhatsApp integration for easy access
- 🔄 Real-time price updates
- 🎯 Affiliate links for monetization

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env`:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run the application:
```bash
# Using Docker
make build
make up

# Or directly
python -m src.main
```

## Usage

### Via WhatsApp

1. Send a direct AliExpress product link to find cheaper alternatives
2. Use the search command: `/search <keywords> <max_price>`
   Example: `/search smartphone 500`

### API Endpoints

- `POST /webhook` - WhatsApp webhook endpoint
- `GET /health` - Health check endpoint

## Development

### Project Structure

```
src/
├── api/        # API routes and endpoints
├── core/       # Core functionality and base classes
├── models/     # Data models
├── services/   # Business logic and external services
├── utils/      # Utility functions
└── config/     # Configuration management
```

### Testing

```bash
# Run tests
make test

# Run linter
make lint
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License - see LICENSE file for details

## Support

For support, please open an issue in the GitHub repository.
