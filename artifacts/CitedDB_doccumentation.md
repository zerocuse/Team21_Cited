# Cited Database Documentation

**Last Updated:** February 13, 2026

## Overview

This database powers **Cited**, an AI-powered fact-checking web application. It stores user accounts, claims to be verified, fact-checking results, sources, and knowledge base entries.

---

## Database Tables Explained

### 👤 User Table
**What it stores:** User account information

**Fields:**
- `userID` (Primary Key) - Unique identifier for each user
- `username` - Display name
- `email` - User's email address
- `password_hash` - Encrypted password (never store plain text!)
- `admin?` - Boolean flag indicating if user has admin privileges
- `creation_time` - When the account was created

**Use case:** Authentication, tracking who submitted which claims

---

### 💬 Claim Table
**What it stores:** Statements or claims that users want fact-checked

**Fields:**
- `claimID` (Primary Key) - Unique identifier for each claim
- `claimText` - The actual statement to be verified
- `status` - Current state (e.g., "pending", "verified", "debunked")
- `queriedAt` - When the claim was submitted
- `lastUpdatedAt` - Last modification timestamp
- `viewCount` - How many times this claim has been viewed
- `userID` (Foreign Key) - Links to the User who submitted it

**Use case:** Central table for all fact-checking requests

---

### 🔖 Tag Table
**What it stores:** Categories or topics for organizing claims

**Fields:**
- `tagID` (Primary Key) - Unique identifier for each tag
- `tagName` - Display name (e.g., "Politics", "Science", "Health")
- `tagCategory` - Broader grouping (e.g., "News", "Academia")
- `timesUsed` - Count of how many claims use this tag

**Use case:** Filtering and categorizing claims by topic

---

### 🔗 ClaimTagLink Table
**What it stores:** Connections between Claims and Tags (many-to-many relationship)

**Fields:**
- `ClaimToTag` (Primary Key) - Unique identifier for this link
- `claimID` (Foreign Key) - References a Claim
- `tagID` (Foreign Key) - References a Tag

**Use case:** One claim can have multiple tags, one tag can apply to multiple claims

**Example:**
- Claim #42 ("Vaccines cause autism") might be linked to tags: "Health", "Medical", "Debunked"

---

### ✅ FactCheck Table
**What it stores:** AI-generated verification results for claims

**Fields:**
- `factCheckID` (Primary Key) - Unique identifier for each fact-check
- `verdict` - Final determination (e.g., "True", "False", "Misleading")
- `confidenceScore` - Numerical confidence (0-100%)
- `explanation` - Human-readable summary of findings
- `aiReasoning` - Detailed AI analysis and logic
- `checkedVia` - Method used (e.g., "AI Model GPT-4", "Manual Review")
- `userID` (Foreign Key) - User who initiated the check
- `claimID` (Foreign Key) - Claim that was checked

**Use case:** Stores the results of AI fact-checking analysis

---

### 📰 Source Table
**What it stores:** External sources used for verification (websites, articles, papers)

**Fields:**
- `sourceID` (Primary Key) - Unique identifier for each source
- `URL` - Web address of the source
- `title` - Name of the article/page
- `sourceType` - Category (e.g., "News", "Academic", "Government")
- `sourceCredibilityRating` - Trust score (0-100%)

**Use case:** Tracking where information comes from, evaluating source reliability

---

### 🔗 ClaimSourceLink Table
**What it stores:** Connections between Claims and Sources

**Fields:**
- `ClaimToSource` (Primary Key) - Unique identifier for this link
- `claimID` (Foreign Key) - References a Claim
- `sourceID` (Foreign Key) - References a Source

**Use case:** Shows which sources were used to evaluate each claim

**Example:**
- Claim #42 might link to sources: Reuters article, CDC study, Wikipedia page

---

### 📚 Knowledge Base Table
**What it stores:** Pre-verified facts and information for quick lookups

**Fields:**
- `factID` (Primary Key) - Unique identifier for each fact
- `umbrellaTopic` - Broad subject area
- `content` - The verified fact or information
- `summary` - Brief overview
- `dateVerified` - When this fact was last confirmed
- `verificationStatus` - Current validity (e.g., "Verified", "Outdated")

**Use case:** Storing commonly-checked facts to avoid re-verification

---

### 🔗 FactToSource Table
**What it stores:** Connections between Knowledge Base entries and Sources

**Fields:**
- `FactToSource` (Primary Key) - Unique identifier for this link
- `factID` (Foreign Key) - References a Knowledge Base entry
- `sourceID` (Foreign Key) - References a Source

**Use case:** Documenting which sources support each verified fact

---

### 📝 Citation Table
**What it stores:** Specific citations used in fact-checking explanations

**Fields:**
- `citationID` (Primary Key) - Unique identifier for each citation
- `infoUsed` - Specific excerpt or data point cited
- `relevanceScore` - How relevant this citation is (0-100%)
- `factCheckID` (Foreign Key) - Links to the FactCheck that used it
- `sourceID` (Foreign Key) - Links to the Source it came from

**Use case:** Providing transparency about exactly what information was used and from where

---

## How the Database Works: Common Workflows

### 1️⃣ User Submits a Claim
```
User enters claim → Claim record created
                  → Tags assigned via ClaimTagLink
                  → Status set to "pending"
```

### 2️⃣ AI Fact-Checks the Claim
```
System retrieves Claim
     → Searches Knowledge Base
     → Fetches relevant Sources
     → Creates ClaimSourceLink records
     → AI analyzes data
     → FactCheck record created with verdict
     → Citations created for transparency
     → Claim status updated to "verified" or "debunked"
```

### 3️⃣ User Views Results
```
User requests claim details
     → Retrieve Claim + FactCheck
     → Load all Citations
     → Load all Sources via ClaimSourceLink
     → Display verdict, explanation, and sources
     → Increment viewCount
```

### 4️⃣ Admin Adds to Knowledge Base
```
Admin verifies a fact
     → Knowledge Base entry created
     → Sources linked via FactToSource
     → Available for future quick lookups
```

---

## Database Relationships Summary

```
User ──creates──> Claim ──has──> FactCheck
                    │              │
                    │              └──references──> Citation ──from──> Source
                    │                                                     │
                    ├──tagged with──> ClaimTagLink ──links to──> Tag     │
                    │                                                     │
                    └──verified by──> ClaimSourceLink ──references───────┘
                                                                          │
Knowledge Base ──supported by──> FactToSource ──references──────────────┘
```
