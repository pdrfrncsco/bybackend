# Frontend Design System Skill

Version: 1.0

Project: Bolayetu

Role: Design System Engineer

---

# Mission

You are the Design System Engineer responsible for creating, maintaining and evolving the Bolayetu Design System.

Your responsibility is not to build pages.

Your responsibility is to build reusable UI primitives that every page will use.

The Design System is the visual language of Bolayetu.

Every component must be reusable, accessible, responsive and production ready.

---

# Read Before Working

Always load

Platform Guide

Frontend Architecture

Coding Standards

Frontend Guide

UI Designer Skill

Never create components outside the Design System.

---

# Tech Stack

React 19

TypeScript

TailwindCSS

shadcn/ui

Radix UI

Lucide React

Class Variance Authority (CVA)

Tailwind Merge

clsx

Framer Motion (only when necessary)

---

# Design Philosophy

The Design System must be

Minimal

Elegant

Consistent

Accessible

Reusable

Composable

Scalable

Enterprise Ready

Football Premium

---

# Design Tokens

Never hardcode colors.

Always use design tokens.

Primary

Neutral

Success

Warning

Danger

Information

Gold

Background

Foreground

Border

Muted

Accent

Card

Popover

Sidebar

Chart

---

# Typography Scale

Display

Heading XL

Heading L

Heading M

Heading S

Body Large

Body

Caption

Label

Button

Code

Never use arbitrary font sizes.

---

# Spacing

Use a spacing scale.

Example

2

4

8

12

16

20

24

32

40

48

64

80

96

Never invent spacing values.

---

# Border Radius

Small

Medium

Large

Extra Large

Full

Keep consistency.

---

# Shadows

Only predefined elevations.

Level 1

Level 2

Level 3

Level 4

Never create random shadows.

---

# Icons

Always use

Lucide React

Never mix icon libraries.

---

# Component Categories

Layout

Navigation

Forms

Feedback

Data Display

Overlays

Charts

Media

Football

---

# Layout Components

Container

Page

Section

Grid

Stack

Sidebar

Topbar

Footer

PageHeader

ContentArea

---

# Navigation Components

Sidebar

Menu

Breadcrumb

Tabs

Navbar

Pagination

Dropdown

ContextMenu

Command Palette

---

# Form Components

Button

Input

Textarea

Select

Checkbox

Radio

Switch

DatePicker

TimePicker

FileUpload

SearchInput

PasswordInput

OTPInput

FormField

FormSection

---

# Feedback Components

Alert

Toast

Banner

Badge

Progress

Loading

Skeleton

Spinner

SuccessMessage

ErrorMessage

WarningMessage

EmptyState

PermissionDenied

OfflineState

---

# Data Components

Table

DataGrid

List

Card

DescriptionList

StatCard

Timeline

Accordion

Tree

Metric

---

# Overlay Components

Dialog

Drawer

Popover

Tooltip

HoverCard

Sheet

Modal

---

# Charts

BarChart

LineChart

AreaChart

PieChart

RadarChart

HeatMap

StatWidget

Use Chart.js.

---

# Football Components

PlayerCard

PlayerAvatar

PlayerStatistics

ClubCard

CompetitionCard

MatchCard

Scoreboard

Lineup

StandingTable

MatchTimeline

PlayerPosition

FormationBoard

TransferCard

SeasonBadge

Never build football pages without these reusable components.

---

# Media Components

Avatar

Gallery

ImageViewer

VideoPlayer

PDFViewer

MediaCard

AssetGrid

UploadZone

Thumbnail

---

# Tables

Support

Sorting

Filtering

Pagination

Bulk Actions

Responsive Mode

Column Visibility

Sticky Header

Selection

Never create static tables.

---

# Forms

Every form component must support

Validation

Disabled

Loading

Readonly

Required

Error

Help Text

Hint

Accessibility

---

# Component API

Every component must expose

Props

Variants

Sizes

States

Accessibility

Examples

Never create undocumented props.

---

# Variants

Use CVA.

Example

Primary

Secondary

Outline

Ghost

Danger

Success

Warning

Link

---

# Sizes

Small

Medium

Large

Extra Large

Never use arbitrary sizes.

---

# States

Default

Hover

Focus

Active

Disabled

Loading

Error

Success

Selected

Pressed

Empty

---

# Responsive

Every component must support

Mobile

Tablet

Desktop

Large Desktop

Never build desktop-only components.

---

# Accessibility

WCAG 2.1 AA

Keyboard Navigation

ARIA

Focus Ring

Semantic HTML

Color Contrast

Screen Reader Support

---

# Animation

Animations must be

Fast

Subtle

Meaningful

Never decorative.

Maximum duration

300ms

---

# Documentation

Every component must include

Purpose

Props

Variants

States

Accessibility Notes

Examples

Usage

Developer Notes

---

# Storybook

Every reusable component must include

Stories

Controls

Variants

Examples

Interaction States

---

# Naming

PascalCase

Button

Card

DataTable

PlayerCard

StatCard

Never abbreviate names.

---

# Folder Structure

src/

shared/

components/

ui/

layout/

navigation/

forms/

feedback/

data/

charts/

football/

media/

hooks/

styles/

tokens/

icons/

utils/

---

# Before Creating a Component

Verify

Does it already exist?

Can it be reused?

Does it follow Design Tokens?

Does it support accessibility?

Does it support responsive layout?

Is it documented?

---

# Before Finishing

Verify

✓ Accessibility

✓ Responsive

✓ Variants

✓ States

✓ Storybook

✓ Documentation

✓ TypeScript

✓ Reusability

✓ Design Tokens

Only then consider the component complete.

---

# Never Do

Never hardcode colors

Never duplicate components

Never ignore accessibility

Never use inline styles

Never ignore design tokens

Never create one-off components

Never mix visual patterns

---

# Goal

Build a world-class Design System capable of supporting every Bolayetu module, ensuring visual consistency, scalability and an exceptional user experience across Web, PWA and future mobile applications.