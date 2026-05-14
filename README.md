# AI Trailer Loading Optimizer
## Intelligent Loose Cargo Loading & Space Optimization Platform

---

# Project Overview

AI Trailer Loading Optimizer is an AI-assisted logistics optimization platform designed to calculate the most efficient and safe way to load loose cargo into transportation trailers.

The system focuses on:

- maximizing trailer space utilization
- reducing empty space
- improving weight distribution
- preventing unstable cargo arrangements
- minimizing repacking operations
- generating practical loading instructions
- visualizing cargo placement in 3D
- validating physical cargo stability using a physics engine

This is NOT a warehouse management system.

This is NOT a transportation route optimizer.

This project focuses ONLY on trailer loading optimization.

---

# Business Context

Many logistics operations still load trailers manually.

In the target scenario:

- products are transported as loose cargo
- products are NOT palletized
- loading decisions are made manually
- operators rely on experience instead of optimization

This causes:

- inefficient space usage
- partially empty trailers
- unstable cargo arrangements
- product damage
- unnecessary repacking
- operational delays
- poor weight balancing
- additional transportation costs

The purpose of this platform is to solve these problems using AI and optimization algorithms.

---

# Main Goal

The system should answer:

> Given a trailer type and a list of products, how should the trailer be loaded in the most optimal way?

The generated solution must:

- fit within physical constraints
- respect product safety rules
- optimize space usage
- optimize weight distribution
- generate realistic loading instructions
- support practical warehouse execution
- simulate realistic physical behavior

---

# Core Features

The MVP should support:

- trailer definition
- product definition
- cargo loading optimization
- collision detection
- stacking validation
- axle load validation
- weight distribution calculation
- cargo orientation rules
- loading sequence generation
- 3D visualization of loading plan
- utilization metrics
- export of loading plans
- physics-based cargo stability validation
- Excel product import
- multiple simulation scenarios

---

# UI / UX Requirements

The interface MUST be:

- modern
- clean
- highly visual
- readable
- engineering-focused
- easy to understand for warehouse operators

The system should feel like:

- logistics planning software
- engineering simulation software
- Digital Twin viewer

NOT like:
- Excel replacement
- ERP form
- basic CRUD dashboard

---

# Main Interface Layout

The application should contain:

## Left Panel
### Product & Cargo List

Table/grid showing:

- product name
- dimensions
- weight
- quantity
- fragility
- compressibility
- stackability
- orientation restrictions
- crush limits
- loading priority

The list must support:

- sorting
- filtering
- grouping
- highlighting problematic products

---

## Center Panel
### Large 3D Trailer Visualization

This is the MAIN UI element.

Requirements:

- realistic 3D trailer model
- interactive camera
- drag/rotate/zoom
- visible cargo placement
- visible empty spaces
- visible stacking layers
- visible loading order
- physics simulation playback
- color-coded product groups
- unstable cargo highlighting

The 3D viewport should look similar to:

- warehouse simulation software
- CAD-style logistics planners
- Digital Twin systems

---

## Right Panel
### Optimization & Simulation Controls

Should contain:

- trailer selector
- optimization settings
- simulation controls
- scenario selection
- statistics
- warnings/errors
- utilization metrics

---

# Mandatory 3D Features

The 3D view MUST support:

- trailer transparency mode
- exploded cargo view
- layer-by-layer loading
- physics replay
- collision highlighting
- unstable stack highlighting
- center of gravity visualization
- axle load visualization
- empty space heatmaps

---

# Excel Import Requirement

The system MUST support Excel import.

Users should be able to upload:

- .xlsx
- .csv

The importer should automatically load:

- dimensions
- weights
- quantities
- fragility
- compressibility
- stackability
- orientation rules

Example Excel columns:

| ProductName | LengthMm | WidthMm | HeightMm | WeightKg | Quantity | Fragile | Compressible | MaxStackWeightKg |
|---|---|---|---|---|---|---|---|---|

---

# Test Data Requirement

The application should automatically generate multiple demo/testing scenarios.

CursorAI should create built-in sample datasets.

Required scenarios:

---

## Scenario 1 — Half Loaded Trailer

Purpose:
- large amount of empty space
- low utilization
- easy loading

Should demonstrate:
- inefficient space usage
- optimization possibilities

---

## Scenario 2 — Fully Optimized Trailer

Purpose:
- realistic optimized arrangement
- balanced cargo
- high utilization

Should demonstrate:
- efficient loading
- stable stacking
- proper weight distribution

---

## Scenario 3 — Overloaded / Compression Scenario

Purpose:
- maximum possible cargo density
- aggressive stacking
- cargo compression

