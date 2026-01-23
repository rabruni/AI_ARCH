# Verb Prompts Loader Specification

**Part of:** `/init` sequence (Step 4)
**Location:** `/Control_Plane/init/actions_loader_spec.md`

---

## Purpose

Load and register the four verb prompts (install, update, verify, uninstall) that define how to operate on registry items.

---

## The Four Verbs

The Control Plane uses four standard verbs for all operations:

| Verb | Purpose | When Used |
|------|---------|-----------|
| **install** | Create artifact from scratch | New item, status=missing→active |
| **update** | Modify existing artifact | Item exists, needs changes |
| **verify** | Validate artifact is correct | After install/update, or audit |
| **uninstall** | Remove or disable artifact | Decommission item |

---

## Verb Prompt Locations

```
/Control_Plane/control_plane/prompts/
  ├── install.md     # How to install a registry item
  ├── update.md      # How to update a registry item
  ├── verify.md      # How to verify a registry item
  └── uninstall.md   # How to uninstall a registry item
```

---

## Loading Procedure

### Step 1: Locate Verb Prompts

```
verb_prompts_dir = /Control_Plane/control_plane/prompts/
required_verbs = ["install", "update", "verify", "uninstall"]

FOR EACH verb IN required_verbs:
  path = verb_prompts_dir + verb + ".md"
  IF NOT EXISTS path:
    FAIL: "Missing required verb prompt: {verb}.md"
  LOG: "Found verb prompt: {verb}"
```

### Step 2: Parse Each Verb Prompt

```
verb_registry = {}
FOR EACH verb IN required_verbs:
  path = verb_prompts_dir + verb + ".md"
  content = READ path

  verb_registry[verb] = {
    "name": verb,
    "path": path,
    "content": content,
    "loaded_at": ISO_8601_TIMESTAMP
  }
  LOG: "Loaded verb prompt: {verb}"
```

### Step 3: Verify Verb Prompt Structure

Each verb prompt should contain:
- Purpose section
- Input parameters (what context it receives from registry row)
- Step-by-step procedure
- Success criteria
- Error handling

```
FOR EACH verb IN verb_registry:
  VERIFY content contains:
    - "## Purpose" or "## Intent"
    - "## Parameters" or "## Input"
    - "## Steps" or "## Procedure"

  IF verification fails:
    WARN: "Verb prompt {verb} may be incomplete"
```

---

## Verb Prompt Format

Each verb prompt receives a registry row as context:

```markdown
# Install Prompt

## Purpose
Create the artifact defined by a registry row.

## Input (from registry row)
- id: The item ID (e.g., FMWK-001)
- name: Human-readable name
- artifact_path: Where to create the artifact
- purpose: What this item does
- dependencies: Items that must exist first

## Procedure
1. Verify dependencies are installed (status=active)
2. Create artifact at artifact_path
3. Populate with appropriate content
4. Update registry: status=active, last_updated=now
5. Run verify prompt to confirm

## Success Criteria
- Artifact exists at artifact_path
- Content matches purpose
- Validator passes
- Registry updated

## Error Handling
- If dependency missing: report and abort
- If path conflict: report and abort
- If creation fails: report, leave status=missing
```

---

## How Verbs Are Invoked

When executing plan.json, for each item:

```
FOR EACH item IN plan.items:
  verb = determine_verb(item)  # based on status and selected
  prompt = verb_registry[verb]

  # Substitute item fields into prompt
  context = {
    "id": item.id,
    "name": item.name,
    "artifact_path": item.artifact_path,
    "purpose": item.purpose,
    "dependencies": item.dependencies,
    ...
  }

  # Execute the verb with context
  EXECUTE prompt.content WITH context

  # Update registry based on result
  IF success:
    UPDATE item.status = "active"
    UPDATE item.last_updated = now()
  ELSE:
    LOG ERROR: "Verb {verb} failed for {item.id}"
```

---

## Verb Selection Logic

```
FUNCTION determine_verb(item):
  IF item.status == "missing" AND item.selected == "yes":
    RETURN "install"

  IF item.status == "active" AND needs_update(item):
    RETURN "update"

  IF item.status == "active" AND item.selected == "no":
    RETURN "uninstall"

  IF verification_requested:
    RETURN "verify"

  RETURN null  # No action needed
```

---

## Custom Module Prompts

Modules can define their own verb prompts in addition to the core ones:

```
/Control_Plane/modules/repo_os/prompts/v1/
  ├── 01_archive_clean_init_meta_prompt.md
  ├── 02_prompt_governance_model.md
  └── ...
```

These are referenced via `install_prompt_path` in registries.

---

## Output

After successful loading:

```
Verb prompts loaded:
  - install: /Control_Plane/control_plane/prompts/install.md
  - update: /Control_Plane/control_plane/prompts/update.md
  - verify: /Control_Plane/control_plane/prompts/verify.md
  - uninstall: /Control_Plane/control_plane/prompts/uninstall.md

Ready to execute verbs on registry items.
```
