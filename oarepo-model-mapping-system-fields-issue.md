# Bug: oarepo-generated index mapping uses `dynamic: strict` but omits InvenioRDM system fields, making it incompatible with record indexing

## Summary

The mapping template that oarepo-model generates for a custom record type uses `"dynamic": "strict"` throughout, but it does not include the InvenioRDM system fields (`is_published`, `parent`, `versions`, `has_draft`, `is_deleted`, `deletion_status`, `publication_status`, etc.) that the InvenioRDM record indexer adds to every document. If the oarepo template is applied when creating the OpenSearch index, all subsequent record indexing fails immediately with `strict_dynamic_mapping_exception`. If the template is not applied (index created with dynamic mapping), all string fields — including fields explicitly typed as `keyword` in the template — are instead typed as `text`, causing aggregations and facets on those fields to fail with a 400 error.

## Affected version

`oarepo-model` (tested against the version installed in `frozen_testing`, commit/tag unknown at time of writing)

## Steps to reproduce

1. Define a custom record model using `oarepo-model` that extends InvenioRDM drafts (`drafts_preset`) and includes at least one faceted `keyword` field in its metadata.
2. Create the OpenSearch index using `invenio index create` or by directly applying the mapping from `dataset_model['record-mapping']['content']`.
3. Attempt to index a published record via the service indexer.

**Result A** (template applied with `dynamic: strict`):
```
opensearchpy.exceptions.RequestError: RequestError(400,
  'strict_dynamic_mapping_exception',
  'mapping set to strict, dynamic introduction of [is_published] within [_doc] is not allowed')
```

**Result B** (index created with dynamic mapping fallback): the record indexes without error, but the field types do not match the template. Keyword fields such as `metadata.creators.person_or_org.name` are typed as `text`. Any search request that includes an aggregation on these fields then fails:
```
opensearchpy.exceptions.RequestError: RequestError(400,
  'search_phase_execution_exception',
  'Text fields are not optimised for operations that require per-document field data
   like aggregations and sorting ... [metadata.creators.person_or_org.name]')
```

## Root cause

The oarepo-generated mapping template covers only the fields defined in `metadata.yaml` (and any applied presets). The InvenioRDM record indexer's dump pipeline adds a set of system-level fields at the top of every document that are not part of the schema definition and therefore not included in the template:

| Field | Example value |
|---|---|
| `is_published` | `true` |
| `parent` | `{id, pid, pids, access, communities, ...}` |
| `versions` | `{latest_id, latest_index, is_latest, ...}` |
| `has_draft` | `false` |
| `is_deleted` | `false` |
| `deletion_status` | `"P"` |
| `publication_status` | `"published"` |

Because `"dynamic": "strict"` is set at the root, OpenSearch rejects any document that contains a field not named in the mapping. The template is therefore incompatible with InvenioRDM's own indexer output.

## Impact

The custom model search UI fails with a 400 error on any search request that includes aggregations (facets). This breaks the default InvenioRDM search page for any oarepo-model-defined record type, because oarepo auto-generates `TermsFacet` objects for every `keyword` field in the schema.

Reproducible on any fresh database after `./run.sh reset`.

## Proposed fix

The oarepo-model template generator should either:

**Option A — Set `dynamic: true` at the root level** and rely on `dynamic: strict` only within the `metadata` subtree (where the schema is fully known). The InvenioRDM system fields would then be auto-mapped by OpenSearch while the custom metadata fields retain their explicit types. This is the minimal fix.

**Option B — Add explicit mappings for all InvenioRDM system fields** to the generated template. This produces a fully explicit mapping and avoids dynamic field inference for system fields, at the cost of coupling oarepo-model to the InvenioRDM system field set.

### Workaround (applied in this repository)

When creating the OpenSearch index manually, override `dynamic` at the root level and include explicit mappings only for the fields whose types cannot be inferred correctly by dynamic mapping:

```python
from invenio_search import current_search_client

mapping = {
    "mappings": {
        "dynamic": True,
        "properties": {
            "metadata": {
                "properties": {
                    # explicit keyword types that dynamic mapping would type as text
                    "creators": {
                        "properties": {
                            "person_or_org": {
                                "properties": {
                                    "name":        {"type": "keyword", "ignore_above": 256},
                                    "given_name":  {"type": "keyword", "ignore_above": 256},
                                    "family_name": {"type": "keyword", "ignore_above": 256},
                                    "type":        {"type": "keyword", "ignore_above": 256},
                                }
                            }
                        }
                    },
                    # ... other custom fields requiring explicit types
                }
            }
        }
    }
}
current_search_client.indices.create(index="<prefix>-dataset-metadata-v1.0.0", body=mapping)
```