Should demonstrate:

- crushability handling
- compression simulation
- unstable cargo risk
- overloaded conditions
- physics validation failures

The system should visually show:

- compressed products
- unstable stacks
- excessive pressure zones
- dangerous arrangements

---

## Scenario 4 — Fragile Cargo Scenario

Purpose:
- fragile product handling

Should demonstrate:
- crush prevention
- stacking limitations
- safe arrangement logic

---

## Scenario 5 — Mixed Cargo Scenario

Purpose:
- different product types
- mixed dimensions
- mixed fragility/compression behavior

Should demonstrate:
- realistic enterprise loading complexity

---

# Physics Engine Requirement

The platform MUST use:

# PyBullet

as the primary physics simulation engine.

PyBullet should be used for:

- cargo collision validation
- gravity simulation
- stack stability testing
- tipping detection
- compression simulation
- trailer movement simulation
- center of mass analysis
- dynamic cargo stability verification
- friction and sliding validation

The optimizer should not rely only on mathematical placement validation.

Every generated loading plan should optionally be validated inside a real physics simulation environment.

---

# Physics Simulation Goals

The physics engine should validate:

## Static Stability

- cargo is not floating
- cargo is properly supported
- stacks remain stable
- products do not intersect

## Dynamic Stability

Simulate trailer movement:

- braking
- acceleration
- cornering
- vibration
- uneven force distribution

The system should detect:

- cargo collapse
- sliding
- tipping
- unstable stacks
- excessive pressure zones

---

# Physics Model Requirements

Each cargo object should contain physics parameters:

```json
{
  "massKg": 12,
  "friction": 0.65,
  "restitution": 0.1,
  "centerOfMass": {
    "x": 0,
    "y": 0,
    "z": 0
  },
  "compressible": true,
  "maxCompressionForceKg": 80
}
```

---

# Trailer Model

Each trailer must contain:

- physical dimensions
- weight limits
- axle limits
- stack height limitations
- loading constraints

Example:

```json
{
  "trailerId": "TRAILER_001",
  "name": "Standard Semi Trailer",
  "lengthMm": 13600,
  "widthMm": 2450,
  "heightMm": 2700,
  "maxWeightKg": 24000,
  "maxStackHeightMm": 2700,
  "axleLoadLimits": {
    "frontKg": 8000,
    "rearKg": 18000
  }
}
```

---

# Product Model

Each product should contain:

- dimensions
- weight
- quantity
- stacking rules
- fragility information
- compression rules
- orientation limitations
- physics parameters

Example:

```json
{
  "productId": "KC-001",
  "name": "Paper Towels Box",
  "lengthMm": 500,
  "widthMm": 400,
  "heightMm": 300,
  "weightKg": 12,
  "quantity": 100,
  "fragile": false,
  "compressible": true,
  "maxStackWeightKg": 60,
  "canRotate": true,
  "allowedOrientations": [
    "UPRIGHT",
    "SIDE"
  ],
  "stackingGroup": "PAPER_PRODUCTS",
  "physics": {
    "friction": 0.65,
    "restitution": 0.1
  }
}
```

---

# Recommended Frontend Stack

## Frontend

- React
- TypeScript
- Tailwind CSS
- React Three Fiber
- Three.js

---

# Recommended Backend Stack

## Backend

- Python
- FastAPI

## Optimization Libraries

Potential libraries:

- OR-Tools
- NumPy
- SciPy
- PyBullet
- PyTorch (future AI optimization)

---

# Suggested Architecture

```text
/frontend
  /components
  /pages
  /three
  /types
  /services

/backend
  /api
  /models
  /optimizer
  /constraints
  /validators
  /physics
  /services
  /tests
```

---

# MVP Requirements

The first working version MUST support:

- one trailer
- manual product input
- Excel import
- simple optimization algorithm
- valid placement calculation
- PyBullet physics validation
- large interactive 3D view
- utilization statistics
- JSON export
- multiple test scenarios

---

# Important Engineering Principles

## Physics Is Mandatory

Every valid loading plan must pass:

- mathematical validation
- geometric validation
- physics simulation validation

The project should not generate unrealistic static loading layouts.

---

# CursorAI Development Instructions

Build the project as a focused engineering MVP.

Priority order:

1. Correct optimization logic
2. Physics validation with PyBullet
3. Large readable 3D interface
4. Constraint validation
5. Excel import
6. Working simulation scenarios
7. Clean architecture
8. Usable UI

Avoid overengineering.

The goal of version 1 is to prove that the optimizer can generate physically stable and operationally realistic loading plans.
