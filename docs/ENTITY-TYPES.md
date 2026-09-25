# A typed energy-transition catalogue

GlobalGrid2050 indexes work across the energy transition, with an electrical
focus. Equipment is one kind of entry, not the universal record template.

Keep identity, meaning and presentation separate:

- `data/homepage.json`: permanent entity ID, parent relationships, release IDs,
  operative release, destinations and source references.
- `data/entity-types.json`: entity type, intended purpose and audience, keyed
  by that same permanent entity ID.
- `data/presentation.json`: selected highlights and table page size.
- `data/active-pages.json`: measured repository activity and checked app routes.

An entity's type means what it **is**: engine, application, dataset, equipment,
project, reference, drawing or catalogue. Its subject describes what it covers:
solar, cables, electricity markets, materials and other topics. Audience means
who it is intended to serve. None of these establishes verified capability.
File encoding, such as JSON, CSV, Parquet or SVG, is a separate data-format
property; do not use it instead of an entity type. An entity may have several
roles. `engine` and `design-studio` need not compete for the same field: the
former can be its primary type and the latter one of its intended roles.

## Kuiper

Type: **engine**. Intended audience: **humans and LLMs**. Intended purpose:
isolate and study patterns across large bodies of code, text, mathematics and
related work, supporting faster iteration and discovery with LLM assistance.

This records the creator's intended use. It is not evidence that the current
release provides an LLM API, automatic discovery, a particular corpus size or
a measured acceleration. Demonstrated capabilities belong in release-specific
evidence with a method, inputs, result and limitation.

Kuiper's intended roles can include pattern exploration, design studio, drawing
workspace and proposal authoring. Specialised variants should link to the
parent engine while carrying their own release and capability evidence. GIS
outputs need coordinate-reference and accuracy evidence; construction drawings
need defined scope, revision and appropriate review. A shared code foundation
does not automatically transfer validation from one variant to another.

## Extension and federation

Future publishers should retain their own ownership and publish compatible,
versioned records. An external ID needs an explicit publisher namespace; do
not merge unrelated records merely because their titles match. Relationships
should say `uses`, `derived_from`, `implements`, `supersedes` or another defined
relationship instead of relying on visual proximity.

New types need a versioned schema and migration policy. Type-specific fields
should extend a common identity/provenance record rather than putting thousands
of irrelevant columns into every row. A dataset needs coverage, units and
source dates; a part needs specifications and revision identity; a drawing
needs drawing status and revision; an engine needs input/output contracts and
evidence. Missing values remain unknown, not inferred zero or approval.

Source, licence, author, reviewer, review scope and release must remain
distinct. Attribution does not grant a redistribution licence. Review of a
dataset or block diagram is not sign-off of an electrical installation. Do not
publish confidential source material merely because a derived entry is public.

The current files implement a small app catalogue and searchable type metadata.
They do not yet implement external ingestion, equipment ordering, a universal
schema registry, a million-row API or an automated engineering approval system.
