# Fixed Wiki snapshot and current execution evidence

Start with `seisflow.py knowledge stage --stage <stage>` and the matching `bindings/<stage>.md`. The exported Wiki index is [library/wiki/index.md](library/wiki/index.md). Any local file-capable agent can read this bundle without the LLM Wiki desktop application or its model-provider configuration.

- `library/`: 32 existing knowledge pages, eight immutable PDF/text sources, relative cross-links, source hashes and export identity.
- `stage-routes.json`: explicit stage reading routes, scope notes and current implementation references.
- `bindings/`: current-version distinctions for each of the six workflow stages.
- `runtime-sources/`: page-numbered text for the already bundled HYPOINVERSE1.40 manual.
- `knowledge-manifest.json`: hashes of this knowledge and its execution evidence, bound to the exact toolchain.

The original papers and historical manuals explain methods and their documented cases. Specific runtime fields, defaults and units require the corresponding pinned implementation/manual. Project defaults and decisions remain identified as project policy; case values do not become universal recommendations.

The driver pins knowledge identity and stage context in each new run. Explicit read/source/cite commands can record the actual returned material and parameter explanation. Automatically provided pages are not a claim of agent reading or scientific fact validation.

Keep the live authoring Wiki separately. Export a new snapshot/release after maintained changes; never modify a release Wiki underneath an active run. Details: [integration and upgrade guide](../docs/WIKI_INTEGRATION.md).
