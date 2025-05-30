# Tenant First Aid

A chatbot that provides legal advice related to housing and eviction

Live at https://tenantfirstaid.com/

## Local Development

1. copy `backend/.env.example` to a new file named `.env` in the same directory and populate it with your `OPENAI_API_KEY`. You can set an invalid key, in which case the bot will return error messages. This may still be useful for developing other features.
2. cd backend
3. brew install uv
4. uv sync
5. uv run python -m tenantfirstaid.app
6. (in another terminal) cd ../frontend
7. npm install
8. npm run dev
9. Go to http://localhost:5173
10. Start chatting

## Contributing

We currently have regular project meetups: https://www.meetup.com/codepdx/ . Also check out https://www.codepdx.org/ to find our Discord server.

## Remote server setup
On DO, we:
1. added our ssh public keys
2. install nginx
3. Kent got the tls cert (just ask chatgpt?)

## Additional features

go to the routes `/feedback` and `/prompt` for extra features. You will need to provide the password defined in your `.env` file.
