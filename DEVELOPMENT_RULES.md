# Lanhu Design-to-Code Development Rules

Use these rules only when the user intends to implement UI from Lanhu designs.
The target project's existing conventions, framework, components, and tooling
take precedence over this document.

## Required Workflow

Before writing code:

1. Inspect the target project's framework, file structure, styling approach,
   reusable components, and existing data patterns.
2. Separate business UI from phone status bars, home indicators, design-canvas
   backgrounds, rulers, annotations, selection frames, and watermarks.
3. Identify page containers, component boundaries, repeated items, state,
   static interactions, mock data, and shared logic.
4. Record uncertain behavior instead of inventing it.
5. Implement with the target project's native patterns and verify the result.

## Evidence and Semantics

- Canvas coordinates describe geometry, not runtime positioning or business
  meaning.
- Do not infer `fixed`, `sticky`, floating behavior, current-user identity,
  selected state, or recommendation state only from edge placement, cropping,
  color emphasis, or a single numeric value.
- Implement those semantics only when CSS, design annotations, interaction
  notes, or requirements provide evidence.
- Preserve real business navigation, title bars, tabs, and bottom navigation.

## Modules and Files

- Prefer the target project's existing module and naming conventions.
- Create a business module directory only when the project has no relevant
  convention.
- Keep the business entry point responsible for page composition.
- Add `components`, types, data, or hooks files only when they contain real
  responsibilities.
- Do not create wrapper-only components. Component extraction must not add DOM
  wrappers, spacing, positioning contexts, or inheritance changes.
- When page-level tabs are confirmed, keep shared layout and tab state in the
  business entry and give each confirmed tab its own minimal entry. Do not
  invent complete UI for tabs whose designs are unavailable.

## Static Behavior

For each behavior supported by evidence, identify its trigger, initial state,
resulting state, visible feedback, data needs, and unresolved questions.
Consider tabs, buttons, progress indicators, scrolling, horizontal lists,
dialogs, drawers, carousels, inputs, selection, loading, and empty states.

Use local state, view switching, lightweight feedback, mock-data filtering, and
scroll behavior when appropriate. Do not add dependencies solely for a static
design reproduction.

## Repeated Content and Data

- Render lists, grids, tables, repeated cards, tags, menu items, statistics,
  steps, and carousel items from one item component and data when practical.
- Literal one-off copy may remain in the template.
- Put likely API-backed mock data in the current business data module or the
  project's established data location.

## Visual Fidelity

- Use the design-artboard dimensions as the measurement baseline.
- Preserve dimensions, spacing, colors, typography, line height, radius,
  borders, shadows, opacity, gradients, images, and cropping.
- Treat generated HTML/CSS as the primary visual source and design tokens as a
  supplement.
- Distinguish page or module edge spacing from spacing between children. Prefer
  parent padding for shared screen-edge spacing when it does not change the
  container's background, border, radius, clipping, or click-area semantics.
- Follow the target project's established `gap` or margin compatibility style.

## Assets

- Do not replace design images with emoji, CSS drawings, unrelated images, or
  placeholders.
- Follow the tool's active asset behavior and the target project's asset
  conventions.
- Treat migration to another image host as a separate task.

## Pre-Implementation Check

- Target framework and project conventions inspected.
- Non-business canvas and system UI excluded.
- Components, repeated data, state, and file structure identified.
- Runtime behavior is supported by evidence.
- Parent padding and child spacing are correctly distinguished.
- Image handling follows the active Lanhu asset behavior.
- Uncertain requirements are listed for confirmation.
