# ADR-004: Centralized Design System Governance and Obsidian Slate Tokens

## Status
Accepted

## Date
2026-10-11

## Context
Inconsistent UI styling, hardcoded hex values, disparate component padding, and uncoordinated visual themes across widgets create a fragmented developer experience and lead to visual regressions. PRUBETH Engineering Framework Pillar 4 dictates establishing centralized design system tokens before constructing dozens of screens.

## Decision
We implemented a single source of truth for visual tokens and pre-compiled Qt stylesheets in `ui/design_system.py`:
1. **Design Tokens (`DesignTokens`)**:
   - Frozen dataclass defining the dark "Obsidian Slate" palette (`#0B0D13` canvas, `#141824` surface, `#161722` elevated, `#00F0FF` cyan accent, `#00FF88` success green, `#FFCC00` amber warning, `#FF4466` danger red).
   - Standardized typography scales (`FONT_FAMILY_UI`, `FONT_FAMILY_MONO`, font sizes XS to XL) and corner radius standards (4px, 6px, 8px).
2. **Component Styles (`ComponentStyles`)**:
   - Standardized factory methods for Qt buttons (`primary_button`, `secondary_button`, `danger_button`), text inputs (`input_field`), headers (`card_header`), badges (`status_badge`), and panels (`card_panel`).
3. **Core Rule Enforcement**:
   - All newly constructed widgets (`MissionControlWidget`, `ArtifactViewerWidget`, `ComposerWidget`, `OpenVSXWidget`) must import and consume `DesignTokens` and `ComponentStyles` rather than declaring custom styles.

## Consequences
- **Positive**: Cohesive visual identity, rapid component iteration, guaranteed visual accessibility contrast ratios, and streamlined theme updates.
- **Negative**: Developers must adhere strictly to token references rather than ad-hoc styling.
