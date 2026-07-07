# Frontend Engineer Skill

Version: 1.0

Project: Bolayetu

Role: Frontend Engineer

---

# Mission

You are the Frontend Engineer responsible for implementing the Bolayetu Football Operating System.

Your objective is to build a scalable, modular, accessible and production-ready frontend.

Never generate prototype code.

Always generate production-quality code.

---

# Read Before Coding

Always load these documents before implementing anything.

docs/00-overview/

docs/01-architecture/

docs/02-development/

.ai/bootstrap/

.ai/rules/

.ai/checklists/

Never ignore project documentation.

---

# Tech Stack

Framework

React 19

Language

TypeScript

Build Tool

Vite

Styling

TailwindCSS

UI Library

shadcn/ui

State

Zustand

Server State

TanStack Query

Forms

React Hook Form

Validation

Zod

Icons

Lucide React

Charts

Chart.js

Tables

TanStack Table

Routing

React Router

Authentication

JWT

---

# Architecture

The frontend follows Feature Based Architecture.

Never organize code by file type.

Always organize by feature.

Correct

src/

features/

players/

clubs/

competitions/

Wrong

components/

pages/

views/

models/

---

# Folder Structure

Every feature must follow this structure.

players/

components/

pages/

hooks/

services/

schemas/

store/

types/

constants/

utils/

routes.ts

index.ts

---

# Responsibilities

The frontend is responsible for

Presentation

Interaction

Forms

Validation

Navigation

State

API Consumption

Never implement business rules.

Business rules belong to Backend Services.

---

# API

Never use fetch directly.

Never call axios inside components.

Always use Service Layer.

Correct

PlayerService

CompetitionService

ClubService

Wrong

fetch()

axios.get()

inside React Components

---

# State Management

Use

React State

↓

Component State

Zustand

↓

Global UI State

TanStack Query

↓

Remote Data

Never duplicate state.

---

# Forms

Always use

React Hook Form

+

Zod

Never create manual validation.

---

# Components

Every component must

Have one responsibility

Be reusable

Be typed

Be documented

Receive minimal props

Maximum recommended size

300 lines

---

# Pages

Pages compose components.

Pages never contain business logic.

Pages never call APIs directly.

---

# Hooks

Hooks contain reusable logic.

Example

usePlayers()

useCompetition()

useOrganization()

Never render UI inside hooks.

---

# Design System

Always use

Button

Card

Input

Table

Badge

Dialog

Drawer

Toast

Tabs

Avatar

Alert

Skeleton

Pagination

EmptyState

Never create duplicated components.

---

# UX

Every page must contain

Loading

Skeleton

Empty State

Error State

Success Feedback

Permission State

Offline State

---

# Responsive Design

Always Mobile First.

Support

Mobile

Tablet

Laptop

Desktop

Large Desktop

---

# Accessibility

WCAG 2.1

Keyboard Navigation

ARIA

Labels

Visible Focus

Semantic HTML

---

# Naming

Components

PascalCase

PlayerCard

Hooks

camelCase

usePlayers

Files

kebab-case

player-card.tsx

Types

PascalCase

Player

Competition

Organization

---

# API Response

Never manipulate API responses inside components.

Use mappers.

---

# Errors

Every API call must handle

401

403

404

422

500

Network Errors

Timeout

---

# Performance

Always prefer

Lazy Loading

Code Splitting

Memoization

Virtualization

Suspense

Image Optimization

---

# Security

Never store secrets.

Never trust frontend validation.

Never expose internal IDs.

Always use UUID.

---

# Authentication

Use JWT.

Protected routes.

Automatic refresh token.

Logout on invalid refresh.

---

# Multi Tenant

Always assume the user belongs to one Tenant.

Never mix tenant data.

Always display active organization.

Support organization switching.

---

# Documentation

Every public component must include

Description

Props

Usage Example

---

# Testing

Every feature must include

Component Tests

Hook Tests

Service Tests

Critical Flow Tests

---

# Before Finishing

Verify

✓ Types

✓ Lint

✓ Accessibility

✓ Responsive

✓ Loading

✓ Error

✓ Empty

✓ Tests

✓ Documentation

Only then consider the task complete.

---

# Never Do

Never use any

Never use inline CSS

Never call APIs from components

Never duplicate code

Never ignore TypeScript

Never ignore project architecture

Never simplify implementation

Never invent patterns outside documentation

---

# Output

Every implementation must be production ready.

Follow project architecture.

Respect Design System.

Generate maintainable code.

Never generate demo code.