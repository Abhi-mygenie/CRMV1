#!/bin/bash
# Ensure .env file exists for backend

ENV_FILE="/app/backend/.env"
ENV_EXAMPLE="/app/backend/.env.example"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Backend .env file missing! Creating from .env.example..."
    
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "✅ Created backend .env from .env.example"
    else
        # Fallback: create with default values
        cat > "$ENV_FILE" << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=loyalty_app
EOF
        echo "✅ Created backend .env with default values"
    fi
else
    echo "✅ Backend .env file exists"
fi

# Verify required variables
if grep -q "MONGO_URL" "$ENV_FILE" && grep -q "DB_NAME" "$ENV_FILE"; then
    echo "✅ All required backend env variables configured"
else
    echo "⚠️  Missing required variables, fixing..."
    grep -q "MONGO_URL" "$ENV_FILE" || echo "MONGO_URL=mongodb://localhost:27017" >> "$ENV_FILE"
    grep -q "DB_NAME" "$ENV_FILE" || echo "DB_NAME=loyalty_app" >> "$ENV_FILE"
fi

exit 0
