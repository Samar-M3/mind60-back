# MindSathi Backend

This is the FastAPI backend for the MindSathi mental health community platform.

## Features

- Firebase Authentication integration
- Firestore database for posts, reactions, and comments
- Role-based access control (user, doctor, therapist, psychiatrist)
- Community feed with posts and reactions
- Professional comment system (restricted to doctors, therapists, psychiatrists)

## Setup

### Prerequisites

- Python 3.10+
- Firebase project created
- Service account key from Firebase Console

### Installation

1. Create a Python virtual environment:
```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase credentials:
   - Download your Firebase project's service account key from Firebase Console
   - Save it as `firebase-key.json` in the backend directory
   - Add to `.env` file:
   ```
   FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-key.json
   ```

### Running the Server

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

### Posts
- `POST /api/posts` - Create a new post
- `GET /api/posts` - Get all posts (paginated)
- `GET /api/posts/{post_id}` - Get a specific post

### Reactions
- `POST /api/posts/{post_id}/react` - Add/update reaction
- `DELETE /api/posts/{post_id}/react` - Remove reaction
- `GET /api/posts/{post_id}/reactions` - Get all reactions

### Comments
- `POST /api/posts/{post_id}/comment` - Add comment (professionals only)
- `GET /api/posts/{post_id}/comments` - Get all comments
- `DELETE /api/posts/{post_id}/comments/{comment_id}` - Delete own comment

## Firestore Schema

### Collections

**users**
```
{
  email: string,
  role: "user" | "doctor" | "therapist" | "psychiatrist",
  createdAt: timestamp
}
```

**posts**
```
{
  id: string,
  content: string,
  userId: string,
  userRole: string,
  createdAt: string,
  reactionCounts: {
    support: number,
    relate: number,
    care: number
  },
  commentCount: number
}
```

**reactions**
```
{
  id: string,
  postId: string,
  userId: string,
  type: "support" | "relate" | "care",
  createdAt: string
}
```

**comments**
```
{
  id: string,
  postId: string,
  content: string,
  authorId: string,
  authorRole: string,
  createdAt: string
}
```

## Environment Variables

See `.env.example` in the root directory for required environment variables.

## Security

- All endpoints require Firebase ID token authentication
- Role-based access control enforced on backend
- Comments restricted to professionals
- User data validated before database operations
