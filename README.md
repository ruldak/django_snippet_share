# Snippet Share - Backend

This is the backend API for Snippet Share, a platform for sharing code snippets. It is built with Django and Django REST Framework, providing a robust set of endpoints for creating, managing, and retrieving snippets.

This backend is designed to be consumed by a frontend client. The official Vue.js frontend for this project can be found here: **[vue_snippet_share](https://github.com/ruldak/vue_snippet_share)**.

## Core Technologies

- **Python**
- **Django**: The core web framework.
- **Django REST Framework (DRF)**: For building the RESTful API.
- **Simple JWT (JSON Web Token)**: For token-based authentication.
- **MySQL**: The primary database for development and production.
- **CORS Headers**: To allow cross-origin requests from the frontend.

## Features

- **User Authentication**: Secure user registration and login using JWT.
- **Snippet Management (CRUD)**: Create, Read, Update, and Delete code snippets.
- **Snippet Visibility**: Control who can see your snippets (Public, Private, Unlisted).
- **Snippet Expiration**: Set an optional expiration date for snippets.
- **Syntax Highlighting Support**: Snippets can be tagged with a specific language.
- **Search and Filtering**: Full-text search for snippets and filtering by language or visibility.
- **Pagination**: API responses for lists are paginated for efficiency.
- **Caching**: Implemented to improve performance on frequently accessed endpoints.
- **Access Logging**: Tracks views for each snippet.
- **Analytics**: Provides basic analytics on snippet views.

## API Endpoints

Here is a summary of the available API endpoints.

### Authentication

| Method | Endpoint              | Description                  |
|--------|-----------------------|------------------------------|
| `POST` | `/api/register/`      | Register a new user.         |
| `POST` | `/api/token/`         | Obtain a JWT access token.   |
| `POST` | `/api/token/refresh/` | Refresh an expired token.    |
| `GET`  | `/api/profile/`       | Get the current user's profile. |

### Snippets

| Method | Endpoint                               | Description                                            |
|--------|----------------------------------------|--------------------------------------------------------|
| `GET`  | `/api/snippets/`                       | List all public snippets (for anon) or user's snippets (for auth). |
| `POST` | `/api/snippets/`                       | Create a new snippet. (Auth required)                  |
| `GET`  | `/api/snippets/{id}/`                  | Retrieve a specific snippet.                           |
| `PUT`  | `/api/snippets/{id}/`                  | Update a snippet. (Owner required)                     |
| `PATCH`| `/api/snippets/{id}/`                  | Partially update a snippet. (Owner required)           |
| `DELETE`| `/api/snippets/{id}/`                 | Delete a snippet. (Owner required)                     |
| `GET`  | `/api/search/`                         | Search snippets. Params: `q`, `language`, `visibility`.|
| `GET`  | `/api/snippet/detail/{id}/`            | Get detailed view of a snippet and log access.         |
| `GET`  | `/api/snippets/{id}/analytics/`        | Get analytics for a snippet. (Owner required)          |

## Local Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd snippet_share
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the database:**
    - Make sure you have a MySQL server running.
    - Create a database (e.g., `django_snippet_share`).
    - Update the `DATABASES` settings in `snippet_share/settings.py` with your database credentials (user, password, database name).

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Start the development server:**
    ```bash
    python manage.py runserver
    ```
    The API will be available at `http://127.0.0.1:8000`.
