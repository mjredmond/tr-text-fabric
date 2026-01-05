# Project Plan: Textus Receptus Text-Fabric Dataset

**Goal:** Create a Text-Fabric (TF) dataset for the Textus Receptus (TR) that possesses full syntactic equivalence (syntax trees, clause boundaries, phrase functions) to the existing N1904 (Patriarchal Text) dataset.

**Strategy:** "Graft and Patch."
Since the TR and N1904 are ~98% identical (Byzantine text-type), we will programmatically transplant existing syntax data where texts align, and use AI (Stanza/LLMs) to generate syntax trees only for the unique TR variances.

---

## 1. Prerequisites & Setup

### Environment
* **Language:** Python 3.10+
* **Environment:** WSL / Linux (Recommended for TF performance)
* **Key Libraries:** `text-fabric`, `pandas`, `stanza`, `difflib` (or `biopython`), `ipython`

### Data Sources
* **Target Template (N1904):** The existing TF dataset (acts as the schema master).
* **Source Text (TR):** A robust digital TR edition with morphology (e.g., Robinson-Pierpont 2018 or Scrivener 1894) in CSV/JSON format.

---

## 2. Execution Phases

### Phase 1: Reconnaissance & Schema Extraction
*Objective: Map exactly which features exist in N1904 so we can replicate the structure.*

- [ ] **Load N1904 in Text-Fabric:**
    - Script a probe to list all `onetypes` (e.g., sentence, clause, phrase).
    - List all node features (e.g., `role`, `function`, `parent`, `sp`, `voice`).
- [ ] **Create Schema Definition:**
    - Generate a JSON file (`schema_map.json`) defining the required columns and data types.
    - *Critical Decision:* Determine how N1904 handles "embedded clauses" to ensure we mimic the graph depth correctly.
- [ ] **Prepare TR Source:**
    - Standardize the TR raw text into a Pandas DataFrame with unique identifiers per word (`book`, `chapter`, `verse`, `word_rank`).

### Phase 2: The "Great Alignment" (The 98%)
*Objective: Map N1904 syntax trees onto the TR text where words are identical.*

- [ ] **Sequence Alignment Script:**
    - Use `difflib.SequenceMatcher` to align texts at the **Verse Level**.
    - Match criteria: Lemma + Parsing (Case/Tense/Voice).
- [ ] **Data Transplantation:**
    - Iterate through aligned verses.
    - If `TR_Word == N1904_Word`: Copy all syntactic features (`parent`, `function`, `clause_atom`) to the TR dataset.
    - **ID Re-indexing:** Create a translation table (`N1904_NodeID` -> `TR_NodeID`). Syntax trees use pointers; these pointers must be mathematically offset to point to the new TR word positions.
- [ ] **Delta Isolation:**
    - Flag any TR words/phrases that do not match N1904. Store these as "Gaps" for Phase 3.

### Phase 3: The Delta Patching (AI Processing)
*Objective: Generate syntax trees for TR-exclusive readings (e.g., Comma Johanneum, Acts 8:37).*

- [ ] **Configure Stanza (NLP):**
    - Install `stanza` with the Ancient Greek (`grc`) model (trained on PROIEL/Perseus).
- [ ] **Process Gaps:**
    - Feed the unaligned TR phrases into Stanza to generate dependency trees (CoNLL-U format).
- [ ] **Feature Translation ("Rosetta Stone"):**
    - Map Stanza's *Universal Dependencies* labels to N1904's *Lowfat* labels.
    - *Mapping Example:* `nsubj` (Stanza) -> `Subject` (N1904).
- [ ] **Theological Review (Manual/LLM):**
    - Use an LLM (e.g., Claude/GPT-4 via Aider) to review syntax for high-profile verses (1 John 5:7, 1 Tim 3:16).
    - *Prompt:* "Validate this syntax tree for [Verse]. Ensure the subject/predicate relationship follows standard Greek grammar."

### Phase 4: Compilation & Build
*Objective: Serialize the data into valid Text-Fabric files.*

- [ ] **Merge DataFrames:**
    - Combine the Transplanted Data (Phase 2) and Patched Data (Phase 3).
- [ ] **Generate TF Files:**
    - Use `tf.fabric` to write the `.tf` files.
    - **Node Features:** `word.tf`, `sp.tf`, `gloss.tf`, `function.tf`, `role.tf`.
    - **Edge Features:** `parent.tf` (defines the tree structure).
    - **Container Features:** `sentence.tf`, `clause.tf`, `phrase.tf` (defines boundaries).
- [ ] **OTypes Configuration:**
    - Define the hierarchy: `Book > Chapter > Verse > Sentence > Clause > Phrase > Word`.

### Phase 5: Quality Assurance

- [ ] **Cycle Check:** Run a script to ensure no circular dependencies in the syntax trees (Child cannot be parent of its own Ancestor).
- [ ] **Orphan Check:** Ensure every word belongs to a phrase, every phrase to a clause, etc.
- [ ] **Spot Check:** Manually inspect 5 major variants (e.g., Rev 22:19 "Book vs Tree") in the final TF app to ensure structure holds.

---

## 3. Technical Stack & Tools

| Component | Tool | Purpose |
| :--- | :--- | :--- |
| **Orchestrator** | Python (Pandas) | Data manipulation and ID mapping. |
| **NLP Engine** | Stanza (Stanford NLP) | Generating syntax trees for unique TR text. |
| **Alignment** | `difflib` / `collatex` | Matching TR to N1904. |
| **Coding Assistant** | Aider / OpenCode | Generating the "glue" code and mapping logic. |
| **Build Engine** | `text-fabric` API | The official library to write the dataset. |

## 4. Immediate Next Steps for Developer

1.  **Run Schema Scout:** Write the script to dump N1904 feature list.
2.  **Acquire Data:** Download the Robinson-Pierpont 2018 raw CSV.
3.  **Prototype Alignment:** Run the alignment script on a single book (e.g., 3 John) as a Proof of Concept.