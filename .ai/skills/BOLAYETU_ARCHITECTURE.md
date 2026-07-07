# BOLAYETU_ARCHITECTURE.md

Follow these principles.

Architecture Style:

* Domain Driven Design
* Clean Architecture
* Feature Based Modules
* SOLID
* Service Layer Pattern
* Selector Pattern
* Repository Pattern

Avoid:

* Fat Views
* Business Logic inside React Components
* Business Logic inside DRF ViewSets
* Massive utility files
* God Components

Backend Structure:

apps/

accounts/
organizations/
clubs/
players/
competitions/
matches/
transfers/
rankings/
news/
notifications/
subscriptions/
affiliations/
analytics/

Each app must contain:

models/
services/
selectors/
serializers/
permissions/
views/
urls/

Frontend Structure:

modules/

organizations/
clubs/
players/
fans/
competitions/
transfers/
news/
subscriptions/

Each module must contain:

components/
pages/
services/
hooks/
types/
schemas/
constants/
