# Wiki Schema

## Language and scope

Write all wiki pages, summaries, comparisons, and generated answers in English. Preserve official names, bibliographic information, equations, and units. The collection concerns seismic processing methods and scientific agents.

## Page Types

| Type | Directory | Purpose |
|---|---|---|
| source | wiki/sources/ | One grounded summary per imported document |
| entity | wiki/entities/ | Named methods, programs, and agent systems |
| concept | wiki/concepts/ | Scientific and workflow concepts |
| comparison | wiki/comparisons/ | Explicit comparisons using available evidence |
| synthesis | wiki/synthesis/ | Cross-source conclusions and labelled proposals |
| query | wiki/queries/ | Unresolved research or evidence questions |
| overview | wiki/overview.md | Collection scope and reading routes |

## Naming and frontmatter

Use unique lowercase kebab-case filenames. Source pages use an author-year-topic slug matching the imported PDF basename.

Every knowledge page has YAML frontmatter with `type`, `title`, `tags`, `sources`, `related`, `created`, and `updated`. Source pages additionally have `authors`, `year`, `venue`, and `url`. Use `sources: ["source-filename.pdf"]` to identify real files relative to `raw/sources/`. Do not put summary-page paths in the sources array.

## Grounding and references

- Use `[[page-slug]]` links between knowledge pages and list all pages in `wiki/index.md`.
- Cite physical PDF page numbers starting at 1, not journal page numbers unless explicitly labelled.
- Include a source-document link and a link to page-numbered extraction on each source page.
- Clearly distinguish an author's reported experiment, a manual's guidance, and a cross-paper proposal.
- Never describe published metrics as locally reproduced results unless a recorded reproduction exists.
- Preserve version differences. Original PhaseNet is not PhaseNet+; the local HYPOINVERSE and hypoDD manuals are historical versions.
- Keep missing evidence and contradictions visible in query pages.
- Text extraction may omit figures and distort equations or tables. Verify such details against the original PDF before depending on them.

## Maintenance

Keep raw PDFs immutable. Record any added or replaced source in the corpus manifest with a content hash. Update affected summaries, shared entities/concepts, the overview, the index, and `wiki/log.md` when adding knowledge. Source-watch ingestion should be enabled only after a model provider is configured.

The initial collection was curated externally by Codex. Its exact source-text hashes and generated file lists are registered in `.llm-wiki/ingest-cache.json` using the LLM Wiki 0.6.11 format. This records completed external curation, not calls to the application's model provider.
