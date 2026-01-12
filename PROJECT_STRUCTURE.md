# HR Management System - Project Structure

This document provides a detailed overview of the project's file structure and the purpose of each file and folder. It serves as a guide for developers to understand the codebase organization.

## Root Directory

- **`alembic.ini`**: Configuration file for Alembic (database migration tool). Points to the migration script location and database connection string.
- **`docker-compose.yml`**: Docker configuration for running the application and its dependencies (e.g., PostgreSQL) in containers.
- **`pyproject.toml`**: Project metadata and dependency management configuration (using `uv` or standard Python tools).
- **`uv.lock`**: Lock file for `uv` package manager, ensuring reproducible builds.
- **`.env`**: Environment variables file (secrets, database URL, debug settings). **Do not commit this to version control.**
- **`.gitignore`**: Specifies files and directories that Git should ignore (e.g., `__pycache__`, `.env`, `.venv`).

## `/alembic`
Contains database migration scripts.

- **`env.py`**: Python script that runs when Alembic starts. It configures the database connection and model metadata for migrations.
- **`script.py.mako`**: Template for generating new migration scripts.
- **`/versions`**: Directory where individual migration files are stored.
    - **`..._initial_tables_...`**: Migration script for initial database schema (Users, Companies, Roles).
    - **`..._extended_company_...`**: Migration for adding company profile fields and Clients table.

## `/app`
The main application source code.

- **`main.py`**: The entry point of the FastAPI application. Initializes the `FastAPI` app, includes routers, and sets up middleware.

### `/app/api`
Contains API route definitions.

- **`v1/router.py`**: Central router that aggregates all endpoints (auth, users, companies, etc.) into the main API router.
- **`v1/endpoints/`**:
    - **`auth.py`**: Authentication endpoints (login, refresh token).
    - **`users.py`**: User management endpoints (create, list, update users).
    - **`companies.py`**: Company management endpoints (create, update profile, upload logo/banner).
    - **`clients.py`**: Client management endpoints (add, list clients for a company).

### `/app/core`
Core application configuration and security logic.

- **`config.py`**: Pydantic settings class that loads and validates environment variables.
- **`security.py`**: Functions for hashing passwords (bcrypt) and generating JWT tokens.
- **`dependencies.py`**: FastAPI dependencies for dependency injection (e.g., `get_current_user`, `get_db`, `get_current_active_superuser`).

### `/app/database`
Database connection and session management.

- **`base.py`**: Imports all models so Alembic can detect them.
- **`session.py`**: Configures the SQLAlchemy engine and `SessionLocal` class. Contains `get_db` dependency for yielding database sessions.

### `/app/models`
SQLAlchemy database models (ORM definitions).

- **`user.py`**: `User` model (email, password hash, role_id, company_id).
- **`company.py`**: `Company` model (tenant details, branding URLs, address).
- **`role.py`**: `Role` model (permissions).
- **`client.py`**: `Client` model (clients associated with a company).

### `/app/schemas`
Pydantic schemas for data validation and serialization (Request/Response models).

- **`auth.py`**: Schemas for login tokens (`Token`, `TokenPayload`) and password reset.
- **`user.py`**: `UserCreate`, `UserUpdate`, `UserResponse`.
- **`company.py`**: `CompanyCreate`, `CompanyUpdate` (includes branding fields), `CompanyResponse`, `CompanyProfileStatus`.
- **`client.py`**: `ClientCreate`, `ClientUpdate`, `ClientResponse`.
- **`role.py`**: `RoleBase`, `RoleCreate`.

### `/app/services`
Business logic layer. Keeps database logic separate from API routes.

- **`auth_service.py`**: Logic for user authentication and user creation (superuser vs regular user).
- **`company_service.py`**: Logic for creating companies, handling subdomains, and checking profile completeness.
- **`user_service.py`**: Logic for user management (CRUD operations).
- **`client_service.py`**: Logic for client management.

### `/app/utils`
Utility functions.

- **`files.py`**: Helper functions for handling file uploads (saving images, validating types/sizes).

## `/scripts`
Helper scripts for administration and testing.

- **`create_superadmin.py`**: Script to programmatically create the creation of the initial Super Admin user.
- **`verify_features.py`**: Script to verify implemented features (likely for testing/demo purposes).

## `/static`
Directory for serving static files.

- **`/uploads`**: Stores user-uploaded files (company logos, banners, etc.).
    - **`/companies/{uuid}`**: specific folder for each company's files.
