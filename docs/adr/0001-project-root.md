# ADR 0001: Dedicated Catfish project root

Status: accepted from explicit project bootstrap instruction

## Context

The original workspace contained both a game prototype and the experimental Lab that grew around
it. Root discovery consequently depended on the game's `PROJECT_CATFISH.md`, even though the Lab
was becoming a standalone tool.

## Decision

An initialized project is identified by `.lab/config.yaml`. `lab init` always initializes the
caller's current directory, so an installed Catfish Lab can attach to a repository in any language.
The public Catfish Lab repository contains only the standalone Lab. Unrelated prototype history is
kept outside Git rather than shipped to every clone.

## Consequences

Commands may run from any descendant of an initialized repository. A user who invokes another Lab
command before initialization receives one actionable message. Earlier product assumptions cannot
silently consume context or define the active project root.
