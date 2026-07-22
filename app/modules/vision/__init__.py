"""
app/modules/vision/__init__.py

Vision Intelligence Module — Module 1 of ABHEDYA.

Responsibilities:
  - Receive an image/frame
  - Detect safety-related objects (helmet, vest, fire, smoke, person, etc.)
  - Convert raw detections into domain objects
  - Calculate a risk score
  - Persist results
  - Publish an event for downstream modules
  - Return a structured API response

Layered architecture (inner → outer):
  domain          Pure business language. Zero framework dependencies.
  application     Use-cases that orchestrate domain + infrastructure.
  infrastructure  YOLO detector, Postgres repo, Kafka publisher, mapper.
  api             FastAPI routes.
  schemas         Pydantic request/response contracts.
"""
