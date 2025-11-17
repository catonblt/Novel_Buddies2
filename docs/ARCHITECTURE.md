# Architecture Documentation

## System Overview

Novel Writer is a desktop application that combines a React frontend with a Python backend and Rust-based native operations through Tauri.

```
┌─────────────────────────────────────────────────────────┐
│                     Tauri Desktop App                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │           React Frontend (Port 1420)              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │  │
│  │  │  Workspace  │  │ Agent Chat  │  │ Explorer │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │  │
│  │           ↓ HTTP Requests                        │  │
│  └───────────────────────────────────────────────────┘  │
│                      ↓                                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │          Rust Backend (Tauri Commands)            │  │
│  │  • File Operations (read/write/list)              │  │
│  │  • Git Operations (commit/log/restore)            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│           Python FastAPI Backend (Port 8000)            │
│  ┌───────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Projects  │  │ Agent Chat  │  │ File/Git APIs   │  │
│  └───────────┘  └─────────────┘  └─────────────────┘  │
│         ↓                ↓                              │
│  ┌───────────┐  ┌─────────────────────────────────┐   │
│  │  SQLite   │  │     Anthropic Claude API        │   │
│  └───────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Technology Stack

- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **shadcn/ui**: Component library (built on Radix UI)
- **Zustand**: State management
- **Vite**: Build tool

### Component Hierarchy

```
App
├── SetupWizard (first launch)
│   └── Two-step project creation
└── Workspace
    ├── Header
    │   └── SettingsDialog
    ├── AgentChat (60% width)
    │   ├── MessageBubble
    │   ├── AgentSelector
    │   └── Input area
    └── ProjectExplorer (40% width)
        ├── File tree
        └── FilePreview
```

### State Management

**Global State (Zustand)**:
```typescript
interface AppState {
  currentProject: Project | null;
  messages: Message[];
  activeAgents: Agent[];
  selectedFile: FileNode | null;
  settings: AppSettings;
  isLoading: boolean;
}
```

**Key Features**:
- Single source of truth
- Automatic persistence (localStorage)
- No prop drilling
- TypeScript support

### API Communication

All backend communication goes through `src/lib/api.ts`:

```typescript
const api = {
  // Projects
  createProject(data) -> Project
  getProject(id) -> Project
  listProjects() -> Project[]
  updateProject(id, data) -> Project

  // Chat
  sendMessage(projectId, message, agentType, apiKey) -> ReadableStream

  // Files
  listFiles(path) -> FileNode[]
  readFile(path) -> string
  writeFile(path, content) -> void

  // Git
  getCommitHistory(path) -> CommitInfo[]
  restoreFileVersion(path, file, commitId) -> void
}
```

## Backend Architecture (Python)

### FastAPI Structure

```
python-backend/
├── main.py              # App initialization, CORS, routes
├── models/
│   └── database.py      # SQLAlchemy models, DB setup
├── agents/
│   └── prompts.py       # Agent system prompts
└── routes/
    ├── projects.py      # Project CRUD + folder structure creation
    ├── chat.py          # Claude API streaming
    ├── files.py         # File read/write operations
    └── git.py           # Git operations (via subprocess)
```

### Database Schema

**Projects Table**:
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT NOT NULL,
    target_word_count INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    path TEXT UNIQUE NOT NULL,
    premise TEXT,
    themes TEXT,
    setting TEXT,
    key_characters TEXT
);
```

**Messages Table**:
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    agent_type TEXT,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### Agent System

Each agent has a comprehensive system prompt in `agents/prompts.py`:

**Structure**:
```python
AGENT_SYSTEM_PROMPTS = {
    "story-architect": """
        [Role definition]
        [Expertise areas]
        [Responsibilities]
        [File access permissions]
        [Collaboration style]
        [Quality standards]
    """,
    # ... other agents
}
```

**Chat Flow**:
1. User sends message + selects agent
2. Backend retrieves agent system prompt
3. Adds project context (title, genre, path, etc.)
4. Retrieves conversation history from database
5. Streams response from Claude API
6. Saves messages to database
7. Frontend receives streaming chunks

### Streaming Implementation

```python
async def stream_claude_response(project, message, agent_type, api_key, db):
    client = anthropic.Anthropic(api_key=api_key)

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        system=system_prompt,
        messages=conversation,
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'content', 'content': text})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

## Tauri/Rust Backend

### Commands

**File Operations** (`src-tauri/src/file_ops.rs`):
```rust
#[tauri::command]
fn read_file_content(path: String) -> Result<String, String>

