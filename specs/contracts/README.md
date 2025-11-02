# API Contracts

This directory contains API contract specifications for the PyDVR application.

## Contract Files

1. **common.md** - Common schemas, error responses, and shared types
2. **guide.md** - Program guide and search endpoints
3. **recordings.md** - Recording management endpoints (schedule, cancel, list)
4. **series.md** - Series rule management endpoints
5. **library.md** - Recording library endpoints (view, delete completed recordings)
6. **system.md** - System status, configuration, and health endpoints
7. **setup.md** - Initial setup wizard endpoints

## API Design Principles

- **RESTful Design:** Resources identified by URLs, standard HTTP methods
- **JSON Payloads:** All request/response bodies use JSON
- **Error Handling:** Consistent error response format
- **Validation:** Server-side validation with detailed error messages
- **Pagination:** Large lists paginated with limit/offset
- **Timestamps:** All times in ISO 8601 format, UTC

## Base URL

Development: `http://localhost:8000/api`
Production: `http://{server-ip}:{port}/api`

## Authentication

Not implemented for MVP (single-user, local network deployment).
Future consideration for multi-user or remote access.

## Versioning

API version in URL path: `/api/v1/...`
Initial release: v1