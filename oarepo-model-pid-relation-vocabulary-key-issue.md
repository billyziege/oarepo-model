# Bug: `pid-relation` key field referencing a vocabulary term is mapped as scalar `keyword` instead of an object

## Summary

When a `pid-relation` field in a `metadata.yaml` schema lists a key whose value in the target model is itself a vocabulary term (stored as `{"id": "...", "title": {...}}`), oarepo-model generates a mapping entry of `{"type": "keyword"}` for that key. At index time, the denormalized document contains the field as an object `{"id": "analysis"}`, which OpenSearch rejects with a `mapper_parsing_exception` because the mapping declares it a scalar keyword.

## Affected version

`oarepo-model` (tested against the version installed in `frozen_testing`, commit/tag unknown at time of writing)

## Steps to reproduce

1. Define a `pid-relation` field that includes a key pointing to a vocabulary-typed field in the target model. For example, in `dataset/metadata.yaml`:

```yaml
provenance_activities:
  type: array
  items:
    type: object
    properties:
      activity:
        type: pid-relation
        keys:
          - id
          - metadata.title
          - metadata.activity_type    # <-- vocabulary field in target model
        record_cls: "research_activity:ResearchActivityRecord"
```

2. In the target model (`ResearchActivity`), `activity_type` is a vocabulary reference. When denormalized, it is stored as:

```json
{
  "activity": {
    "id": "kf8y6-0px74",
    "metadata": {
      "activity_type": { "id": "analysis" },
      "title": "Analysis — Rietveld refinement of GIXRD data"
    },
    "@v": "1177ccd2-97fc-4115-8b5d-422260b40cda::4"
  }
}
```

3. Inspect the oarepo-generated mapping template:

```python
from dataset.model import dataset_model
import json
mapping = json.loads(dataset_model.__dict__['record-mapping']['content'])
activity_type = (mapping['mappings']['properties']['metadata']['properties']
                 ['provenance_activities']['properties']['activity']
                 ['properties']['metadata']['properties']['activity_type'])
print(activity_type)
# {'type': 'keyword', 'ignore_above': 256}
```

4. Create the OpenSearch index using this template and attempt to index a record.

**Result:**
```
opensearchpy.exceptions.RequestError: RequestError(400,
  'mapper_parsing_exception',
  "failed to parse field [metadata.provenance_activities.activity.metadata.activity_type]
   of type [keyword] in document with id '...'.
   Preview of field's value: '{id=analysis}'")
```

## Root cause

When oarepo-model generates the mapping for a `pid-relation`'s `keys` list, it looks up the type of each key in the owning model's schema and emits the corresponding OpenSearch type. For `metadata.activity_type` in the target model (`ResearchActivity`), the field is a vocabulary term. Vocabulary terms are stored at index time as objects: `{"id": "...", "title": {...}}` (or, for the denormalized pid-relation snapshot, the subset of keys present in the `@v` cache).

The mapping generator does not traverse the target model to resolve the actual stored shape of the denormalized key. Instead, it appears to emit `{"type": "keyword"}` as a fallback, treating the field as a scalar. The result is a type mismatch between the mapping and the document.

## Impact

Any `pid-relation` whose `keys` include a field that resolves to a vocabulary term in the target model will produce an incorrect mapping entry. When the oarepo template is applied to create the index, any attempt to index a record containing that pid-relation fails, making the record unreachable via the search API.

Reproducible whenever a denormalized pid-relation includes a vocabulary-typed key.

## Proposed fix

The oarepo-model mapping generator should resolve the target model's schema for each listed key and emit the correct OpenSearch mapping for the stored shape. Specifically, a vocabulary-typed key field (whose stored form is `{"id": "..."}` after denormalization) should be emitted as:

```json
{
  "type": "object",
  "properties": {
    "id": {"type": "keyword", "ignore_above": 256}
  }
}
```

If the vocabulary field also stores `title` in the snapshot, the mapping should include `"title": {"type": "object", "dynamic": "true"}` alongside `id`.

### Workaround (applied in this repository)

Explicitly override the affected field's mapping when creating the OpenSearch index, bypassing the oarepo template for this field:

```python
"activity_type": {
    "type": "object",
    "properties": {
        "id": {"type": "keyword", "ignore_above": 256}
    }
}
```