#[tauri::command]
fn write_file_content(path: String, content: String) -> Result<(), String>

#[tauri::command]
fn list_directory(path: String) -> Result<Vec<FileInfo>, String>

#[tauri::command]
fn create_directory(path: String) -> Result<(), String>

#[tauri::command]
fn delete_file(path: String) -> Result<(), String>
```

**Git Operations** (`src-tauri/src/git_ops.rs`):
```rust
#[tauri::command]
fn init_git_repo(path: String) -> Result<(), String>

#[tauri::command]
fn git_commit(repo_path, message, author_name, author_email) -> Result<String, String>

#[tauri::command]
fn git_log(repo_path, max_count) -> Result<Vec<CommitInfo>, String>

#[tauri::command]
fn restore_file_version(repo_path, file_path, commit_id) -> Result<(), String>
```

### Security

- File system access is sandboxed to user documents
- No shell access except for controlled git operations
- API keys stored in application settings (not in code)
- CORS restricted to localhost and tauri:// protocol

## Project File Structure

When a project is created:

```
~/NovelProjects/my-novel/
├── .git/                       # Initialized automatically
├── .novel-project.json         # Project metadata
├── planning/
│   ├── story-outline.md
│   ├── chapter-breakdown.md
│   └── themes.md
├── characters/
│   └── _character-template.md
├── manuscript/
│   ├── final-manuscript.md
│   ├── chapters/
│   └── scenes/
├── story-bible/
│   ├── continuity.md
│   ├── timeline.md
│   └── world-notes.md
├── research/
├── feedback/
│   ├── editorial-notes.md
│   └── revision-log.md
└── exports/
```

## Data Flow Examples

### Creating a Project

```
User fills form → Frontend validates → API POST /projects
→ Backend creates DB record → Creates folder structure
→ Initializes Git repo → Returns project object
→ Frontend sets currentProject → Navigates to Workspace
```

### Agent Conversation

```
User types message → Selects agent → Clicks Send
→ Frontend sends to POST /chat (streaming)
→ Backend retrieves project + conversation history
→ Calls Claude API with agent system prompt
→ Streams response chunks to frontend
→ Frontend displays words as they arrive
→ Backend saves messages to database
→ Agent may create/modify files (autonomously or with approval)
→ Frontend shows file change notifications
```

### File Operations

```
User clicks file in explorer → Frontend reads from cache or calls readFile
→ Tauri command reads file from disk → Returns content
→ Frontend displays in preview pane
→ User requests edit → Agent modifies file
→ Tauri command writes to disk → Git auto-commits change
→ Frontend refreshes file list
```

## Performance Considerations

1. **File Caching**: Frequently accessed files are cached in frontend state
2. **Lazy Loading**: File trees load children on-demand
3. **Streaming**: Agent responses stream to avoid blocking
4. **Debouncing**: Search inputs debounced to reduce API calls
5. **Optimistic Updates**: UI updates before backend confirmation

## Error Handling

- **Frontend**: Try-catch blocks with user-friendly alerts
- **Backend**: HTTP status codes + detailed error messages
- **Tauri**: Result types with custom error strings
- **Database**: Transaction rollbacks on failure

## Security Model

1. **API Keys**: Stored in app settings, never logged
2. **File Access**: Limited to project directories
3. **Git Operations**: Sandboxed to project repos
4. **CORS**: Restricted origins
5. **No Eval**: No dynamic code execution

## Build & Deployment

### Development

```bash
# Terminal 1: Backend
cd python-backend && uvicorn main:app --reload

# Terminal 2: Frontend
npm run tauri:dev
```

### Production Build

```bash
npm run tauri:build
```

**Output**:
- **macOS**: `.dmg` and `.app` in `src-tauri/target/release/bundle/`
- **Windows**: `.msi` and `.exe`
- **Linux**: `.deb`, `.AppImage`

## Future Enhancements

1. **Web Version**: Remove Tauri, use Electron or pure web
2. **Collaboration**: WebSocket for real-time multi-user
3. **Cloud Sync**: Optional S3/Dropbox integration
4. **Export Engine**: Generate EPUB/DOCX/PDF
5. **Plugin System**: Allow custom agents and extensions
6. **Testing**: Increase test coverage (currently minimal)

---

For agent-specific details, see [AGENT_GUIDE.md](AGENT_GUIDE.md).
For user documentation, see [USER_GUIDE.md](USER_GUIDE.md).
