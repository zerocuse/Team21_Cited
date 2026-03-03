# Cited Code Guidelines

---

## General Principles

- **Clarity over cleverness** — Code should be obvious to read at a glance.
- **Consistency** — Follow existing patterns in the codebase. When something is done a certain way once, do it that way everywhere.
- **Documentation** — If you need to explain *what* it does, refactor it. If you need to explain *why* it works that way, write a comment.
- **When in doubt:**
  - Check existing code for patterns
  - Prioritize readability
  - **ASK THE TEAM!!!!**

---

## Naming Conventions

### Variables & Functions — `camelCase`
Use descriptive, specific names. Prioritize specificity over brevity — the code needs to be readable to everyone on the team.

```python
# Good
confidenceScore = 87.5
claimVerificationStatus = VerificationStatus.TRUE

# Bad
score = 87.5
s = VerificationStatus.TRUE
```

### Classes — `PascalCase`
Names must describe what the class *represents*, not what it *does*.

```python
# Good
class FactCheck:
class KnowledgeBaseEntry:
class ClaimTagLink:

# Bad
class Checker:
class Entry:
```

### Database Column Names — `snake_case`
All SQLAlchemy column names use `snake_case`. This matches SQL conventions and keeps database fields distinct from Python variables.

```python
# Good
claim_text = db.Column(db.Text, nullable=False)
password_hash = db.Column(db.String(128), nullable=False)
confidence_score = db.Column(db.Float, nullable=True)

# Bad
claimText = db.Column(db.Text, nullable=False)
```

**Exception:** Primary and foreign key IDs follow `entityNameID` format in `camelCase` to distinguish them clearly as identifiers.

```python
userID = db.Column(db.Integer, primary_key=True)
claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'))
```

### Table Names — `snake_case` (plural)
Always define `__tablename__` explicitly. Use lowercase `snake_case`, plural form.

```python
__tablename__ = 'fact_checks'
__tablename__ = 'knowledge_base'
__tablename__ = 'claim_tag_link'
```

### Enum Classes — `PascalCase` class, `ALL_CAPS` members
Enum class names describe the *category* of value. Members are `ALL_CAPS`.

```python
class VerificationStatus(enum.Enum):
    TRUE = "true"
    FALSE = "false"
    PARTIALLY_TRUE = "partially true"

class SourceType(enum.Enum):
    NEWS = "news"
    ACADEMIC = "academic"
    SOCIAL_MEDIA = "social media"
```

### Static / Constant Variables — `ALL_CAPS_WITH_UNDERSCORES`

```python
PASSING_SCORE = 75
TIMEOUT_CAP_SECONDS = 60
MAX_CLAIM_LENGTH = 5000
```

---

## Database Model Standards

Every SQLAlchemy model **must** follow this structure consistently:

### 1. Explicit `__tablename__`
Always define the table name — never rely on SQLAlchemy's default.

### 2. Primary Key Convention
Single-column primary keys follow `entityNameID` format with `autoincrement=True` where applicable.

```python
userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
```

For link/join tables, use composite primary keys:

```python
claimID = db.Column(db.Integer, db.ForeignKey('claims.claimID'), primary_key=True)
tagID = db.Column(db.Integer, db.ForeignKey('tag.tagID'), primary_key=True)
```

### 3. Nullable Fields — Be Explicit
Every column must explicitly declare `nullable=True` or `nullable=False`. Never assume the default. Add a comment when `nullable=True` explaining why it can be null.

```python
profile_picture = db.Column(db.String(500), nullable=True)  # URL to profile picture, can be null
confidence_score = db.Column(db.Float, nullable=True)       # Optional — not always calculable
```

### 4. Enums for Constrained Values
Any field with a fixed set of allowed values must use an `Enum` class (defined at the top of the file), not raw strings.

```python
# Good
status = db.Column(db.Enum(VerificationStatus), nullable=True)

# Bad
status = db.Column(db.String(50), nullable=True)  # "true", "false", etc.
```

### 5. `__repr__` on Every Model
Every model class must have a `__repr__` method for debugging. Include the most identifying fields and at least one meaningful status/type field. Truncate long text fields to 50 characters.

```python
def __repr__(self):
    return f"<Claim {self.claim_text[:50]}... - Status: {self.status}>"

def __repr__(self):
    return f"<User {self.username} ({self.email}) - Membership: {self.membership_status}>"
```

### 6. Timestamps
Use `db.func.current_timestamp()` for all timestamp defaults, never Python's `datetime.now()` (which is evaluated at import time, not at insert time).

```python
creation_date = db.Column(db.DateTime, default=db.func.current_timestamp())
last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
```

---

## Code Organization

- **One primary class per file** for models, services, and utilities
- **Group enums at the top of the file** — before any model definitions
- **Group related utilities together** — export only what's needed publicly
- **Import order:**
  1. Standard library
  2. Third-party packages (Flask, SQLAlchemy, etc.)
  3. Internal modules

---

## Formatting Rules

- **Max line length: 100 characters.** Break longer lines.
- **Space after commas:** `[1, 2, 3]`, `db.Column(db.String(80), nullable=False)`
- **Spaces around operators:** `x = y + 1`, `confidence_score >= PASSING_SCORE`
- **Blank line between class methods** and between top-level definitions
- **No trailing whitespace**
- Break long function calls across multiple lines, aligning arguments:

```python
# Good
userID = db.Column(
    db.Integer,
    db.ForeignKey('users.userID'),
    nullable=False
)

# Bad
userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)  # over 100 chars
```

---

## Documentation Requirements

Comment **why**, not **what**. If the code is clear enough to explain what it does on its own, don't add noise.

```python
# Good — explains why
checked_via = db.Column(db.Enum(CheckedVia), nullable=True)  # Null until a fact-check is assigned

# Bad — explains what (we can already see that)
# This is the checked_via column
checked_via = db.Column(db.Enum(CheckedVia), nullable=True)
```

For any non-obvious logic, constants, or design decisions, add a short inline comment or a block comment above the relevant section.

---

## Git Commit Format

**Format:** `<type>: <short description>`

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring without changing behavior |
| `test` | Adding or updating tests |

**Examples:**
```
feat: add confidence_score field to FactCheck model
fix: correct nullable setting on Source.publication_date
refactor: extract VerificationStatus enum to shared enums file
docs: update coding guidelines with database model standards
```

Keep descriptions short and in the **imperative mood** ("add", "fix", "update" — not "added", "fixed", "updated").
