# Firebase Setup Instructions

## Environment Variables Setup

This application uses environment variables for Firebase configuration instead of a JSON credentials file for security reasons.

### Steps to setup Firebase:

1. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Get your Firebase service account credentials:**
   - Go to the Firebase Console
   - Navigate to Project Settings > Service Accounts
   - Generate a new private key (downloads a JSON file)

3. **Update your `.env` file with the Firebase credentials:**
   ```env
   FIREBASE_TYPE=service_account
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key-content\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
   FIREBASE_CLIENT_ID=your-client-id
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
   FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com
   FIREBASE_UNIVERSE_DOMAIN=googleapis.com
   ```

### Important Notes:

- Never commit the `.env` file to version control
- The `FIREBASE_PRIVATE_KEY` should include the full private key with `\n` characters for line breaks
- Make sure to escape any special characters in environment variables
- For production, use your platform's environment variable management system

### Security Best Practices:

- Always use environment variables for sensitive configuration
- Never commit credentials files to Git repositories
- Use different Firebase projects for development, staging, and production
- Regularly rotate your service account keys
